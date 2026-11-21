import re, os, urllib.request, urllib.error
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/linear_algebra/lesson_12.html'
s=open(p,encoding='utf-8').read()
srcs=set(re.findall(r'<img[^>]+src="([^"]+)"', s))
base='http://127.0.0.1:8085/courses/linear_algebra/'
bad=[]
for src in srcs:
    if src.startswith('http'):
        url=src
    else:
        url=urllib.parse.urljoin(base, src)
    try:
        req=urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=8) as r:
            if r.status>=400: bad.append((src,r.status))
    except Exception as e:
        bad.append((src,str(e)[:60]))
print('IMAGES FOUND:', len(srcs))
print('BAD:', len(bad))
for b in bad[:20]: print(' ', b)
