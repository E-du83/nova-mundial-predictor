import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    team TEXT PRIMARY KEY,
    fifa_rank INTEGER,
    fifa_points REAL,
    nova_strength_rating REAL,
    data_quality_json TEXT
);

CREATE TABLE IF NOT EXISTS simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    simulation_type TEXT NOT NULL,
    simulations_count INTEGER NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS odds_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    match_name TEXT NOT NULL,
    market TEXT NOT NULL,
    bookmaker TEXT NOT NULL,
    odds REAL NOT NULL,
    source TEXT,
    label TEXT
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    match_name TEXT,
    market TEXT,
    decision TEXT,
    recommended_play TEXT,
    model_probability REAL,
    current_odds REAL,
    minimum_odds REAL,
    expected_value REAL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_odds_match_market ON odds_snapshots(match_name, market);
CREATE INDEX IF NOT EXISTS idx_recommendations_match ON recommendations(match_name);
"""


def connect(db_path: str | Path = "nova_mundial_predictor.sqlite3"):
    return sqlite3.connect(db_path)


def init_db(db_path: str | Path = "nova_mundial_predictor.sqlite3") -> str:
    db_path = Path(db_path)
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    return str(db_path)


def insert_odds_snapshot(db_path, match_name, market, bookmaker, odds, source="manual", label=None):
    conn = connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO odds_snapshots (match_name, market, bookmaker, odds, source, label)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (match_name, market, bookmaker, odds, source, label)
        )
        conn.commit()
    finally:
        conn.close()


def insert_recommendation(db_path, **kwargs):
    conn = connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO recommendations (
                match_name, market, decision, recommended_play, model_probability,
                current_odds, minimum_odds, expected_value, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                kwargs.get("match_name"),
                kwargs.get("market"),
                kwargs.get("decision"),
                kwargs.get("recommended_play"),
                kwargs.get("model_probability"),
                kwargs.get("current_odds"),
                kwargs.get("minimum_odds"),
                kwargs.get("expected_value"),
                kwargs.get("notes"),
            )
        )
        conn.commit()
    finally:
        conn.close()