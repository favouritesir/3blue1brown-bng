import json, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
p=f'{W}/data/probability/lesson_03.json'
d=json.load(open(p,encoding='utf-8'))
print('top keys:',list(d.keys())[:10])
sec=d.get('sections',[])
print('sections:',[s.get('id') for s in sec])
print('meta:',str(d.get('meta',{}))[:200])
print('manifest exists:',os.path.isfile(f'{W}/assets/audio/probability/lesson_03/manifest.json'))
