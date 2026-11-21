# -*- coding: utf-8 -*-
import json, os
base = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(base, '..', 'assets', 'audio', 'geometry'))
for n in (1, 2, 3, 4, 5, 6):
    mf = json.load(open(os.path.join(root, f'lesson_{n:02d}', 'manifest.json'), encoding='utf-8'))
    print('\nLESSON %d  keys=%s' % (n, list(mf.keys())))
    for sid, sec in mf['sections'].items():
        types = [c['type'] for c in sec['cues']]
        print('  %-26s %-34s cues=%d %s' % (sid, sec['audio_file'], len(types), types))
