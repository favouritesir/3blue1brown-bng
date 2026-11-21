import urllib.request, re
base='https://www.3blue1brown.com/assets/'
idx=urllib.request.urlopen('https://www.3blue1brown.com/',timeout=20).read().decode('utf-8','ignore')
js=re.findall(r'src="(/assets/[^"]+\.js)"',idx)
print('bundles:',len(js))
for j in js:
    try: s=urllib.request.urlopen('https://www.3blue1brown.com'+j,timeout=15).read().decode('utf-8','ignore')
    except: continue
    if 'basel-problem' in s or 'taylor-series' in s:
        print('FOUND in',j,'len',len(s))
        m=s.find('basel-problem')
        print(repr(s[max(0,m-300):m+300]))
        break
