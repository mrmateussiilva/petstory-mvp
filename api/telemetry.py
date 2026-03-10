import sqlite3
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel


TELEMETRY_DB = Path(__file__).parent / "telemetry.db"


class TelemetryEvent(BaseModel):
    session_id: str
    event_name: str
    path: str
    timestamp: str
    referrer: str = ""
    user_agent: str = ""
    screen_width: int = 0
    screen_height: int = 0
    metadata: dict = {}


def init_db():
    """Initialize the SQLite database and create table if not exists."""
    conn = sqlite3.connect(str(TELEMETRY_DB))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            event_name TEXT NOT NULL,
            path TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            referrer TEXT,
            user_agent TEXT,
            screen_width INTEGER,
            screen_height INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_session ON telemetry_events(session_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_event_name ON telemetry_events(event_name)"
    )
    conn.commit()
    conn.close()


def save_event(event: TelemetryEvent):
    """Save a telemetry event to the database."""
    conn = sqlite3.connect(str(TELEMETRY_DB))
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO telemetry_events 
        (session_id, event_name, path, timestamp, referrer, user_agent, screen_width, screen_height, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.session_id,
            event.event_name,
            event.path,
            event.timestamp,
            event.referrer,
            event.user_agent,
            event.screen_width,
            event.screen_height,
            str(event.metadata) if event.metadata else "{}",
        ),
    )
    conn.commit()
    conn.close()


def get_summary() -> dict:
    """Get summary of events grouped by event_name."""
    conn = sqlite3.connect(str(TELEMETRY_DB))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_name, COUNT(*) as count 
        FROM telemetry_events 
        GROUP BY event_name 
        ORDER BY count DESC
    """)
    results = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return results


def get_unique_sessions() -> int:
    """Get count of unique sessions."""
    conn = sqlite3.connect(str(TELEMETRY_DB))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT session_id) FROM telemetry_events")
    result = cursor.fetchone()[0]
    conn.close()
    return result
