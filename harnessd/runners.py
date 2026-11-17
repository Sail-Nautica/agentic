from collections.abc import Iterator
import itertools
import math
import msgspec
from msgspec import Struct
import os
from pathlib import Path
import random
import sys

RUNNERS_CONFIG = Path(os.environ.get("RUNNERS_CONFIG") or Path(__file__).resolve().parent.parent / "runners.toml")

class LlmRunnerAPI(Struct):
    url: str
    key: str

class LlmRunner(Struct):
    api: LlmRunnerAPI
    model: str
    weight: float
    
class RawRunner(Struct):
    api: str
    model: str
    weight: float

class RawEmbed(Struct):
    dim: int
    api: str | None = None
    model: str | None = None
    local: str | None = None

# to hold options for cloud or local runners
class EmbedRunner(Struct):
    api: LlmRunnerAPI | None
    model: str
    dim: int
    local: str | None = None

class RawRunners(Struct):
    apis: dict[str, 'LlmRunnerAPI'] = {}
    runners: list[RawRunner] = []
    embed: RawEmbed | None = None

class LlmRunners:
    # The iterator that powers the `for runner in runners` loop:
    # to iterate through the runner array randomized per HTTP-request to load balance
    def __iter__(self) -> Iterator[LlmRunner]:
        '''
        Calculate the Efraimidis and Spirakis A-Res scores based on weights
        Each runner gets a randomized score that, when sorted, determines
        the fallback order for each HTTP-request.
        Each HTTP-request gets a different ordered list, effecting the
        round-robin selection of runners across HTTP-requests.
        '''
        scored = sorted( # sort ascending by score
            self.runners,
            key=lambda r: -math.log(1.0 - random.random()) / (r.weight if r.weight > 0.0 else 1e-9)
        )
        
        if self.local:
            # lazily chain the local fallback as the last resort
            return itertools.chain(scored, (self.local,))
        
        # If no local fallback, just return the list iterator
        return iter(scored)

    def __init__(self):
        print(f"Reading {RUNNERS_CONFIG}")
        
        # ingest runners config file
        toml_bytes = Path(RUNNERS_CONFIG).read_bytes()
            
        rawRunners = msgspec.toml.decode(toml_bytes, type=RawRunners)
    
        # build each runner's base url and API key (fetched from the environment)
        # build a new dict of only the ACTIVE ones        
        apis: dict[str, LlmRunnerAPI] = {}
        
        for runner, api in rawRunners.apis.items():
            key = os.environ.get(api.key) if api.key != "" else None
            
            if key: # don't want empty string either
                print(f"Runner {runner} ACTIVE", file=sys.stderr)
                apis[runner] = LlmRunnerAPI(url=api.url, key=key)
            elif runner == "local":
                if api.url:
                    print(f"Local runner {api.url} ACTIVE. API key {api.key}", file=sys.stderr)
                    apis[runner] = api
                else:
                    print("Local runner INACTIVE. No URL", file=sys.stderr)
            else:
                print(f"Runner {runner} INACTIVE: NO '{api.key}'", file=sys.stderr)
                    
        if not apis:
            raise ValueError("CRITICAL: No API keys found and no local LLM configured.")
            
        # construct the full list of potential runners
        self.runners: list[LlmRunner] = [
            LlmRunner(api=api, model=runner.model, weight=runner.weight)
            for runner in rawRunners.runners
            if (api := apis.get(runner.api)) is not None
        ]
    
        self.local: LlmRunner | None = None
        local = apis.get("local")
        if local is not None and local.url != "":
            self.local = LlmRunner(
                api=local,
                model="", # let agent set
                weight=1.0
            )

        self.embed: EmbedRunner | None = None
        rawEmbed = rawRunners.embed
        if rawEmbed is not None and rawEmbed.dim > 0:
            if rawEmbed.local:
                if rawEmbed.api or rawEmbed.model:
                    print("Embed runner local model: ignoring api/model", file=sys.stderr)
                self.embed = EmbedRunner(
                    api=None,
                    model="",
                    dim=rawEmbed.dim,
                    local=rawEmbed.local
                )
                print(f"Embed runner ACTIVE: {rawEmbed.local} (dim {rawEmbed.dim})", file=sys.stderr)
            elif rawEmbed.model:
                embedApi = apis.get(rawEmbed.api)
                if embedApi is None:
                    print(f"Embed runner INACTIVE: unknown or inactive api '{rawEmbed.api}'", file=sys.stderr)
                else:
                    self.embed = EmbedRunner(
                        api=embedApi,
                        model=rawEmbed.model,
                        dim=rawEmbed.dim
                    )
                    print(f"Embed runner ACTIVE: {rawEmbed.model} (dim {rawEmbed.dim})", file=sys.stderr)
        if self.embed is None:
            print("Embed runner INACTIVE: semantic recall disabled", file=sys.stderr)
