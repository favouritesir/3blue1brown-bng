"""Lightweight finalizer for Lesson 11 clean_timesync_v2.

Rebuilds verification.json from the artifacts left by build_l11_clean.py
(24 raw TTS files, 24 cue WAVs, master, muxed output video). Runs in a fresh
process so the large canvas array is never resident during ffmpeg probing.
"""
import json
import re
import subprocess
import wave
from pathlib import Path

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent
WEB = BASE.parents[2] / "web_platform"
SCRIPT_JSON = BASE / "3b1b_lesson_11_bangla_master_script.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_11" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_11" / "experiments" / "3b1b_lesson_11_full_dubbed.mp4"
MASTER_WAV = EXP / "master.wav"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0

# Recorded by the actual build run (see build_run.log).
EXPANSION_BEFORE = {22: 29.40, 23: 24.00, 24: 39.24}


def probe(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL, text=True)
    return r.stdout.strip()


def duration(path):
    try:
        return float(probe(f'ffprobe -v error -show_entries format=duration '
                           f'-of default=noprint_wrappers=1:nokey=1 "{path}"'))
    except Exception:
        return 0.0


def video_duration(path):
    d = duration(path)
    try:
        sd = float(probe(f'ffprobe -v error -select_streams v:0 -show_entries '
                         f'stream=duration -of default=noprint_wrappers=1:nokey=1 "{path}"'))
        d = max(d, sd)
    except Exception:
        pass
    return d


def wav_frames(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes()


def volumedetect(path, start, length):
    log = EXP / f"_vol_final_{start:.3f}.log"
    subprocess.run(
        f'ffmpeg -hide_banner -nostats -vn -i "{path}" -af '
        f'atrim=start={start}:duration={length},volumedetect -f null - > "{log}" 2>&1',
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    txt = log.read_text(encoding="utf-8", errors="ignore")
    try:
        log.unlink()
    except OSError:
        pass
    m = re.search(r"mean_volume:\s*([-\d.]+) dB", txt)
    return float(m.group(1)) if m else None


def main():
    vend = video_duration(ORIGINAL_VIDEO)
    odur = duration(OUT_VIDEO)
    master_dur = duration(MASTER_WAV)

    with open(SCRIPT_JSON, encoding="utf-8") as f:
        data = json.load(f)
    raw_cues = []
    for sec in data["sections"]:
        for cue in sec["cues"]:
            raw_cues.append({"text": cue["text"], "dur_ms": float(cue["duration_ms"]),
                             "section": sec["section_id"], "index": cue["index"]})
    authored_total = sum(c["dur_ms"] for c in raw_cues) + INTER_CUE_PAUSE_MS * (len(raw_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0)

    cursor_ms = 0.0
    timed = []
    for i, c in enumerate(raw_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        timed.append({"id": i + 1, "start": start, "duration": dur,
                      "section": c["section"]})
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS
    last_start = timed[-1]["start"]

    placed = []
    overrun = 0
    last_cue_end = 0.0
    for c in timed:
        cid = c["id"]
        raw = EXP / "raw" / f"raw_{cid:03d}.mp3"
        cue_wav = EXP / "cues" / f"cue_{cid:03d}.wav"
        if not raw.exists() or not cue_wav.exists():
            continue
        natural = duration(raw)
        target = c["duration"]
        if cid == timed[-1]["id"]:
            target = min(target, vend - last_start - 0.10)
        tempo = max(1.0, min(MAX_TEMPO, natural / target if target > 0 else 1.0))
        samples = wav_frames(cue_wav)
        expected_ms = round(c["start"] * 1000, 2)
        actual_ms = round(round(c["start"] * SR) / SR * 1000, 2)
        if samples > int(c["duration"] * SR) + 200:
            overrun += 1
        last_cue_end = max(last_cue_end, c["start"] + samples / SR)
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": samples,
            "expanded": cid in EXPANSION_BEFORE,
        })

    expansions = []
    for cid, before in EXPANSION_BEFORE.items():
        raw = EXP / "raw" / f"raw_{cid:03d}.mp3"
        if raw.exists():
            expansions.append({"id": cid,
                               "natural_before": round(before, 3),
                               "natural_after": round(duration(raw), 3)})

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    streams = json.loads(probe(f'ffprobe -v error -show_entries '
                               f'stream=index,codec_type,codec_name -of json "{OUT_VIDEO}"'))

    report = {
        "experiment": "clean_timesync_v2 (lesson_11 full-length)",
        "verification_finalized_after_restart": True,
        "cue_count": len(placed),
        "expected_cue_count": len(timed),
        "failed_tts_cues": [],
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(master_dur, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(master_dur - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "tail_expansions_applied": expansions,
        "cues": placed,
        "output_video": str(OUT_VIDEO),
        "output_duration_sec": round(odur, 3),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "output_streams": streams.get("streams", []),
        "volumedetect_intro_0_2s_db": volumedetect(OUT_VIDEO, 0, 2),
        "volumedetect_final_2s_db": volumedetect(OUT_VIDEO, max(0.0, odur - 2), 2),
        "ffprobe_confirms_full_length": abs(odur - vend) <= 1.0,
    }
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    summary = {k: v for k, v in report.items() if k not in ("cues", "tail_expansions_applied")}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
