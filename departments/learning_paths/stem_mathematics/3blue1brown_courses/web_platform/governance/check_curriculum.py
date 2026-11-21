import json
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
d=json.load(open(W+'/curriculum_index.json',encoding='utf-8'))
print('total_courses:',d.get('total_courses'),'topic_collections:',d.get('total_topic_collections'))
print('\nCOURSES:')
for c in d.get('courses',[]):
    print('  ',c.get('id'),c.get('title_en','')[:50],'lessons:',len(c.get('lessons',[])) if isinstance(c.get('lessons'),list) else c.get('lesson_count'))
print('\nTOPIC COLLECTIONS:')
for t in d.get('topic_collections',[]):
    print('  ',t.get('id'),t.get('title_en','')[:60],'items:',len(t.get('items',t.get('lessons',[]))) if isinstance(t.get('items',t.get('lessons',[])),list) else '?')
