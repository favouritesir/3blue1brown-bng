import json, glob, os, re
ROOT='departments/learning_paths/stem_mathematics/3blue1brown_courses'
rows=[]
for p in glob.glob(f'{ROOT}/**/dubbing_pipeline/**/verification.json', recursive=True):
    try: d=json.load(open(p,encoding='utf-8'))
    except: continue
    if d.get('cue_count',0)<5: continue
    fill=d.get('median_fill')
    if isinstance(fill,(int,float)) and fill>=0.72: continue
    # identify course+lesson from path
    m=re.search(r'(linear_algebra|calculus|neural_networks|probability|differential_equations|lockdown_math)[\\/]lesson_(\d+)',p)
    if not m: continue
    course,n=m.group(1),int(m.group(2))
    sc=d.get('timeline_scale') or 0
    rows.append((sc,course,n,p))
rows.sort(reverse=True)
print('need re-render:',len(rows))
for sc,course,n,p in rows:
    print(f'{course} L{n:02d} scale={sc:.2f}')
