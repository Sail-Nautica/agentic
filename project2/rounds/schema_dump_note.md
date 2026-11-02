# Read-only schema dump (Step 0)
Run by the orchestrator over ssh as authorized by the owner: `sqlite3 -readonly /home/ubuntu/agentic/harnessd/harnessd.db ".schema"` (no data read, no write). Output saved as db_schema_dump_readonly.sql (the first stderr line "Usage: .headers on|off" printed by the sqlite3 shell was removed).
