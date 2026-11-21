import re, json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
topics=json.load(open(W+'/governance/topic_lesson_map.json',encoding='utf-8'))
p=W+'/index.html'; h=open(p,encoding='utf-8').read()
BN={'analysis':'বিশ্লেষণ','physics':'পদার্থবিজ্ঞান','computer-science':'কম্পিউটার বিজ্ঞান','why-pi':'কেন পাই','puzzles':'ধাঁধা','geometry':'জ্যামিতি','topology':'টপোলজি','fractals':'ফ্র্যাক্টাল','group-theory':'গ্রুপ তত্ত্ব','number-theory':'সংখ্যা তত্ত্ব','guest-videos':'অতিথি ভিডিও','talks':'বক্তৃতা','videos-elsewhere':'অন্য চ্যানেলে','best-of':'সেরা ভিডিও'}
new=["\n    <!-- Local topic library (all 20 official topics) -->",'    <div class="topic-library" id="topicLibrary" style="margin-top:28px">','      <h3 class="track-card__title" style="margin-bottom:14px">📚 টপিক লাইব্রেরি — সব ২০টি বিষয় (local)</h3>','      <div style="display:flex;flex-wrap:wrap;gap:10px">']
for k in topics:
    if k in ('all',): continue
    bn=BN.get(k,k.replace('-',' '))
    n=len(topics[k]['lessons'])
    new.append(f'        <a href="courses/topics/{k}.html" style="padding:8px 14px;border:1px solid #2a3340;border-radius:20px;text-decoration:none;color:inherit;background:#151b24">{bn} ({n})</a>')
new+=['      </div>','    </div>','']
block='\n'.join(new)
# insert before end of topic-collections section: find the filter bar closing or section end
marker='id="topic-collections"'
i=h.find(marker)
if i<0: print('section not found'); raise SystemExit(1)
# find next section start after i
j=h.find('<section', i+10)
if j<0: j=h.find('</main>',i)
h=h[:j]+block+'\n'+h[j:]
# fix section subtitle to reflect local pages
h=h.replace('Official curriculum of 3blue1brown.com - 6 core series + 11 topic collections.',
            'Official 3Blue1Brown curriculum: 6 core series + 20 topic collections — with local pages for every topic.')
open(p,'w',encoding='utf-8').write(h)
print('linked',len(topics),'topic pages from homepage')
