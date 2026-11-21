import re
s=open('departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/linear_algebra/lesson_01.html',encoding='utf-8').read()
print(set(re.findall(r'video-src="([^"]+)"',s)))
