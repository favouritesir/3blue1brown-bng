import urllib.request,re
s=urllib.request.urlopen('https://www.3blue1brown.com/assets/root-D4Pcswfl.js',timeout=20).read().decode('utf-8','ignore')
for m in re.finditer(re.escape('/api'),s):
    print(repr(s[max(0,m.start()-200):m.start()+250]))
