import glob, os, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
# search for bookmark time attributes matching screenshot seconds 0,64,140,158,90
for p in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    s=open(p,encoding='utf-8',errors='ignore').read()
    bms=re.findall(r'<b1b-bookmark[^>]*time="([^"]+)"[^>]*time-bn="([^"]+)"',s)
    if not bms: continue
    secs=[float(x[0] or 0) for x in bms]
    if any(abs(v-64)<1 for v in secs) and any(abs(v-158)<2 for v in secs):
        print(os.path.relpath(p,W),bms[:10])
# also dump a few new-course lesson bookmark lists to see what they look like
for c in ['lockdown_math','probability','linear_algebra']:
    p=f'{W}/courses/{c}/lesson_02.html'
    s=open(p,encoding='utf-8').read()
    print(c,'L02 bookmarks:',re.findall(r'time-bn="([^"]+)"',s)[:8])
