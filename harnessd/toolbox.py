from __future__ import annotations # must be the first line of the file
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from msgspec import Struct, json
import pkgutil
import time
from starlette.datastructures import State
from typing import TYPE_CHECKING

if TYPE_CHECKING: # handlers imports this module; resolved only for type checkers
    from handlers import OpenAIFunction

class OpenAIParamProp(Struct, omit_defaults=True):
    type:        str
    description: str
    enum:        list[str] | None = None

class OpenAIFunctionParams(Struct, omit_defaults=True):
    type:       str
    properties: dict[str, OpenAIParamProp]
    required:   list[str] | None = None

class OpenAISchemaFunction(Struct, omit_defaults=True):
    name:        str
    description: str
    parameters:  OpenAIFunctionParams | None = None

class OpenAIToolSchema(Struct, omit_defaults=True):
    type:     str
    function: OpenAISchemaFunction

WEATHER_AUTH_JSON = pkgutil.get_data(__name__, "tools/get_weather_auth.json").decode("utf-8")

class Current(Struct):
    temperature_2m: float = 0.0

class OMeteoResponse(Struct):
    latitude:  float
    longitude: float
    current:   Current

async def getWeather(app: State, argv: list[str]) -> tuple[str | None, str | None]:
    try:
        response = await app.client.get(
            url=(f"https://api.open-meteo.com/v1/forecast"
                 f"?latitude={argv[0]}&longitude={argv[1]}"
                 f"&current=temperature_2m"
                 f"&temperature_unit=fahrenheit"),
            timeout=5.0)
        if response.status_code != HTTPStatus.OK:
            return None, f"Open-meteo: {response.status_code}"

        ometeoResponse = json.decode(response.content, type=OMeteoResponse)
        result = (f"Weather at lat: {ometeoResponse.latitude}, "
                  f"lon: {ometeoResponse.longitude} is "
                  f"{ometeoResponse.current.temperature_2m}ºF")
        return result, None
    except Exception as err:
        return None, f"Cannot connect to Open Meteo: {err}"

# None if the ticket is live, else the 401 message for the LLM
async def _checkAuth(rwdb, ticket: str) -> str | None:
    try:
        async with rwdb.execute("SELECT expiration FROM tickets WHERE ticket = ?", (ticket,)) as cur:
            row = await cur.fetchone()
    except Exception as err:
        return f"Ticket lookup failed: {err}"
    if row is None or time.time() > row[0]:
        return ("401 Unauthorized. Call get_auth to obtain a new ticket and retry. "
                "Never reuse an old ticket.")
    return None

async def getWeatherAuth(app: State, argv: list[str]) -> tuple[str | None, str | None]:
    authErr = await _checkAuth(app.rwdb, argv[0])
    return (None, authErr) if authErr else await getWeather(app, argv[1:])

type ToolFunction = Callable[[State, list[str]], Awaitable[tuple[str | None, str | None]]]

class Tool:
    __slots__ = ("schema", "function")
    def __init__(self, schema: OpenAIToolSchema, function: ToolFunction):
        self.schema = schema
        self.function = function

class Toolbox:
    def __init__(self):
        self.tools: dict[str, Tool] = {
            "get_weather_auth": Tool(json.decode(WEATHER_AUTH_JSON, type=OpenAIToolSchema), getWeatherAuth),
        }

    def schemas(self) -> list[OpenAIToolSchema]:
        return [tool.schema for tool in self.tools.values()]

    # (None, None) if tool not resident, (None, error) if it failed, (result, None) on success
    async def invoke(self, app: State, function: OpenAIFunction) -> tuple[str | None, str | None]:
        if not function.name:
            return None, None
        tool = self.tools.get(function.name)
        if tool is None:
            return None, None
        try:
            args = json.decode(function.arguments or '{}')
        except Exception as err:
            return None, f"bad tool arguments JSON: {err}"

        params = tool.schema.function.parameters
        required = (params.required if params else []) or []
        argv = []
        for label in required:
            value = args.get(label)
            if value is None:
                return None, f"422 UnprocessableEntity: Missing required argument '{label}'"
            argv.append(value if isinstance(value, str) else str(value))

        return await tool.function(app, argv)
