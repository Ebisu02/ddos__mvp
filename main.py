from __future__ import annotations

import argparse
import json
import os
import threading
import time
from typing import List, Dict, Any

from storage.database import init_db, insert_metric, insert_sources, fetch_metrics, insert_analysis, insert_incident, DB_PATH_DEFAULT
from data_collector.traffic_collector import generate_stream
from analyzer.anomaly_detector import detect_points
from api.server import serve
from ui.templates import render_dashboard


def load_config() -> Dict[str, Any]:
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_init_db(args):
    init_db(args.db)
    print(f"[db] initialized: {args.db}")


def cmd_generate(args):
    cfg = load_config()
    init_db(args.db)
    start_ts = int(time.time())
    for p in generate_stream(seconds=args.seconds, start_ts=start_ts, ddos_probability=args.ddos_prob):
        insert_metric(args.db, p.ts, p.rps, p.bps, p.unique_src, p.syn_ratio)
        insert_sources(args.db, p.ts, p.sources)
    print(f"[gen] wrote {args.seconds} points into {args.db}")


def cmd_analyze(args):
    cfg = load_config()
    init_db(args.db)
    pts = fetch_metrics(args.db, since_ts=None, limit=args.limit)
    # fetch_metrics returns DESC; detector expects ASC
    pts = list(reversed(pts))

    results = detect_points(
        pts,
        window_size=cfg["window_size"],
        z_threshold=cfg["z_threshold"],
        rps_hard_threshold=cfg["rps_hard_threshold"],
        bps_hard_threshold=cfg["bps_hard_threshold"],
        min_consecutive_points=cfg["min_consecutive_points"],
    )

    # write analysis + incidents (simple grouping of consecutive anomalies)
    in_incident = False
    start_ts = None

    for r in results:
        insert_analysis(args.db, r.ts, r.z_rps, r.z_bps, r.score, r.is_anomaly)

        if r.is_anomaly and not in_incident:
            in_incident = True
            start_ts = r.ts
        if not r.is_anomaly and in_incident:
            end_ts = r.ts
            _write_incident(args.db, start_ts, end_ts, results, cfg)
            in_incident = False
            start_ts = None

    # if ends inside incident
    if in_incident and start_ts is not None:
        end_ts = results[-1].ts
        _write_incident(args.db, start_ts, end_ts, results, cfg)

    print(f"[an] analyzed {len(results)} points; analysis+incidents updated")


def _write_incident(db_path: str, start_ts: int, end_ts: int, results, cfg):
    duration = max(1, end_ts - start_ts)
    # Severity heuristic
    severity = "medium"
    if duration >= 15:
        severity = "high"
    details = f"anomaly window: {start_ts}-{end_ts}; duration={duration}s; thresholds: z>={cfg['z_threshold']} or hard"
    insert_incident(db_path, start_ts, end_ts, "traffic_spike", severity, details)


def cmd_run(args):
    cfg = load_config()
    init_db(args.db)

    stop = threading.Event()

    def producer():
        # online loop
        ts = int(time.time())
        while not stop.is_set():
            for p in generate_stream(seconds=1, start_ts=ts, ddos_probability=args.ddos_prob):
                insert_metric(args.db, p.ts, p.rps, p.bps, p.unique_src, p.syn_ratio)
                insert_sources(args.db, p.ts, p.sources)
        insert_sources(args.db, p.ts, p.sources)
        ts = p.ts + 1
        time.sleep(1)

    def analyzer_loop():
        while not stop.is_set():
            try:
                # analyze last N points frequently
                pts = fetch_metrics(args.db, since_ts=None, limit=args.limit)
                pts = list(reversed(pts))
                results = detect_points(
                    pts,
                    window_size=cfg["window_size"],
                    z_threshold=cfg["z_threshold"],
                    rps_hard_threshold=cfg["rps_hard_threshold"],
                    bps_hard_threshold=cfg["bps_hard_threshold"],
                    min_consecutive_points=cfg["min_consecutive_points"],
                )

                # write analysis
                for r in results[-50:]:
                    insert_analysis(args.db, r.ts, r.z_rps, r.z_bps, r.score, r.is_anomaly)

                # very simple incident detection over last window
                recent = results[-cfg["window_size"]:]
                anomalies = [r for r in recent if r.is_anomaly]
                if len(anomalies) >= cfg["min_consecutive_points"]:
                    start_ts = anomalies[0].ts
                    end_ts = anomalies[-1].ts
                    _write_incident(args.db, start_ts, end_ts, results, cfg)

            except Exception as e:
                print("[an-loop] error:", e)
            time.sleep(2)

    t1 = threading.Thread(target=producer, daemon=True)
    t2 = threading.Thread(target=analyzer_loop, daemon=True)
    t1.start()
    t2.start()

    try:
        serve(args.host, args.port, args.db, render_dashboard)
    finally:
        stop.set()
        print("[run] stopping...")


def build_parser():
    p = argparse.ArgumentParser(prog="ddos_mvp", description="Practice DDoS detection MVP")
    p.add_argument("--db", default=DB_PATH_DEFAULT, help="path to sqlite db (default: storage/ddos.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("init-db", help="initialize sqlite db")
    s1.set_defaults(func=cmd_init_db)

    s2 = sub.add_parser("generate", help="generate synthetic metrics and store to db")
    s2.add_argument("--seconds", type=int, default=120)
    s2.add_argument("--ddos-prob", type=float, default=0.08)
    s2.set_defaults(func=cmd_generate)

    s3 = sub.add_parser("analyze", help="analyze stored metrics and write analysis/incidents")
    s3.add_argument("--limit", type=int, default=600)
    s3.set_defaults(func=cmd_analyze)

    s4 = sub.add_parser("run", help="run web dashboard + background generator/analyzer")
    s4.add_argument("--host", default="127.0.0.1")
    s4.add_argument("--port", type=int, default=8000)
    s4.add_argument("--limit", type=int, default=600)
    s4.add_argument("--ddos-prob", type=float, default=0.08)
    s4.set_defaults(func=cmd_run)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
