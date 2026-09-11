"""Version-one metadata schema."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL,
 session_id TEXT NOT NULL REFERENCES sessions(id), relationship_id TEXT NOT NULL,
 event_type TEXT NOT NULL, metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS relationships (
 id TEXT PRIMARY KEY, trust REAL NOT NULL CHECK(trust BETWEEN 0 AND 100),
 verified INTEGER NOT NULL DEFAULT 0, successes INTEGER NOT NULL DEFAULT 0,
 failures INTEGER NOT NULL DEFAULT 0, last_verified TEXT, baselines TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
 id TEXT PRIMARY KEY, relationship_id TEXT NOT NULL REFERENCES relationships(id),
 started TEXT NOT NULL, ended TEXT, mode TEXT NOT NULL CHECK(mode IN ('real','simulated')),
 status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS trust_history (
 id INTEGER PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
 timestamp TEXT NOT NULL, score REAL NOT NULL CHECK(score BETWEEN 0 AND 100),
 delta REAL NOT NULL CHECK(delta BETWEEN -100 AND 100), reason TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS verification_events (
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
 timestamp TEXT NOT NULL, outcome TEXT NOT NULL, simulated INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS key_events (
 id INTEGER PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
 timestamp TEXT NOT NULL, action TEXT NOT NULL, key_id TEXT NOT NULL);
"""


def open_database(path):
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    return db
