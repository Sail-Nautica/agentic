from __future__ import annotations # must be the first line of the file
import aiosqlite
import asyncio
from collections.abc import AsyncGenerator
from enum import IntEnum, auto
from sse_starlette.sse import EventSourceResponse

from http import HTTPStatus
import httpx
from httpx import RequestError, Response
import logging
from msgspec import DecodeError, Raw, Struct, ValidationError, field, json, structs, UNSET, UnsetType
import sqlite3
import sys
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response, StreamingResponse
from structured import Capture, CompletionLexer, LexTarget
from pensieve import _recallBlock, _recallMessage, _promptPlaintext, _embedText, _blobFromUnit, MAX_RECALL_ITEM_CHARS

MAX_HISTORY_BYTES = 64_000  # replayed-window budget in JSON bytes (~16K tokens)
MAX_EMBED_ITEM_CHARS = 4000 # caps the completion fallback in end-of-stream outcome triage

EMBED_CONCURRENCY = 4                   # max number of outstanding embeddings
_embedGate = asyncio.Semaphore(EMBED_CONCURRENCY)
_embedTasks: set[asyncio.Task] = set()  # for shutdown cleanup

class Message(Struct, omit_defaults=True):
	role: str
	content: str | None

class OpenAIRequest(Struct, omit_defaults=True, kw_only=True):
	appID:    str | UnsetType
	model: str
	messages: Raw
	stream: bool = False
	max_tokens: int | None = None
	response_format: Raw = Raw()

class OpenAIDelta(Struct):
    content:           str | None = None
    reasoning:         str | None = None
    reasoning_content: str | None = None

class OpenAIChoice(Struct):
    delta:         OpenAIDelta = field(default_factory=OpenAIDelta)
    finish_reason: str | None = None

class OpenAIResponse(Struct):
    choices: list[OpenAIChoice] = []  # so as to automatically skip control messages
    model: str | None = None          # echoed to front-end when creating the synthetic OpenAIResponse
                                      # wrapper for structured output completion

class SseEvent(IntEnum):
    Message = auto()
    Unknown = auto()

logger = logging.getLogger("runner")
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

def _logOk(clientIP: str, runner: str, model: str):
    logger.info(f"{clientIP} | {runner}:{model}")

def _logInfo(clientIP: str, runner: str, model: str, errcode: int, msg: str):
    logger.info(f"{errcode} | {clientIP} | {runner}:{model} {msg} |")

def _logClientErr(clientIP: str, errcode: HTTPStatus, errmsg: str) -> PlainTextResponse:
    logger.warning(f"{errcode.value} | {clientIP} |")
    return PlainTextResponse(status_code=errcode, content=errmsg)

def _logServerErr(clientIP: str, errmsg: str) -> PlainTextResponse:
    logger.warning(f"{HTTPStatus.INTERNAL_SERVER_ERROR} | {clientIP} |")
    return PlainTextResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=errmsg)

# Setup-verification endpoint. Encoded once at import: the payload is constant,
# so there is nothing to serialize per request.
TOP = json.encode({"message": "UM EECS agentic harnessd"})

async def top(request: Request):
    return Response(TOP, media_type="application/json")

async def llmprompt(request: Request):
    clientIP = request.client.host if request.client else "Unknown"
    try:
        openAIRequest = json.decode(await request.body(), type=OpenAIRequest)
    except Exception:
        return _logClientErr(clientIP, HTTPStatus.BAD_REQUEST, "Invalid JSON body.")

    # forward prompt to LLM runner
    response = await _routePrompt(request, openAIRequest)
    if response is None:
        return _logClientErr(clientIP, HTTPStatus.SERVICE_UNAVAILABLE,
            "All available LLM providers are rate limited or offline.")
        
    # pass upstream body straight through.
    return StreamingResponse(response.aiter_bytes(), 
        headers= { "Content-Type": "text/event-stream" },
        background=BackgroundTask(response.aclose))
        
