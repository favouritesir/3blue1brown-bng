import re, os
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/probability/lesson_01.json'
s=open(p,encoding='utf-8').read()
print('ids', re.findall(r'"[A-Za-z0-9_-]{11}"', s)[:8])
print('keys', list(__import__('json').loads(s).keys())[:12])
print('has_html', os.path.isfile('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/probability/lesson_01.html'))
