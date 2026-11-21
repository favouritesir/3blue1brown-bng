import json, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in [3]:
    m=f'{W}/assets/audio/neural_networks/lesson_{n:02d}/manifest.json'
    s=open(m,encoding='utf-8').read()
    d=json.load(open(m,encoding='utf-8'))
    print(f'L{n} forbidden:',s.count('চিত্র প্রদর্শনী'))
    print(f'L{n} backup:',os.path.isdir(os.path.dirname(m)+'/_backup_before_expressive_build'))
    sec=d.get('sections',{})
    if isinstance(sec,dict):
        print(' section keys:',list(sec.keys()))
        for k,v in list(sec.items())[:1]:
            print(' audio_file:',v.get('audio_file'),'cues:',len(v.get('cues',[])))
