import wave, numpy as np, statistics, pathlib
p = pathlib.Path(__file__).resolve().parent / "cues"
for th in [0.005, 0.003, 0.002, 0.001, 0.0005]:
    vals = []
    for f in sorted(p.glob("cue_*.wav")):
        with wave.open(str(f), "rb") as w:
            a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
        vals.append(float((np.abs(a) >= th).sum()) / len(a))
    print(f"th={th}: median={statistics.median(vals):.4f} min={min(vals):.4f} max={max(vals):.4f}")
