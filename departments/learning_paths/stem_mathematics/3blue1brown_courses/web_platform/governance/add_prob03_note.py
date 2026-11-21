p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/OFFICIAL_SOURCE_NOTES.md'
s=open(p,encoding='utf-8').read()
note = """
## PROBABILITY L03 — Binomial Distribution and Pascal's Triangle — NEXT
Authoritative data `data/probability/lesson_03.json`; youtube_id `8idr1WZ1A7Q` (verified "Binomial distributions | Probabilities of probabilities, part 1" via oEmbed). Official source https://www.3blue1brown.com/lessons/binomial-distributions. Core: repeated independent Bernoulli trials (coin flips), exactly k heads in n flips = C(n,k)/2^n; binomial coefficient n-choose-k = n!/(k!(n-k)!); Pascal's triangle construction (each entry = sum of two above), connection to combinatorics (paths / lattice grids); probabilities of probabilities (distribution over outcomes); expected value np; bell-curve emergence as n grows; quiz examples (e.g. P(exactly 2 heads in 5 flips)=10/32; 5-heads-in-10). Use data JSON as primary source (all Bengali sections/formulas/quizzes/figures). Manifest keys from `assets/audio/probability/lesson_03/manifest.json`.

"""
if 'PROBABILITY L03 —' not in s:
    s=s.replace('## নীতি', note + '## নীতি')
open(p,'w',encoding='utf-8').write(s)
print('L03 note:', 'PROBABILITY L03 —' in s)
