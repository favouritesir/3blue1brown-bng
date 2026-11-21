import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
h=open(W+'/index.html',encoding='utf-8').read()
for sec in ['core-series','topic-collections','tracks']:
    m=re.search(r'id="'+sec+r'"(.*?)(?=<section|</main>|$)',h,re.S)
    if m:
        chunk=m.group(1)
        print(f'=== {sec} ({len(chunk)} chars) ===')
        print(chunk[:1500])
        print('...\n')
c=open(W+'/courses/linear_algebra/index.html',encoding='utf-8').read()
print('=== LA index first 3000 ===')
print(c[:3000])
