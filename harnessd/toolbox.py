import asyncio
from collections.abc import Awaitable, Callable
from http import HTTPStatus
import httpx
import msgspec
from msgspec import Struct, json
import pkgutil
from starlette.datastructures import State
import time

import main
from handlers import OpenAIFunction

class OpenAIParamProp(Struct, omit_defaults=True):
    type:        str
    description: str
    enum:        list[str] | None = None

class OpenAIFunctionParams(Struct, omit_defaults=True):
    type:       str
    properties: dict[str, OpenAIParamProp]
    required:   list[str] | None = None      # parameters MUST be in function-signature order

class OpenAISchemaFunction(Struct, omit_defaults=True):
    name:        str
    description: str
    parameters:  OpenAIFunctionParams | None = None

class OpenAIToolSchema(Struct, omit_defaults=True):
    type: str
    function: OpenAISchemaFunction

WEATHER_JSON = pkgutil.get_data(__name__, "tools/get_weather.json").decode("utf-8")
WEATHER_AUTH_JSON = pkgutil.get_data(__name__, "tools/get_weather_auth.json").decode("utf-8")

class Current(Struct):
    temperature_2m: float = 0.0

class OMeteoResponse(Struct):
    latitude: float
    longitude: float
    current: Current

async def getWeather(app: State, argv: list[str]) -> tuple[str | None, str | None]:
    # Open-Meteo API doc: https://open-meteo.com/en/docs#api_documentation
    try:
        response = await app.client.get(
            url=f"https://api.open-meteo.com/v1/forecast?latitude={argv[0]}&longitude={argv[1]}&current=temperature_2m&temperature_unit=fahrenheit",
            timeout=5.0
        )
        if response.status_code != HTTPStatus.OK:
            return None, f"Open-meteo response: {response.status_code}"

        ometeoResponse = json.decode(response.content, type=OMeteoResponse)
        return f"Weather at lat: {ometeoResponse.latitude}, lon: {ometeoResponse.longitude} is {ometeoResponse.current.temperature_2m}ºF", None
    except Exception as err:
        return None, f"Cannot connect to Open Meteo: {err}"

async def getWeatherAuth(app: State, argv: list[str]) -> tuple[str | None, str | None]:
    err = await _checkAuth(app.rwdb, argv[0])
    if err is not None:
        return None, err

    return await getWeather(app, argv[1:])

async def _checkAuth(rwdb: aiosqlite.Connection, ticket) -> str | None:
    try:
        async with rwdb.execute(
            "SELECT expiration FROM tickets WHERE ticket = ?", (ticket,)
        ) as cur:
            row = await cur.fetchone()
        now = int(time.time())
        if row is None or now > row[0]:
            return "401 Unauthorized: The ticket is invalid or expired. Ask the user if they want to try again. If so, you **MUST** call the get_auth tool again to get a fresh new ticket and retry the operation. DO NOT reuse any ticket in context/history that came before this message."
        return None
    except Exception as e:
        return str(e)

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

    async def invoke(self, app: State, function: OpenAIFunction) -> tuple[str | None, str | None]:
        if not function.name: return (None, None)
        tool = self.tools.get(function.name)
        if tool is None:
            return None, None
        try:
            # parses JSON arguments string: stringifies each required argument into args
            args = json.decode(function.arguments or '{}')
        except Exception as err:
            return None, f"bad tool arguments JSON: {err}"
            
        # get args in parameters.required order, they may arrive out of order from the back end
        params = tool.schema.function.parameters
        required = (params.required if params else []) or []
        argv = []
                
        for label in required:
            value = args.get(label)
            if value is None:
                return None, f"422 UnprocessableEntity: Missing required argument '{label}'"
            argv.append(value if isinstance(value, str) else str(value))
            
        return await tool.function(app, argv)
    
