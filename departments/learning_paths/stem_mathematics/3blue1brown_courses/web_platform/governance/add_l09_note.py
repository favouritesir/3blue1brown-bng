p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/OFFICIAL_SOURCE_NOTES.md'
s=open(p,encoding='utf-8').read()
note = """
## CALCULUS L09 — `/lessons/area-and-slope` (পরবর্তী ব্যাচ)
Chapter 12 · "What does area have to do with slope?" · May 6 2017 · epigraph **Gian-Carlo Rota**: "We often hear that mathematics consists mainly of proving theorems. Is a writer's job mainly that of writing sentences?" · সেকশন: Quick Intuition (average = area under curve ÷ width, pile of sand analogy); Average of sine function (sin x on 0–π, daylight hours example, finite samples → dx spacing, number of samples ≈ π/dx, rearrange sum → integral ÷ π); Computing a result (antiderivative of sin = −cos, ∫₀^π sin = (−cos π)−(−cos 0)=2, average 2/π≈0.64); Comprehensive Question (average of f(x)=−x²+4x−3 from 1 to 3 → 0.666); Another perspective (average = rise-over-run slope of antiderivative −cos between endpoints = average of all tangent slopes); Generalize (average = ∫_a^b f dx/(b−a) = [F(b)−F(a)]/(b−a), signed area, finite-vs-continuous average); Summary (second sensation for integrals). Video `FnJqaIESC2s` · next higher-order-derivatives `BLkz5LGWihw`.

"""
if 'CALCULUS L09' not in s:
    s=s.replace('## নীতি', note + '## নীতি')
open(p,'w',encoding='utf-8').write(s)
print('L09 added:', 'CALCULUS L09' in s)
