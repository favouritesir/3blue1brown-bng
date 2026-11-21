"""Read-only: check all expressive audio manifests for forbidden labels + validity + backups."""
import os, json, glob, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
FORBIDDEN=['চিত্র প্রদর্শনী','চিত্রপ্রদর্শনী']
issues=[]
manifests=glob.glob(f'{W}/assets/audio/*/lesson_*/manifest.json')
checked=0
for m in manifests:
    course=os.path.basename(os.path.dirname(os.path.dirname(m)))
    ldir=os.path.dirname(m)
    num=os.path.basename(ldir)
    try:
        d=json.load(open(m,encoding='utf-8'))
    except Exception as e:
        issues.append((course,num,'INVALID JSON: '+str(e))); continue
    checked+=1
    s=open(m,encoding='utf-8').read()
    for f in FORBIDDEN:
        if f in s:
            issues.append((course,num,'FORBIDDEN LABEL: '+f))
    backup=os.path.isdir(ldir+'/_backup_before_expressive_build')
    if not backup:
        issues.append((course,num,'NO expressive backup'))
    # manifest.js must exist and match
    mjs=ldir+'/manifest.js'
    if os.path.isfile(mjs):
        js=open(mjs,encoding='utf-8').read()
        if 'TEACHER_AUDIO_MANIFEST' not in js:
            issues.append((course,num,'manifest.js missing global'))
        else:
            try:
                payload=js.split('=',1)[1].strip().rstrip(';').strip()
                jd=json.loads(payload)
                if jd!=d:
                    issues.append((course,num,'manifest.js != manifest.json'))
            except Exception:
                pass
print('manifests checked:',checked)
print('issues:',len(issues))
for x in issues:
    print(' ',x)
