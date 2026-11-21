import urllib.request, re
u='https://www.3blue1brown.com/assets/api-CgAUf-Xl.js'
s=urllib.request.urlopen(u,timeout=30).read().decode('utf-8','ignore')
print('len',len(s))
# find URL-like strings and fetch calls
for pat in [r'"(/[^"]{3,80})"',r'fetch\(([^)]{0,120})',r'https?://[^"\']+']:
    print('\nPATTERN',pat)
    for m in re.findall(pat,s)[:30]: print(' ',m[:150])
