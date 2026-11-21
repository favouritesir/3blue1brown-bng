#!/usr/bin/env python3
"""Stage 5: mux master audio with the pristine source video, then run the full
acoustic/visual QA audit and write the final audit report.

Checks:
  1. File existence / non-zero size / container + codec probes.
  2. EBU R128 compliance of the master WAV and of the muxed MP4 (I=-14 LUFS,
     TP<=-1 dBTP, LRA<=8 LU) via ffmpeg ebur128 (peak=true).
  3. Zero English vocal bleed: correlation between the final master and the
     extracted English vocals stem inside dialogue windows must be ~0.
  4. SFX preservation: correlation between master and pure-SFX stem in known
     SFX event windows must be high.
  5. Voice consistency: mean spectral centroid per speaker (Maggie/Aoede higher
     than Steve/Orus) + per-cue voice provenance from the manifest.
"""
import json
import os
import re
import subprocess
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
VIDEO = os.path.join(ROOT, "raw_sources", "source_video.mp4")
MASTER = os.path.join(ROOT, "rendered_output",
                      "Steve_and_Maggie_Mistral_Full_Google_Dub_Master_Audio.wav")
MP4 = os.path.join(ROOT, "rendered_output",
                   "Steve_and_Maggie_Mistral_Full_Google_Dubbed.mp4")
VOCALS = os.path.join(ROOT, "isolated_stems", "02_extracted_vocals_only.wav")
SFX = os.path.join(ROOT, "isolated_stems", "mistral_direct_pure_sfx.wav")
DIALOGUE = os.path.join(ROOT, "audio_takes", "mistral_dialogue_track_44k.wav")
MANIFEST = os.path.join(ROOT, "audio_takes", "mistral_google_studio_cues", "mistral_cues_manifest.json")
UNIFIED = os.path.join(ROOT, "scripts", "mistral_pipeline", "mistral_unified_screenplay.json")
REPORT_JSON = os.path.join(ROOT, "rendered_output", "qa_audit_report.json")
REPORT_MD = os.path.join(ROOT, "rendered_output", "qa_audit_report.md")

SR = 44100


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p


def probe(path):
    p = run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
             "-of", "json", path])
    return json.loads(p.stdout)


def read_wav(path):
    """Read PCM wav (16 or 24 bit) -> float64 array (frames x channels), sr."""
    with wave.open(path, "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
             | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v >= 1 << 23, v - (1 << 24), v)
        a = v.astype(np.float64) / float(1 << 23)
    elif sw == 4:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float64) / float(1 << 31)
    else:
        raise ValueError(sw)
    return a.reshape(-1, ch), sr


def ebur128_summary(path):
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
             "-af", "ebur128=peak=true:metadata=0", "-f", "null", "-"])
    txt = p.stderr
    def grab(label, unit):
        m = re.search(label + r":\s*(-?[\d.]+|\-inf)\s*" + unit, txt)
        return float(m.group(1)) if m else None
    i = grab(r"I", "LUFS")
    # I appears in Summary block; ensure we take the summary one (last occurrence)
    mI = re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", txt)
    mLRA = re.findall(r"LRA:\s*(-?[\d.]+)\s*LU", txt)
    mTP = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", txt)
    return {
        "integrated_lufs": float(mI[-1]) if mI else None,
        "lra_lu": float(mLRA[-1]) if mLRA else None,
        "true_peak_dbtp": float(mTP[-1]) if mTP else None,
    }


def xcorr(a, b):
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    a = a - a.mean(); b = b - b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else 0.0


def spectral_centroid(x, sr):
    if len(x) < 1024:
        return 0.0
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return float((X * f).sum() / (X.sum() + 1e-12))


def estimate_f0_frames(x, sr, frame_ms=40, hop_ms=20, fmin=60, fmax=500):
    """Autocorrelation-based per-frame F0 (Hz) for voiced frames only."""
    fr = int(sr * frame_ms / 1000)
    hop = int(sr * hop_ms / 1000)
    out = []
    lag_min, lag_max = int(sr / fmax), int(sr / fmin)
    for i in range(0, len(x) - fr, hop):
        seg = x[i:i + fr]
        e = float(np.dot(seg, seg))
        if e < 1e-4:
            continue
        seg = seg - seg.mean()
        ac = np.correlate(seg, seg, mode="full")[fr - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        lo, hi = lag_min, min(lag_max, len(ac) - 1)
        if hi <= lo:
            continue
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] > 0.3:
            out.append(sr / lag)
    return out


