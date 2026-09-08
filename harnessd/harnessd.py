from granian.server import Server
import os
from pathlib import Path

AGENTIC_ROOT = Path(os.environ.get("AGENTIC_ROOT") or Path(__file__).resolve().parent.parent)

if __name__ == '__main__':
	Server(
		"main:app",
		address="0.0.0.0",
		port=443,
		interface="asgi",
		loop="uvloop",
		log_access=True,
		ssl_cert=AGENTIC_ROOT / "harnessd.crt",
		ssl_key=AGENTIC_ROOT / "harnessd.key",
		workers=1,
		workers_kill_timeout=3,
		respawn_failed_workers=True,
		respawn_interval=1.0,
	).serve()


