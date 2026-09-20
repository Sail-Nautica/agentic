from httpx import AsyncClient, Timeout

from starlette.applications import Starlette
from starlette.routing import Route

import handlers
from runners import LlmRunners

import aiosqlite
import asyncio
from contextlib import asynccontextmanager
import sys

HARNESS_DB_PATH = "/home/ubuntu/agentic/harnessd/harnessd.db"

@asynccontextmanager
async def lifespan(app: Starlette):
    # mode=rw ensures SQLite errors out instead of creating a db if it doesn't exist.
    rwdb = await aiosqlite.connect(f"file:{HARNESS_DB_PATH}?mode=rw", uri=True, autocommit=True)
    waldb = await aiosqlite.connect(f"file:{HARNESS_DB_PATH}?mode=rw", uri=True, autocommit=True)

    # for a 1GB GCP/AWS micro instance running on bare-metal Ubuntu, no containerization.
    await rwdb.executescript("""
        PRAGMA busy_timeout = 5000;     -- 5 secs
        PRAGMA cache_size = -32000;     -- 32 MB
        PRAGMA mmap_size = 0;
        PRAGMA synchronous = NORMAL;
        PRAGMA journal_size_limit = 104857600; -- 100 MB
        PRAGMA temp_store = MEMORY;
        PRAGMA wal_autocheckpoint = 0;
    """)
    # make db accessible to all route handlers
    app.state.rwdb = rwdb

    # a dedicated maintenance connection
    await waldb.executescript("""
        PRAGMA busy_timeout = 5000;     -- 5 secs
        PRAGMA synchronous = NORMAL;
        PRAGMA journal_size_limit = 104857600; -- 100 MB
        PRAGMA wal_autocheckpoint = 0;
    """)

    task = asyncio.create_task(waloop(waldb))

    # graceful shutdown
    try:
        yield
    finally:
        task.cancel()
        try:
            await task          # await wal_checkpoint() to complete
        except (asyncio.CancelledError, Exception):
            pass
        await rwdb.close()      # close DB (flushes WAL)
        await waldb.close()

async def waloop(waldb: aiosqlite.Connection):
    while True:
        await asyncio.sleep(60)
        try:
            # query plan analyzer optimization
            await waldb.execute("PRAGMA optimize=0x10002")

            # PASSIVE reuses flushed WAL blocks, file grows to high-water mark
            # PRAGMA journal_size_limit handles automatic OS file truncation
            await waldb.execute("PRAGMA wal_checkpoint(PASSIVE)")

            # gate incremental vacuum by actual db freelist
            async with waldb.cursor() as cur:
                await cur.execute("PRAGMA freelist_count")
                row = await cur.fetchone()

            if row is not None and row[0] > 25600:
                # 100 MB freePages for HDD, can lower to 20 MB (5120 pages) for SDD
                # reclaim unused pages in batches (of 256) so as not to freeze the db
                await waldb.execute("PRAGMA incremental_vacuum(256)")
        except Exception as e:
            print(f"SQLite checkpointing or optimization failed: {e}", file=sys.stderr)

routes = [
	# TODO(graded): comment out this '/' route before submission so it returns 404.
	# Route('/', handlers.top, methods=['GET']),
	Route('/llmprompt', handlers.llmprompt, methods=['POST']),
	Route('/llmchat', handlers.llmchat, methods=['POST']),
	Route('/llmclear', handlers.llmclear, methods=['POST']),
]

app = Starlette(routes=routes, lifespan=lifespan)

app.state.runners = LlmRunners()
app.state.client = AsyncClient(timeout = Timeout(connect=5.0, read=None, write=None, pool=None), http2=True)
