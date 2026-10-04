import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

DB_PATH = Path(os.environ.get("GROWHUB_DB_PATH", Path(__file__).resolve().parent / "growhub.db"))
MAX_POINTS = 120
RANGE_SECONDS = {
    "1h": 3600,
    "24h": 24 * 3600,
    "7d": 7 * 24 * 3600,
}
RETENTION_SECONDS = max(RANGE_SECONDS.values())


@contextmanager
def _connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hub_id TEXT NOT NULL DEFAULT '',
                device_id TEXT NOT NULL,
                recorded_at REAL NOT NULL,
                moisture REAL NOT NULL,
                temperature REAL NOT NULL,
                ec REAL
            )
            """
        )

        columns = {row[1] for row in conn.execute("PRAGMA table_info(readings)")}
        if "hub_id" not in columns:
            conn.execute("ALTER TABLE readings ADD COLUMN hub_id TEXT NOT NULL DEFAULT ''")
        if "ec" not in columns:
            conn.execute("ALTER TABLE readings ADD COLUMN ec REAL")

        conn.execute("DROP INDEX IF EXISTS idx_readings_device_time")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_readings_hub_device_time "
            "ON readings (hub_id, device_id, recorded_at)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_time ON readings (recorded_at)")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hubs (
                hub_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                last_telemetry_at REAL,
                telemetry_interval REAL,
                low_water_streak INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def record_readings(
    hub_id: str,
    recorded_at: float,
    rows: Iterable[Tuple[str, float, float Optional[float]]]
) -> None:
    with _connection() as conn:
        conn.executemany(
            "INSERT INTO readings (hub_id, device_id, recorded_at, moisture, temperature, ec) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (hub_id, device_id, recorded_at, moisture, temperature, ec)
                for device_id, moisture, temperature, ec in rows
            ],
        )
        conn.execute("DELETE FROM readings WHERE recorded_at < ?", (recorded_at - RETENTION_SECONDS,))


def get_recent_moisture(hub_id: str, device_id: str, limit: int) -> List[float]:
    with _connection() as conn:
        rows = conn.execute(
            "SELECT moisture FROM readings WHERE hub_id = ? AND device_id = ? ",
            "ORDER BY recorded_at DESC LIMIT",
            (hub_id, device_id, limit),
        ).fetchall()
    return [moisture for (moisture,) in rows]


def get_history(hub_id: str, device_id: str, range_key: str, now: float) -> List[dict]:
    span = RANGE_SECONDS[range_key]
    bucket_seconds = span / MAX_POINTS

    with _connection() as conn:
        rows = conn.execute(
            """
            SELECT CAST(recorded_at / ? AS INTEGER) AS bucket,
                   AVG(recorded_at),
                   AVG(moisture),
                   AVG(temperature),
                   AVG(ec)
            FROM readings
            WHERE hub_id = ? AND device_id = ? AND recorded_at >= ?
            GROUP BY bucket
            ORDER BY bucket
            """,
            (bucket_seconds, hub_id, device_id, now - span),
        ).fetchall()

    return [
        {
            "at": int(recorded_at * 1000),
            "moisture": round(moisture, 1),
            "temperature": round(temperature, 1),
            "ec": round(ec, 2) if ec is not None else None,
        }
        for _, recorded_at, moisture, temperature, ec in rows
    ]


def save_hub(
    hub_id: str,
    state: dict,
    last_telemetry_at: Optional[float],
    telemetry_interval: Optional[float],
    low_water_streak: int,
) -> None:
    with _connection() as conn:
        conn.execute(
            """
            INSERT INTO hubs (hub_id, state, last_telemetry_at, telemetry_interval, low_water_streak)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (hub_id) DO UPDATE SET
                state = excluded.state,
                last_telemetry_at = excluded.last_telemetry_at,
                telemetry_interval = excluded.telemetry_interval.
                low_water_streak = excluded.low_water_streak
            """,
            (hub_id, json.dumps(state), last_telemetry_at, telemetry_interval, low_water_streak),
        )


def load_hubs() -> List[dict]:
    with _connection() as conn:
        rows = conn.execute(
            "SELECT hub_id, state, last_telemetry_at, telemetry_interval, low_water_streak FROM hubs"
        ).fetchall()
    return [
        {
            "hub_id": hub_id,
            "state": json.loads(state),
            "last_telemetry_at": last_telemetry_at,
            "telemetry_interval": telemetry_interval,
            "low_water_streak": low_water_streak,
        }
        for hub_id, state, last_telemetry_at, telemetry_interval, low_water_streak in rows
    ]