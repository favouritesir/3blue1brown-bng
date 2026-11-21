"""Re-run the (patched) independent verification on already-built outputs.

Updates verification.json in place without re-rendering audio.
"""
import json
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHYPI = HERE.parent.parent.parent


def main():
    for nn in ["01", "02", "03", "04", "05", "06", "07", "08"]:
        script = WHYPI / f"lesson_{nn}" / "dubbing_pipeline" / "experiments" / "clean_timesync_v2" / f"build_why_pi{nn}_clean.py"
        vf = script.parent / "verification.json"
        if not script.exists() or not vf.exists():
            print(f"L{nn}: no build/verification yet", flush=True)
            continue
        spec = importlib.util.spec_from_file_location(f"b{nn}", script)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        rep = json.loads(vf.read_text(encoding="utf-8"))
        if not m.OUT_VIDEO.exists():
            print(f"L{nn}: output video missing", flush=True)
            continue
        old = rep.get("independent_verification", {})
        vend = float(rep["video_duration_sec"])
        first = float(old.get("first_cue_start_sec", 2.5))
        last = float(old.get("last_cue_end_sec", vend - 3.0))
        ind = m.independent_verify(vend, first, last)
        rep["independent_verification"] = ind
        gates = {
            "duration_match": ind["duration_match"],
            "no_internal_silence_gt_2s": ind["internal_silence_gate_pass"],
            "median_fill_ge_0.72": bool(rep["median_fill"] >= 0.72),
            "max_internal_gap_le_1.5": bool(rep["max_internal_gap_s"] <= 1.5),
        }
        gates["all_pass"] = all(gates.values())
        rep["gates"] = gates
        rep["success"] = gates["all_pass"]
        rep["output_duration_sec"] = ind["output_duration_sec"]
        vf.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"L{nn}: delta={ind['duration_delta_sec']}s "
              f"internal>2s={ind['internal_runs_gt_2s_count']} "
              f"fill={rep['median_fill']} gap={rep['max_internal_gap_s']} "
              f"SUCCESS={gates['all_pass']}", flush=True)


if __name__ == "__main__":
    main()
