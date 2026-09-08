from collections.abc import Iterator
import itertools
import math
import msgspec
from msgspec import Struct
import os
from pathlib import Path
import random
import sys

RUNNERS_CONFIG = "/home/ubuntu/agentic/runners.toml"

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

class RawRunners(Struct):
    apis: dict[str, 'LlmRunnerAPI'] = {}
    runners: list[RawRunner] = []

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
            key=lambda r: -math.log(random.random()) / (r.weight if r.weight > 0.0 else 1e-9)
        )
        
        if self.local:
            # lazily chain the local fallback as the last resort
            return itertools.chain(scored, (self.local,))
        
        # If no local fallback, just return the list iterator
        return iter(scored)

    def __init__(self):
        print(f"Reading {RUNNERS_CONFIG}")
        
        # ingest runners config file
        try:
            toml_bytes = Path(RUNNERS_CONFIG).read_bytes()
        except FileNotFoundError:
            raise ValueError(f"Config file not found at {RUNNERS_CONFIG}")
            
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
