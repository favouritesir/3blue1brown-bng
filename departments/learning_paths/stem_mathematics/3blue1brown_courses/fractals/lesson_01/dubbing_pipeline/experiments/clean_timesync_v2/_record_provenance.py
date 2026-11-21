"""Record download provenance: oEmbed 3B1B authorship + ffprobe of each original."""
import json
import subprocess
import urllib.request
from pathlib import Path

WEB = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics"
           r"\3blue1brown_courses\web_platform")
VIDEOS = {
    "01": "-RdOwhmqP5s",
    "02": "LqbZpur38nw",
    "03": "gB9n2gHsHN4",
    "04": "3s7h2MHQtxc",
}

for nn, vid in VIDEOS.items():
    url = f"https://www.youtube.com/watch?v={vid}"
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    with urllib.request.urlopen(oembed_url, timeout=20) as r:
        oe = json.loads(r.read().decode("utf-8"))
    orig = WEB / "media_vault" / "fractals" / f"lesson_{nn}" / "original_source" / "full_original.mp4"
    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=index,codec_name,codec_type,width,height",
         "-of", "json", str(orig)], capture_output=True, text=True).stdout)
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    rec = {
        "lesson": f"lesson_{nn}",
        "youtube_id": vid,
        "youtube_url": url,
        "oembed_author_name": oe.get("author_name"),
        "oembed_author_url": oe.get("author_url"),
        "oembed_title": oe.get("title"),
        "oembed_confirms_3b1b": oe.get("author_name") == "3Blue1Brown",
        "ffprobe_duration_sec": float(probe["format"]["duration"]),
        "ffprobe_size_bytes": int(probe["format"]["size"]),
        "video_codec": v.get("codec_name"),
        "video_resolution": [v.get("width"), v.get("height")],
    }
    out = orig.parent / "source_provenance.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"lesson {nn}: oembed_3b1b={rec['oembed_confirms_3b1b']} "
          f"dur={rec['ffprobe_duration_sec']:.3f}s -> {out}", flush=True)
