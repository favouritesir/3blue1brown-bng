import glob,os,re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
weird=[]
for p in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    s=open(p,encoding='utf-8',errors='ignore').read()
    times=re.findall(r'<b1b-bookmark[^>]*\btime="([^"]+)"',s)
    for t in times:
        if not re.fullmatch(r'\d+(\.\d+)?',t):
            weird.append((os.path.relpath(p,W),t))
print('non-numeric time attributes:',len(weird))
for w in weird[:30]: print(' ',w)
# also check rendered chips with jumpToLessonTime(NaN)
nan=[]
for p in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    s=open(p,encoding='utf-8',errors='ignore').read()
    if 'jumpToLessonTime(NaN' in s or 'jumpToLessonTime(0, this)' in s:
        nan.append(os.path.relpath(p,W))
print('pages with jumpToLessonTime(0) or NaN in source:',nan[:10])
