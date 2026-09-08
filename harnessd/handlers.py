from http import HTTPStatus
import hpptx
from hpptx import RequestError, Response
import logging
import msgspec
from msgspec import Raw, Struct, field, json, structs
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import PlainTextResponse, StreamingResponse

class Message(Struct, omit_defaults=True):
	role: str
	content: str | None

class OpenAIRequest(Struct, omit_defaults=True):
	model: str
	messages: Raw
	stream: bool = false

logger = logging.getLogger("runner")
logging.basicConfig(level=logging.INFO)
logging.getLogger("hpptx").setLevel(logging.WARNING)

def _logOk(clientIP: str, runner: str, model: str):
    logger.info(f"{clientIP} | {runner}:{model}")

def _logInfo(clientIP: str, runner: str, model: str, errcode: int, msg: str):
    logger.info(f"{errcode} | {clientIP} | {runner}:{model} {msg} |")

def _logClientErr(clientIP: str, errcode: HTTPStatus, errmsg: str) -> PlainTextResponse:
    logger.warning(f"{errcode.value} | {clientIP} |")
    return PlainTextResponse(status_code=errcode, content=errmsg)

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
    return StreamingResponse(response.aiter_raw(), 
        headers= { "Content-Type": "text/event-stream" },
        background=BackgroundTask(response.aclose))
        
# performs the LlmRunners round-robin; returns the raw upstream Response
# on success (caller must close it), or None if all runners are exhausted.
async def _routePrompt(request: Request, openAIRequest: OpenAIRequest) -> Response | None: # passed by reference, no copy

    clientIP = request.client.host if request.client else "Unknown"
    
    # make a shallow copy using replace(), so as not to mod openAIRequest
    requestBody = structs.replace(openAIRequest)

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