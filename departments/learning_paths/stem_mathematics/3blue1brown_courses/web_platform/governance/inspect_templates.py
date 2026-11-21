import re
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
s=open(W+'/courses/linear_algebra/index.html',encoding='utf-8').read()
i=s.find('<div class="chapter-grid">')
j=s.find('</main>',i)
print('chapter-grid start',i,'main end',j)
print('--- tail of chapter grid (last 1200) ---')
print(s[j-1200:j])
print('\n--- after main (footer area) ---')
print(s[j:j+600])

h=open(W+'/index.html',encoding='utf-8').read()
for m in re.finditer(r'data-href="(courses/[^"]+index\.html)"',h):
    print('homepage card link:',m.group(1))
print('\nhomepage stale phrases:')
for phrase in ['01-05','5 / 15','আসছে','লেসন 01-05','পাঠ ১–৫']:
    print(f'  "{phrase}":',h.count(phrase))
