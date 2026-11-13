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
from msgspec import DecodeError, Raw, Struct, field, json, structs, UNSET, UnsetType
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import Response as Reply, PlainTextResponse, StreamingResponse
from google.oauth2 import id_token
import secrets
from starlette.concurrency import run_in_threadpool
import time

class OpenAIFunction(Struct, omit_defaults=True):
    name:      str | None = None
    arguments: str | None = None    # arguments are streamed as tokens across deltas

# kw_only=True stops type check complaining about ordering of fields with default values
class OpenAIToolCall(Struct, kw_only=True):
    id:       str
    type:     str = "function"    
    function: OpenAIFunction

class Message(Struct, omit_defaults=True):
    role: str
    content: str | None
    tool_calls: list[OpenAIToolCall] | None = None
    tool_call_id: str | None = None    # must match result with call

class OpenAIRequest(Struct, omit_defaults=True, kw_only=True):
    appID:    str | UnsetType
    model:    str
    max_tokens: int | None = None   # don't cut off reasoning stream
    messages: Raw
    stream:   bool = False
    
    turnID:   int | UnsetType = UNSET       # NULL/0 or must match tool result with turnID of call
    tools: Raw | UnsetType = UNSET          # for list[OpenAIToolSchema]     

class ToolCallDelta(Struct, kw_only=True):
    index: int = 0         # for parallel tool calls
    id: str | None = None  # must be echoed as tool_call_id in result message
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

class AgentAuth(Struct):
    clientID: str
    idToken: str

class WeatherRequest(Struct):
	lat: str
	lon: str


logger = logging.getLogger("runner")
logging.basicConfig(level=logging.INFO) # Ensures WARNING logs go to standard output
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

async def llmprompt(request: Request):
    clientIP = request.client.host if request.client else "Unknown"
    try:
        openAIRequest = json.decode(await request.body(), type=OpenAIRequest)
    except DecodeError as err:
        return _logClientErr(clientIP, HTTPStatus.UNPROCESSABLE_ENTITY, f"Invalid JSON body: {err}")

    # forward prompt to LLM runner
    response = await _routePrompt(request, openAIRequest)
    if response is None:
        return _logClientErr(clientIP, HTTPStatus.SERVICE_UNAVAILABLE,
            "All available LLM providers are rate limited or offline.")
        
    # pass upstream body straight through.
    return StreamingResponse(response.aiter_raw(), 
        headers= { "Content-Type": "text/event-stream" },
        background=BackgroundTask(response.aclose))
        

