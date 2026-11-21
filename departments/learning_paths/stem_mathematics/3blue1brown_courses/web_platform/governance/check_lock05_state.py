import re
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/lockdown_math/lesson_05.html'
s=open(p,encoding='utf-8').read()
print('manifest tags:',re.findall(r'<script[^>]*manifest\.js[^>]*>',s)[:2])
print('cache-busters:',re.findall(r'manifest\.js\?v=(\d+)',s))
print('has b1b components:',s.count('<b1b-')>10)
