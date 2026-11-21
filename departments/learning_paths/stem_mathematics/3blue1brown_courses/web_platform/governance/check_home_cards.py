import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
h=open(W+'/index.html',encoding='utf-8').read()
print('lockdown count:',h.count('courses/lockdown_math/index.html'))
print('data-hrefs:',re.findall(r'data-href="([^"]*index\.html)"',h))
