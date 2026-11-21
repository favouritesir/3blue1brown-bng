import glob, json, re
ROOT='departments/learning_paths/stem_mathematics/3blue1brown_courses'
for p in glob.glob(f'{ROOT}/**/lesson_01*/dubbing_pipeline/**/*master*.json',recursive=True)[:20]:
    print(p)
    try:
        d=json.load(open(p,encoding='utf-8'))
        arr=d if isinstance(d,list) else (d.get('cues') or d.get('segments') or d.get('script') or [])
        print('  items',len(arr),'sample',json.dumps(arr[0],ensure_ascii=False)[:250] if arr else '')
    except Exception as e: print('  ERR',e)
