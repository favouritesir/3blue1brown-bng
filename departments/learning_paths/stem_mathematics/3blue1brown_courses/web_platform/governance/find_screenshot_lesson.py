import glob, os, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
targets=['০১:০৪','০২:২০','০২:৩৮','০১:৩০']
for p in sorted(glob.glob(W+'/courses/*/lesson_*.html')):
    s=open(p,encoding='utf-8',errors='ignore').read()
    found=[t for t in targets if t in s]
    if len(found)>=2:
        bms=re.findall(r'<b1b-bookmark\s+time="([^"]+)"\s+time-bn="([^"]+)"',s)[:8]
        print(os.path.relpath(p,W),'matches',found,'bookmarks',bms)
