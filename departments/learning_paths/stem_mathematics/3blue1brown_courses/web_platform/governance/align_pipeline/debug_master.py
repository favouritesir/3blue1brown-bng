import json
p='departments/learning_paths/stem_mathematics/3blue1brown_courses/essence_of_calculus/lesson_04_chain_rule/dubbing_pipeline/3b1b_calculus_l04_bangla_master_script.json'
d=json.load(open(p,encoding='utf-8'))
c=d if isinstance(d,list) else d.get('cues',[])
print('cues',len(c))
for i,x in enumerate(c):
    if i>=30 or i<3:
        print(i,'start',x.get('start'),'end',x.get('end'),'dur',x.get('duration'),'bn',str(x.get('bn',''))[:45])
