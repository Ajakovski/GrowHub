import json
from optparse import Option
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List, NamedTuple, Optional, Tuple

DB_PATH = Path(os.environ.get("GROWHUB_DB_PATH", Path(__file__).resolve().parent / "growhub.db"))
MAX_POINTS = 120
RANGE_SECONDS = {
    "1h": 3600,
    "24h": 24 * 3600,
    "7d": 7 * 24 * 3600,
}
RETENTION_SECONDS = max(RANGE_SECONDS.values())
METRIC_DECIMALS = {
    "water_temp": 1,
    "ec": 2,
    "ph": 2,
    "air_temp": 1,
    "humidity": 0,
    "light": 0,
    "flow": 2,
}
METRICS = tuple[str, ...](METRIC_DECIMALS)
LEGACY_COLUMNS = {"moisture", "temperature"}
HUB_ONLY_LEGACY = {"water_temp", "temperature", "ec": "ec", "ph": "ph"}


@contextmanager
def _connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _create_readings_table(conn: sqlite3.Connection, name: str) -> None:
    metric_columns = ",\n".join(f"{metric} REAL" for metric in METRICS)
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hub_id TEXT NOT NULL DEFAULT '',
            device_id TEXT NOT NULL,
            recorded_at REAL NOT NULL,
            {metric_columns}
        )
        """
    )


def _migrate_legacy_readings(conn: sqlite3.Connection, columns: set) -> None:
    selects = {}
    for metric, legacy in HUB_ONLY_LEGACY.items():
        selects[metric] = f"CASE WHEN device_id = 'hub' THEN {legacy} END" if legacy in columns else "NULL"
        selects["light"] = "light" if "light" in columns else "NULL"
        hub_id = "hub_id" if "hub_id" in columns else "''"

        _create_readings_table(conn, "readings_new")
        targets = ", ".join(selects)
        values = ", ".join(selects.values())
        conn.execute(
            f"INSERT INTO readings_new (id, hub_id, device_id, recorded_at, {targets}) "
            f"SELECT id, {hub_id}, device_id, recorded_at, {values} FROM readings"
        )
        conn.execute("DROP TABLE readings")
        conn.execute("ALTER TABLE readings_new RENAME TO readings")


def init_db() -> None:
    with _connection() as conn:
        _create_readings_table(conn, "readings")

        columns = {row[1] for row in conn.execute("PRAGMA table_info(readings)")}
        if columns & LEGACY_COLUMNS:
            _migrate_legacy_readings(conn, columns)
        else:
            for metric in METRICS:
                if metric not in columns:
                    conn.execute(f"ALTER TABLE readings ADD COLUMN {metric} REAL")

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
                low_water_streak INTEGER NOT NULL DEFAULT 0,
                ai_status TEXT,
                ai_summary TEXT,
                ai_updated_at REAL,
                camera_source TEXT
            )
            """
        )

        hub_columns = {row[1] for row in conn.execute("PRAGMA table_info(hubs)")}
        for column, column_type in (
            ("ai_status", "TEXT"),
            ("ai_summary", "TEXT"),
            ("ai_updated_at", "REAL"),
            ("camera_source", "TEXT"),
            ("plants", "TEXT"),
        ):
            if column not in hub_columns:
                conn.execute(f"ALTER TABLE hubs ADD COLUMN {column} {column_type}")


class Reading(NamedTuple):
    device_id: str
    water_temp: Optional[float] = None
    ec: Optional[float] = None
    ph: Optional[float] = None
    air_temp: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[float] = None
    flow: Optional[float] = None


def record_readings(hub_id: str, recorded_at: float, rows: Iterable[Reading]) -> None:
    placeholders = ", ".join("?" for _ in METRICS)
    with _connection() as conn:
        conn.executemany(
            f"INSERT INTO readings (hub_id, device_id, recorded_at, {', '.join(METRICS)}) "
            f"VALUES (?, ?, ?, {placeholders})",
            [
                (hub_id, row.device_id, recorded_at, *(getattr(row, metric) for metric in METRICS))
                for row in rows
            ],
        )
        conn.execute("DELETE FROM readings WHERE recorded_at < ?", (recorded_at - RETENTION_SECONDS,))


