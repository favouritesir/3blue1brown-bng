import re, urllib.request, urllib.parse
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/linear_algebra/lesson_12.html'
s=open(p,encoding='utf-8').read()
srcs=set(re.findall(r'<b1b-figure[^>]+src="([^"]+)"', s))
base='http://127.0.0.1:8085/courses/linear_algebra/'
bad=[]
for src in srcs:
    url=src if src.startswith('http') else urllib.parse.urljoin(base,src)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=8) as r:
            if r.status>=400: bad.append((src,r.status))
    except Exception as e:
        bad.append((src,str(e)[:60]))
print('B1B FIGURE SRCS:',len(srcs),'BAD:',len(bad))
for b in bad[:25]: print(' ',b)
