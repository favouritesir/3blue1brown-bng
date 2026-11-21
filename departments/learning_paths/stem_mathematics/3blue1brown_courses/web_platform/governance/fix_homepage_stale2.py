import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
p=W+'/index.html'
h=open(p,encoding='utf-8').read()
pat=r'Bengali-dubbed now: Linear Algebra lessons 01-05 \(চলমান\)\.\s*All other series: আসছে\s*-\s*tap a card to open the official 3blue1brown\.com topic page\.'
new='All 53 lessons across 6 core series are fully Bengali-dubbed, with full-length video and expressive teacher narration. Tap a card to explore.'
h2,n=re.subn(pat,new,h)
print('replaced paragraphs:',n)
open(p,'w',encoding='utf-8').write(h2)
print('remaining 01-05:',h2.count('01-05'),'আসছে:',h2.count('আসছে'))
