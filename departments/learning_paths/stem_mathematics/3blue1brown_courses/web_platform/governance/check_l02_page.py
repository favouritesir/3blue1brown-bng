import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
for n in [1,2,3]:
    p=f'{W}/courses/linear_algebra/lesson_{n:02d}.html'
    s=open(p,encoding='utf-8').read()
    title=re.search(r'<title>(.*?)</title>',s)
    h1=re.findall(r'<h1[^>]*>(.*?)</h1>',s)[:2]
    srcs=set(re.findall(r'video-src="([^"]+)"',s))
    print(f'L{n}: title={title.group(1)[:70] if title else "?"}')
    print(f'     h1={[re.sub("<[^>]+>","",x)[:60] for x in h1]}')
    print(f'     video-src={list(srcs)[:2]}')
