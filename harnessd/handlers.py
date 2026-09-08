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
