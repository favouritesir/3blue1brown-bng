p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/OFFICIAL_SOURCE_NOTES.md'
s=open(p,encoding='utf-8').read()
notes = """
## CALCULUS L11 — "What does dx really mean?" (Chapter 12, Essence of calculus) — NEXT
Video `CfW845LNObM` ("The other way to visualize derivatives | Chapter 12"). NOTE: data JSON previously had a wrong duplicate id (`9vKqVkMQHKk`, the paradox-of-derivative video) — corrected in data/calculus/lesson_11.json. This lesson reinterprets the derivative not as a ratio of two separate nudges (df and dx) but as the magnification factor: when you zoom in on a point on f(x), the graph looks like a line, and multiplying by f'(x) is the scaling that turns a small dx into the corresponding df. df = f'(x)·dx. Content is authoritative in `data/calculus/lesson_11.json` — use it as primary source; official 3B1B slug for chapter 12 is `/lessons/the-other-way-to-visualize-derivatives` (website slug 404s, so rely on data JSON + video knowledge). Use component template; manifest keys from `assets/audio/calculus/lesson_11/manifest.json`.

## PROBABILITY L02 — Bayes' Rule and the False Positive Paradox — NEXT
Authoritative data `data/probability/lesson_02.json` (fixed youtube_id `lG4VkPoG3ko` = "The medical test paradox, and redesigning Bayes' rule"). Sections: sec-puzzle (medical test paradox + joint probability), sec-base-rate (base rate fallacy + population partitioning), sec-tree-area (probability tree + area grid), sec-simulator (interactive 1000-person dot grid), sec-formula (algebraic derivation of Bayes + philosophy), sec-quizzes. Key numbers: disease prevalence 0.1%, test 99% accurate → P(diseased | positive) ≈ 9% (false positive paradox); P(A∩B)=P(A|B)P(B); P(A|B)=P(B|A)P(A)/P(B); tree-diagram & area reasoning; Kahneman-Tversky base-rate neglect. Rich Bengali feedback on all quizzes. Official source https://www.3blue1brown.com/lessons/bayes-theorem (Steve librarian/farmer example, 20:1 ratio, representative sample 200 farmers+10 librarians, 40% vs 10%→4/24=16.7%, prior/likelihood/posterior, thinking with area, Linda bank-teller conjunction fallacy) can be added as extra context. Use manifest keys from `assets/audio/probability/lesson_02/manifest.json`.

"""
if 'CALCULUS L11 —' not in s:
    s=s.replace('## নীতি', notes + '## নীতি')
open(p,'w',encoding='utf-8').write(s)
print('notes added:', 'CALCULUS L11 —' in s, 'PROBABILITY L02 —' in s)