# performs the LlmRunners round-robin; returns the raw upstream Response
# on success (caller must close it), or None if all runners are exhausted.
async def _routePrompt(request: Request, openAIRequest: OpenAIRequest) -> Response | None: # passed by reference, no copy

    clientIP = request.client.host if request.client else "Unknown"
    
    #old # make a shallow copy using replace(), so as not to mod openAIRequest
    requestBody = structs.replace(openAIRequest, appID = UNSET)
    # strips appID, msgspec.json.encode() drops fields with value UNSET

    client = request.app.state.client
    runners = request.app.state.runners
    for runner in runners:
        # patch the "model" field with the model available for this runner,
        # if specified, else restore original model that came with request.
        requestBody.model = runner.model or openAIRequest.model

        headers = {"Content-Type": "application/json"}
        if runner.api.key:
            headers["Authorization"] = f"Bearer {runner.api.key}"

        try:
            # async with client.send( // NOT send()
            # https://www.python-httpx.org/async/
            # Cannot use `async with`, instead we will close the response manually in
            # a background task after streaming is done (https://stackoverflow.com/a/73736138)
            response = await client.send(
                # client.build_request allows us to stream the response safely
                client.build_request(
                    method=request.method,
                    url=f"{runner.api.url}/chat/completions",
                    headers=headers,
                    content=json.encode(requestBody),
                ), stream=True)

            # If rate limited or server error, continue advances the iterator
            if response.status_code != HTTPStatus.OK:
                _logInfo(clientIP, runner.api.url, runner.model, response.status_code, "Server error. Trying another one.")
                await response.aclose()  # cleanup: prevent client target connection leaks
                continue

            # Success! Return upstream response to caller
            _logOk(clientIP, runner.api.url, runner.model)
            return response

        except RequestError as e:
            # failover if network/connection error
            # user would have to deal with partial output if error mid-stream
            _logInfo(clientIP, runner.api.url, runner.model, HTTPStatus.PROCESSING,
                f"Connection error: {e}. Trying another one.")
            continue

    # If the for-loop naturally finishes without returning, we are exhausted.
    return None


async def llmsearch(request: Request):
    clientIP = request.client.host if request.client else "Unknown"
    try:
        openAIRequest = json.decode(await request.body(), type=OpenAIRequest)
    except ValidationError as err:
        return _logClientErr(clientIP, HTTPStatus.UNPROCESSABLE_ENTITY, f"Invalid request body: {err}")
    except DecodeError as err:
        return _logClientErr(clientIP, HTTPStatus.BAD_REQUEST, f"Malformed JSON body: {err}")

    if openAIRequest.stream is not True:
        return _logClientErr(clientIP, HTTPStatus.UNPROCESSABLE_ENTITY, "stream must be true")

    rwdb: aiosqlite.Connection = request.app.state.rwdb

    try:
        # save prompt to db in an atomic transaction
        turnID = (await rwdb.execute(
            "INSERT INTO turns (appID, prompt) VALUES (?, ?)",
            (openAIRequest.appID,
                openAIRequest.messages),
        )).lastrowid
    except Exception as e:
        return _logServerErr(clientIP, str(e))

    prompt = _promptPlaintext(openAIRequest.messages)[:MAX_RECALL_ITEM_CHARS]

    isStructured = not openAIRequest.response_format or bytes(openAIRequest.response_format) == b"null"
    try:
        
        # create recall block with the prompt for semantic search
        recall, historyFloor = await _recallBlock(request.app.state, rwdb,
            openAIRequest.appID, prompt)

        # reconstruct history, with the current prompt appended
        history = await _retrieveHistory(rwdb, openAIRequest.appID, historyFloor, turnID)

        # add recall block to the front of history, _recallMessage() will set "role: system" on the message
        if recall:
            history.insert(0, _recallMessage(recall)) # one memmove of N pointers

        # attach recall+history as context+prompt to openAIRequest
        openAIRequest.messages = Raw(json.encode(history))

        if isStructured:
            # retrieve JSON schema to be used with response_format
            openAIRequest.response_format = Raw(request.app.state.structured)
        # forward prompt to LLM runner (with response_format specified)
        response = await _routePrompt(request, openAIRequest)
        
    except Exception as e:
        try:
            await rwdb.execute("UPDATE turns SET completed = 0 WHERE turnID = ?", (turnID,))
        except Exception as degradeErr:
            print(f"turn {turnID} degrade write failed: {degradeErr}", file=sys.stderr)
        return _logServerErr(clientIP, str(e))

    # No available runner
    if response is None:
        try:
            await rwdb.execute("UPDATE turns SET completed = 0 WHERE turnID = ?", (turnID,))
        except Exception as degradeErr:
            print(f"turn {turnID} degrade write failed: {degradeErr}", file=sys.stderr)
        return _logClientErr(clientIP, HTTPStatus.SERVICE_UNAVAILABLE,
            "All available LLM providers are rate limited or offline.")

    acc = SseAccumulator()

    return EventSourceResponse(_yieldSse(response, acc, isStructured),
        headers= { "Content-Type": "text/event-stream" },
        background=BackgroundTask(_writeTurnResult, request.app.state, rwdb, turnID, acc, prompt))

