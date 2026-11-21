import urllib.request,re
s=urllib.request.urlopen('https://www.3blue1brown.com/assets/Header-qk6vXxWo.js',timeout=30).read().decode('utf-8','ignore')
i=s.find('"why-pi":{title:')
print(s[i-2500:i+5000])
