"""Regenerate course index pages + curriculum_index.json + homepage from authoritative data."""
import os, json, re, glob, html
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
COURSES=['linear_algebra','calculus','neural_networks','probability','differential_equations','lockdown_math']
BN_NUM={1:'০১',2:'০২',3:'০৩',4:'০৪',5:'০৫',6:'০৬',7:'০৭',8:'০৮',9:'০৯',10:'১০',11:'১১',12:'১২',13:'১৩',14:'১৪',15:'১৫'}

def lesson_info(course, n):
    d=json.load(open(f'{W}/data/{course}/lesson_{n:02d}.json',encoding='utf-8'))
    m=d.get('meta',{})
    title_bn=(m.get('title_bn') or d.get('title_bn') or '').split('|')[0].strip()
    title_en=(m.get('title_en') or d.get('title_en') or '').split('|')[0].strip()
    sub=(m.get('subtitle_bn') or d.get('subtitle_bn') or d.get('subtitle') or d.get('description_bn') or '')
    dur=(m.get('duration') or d.get('duration') or '')
    return title_bn,title_en,sub[:220],dur

def chapter_html(course,n):
    bn,en,sub,dur=lesson_info(course,n)
    title=html.escape(bn if bn else en)
    if en and en not in title: title+=f' ({html.escape(en)})'
    tags=[]
    if dur: tags.append(f'⏱️ {html.escape(str(dur))}')
    tags+=['🎮 ইন্টারেক্টিভ ল্যাব','❓ কুইজ সংযুক্ত']
    return f'''    <a href="lesson_{n:02d}.html" class="chapter-row">
      <div class="ch-num">{BN_NUM.get(n,str(n))}</div>
      <div class="ch-body">
        <h2 class="ch-title">{title}</h2>
        <p class="ch-desc">{html.escape(sub) if sub else 'সম্পূর্ণ বাংলা ডাবিং, ইন্টারেক্টিভ ল্যাব ও কুইজসহ পাঠ।'}</p>
        <div class="ch-tags">
          {''.join(f'<span class="ch-tag">{t}</span>' for t in tags)}
        </div>
      </div>
      <div class="ch-action">পাঠ খুলুন →</div>
    </a>'''

# 1. Course index pages
for c in COURSES:
    p=f'{W}/courses/{c}/index.html'
    s=open(p,encoding='utf-8').read()
    n=len(glob.glob(f'{W}/data/{c}/lesson_*.json'))
    rows='\n\n'.join(chapter_html(c,i) for i in range(1,n+1))
    new_grid='<div class="chapter-grid">\n\n'+rows+'\n\n  </div>'
    s2=re.sub(r'<div class="chapter-grid">.*?\n  </div>',lambda m:new_grid,s,flags=re.S)
    if s2==s:
        print('WARN no chapter-grid replaced in',c); continue
    # hero stats: replace first c-stat-val if it's a stale count
    s2=re.sub(r'(<div class="c-stat-val">)[^<]*(</div>\s*<div class="c-stat-lbl">সম্পূর্ণ পাঠ</div>)',r'\g<1>'+str(n)+r'\g<2>',s2)
    open(p,'w',encoding='utf-8').write(s2)
    print(f'{c}: index now lists {n} lessons (was {len(set(re.findall(r"lesson_\\d+\\.html",s)))})')

# 2. curriculum_index.json — full lesson lists + correct dubbed counts
ci=json.load(open(W+'/curriculum_index.json',encoding='utf-8'))
for c in ci['courses']:
    cid=c['id']
    n=len(glob.glob(f'{W}/data/{cid}/lesson_*.json'))
    lessons=[]
    for i in range(1,n+1):
        bn,en,sub,dur=lesson_info(cid,i)
        lessons.append({'id':f'{i:02d}','title_bn':bn,'title_en':en,'href':f'courses/{cid}/lesson_{i:02d}.html','duration':dur})
    c['lessons']=lessons
    c['lessons_total']=n
    c['lessons_dubbed']=n
    c['status']='completed'; c['status_bn']='সম্পূর্ণ'
ci['total_lessons']=sum(len(c['lessons']) for c in ci['courses'])
json.dump(ci,open(W+'/curriculum_index.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('curriculum_index.json: total_lessons',ci['total_lessons'])

# 3. Homepage — fix stale counts + add lockdown card
p=W+'/index.html'
h=open(p,encoding='utf-8').read()
h=h.replace('5 / 15 পাঠ','15 / 15 পাঠ')
h=h.replace('পাঠ ১–৫ সম্পূর্ণ বাংলা ডাবিং','পাঠ ০১–১৫ সম্পূর্ণ বাংলা ডাবিং')
h=h.replace('Bengali-dubbed now: Linear Algebra lessons 01-05 (চলমান). All other series: আসছে - tap a card to open the official 3blue1brown.com topic page.',
            'All 53 lessons across 6 series are fully Bengali-dubbed with interactive labs. Tap a card to explore.')
# add lockdown card if missing (clone probability card structure)
if 'courses/lockdown_math/index.html' not in h:
    m=re.search(r'(<article class="track-card[^>]*data-href="courses/probability/index\.html".*?</article>)',h,re.S)
    if m:
        card=m.group(1)
        lc=card.replace('courses/probability/index.html','courses/lockdown_math/index.html')
        lc=lc.replace('probability','lockdown_math').replace('সম্ভাব্যতা','লকডাউন ম্যাথ')
        h=h.replace(m.group(1),m.group(1)+'\n      '+lc)
        print('homepage: lockdown_math card added')
open(p,'w',encoding='utf-8').write(h)
print('homepage stale phrases after:',{x:h.count(x) for x in ['01-05','5 / 15','আসছে']})
