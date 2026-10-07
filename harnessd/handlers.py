from __future__ import annotations # must be the first line of the file
import aiosqlite
from collections.abc import AsyncGenerator
from enum import IntEnum, auto
from sse_starlette.sse import EventSourceResponse

from http import HTTPStatus
import httpx
from httpx import RequestError, Response
import logging
import msgspec
from msgspec import Raw, Struct, field, json, structs, UNSET, UnsetType
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response, StreamingResponse
from toolbox import OpenAIToolSchema, getWeather

class OpenAIFunction(Struct, omit_defaults=True):
	name:      str | None = None
	arguments: str | None = None

class OpenAIToolCall(Struct, kw_only=True):
	id:       str
	type:     str = "function"
	function: OpenAIFunction

class Message(Struct, omit_defaults=True):
	role: str
	content: str | None = None
	tool_calls: list[OpenAIToolCall] | None = None
	tool_call_id: str | None = None

class OpenAIRequest(Struct, omit_defaults=True):
	appID:    str | UnsetType
	model: str
	messages: Raw
	stream: bool = False
	turnID: int | UnsetType = UNSET
	max_tokens: int | None = None
	tools: Raw | UnsetType = UNSET

class WeatherRequest(Struct):
	lat: str
	lon: str

class ToolCallDelta(Struct, kw_only=True):
    index:    int = 0
    id:       str | None = None
    function: OpenAIFunction | None = None

class OpenAIDelta(Struct):
    content:           str | None = None
    reasoning:         str | None = None
    reasoning_content: str | None = None
    tool_calls:        list[ToolCallDelta] | None = None

class OpenAIChoice(Struct):
    delta:         OpenAIDelta = field(default_factory=OpenAIDelta)

class OpenAIResponse(Struct):
    choices: list[OpenAIChoice] = []

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
    requestBody = structs.replace(openAIRequest, appID = UNSET, turnID = UNSET)
    # strips appID and turnID, msgspec.json.encode() drops fields with value UNSET

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


