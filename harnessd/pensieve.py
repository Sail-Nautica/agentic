from __future__ import annotations
import aiosqlite
import asyncio
from collections.abc import Iterator
from http import HTTPStatus
import math
from msgspec import DecodeError, Raw, Struct, UNSET, UnsetType, json
import struct
import sys
import threading

MAX_RECENT_TURNS = 20            # newest turns served verbatim from _retrieveHistory,
                                 # lower it for smaller demo conversations
MAX_FALLBACK_TURNS = 200         # newest turns served when recall is unavailable
MAX_VECTOR_LEG_CANDIDATES = 48   # vector leg candidate depth before selection
MAX_RECALL_ITEMS = 24            # hard ceiling on recall bullets
MAX_RECALL_CHARS = 16_000        # recall block budget in display chars (~4K tokens)
MAX_RECALL_ITEM_CHARS = 4000     # recalled user-utterance chars per turn

# OpenAI embeddings response: {"data": [{"embedding": [...], ...}, ...]}
class EmbeddingData(Struct):
    embedding: list[float] = []

class EmbeddingResponse(Struct):
    data: list[EmbeddingData] = []

class PromptMessage(Struct):
    role: str | None = None
    content: Raw | UnsetType = UNSET

class ContentPart(Struct):
    text: str | None = None

def _contentText(content: Raw) -> Iterator[str]:
    body = bytes(content)
    match body[:1]:
        # string content decodes directly
        case b'"':
            try:
                yield json.decode(content, type=str)
            except DecodeError:
                return
        # array content (multimodal) yields its text parts
        case b'[':
            try:
                parts = json.decode(content, type=list[ContentPart])
            except DecodeError:
                return
            yield from (part.text for part in parts if part.text)

def _messageText(raw: Raw) -> Iterator[str]:
    try:
        message = json.decode(raw, type=PromptMessage)
    except DecodeError:
        return
    if message.role == "user" and message.content is not UNSET:
        yield from _contentText(message.content)

def _promptPlaintext(promptJson: bytes | Raw) -> str:
    try:
        messages = json.decode(promptJson, type=list[Raw])
    except DecodeError:
        return ""
    return "\n".join(text for raw in messages for text in _messageText(raw))

localEmbedLock = threading.Lock()
_embedLongInputWarned = False

async def _embedText(state, text: str) -> list[float]:
    global _embedLongInputWarned
    embed = state.runners.embed
    if embed is None:
        raise RuntimeError("no embedding runner configured")

    inputCap = 2_000 if embed.local is not None else 24_000
    if not _embedLongInputWarned and len(text) > inputCap:
        _embedLongInputWarned = True
        print(f"embed input exceeds the ~{inputCap}-char embedder context; the "
              f"tail is truncated or rejected by the embedder, not by this check",
              file=sys.stderr)

    if embed.local is not None:
        def embedLocal() -> list[float]:
            with localEmbedLock:
                return next(state.embedModel.embed([text])).tolist()
        vec = await asyncio.wait_for(asyncio.to_thread(embedLocal), 15.0)
        got = len(vec)
    else:
        headers = {"Authorization": f"Bearer {embed.api.key}"} if embed.api.key else {}
        response = await state.client.post(
            f"{embed.api.url}/v1/embeddings",
            json={"model": embed.model, "input": [text]},
            headers=headers,
            timeout=15.0,
        )
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError(f"embedding runner returned {response.status_code}")

        parsed = json.decode(response.content, type=EmbeddingResponse)
        vec = parsed.data[0].embedding if parsed.data else []
        got = len(vec)
    if got != embed.dim:
        raise RuntimeError(f"embedding dim {got}, expected {embed.dim}")
    norm = math.sqrt(sum(value * value for value in vec))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError(f"degenerate embedding norm {norm}")
    for i, v in enumerate(vec):
        vec[i] = v / norm
    return vec

def _blobFromUnit(embedding: list[float]) -> bytes:
    return struct.pack(f"<{len(embedding)}f", *embedding)

async def _recallGate(rwdb: aiosqlite.Connection, appID: str, limit: int) -> tuple[int, int]:
    row = await (await rwdb.execute(
        "WITH last AS ("
        " SELECT turnID, ROW_NUMBER() OVER (ORDER BY turnID DESC) AS rn"
        " FROM turns WHERE appID = ? AND completed = 1"
        " ORDER BY turnID DESC LIMIT ?)"
        " SELECT COUNT(*), COALESCE(MIN(CASE WHEN rn <= ? THEN turnID END), 0) FROM last",
        (appID, limit + 1, limit),
    )).fetchone()
    assert row is not None  # aggregate without GROUP BY always returns exactly one row
    return row[0], row[1]

class Recall(Struct):
    turnID:    int
    prompt: str

async def _recallBlock(state, rwdb: aiosqlite.Connection, appID: str, prompt: str) -> tuple[list[Recall], int]:
    try:
        turnCount, scanFloor = await _recallGate(rwdb, appID, MAX_RECENT_TURNS)
        if turnCount <= MAX_RECENT_TURNS:
            # 0..=MAX_RECENT_TURNS turns: the window serves everything, floor stays 0
            return [], 0

        recall = await _recallTurns(state, rwdb, appID, prompt, scanFloor)
        if recall:
            return recall, scanFloor

    except Exception as e:
        print(f"recall failed (serving the fallback window): {e}", file=sys.stderr)

    _, floor = await _recallGate(rwdb, appID, MAX_FALLBACK_TURNS)
    return [], floor

async def _recallTurns(state, rwdb: aiosqlite.Connection, appID: str, prompt: str, scanFloor: int) -> list[Recall]:
    if state.runners.embed is None or state.vectorOptions is None:
        return []
    embedding = await _embedText(state, prompt)
    blob = _blobFromUnit(embedding)

    async with rwdb.execute(
        "SELECT v.rowid"
        " FROM vector_quantize_scan('turns','embedding', ?) AS v"
        " JOIN turns t ON t.turnID = v.rowid"
        " WHERE t.appID = ? AND t.turnID < ?"
        " ORDER BY v.distance LIMIT ?",
        (blob, appID, scanFloor, MAX_VECTOR_LEG_CANDIDATES),
    ) as cur:
        ids = [row[0] for row in await cur.fetchall()]
    if not ids:
        return []

    pool = ids[:MAX_RECALL_ITEMS]
    async with rwdb.execute(
        "SELECT turnID, prompt FROM turns WHERE turnID IN (SELECT value FROM json_each(?))",
        (json.encode(pool).decode(),),
    ) as cur:
        byID = {row[0]: row[1] for row in await cur.fetchall()}

    recall: list[Recall] = []
    remaining = MAX_RECALL_CHARS
    for turnID in pool:
        if turnID not in byID:
            continue
        # cap the per-turn display text in place: one pass, no second payload
        prompt = _promptPlaintext(byID[turnID])[:MAX_RECALL_ITEM_CHARS]
        if not prompt:
            continue
        cost = len(prompt)
        if cost > remaining:
            continue
        remaining -= cost
        recall.append(Recall(turnID, prompt))

    return recall

def _recallMessage(recall: list[Recall]) -> Raw:
    from handlers import Message  # call-time: handlers imports pensieve at startup
    return Raw(json.encode(Message(
        role="system",
        content="Semantic search results from earlier turns in this conversation matching current prompt:\n"
            + "".join(f"- [turn {item.turnID}] {item.prompt}\n" for item in recall),
    )))
