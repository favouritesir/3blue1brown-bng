import glob, os, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
files=glob.glob(W+'/media_vault/**/fill_v2/*fill2.mp4',recursive=True)
print('fill2 files:',len(files))
for f in sorted(files):
    # find if any page references it
    fn=os.path.basename(f)
    used=[]
    for p in glob.glob(W+'/courses/*/lesson_*.html'):
        if fn in open(p,encoding='utf-8',errors='ignore').read():
            used.append(os.path.relpath(p,W))
    print(('SWAPPED' if used else 'PENDING'),os.path.relpath(f,W), used[:1])
