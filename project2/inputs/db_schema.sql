CREATE TABLE turns (
    turnID INTEGER PRIMARY KEY,
    appID TEXT NOT NULL,
    prompt BLOB NOT NULL,
    reasoning TEXT,
    completion TEXT,
    completed INTEGER,
    prompt_ts INTEGER NOT NULL DEFAULT (unixepoch()),
    completion_ts INTEGER
);
CREATE INDEX turns_idx ON turns(appID, turnID);
CREATE TRIGGER completion_ts_trg
AFTER UPDATE OF completion ON turns
WHEN NEW.completion IS NOT NULL AND OLD.completion IS NULL
BEGIN
    UPDATE turns
    SET completion_ts = unixepoch()
    WHERE turnID = NEW.turnId;
END;
CREATE VIEW turns_tz AS SELECT appID, datetime(prompt_ts, 'unixepoch', 'localtime') AS prompt_ts, prompt, reasoning, completion, datetime(completion_ts, 'unixepoch', 'localtime') AS completion_ts FROM turns
/* turns_tz(appID,prompt_ts,prompt,reasoning,completion,completion_ts) */;
CREATE TABLE sqlite_stat1(tbl,idx,stat);
CREATE TABLE tools (appID TEXT PRIMARY KEY, schemas BLOB, timestamp INTEGER NOT NULL DEFAULT (unixepoch()));
CREATE TABLE calls (id TEXT PRIMARY KEY, idx INTEGER NOT NULL, turnID INTEGER NOT NULL, name TEXT NOT NULL, arguments TEXT NOT NULL, result TEXT, call_ts INTEGER NOT NULL DEFAULT (unixepoch()), result_ts INTEGER, FOREIGN KEY(turnID) REFERENCES turns(turnID));
CREATE TRIGGER result_ts_trg AFTER UPDATE OF result ON calls WHEN NEW.result IS NOT NULL AND OLD.result IS NULL BEGIN UPDATE calls SET result_ts = unixepoch() WHERE id = NEW.id; END;
CREATE INDEX calls_idx ON calls(turnID, idx);
CREATE TABLE tickets (ticket TEXT PRIMARY KEY, creator TEXT NOT NULL, expiration INTEGER NOT NULL, ticket_ts INTEGER NOT NULL DEFAULT (unixepoch()));
CREATE INDEX tix_idx ON tickets(expiration);
CREATE VIEW tix_ts AS SELECT ticket, creator, datetime(expiration, "unixepoch", "localtime") AS expiration, datetime(ticket_ts, "unixepoch", "localtime") AS ticket_ts FROM tickets
/* tix_ts(ticket,creator,expiration,ticket_ts) */;
