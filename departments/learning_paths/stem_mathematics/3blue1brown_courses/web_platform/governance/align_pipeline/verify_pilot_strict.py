import subprocess, re, json
P='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault/lesson_01/experiments/aligned_v2/3b1b_lesson_01_aligned.mp4'
r=subprocess.run(['ffmpeg','-v','info','-i',P,'-vn','-af','silencedetect=noise=-45dB:d=1','-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout.decode('utf-8','ignore')
events=[]
for l in r.splitlines():
    m=re.search(r'silence_start: ([\d.]+)',l)
    if m: events.append({'start':float(m.group(1))})
    m=re.search(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',l)
    if m and events: events[-1]['end']=float(m.group(1)); events[-1]['dur']=float(m.group(2))
internal=[e for e in events if e.get('dur',0)>1.5 and e['start']>2]
big=[e for e in internal if e['dur']>5]
print('silence events >1s:',len(events),'internal>1.5s:',len(internal),'internal>5s:',len(big))
print('max internal:',max((e['dur'] for e in internal),default=0))
for e in big[:10]: print('BIG',e)
