"""Read-only full project status scan. No writes."""
import os, json, glob, re

W = 'departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
completed = json.load(open(f'{W}/governance/completed_lessons.json', encoding='utf-8'))
ids = completed.get('completed_lessons', completed) if isinstance(completed, dict) else completed
if isinstance(ids, dict):
    ids = ids.get('completed', [])
print('=== COMPLETED LEAKEN LOSS ===')
print('total', len(ids))
for x in ids:
    print('  ', x)

print('\n=== DATA LESSONS PER COURSE ===')
data_root = f'{W}/data'
for course in sorted(os.listdir(data_root)):
    cdir = f'{data_root}/{course}'
    if not os.path.isdir(cdir):
        continue
    lessons = sorted(glob.glob(f'{cdir}/lesson_*.json'))
    nums = sorted(int(re.search(r'lesson_(\d+)', os.path.basename(p)).group(1)) for p in lessons)
    print(f'{course}: {len(nums)} lessons [{nums[0] if nums else "-" }..{nums[-1] if nums else "-"}]')

print('\n=== COMPONENT PAGES (has <b1b- custom elements) ===')
for course in sorted(os.listdir(f'{W}/courses')):
    cdir = f'{W}/courses/{course}'
    if not os.path.isdir(cdir):
        continue
    pages = sorted(glob.glob(f'{cdir}/lesson_*.html'))
    comp = []
    static = []
    for p in pages:
        s = open(p, encoding='utf-8', errors='ignore').read()
        (comp if '<b1b-' in s else static).append(int(re.search(r'lesson_(\d+)', os.path.basename(p)).group(1)))
    print(f'{course}: component={sorted(comp)} static_only={sorted(static)}')

print('\n=== DUBBED VIDEOS ===')
vroot = f'{W}/media_vault'
for course in sorted(os.listdir(vroot)):
    cdir = f'{vroot}/{course}'
    if not os.path.isdir(cdir):
        continue
    vids = glob.glob(f'{cdir}/lesson_*/experiments/*full_dubbed.mp4')
    for v in sorted(vids):
        m = re.search(r'lesson_(\d+)', v)
        print(f'  {course} L{m.group(1) if m else "?"}: {os.path.basename(v)} ({os.path.getsize(v)//1048576} MB)')

print('\n=== AUDIO MANIFESTS (teacher narration) ===')
aroot = f'{W}/assets/audio'
for course in sorted(os.listdir(aroot)):
    cdir = f'{aroot}/{course}'
    if not os.path.isdir(cdir):
        continue
    mans = global_mans = sorted(glob.glob(f'{cdir}/lesson_*/manifest.json'))
    info = []
    for m in mans:
        num = re.search(r'lesson_(\d+)', m).group(1)
        exp = os.path.exists(os.path.dirname(m) + '/_backup_before_expressive_build')
        info.append(f'L{num}' + ('*' if exp else ''))
    print(f'  {course}: {" ".join(info)} (* = expressive backup present)')