async def llmchat(request: Request):
    clientIP = request.client.host if request.client else "Unknown"
    try:
        openAIRequest = json.decode(await request.body(), type=OpenAIRequest)
    except Exception:
        return _logClientErr(clientIP, HTTPStatus.BAD_REQUEST, "Invalid JSON body.")

    rwdb = request.app.state.rwdb

    try:
        # save prompt to db in an atomic transaction
        async with rwdb.cursor() as cur:
            await cur.execute(
                "INSERT INTO turns (appID, prompt) VALUES (?, ?)",
                (openAIRequest.appID,
                    openAIRequest.messages),
            )
            turnID = cur.lastrowid
    except Exception as e:
        return _logClientErr(clientIP, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    try:
        # reconstruct openAIRequest to be sent to LLM runner--add context:
        # retrieve all messages belonging to appID and
        # insert them as one Messages array of openAIRequest.messages
        history = await _retrieveHistory(rwdb, openAIRequest.appID)
        openAIRequest.messages = Raw(json.encode(history))
    except Exception as e:
        return _logClientErr(clientIP, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    # forward prompt to LLM runner
    response = await _routePrompt(request, openAIRequest)
    if response is None:
        return _logClientErr(clientIP, HTTPStatus.SERVICE_UNAVAILABLE,
            "All available LLM providers are rate limited or offline.")

    async def _conveyCompletion(response: Response) -> AsyncGenerator[dict[str, str]]:

        # accumulate completion (and reasoning) tokens and forward token stream to front-end agent
        acc = SseAccumulator()
        async for event in _yieldSse(response, acc):
            yield event # convey LLM completion stream to client

        # after the stream ends, save the accumulated completion
        completion = "".join(acc.tokens)
        reasoning = "".join(acc.reasoning)
        if completion or reasoning:
            try:
                async with rwdb.cursor() as cur:
                    await cur.execute(
                        "UPDATE turns SET completion = NULLIF(?, ''), reasoning = CASE WHEN ? = '' THEN reasoning ELSE COALESCE(reasoning || ' ', '') || ? END WHERE turnID = ?",
                        (completion, reasoning, reasoning, turnID),
                    )
            except Exception as e:
                yield {"event": "error", "data": json.encode(str(e)).decode()}

    return EventSourceResponse(_conveyCompletion(response),
        headers= { "Content-Type": "text/event-stream" })

async def llmclear(request: Request):
    clientIP = request.client.host if request.client else "Unknown"
    try:
        openAIRequest = json.decode(await request.body(), type=OpenAIRequest)
    except Exception:
        return _logClientErr(clientIP, HTTPStatus.BAD_REQUEST, "Invalid JSON body.")

    rwdb = request.app.state.rwdb
    try:
        async with rwdb.cursor() as cur:
            # calls reference turns without ON DELETE CASCADE
            await cur.execute("DELETE FROM calls WHERE turnID IN (SELECT turnID FROM turns WHERE appID = ?)", (openAIRequest.appID,))
            await cur.execute("DELETE FROM turns WHERE appID = ?", (openAIRequest.appID,))
    except Exception as e:
        return _logClientErr(clientIP, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    _logOk(clientIP, "llmclear", openAIRequest.appID if isinstance(openAIRequest.appID, str) else "")
    return PlainTextResponse(status_code=HTTPStatus.OK, content="")

class SseAccumulator(Struct):
    reasoning:     list[str] = field(default_factory=list)
    tokens:        list[str] = field(default_factory=list)
    parallelCalls: dict[int, OpenAIToolCall] = field(default_factory=dict)

    def clear(self):
        self.reasoning.clear()
        self.tokens.clear()
        self.parallelCalls.clear()

def _assembleToolCall(parallelCalls: dict[int, OpenAIToolCall], delta: ToolCallDelta) -> None:
    call = parallelCalls.get(delta.index)
    if call is None:
        call = OpenAIToolCall(id=delta.id or "", function=OpenAIFunction())
        parallelCalls[delta.index] = call
    if delta.id and not call.id:
        call.id = delta.id
    if delta.function is not None:
        if delta.function.name and not call.function.name:
            call.function.name = delta.function.name
        if delta.function.arguments:
            call.function.arguments = (call.function.arguments or "") + delta.function.arguments

async def _yieldSse(
    # yield clean SSE event (key:value line) to agent, accumulate content deltas
    # and assemble tool call deltas.
    response: Response,
    acc: SseAccumulator,
) -> AsyncGenerator[dict[str, str]]:
    sseEvent = SseEvent.Message
    eventName = ''
    accTokens = acc.tokens.append
    accReasoning = acc.reasoning.append

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
                        # OpenAI's `/v1/chat/completions` API requires that
                        # a serialized JSON object follows a `data:` tag.
                        openAIResponse = json.decode(tagline, type=OpenAIResponse)
                        if openAIResponse.choices:
                            # OpenAI defaults to generating only one completion choice
                            # when the 'n' parameter is not included in OpenAIRequest
                            delta = openAIResponse.choices[0].delta
                            # the following three fields usage should be mutually exclusive
                            if delta.content:
                                # assemble response tokens into full completion
                                accTokens(delta.content)
                            elif delta.reasoning_content:
                                # some models (e.g., Qwen, Deepseek) stream their reasoning
                                accReasoning(delta.reasoning_content)
                            elif delta.reasoning:
                                accReasoning(delta.reasoning)
                            if delta.tool_calls:
                                for toolCall in delta.tool_calls:
                                    _assembleToolCall(acc.parallelCalls, toolCall)
                    except Exception as e:
                        yield {"event": "error", "data": json.encode(str(e)).decode()}

                    # convey LLM completion stream to client:
                    # yield clean SSE event (key:value line)
                    yield {"data": tagline}

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
            
    finally:
        await response.aclose()

class Turn(Struct):
    turnID:     int
    prompt:     bytes
    reasoning:  str | None
    completion: str | None

class Call(Struct):
    turnID:    int
    id:        str
    name:      str
    arguments: str
    result:    str | None

async def _retrieveHistory(rwdb: aiosqlite.Connection, appID: str) -> list[Message]:
    # retrieve full message history by appID, ordered by insertion,
    # push them all into one Message array and return it
    async with rwdb.execute(
        "SELECT turnID, prompt, reasoning, completion FROM turns WHERE appID = ? ORDER BY turnID ASC",
        (appID,)
    ) as cur:
        turns = [Turn(*row) for row in await cur.fetchall()]

    async with rwdb.execute(
        "SELECT turnID, id, name, arguments, result FROM calls "
        "WHERE turnID IN (SELECT turnID FROM turns WHERE appID = ?) ORDER BY turnID ASC, idx ASC",
        (appID,)
    ) as cur:
        calls = [Call(*row) for row in await cur.fetchall()]

    # create Messages array from prompt messages and reasoning and completion if present
    history: list[Message] = []
    callsEnd = 0
    for turn in turns:
        if turn.prompt: # deserialize prompt into Message array and pushed to history
            history.extend(json.decode(turn.prompt, type=list[Message]))

        callsStart = callsEnd
        while callsEnd < len(calls) and calls[callsEnd].turnID == turn.turnID:
            callsEnd += 1

        if callsEnd > callsStart:
            turnCalls = calls[callsStart:callsEnd]
            history.append(Message(role="assistant", content=turn.reasoning or "",
                tool_calls=[OpenAIToolCall(id=call.id,
                    function=OpenAIFunction(name=call.name, arguments=call.arguments))
                    for call in turnCalls]))
            for call in turnCalls:
                if call.result is not None:
                    history.append(Message(role="tool", content=call.result, tool_call_id=call.id))
            if turn.completion:
                history.append(Message(role="assistant", content=turn.completion))
        elif turn.completion:
            # if reasoning present, prepend it to completion
            content = (turn.reasoning + "\n\n" + turn.completion) if turn.reasoning else turn.completion
            history.append(Message(role="assistant", content=content))
        # else, current turn, no assistant reply yet, not an error
    return history

async def _upsertAgentTools(rwdb: aiosqlite.Connection, appID: str, tools: Raw | UnsetType) -> list[OpenAIToolSchema]:
    if tools is not UNSET:
        agentTools = json.decode(tools, type=list[OpenAIToolSchema] | None)
        await rwdb.execute(
            "INSERT INTO tools (appID, schemas) VALUES (?, ?) "
            "ON CONFLICT (appID) DO UPDATE SET schemas = excluded.schemas, timestamp = unixepoch()",
            (appID, tools))
        return agentTools

    async with rwdb.execute("SELECT schemas FROM tools WHERE appID = ?", (appID,)) as cur:
        row = await cur.fetchone()
    if not row or row[0] is None:
        return []
    try:
        return json.decode(row[0], type=list[OpenAIToolSchema])
    except Exception:
        return []

async def weather(request: Request):
    clientIP = request.client.host if request.client else "Unknown"
    try:
        coords = json.decode(await request.body(), type=WeatherRequest)
    except Exception:
        return _logClientErr(clientIP, HTTPStatus.BAD_REQUEST, "Invalid JSON body.")

    result, error = await getWeather(request.app.state, [coords.lat, coords.lon])
    if result is None:
        return _logClientErr(clientIP, HTTPStatus.BAD_GATEWAY, error or "No weather result.")
    return PlainTextResponse(result)

async def llmtools(request: Request):
    clientIP = request.client.host if request.client else "Unknown"
    try:
        openAIRequest = json.decode(await request.body(), type=OpenAIRequest)
    except Exception as err:
        return _logClientErr(clientIP, HTTPStatus.BAD_REQUEST, f"Invalid JSON body: {err}")

    rwdb = request.app.state.rwdb
    toolbox = request.app.state.toolbox

    # tool results from the frontend, or a new prompt
    try:
        if openAIRequest.turnID is not UNSET and openAIRequest.turnID > 0:
            turnID = openAIRequest.turnID
            for msg in json.decode(openAIRequest.messages, type=list[Message]):
                if msg.role == "tool" and msg.tool_call_id:
                    await rwdb.execute("UPDATE calls SET result = ? WHERE id = ?",
                        (msg.content, msg.tool_call_id))
        else:
            async with rwdb.cursor() as cur:
                await cur.execute("INSERT INTO turns (appID, prompt) VALUES (?, ?)",
                    (openAIRequest.appID, openAIRequest.messages))
                turnID = cur.lastrowid
    except Exception as e:
        return _logClientErr(clientIP, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    agentTools = await _upsertAgentTools(rwdb, openAIRequest.appID, openAIRequest.tools)
    history = await _retrieveHistory(rwdb, openAIRequest.appID)
    openAIRequest.tools = Raw(json.encode(toolbox.schemas() + agentTools))

    async def _conveyCompletion() -> AsyncGenerator[dict[str, str]]:
        sendNewPrompt = True
        acc = SseAccumulator()

        while sendNewPrompt:
            sendNewPrompt = False
            openAIRequest.messages = Raw(json.encode(history))

            response = await _routePrompt(request, openAIRequest)
            if response is None:
                yield {"event": "error", "data": json.encode("All available LLM providers are rate limited or offline.").decode()}
                return

            acc.clear()
            async for event in _yieldSse(response, acc):
                yield event

            completion = "".join(acc.tokens)
            reasoning = "".join(acc.reasoning)

            if not acc.parallelCalls:
                if completion or reasoning:
                    try:
                        async with rwdb.cursor() as cur:
                            await cur.execute(
                                "UPDATE turns SET completion = NULLIF(?, ''), reasoning = CASE WHEN ? = '' THEN reasoning ELSE COALESCE(reasoning || ' ', '') || ? END WHERE turnID = ?",
                                (completion, reasoning, reasoning, turnID),
                            )
                    except Exception as e:
                        yield {"event": "error", "data": json.encode(str(e)).decode()}
                return

            try:
                for idx, call in acc.parallelCalls.items():
                    await rwdb.execute(
                        "INSERT INTO calls (turnID, id, idx, name, arguments) VALUES (?, ?, ?, ?, ?)",
                        (turnID, call.id, idx, call.function.name or "", call.function.arguments or ""))

                if not acc.tokens:
                    reasoning = "".join(acc.reasoning)
                elif not acc.reasoning:
                    reasoning = "".join(acc.tokens)
                else:
                    reasoning = "".join(acc.tokens) + "".join(acc.reasoning)

                if reasoning:
                    await rwdb.execute(
                        "UPDATE turns SET reasoning = COALESCE(reasoning || ' ', '') || ? WHERE turnID = ?",
                        (reasoning, turnID))
            except Exception as e:
                yield {"event": "error", "data": json.encode(str(e)).decode()}
                return

            sendNewPrompt = True
            history.append(Message(role="assistant", content=reasoning,
                tool_calls=list(acc.parallelCalls.values())))

            agentToolCalls = []
            for call in acc.parallelCalls.values():
                toolResult, toolErr = await toolbox.invoke(request.app.state, call.function)

                if toolResult is None and toolErr is None:
                    # non-resident tool
                    agentToolCalls.append({"id": call.id, "function": {
                        "name": call.function.name, "arguments": call.function.arguments}})
                    sendNewPrompt = False
                    continue

                result = toolErr if toolErr is not None else toolResult
                if not result:
                    yield {"event": "error", "data": f'"{call.function.name}: invalid result"'}
                    return

                try:
                    await rwdb.execute("UPDATE calls SET result = ? WHERE id = ?", (result, call.id))
                except Exception as e:
                    yield {"event": "error", "data": json.encode(str(e)).decode()}
                    return

                if sendNewPrompt:
                    history.append(Message(role="tool", content=result, tool_call_id=call.id))

            if not sendNewPrompt:
                yield {"event": "tool_calls", "data": json.encode(
                    {"turnID": turnID, "calls": agentToolCalls}).decode()}

    return EventSourceResponse(_conveyCompletion(),
        headers= { "Content-Type": "text/event-stream" })
