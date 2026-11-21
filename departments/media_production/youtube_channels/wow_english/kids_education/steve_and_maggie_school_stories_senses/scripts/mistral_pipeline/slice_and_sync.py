#!/usr/bin/env python3
"""Stage 3: slice the continuous master takes into individual dialogue cues and
synchronize each cue to its exact mouth-movement window on the 213.53 s timeline.

Boundary detection: energy-envelope silence gaps (phrase-boundary candidates),
then a DP forced alignment that assigns the expected-ordered phrases to gaps by
matching segment durations to the target window durations (global speaking-rate
estimated iteratively). Each fitted cue gets raised-cosine (30 ms) edge fades —
no clicks, no pops — and is placed sample-accurately at its window start.

Output: fitted cue WAVs + one full-length Bengali dialogue track (44.1 kHz stereo).
"""
import json
import math
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
TAKES = os.path.join(ROOT, "audio_takes", "mistral_google_studio_masters")
CUES_OUT = os.path.join(ROOT, "audio_takes", "mistral_google_studio_cues")
UNIFIED = os.path.join(SCRIPTS, "mistral_pipeline", "mistral_unified_screenplay.json")
DIALOGUE_TRACK = os.path.join(ROOT, "audio_takes", "mistral_dialogue_track_44k.wav")
MANIFEST = os.path.join(CUES_OUT, "mistral_cues_manifest.json")

SR = 44100      # project rate (masters are 24 kHz mono from the TTS API)
VIDEO_DUR = 213.53
FADE_MS = 30    # raised-cosine edge fade


def read_wav_mono(path):
    with wave.open(path, "rb") as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2, (path, w.getparams())
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
    return data, sr


def write_wav(path, data, sr, stereo=False):
    data = np.clip(data, -1.0, 1.0)
    out = np.stack([data, data], axis=1) if stereo else data
    pcm = (out * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2 if stereo else 1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def energy_db(x, sr, win_ms=20, hop_ms=10):
    win = int(sr * win_ms / 1000)
    hop = int(sr * hop_ms / 1000)
    n = max(0, (len(x) - win) // hop + 1)
    e = np.empty(n)
    for i in range(n):
        seg = x[i * hop: i * hop + win]
        e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg * seg)) + 1e-9)
    return e, hop


def detect_gaps(x, sr, thresh_db=-50.0, min_gap_s=0.12, hop_ms=10):
    """Return list of (gap_start_s, gap_end_s) where energy stays below threshold."""
    e, hop = energy_db(x, sr, hop_ms=hop_ms)
    hop_s = hop / sr
    quiet = e < thresh_db
    gaps = []
    i, n = 0, len(e)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * hop_s >= min_gap_s:
                gaps.append((i * hop_s, j * hop_s))
            i = j
        else:
            i += 1
    return gaps


def dp_align(cands, targets, rate):
    """Choose n-1 internal boundaries among candidate positions so that segment
    durations best match rate*targets (log-ratio cost). Returns boundary indices."""
    n = len(targets)
    m = len(cands)
    INF = float("inf")
    dp = [[INF] * m for _ in range(n)]
    back = [[-1] * m for _ in range(n)]
    for k in range(1, m):
        seg = max(cands[k] - cands[0], 0.05)
        d = max(rate * targets[0], 0.05)
        dp[0][k] = abs(math.log2(seg / d))
    for j in range(1, n):
        tj = max(rate * targets[j], 0.05)
        for k in range(j + 1, m):
            best, bk = INF, -1
            for p in range(j, k):
                if dp[j - 1][p] == INF:
                    continue
                seg = max(cands[k] - cands[p], 0.05)
                c = dp[j - 1][p] + abs(math.log2(seg / tj))
                if c < best:
                    best, bk = c, p
            dp[j][k] = best
            back[j][k] = bk
    # last phrase must end at final candidate
    end = m - 1
    if dp[n - 1][end] == INF:
        raise RuntimeError("DP alignment infeasible")
    idxs = [end]
    for j in range(n - 1, 0, -1):
        end = back[j][end]
        idxs.append(end)
    idxs.append(0)
    idxs.reverse()
    return idxs


def slice_master(x, sr, targets, thresh_db=-50.0, min_gap_s=0.12):
    """Return list of (seg_start_s, seg_samples) — one per target, in order."""
    T = len(x) / sr
    gaps = detect_gaps(x, sr, thresh_db=thresh_db, min_gap_s=min_gap_s)
    cands = sorted(set([0.0] + [(a + b) / 2.0 for a, b in gaps] + [T]))
    n = len(targets)
    rate = (T - 0.5 * max(n - 1, 0) * 0.3) / max(sum(targets), 1e-6)  # rough init
    rate = min(max(rate, 0.5), 2.0)
    idxs = None
    for _ in range(4):
        idxs = dp_align(cands, targets, rate)
        segs = [cands[idxs[i + 1]] - cands[idxs[i]] for i in range(n)]
        rate = min(max(sum(segs) / max(sum(targets), 1e-6), 0.5), 2.0)
    bounds = [cands[i] for i in idxs]
    segs_out = []
    for i in range(n):
        a, b = int(bounds[i] * sr), int(bounds[i + 1] * sr)
        segs_out.append((bounds[i], x[a:b]))
    return segs_out, gaps, bounds, rate


