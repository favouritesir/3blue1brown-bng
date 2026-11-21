p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance/OFFICIAL_SOURCE_NOTES.md'
s=open(p,encoding='utf-8').read()
note = """
## CALCULUS L08 — `/lessons/integration` (পরবর্তী ব্যাচ)
Chapter 11 · "Integration and the fundamental theorem of calculus" · May 5 2017 · epigraph **Alexander Grothendieck**: "One should never try to prove anything that is not almost obvious" · সেকশন: Velocity (speedometer-only car, v(t)=t(8−t)=8t−t², 0–8s); Relationship between velocity and distance (antiderivative, area under curve as distance, constant-velocity rectangles); Integral Notation (∫ stretched S, dt dual role factor+spacing, limit as dt→0, signed area); Area Under Graphs (variable right endpoint T, area function s(T), ds≈v(T)·dT, derivative of area function = graph function); Find the antiderivative (8t−t² → 4t²−⅓t³, quizzes 3x²+5 → x³+5x, x+2 → ½x²+2x); The +C issue (constant cancels, lower bound, ∫₀ᵀ, distance 85.33m at T=8, quizzes v=−5/2 t+20 → 80m, v=−t(t−10) between 2–6); Fundamental theorem (F(top)−F(bottom), integrate all inputs via two endpoints); Quick recap; Negative area (signed area, quiz v=2t³−2t² returns to start at t=4/3); Next. Video `rfG8ce4nNh0` (from data JSON) · next area-and-slope `FnJqaIESC2s`.

"""
if 'CALCULUS L08' not in s:
    s=s.replace('## নীতি', note + '## নীতি')
open(p,'w',encoding='utf-8').write(s)
print('L08 added:', 'CALCULUS L08' in s)
