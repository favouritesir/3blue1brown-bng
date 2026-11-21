W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
h=open(W+'/index.html',encoding='utf-8').read()
i=h.find('courses/lockdown_math/index.html')
print(h[max(0,i-700):i+900])
