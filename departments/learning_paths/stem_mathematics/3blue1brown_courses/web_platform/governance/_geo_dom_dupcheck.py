# -*- coding: utf-8 -*-
import json, os
base = os.path.dirname(os.path.abspath(__file__))
for n in range(1, 7):
    d = json.load(open(os.path.join(base, f'geo{n:02d}_dom_blocks.json'), encoding='utf-8'))
    texts = [b['engine_text'] or b['text'] for s in d['sections'] for b in s['blocks']]
    dupes = [t for t in set(texts) if texts.count(t) > 1]
    print(f'geo{n:02d}: {len(texts)} DOM cues, {len(dupes)} duplicate texts')
    for t in dupes:
        print('   DUP:', t[:100])
