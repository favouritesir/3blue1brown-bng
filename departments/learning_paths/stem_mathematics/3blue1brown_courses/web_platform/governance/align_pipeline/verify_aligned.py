import sys, re, subprocess
P=sys.argv[1]
r=subprocess.run(['ffmpeg','-v','info','-i',P,'-vn','-af','silencedetect=noise=-45dB:d=1','-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout.decode('utf-8','ignore')
ev=[]
for l in r.splitlines():
    m=re.search(r'silence_start: ([\d.]+)',l)
    if m: ev.append({'s':float(m.group(1))})
    m=re.search(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',l)
    if m and ev: ev[-1]['d']=float(m.group(2))
big=[e for e in ev if e.get('d',0)>5 and e['s']>2]
print(P.split('/')[-1],'internal>5s:',len(big),'max:',max((e['d'] for e in ev if e['s']>2),default=0))
for e in big[:5]: print(' ',e)
