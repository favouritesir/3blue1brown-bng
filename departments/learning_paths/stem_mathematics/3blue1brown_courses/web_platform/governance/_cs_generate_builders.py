# -*- coding: utf-8 -*-
"""Generate the 13 self-contained expressive-teacher builders from the template."""
import copy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = json.load(open(os.path.join(ROOT, "governance", "_cs_expressive_scripts.json"), encoding="utf-8"))
DOM = json.load(open(os.path.join(ROOT, "governance", "_cs_dom_dump.json"), encoding="utf-8"))
TPL = open(os.path.join(ROOT, "governance", "_cs_builder_template.py"), encoding="utf-8").read()


def main():
    for n in range(1, 14):
        lk = "lesson_%02d" % n
        data = SCRIPTS[lk]
        dom_secs = DOM[lk]["sections"]

        sections = copy.deepcopy(data["sections"])
        for sid, sec in sections.items():
            cues = sec["cues"]
            if len(cues) > 1 and cues[-1]["type"] not in ("h2", "formula-box"):
                cues[-1]["role"] = "conclusion"

        expected_types = {s["id"]: [b["type"] for b in s["blocks"]] for s in dom_secs}
        expected_audio = {s["id"]: s["audio_file"] for s in dom_secs}
        n_cues = sum(len(s["cues"]) for s in sections.values())

        src = TPL
        src = src.replace("__LESSON_NUM__", "%02d" % n)
        src = src.replace("__N_CUES__", str(n_cues))
        src = src.replace("__MANIFEST_TITLE__", data["title_bn"])
        src = src.replace("__EXPECTED_TYPES__", json.dumps(expected_types, ensure_ascii=False, indent=4))
        src = src.replace("__EXPECTED_AUDIO_FILES__", json.dumps(expected_audio, ensure_ascii=False, indent=4))
        src = src.replace("__SECTIONS_DATA__", json.dumps(sections, ensure_ascii=False, indent=4))
        src = src.replace("__LESSON__", "%02d" % n)

        dst = os.path.join(ROOT, "governance", "build_expressive_teacher_audio_cs%02d.py" % n)
        with open(dst, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src)
        print("BUILDER %02d: %d cues -> %s (%d bytes)" % (n, n_cues, os.path.basename(dst), len(src)))


if __name__ == "__main__":
    main()
