# -*- coding: utf-8 -*-
import importlib.util
import os
import sys

gov = os.path.dirname(os.path.abspath(__file__))
for n in [int(x) for x in sys.argv[1:]] or [1]:
    p = os.path.join(gov, f"build_expressive_teacher_audio_physics{n:02d}.py")
    spec = importlib.util.spec_from_file_location(f"b{n}", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    print("#" * 74)
    print("LESSON", n)
    for sid, sec in m.SECTIONS_DATA.items():
        print(" SECTION", sid)
        for c in sec["cues"]:
            print(f"   [{c['index']}] {c['type']:12s} {c['tts']}")
