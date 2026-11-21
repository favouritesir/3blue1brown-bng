import subprocess
import os

def extract_frames(start_s, end_s, fps, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-ss", str(start_s), "-to", str(end_s),
        "-i", "departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/raw_sources/source_video.mp4",
        "-vf", f"fps={fps},scale=320:180",
        os.path.join(out_dir, "frame_%04d.jpg")
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Extracted {len(os.listdir(out_dir))} frames to {out_dir}")

extract_frames(2.0, 7.0, 5, "temp_audit_frames/cue1")
extract_frames(10.0, 15.0, 5, "temp_audit_frames/cue4_5")
extract_frames(36.0, 48.0, 5, "temp_audit_frames/ruler_hunt")
extract_frames(65.0, 75.0, 5, "temp_audit_frames/pen_lift")
extract_frames(142.0, 155.0, 5, "temp_audit_frames/blindfold")
extract_frames(204.0, 212.0, 5, "temp_audit_frames/chili")
