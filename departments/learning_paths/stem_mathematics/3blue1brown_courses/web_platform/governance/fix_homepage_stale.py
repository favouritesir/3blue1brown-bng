import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
p=W+'/index.html'
h=open(p,encoding='utf-8').read()
h=h.replace('Only Linear Algebra lessons 01-05 are Bengali-dubbed; other series open the official 3blue1brown.com topic pages.',
            'All 53 lessons across 6 series are fully Bengali-dubbed with interactive labs and quizzes.')
h=h.replace('Bengali-dubbed now: Linear Algebra lessons 01-05 (চলমান). All other series: আসছে - tap a card to open the official 3blue1brown.com topic page.',
            'All 53 lessons across 6 core series are fully Bengali-dubbed, with full-length video and expressive teacher narration. Tap a card to explore.')
# update topic count mention if stale
h=h.replace('65+ lessons','53 lessons')
open(p,'w',encoding='utf-8').write(h)
print('stale 01-05:',h.count('01-05'),'| আছে:',h.count('আসছে'))
# verify lockdown card present
print('lockdown card:', 'courses/lockdown_math/index.html' in h)
