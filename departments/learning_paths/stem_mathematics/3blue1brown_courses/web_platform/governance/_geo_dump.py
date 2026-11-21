# -*- coding: utf-8 -*-
import json, os
base = os.path.dirname(os.path.abspath(__file__))
for n in (1, 2, 3, 4, 5, 6):
    d = json.load(open(os.path.join(base, f'geo{n:02d}_dom_blocks.json'), encoding='utf-8'))
    print('\n' + '#' * 70)
    print('LESSON', n)
    for s in d['sections']:
        print('\n=== %s | %s | cues %d' % (s['id'], s['title'], len(s['blocks'])))
        for i, b in enumerate(s['blocks']):
            print('  [%d] %s: %s' % (i, b['type'], b['text']))
