# -*- coding: utf-8 -*-
"""
Checkpointed batch runner for the 13 PHYSICS expressive teacher-audio builds.

Usage:
  python governance/run_expressive_physics_batch.py 1 4      # lessons 01..04
  python governance/run_expressive_physics_batch.py 5 8
  python governance/run_expressive_physics_batch.py 9 13

A lesson already recorded as 'verified' in the checkpoint is skipped, so a
partial failure is recoverable by simply re-running any range.
"""
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHECKPOINT = os.path.join(HERE, "_physics_expressive_checkpoint.json")


def load():
    if os.path.exists(CHECKPOINT):
        return json.load(open(CHECKPOINT, encoding="utf-8"))
    return {"verified": {}, "last_run": None}


def save(cp):
    cp["last_run"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(CHECKPOINT, "w", encoding="utf-8") as fh:
        json.dump(cp, fh, ensure_ascii=False, indent=2)


def run(cmd, log):
    print("  $", " ".join(cmd), flush=True)
    with open(log, "w", encoding="utf-8") as fh:
        proc = subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
    return proc.returncode


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 13
    cp = load()
    for n in range(lo, hi + 1):
        key = f"lesson_{n:02d}"
        if key in cp["verified"]:
            print(f"[{key}] SKIP (already verified at {cp['verified'][key].get('at')})", flush=True)
            continue
        print(f"\n[{key}] BUILD START", flush=True)
        rc = run([sys.executable, f"governance/build_expressive_teacher_audio_physics{n:02d}.py"],
                 os.path.join(HERE, f"_physics{n:02d}_expressive_build.log"))
        if rc != 0:
            print(f"[{key}] BUILD FAILED rc={rc} — see log. Checkpoint unchanged.", flush=True)
            continue
        print(f"[{key}] VERIFY START", flush=True)
        rc = run([sys.executable, "governance/verify_physics_expressive_build.py", str(n)],
                 os.path.join(HERE, f"_physics{n:02d}_expressive_verify.log"))
        if rc != 0:
            print(f"[{key}] VERIFY FAILED rc={rc} — see log. Checkpoint unchanged.", flush=True)
            continue
        cp["verified"][key] = {
            "at": datetime.datetime.now().isoformat(timespec="seconds"),
            "cues": None,
        }
        save(cp)
        print(f"[{key}] VERIFIED + checkpointed", flush=True)
    save(cp)
    print(f"\nBatch {lo}-{hi} complete. Verified total: {len(cp['verified'])}/13", flush=True)


if __name__ == "__main__":
    main()
