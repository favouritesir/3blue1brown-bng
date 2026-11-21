import urllib.request, re
base='https://www.3blue1brown.com'
h=urllib.request.urlopen(base+'/',timeout=20).read().decode('utf-8','ignore')
assets=sorted(set(re.findall(r'([/\w.-]+\.js)',h)))
print('js assets:',len(assets))
for j in assets:
    u=base+(j if j.startswith('/') else '/assets/'+j)
    try: s=urllib.request.urlopen(u,timeout=12).read().decode('utf-8','ignore')
    except: continue
    if 'basel-problem' in s or 'taylor-series' in s:
        print('FOUND',u,'len',len(s))
        m=s.find('basel-problem')
        print(repr(s[max(0,m-400):m+400]))
        break
else:
    print('none found; sample bundle sizes:')
    for j in assets[:5]:
        try: print(' ',j,len(urllib.request.urlopen(base+j,timeout=10).read()))
        except: pass
