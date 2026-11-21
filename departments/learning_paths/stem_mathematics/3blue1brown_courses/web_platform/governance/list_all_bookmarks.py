import glob,os,re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for p in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    s=open(p,encoding='utf-8',errors='ignore').read()
    b=re.findall(r'time-bn="([^"]+)"',s)
    if b: print(os.path.basename(os.path.dirname(p)),os.path.basename(p),':',b[:6])
