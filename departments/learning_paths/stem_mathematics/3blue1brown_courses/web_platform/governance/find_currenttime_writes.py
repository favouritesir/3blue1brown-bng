import glob,os
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/assets/js'
for p in glob.glob(W+'/*.js'):
    lines=open(p,encoding='utf-8',errors='ignore').read().splitlines()
    for i,l in enumerate(lines):
        if 'currentTime' in l and '=' in l and not l.strip().startswith('//'):
            print(f'{os.path.basename(p)}:{i+1}: {l.strip()[:150]}')
