W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
p=W+'/index.html'; h=open(p,encoding='utf-8').read()
# within lockdown card region only
i=h.find('courses/lockdown_math/index.html'); j=h.find('</article>',i)
reg=h[i:j]
reg=reg.replace('নতুন পাঠ উন্মুক্ত','সম্পূর্ণ ১০/১০')
reg=reg.replace('কোর্স ড্যাশবোর্ড &rarr;','পাঠ ০১–১০ সম্পূর্ণ &rarr;')
h=h[:i]+reg+h[j:]
open(p,'w',encoding='utf-8').write(h)
print('polished lockdown card')
