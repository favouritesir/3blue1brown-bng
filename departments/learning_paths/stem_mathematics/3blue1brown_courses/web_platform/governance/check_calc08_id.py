import re
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/data/calculus/lesson_08.json'
s=open(p,encoding='utf-8').read()
print('ids', re.findall(r'"[A-Za-z0-9_-]{11}"', s)[:8])
print('urls', re.findall(r'https?://[^" ]+', s)[:5])
