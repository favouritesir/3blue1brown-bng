"""Independent verification of the 6 geometry full-dubbed videos.

Checks, per lesson:
  1. ffprobe output duration ~= original full duration.
  2. Zero internal silent runs > 2s (only lead-in / tail allowed).
  3. median_fill >= 0.72 and max_internal_gap_s <= 1.5 (from verification.json).
  4. Valid video + audio streams, no fatal TTS failures.
Writes a JSON artifact and prints a compact table.
"""
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path('departments/learning_paths/stem_mathematics/3blue1brown_courses')
WEB = ROOT / 'web_platform'
SR = 44100
SIL_THR = 0.01           # ~ -40 dBFS
MIN_RUN_S = 2.0
DUR_TOL_S = 2.0          # output vs original tolerance


def run(cmd):
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True)
    return r.stdout


def probe_duration(path):
    out = run(f'ffprobe -v error -show_entries format=duration '
              f'-of default=noprint_wrappers=1:nokey=1 "{path}"')
    try:
        return float(out.strip())
    except Exception:
        return 0.0


def probe_streams(path):
    out = run(f'ffprobe -v error -show_entries stream=codec_type,codec_name '
              f'-of json "{path}"')
    return json.loads(out).get('streams', [])


def silence_runs(wav_path):
    with wave.open(str(wav_path), 'rb') as w:
        arr = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32) / 32768.0
    active = np.abs(arr) > SIL_THR
    if not active.any():
        return len(arr) / SR, [], 0.0, float('inf')
    first = int(np.flatnonzero(active)[0])
    last = int(np.flatnonzero(active)[-1])
    quiet = (~active).astype(np.int8)
    quiet[0] = 0
    quiet[-1] = 0
    d = np.diff(quiet)
    starts = np.flatnonzero(d == 1) + 1
    ends = np.flatnonzero(d == -1) + 1
    limit = int(MIN_RUN_S * SR)
    runs = []
    for s, e in zip(starts, ends):
        s, e = int(s), int(e)
        if e - s < limit:
            continue
        if e <= first:
            kind = 'lead_in'
        elif s >= last:
            kind = 'tail'
        else:
            kind = 'INTERNAL'
        runs.append({'kind': kind, 'start_s': round(s / SR, 3),
                     'end_s': round(e / SR, 3), 'duration_s': round((e - s) / SR, 3)})
    return len(arr) / SR, runs, first / SR, last / SR


results = []
for n in range(1, 7):
    nn = f'{n:02d}'
    orig_dir = WEB / 'media_vault' / 'geometry' / f'lesson_{nn}' / 'original_source'
    exp_dir = ROOT / 'geometry' / f'lesson_{nn}' / 'dubbing_pipeline' / 'experiments' / 'clean_timesync_v2'
    out = WEB / 'media_vault' / 'geometry' / f'lesson_{nn}' / 'experiments' / f'3b1b_geometry_{nn}_full_dubbed.mp4'
    ver_path = exp_dir / 'verification.json'
    sv_path = orig_dir / 'source_verification.json'

    rec = {'lesson': f'lesson_{nn}', 'output': str(out)}
    orig_dur = probe_duration(orig_dir / 'full_original.mp4')
    if sv_path.exists():
        sv = json.loads(sv_path.read_text(encoding='utf-8'))
        rec['youtube_id'] = sv.get('video_id')
        rec['is_3b1b'] = sv.get('is_3b1b') or sv.get('oembed', {}).get('author_name') == '3Blue1Brown'
        orig_dur = sv.get('ffprobe_duration_sec') or orig_dur
    rec['original_duration_s'] = round(orig_dur, 3)

    if not out.exists() or out.stat().st_size < 100000:
        rec['status'] = 'MISSING_OR_TOO_SMALL'
        rec['output_size_bytes'] = out.stat().st_size if out.exists() else 0
        results.append(rec)
        continue

    rec['output_size_bytes'] = out.stat().st_size
    odur = probe_duration(out)
    rec['output_duration_s'] = round(odur, 3)
    rec['duration_delta_s'] = round(odur - orig_dur, 3)
    rec['duration_ok'] = abs(odur - orig_dur) <= DUR_TOL_S
    streams = probe_streams(out)
    rec['streams'] = streams
    rec['has_video'] = any(s.get('codec_type') == 'video' for s in streams)
    rec['has_audio'] = any(s.get('codec_type') == 'audio' for s in streams)

    tmp = Path(f'temp_geo_verify_{nn}.wav')
    run(f'ffmpeg -y -i "{out}" -vn -af aresample=44100 -ar 44100 -ac 1 -c:a pcm_s16le "{tmp}" > NUL 2>&1')
    wdur, runs, first, last = silence_runs(tmp)
    try:
        tmp.unlink()
    except OSError:
        pass
    rec['audio_duration_s'] = round(wdur, 3)
    rec['first_speech_s'] = round(first, 3)
    rec['last_speech_s'] = round(last, 3)
    rec['silent_runs_gt_2s'] = runs
    rec['internal_silent_runs_gt_2s'] = [r for r in runs if r['kind'] == 'INTERNAL']
    rec['internal_silence_ok'] = len(rec['internal_silent_runs_gt_2s']) == 0

    if ver_path.exists():
        v = json.loads(ver_path.read_text(encoding='utf-8'))
        rec['pipeline_median_fill'] = v.get('median_fill')
        rec['pipeline_max_internal_gap_s'] = v.get('max_internal_gap_s')
        rec['pipeline_quality_gate'] = v.get('quality_gate')
        rec['pipeline_failed_tts_cues'] = v.get('failed_tts_cues')
        rec['pipeline_render_rounds'] = v.get('render_rounds')
        rec['pipeline_cue_count'] = v.get('cue_count')

    gates = {
        'duration_ok': rec.get('duration_ok', False),
        'internal_silence_ok': rec.get('internal_silence_ok', False),
        'median_fill_ok': (rec.get('pipeline_median_fill') or 0) >= 0.72,
        'max_internal_gap_ok': (rec.get('pipeline_max_internal_gap_s') or 99) <= 1.5,
        'has_video': rec.get('has_video', False),
        'has_audio': rec.get('has_audio', False),
        'no_failed_cues': not rec.get('pipeline_failed_tts_cues'),
        'is_3b1b': rec.get('is_3b1b', False),
    }
    rec['gates'] = gates
    rec['status'] = 'PASS' if all(gates.values()) else 'FAIL'
    results.append(rec)

ART = WEB / 'media_vault' / 'geometry' / 'independent_verification.json'
ART.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"{'lesson':<10}{'status':<7}{'orig_s':>9}{'out_s':>9}{'delta':>8}"
      f"{'med_fill':>10}{'max_gap':>9}{'int_sil':>9}{'rounds':>8}")
for r in results:
    print(f"{r['lesson']:<10}{r.get('status',''):<7}"
          f"{r.get('original_duration_s',0):>9.1f}{r.get('output_duration_s',0):>9.1f}"
          f"{r.get('duration_delta_s',0):>8.2f}"
          f"{(r.get('pipeline_median_fill') or 0):>10.4f}"
          f"{(r.get('pipeline_max_internal_gap_s') or 99):>9.3f}"
          f"{len(r.get('internal_silent_runs_gt_2s', [])):>9}"
          f"{(r.get('pipeline_render_rounds') or 0):>8}")
print(f'ARTIFACT: {ART}')
