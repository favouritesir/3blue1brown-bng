#!/usr/bin/env python3
"""EGM V3 Stage 1: Slice fresh V3 Authentic Google AI Studio master takes
and synchronize all 48 cues onto the 213.53 s video timeline.
"""
import json
import math
import os
import re
import subprocess

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TAKES = os.path.join(ROOT, "audio_takes", "v3_authentic_masters")
CUES_OUT = os.path.join(ROOT, "audio_takes", "v3_authentic_cues")
SCREENPLAY = os.path.join(ROOT, "scripts", "master_screenplay_v3_authentic.json")
DIALOGUE_TRACK = os.path.join(ROOT, "audio_takes", "v3_authentic_dialogue_track_44k.wav")
MANIFEST = os.path.join(CUES_OUT, "v3_authentic_cues_manifest.json")
SFX_STEM = os.path.join(ROOT, "isolated_stems", "mistral_direct_pure_sfx.wav")
TMP = r"C:\Users\Ashik\AppData\Local\Temp\opencode\v3_slice"

SR = 44100            # project rate
FADE_MS = 30          # raised-cosine edge fade
TAIL_MARGIN_S = 0.04  # margin from end of window
THRESH_DB = -42.0     # silence threshold for gap candidates
MIN_CAND_GAP_S = 0.08 # min quiet run

