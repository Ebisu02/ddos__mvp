"""
SQLite storage layer.

Tables:
- metrics(ts, rps, bps, unique_src, syn_ratio)
- sources(ts, src_ip, req)                        # request counts by source for the second
- analysis(ts, z_rps, z_bps, score, is_anomaly)
- incidents(id, start_ts, end_ts, kind, severity, details)
"""
from __future__ import annotations

import sqlite3
from typing import Optional, Any, Dict, List


DB_PATH_DEFAULT = "storage/ddos.db"


def connect(db_path: str = DB_PATH_DEFAULT) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: str = DB_PATH_DEFAULT) -> None:
    con = connect(db_path)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        ts INTEGER PRIMARY KEY,
        rps INTEGER NOT NULL,
        bps INTEGER NOT NULL,
        unique_src INTEGER NOT NULL,
        syn_ratio REAL NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        ts INTEGER NOT NULL,
        src_ip TEXT NOT NULL,
        req INTEGER NOT NULL,
        PRIMARY KEY (ts, src_ip),
        FOREIGN KEY(ts) REFERENCES metrics(ts)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS analysis (
        ts INTEGER PRIMARY KEY,
        z_rps REAL NOT NULL,
        z_bps REAL NOT NULL,
        score REAL NOT NULL,
        is_anomaly INTEGER NOT NULL,
        FOREIGN KEY(ts) REFERENCES metrics(ts)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_ts INTEGER NOT NULL,
        end_ts INTEGER NOT NULL,
        kind TEXT NOT NULL,
        severity TEXT NOT NULL,
        details TEXT NOT NULL
    )
    """)

    # helpful indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sources_ts ON sources(ts)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sources_ip ON sources(src_ip)")

    con.commit()
    con.close()


def insert_metric(db_path: str, ts: int, rps: int, bps: int, unique_src: int, syn_ratio: float) -> None:
    con = connect(db_path)
    con.execute(
        "INSERT OR REPLACE INTO metrics(ts, rps, bps, unique_src, syn_ratio) VALUES(?,?,?,?,?)",
        (ts, rps, bps, unique_src, syn_ratio),
    )
    con.commit()
    con.close()


def insert_sources(db_path: str, ts: int, sources: List[Dict[str, Any]]) -> None:
    """
    sources: list of dicts: {"src_ip": str, "req": int}
    """
    if not sources:
        return
    con = connect(db_path)
    con.executemany(
        "INSERT OR REPLACE INTO sources(ts, src_ip, req) VALUES(?,?,?)",
        [(ts, s["src_ip"], int(s["req"])) for s in sources],
    )
    con.commit()
    con.close()


def fetch_metrics(db_path: str, since_ts: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
    con = connect(db_path)
    if since_ts is None:
        rows = con.execute("SELECT * FROM metrics ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM metrics WHERE ts >= ? ORDER BY ts ASC LIMIT ?", (since_ts, limit)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def insert_analysis(db_path: str, ts: int, z_rps: float, z_bps: float, score: float, is_anomaly: bool) -> None:
    con = connect(db_path)
    con.execute(
        "INSERT OR REPLACE INTO analysis(ts, z_rps, z_bps, score, is_anomaly) VALUES(?,?,?,?,?)",
        (ts, float(z_rps), float(z_bps), float(score), 1 if is_anomaly else 0),
    )
    con.commit()
    con.close()


def fetch_analysis(db_path: str, limit: int = 500) -> List[Dict[str, Any]]:
    con = connect(db_path)
    rows = con.execute("""
        SELECT a.ts, a.z_rps, a.z_bps, a.score, a.is_anomaly,
               m.rps, m.bps, m.unique_src, m.syn_ratio
        FROM analysis a
        JOIN metrics m ON m.ts = a.ts
        ORDER BY a.ts DESC
        LIMIT ?
    """, (limit,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def insert_incident(db_path: str, start_ts: int, end_ts: int, kind: str, severity: str, details: str) -> None:
    con = connect(db_path)
    con.execute(
        "INSERT INTO incidents(start_ts, end_ts, kind, severity, details) VALUES(?,?,?,?,?)",
        (start_ts, end_ts, kind, severity, details),
    )
    con.commit()
    con.close()


def fetch_incidents(db_path: str, limit: int = 100) -> List[Dict[str, Any]]:
    con = connect(db_path)
    rows = con.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def fetch_top_sources(db_path: str, limit: int = 5, window_seconds: int = 3600) -> List[Dict[str, Any]]:
    """
    Return top sources by request counts for the recent time window (default: last hour),
    but bounded by the latest timestamp present in DB (so it works with synthetic data).
    """
    con = connect(db_path)
    row = con.execute("SELECT MAX(ts) AS max_ts FROM metrics").fetchone()
    if row is None or row["max_ts"] is None:
        con.close()
        return []
    max_ts = int(row["max_ts"])
    min_ts = max_ts - int(window_seconds)

    rows = con.execute("""
        SELECT src_ip, SUM(req) AS cnt
        FROM sources
        WHERE ts BETWEEN ? AND ?
        GROUP BY src_ip
        ORDER BY cnt DESC
        LIMIT ?
    """, (min_ts, max_ts, limit)).fetchall()
    con.close()
    return [{"src_ip": r["src_ip"], "count": int(r["cnt"])} for r in rows]