def get_recent(hub_id: str, device_id: str, metric: str, limit: int) -> List[Optional[float]]:
    if metric not in METRIC_DECIMALS:
        raise ValueError(f"Unknown metric '{metric}'")
    with _connection() as conn:
        rows = conn.execute(
            f"SELECT {metric} FROM readings WHERE hub_id = ? AND device_id = ? "
            "ORDER BY recorded_at DESC LIMIT ?",
            (hub_id, device_id, limit),
        ).fetchall()
    return [value for (value,) in rows]


def _round_or_none(value: Optional[float], decimals: int) -> Optional[float]:
    return round(value, decimals) if value is not None else None


def get_history(hub_id: str, device_id: str, range_key: str, now: float) -> List[dict]:
    span = RANGE_SECONDS[range_key]
    bucket_seconds = span / MAX_POINTS
    averages = ", ".join(f"AVG({metric})" for metric in METRICS)

    with _connection() as conn:
        rows = conn.execute(
            f"""
            SELECT CAST(recorded_at / ? AS INTEGERS) AS bucket, AVG(recorded_at), {averages}
            FROM readings
            WHERE hub_id = ? AND device_id = ? AND recorded_at >= ?
            GROUP BY bucket
            ORDER BY bucket
            """,
            (bucket_seconds, hub_id, device_id, now - span),
        ).fetchall()

    return [
        {
            "at": int(row[1] * 1000),
            **{
                metric: _round_or_none(value, METRIC_DECIMALS[metric])
                for metric, value in zip[tuple[str, Any]](METRICS, row[2:])
            }
        }
        for row in rows
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
                telemetry_interval = excluded.telemetry_interval,
                low_water_streak = excluded.low_water_streak
            """,
            (hub_id, json.dumps(state), last_telemetry_at, telemetry_interval, low_water_streak),
        )


def save_hub_ai(hub_id: str, status: str, summary: str, updated_at: float) -> None:
    with _connection() as conn:
        conn.execute(
            "UPDATE hubs SET ai_status = ?, ai_summary = ?, ai_updated_at = ? WHERE hub_id = ?",
            (status, summary, updated_at, hub_id),
        )


def save_hub_camera_source(hub_id: str, camera_source: str) -> None:
    with _connection() as conn:
        conn.execute(
            f"""
            INSERT INTO hubs (hub_id, state, camera_source) VALUES (?, '{}', ?)
            ON CONFLICT (hub_id) DO UPDATE SET camera_source = excluded.camera_source
            """,
            (hub_id, camera_source),
        )


def save_hub_plants(hub_id: str, plants: dict) -> None:
    with _connection() as conn:
        conn.execute(
            """
            INSERT INTO hubs (hub_id, state, plants) VALUES (?, '{}', ?)
            ON CONFLICT (hub_id) DO UPDATE SET plants = excluded.plants
            """,
            (hub_id, json.dumps(plants))
        )


def _parse_plants(raw: Optional[str]) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def load_hubs() -> List[dict]:
    with _connection() as conn:
        rows = conn.execute(
            "SELECT hub_id, state, last_telemetry_at, telemetry_interval, low_water_streak, "
            "ai_status, ai_summary, ai_updated_at, camera_source, plants FROM hubs"
        ).fetchall()
    return [
        {
            "hub_id": hub_id,
            "state": json.loads(state),
            "last_telemetry_at": last_telemetry_at,
            "telemetry_interval": telemetry_interval,
            "low_water_streak": low_water_streak,
            "ai_status": ai_status,
            "ai_summary": ai_summary,
            "ai_updated_at": ai_updated_at,
            "camera_source": camera_source,
            "plants": _parse_plants(plants),
        }
        for (
            hub_id, state, last_telemetry_at, telemetry_interval, low_water_streak,
            ai_status, ai_summary, ai_updated_at, camera_source, plants,
        ) in rows
    ]
