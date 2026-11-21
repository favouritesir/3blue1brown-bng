import urllib.request, re
base='https://www.3blue1brown.com'
h=urllib.request.urlopen(base+'/',timeout=20).read().decode('utf-8','ignore')
assets=sorted(set(re.findall(r'([/\w.-]+\.js)',h)))
needle='Derivative formulas through geometry'
for j in assets:
    u=base+(j if j.startswith('/') else '/assets/'+j)
    try: s=urllib.request.urlopen(u,timeout=12).read().decode('utf-8','ignore')
    except: continue
    if needle in s or 'title:`Derivative' in s:
        print('FOUND',u,len(s))
        m=s.find(needle)
        print(repr(s[max(0,m-300):m+300])); break
else: print('no title metadata in JS bundles (titles are in per-lesson MD frontmatter)')
