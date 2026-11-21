import sys, importlib
print("PYTHON:", sys.executable, sys.version)
for m in ("numpy", "edge_tts", "yt_dlp"):
    try:
        mod = importlib.import_module(m)
        print(f"  {m}: OK", getattr(mod, "__version__", ""))
    except Exception as e:
        print(f"  {m}: MISSING ({e.__class__.__name__})")
