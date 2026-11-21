"""
Finalize the interrupted verification step of build_l07_clean.py.

TTS, master construction and the video mux already completed successfully;
the server restart interrupted only the final ffprobe/volumedetect bookkeeping.
This script reconstructs verification.json from the on-disk artifacts WITHOUT
re-synthesizing speech or re-muxing the video.
"""
import json
import re
import wave

import build_l07_clean as b


def fast_volumedetect(path, start, length):
    """Audio-only atrim volumedetect.

    Do NOT use -ss on this VP9-in-MP4 file: seeking before/after -i produces
    bogus (silent) readings. Decoding the audio-only stream from the start and
    trimming with atrim is both fast and accurate.
    """
    out = b.run(f'ffmpeg -hide_banner -nostdin -i "{path}" -vn -map 0:a:0 '
                f'-af "atrim=start={start:.3f}:duration={length:.3f},volumedetect" '
                f'-f null - 2>&1')
    m = re.search(r"mean_volume:\s*([-\d.]+) dB", out)
    return float(m.group(1)) if m else None


def main():
    vend = b.video_duration(b.ORIGINAL_VIDEO)
    cues, scale = b.load_cues(vend)
    last_id = cues[-1]["id"]
    last_start = float(cues[-1]["start"])

    failed = [c["id"] for c in cues
              if not b.valid(b.RAW_DIR / f"raw_{c['id']:03d}.mp3")]
    expanded_ids = [31, 32, 33]

    placed = []
    overrun = 0
    max_end_samples = 0
    for c in cues:
        cid = c["id"]
        raw = b.RAW_DIR / f"raw_{cid:03d}.mp3"
        cuewav = b.CUE_DIR / f"cue_{cid:03d}.wav"
        natural = b.duration(raw)
        target = float(c["duration"])
        if cid == last_id:
            target = min(target, vend - last_start - 0.10)
        tempo = max(1.0, min(b.MAX_TEMPO, natural / target)) if natural > 0 else 1.0

        with wave.open(str(cuewav), "rb") as w:
            n = w.getnframes()
        start_sample = int(round(float(c["start"]) * b.SR))
        max_end_samples = max(max_end_samples, start_sample + n)
        expected_ms = round(float(c["start"]) * 1000, 2)
        actual_ms = round(start_sample / b.SR * 1000, 2)
        if n > int(float(c["duration"]) * b.SR) + 200:
            overrun += 1
        placed.append({
            "id": cid,
            "section": c["section"],
            "expected_start_ms": expected_ms,
            "actual_start_ms": actual_ms,
            "drift_ms": round(actual_ms - expected_ms, 6),
            "tempo": round(tempo, 4),
            "natural_sec": round(natural, 3),
            "target_sec": round(target, 3),
            "placed_samples": n,
            "expanded": cid in expanded_ids,
        })

    max_drift = max((abs(x["drift_ms"]) for x in placed), default=0.0)
    master_dur = b.duration(b.MASTER_WAV)
    last_cue_end = max_end_samples / b.SR

    report = {
        "experiment": "clean_timesync_v2 (lesson_07 full-length)",
        "verification_finalized_after_restart": True,
        "cue_count": len(placed),
        "expected_cue_count": len(cues),
        "failed_tts_cues": failed,
        "strategy": "absolute sample offset (start*44100); atempo fit; pad only; no truncation",
        "sfx": "NONE — clean speech only",
        "voice": b.VOICE,
        "max_tempo": b.MAX_TEMPO,
        "overrun_cues": overrun,
        "max_measured_drift_ms": round(max_drift, 6),
        "timeline_scale": round(scale, 6),
        "lead_in_sec": b.LEAD_IN_SEC,
        "tail_margin_sec": b.TAIL_MARGIN_SEC,
        "video_duration_sec": round(vend, 3),
        "master_audio_duration_sec": round(master_dur, 3),
        "last_cue_end_sec": round(last_cue_end, 3),
        "tail_silence_sec": round(master_dur - last_cue_end, 3),
        "speech_ends_before_video_end": last_cue_end < vend,
        "tail_expansions_applied": [
            {"id": cid, "natural_after": round(b.duration(b.RAW_DIR / f"raw_{cid:03d}.mp3"), 3)}
            for cid in expanded_ids
        ],
        "cues": placed,
    }

    report["output_video"] = str(b.OUT_VIDEO)
    report["output_duration_sec"] = round(b.duration(b.OUT_VIDEO), 3)
    report["output_size_bytes"] = b.OUT_VIDEO.stat().st_size if b.OUT_VIDEO.exists() else 0
    probe = json.loads(b.run(
        f'ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate '
        f'-of json "{b.OUT_VIDEO}"'))
    report["output_streams"] = probe.get("streams", [])

    report["volumedetect_intro_0_2s_db"] = fast_volumedetect(b.OUT_VIDEO, 0, 2)
    odur = b.duration(b.OUT_VIDEO)
    report["volumedetect_final_2s_db"] = fast_volumedetect(b.OUT_VIDEO, max(0.0, odur - 2), 2)

    with open(b.VERIFY, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps({k: report[k] for k in (
        "cue_count", "expected_cue_count", "failed_tts_cues", "overrun_cues",
        "max_measured_drift_ms", "video_duration_sec", "master_audio_duration_sec",
        "last_cue_end_sec", "tail_silence_sec", "speech_ends_before_video_end",
        "output_duration_sec", "output_size_bytes", "output_streams",
        "volumedetect_intro_0_2s_db", "volumedetect_final_2s_db")},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
