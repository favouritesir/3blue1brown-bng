import json, os, re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
topics=json.load(open(W+'/governance/topic_lesson_map.json',encoding='utf-8'))
DIRMAP={'number-theory':'number_theory','why-pi':'why_pi','group-theory':'group_theory','computer-science':'computer_science','guest-videos':'guest_videos','videos-elsewhere':'videos_elsewhere','differential-equations':'differential_equations','neural-networks':'neural_networks','linear-algebra':'linear_algebra','lockdown-math':'lockdown_math'}
updated=0
for key,v in topics.items():
    d=DIRMAP.get(key,key.replace('-','_'))
    p=f'{W}/courses/topics/{key}.html'
    if not os.path.isfile(p): continue
    s=open(p,encoding='utf-8').read()
    # normalize previously-generated wrong ../courses/<x>/... links
    s=re.sub(r'\.\./courses/([^/]+)/lesson_(\d+)\.html',r'../\1/lesson_\2.html',s)
    out=s
    for i,slug in enumerate(v['lessons'],1):
        local=f'courses/{d}/lesson_{i:02d}.html'
        if not os.path.isfile(f'{W}/{local}'): continue
        rel_local='../'+d+'/lesson_'+f'{i:02d}'+'.html'  # from courses/topics/ → courses/<course>/lesson_NN.html
        ext=f'https://www.3blue1brown.com/lessons/{slug}'
        old=f'href="{ext}" target="_blank" rel="noopener"'
        new=f'href="{rel_local}"'
        if old in out:
            out=out.replace(old,new,1)
            # add secondary external marker in the small line
            out=out.replace(f'<small>অফিশিয়াল ৩ব্লু১ব্রাউন পাঠ →</small>',f'<small><a href="{ext}" target="_blank" rel="noopener">অফিশিয়াল ৩ব্লু১ব্রাউন পাঠ ↗</a></small>',1)
            updated+=1
    if out!=s: open(p,'w',encoding='utf-8').write(out)
print('topic pages updated with local lesson links:',updated)
