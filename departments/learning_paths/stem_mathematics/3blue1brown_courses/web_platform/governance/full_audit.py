import json, os, collections, glob
w='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
done=json.load(open(f'{w}/governance/completed_lessons.json',encoding='utf-8'))['completed_lessons']
board=json.load(open(f'{w}/board_data.json',encoding='utf-8'))
print('COMPLETED LIST:', len(done), done)
print('BOARD STATUS:', collections.Counter(l['status'] for c in board for l in c['lessons']))
print()
for c in board:
    rows=[]
    for l in c['lessons']:
        n=l['num']; cid=c['id']
        html=l['has_html']; comp=l.get('uses_components')
        mani=l['has_manifest']
        vid=os.path.isfile(f"{w}/media_vault/lesson_{n}/3b1b_lesson_{n}_bangla_dubbed_video.mp4")
        exp=glob.glob(f"{w}/media_vault/lesson_{n}/experiments/*full_dubbed*.mp4")
        rows.append(f"{n}:{'H' if html else '-'}{'C' if comp else '-'}{'M' if mani else '-'}{'V' if vid else '-'}{'E' if exp else '-'}{'*' if f'{cid}_l{n}' in done else ' '}")
    print(f"{c['id']:22} " + ' '.join(rows))
