"""Read-only: scan all dubbing verification.json files and report fill-policy compliance."""
import os, json, glob
ROOT='departments/learning_paths/stem_mathematics/3blue1brown_courses'
rows=[]
for p in glob.glob(f'{ROOT}/**/dubbing_pipeline/**/verification.json', recursive=True):
    try:
        d=json.load(open(p,encoding='utf-8'))
    except Exception:
        continue
    if d.get('cue_count',0)<5:
        continue
    lesson=d.get('lesson') or d.get('experiment') or '?'
    scale=d.get('timeline_scale')
    fill=d.get('median_fill')
    gap=d.get('max_internal_gap_s')
    ok=d.get('fill_policy_met')
    rows.append((os.path.relpath(p,ROOT), d.get('cue_count'), scale, fill, gap, ok))
rows.sort()
print(f"{'experiment':<70} {'cues':>4} {'scale':>6} {'fill':>6} {'gap':>6} {'ok':>5}")
for r in rows:
    exp,cues,scale,fill,gap,ok=r
    sc=f'{scale:.2f}' if isinstance(scale,(int,float)) else str(scale)
    fl=f'{fill:.3f}' if isinstance(fill,(int,float)) else 'n/a'
    gp=f'{gap:.2f}' if isinstance(gap,(int,float)) else 'n/a'
    flag='' if (isinstance(fill,(int,float)) and fill>=0.72) else '  <-- LOW'
    print(f'{exp[-70:]:<70} {cues:>4} {sc:>6} {fl:>6} {gp:>6} {str(ok):>5}{flag}')
print('\nTotal videos:',len(rows))
low=[r for r in rows if not (isinstance(r[3],(int,float)) and r[3]>=0.72)]
print('Need re-render (fill<0.72 or unknown):',len(low))
