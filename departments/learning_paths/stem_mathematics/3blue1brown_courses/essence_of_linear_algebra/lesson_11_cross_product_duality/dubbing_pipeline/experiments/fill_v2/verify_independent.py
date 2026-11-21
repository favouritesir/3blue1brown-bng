"""Independent verification of the fill_v2 output FILE (not the in-memory canvas)."""
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

WEB = Path(__file__).resolve().parents[5] / "web_platform"
ORIG = WEB / "media_vault" / "lesson_11" / "original_source" / "full_original.mp4"
OUT = WEB / "media_vault" / "lesson_11" / "experiments" / "fill_v2" / "3b1b_lesson_11_full_dubbed_fill2.mp4"
OLD = WEB / "media_vault" / "lesson_11" / "experiments" / "3b1b_lesson_11_full_dubbed.mp4"
TMP = Path(__file__).resolve().parent / "_verify_audio.wav"


def probe(path, entries):
    o = subprocess.run(
        f'ffprobe -v error -show_entries {entries} -of json "{path}"',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return json.loads(o.stdout)


def dur(path):
    o = subprocess.run(
        f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"',
        shell=True, stdout=subprocess.PIPE, text=True)
    return float(o.stdout.strip())


# 1) duration parity
d_orig, d_out = dur(ORIG), dur(OUT)
print(f"[duration] original={d_orig:.3f}s output={d_out:.3f}s diff={abs(d_out-d_orig):.3f}s "
      f"parity={abs(d_out-d_orig)<=1.0}")

# 2) video stream identity (no swap)
def vinfo(path):
    j = probe(path, "stream=index,codec_type,codec_name,width,height,nb_frames")
    v = [s for s in j.get("streams", []) if s.get("codec_type") == "video"][0]
    return {k: v.get(k) for k in ("codec_name", "width", "height", "nb_frames")}
vi_o, vi_x = vinfo(ORIG), vinfo(OUT)
print(f"[video-src] original={vi_o}")
print(f"[video-src] output  ={vi_x}")
print(f"[video-src] MATCH={vi_o == vi_x}")

# 3) decode output audio to PCM and scan internal silence runs
subprocess.run(
    f'ffmpeg -y -hide_banner -loglevel error -i "{OUT}" -vn -ac 1 -ar 44100 '
    f'-c:a pcm_s16le "{TMP}"', shell=True, check=True)
with wave.open(str(TMP), "rb") as w:
    x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0

SR = 44100
def runs_in(threshold, start_s, end_s, hop_ms=20):
    seg = x[int(start_s*SR):int(end_s*SR)]
    hop = int(hop_ms/1000*SR)
    nf = int(np.ceil(len(seg)/hop))
    silent = []
    for f in range(nf):
        c = seg[f*hop:(f+1)*hop]
        silent.append(bool(c.size and np.sqrt(np.mean(c**2)) < threshold))
    runs, f = [], 0
    while f < nf:
        if silent[f]:
            g = f
            while g+1 < nf and silent[g+1]:
                g += 1
            runs.append(round((g-f+1)*hop/SR, 3))
            f = g+1
        else:
            f += 1
    return runs

for th in (0.01, 0.02):
    runs = runs_in(th, 2.5, d_out-3.0)
    big = [r for r in runs if r > 2.0]
    print(f"[silence th={th}] internal runs>2s={len(big)} max_run={max(runs) if runs else 0}s "
          f"details={big[:10]}")

# 4) backup untouched
print(f"[backup] old video exists={OLD.exists()} size={OLD.stat().st_size if OLD.exists() else 0}")

# 5) gates from report
rep = json.loads((Path(__file__).resolve().parent / "verification.json").read_text(encoding="utf-8"))
g = rep["fill_gate"]
print(f"[gates] median_fill={g['median_fill']} pass={g['median_fill_pass']} | "
      f"max_gap={g['max_internal_gap_s']} pass={g['max_internal_gap_pass']} | "
      f"runs>2s={g['internal_silence_runs_gt_2s']} pass={g['internal_silence_runs_pass']}")
print(f"[gates] all_fill_gates_pass={g['all_fill_gates_pass']} success={rep['success']}")

TMP.unlink(missing_ok=True)