os.makedirs(CUES_OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

def energy_db(x, sr, win_ms=20, hop_ms=5):
    win = max(1, int(sr * win_ms / 1000))
    hop = max(1, int(sr * hop_ms / 1000))
    n = max(0, (len(x) - win) // hop + 1)
    e = np.empty(n)
    for i in range(n):
        seg = x[i * hop: i * hop + win]
        e[i] = 20.0 * np.log10(np.sqrt(np.mean(seg * seg)) + 1e-9)
    return e, hop

def candidate_boundaries(x, sr):
    e, hop = energy_db(x, sr)
    hop_s = hop / sr
    quiet = e < THRESH_DB
    cands = [0.0]
    i, n = 0, len(e)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * hop_s >= MIN_CAND_GAP_S:
                cands.append((i + (j - i) / 2.0) * hop_s)
            i = j
        else:
            i += 1
    cands.append(len(x) / sr)
    return sorted(set(cands))

def expected_durations(cues):
    weights = []
    for c in cues:
        txt = re.sub(r"<[^>]+>", " ", c.get("google_tts_prompt") or c["bn"])
        txt = txt.replace(" ", "")
        weights.append(max(len(txt), 1))
    tot = sum(weights)
    return weights, tot

def dp_align(cands, expected):
    n, m = len(expected), len(cands)
    INF = float("inf")
    dp = [[INF] * m for _ in range(n)]
    back = [[-1] * m for _ in range(n)]
    for k in range(1, m):
        seg = max(cands[k] - cands[0], 1e-3)
        dp[0][k] = abs(math.log2(seg / max(expected[0], 1e-3)))
    for j in range(1, n):
        for k in range(j + 1, m):
            best, bk = INF, -1
            for p in range(j, k):
                if dp[j - 1][p] == INF:
                    continue
                seg = max(cands[k] - cands[p], 1e-3)
                c = dp[j - 1][p] + abs(math.log2(seg / max(expected[j], 1e-3)))
                if c < best:
                    best, bk = c, p
            dp[j][k] = best
            back[j][k] = bk
    end = m - 1
    if dp[n - 1][end] == INF:
        raise RuntimeError("DP alignment infeasible")
    idxs = [end]
    for j in range(n - 1, 0, -1):
        end = back[j][end]
        idxs.append(end)
    idxs.append(0)
    idxs.reverse()
    return [cands[i] for i in idxs], dp[n - 1][m - 1] / n

def slice_master(x, sr, cues):
    T = len(x) / sr
    cands = candidate_boundaries(x, sr)
    weights, tot = expected_durations(cues)
    expected = [T * w / tot for w in weights]
    bounds, cost = dp_align(cands, expected)
    segs = []
    for i in range(len(cues)):
        a, b = int(round(bounds[i] * sr)), int(round(bounds[i + 1] * sr))
        segs.append((bounds[i], x[a:b]))
    return segs, bounds, cost, expected

def trim_silence(seg, sr, thresh_db=-48.0, margin_s=0.03):
    e, hop = energy_db(seg, sr)
    hop_s = hop / sr
    loud = np.where(e > thresh_db)[0]
    if len(loud) == 0:
        return seg
    a = max(0, int(loud[0] * hop_s * sr) - int(margin_s * sr))
    b = min(len(seg), int(loud[-1] * hop_s * sr + int(margin_s * sr)))
    return seg[a:b]

def atempo_compress(seg, sr_in, target_s, tag):
    n_t = max(1, int(round(target_s * SR)))
    dur = len(seg) / sr_in
    if dur <= target_s or dur <= 0:
        ratio = 1.0
    else:
        ratio = min(dur / target_s, 100.0)
    src = os.path.join(TMP, f"seg_{tag}.wav")
    dst = os.path.join(TMP, f"fit_{tag}.wav")
    sf.write(src, seg, sr_in, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", src, "-af", f"atempo={ratio:.6f}",
                    "-ar", str(SR), "-ac", "1", "-c:a", "pcm_f32le", dst], check=True)
    y, sr_o = sf.read(dst, dtype="float64")
    assert sr_o == SR
    if len(y) > n_t:
        y = y[:n_t]
    elif len(y) < n_t:
        y = np.pad(y, (0, n_t - len(y)))
    return y, dur, ratio

def raised_cosine(n):
    if n <= 1:
        return np.ones(max(n, 1))
    t = np.linspace(0, np.pi, n)
    return 0.5 * (1 - np.cos(t))

def main():
    with open(SCREENPLAY, encoding="utf-8") as f:
        sp = json.load(f)
    cues = sp["cues"]
    print(f"Screenplay v{sp['version']}: {len(cues)} cues, video {sp['duration_seconds']}s")

    sfx_info = sf.info(SFX_STEM)
    n_track = sfx_info.frames
    track = np.zeros((n_track, 2), dtype=np.float64)
    manifest = []

    jobs = [
        ("Steve", "steve_master_take_v3_authentic.wav"),
        ("Maggie", "maggie_master_take_v3_authentic.wav")
    ]

    for speaker, fname in jobs:
        path = os.path.join(TAKES, fname)
        x, sr_in = sf.read(path, dtype="float64")
        if x.ndim > 1:
            x = x.mean(axis=1)
        spk_cues = [c for c in cues if c["speaker"] == speaker]
        print(f"\n{speaker}: master {len(x)/sr_in:.2f}s @ {sr_in} Hz, {len(spk_cues)} cues")
        segs, bounds, cost, expected = slice_master(x, sr_in, spk_cues)
        print(f"  DP alignment: {len(bounds)-1} segments, mean log2 cost {cost:.3f}")

        for i, cue in enumerate(spk_cues):
            seg_t0, seg_raw = segs[i]
            seg = trim_silence(seg_raw, sr_in)
            raw_dur = len(seg) / sr_in
            window = cue["end"] - cue["start"]
            next_start = cues[cue["id"]]["start"] if cue["id"] < len(cues) else None
            cap = window
            if next_start is not None:
                cap = min(cap, next_start - cue["start"] - 0.02)
            fit_target = max(cap - TAIL_MARGIN_S, 0.05)

            if raw_dur > fit_target:
                fitted, dur_used, ratio = atempo_compress(seg, sr_in, fit_target,
                                                          f"{cue['id']:03d}_{speaker}")
            else:
                fitted, dur_used, ratio = atempo_compress(seg, sr_in, raw_dur,
                                                          f"{cue['id']:03d}_{speaker}")

            nf = int(SR * FADE_MS / 1000)
            if len(fitted) > 2 * nf:
                fitted[:nf] *= raised_cosine(nf)
                fitted[-nf:] *= raised_cosine(nf)[::-1]

            pos = int(round(cue["start"] * SR))
            end_pos = min(pos + len(fitted), n_track)
            track[pos:end_pos, 0] += fitted[: end_pos - pos]
            track[pos:end_pos, 1] += fitted[: end_pos - pos]

            cname = f"fitted_cue_{cue['id']:03d}_{speaker}.wav"
            sf.write(os.path.join(CUES_OUT, cname), fitted, SR, subtype="PCM_24")
            manifest.append({
                "id": cue["id"], "speaker": speaker, "voice": cue["voice"],
                "start": cue["start"], "end": cue["end"],
                "window_dur": round(window, 3),
                "master_seg_start_s": round(seg_t0, 3),
                "expected_dur_s": round(expected[i], 3),
                "raw_seg_dur": round(raw_dur, 3),
                "tempo_ratio": round(ratio, 4),
                "fitted_dur": round(len(fitted) / SR, 3),
                "fade_ms": FADE_MS,
                "bn": cue["bn"],
                "file": os.path.relpath(os.path.join(CUES_OUT, cname), ROOT),
            })
            flag = " COMPRESSED" if ratio > 1.001 else ""
            print(f"  cue {cue['id']:03d} {speaker}: win {cue['start']:6.2f}-{cue['end']:6.2f}s "
                  f"raw {raw_dur:5.2f}s -> placed {len(fitted)/SR:5.2f}s"
                  f"{' x%.3f' % ratio if ratio > 1.001 else ''}{flag}")

    peak = float(np.abs(track).max())
    if peak > 0.89:
        track *= 0.89 / peak
        print(f"\nDialogue bed peak-limited to 0.89 (was {20*np.log10(peak):.2f} dBFS)")
    sf.write(DIALOGUE_TRACK, track, SR, subtype="PCM_24")
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    rms = float(np.sqrt(np.mean(track ** 2)))
    print(f"\nDialogue bed -> {os.path.relpath(DIALOGUE_TRACK, ROOT)} "
          f"({n_track/SR:.3f}s, peak {20*np.log10(peak+1e-12):.2f} dBFS, rms {20*np.log10(rms+1e-12):.2f} dBFS)")
    print(f"Manifest -> {os.path.relpath(MANIFEST, ROOT)} ({len(manifest)} cues)")

if __name__ == "__main__":
    main()
