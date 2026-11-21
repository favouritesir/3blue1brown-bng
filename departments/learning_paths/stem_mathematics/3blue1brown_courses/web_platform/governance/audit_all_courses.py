"""Find ALL course data/course dirs in the platform — beyond the 6 we migrated."""
import os, glob, json, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
print('=== DATA dirs ===')
for d in sorted(os.listdir(W+'/data')):
    p=W+'/data/'+d
    if os.path.isdir(p):
        n=len(glob.glob(p+'/lesson_*.json'))
        print(f'  {d}: {n} lessons')
print('\n=== COURSES page dirs ===')
for d in sorted(os.listdir(W+'/courses')):
    p=W+'/courses/'+d
    if os.path.isdir(p):
        pages=len(glob.glob(p+'/lesson_*.html'))
        comp=len([1 for f in glob.glob(p+'/lesson_*.html') if '<b1b-' in open(f,encoding='utf-8',errors='ignore').read()])
        print(f'  {d}: {pages} pages ({comp} component)')
print('\n=== AUDIO dirs ===')
for d in sorted(os.listdir(W+'/assets/audio')):
    p=W+'/assets/audio/'+d
    if os.path.isdir(p):
        print(f'  {d}: {len(glob.glob(p+"/lesson_*/manifest.json"))} manifests')
print('\n=== HOMEPAGE links ===')
h=open(W+'/index.html',encoding='utf-8',errors='ignore').read()
links=sorted(set(re.findall(r'href="([^"]+)"',h)))
for l in links[:80]:
    print('  ',l)
print('total homepage links:',len(links))
