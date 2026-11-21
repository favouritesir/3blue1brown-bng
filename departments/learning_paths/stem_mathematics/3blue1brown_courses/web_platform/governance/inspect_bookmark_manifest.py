import json,re,os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
p=f'{W}/courses/lockdown_math/lesson_02.html'
s=open(p,encoding='utf-8').read()
print('PAGE bookmarks:',re.findall(r'<b1b-bookmark[^>]*>',s)[:8])
m=json.load(open(f'{W}/assets/audio/lockdown_math/lesson_02/manifest.json',encoding='utf-8'))
print('manifest keys:',list(m.keys())[:10])
secs=m.get('sections',{})
if isinstance(secs,dict):
    for k,v in list(secs.items())[:6]:
        cues=v.get('cues',[])
        first=cues[0].get('start_ms') if cues else None
        print(' ',k,'cues',len(cues),'first_start_ms',first,'audio',v.get('audio_file'))
