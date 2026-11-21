# -*- coding: utf-8 -*-
"""Scan all puzzles builder tts strings for forbidden chars (authoring aid)."""
import ast
import glob
import os
import re

BAD = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
for f in sorted(glob.glob("governance/build_expressive_teacher_audio_puzzles*.py")):
    tree = ast.parse(open(f, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if (isinstance(k, ast.Constant) and k.value == "tts"
                        and isinstance(v, ast.Constant)):
                    bad = BAD.findall(v.value)
                    if bad:
                        print(os.path.basename(f), "line", v.lineno, bad, v.value[:90])
print("scan done")
