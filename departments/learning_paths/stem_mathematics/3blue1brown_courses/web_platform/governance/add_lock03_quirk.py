p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/VIDEO_ID_DATA_QUIRKS.md'
s=open(p,encoding='utf-8').read()
note='''
## Lockdown L03 — FIXED 2026-11-20
- data id `bT1p5tJwn_0` was NOT 3B1B (jbstatistics "Intro to Bernoulli Distribution", 301s). Agent built a 301s dub before flagging.
- FIXED to `8idr1WZ1A7Q` (official 3B1B "Binomial distributions | Probabilities of probabilities, part 1") — closest official source for the lesson topic. Old jbstatistics video renamed to `..._jbstatistics_replaced.mp4`; new official dub to be built at the same video-src path.
'''
if 'Lockdown L03 — FIXED' not in s:
    s += '\n' + note
open(p,'w',encoding='utf-8').write(s)
print('note added:', 'Lockdown L03 — FIXED' in s)
