# -*- coding: utf-8 -*-
"""STEP 1: back up each placeholder analysis manifest BEFORE any expressive
build overwrites it. Copies manifest.json + manifest.js into
assets/audio/analysis/lesson_NN/_backup_before_expressive_build/.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)
AUDIO_ROOT = os.path.join(WORKSPACE, "assets", "audio", "analysis")


def main():
    for n in range(1, 11):
        lesson = f"lesson_{n:02d}"
        src_dir = os.path.join(AUDIO_ROOT, lesson)
        bak_dir = os.path.join(src_dir, "_backup_before_expressive_build")
        os.makedirs(bak_dir, exist_ok=True)
        copied = []
        for name in ("manifest.json", "manifest.js"):
            src = os.path.join(src_dir, name)
            dst = os.path.join(bak_dir, name)
            if not os.path.exists(src):
                raise RuntimeError(f"Missing placeholder {src}")
            shutil.copy2(src, dst)
            if os.path.getsize(dst) == 0:
                raise RuntimeError(f"Empty backup {dst}")
            copied.append(name)
        print(f"[{lesson}] backed up {', '.join(copied)} -> {bak_dir}")


if __name__ == "__main__":
    main()
