import glob, os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
needle='3b1b_lesson_01_bangla_dubbed_video_v2.mp4'
for p in glob.glob(W+'/**/*.html',recursive=True):
    try: s=open(p,encoding='utf-8',errors='ignore').read()
    except: continue
    if needle in s:
        print(os.path.relpath(p,W),'count',s.count(needle))
