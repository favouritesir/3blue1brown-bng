import glob, os, json
root='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/governance'
files=glob.glob(f'{root}/build_expressive_teacher_audio*.py')
changed=[]
for p in files:
    s=open(p,encoding='utf-8').read()
    o=s
    # Natural spoken openings — no label-like prefix
    s=s.replace('"চিত্র প্রদর্শনী। ', '"')
    s=s.replace("'চিত্র প্রদর্শনী। ", "'")
    s=s.replace('"চিত্র প্রদর্শনী: ', '"')
    s=s.replace("'চিত্র প্রদর্শনী: ", "'")
    s=s.replace('"চিত্র প্রদর্শনী।"', '""')
    s=s.replace("'চিত্র প্রদর্শনী।'", "''")
    # Legacy strip guards become harmless no-ops but keep them working
    s=s.replace('body.startswith("চিত্র প্রদর্শনী।")', 'body.startswith("চিত্র প্রদর্শনী।") or body.startswith("চিত্র প্রদর্শনী: ")')
    if s!=o:
        open(p,'w',encoding='utf-8').write(s)
        changed.append(os.path.basename(p))
print('PATCHED:', len(changed))
for c in sorted(changed): print(' ',c)