def trim_silence(seg, sr, thresh_db=-50.0, margin_s=0.03):
    e, hop = energy_db(seg, sr, hop_ms=5)
    hop_s = hop / sr
    loud = np.where(e > thresh_db)[0]
    if len(loud) == 0:
        return seg
    a = max(0, int(loud[0] * hop_s * sr) - int(margin_s * sr))
    b = min(len(seg), int(loud[-1] * hop_s * sr + int(margin_s * sr)))
    return seg[a:b]


def resample_linear(x, factor):
    """Time-stretch by `factor` (>1 = longer) via linear interpolation."""
    if abs(factor - 1.0) < 1e-3 or len(x) < 2:
        return x
    n_out = max(1, int(round(len(x) * factor)))
    idx = np.linspace(0, len(x) - 1, n_out)
    return np.interp(idx, np.arange(len(x)), x)


def raised_cosine(n):
    if n <= 1:
        return np.ones(max(n, 1))
    t = np.linspace(0, np.pi, n)
    return 0.5 * (1 - np.cos(t))


def fit_cue(seg, sr_in, start, end):
    """Fit segment into [start, end]: compress if too long, align to window start,
    upsample to 44.1 kHz, apply raised-cosine edge fades."""
    window = end - start
    seg = trim_silence(seg, sr_in)
    dur = len(seg) / sr_in
    target = window - 0.04  # tail margin so the fade never touches the next cue
    factor_eff = 1.0
    if target > 0 and dur > target:
        seg = resample_linear(seg, target / dur)   # speed up to fit the mouth window
        factor_eff = dur / target
    up = resample_linear(seg, SR / sr_in)
    nf = int(SR * FADE_MS / 1000)
    if len(up) > 2 * nf:
        up[:nf] *= raised_cosine(nf)
        up[-nf:] *= raised_cosine(nf)[::-1]
    return up, factor_eff, dur


def main():
    os.makedirs(CUES_OUT, exist_ok=True)
    with open(UNIFIED, encoding="utf-8") as f:
        unified = json.load(f)
    cues = unified["cues"]

    track = np.zeros(int(VIDEO_DUR * SR) + SR, dtype=np.float64)
    manifest = []

    for speaker, fname in [("Steve", "steve_master_take_mistral_google.wav"),
                           ("Maggie", "maggie_master_take_mistral_google.wav")]:
        path = os.path.join(TAKES, fname)
        x, sr_in = read_wav_mono(path)
        spk_cues = [c for c in cues if c["speaker"] == speaker]
        targets = [c["end"] - c["start"] for c in spk_cues]
        segs, gaps, bounds, rate = slice_master(x, sr_in, targets)
        print(f"{speaker}: master {len(x)/sr_in:.1f}s, {len(gaps)} raw gaps, "
              f"aligned {len(segs)} segments (expected {len(spk_cues)}), rate x{rate:.3f}")
        for i, cue in enumerate(spk_cues):
            seg_t0, seg = segs[i]
            fitted, factor_eff, raw_dur = fit_cue(seg, sr_in, cue["start"], cue["end"])
            pos = int(cue["start"] * SR)
            end_pos = min(pos + len(fitted), len(track))
            track[pos:end_pos] += fitted[: end_pos - pos]
            cname = f"fitted_cue_{cue['id']:03d}_{speaker}.wav"
            write_wav(os.path.join(CUES_OUT, cname), fitted, SR)
            manifest.append({
                "id": cue["id"], "speaker": speaker, "voice": cue["voice"],
                "start": cue["start"], "end": cue["end"],
                "window_dur": round(cue["end"] - cue["start"], 3),
                "raw_seg_dur": round(raw_dur, 3), "stretch": round(factor_eff, 4),
                "fitted_dur": round(len(fitted) / SR, 3),
                "master_seg_start_s": round(seg_t0, 3),
                "bn": cue["bn"], "file": os.path.relpath(os.path.join(CUES_OUT, cname), ROOT),
            })
            flag = " <-- compressed" if factor_eff > 1.05 else ""
            print(f"  cue {cue['id']:03d} {speaker}: win {cue['start']:6.1f}-{cue['end']:6.1f}s "
                  f"raw {raw_dur:6.2f}s -> fitted {len(fitted)/SR:6.2f}s (x{factor_eff:.3f}){flag}")

    peak = np.max(np.abs(track))
    if peak > 0.89:
        track *= 0.89 / peak
        print(f"Dialogue track peak-limited to -1.0 dBFS (was {20*np.log10(peak):.1f} dBFS)")
    write_wav(DIALOGUE_TRACK, track, SR, stereo=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    rms = np.sqrt(np.mean(track ** 2))
    print(f"Dialogue track -> {os.path.relpath(DIALOGUE_TRACK, ROOT)} "
          f"({len(track)/SR:.2f}s, peak {20*np.log10(peak+1e-9):.1f} dBFS, rms {20*np.log10(rms+1e-9):.1f} dBFS)")
    print(f"Manifest -> {os.path.relpath(MANIFEST, ROOT)} ({len(manifest)} cues)")


if __name__ == "__main__":
    main()
