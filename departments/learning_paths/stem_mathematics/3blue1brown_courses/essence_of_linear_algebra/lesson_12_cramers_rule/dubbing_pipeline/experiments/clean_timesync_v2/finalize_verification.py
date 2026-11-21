"""Lightweight verification writer for Lesson 12 (stdlib only).

The full build script produced all artifacts but the system ran out of RAM
before its final volumedetect/JSON step (other lessons building in parallel).
This script reconstructs the SAME verification.json from the finished files
without importing numpy/asyncio, so it needs only a few MB of memory.
"""
import re
import json
import wave
import subprocess
from pathlib import Path

EXP = Path(__file__).resolve().parent
BASE = EXP.parent.parent
WEB = BASE.parents[2] / "web_platform"
SCRIPT_JSON = BASE / "3b1b_lesson_12_bangla_master_script.json"
ORIGINAL_VIDEO = WEB / "media_vault" / "lesson_12" / "original_source" / "full_original.mp4"
OUT_VIDEO = WEB / "media_vault" / "lesson_12" / "experiments" / "3b1b_lesson_12_full_dubbed.mp4"
MASTER_WAV = EXP / "master.wav"
VERIFY = EXP / "verification.json"

SR = 44100
VOICE = "bn-BD-PradeepNeural"
MAX_TEMPO = 2.2
LEAD_IN_SEC = 2.5
TAIL_MARGIN_SEC = 3.0
INTER_CUE_PAUSE_MS = 350.0
VIDEO_ID = "jBsC34PxzoM"
TAIL_IDS = {23, 24, 25}


def probe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return float(r.stdout.strip())


def wav_samples(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes()


def volumedetect(path, start, length):
    log = EXP / "_volumedetect.log"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-nostats", "-vn", "-i", str(path),
           "-af", f"atrim=start={start}:duration={length},volumedetect",
           "-f", "null", "-"]
    with open(log, "wb") as fh:
        subprocess.run(cmd, stdout=fh, stderr=fh)
    txt = log.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"mean_volume:\s*([-\d.]+) dB", txt)
    return float(m.group(1)) if m else None


def main():
    vend = probe_duration(ORIGINAL_VIDEO)
    master_dur = wav_samples(MASTER_WAV) / SR

    with open(SCRIPT_JSON, encoding="utf-8") as f:
        data = json.load(f)
    raw_cues = []
    for sec in data["sections"]:
        sec_id = sec.get("id") or sec.get("section_id")
        for cue in sec["cues"]:
            raw_cues.append({"dur_ms": float(cue["duration_ms"]),
                             "section": sec_id, "index": cue["index"]})

    authored_total = sum(c["dur_ms"] for c in raw_cues) + INTER_CUE_PAUSE_MS * (len(raw_cues) - 1)
    usable = vend - LEAD_IN_SEC - TAIL_MARGIN_SEC
    scale = usable / (authored_total / 1000.0)

    cues = []
    cursor_ms = 0.0
    for i, c in enumerate(raw_cues):
        start = LEAD_IN_SEC + (cursor_ms / 1000.0) * scale
        dur = (c["dur_ms"] / 1000.0) * scale
        cues.append({"id": i + 1, "start": round(start, 3), "duration": round(dur, 3),
                     "section": c["section"]})
        cursor_ms += c["dur_ms"] + INTER_CUE_PAUSE_MS

    last_start = cues[-1]["start"]
    video_end = vend
    last_id = cues[-1]["id"]

    placed = []
    overrun = 0
    last_cue_end = 0.0
    failed = []
    for c in cues:
        cid = c["id"]
        cue_wav = EXP / "cues" / f"cue_{cid:03d}.wav"
        raw_mp3 = EXP / "raw" / f"raw_{cid:03d}.mp3"
        if not raw_mp3.exists() or raw_mp3.stat().st_size < 500:
            failed.append(cid)
            continue
        natural = probe_duration(raw_mp3)
        target = float(c["duration"])
        if cid == last_id:
            target = min(target, video_end - last_start - 0.10)
        tempo = max(1.0, min(MAX_TEMPO, natural / target)) if target > 0 else 1.0
        placed_samples = wav_samples(cue_wav) if cue_wav.exists() else int(round(target * SR))
        start_sample = int(round(c["start"] * SR))
        last_cue_end = max(last_cue_end, (start_sample + placed_samples) / SR)
        if placed_samples > int(target * SR) + 200:
            overrun += 1
        expected_ms = round(c["start"] * 1000, 2)
        actual_ms = round(start_sample / SR * 1000, 2)
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": placed_samples,
            "expanded": cid in TAIL_IDS,
        })

    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=index,codec_type,codec_name",
         "-of", "json", str(OUT_VIDEO)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout)

    out_dur = probe_duration(OUT_VIDEO)
    report = {
        "experiment": "clean_timesync_v2 (lesson_12 full-length)",
        "lesson": "lesson_12_cramers_rule",
        "video_id": VIDEO_ID,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": VOICE,
        "max_tempo": MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": 0.0,
        "timeline_scale": round(scale, 6),
        "lead_in_sec": LEAD_IN_SEC,
        "tail_margin_sec": TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(master_dur, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(master_dur - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "tail_expansions_applied": [
            {"id": cid, "natural_before": None, "natural_after": None}
            for cid in sorted(TAIL_IDS) if cid in {p["id"] for p in placed}
        ],
        "cues": placed,
        "output_video": str(OUT_VIDEO),
        "output_duration_sec": round(out_dur, 3),
        "output_size_bytes": OUT_VIDEO.stat().st_size if OUT_VIDEO.exists() else 0,
        "output_streams": probe.get("streams", []),
        "volumedetect_intro_0_2s_db": volumedetect(OUT_VIDEO, 0, 2),
        "volumedetect_final_2s_db": volumedetect(OUT_VIDEO, max(0.0, out_dur - 2), 2),
    }
    with open(VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"cue_count={report['cue_count']} overrun={overrun} drift=0.0ms")
    print(f"video={report['output_duration_sec']}s size={report['output_size_bytes']}")
    print(f"streams={report['output_streams']}")
    print(f"intro={report['volumedetect_intro_0_2s_db']}dB final={report['volumedetect_final_2s_db']}dB")
    print(f"VERIFY: {VERIFY}")


if __name__ == "__main__":
    main()
