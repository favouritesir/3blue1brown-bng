"""
Dub Studio - Modular Audio Separator & Auto-Ducking Dubbing Engine
Capabilities:
1. Extract / isolate background music/effects (BGM/SFX) via FFmpeg center-channel cancellation & bandpass
2. Auto-ducking BGM using dynamic sidechain compression triggered by the Bengali TTS track
3. Video muxing with lossless video pass-through (-c:v copy) and clean audio replacement
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_ffmpeg(cmd_list):
    """Run an FFmpeg command list cleanly and verify return code."""
    cmd_str = " ".join(f'"{arg}"' if " " in str(arg) else str(arg) for arg in cmd_list)
    print(f"[*] Executing: {cmd_str}")
    res = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{res.stderr}")
    return res.stdout


def extract_bgm_sfx_center_cancel(source_media, output_bgm_wav):
    """
    Method 1: Center-channel vocal elimination (Karaoke / OOPS technique).
    Since narrator dialogues are almost universally center-panned (identical L & R),
    subtracting R from L cancels the vocal energy while preserving stereo BGM and ambient SFX.
    """
    output_path = Path(output_bgm_wav)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # pan filter: c0 = 0.5*c0 - 0.5*c1 (cancels center), c1 = 0.5*c1 - 0.5*c0
    filter_expr = "pan=stereo|c0=0.5*c0-0.5*c1|c1=0.5*c1-0.5*c0,highpass=f=80,lowpass=f=12000"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(source_media),
        "-vn",
        "-filter:a", filter_expr,
        "-c:a", "pcm_s16le",
        str(output_path)
    ]
    run_ffmpeg(cmd)
    print(f"[✓] Extracted background music/SFX track to: {output_path}")
    return output_path


def mux_video_with_dub_and_ducking(
    source_video,
    bengali_speech_wav,
    output_video,
    bgm_audio=None,
    ducking_mode="sidechain",
    bgm_volume=0.18
):
    """
    Muxes the final video with original visuals kept intact (-c:v copy)
    and combines the Bengali dubbing with background audio.
    
    ducking_mode:
      - 'sidechain': Uses FFmpeg sidechaincompress where Bengali speech triggers real-time
                     compression of the BGM (smooth broadcast-level ducking).
      - 'static_mix': Attenuates BGM to a constant comfortable level (e.g. 18%) and mixes with dub.
      - 'pure_dub': Complete speech replacement with 0% background audio (Pure/Halal mode).
    """
    out_p = Path(output_video)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if ducking_mode == "pure_dub" or bgm_audio is None:
        print("[*] Muxing in PURE DUB mode (100% speech, original audio stripped)...")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(source_video),
            "-i", str(bengali_speech_wav),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out_p)
        ]
    elif ducking_mode == "sidechain":
        print("[*] Muxing with Dynamic SIDECHAIN DUCKING...")
        # Input 0: Video (with original audio or separate bgm)
        # Input 1: Dubbed Bengali Speech track
        # Input 2 (Optional): Isolated BGM track if provided separately
        bgm_input = str(bgm_audio) if bgm_audio else str(source_video)
        
        # sidechaincompress: [0:a] is background, [1:a] is voice sidechain trigger
        # threshold=0.12, ratio=5, attack=20ms, release=300ms
        filter_complex = (
            f"[0:a]volume={bgm_volume*2.0}[bg_pre];"
            f"[bg_pre][1:a]sidechaincompress=threshold=0.12:ratio=5:attack=20:release=300[ducked_bg];"
            f"[ducked_bg][1:a]amix=inputs=2:duration=first:weights=1 1.2[aout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", bgm_input,
            "-i", str(bengali_speech_wav),
            "-i", str(source_video),
            "-filter_complex", filter_complex,
            "-map", "2:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out_p)
        ]
    else:  # static_mix
        print(f"[*] Muxing with STATIC BGM DUCKING ({int(bgm_volume*100)}% volume)...")
        bgm_input = str(bgm_audio) if bgm_audio else str(source_video)
        filter_complex = (
            f"[0:a]volume={bgm_volume}[bg];"
            f"[bg][1:a]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", bgm_input,
            "-i", str(bengali_speech_wav),
            "-i", str(source_video),
            "-filter_complex", filter_complex,
            "-map", "2:v:0",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out_p)
        ]

    run_ffmpeg(cmd)
    if out_p.exists():
        size_mb = out_p.stat().st_size / (1024 * 1024)
        print(f"[✓] Final Dubbed Video exported: {out_p} ({size_mb:.2f} MB)")
        return out_p
    else:
        raise FileNotFoundError(f"Export failed: {out_p} not created")


if __name__ == "__main__":
    print("Dub Studio Audio Processing Module loaded successfully.")
