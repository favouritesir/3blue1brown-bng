import re
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/calculus/lesson_08.html'
s=open(p,encoding='utf-8').read()
new='../../media_vault/calculus/lesson_08/experiments/3b1b_calculus_08_full_dubbed.mp4'
# replace any video-src="..." value (including long data URI) with real path
s2,n=re.subn(r'(video-src=")[^"]*(")', r'\g<1>'+new+r'\g<2>', s)
open(p,'w',encoding='utf-8').write(s2)
print('replaced',n,'video-src refs')