def _isBusy(err: Exception) -> bool:
    return isinstance(err, sqlite3.OperationalError) and "database is locked" in str(err)

async def _writeTurnResult(state, rwdb: aiosqlite.Connection, turnID: int, acc: SseAccumulator, prompt: str) -> None:
    acc.completion.flushPending()
    acc.summary.flushPending()
    completion = "".join(acc.completion.text)
    summary = "".join(acc.summary.text)
    reasoning = "".join(acc.reasoning)
    completed = 1 if acc.finishReason == "stop" else 0
    for attempt in range(5):
        try:
            await rwdb.execute(
                "UPDATE turns SET completion = NULLIF(?, ''), summary = NULLIF(?, ''), reasoning = NULLIF(?, ''), completed = ? WHERE turnID = ?",
                (completion, summary, reasoning, completed, turnID),
            )
            break
        except Exception as e:
            if not _isBusy(e) or attempt == 4:
                print(f"turn {turnID} stream-end write failed: {e}", file=sys.stderr)
                return
                
    if completed == 1 and state.runners.embed is not None and state.vectorOptions is not None:
        text = summary.strip()
        if not text:
            if len(completion) > MAX_EMBED_ITEM_CHARS:
                print(f"turn {turnID}: no summary; embedding the first "
                      f"{MAX_EMBED_ITEM_CHARS} of {len(completion)} chars", file=sys.stderr)
            text = completion[:MAX_EMBED_ITEM_CHARS]

        if text and prompt:
            embedTask = asyncio.get_running_loop().create_task(
                _embedTurnText(state, turnID, text))
            _embedTasks.add(embedTask)
            embedTask.add_done_callback(_embedTasks.discard)

async def _embedTurnText(state, turnID: int, text: str) -> None:
    try:
        async with _embedGate:
            embedding = await _embedText(state, text)
        await state.rwdb.execute(
            "UPDATE turns SET embedding = ? WHERE turnID = ?",
            (_blobFromUnit(embedding), turnID),
        )
        state.snapshotDirty = True
    except Exception as e:
        print(f"turn embedding failed for turn {turnID}: {e}", file=sys.stderr)
        
class SseAccumulator(Struct):
    reasoning:     list[str] = field(default_factory=list)
    completion:    Capture    = field(default_factory=Capture)
    summary:       Capture    = field(default_factory=Capture)
    finishReason:  str | None = None
    model:         str | None = None
    lexer:         CompletionLexer = field(default_factory=CompletionLexer)

def _textPacket(text: str, model: str | None) -> str:
    packet: dict[str, object] = {"choices": [{"delta": {"content": text}}]}
    if model:
        packet["model"] = model
    return json.encode(packet).decode()

