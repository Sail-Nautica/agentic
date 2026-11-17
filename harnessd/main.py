from httpx import AsyncClient, Timeout

from starlette.applications import Starlette
from starlette.routing import Route

import handlers
from runners import LlmRunners

import aiosqlite
import asyncio
from contextlib import asynccontextmanager
import sys
import contextlib
from fastembed import TextEmbedding
import importlib.resources
from structured import structuredResponseFormat

HARNESS_DB_PATH = "/home/ubuntu/agentic/harnessd/harnessd.db"

FASTEMBED_CACHE = "/home/ubuntu/agentic/harnessd/fastembed-cache"

CONNECTION_PRAGMAS = """
        PRAGMA busy_timeout = 5000;     -- 5 secs, raise to 20 if multiple workers
        PRAGMA cache_size = -32000;     -- 32 MB
        PRAGMA mmap_size = 0;           -- DISABLED: Prevents the OS from evicting TurboQuant buffers
        PRAGMA synchronous = NORMAL;
        PRAGMA journal_size_limit = 104857600; -- 100 MB
        PRAGMA temp_store = MEMORY;
        PRAGMA wal_autocheckpoint = 0;
"""

@asynccontextmanager
async def lifespan(app: Starlette):
    # mode=rw ensures SQLite errors out instead of creating a db if it doesn't exist.
    rwdb = await aiosqlite.connect(f"file:{HARNESS_DB_PATH}?mode=rw", uri=True, autocommit=True)
    waldb = await aiosqlite.connect(f"file:{HARNESS_DB_PATH}?mode=rw", uri=True, autocommit=True)

    embed = app.state.runners.embed
    app.state.embedModel = None
    if embed is not None and embed.local is not None:
        try:
            app.state.embedModel = await asyncio.wait_for(
                asyncio.to_thread(
                    TextEmbedding,
                    model_name=embed.local,
                    cache_dir=FASTEMBED_CACHE,
                    threads=handlers.EMBED_CONCURRENCY,
                ),
                120.0,
            )
        except Exception as e:
            print(f"Embed runner INACTIVE: {e}", file=sys.stderr)
            embed = app.state.runners.embed = None
            
    # set the embedding runner's options:
    vectorOptions = (f"type=FLOAT32,dimension={embed.dim},distance=COSINE,normalized=1,"
                        f"qtype=TURBO,qbits=4"
                        if embed is not None else None)            

    if vectorOptions is not None:
        try:
            extPath = str(importlib.resources.files("sqlite_vector.binaries") / "vector")
            for db in (rwdb, waldb):
                await db.enable_load_extension(True)
                await db.load_extension(extPath)
                await db.enable_load_extension(False)
                # a connection that cannot be registered must not be used:
                # recall would fail later at query time, silently
                await db.execute("SELECT vector_init('turns','embedding', ?)", (vectorOptions,))
        except Exception as e:
            print(f"sqlite-vector unavailable, semantic recall disabled: {e}", file=sys.stderr)
            vectorOptions = None

    app.state.vectorOptions = vectorOptions
    app.state.snapshotDirty = False  # whether to rerun vector_quantize()

    await asyncio.gather(
        rwdb.executescript(CONNECTION_PRAGMAS),
        waldb.executescript(CONNECTION_PRAGMAS)
    )
    app.state.rwdb = rwdb
    app.state.waldb = waldb

    walTask = asyncio.create_task(waloop(app.state))

    try:
        yield
    finally:
        # graceful shutdown
        walTask.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await walTask
        if handlers._embedTasks:
            await asyncio.wait(handlers._embedTasks, timeout=2.0) # < granian's workers_kill_timeout
        for embedTask in handlers._embedTasks:
            embedTask.cancel()
        await asyncio.gather(*handlers._embedTasks, return_exceptions=True)
        await rwdb.close()
        await waldb.close()

async def rebuildVectorSnapshot(waldb: aiosqlite.Connection, state):
    if not state.snapshotDirty:
        return
    state.snapshotDirty = False
    try:
        await waldb.execute("SELECT vector_quantize('turns','embedding', ?)", ("qtype=TURBO,qbits=4",))
    except Exception as e:
        print(f"vector_quantize failed: {e}", file=sys.stderr)
        state.snapshotDirty = True

async def waloop(state):
    waldb = state.waldb
    # startup rebuild is unconditional: embeddings that landed after the
    # previous process exited must enter the first snapshot; later rebuilds
    # only fire when a new turn embedding persists
    if state.vectorOptions is not None:
        state.snapshotDirty = True
        await rebuildVectorSnapshot(waldb, state)

    # Runs one maintenance job for this tick. Jobs are best-effort: a failed
    # statement logs under its label and the loop carries on.
    async def swept(label: str, sql: str, params: tuple = ()):
        try:
            await waldb.execute(sql, params)
        except Exception as e:
            print(f"{label} failed: {e}", file=sys.stderr)

    while True:
        await asyncio.sleep(60)            
        
        if state.vectorOptions is not None:
            await rebuildVectorSnapshot(waldb, state)

        # stream-end janitor: past the grace window, completed = NULL can only
        # mean an abandoned turn, set it to completed = 0 (incomplete, not to be
        # included in semantic memory)
        await swept("turn janitor sweep",
            "UPDATE turns SET completed = 0 WHERE completed IS NULL AND prompt_ts < unixepoch() - 600")

        # query plan analyzer optimization
        await swept("SQLite optimization", "PRAGMA optimize=0x10002")

        # PASSIVE reuses flushed WAL blocks, file grows to high-water mark 
        # PRAGMA journal_size_limit handles automatic OS file truncation
        await swept("SQLite checkpointing", "PRAGMA wal_checkpoint(PASSIVE)")

        try:
            # gate incremental vacuum by actual db freelist
            row = await (await waldb.execute("PRAGMA freelist_count")).fetchone()

            if row is not None and row[0] > 6400:
                # 100 MB for HDD, can lower to 20 MB for SSD
                # reclaim unused pages in batches (of 64) so as not to freeze the db
                await swept("SQLite vacuuming", "PRAGMA incremental_vacuum(64)")
        except Exception as e:
            print(f"SQLite vacuuming failed: {e}", file=sys.stderr)

routes = [
	# TODO(graded): comment out this '/' route before submission so it returns 404.
	# Route('/', handlers.top, methods=['GET']),
	Route('/llmprompt', handlers.llmprompt, methods=['POST']),
	Route('/llmsearch', handlers.llmsearch, methods=['POST']),
]

app = Starlette(routes=routes, lifespan=lifespan)

app.state.runners = LlmRunners()
app.state.structured = structuredResponseFormat
app.state.client = AsyncClient(timeout = Timeout(connect=5.0, read=300.0, write=None, pool=None), http2=True)
