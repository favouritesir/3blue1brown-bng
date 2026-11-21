"""Read-only: oEmbed-check all Lockdown + remaining video IDs for 3B1B authorship."""
import json, urllib.request, urllib.error, glob, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
ids={}
for course in ('lockdown_math','differential_equations','probability','neural_networks'):
    for p in sorted(glob.glob(f'{W}/data/{course}/lesson_*.json')):
        d=json.load(open(p,encoding='utf-8'))
        vid=(d.get('youtube_id') or d.get('meta',{}).get('youtube_id'))
        n=int(os.path.basename(p).split('_')[1].split('.')[0])
        if vid: ids[(course,n)]=vid
for (course,n),vid in sorted(ids.items()):
    try:
        url=f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'
        d=json.load(urllib.request.urlopen(url,timeout=12))
        title=d.get('title','?'); author=d.get('author_name','?')
        flag='' if '3blue1brown' in author.lower() or '3blue' in author.lower() else '  <-- NOT 3B1B'
        print(f'{course} L{n}: {vid} | {author} | {title[:45]}{flag}')
    except Exception as e:
        print(f'{course} L{n}: {vid} | ERROR {e}')
