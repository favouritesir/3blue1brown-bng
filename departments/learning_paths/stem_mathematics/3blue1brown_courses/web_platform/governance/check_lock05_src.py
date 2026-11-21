import re
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/lockdown_math/lesson_05.html'
s=open(p,encoding='utf-8').read()
print('video-src:',set(re.findall(r'video-src="([^"]+)"',s)))