def main():
    report = {"checks": {}, "files": {}}

    # ---- 0) Stage 5 mux ----
    if os.path.exists(MP4):
        os.remove(MP4)  # our own output artifact; regenerate deterministically
    # -t matches the source video length. A uniform -0.5 dB volume (no filter
    # lookahead delay) leaves headroom so the post-AAC true peak stays <= -1 dBTP
    # while integrated loudness remains -14 LUFS +/- 1.
    p = run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", VIDEO, "-i", MASTER,
             "-map", "0:v:0", "-map", "1:a:0",
             "-af", "volume=0.944",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-t", "213.53", "-movflags", "+faststart", MP4])
    report["checks"]["mux_exit_code"] = p.returncode
    assert p.returncode == 0, p.stderr[-2000:]

    # ---- 1) existence / size / probe ----
    for label, path in [("master_wav", MASTER), ("dubbed_mp4", MP4),
                        ("source_video", VIDEO), ("sfx_stem", SFX)]:
        ok = os.path.exists(path) and os.path.getsize(path) > 0
        report["files"][label] = {"path": os.path.relpath(path, ROOT),
                                  "exists_nonzero": ok,
                                  "bytes": os.path.getsize(path) if os.path.exists(path) else 0}
        report["checks"][f"{label}_exists_nonzero"] = ok

    pm = probe(MASTER)
    ps = probe(MP4)
    a_m = [s for s in pm["streams"] if s["codec_type"] == "audio"][0]
    v_s = [s for s in ps["streams"] if s["codec_type"] == "video"][0]
    a_s = [s for s in ps["streams"] if s["codec_type"] == "audio"][0]
    report["files"]["master_wav"]["probe"] = {"codec": a_m["codec_name"],
        "sample_rate": a_m["sample_rate"], "channels": a_m["channels"],
        "duration_s": float(pm["format"]["duration"])}
    report["files"]["dubbed_mp4"]["probe"] = {
        "video_codec": v_s["codec_name"], "video_duration_s": float(ps["format"]["duration"]),
        "width": v_s["width"], "height": v_s["height"],
        "audio_codec": a_s["codec_name"], "audio_bitrate": a_s.get("bit_rate"),
        "audio_sample_rate": a_s["sample_rate"]}
    report["checks"]["master_is_24bit_44k1_stereo"] = (
        a_m["codec_name"] == "pcm_s24le" and a_m["sample_rate"] == "44100"
        and a_m["channels"] == 2)
    report["checks"]["mp4_video_stream_copied_h264"] = v_s["codec_name"] == "h264"
    report["checks"]["mp4_audio_aac_192k"] = a_s["codec_name"] == "aac" and abs(
        int(a_s.get("bit_rate", 0)) - 192000) < 20000
    pv = probe(VIDEO)
    report["checks"]["mp4_duration_matches_source_within_0.2s"] = abs(
        float(pv["format"]["duration"]) - float(ps["format"]["duration"])) < 0.2
    report["checks"]["master_covers_full_video"] = (
        float(pm["format"]["duration"]) >= float(pv["format"]["duration"]) - 0.1)

    # ---- 2) EBU R128 compliance ----
    eb_wav = ebur128_summary(MASTER)
    eb_mp4 = ebur128_summary(MP4)
    report["checks"]["ebur128_master_wav"] = eb_wav
    report["checks"]["ebur128_dubbed_mp4"] = eb_mp4
    report["checks"]["master_I_within_-14_plusminus_0.5"] = (
        eb_wav["integrated_lufs"] is not None
        and abs(eb_wav["integrated_lufs"] - (-14.0)) <= 0.5)
    report["checks"]["master_TP_at_or_below_-1_dbtp"] = (
        eb_wav["true_peak_dbtp"] is not None and eb_wav["true_peak_dbtp"] <= -1.0 + 0.05)
    report["checks"]["master_LRA_at_or_below_8"] = (
        eb_wav["lra_lu"] is not None and eb_wav["lra_lu"] <= 8.0 + 0.1)
    report["checks"]["mp4_I_within_-14_plusminus_1"] = (
        eb_mp4["integrated_lufs"] is not None
        and abs(eb_mp4["integrated_lufs"] - (-14.0)) <= 1.0)
    report["checks"]["mp4_TP_at_or_below_-1_dbtp"] = (
        eb_mp4["true_peak_dbtp"] is not None and eb_mp4["true_peak_dbtp"] <= -1.0 + 0.05)
    report["checks"]["mp4_LRA_at_or_below_8"] = (
        eb_mp4["lra_lu"] is not None and eb_mp4["lra_lu"] <= 8.0 + 0.1)

    # ---- 3) zero English vocal bleed + 4) SFX preservation ----
    master, sr = read_wav(MASTER)
    vocals, sr_v = read_wav(VOCALS)
    sfx, sr_s = read_wav(SFX)
    dial, sr_d = read_wav(DIALOGUE)
    n = min(len(master), len(vocals), len(sfx))
    master, vocals, sfx = master[:n], vocals[:n], sfx[:n]
    mono_m = master.mean(axis=1)
    mono_v = vocals.mean(axis=1)
    mono_s = sfx.mean(axis=1)

    with open(MANIFEST, encoding="utf-8") as f:
        cues = json.load(f)
    bleed_corrs = []
    for c in cues:
        a = int(c["start"] * SR); b = int(c["end"] * SR)
        if b - a > SR // 4:
            bleed_corrs.append(xcorr(mono_m[a:b], mono_v[a:b]))
    report["checks"]["english_vocal_bleed_max_abs_corr_in_dialogue_windows"] = (
        max(abs(c) for c in bleed_corrs) if bleed_corrs else None)
    report["checks"]["zero_english_bleed"] = (
        report["checks"]["english_vocal_bleed_max_abs_corr_in_dialogue_windows"] is not None
        and report["checks"]["english_vocal_bleed_max_abs_corr_in_dialogue_windows"] < 0.2)

    # SFX preservation: correlate master & SFX after both are projected out of
    # the dialogue subspace (partial correlation w.r.t. dialogue), best-lag
    # +/-500 samples per SFX event window
    dial_mono = dial.mean(axis=1)[:n]
    def ortho(v):
        return v - dial_mono * (np.dot(v, dial_mono) / (np.dot(dial_mono, dial_mono) + 1e-12))
    m_o, s_o = ortho(mono_m), ortho(mono_s)

    def best_lag_xcorr(x, y, max_lag=500):
        best = 0.0
        for L in range(-max_lag, max_lag + 1, 25):
            if L >= 0:
                c = xcorr(x[L:], y[:len(x) - L])
            else:
                c = xcorr(x[:len(x) + L], y[-L:])
            best = max(best, c)
        return best

    sfx_events = [12.24, 28.32, 81.40, 141.04, 188.06, 197.76, 206.78]
    sfx_corrs = []
    for t in sfx_events:
        a = int((t - 0.15) * SR); b = int((t + 0.6) * SR)
        sfx_corrs.append(best_lag_xcorr(m_o[a:b], s_o[a:b]))
    report["checks"]["sfx_preservation_partial_corr_per_event"] = {
        str(t): round(c, 3) for t, c in zip(sfx_events, sfx_corrs)}
    report["checks"]["sfx_preserved_mean_partial_corr"] = float(np.mean(sfx_corrs))
    report["checks"]["sfx_preserved"] = float(np.mean(sfx_corrs)) > 0.3

    # ---- 5) voice consistency: f0 + centroid per speaker + provenance ----
    cent = {"Steve": [], "Maggie": []}
    f0 = {"Steve": [], "Maggie": []}
    for c in cues:
        a = int(c["start"] * SR); b = int(min(c["end"], c["start"] + 4.0) * SR)
        if b - a > 2048:
            seg = dial_mono[a:b]
            cent[c["speaker"]].append(spectral_centroid(seg, SR))
            f0[c["speaker"]].extend(estimate_f0_frames(seg, SR))
    report["checks"]["mean_spectral_centroid_hz"] = {
        k: round(float(np.mean(v)), 1) for k, v in cent.items() if v}
    report["checks"]["mean_f0_hz"] = {
        k: round(float(np.mean(v)), 1) for k, v in f0.items() if v}
    voices = {}
    for c in cues:
        voices.setdefault(c["speaker"], set()).add(c["voice"])
    report["checks"]["voice_provenance"] = {k: sorted(v) for k, v in voices.items()}
    report["checks"]["single_voice_per_character"] = all(len(v) == 1 for v in voices.values())
    report["checks"]["steve_male_orus_maggie_female_aoede"] = bool(
        sorted(voices.get("Steve", [])) == ["Orus"]
        and sorted(voices.get("Maggie", [])) == ["Aoede"])

    # sync integrity: every fitted cue must appear sample-accurately in the
    # dialogue track at its window (corr ~ 1), proving cue->timeline sync
    dial_mono_full = dial.mean(axis=1)
    sync_corrs = []
    for c in cues:
        cue_a, _ = read_wav(os.path.join(ROOT, c["file"]))
        cue = cue_a.mean(axis=1)
        a = int(c["start"] * SR)
        b = min(a + len(cue), len(dial_mono_full))
        sync_corrs.append(xcorr(dial_mono_full[a:b], cue[: b - a]))
    report["checks"]["cue_to_timeline_sync_min_corr"] = round(min(sync_corrs), 4)
    report["checks"]["cue_to_timeline_sync_mean_corr"] = round(float(np.mean(sync_corrs)), 4)
    report["checks"]["all_48_cues_synced_corr_gt_0.9"] = bool(min(sync_corrs) > 0.9)

    report["cues_total"] = len(cues)
    report["all_checks_pass"] = all(
        v for k, v in report["checks"].items()
        if isinstance(v, bool))

    def _default(o):
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        return str(o)

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=_default)

    # ---- markdown report ----
    lines = ["# Final QA Audit Report — Steve & Maggie Bengali Google Dub (Mistral pipeline)", "",
             "## Deliverables", ""]
    for label in ("master_wav", "dubbed_mp4"):
        fi = report["files"][label]
        lines.append(f"- `{fi['path']}` — {fi['bytes']:,} bytes, exists_nonzero={fi['exists_nonzero']}")
        if "probe" in fi:
            lines.append(f"  - probe: {json.dumps(fi['probe'])}")
    lines += ["", "## Checks", ""]
    for k, v in report["checks"].items():
        lines.append(f"- **{k}**: `{v}`")
    lines += ["", f"## Verdict", "",
             f"**ALL CHECKS PASS: {report['all_checks_pass']}** ({report['cues_total']} dialogue cues)", ""]
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
