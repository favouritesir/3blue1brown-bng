# -*- coding: utf-8 -*-
"""Validate per-lesson expressive scripts against the extracted live DOM."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOM = json.load(open(os.path.join(ROOT, 'governance', 'why_pi_dom_extract.json'),
                     encoding='utf-8'))
BAD = re.compile(r'[A-Za-z\\$⟦⟧{}\[\]—–\-]')
FORBIDDEN = 'চিত্র প্রদর্শনী'

ok_all = True
for nn in ['01', '02', '03', '04', '05', '06', '07', '08']:
    scripts = json.load(open(os.path.join(ROOT, 'governance', 'why_pi_scripts',
                                          'lesson_%s.json' % nn), encoding='utf-8'))
    dom_secs = DOM['lesson_' + nn]['sections']
    assert len(scripts['sections']) == len(dom_secs), (nn, 'section count')
    total = 0
    for sec, dsec in zip(scripts['sections'], dom_secs):
        assert sec['id'] == dsec['id'], (nn, sec['id'], dsec['id'])
        dom_types = [n['type'] for n in dsec['nodes']]
        types = [c['type'] for c in sec['cues']]
        if types != dom_types:
            ok_all = False
            print('TYPE MISMATCH', nn, sec['id'], types, dom_types)
        for i, cue in enumerate(sec['cues']):
            total += 1
            t = cue['tts']
            bad = BAD.findall(t)
            if bad:
                ok_all = False
                print('BAD CHARS', nn, sec['id'], i, set(bad), t[:60])
            if FORBIDDEN in t:
                ok_all = False
                print('FORBIDDEN LABEL', nn, sec['id'], i)
            dev = [c for c in t if 0x0900 <= ord(c) <= 0x097f and c != '।']
            if dev:
                ok_all = False
                print('DEVANAGARI', nn, sec['id'], i, set(dev))
            sents = [s for s in t.split('।') if s.strip()]
            if not (2 <= len(sents) <= 4):
                ok_all = False
                print('SENTENCE COUNT', nn, sec['id'], i, len(sents))
    print('lesson_%s: %d sections, %d cues' % (nn, len(scripts['sections']), total))
print('ALL VALID' if ok_all else 'VALIDATION FAILED')
sys.exit(0 if ok_all else 1)
