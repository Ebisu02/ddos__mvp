"""
Synthetic traffic generator (collector).

Generates per-second aggregate metrics:
- rps: requests per second
- bps: bytes per second
- unique_src: approximate unique sources
- syn_ratio: ratio of SYN packets (simplified signal for SYN flood)

Additionally generates "top sources" list for each second:
- sources: list of {"src_ip": str, "req": int}

This is a simulation for practice project.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Iterator, Optional, List, Dict, Any


@dataclass
class MetricPoint:
    ts: int
    rps: int
    bps: int
    unique_src: int
    syn_ratio: float
    label: str  # "normal" or "attack"
    sources: List[Dict[str, Any]]  # top sources by req


def _rand_ip(private: bool = False) -> str:
    if private:
        # 10.x.x.x
        return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    # public-ish range (not real, demo)
    return f"{random.randint(80, 185)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def _make_sources(total_rps: int, unique_src: int, attack: bool) -> List[Dict[str, Any]]:
    # We will output top 5 sources. In attack mode, top sources are more skewed.
    top_n = 5
    ips = [_rand_ip(private=False) for _ in range(top_n)]

    if attack:
        # heavy hitters + long tail (compressed into unique_src)
        base = max(50, int(total_rps * 0.18))
        counts = [
            base + random.randint(0, int(total_rps * 0.06)),
            int(total_rps * 0.16) + random.randint(0, int(total_rps * 0.05)),
            int(total_rps * 0.12) + random.randint(0, int(total_rps * 0.04)),
            int(total_rps * 0.09) + random.randint(0, int(total_rps * 0.03)),
            int(total_rps * 0.06) + random.randint(0, int(total_rps * 0.02)),
        ]
    else:
        # more even distribution
        base = max(10, int(total_rps / max(10, top_n)))
        counts = [max(1, int(random.gauss(base, base*0.15))) for _ in range(top_n)]

    # normalize to not exceed total_rps too much
    s = sum(counts)
    if s > 0:
        scale = min(1.0, total_rps / s)
        counts = [max(1, int(c * scale)) for c in counts]

    sources = [{"src_ip": ip, "req": int(cnt)} for ip, cnt in zip(ips, counts)]
    sources.sort(key=lambda x: x["req"], reverse=True)
    return sources


def generate_stream(
    seconds: int,
    start_ts: Optional[int] = None,
    ddos_probability: float = 0.08,
) -> Iterator[MetricPoint]:
    """
    Generate `seconds` points. With some probability, start an 'attack burst'
    lasting 10-25 seconds.
    """
    if start_ts is None:
        start_ts = int(time.time())

    t = start_ts
    attack_left = 0

    for _ in range(seconds):
        # Decide to start a burst
        if attack_left == 0 and random.random() < ddos_probability:
            attack_left = random.randint(10, 25)

        if attack_left > 0:
            # Attack mode
            label = "attack"
            rps = int(random.gauss(1600, 220))
            bps = int(random.gauss(110_000_000, 12_000_000))
            unique_src = int(random.gauss(1800, 250))
            syn_ratio = max(0.0, min(1.0, random.gauss(0.72, 0.08)))
            sources = _make_sources(rps, unique_src, attack=True)
            attack_left -= 1
        else:
            # Normal mode
            label = "normal"
            rps = max(50, int(random.gauss(420, 60)))
            bps = max(5_000_000, int(random.gauss(28_000_000, 5_000_000)))
            unique_src = max(30, int(random.gauss(220, 40)))
            syn_ratio = max(0.0, min(1.0, random.gauss(0.18, 0.05)))
            sources = _make_sources(rps, unique_src, attack=False)

        yield MetricPoint(ts=t, rps=rps, bps=bps, unique_src=unique_src, syn_ratio=syn_ratio, label=label, sources=sources)
        t += 1
