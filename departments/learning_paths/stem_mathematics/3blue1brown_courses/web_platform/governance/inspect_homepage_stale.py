import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
h=open(W+'/index.html',encoding='utf-8').read()
for kw in ['01-05','5 / 15','আসছে']:
    print('\n===',kw,'===')
    for m in list(re.finditer(re.escape(kw),h))[:4]:
        print(repr(h[max(0,m.start()-120):m.end()+120]))
