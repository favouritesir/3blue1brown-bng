import os, re

base = 'departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses'

# Pattern to match the entire audio-track-bar div
pattern = re.compile(r'<!--\s*(?:Dual-Track|Standalone|Master).*?-->\s*<div class="audio-track-bar".*?</div>\s*(?=</div>|\n\s*<!--|\n\s*<div class="lesson-body")', re.DOTALL)
alt_pattern = re.compile(r'<div class="audio-track-bar".*?</div>\s*(?=</div>|\n\s*<!--|\n\s*<div class="lesson-body")', re.DOTALL)

for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.html') and f.startswith('lesson_'):
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            
            orig_len = len(content)
            content = pattern.sub('', content)
            content = alt_pattern.sub('', content)
            
            if len(content) != orig_len:
                with open(fp, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                print(f'Removed audio-track-bar from: {fp}')

print('Audio track bars purge complete.')
