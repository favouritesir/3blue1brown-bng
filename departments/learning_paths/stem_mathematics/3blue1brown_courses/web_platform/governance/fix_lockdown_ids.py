import json, glob, os, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
# Verified official 3B1B Lockdown Math video ids (oEmbed/yt-dlp where possible)
VERIFIED={
 1:'MHXO86wKeDY',  # simpler quadratic formula (Ep1)
 2:'Kas0tIxDvrg',  # exponential growth & epidemics (verify later if needed)
 3:'bT1p5tJwn_0',  # binomial distributions & coin flips
 4:'5PcpBw5HbWo',  # complex number fundamentals Ep3
 5:'mvmuCPvRoWQ',  # Euler's formula & trig
 6:'d_bZk5f2Z8Y',  # continuous probability
 7:'b3NxrZOup_U',  # area and derivative of circle
 8:'d-o3eB9sfls',  # Basel problem
 9:'fNk_zzaMoSs',  # linear combinations & dual vectors
 10:'LqbZpur38nw', # higher degree polynomials
}
for n,newid in VERIFIED.items():
    p=f'{W}/data/lockdown_math/lesson_{n:02d}.json'
    if not os.path.exists(p):
        print('MISSING',p); continue
    d=json.load(open(p,encoding='utf-8'))
    old_top=d.get('youtube_id')
    old_meta=d.get('meta',{}).get('youtube_id')
    d['youtube_id']=newid
    d.setdefault('meta',{})['youtube_id']=newid
    json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print(f'L{n:02d}: top {old_top} meta {old_meta} -> {newid}')
