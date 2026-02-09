"""
Anomaly detector for DDoS.

Approach (simple and explainable):
- Maintain rolling window for rps and bps.
- Compute z-score for current point vs window mean/std.
- Also apply hard thresholds (rps_hard_threshold, bps_hard_threshold).
- Mark anomaly when score >= threshold and repeats for N consecutive points.

This is a practice-friendly baseline; easy to justify in report.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any


@dataclass
class DetectionResult:
    ts: int
    z_rps: float
    z_bps: float
    score: float
    is_anomaly: bool
    kind: str  # e.g. "traffic_spike"


def _mean_std(values: List[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    m = sum(values) / len(values)
    var = sum((x - m) ** 2 for x in values) / len(values)
    std = math.sqrt(var)
    return m, std


def detect_points(
    points: List[Dict[str, Any]],
    window_size: int = 30,
    z_threshold: float = 3.0,
    rps_hard_threshold: int = 1200,
    bps_hard_threshold: int = 80_000_000,
    min_consecutive_points: int = 3,
) -> List[DetectionResult]:
    results: List[DetectionResult] = []
    recent_rps: List[float] = []
    recent_bps: List[float] = []
    consec = 0

    for p in points:
        rps = float(p["rps"])
        bps = float(p["bps"])

        # Use previous window to compute stats
        m_rps, s_rps = _mean_std(recent_rps[-window_size:])
        m_bps, s_bps = _mean_std(recent_bps[-window_size:])

        # Avoid division by zero
        z_rps = 0.0 if s_rps == 0 else (rps - m_rps) / s_rps
        z_bps = 0.0 if s_bps == 0 else (bps - m_bps) / s_bps

        # Score combines both signals
        score = max(abs(z_rps), abs(z_bps))

        hard_hit = (rps >= rps_hard_threshold) or (bps >= bps_hard_threshold)

        is_candidate = hard_hit or (score >= z_threshold)

        if is_candidate:
            consec += 1
        else:
            consec = 0

        is_anomaly = consec >= min_consecutive_points

        kind = "traffic_spike" if is_anomaly else "none"

        results.append(DetectionResult(
            ts=int(p["ts"]),
            z_rps=float(z_rps),
            z_bps=float(z_bps),
            score=float(score),
            is_anomaly=bool(is_anomaly),
            kind=kind,
        ))

        recent_rps.append(rps)
        recent_bps.append(bps)

    return results
