#!/usr/bin/env python3
"""Diagnostic: dump the silence-gap structure of both master takes."""
import os
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TAKES = os.path.join(ROOT, "audio_takes", "google_studio_masters")


def energy_db(x, sr, win_ms=20, hop_ms=5):
    win = max(1, int(sr * win_ms / 1000))
    hop = max(1, int(sr * hop_ms / 1000))
    n = max(0, (len(x) - win) // hop + 1)
    e = np.empty(n)
    for i in range(n):
        seg = x[i * hop: i * hop + win]
        e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg * seg)) + 1e-9)
    return e, hop


for fname, expected in [("steve_master_take_google_studio.wav", 40),
                        ("maggie_master_take_google_studio.wav", 8)]:
    x, sr = sf.read(os.path.join(TAKES, fname), dtype="float64")
    if x.ndim > 1:
        x = x.mean(axis=1)
    T = len(x) / sr
    print(f"\n=== {fname}: {T:.3f}s @ {sr} Hz, expected {expected} phrases ===")
    e, hop = energy_db(x, sr)
    hop_s = hop / sr
    print(f"envelope: min {e.min():.1f} dB, p10 {np.percentile(e,10):.1f}, "
          f"median {np.percentile(e,50):.1f}, p90 {np.percentile(e,90):.1f}, max {e.max():.1f} dB")
    for thresh in (-30, -35, -40, -45, -50, -55, -60):
        quiet = e < thresh
        gaps = []
        i, n = 0, len(e)
        while i < n:
            if quiet[i]:
                j = i
                while j < n and quiet[j]:
                    j += 1
                if (j - i) * hop_s >= 0.05:
                    gaps.append((i * hop_s, (j - i) * hop_s))
                i = j
            else:
                i += 1
        print(f"thresh {thresh} dB: {len(gaps)} gaps >=50ms -> {len(gaps)+1} segments")
    # detail at -45 dB
    thresh = -45.0
    quiet = e < thresh
    gaps = []
    i, n = 0, len(e)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * hop_s >= 0.05:
                gaps.append((i * hop_s, (j - i) * hop_s))
            i = j
        else:
            i += 1
    print(f"gaps >=50ms @ -45dB (start_s, dur_s):")
    for g in gaps:
        print(f"   {g[0]:7.3f}  {g[1]:6.3f}")
