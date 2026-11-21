"""Generate local landing pages for ALL official 3B1B topics from extracted topic map."""
import json, os, re, html
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
topics=json.load(open(W+'/governance/topic_lesson_map.json',encoding='utf-8'))
BN={'analysis':'বিশ্লেষণ','physics':'পদার্থবিজ্ঞান','computer-science':'কম্পিউটার বিজ্ঞান','why-pi':'কেন পাই','puzzles':'ধাঁধা','geometry':'জ্যামিতি','topology':'টপোলজি','fractals':'ফ্র্যাক্টাল','group-theory':'গ্রুপ তত্ত্ব','number-theory':'সংখ্যা তত্ত্ব','guest-videos':'অতিথি ভিডিও','talks':'বক্তৃতা','videos-elsewhere':'অন্য চ্যানেলে','best-of':'সেরা ভিডিও','neural-networks':'নিউরাল নেটওয়ার্ক','linear-algebra':'লিনিয়ার অ্যালজেব্রা','calculus':'ক্যালকুলাস','differential-equations':'ডিফারেনশিয়াল সমীকরণ','probability':'সম্ভাব্যতা','lockdown-math':'লকডাউন ম্যাথ'}
def title_from_slug(slug):
    words=slug.replace('-',' ').split()
    small={'and':'এবং','the':'','of':'র','a':'','in':'তে'}
    return ' '.join(w.capitalize() for w in words)
os.makedirs(W+'/courses/topics',exist_ok=True)
created=[]
for key,v in topics.items():
    bn=BN.get(key,key.replace('-',' '))
    cards=[]
    for i,slug in enumerate(v['lessons'],1):
        en=title_from_slug(slug)
        official=f'https://www.3blue1brown.com/lessons/{slug}'
        cards.append(f'''        <a class="topic-lesson" href="{official}" target="_blank" rel="noopener">
          <span class="tl-num">{i:02d}</span>
          <span class="tl-body"><strong>{html.escape(en)}</strong><small>অফিশিয়াল ৩ব্লু১ব্রাউন পাঠ →</small></span>
        </a>''')
    page=f'''<!DOCTYPE html>
<html lang="bn" data-theme="dark">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{html.escape(bn)} — ৩ব্লু১ব্রাউন বাংলা</title>
<link rel="stylesheet" href="../../assets/css/main.css"/>
<style>
 body{{background:var(--bg,#0e1117);color:var(--text,#e8eef5);font-family:'Hind Siliguri',sans-serif;margin:0}}
 .wrap{{max-width:900px;margin:0 auto;padding:36px 20px}}
 .crumb a{{color:#74c0e3;text-decoration:none}}.topic-h{{font-size:2rem;margin:12px 0}}
 .topic-sub{{opacity:.8}}.topic-grid{{display:grid;gap:10px;margin-top:24px}}
 .topic-lesson{{display:flex;gap:14px;align-items:center;padding:14px 16px;border:1px solid #2a3340;border-radius:12px;background:#151b24;color:inherit;text-decoration:none;transition:.2s}}
 .topic-lesson:hover{{border-color:#74c0e3;transform:translateX(4px)}}
 .tl-num{{font-weight:700;color:#74c0e3}}.tl-body{{display:flex;flex-direction:column}}.tl-body small{{opacity:.6}}
</style></head><body>
<main class="wrap">
 <nav class="crumb"><a href="../../index.html">← হোম</a> / টপিক লাইব্রেরি</nav>
 <h1 class="topic-h">{html.escape(bn)}</h1>
 <p class="topic-sub">{html.escape(v['title'])} — {len(v['lessons'])}টি অফিশিয়াল পাঠ। প্রতিটি পাঠ ৩ব্লু১ব্রাউন-এ খুলবে; বাংলা ডাবিং ও কম্পোনেন্ট পেজ পর্যায়ক্রমে যোগ করা হচ্ছে।</p>
 <div class="topic-grid">
{chr(10).join(cards)}
 </div>
</main></body></html>'''
    p=W+f'/courses/topics/{key}.html'
    open(p,'w',encoding='utf-8').write(page)
    created.append((key,len(v['lessons'])))
print('created topic pages:',len(created))
for k,n in created: print(' ',k,n)