# performs the LlmRunners round-robin; returns the raw upstream Response
# on success (caller must close it), or None if all runners are exhausted.
async def _routePrompt(request: Request, openAIRequest: OpenAIRequest) -> Response | None: # passed by reference, no copy

    clientIP = request.client.host if request.client else "Unknown"
    
    # make a shallow copy using replace(), so as not to mod openAIRequest
    requestBody = structs.replace(openAIRequest, appID = UNSET, turnID = UNSET)

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
                    url=f"{runner.api.url}/v1/chat/completions",
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
    except DecodeError as err:
        return _logClientErr(clientIP, HTTPStatus.UNPROCESSABLE_ENTITY, f"Invalid JSON body: {err}")

    rwdb = request.app.state.rwdb

    try:
        # save prompt to db in an atomic transaction
        turnID = (await rwdb.execute(
            "INSERT INTO turns (appID, prompt) VALUES (?, ?)",
            (openAIRequest.appID, # None, # for testing SSE error event
                openAIRequest.messages),
        )).lastrowid
    except Exception as e:
        return _logServerErr(clientIP, str(e))

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
                await rwdb.execute(
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
            await cur.execute("DELETE FROM tools WHERE appID = ?", (openAIRequest.appID,))
    except Exception as e:
        return _logClientErr(clientIP, HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    _logOk(clientIP, "llmclear", openAIRequest.appID if isinstance(openAIRequest.appID, str) else "")
    return PlainTextResponse(status_code=HTTPStatus.OK, content="")


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
        "SELECT turnID, id, name, arguments, result FROM calls"
        " WHERE turnID IN (SELECT turnID FROM turns WHERE appID = ?)"
        " ORDER BY turnID ASC, idx ASC",
        (appID,)
    ) as cur:
        calls = [Call(*row) for row in await cur.fetchall()]

    calls_end_idx = 0

    # create Messages array from prompt messages and reasoning and completion if present
    history: list[Message] = []
    for turn in turns:
        if turn.prompt: # deserialize prompt into Message array and pushed to history
            history.extend(json.decode(turn.prompt, type=list[Message]))

        calls_start_idx = calls_end_idx
        while calls_end_idx < len(calls) and calls[calls_end_idx].turnID == turn.turnID:
            calls_end_idx += 1
        if calls_end_idx > calls_start_idx:
            turnCalls = calls[calls_start_idx:calls_end_idx]
        
            #if turnCalls:
            # if there are any tool calls: extract the calls of this turn 
            # into a tool calls array.  
            toolCalls = [OpenAIToolCall(id=call.id, function=OpenAIFunction(name=call.name, arguments=call.arguments)) for call in turnCalls]

            # push assistant message declaring the tool calls into history (FIRST, by API)
            # collect tool call reasoning if present
            history.append(Message(role="assistant", content=turn.reasoning or "", tool_calls=toolCalls))

            # then extract tool results and append them to history
            for call in turnCalls:
                if call.result is not None:
                    history.append(Message(role="tool", content=call.result, tool_call_id=call.id))

        if turn.completion:
            # if reasoning present, prepend it to completion
            content = (turn.reasoning + "\n\n" + turn.completion) if turn.reasoning else turn.completion
            history.append(Message(role="assistant", content=content))
        # else, current turn, no assistant reply yet, not an error
    return history
    

class SseAccumulator(Struct):
    reasoning:     list[str] = field(default_factory=list)
    tokens:        list[str] = field(default_factory=list)
    parallelCalls: dict[int, OpenAIToolCall] = field(default_factory=dict) 

    def clear(self):
        self.reasoning.clear()
        self.tokens.clear()
        self.parallelCalls.clear() # retains capacity   

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

                        # convey LLM completion stream to client:
                        # yield clean SSE event (key:value line) 
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
            
    finally:
        await response.aclose()            

def _assembleToolCall(parallelCalls: dict[int, OpenAIToolCall], delta: ToolCallDelta) -> None:
    # look for call in array; if not found, allocate a new entry
    call = parallelCalls.get(delta.index)
    if call is None:
        # new entry
        call = OpenAIToolCall(id=delta.id or "", function=OpenAIFunction())
        parallelCalls[delta.index] = call

    if delta.id and not call.id:
        # sometimes the call ID arrives in a later delta, just store it
        call.id = delta.id

    if delta.function is not None:
        if delta.function.name and not call.function.name:
            # populate call with function name
            # allow for this to also be in later deltas
            call.function.name = delta.function.name
        
        if delta.function.arguments:
            # accumulate arguments across deltas.
            call.function.arguments = (call.function.arguments or "") + delta.function.arguments

from toolbox import OpenAIToolSchema    # workaround circular import

async def _upsertAgentTools(rwdb: aiosqlite.Connection, appID: str, tools: Raw | UnsetType) -> list[OpenAIToolSchema]:
    # REQUIREMENT 1: "tools != None, UPSERT the current tool set"
    if tools is not UNSET:
        # REQUIREMENT 2: "map [] to NULL (stale marker), see REQ 4.2 below"    
        agentTools: list[OpenAIToolSchema] | None = json.decode(tools, type=list[OpenAIToolSchema] | None )

        # upsert current tool set (maybe [], used to clear tools)
        await rwdb.execute(
            """
            INSERT INTO tools (appID, schemas) 
            VALUES (?, ?)
            ON CONFLICT (appID) DO UPDATE SET 
                schemas = excluded.schemas,
                timestamp = unixepoch()
            """,
            (appID, tools),
        )
        # returns current set of tools (maybe [], to clear tools)        
        return agentTools

    # REQUIREMENT 3: "if (tools == None), return the existing row."            
    row = await (await rwdb.execute("SELECT schemas FROM tools WHERE appID = ?", (appID,))).fetchone()

    # REQUIREMENT 4: "Returns [] if appID has never registered."
    if not row or row[0] is None:
        # 1. If the row doesn't exist, returns `[]`.
        # 2. If the row exists but `schemas` is NULL, returns `[]`.
        return []
    try:
        # 3. Otherwise, it parses the JSON string back into an `OpenAIToolSchema[]`.    
        return json.decode(row[0], type=list[OpenAIToolSchema])
    except Exception:
        return []
from toolbox import getWeather

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


async def addagent(request):
    clientIP = request.client.host if request.client else "Unknown"
    try:
        agentAuth = json.decode(await request.body(), type=AgentAuth)
    except DecodeError as err:
        return _logClientErr(clientIP, HTTPStatus.UNPROCESSABLE_ENTITY, f"Invalid JSON body: {err}")

    try: 
        # https://developers.google.com/identity/sign-in/ios/backend-auth#python
        # Collect user info from the Google idToken, verify_oauth2_token checks
        # the integrity of idToken and throws a "ValueError" if idToken or
        # clientID is corrupted or if user has been disconnected from Google
        # OAuth (requiring user to log back in to Google).
        # idToken has a lifetime of about 1 hour
        # Must have clock_skew_in_seconds=50, else python gets "token used too early"
        # Offload synchronous Google verification to threadpool to prevent blocking Granian.
        idInfo = await run_in_threadpool(
            id_token.verify_oauth2_token,
            agentAuth.idToken,              # validate user's idToken
            request.app.state.googleJWKS,
            audience=agentAuth.clientID,    # validate Google client the idToken was issued to
            clock_skew_in_seconds=50
        )
    except ValueError:
        return _logClientErr(clientIP, HTTPStatus.UNAUTHORIZED, "Unauthorized")   

    # create ticket
    creator = idInfo.get('name', 'Profile NA')
    ticket = secrets.token_hex(32)

    now = int(time.time()) 
    lifetime = min((idInfo['exp'] - now) + 1, 180) # secs, up to max of 1800, idToken lifetime

    # insert ticket to database
    rwdb: aiosqlite.Connection = request.app.state.rwdb
    try:
        # clean up tickets table at most once every 5 minutes
        #async with rwdb.execute('SELECT COUNT(*) FROM tickets WHERE ? > (expiration + 300)', (now,)) as cur:
        #    row = await cur.fetchone()
        row = await (await rwdb.execute('SELECT COUNT(*) FROM tickets WHERE ? > (expiration + 300)', (now,))).fetchone()
        expired = row[0] if row else 0

        # if 10 or more entries have been stale for > 5 mins, run the greedy DELETE
        if expired > 10:
            await rwdb.execute('DELETE FROM tickets WHERE ? > expiration', (now,))

	    # insert ticket to database
        await rwdb.execute(
            'INSERT INTO tickets (ticket, creator, expiration) VALUES (?, ?, ?)', 
            (ticket, creator, now + lifetime)
        )

        # return ticket, creator, lifetime 
        return Reply(json.encode({
            'ticket': ticket, 
            'creator': creator, 
            'lifetime': lifetime
        }), media_type="application/json")
        
    except Exception as e:
        return _logServerErr(clientIP, str(e))

async def llmtools(request: Request):

    clientIP = request.client.host if request.client else "Unknown"
    try:
        openAIRequest = json.decode(await request.body(), type=OpenAIRequest)
    except DecodeError as err:
        return _logClientErr(clientIP, HTTPStatus.UNPROCESSABLE_ENTITY, f"Invalid JSON body: {err}")

    rwdb: aiosqlite.Connection = request.app.state.rwdb
    toolbox = request.app.state.toolbox

    # insert prompt into database or update existing database with tool result
    try:
        if openAIRequest.turnID is not UNSET and openAIRequest.turnID > 0:
            # request carries result(s) for non-resident tool call(s) made at turn turnID,
            # the turnID was forwarded to the agent along with the non-resident tool call(s)
            # and is now echoed back along with the result(s)
            turnID = openAIRequest.turnID

            # ownership gate: the echoed turnID is client-controlled, so verify it
            # belongs to this appID before any write keys on it
            row = await (await rwdb.execute(
                "SELECT appID FROM turns WHERE turnID = ?", (turnID,),
            )).fetchone()
            if row is None:
                return _logClientErr(clientIP, HTTPStatus.NOT_FOUND, f"unknown turn {turnID}")
            if row[0] != openAIRequest.appID:
                return _logClientErr(clientIP, HTTPStatus.FORBIDDEN,
                    f"turn {turnID} does not belong to app {openAIRequest.appID}")
            
            messages = json.decode(openAIRequest.messages, type=list[Message])
            for msg in messages:
                if msg.role == "tool" and msg.tool_call_id:
                    await rwdb.execute(
                        "UPDATE calls SET result = ? WHERE id = ? AND turnID = ?",
                        (msg.content, msg.tool_call_id, turnID),    # both content and tool_call_id must be valid for the LLM
                    )
        else:
            # a new prompt, not carrying any tool call result
            turnID = (await rwdb.execute(
                "INSERT INTO turns (appID, prompt) VALUES (?, ?)",
                (openAIRequest.appID, openAIRequest.messages),
            )).lastrowid
    except Exception as e:
        return _logServerErr(clientIP, str(e))

    # save non-resident tools
    agentTools = await _upsertAgentTools(rwdb, openAIRequest.appID, openAIRequest.tools)

    history = await _retrieveHistory(rwdb, openAIRequest.appID)

    openAIRequest.tools = Raw(json.encode(toolbox.schemas() + agentTools))
 
    # convey completion
    async def _conveyCompletion() -> AsyncGenerator[dict[str, str], None]:
        sendNewPrompt = True
        acc = SseAccumulator()

        while sendNewPrompt:
            sendNewPrompt = False

            openAIRequest.messages = Raw(json.encode(history))        

            response = await _routePrompt(request, openAIRequest) # body)
            if response is None:
                yield {"event": "error", "data": json.encode("All available LLM providers are rate limited or offline.").decode()}
                return

            # accumulate completion or tool call (and reasoning) tokens and forward token stream to front-end agent
            acc.clear()
            async for event in _yieldSse(response, acc):
                yield event

            # stream ended
            completion = "".join(acc.tokens)
            reasoning = "".join(acc.reasoning)
            if acc.parallelCalls:
                # there's a tool call!
                try:
                    for idx, call in acc.parallelCalls.items():
                        # save tool call to db
                        await rwdb.execute(
                            "INSERT INTO calls (turnID, id, idx, name, arguments) VALUES (?, ?, ?, ?, ?)",
                            (turnID, call.id, idx, call.function.name or "", call.function.arguments or ""),
                        )

                    # save any reasoning associated with tool call
                    if not acc.tokens:
                        reasoning = "".join(acc.reasoning)
                    elif not acc.reasoning:
                        reasoning = "".join(acc.tokens)
                    else:
                        reasoning = "".join(acc.tokens) + "".join(acc.reasoning)                        
                    if reasoning:
                        await rwdb.execute(
                            "UPDATE turns SET reasoning = COALESCE(reasoning || ' ', '') || ? WHERE turnID = ?",
                            (reasoning, turnID),
                        )
                except Exception as e:
                    yield {"event": "error", "data": json.encode(str(e)).decode()}
                    return

                # handle tool call
                sendNewPrompt = True # assume only resident tool calls
                # **opportunistically** prepare request to be posted
                # to LLM with resident tool result(s) 
                toolCalls = list(acc.parallelCalls.values())
                assistantMsg = Message(role="assistant", content=reasoning, tool_calls=toolCalls)
                history.append(assistantMsg)

                # make the tool calls!
                agentToolCalls = []
                for call in acc.parallelCalls.values():
                    # invoke individual tool call
                    toolResult, toolErr = await toolbox.invoke(request.app.state, call.function)
                    if toolResult is None and toolErr is None:
                        # tool non-resident, need to forward to front-end agent
                        agentToolCalls.append({"id": call.id, "function": {"name": call.function.name, "arguments": call.function.arguments}})
                        sendNewPrompt = False
                        continue

                    result = toolErr if toolErr is not None else toolResult
                    if not result:
                        yield {"event": "error", "data": f'"{call.function.name}: invalid toolResult: cannot be null or an empty string."'}                        
                        return
                        
                    try:
                        # save resident tool call result or error
                        # turnID guard makes client spoofing impossible, predicated upon
                        # the LLM provider not reusing a call id within one turn
                        await rwdb.execute(
                            "UPDATE calls SET result = ? WHERE id = ? AND turnID = ?",
                            (result, call.id, turnID),
                        )                        
                    except Exception as e:
                        yield {"event": "error", "data": json.encode(str(e)).decode()}
                        return

                    # if only resident tool calls so far . . .
                    if sendNewPrompt:
                        # **opportunistically** prepare this resident tool result
                        # and append it to the request to be posted to LLM
                        toolMsg = Message(role="tool", content=result, tool_call_id=call.id)
                        history.append(toolMsg)
                        
                if not sendNewPrompt:
                    # Some tools were non-resident, forward to front-end agent, along
                    # with the current turn's turnID. Earlier we stored resident tool 
                    # results in db, they just stay there for now. All **opportunistic** 
                    # work to prepare posting response to LLM wasted, oh well.
                    # 
                    # At some point, the agent will post non-resident tool results, tagged with the
                    # turnID of the current turn. At that time, we look up current turn's resident
                    # tool results and append them to the incoming request before posting it to the
                    # LLM. 
                    yield {"event": "tool_calls", "data": json.encode({"turnID": turnID, "calls":
                    agentToolCalls}).decode()}

                # else: all resident — **opportunistic** work paid off.
                # loop continues and sends resident tool results, with the current turnID

            else:
                # there's no tool call
                if completion or reasoning:
                    try:
                        # save the accumulated completion
                        await rwdb.execute(
                            "UPDATE turns SET completion = NULLIF(?, ''), reasoning = CASE WHEN ? = '' THEN reasoning ELSE COALESCE(reasoning || ' ', '') || ? END WHERE turnID = ?",
                            (completion, reasoning, reasoning, turnID),
                        )                                            
                    except Exception as e:
                        yield {"event": "error", "data": json.encode(str(e)).decode()}

    # send the SSE stream to agent  
    return EventSourceResponse(_conveyCompletion())
