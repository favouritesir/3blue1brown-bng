"""
Quick finalize for Lesson-03 clean build: re-encode the already-built
master.wav with two-pass linear loudnorm (exact -14 LUFS), re-mux with the
full original video, and refresh verification.json. Does NOT re-run TTS.
"""
import importlib.util
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("b", HERE / "build_l03_clean.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd}\n{r.stderr[-1200:]}")
    return r.stdout + "\n" + r.stderr


af = b.loudnorm_two_pass_filter(b.MASTER_WAV)
print("FILTER:", af, flush=True)
run(f'ffmpeg -y -i "{b.MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a libmp3lame -b:a 192k "{b.MASTER_MP3}" > NUL 2>&1')
run(f'ffmpeg -y -i "{b.MASTER_WAV}" -af "{af}" -ar 44100 -ac 2 -c:a aac -b:a 192k "{b.MASTER_M4A}" > NUL 2>&1')

b.OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
run(f'ffmpeg -y -i "{b.ORIGINAL_VIDEO}" -i "{b.MASTER_M4A}" -map 0:v:0 -map 1:a:0 '
    f'-c:v copy -c:a aac -shortest "{b.OUT_VIDEO}" > NUL 2>&1')

ebur = run(f'ffmpeg -hide_banner -nostats -i "{b.MASTER_MP3}" -filter_complex ebur128=peak=true -f null NUL')
mi = re.findall(r'I:\s*(-?[\d.]+)\s*LUFS', ebur)
integrated = float(mi[-1]) if mi else None  # last = Summary value (early lines are -70 placeholders)
mp = re.findall(r'Peak:\s*(-?[\d.]+)\s*dBFS', ebur)
true_peak = float(mp[-1]) if mp else None

v = json.load(open(b.VERIFY, encoding="utf-8"))
v["loudnorm_filter"] = af
v["measured_integrated_lufs"] = integrated
v["measured_true_peak_dbfs"] = true_peak
v["master_mp3_duration_sec"] = b.duration(b.MASTER_MP3)
v["output_video_duration_sec"] = b.duration(b.OUT_VIDEO)
v["volumedetect_intro_0_2s"] = b.volumedetect(b.MASTER_MP3, 0, 2)
v["volumedetect_final_2s"] = b.volumedetect(b.MASTER_MP3, max(0, v["master_mp3_duration_sec"] - 2), 2)
v["output_volumedetect_intro_0_2s"] = b.volumedetect(b.OUT_VIDEO, 0, 2)
v["output_volumedetect_final_2s"] = b.volumedetect(b.OUT_VIDEO, max(0, v["output_video_duration_sec"] - 2), 2)
v["volumedetect_before_first_cue_10_12s"] = b.volumedetect(b.OUT_VIDEO, 10, 2)
v["volumedetect_last_cue_tail_644_646s"] = b.volumedetect(b.OUT_VIDEO, 644, 2)
json.dump(v, open(b.VERIFY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"Integrated: {integrated} LUFS | True peak: {true_peak} dBFS", flush=True)
print(f"Output video: {b.OUT_VIDEO} ({v['output_video_duration_sec']}s)", flush=True)
print(f"intro={v['output_volumedetect_intro_0_2s']} final={v['output_volumedetect_final_2s']}", flush=True)
