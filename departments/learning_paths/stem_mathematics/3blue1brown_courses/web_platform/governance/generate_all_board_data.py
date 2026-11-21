"""Generate board_data.json for ALL courses (original 6 + new topic courses) from data/ dirs."""
import os, json, glob, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
board_path=W+'/board_data.json'
board=json.load(open(board_path,encoding='utf-8'))
existing={c['id'] for c in board}
completed=json.load(open(W+'/governance/completed_lessons.json',encoding='utf-8'))
ids=completed.get('completed_lessons',completed)
if isinstance(ids,dict): ids=ids.get('completed',[])
BN={'analysis':'বিশ্লেষণ','physics':'পদার্থবিজ্ঞান','computer_science':'কম্পিউটার বিজ্ঞান','why_pi':'কেন পাই','puzzles':'ধাঁধা','geometry':'জ্যামিতি','topology':'টপোলজি','fractals':'ফ্র্যাক্টাল','group_theory':'গ্রুপ তত্ত্ব','number_theory':'সংখ্যা তত্ত্ব','guest_videos':'অতিথি ভিডিও','talks':'বক্তৃতা','videos_elsewhere':'অন্য চ্যানেলে','best_of':'সেরা ভিডিও'}
EMO={'analysis':'∫','physics':'⚛','computer_science':'💻','why_pi':'π','puzzles':'🧩','geometry':'📐','topology':' knots','fractals':'🌀','group_theory':' symmetric','number_theory':'🔢','guest_videos':'🎥','talks':'🎤','videos_elsewhere':'📺','best_of':'⭐'}
def titles_from_data(d):
    p=f'{W}/data/{d}/lesson_01.json'
    if not os.path.isfile(p): return d,d
    try:
        j=json.load(open(p,encoding='utf-8'))
        m=j.get('meta',{})
        return j.get('title_en') or m.get('title_en') or d, j.get('title_bn') or m.get('title_bn') or d
    except: return d,d
added=[]
for d in sorted(os.listdir(W+'/data')):
    dp=f'{W}/data/{d}'
    if not os.path.isdir(dp) or d in existing: continue
    lessons=[]
    files=sorted(glob.glob(dp+'/lesson_*.json'))
    if not files: continue
    for i,f in enumerate(files,1):
        num=f'{i:02d}'
        try:
            j=json.load(open(f,encoding='utf-8')); m=j.get('meta',{})
            en=j.get('title_en') or m.get('title_en') or f'Lesson {num}'
            bn=j.get('title_bn') or m.get('title_bn') or en
        except: en=bn=f'Lesson {num}'
        lid=f'{d}_l{num}'
        html=f'{W}/courses/{d}/lesson_{num}.html'
        man=f'{W}/assets/audio/{d}/lesson_{num}/manifest.js'
        vids=glob.glob(f'{W}/media_vault/{d}/lesson_{num}/experiments/*full_dubbed*.mp4')
        real=[v for v in vids if os.path.getsize(v)>1000000]
        lessons.append({'id':lid,'num':num,'title_en':en,'title_bn':bn,
            'status':'completed' if lid in ids else 'under_review',
            'has_html':os.path.isfile(html),'html_path':f'courses/{d}/lesson_{num}.html',
            'has_data':True,'data_path':f'data/{d}/lesson_{num}.json',
            'has_manifest':os.path.isfile(man),'manifest_path':f'assets/audio/{d}/lesson_{num}/manifest.js',
            'audio_count':len(glob.glob(f'{W}/assets/audio/{d}/lesson_{num}/*.mp3')),
            'has_vault_mp4':bool(real),'uses_components':os.path.isfile(html)})
    en,bn=titles_from_data(d)
    board.append({'id':d,'title':en,'title_bn':BN.get(d,bn),'badge':'Topic collection',
        'accent':'#74c0e3','total':len(lessons),'lessons':lessons})
    added.append((d,len(lessons)))
json.dump(board,open(board_path,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('added courses:',len(added),added)
import collections
print('board totals:',collections.Counter(l['status'] for c in board for l in c['lessons']))
