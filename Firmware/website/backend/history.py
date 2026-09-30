import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List, Tuple

DB_PATH = Path(__file__).resolve().parent / "growhub.db"
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
                device_id TEXT NOT NULL,
                recorded_at REAL NOT NULL,
                moisture REAL NOT NULL,
                temperature REAL NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_readings_device_time ON readings (device_id, recorded_at)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_time ON readings (recorded_at)")


def record_readings(recorded_at: float, rows: Iterable[Tuple[str, float, float]]) -> None:
    with _connection() as conn:
        conn.executemany(
            "INSERT INTO readings (device_id, recorded_at, moisture, temperature) VALUES (?, ?, ?, ?)",
            [(device_id, recorded_at, moisture, temperature) for device_id, moisture, temperature in rows],
        )
        conn.execute("DELETE FROM readings WHERE recorded_at < ?", (recorded_at - RETENTION_SECONDS,))


def get_history(device_id: str, range_key: str, now: float) -> List[dict]:
    span = RANGE_SECONDS[range_key]
    bucket_seconds = span / MAX_POINTS

    with _connection() as conn:
        rows = conn.execute(
            """
            SELECT CAST(recorded_at / ? AS INTEGER) AS bucket,
                   AVG(recorded_at),
                   AVG(moisture),
                   AVG(temperature)
            FROM readings
            WHERE device_id = ? AND recorded_at >= ?
            GROUP BY bucket
            ORDER BY bucket
            """,
            (bucket_seconds, device_id, now - span),
        ).fetchall()

    return [
        {
            "at": int(recorded_at * 1000),
            "moisture": round(moisture, 1),
            "temperature": round(temperature, 1),
        }
        for _, recorded_at, moisture, temperature in rows
    ]
