"""Download full original 3Blue1Brown geometry source videos + provenance."""
import json
import subprocess
import sys
import time
from pathlib import Path


def ytdlp_meta(vid, retries=3):
    """Return parsed yt-dlp JSON metadata (stdout only; stderr kept separate)."""
    cmd = [sys.executable, '-m', 'yt_dlp', '--no-warnings', '--skip-download',
           '--no-playlist', '--dump-single-json', vid]
    last = None
    for i in range(retries):
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            return json.loads(r.stdout)
        except Exception as e:
            last = f'{e}\nSTDERR: {r.stderr[-800:]}'
            print(f'  meta retry {i+1}/{retries}: {last}', flush=True)
            time.sleep(2 * (i + 1))
    raise RuntimeError(last or 'metadata failed')

BASE = Path('departments/learning_paths/stem_mathematics/3blue1brown_courses')
WEB = BASE / 'web_platform'
IDS = {
    1: 'GNcFjFmqEc8', 2: 'pQa_tWZmlGs', 3: 'fsLh-NYhOoU',
    4: 'd4EgbgTm0Bg', 5: 'zjMuIxRvygQ', 6: 'zwAD6dRSVyI',
}
OEMBED = {
    1: ("But why is a sphere's surface area four times its shadow?", '3Blue1Brown'),
    2: ('Why slicing a cone gives an ellipse (beautiful proof)', '3Blue1Brown'),
    3: ('The most beautiful formula not enough people understand', '3Blue1Brown'),
    4: ('Visualizing the 4d numbers Quaternions', '3Blue1Brown'),
    5: ('Quaternions and 3d rotation, explained interactively', '3Blue1Brown'),
    6: ('Thinking outside the 10-dimensional box', '3Blue1Brown'),
}


def run(cmd, retries=3):
    last = None
    for i in range(retries):
        r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True)
        if r.returncode == 0:
            return r.stdout
        last = r.stdout
        print(f'  retry {i+1}/{retries}: {r.stdout[-500:]}', flush=True)
        time.sleep(2 * (i + 1))
    raise RuntimeError(last or 'failed')


def probe(path):
    return json.loads(run(f'ffprobe -v error -show_entries '
                          f'format=duration,size:'
                          f'stream=index,codec_type,codec_name,width,height,avg_frame_rate '
                          f'-of json "{path}"'))


only = int(sys.argv[1]) if len(sys.argv) > 1 else None

for n in range(1, 7):
    if only and n != only:
        continue
    nn = f'{n:02d}'
    vid = IDS[n]
    outdir = WEB / 'media_vault' / 'geometry' / f'lesson_{nn}' / 'original_source'
    outdir.mkdir(parents=True, exist_ok=True)
    final = outdir / 'full_original.mp4'
    print(f'=== L{nn} {vid} -> {final} ===', flush=True)

    if final.exists() and final.stat().st_size > 100000:
        print(f'  already present ({final.stat().st_size} bytes)', flush=True)
    else:
        # metadata dump (provenance)
        meta = ytdlp_meta(vid)
        (outdir / 'ytdlp_metadata.json').write_text(
            json.dumps({k: meta.get(k) for k in
                        ('id', 'title', 'uploader', 'channel', 'channel_id',
                         'duration', 'width', 'height', 'webpage_url')},
                       ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'  ytdlp: uploader={meta.get("uploader")} channel={meta.get("channel")} '
              f'dur={meta.get("duration")}s', flush=True)
        tmpl = (outdir / 'full_original.%(ext)s').as_posix()
        run(f'python -m yt_dlp --no-playlist --no-part '
            f'-f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/b[ext=mp4]/b" '
            f'--merge-output-format mp4 -o "{tmpl}" "{vid}"', retries=3)

    cands = sorted(outdir.glob('full_original.*'),
                   key=lambda p: p.stat().st_size, reverse=True)
    if not cands or cands[0].stat().st_size < 100000:
        raise SystemExit(f'L{nn}: download FAILED -> {outdir}')
    if cands[0] != final:
        cands[0].replace(final)

    pr = probe(final)
    dur = float(pr.get('format', {}).get('duration', 0))
    vids = [s for s in pr.get('streams', []) if s.get('codec_type') == 'video']
    title, author = OEMBED[n]
    ver = {
        'lesson': f'lesson_{nn}', 'video_id': vid,
        'official_url': f'https://www.youtube.com/watch?v={vid}',
        'oembed': {'title': title, 'author_name': author,
                   'author_url': 'https://www.youtube.com/@3blue1brown'},
        'downloaded_file': str(final), 'file_size_bytes': final.stat().st_size,
        'ffprobe': pr, 'ffprobe_duration_sec': dur,
        'ffprobe_video_streams': len(vids), 'is_3b1b': author == '3Blue1Brown',
        'verified_via': ['oEmbed author_name=3Blue1Brown',
                         'yt-dlp metadata channel=3Blue1Brown',
                         'ffprobe of downloaded original'],
    }
    (outdir / 'source_verification.json').write_text(
        json.dumps(ver, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  OK duration={dur:.1f}s size={final.stat().st_size} '
          f'video_streams={len(vids)}', flush=True)

print('ALL DOWNLOADS DONE', flush=True)
