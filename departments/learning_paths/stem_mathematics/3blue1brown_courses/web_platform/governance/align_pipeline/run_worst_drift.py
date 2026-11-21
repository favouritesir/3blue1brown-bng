import glob, json, os, subprocess, re, sys
ROOT='departments/learning_paths/stem_mathematics/3blue1brown_courses'
W=ROOT+'/web_platform'
# worst drift lessons from check_alignment_drift
targets=[('calculus',4),('probability',2),('calculus',3),('linear_algebra',2)]
for course,n in targets:
    masters=glob.glob(f'{ROOT}/**/lesson_{n:02d}*/dubbing_pipeline/*master*.json',recursive=True)
    # course-aware: LA videos live in media_vault/lesson_NN; other courses in media_vault/<course>/lesson_NN
    if course=='linear_algebra':
        origs=glob.glob(f'{W}/media_vault/lesson_{n:02d}/original_source/full_original.mp4',recursive=True)
    else:
        origs=glob.glob(f'{W}/media_vault/{course}/lesson_{n:02d}/original_source/full_original.mp4',recursive=True)
    if not masters or not origs:
        print('SKIP',course,n,'master',len(masters),'orig',len(origs),flush=True); continue
    # pick master matching course hint in path
    m=next((x for x in masters if course.split('_')[0][:4] in x.lower()),masters[0])
    o=origs[0]
    out=f'{W}/media_vault/{course}/lesson_{n:02d}/experiments/aligned_v2/3b1b_{course}_{n:02d}_aligned.mp4'
    print('BUILD',course,n,m,o,flush=True)
    r=subprocess.run(['python',W+'/governance/align_pipeline/build_aligned_generic.py',m,o,out],capture_output=True,text=True)
    print(r.stdout[-600:],r.stderr[-300:],flush=True)
