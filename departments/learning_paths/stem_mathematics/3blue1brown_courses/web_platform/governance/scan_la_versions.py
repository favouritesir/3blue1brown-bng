import os, glob, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in range(1,16):
    d=f'{W}/media_vault/lesson_{n:02d}'
    page=f'{W}/courses/linear_algebra/lesson_{n:02d}.html'
    files=sorted(os.path.basename(x) for x in glob.glob(d+'/*.mp4')+glob.glob(d+'/experiments/*.mp4'))
    src=set()
    if os.path.isfile(page):
        src=set(re.findall(r'video-src="([^"]+)"',open(page,encoding='utf-8').read()))
    print(f'L{n}: src={[os.path.basename(s) for s in src]}')
    print(f'    files={files}')
