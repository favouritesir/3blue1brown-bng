import soundfile as sf, os, json, subprocess

base = r"D:\0PEN CODE\Dub Studio\departments\media_production\youtube_channels\wow_english\kids_education\steve_and_maggie_school_stories_senses"
files = [
    "audio_takes/google_studio_masters/steve_master_take_google_studio.wav",
    "audio_takes/google_studio_masters/maggie_master_take_google_studio.wav",
    "isolated_stems/mistral_direct_pure_sfx.wav",
    "raw_sources/source_video.mp4",
    "raw_sources/original_audio.wav",
]
report = {}
for f in files:
    p = os.path.join(base, f)
    sz = os.path.getsize(p)
    if f.endswith(".wav"):
        info = sf.info(p)
        report[f] = dict(size_mb=round(sz/1e6, 3), samplerate=info.samplerate,
                         channels=info.channels, duration_s=round(info.frames/info.samplerate, 3),
                         subtype=info.subtype)
        print(f"{f}: {sz/1e6:.2f} MB | {info.samplerate} Hz | {info.channels} ch | {info.frames/info.samplerate:.3f} s | {info.subtype}")
    else:
        report[f] = dict(size_mb=round(sz/1e6, 3))
        print(f"{f}: {sz/1e6:.2f} MB")

# probe video with ffprobe
p = os.path.join(base, "raw_sources/source_video.mp4")
out = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                      "-of", "json", p], capture_output=True, text=True)
vid = json.loads(out.stdout)
for s in vid["streams"]:
    print("stream:", s["codec_type"], s.get("codec_name"), s.get("sample_rate"),
          f"dur={float(s.get('duration', vid['format'].get('duration', 0))):.3f}",
          "sr=", s.get("sample_rate"), "ch=", s.get("channels"),
          "w=", s.get("width"), "h=", s.get("height"), "r=", s.get("r_frame_rate"))
report["video_streams"] = [{k: s.get(k) for k in ("codec_type","codec_name","duration","sample_rate","channels","width","height","r_frame_rate")} for s in vid["streams"]]

with open(os.path.join(base, "scripts/mistral_pipeline/v2_probe_report.json"), "w") as fh:
    json.dump(report, fh, indent=2, ensure_ascii=False)
print("probe report saved")