async def _yieldSse(
    response: Response,
    acc: SseAccumulator,
    isStructured: bool,
) -> AsyncGenerator[dict[str, str]]:
    sseEvent = SseEvent.Message
    eventName = ''
    accCompletion = acc.completion.text.append
    accReasoning = acc.reasoning.append    

    # incremental structured output decoding
    def sink(target: LexTarget, data: str) -> None:
        if target is LexTarget.Completion:
            acc.completion.push(data)
        else:
            acc.summary.push(data)

    try:
        async for line in response.aiter_lines():
            # delimiter ('\n') discarded from resulting line

            # SSE events are delimited by "\n\n"
            # new SSE event, default to Message
            if not line or line.isspace():
                sseEvent = SseEvent.Message
                eventName = ''
                continue
              
            # parse SSE line
            splitAt = line.find(":")
            if splitAt == -1: continue
            # separate out `tag: tagline` from the SSE line
            tag = line[:splitAt]
            tagline = line[splitAt + 1:]
            # drop the first leading space (per SSE spec)
            tagline = tagline.removeprefix(" ")

            # "tag" can only be "data" or "event"
            if tag == "data":
                
                # OpenAI's `/v1/chat/completions` uses "data: [DONE]"
                # to indicate end of stream
                if tagline == "[DONE]": continue

                # multiple data lines can belong to the same event
                if sseEvent == SseEvent.Message:

                    try:
                        openAIResponse = json.decode(tagline, type=OpenAIResponse)
                        suppressTagline = False
                        if openAIResponse.model:
                            acc.model = openAIResponse.model
                        if openAIResponse.choices:
                            choice = openAIResponse.choices[0]
                            if choice.finish_reason:
                                # terminal signal: providers send it on the final content
                                # chunk or a trailing empty-delta chunk; last write wins
                                acc.finishReason = choice.finish_reason
                            delta = choice.delta
                            if isStructured and delta.content:

                                suppressTagline = True
                                if acc.lexer.fallback:
                                    accCompletion(delta.content)
                                    yield {"data": _textPacket(delta.content, acc.model)}
                                else:
                                    mark = len(acc.completion.text)
                                    fell = acc.lexer.feed(delta.content, sink)
                                    spansEnd = len(acc.completion.text)

                                    if fell is not None:
                                        flushedBackslash = acc.completion.flushPending()
                                        acc.summary.flushPending()
                                        accCompletion(fell)

                                    if spansEnd > mark:
                                        yield {"data": _textPacket("".join(acc.completion.text[mark:spansEnd]), acc.model)}
                                    if fell is not None:
                                        if flushedBackslash:
                                            yield {"data": _textPacket("\\", acc.model)}
                                        yield {"event": "error", "data": json.encode("structured output schema violation; passing raw text through").decode()}
                                        yield {"data": _textPacket(fell, acc.model)}

                            else:

                                # the following three fields usage should be mutually exclusive
                                if delta.content:
                                    # assemble response tokens into full completion
                                    accCompletion(delta.content)
                                elif delta.reasoning_content:
                                    # some models (e.g., Qwen, Deepseek) stream their reasoning
                                    accReasoning(delta.reasoning_content)
                                elif delta.reasoning:
                                    accReasoning(delta.reasoning)

                        # convey LLM completion stream to client:
                        # yield clean SSE event (key:value line)  
                        if not suppressTagline:
                            yield {"data": tagline}
                    except Exception as e:
                        yield {"event": "error", "data": json.encode(str(e)).decode()}

                else:
                    # silent passthrough non-Message events, should not happen with
                    # /v1/chat/completions API; support for other APIs will likely
                    # require more extensive support for non-Message events.
                    yield {"event": eventName, "data": tagline}
            
            elif tag == "event":
                eventName = tagline
                match eventName:
                    case "message" | "Message" | "MESSAGE":
                        sseEvent = SseEvent.Message
                    case _:
                        sseEvent = SseEvent.Unknown
            
        # withheld backslash from any split escape flushes when the stream ends
        if acc.completion.flushPending():
            yield {"data": _textPacket("\\", acc.model)}
        acc.summary.flushPending()
    except httpx.HTTPError as e:
        # flush any withheld escape backslash first before the error
        if acc.completion.flushPending():
            yield {"data": _textPacket("\\", acc.model)}
        acc.summary.flushPending()
        # yield upstream read fail as SSE error event
        yield {"event": "error", "data": json.encode(f"upstream read failed: {e}").decode()}
    finally:
        await response.aclose()

class Turn(Struct):
    turnID:     int
    prompt:     bytes
    reasoning:  str | None
    completion: str | None

async def _retrieveHistory(rwdb: aiosqlite.Connection, appID: str, minTurnID: int, currentTurnID: int) -> list[Raw]:

    async with rwdb.execute(
        "SELECT turnID, length(prompt) + COALESCE(length(reasoning), 0) + COALESCE(length(completion), 0)"
        " FROM turns"
        " WHERE appID = ? AND turnID >= ? AND (turnID = ? OR completed = 1)"
        " ORDER BY turnID ASC",
        (appID, minTurnID, currentTurnID)
    ) as cur:
        sizes = list(await cur.fetchall())

    total = sum(size for _, size in sizes)
    drop = 0
    while drop + 1 < len(sizes) and total > MAX_HISTORY_BYTES:
        total -= sizes[drop][1]
        drop += 1

    survivors = [row[0] for row in sizes[drop:]]
    async with rwdb.execute(
        "SELECT turnID, prompt, reasoning, completion FROM turns"
        " WHERE turnID IN (SELECT value FROM json_each(?))"
        " ORDER BY turnID ASC",
        (json.encode(survivors).decode(),)
    ) as cur:
        turns = [Turn(*row) for row in await cur.fetchall()]

    history: list[Raw] = []
    for turn in turns:
        
        if turn.prompt:
            try:
                history.extend(json.decode(turn.prompt, type=list[Raw]))
            except DecodeError:
                pass

        if turn.completion or turn.reasoning:
            content = (turn.reasoning + "\n\n" + turn.completion) if turn.reasoning and turn.completion else (turn.completion or turn.reasoning)
            history.append(Raw(json.encode(Message(role="assistant", content=content))))

    return history
