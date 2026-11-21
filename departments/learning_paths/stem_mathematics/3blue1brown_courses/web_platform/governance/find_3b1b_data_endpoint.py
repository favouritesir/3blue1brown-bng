import urllib.request, re
h=urllib.request.urlopen('https://www.3blue1brown.com/',timeout=30).read().decode('utf-8','ignore')
print('len',len(h))
for m in re.findall(r'(?:src|href)="([^"]+\.(?:js|json))"',h)[:30]: print(' ',m)
for kw in ['lessons.json','api/','data.json','__NEXT_DATA__','application/json','index-']:
    print(kw, h.count(kw))
