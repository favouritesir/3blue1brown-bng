import subprocess, re, os
ROOT=r'D:\0PEN CODE\Dub Studio'
out=subprocess.run(['git','-C',ROOT,'ls-files'],capture_output=True,text=True).stdout.splitlines()
pats=[('GCP_AQ',re.compile(r'AQ\.Ab8RN6[A-Za-z0-9_-]{20,}')),
      ('GH_PAT',re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}')),
      ('GOOGLE_AIZA',re.compile(r'AIza[0-9A-Za-z_-]{30,}')),
      ('OPENAI_SK',re.compile(r'sk-[A-Za-z0-9]{30,}'))]
found=[]
for f in out:
    p=os.path.join(ROOT,f)
    if not os.path.isfile(p): continue
    try: s=open(p,encoding='utf-8',errors='ignore').read()
    except: continue
    for name,pat in pats:
        for m in pat.finditer(s):
            found.append((f,name,s[max(0,m.start()-30):m.start()+50].replace('\n',' ')))
for x in found[:40]: print(x)
print('total findings:',len(found))
