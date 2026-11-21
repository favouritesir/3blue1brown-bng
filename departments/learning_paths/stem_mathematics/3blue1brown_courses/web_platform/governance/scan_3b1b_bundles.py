import urllib.request, re
base='https://www.3blue1brown.com/assets/'
files=['site-DtxZ8-8h.js','root-D4Pcswfl.js','startCase-GB2jJtZo.js','Form-Clr7uBLQ.js','entry.client-CtKfh0UU.js']
for f in files:
    try: s=urllib.request.urlopen(base+f,timeout=20).read().decode('utf-8','ignore')
    except Exception as e: print(f,'ERR',e); continue
    print('\n===',f,'len',len(s))
    for kw in ['topic','lesson','fetch(','/api','lessons.json','lessonList','title_en']:
        c=s.count(kw)
        if c: print(' ',kw,c)
    for m in re.findall(r'fetch\(([^)]{0,100})',s)[:6]: print('  fetch:',m[:120])
