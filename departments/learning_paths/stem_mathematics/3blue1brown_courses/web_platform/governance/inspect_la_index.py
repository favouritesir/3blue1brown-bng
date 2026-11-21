import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
s=open(W+'/courses/linear_algebra/index.html',encoding='utf-8').read()
# find where lesson_01 appears, show surrounding context
i=s.find('lesson_01.html')
print('first lesson_01 at',i,'of',len(s))
print(s[max(0,i-1500):i+2500])
