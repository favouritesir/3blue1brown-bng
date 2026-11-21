"""
Rebuild Lesson 01 teacher audio from the CURRENT (migrated) DOM.
- Source: governance/l01_dom_blocks.json (extracted from live page, TeX markers intact)
- Backs up existing manifests + mp3s into assets/audio/.../_backup_pre_dom_rebuild/
- Generates clean Bengali spoken text with phonetic safeguards
- 1:1 cue parity (73 cues / 6 sections) preserved exactly
"""
import os
import re
import json
import shutil
import asyncio
import subprocess
import edge_tts

BASE = 'departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
BLOCKS_JSON = f'{BASE}/governance/l01_dom_blocks.json'
AUDIO_DIR = f'{BASE}/assets/audio/linear_algebra/lesson_01'
BACKUP_DIR = f'{AUDIO_DIR}/_backup_pre_dom_rebuild'
VOICE = 'bn-BD-PradeepNeural'
GAP_MS = 350

BN_DIGITS = {'0':'শূন্য','1':'এক','2':'দুই','3':'তিন','4':'চার','5':'পাঁচ','6':'ছয়','7':'সাত','8':'আট','9':'নয়'}

ORDINAL = ['প্রথম','দ্বিতীয়','তৃতীয়','চতুর্থ','পঞ্চম','ষষ্ঠ','সপ্তম','অষ্টম','নবম','দশম']


def num_words(n: str) -> str:
    n = n.strip()
    if n.isdigit() and len(n) <= 3:
        # simple large-number handling for the two values used here
        special = {'600':'ছয়শত','2600':'দুই হাজার ছয়শত','300000':'তিন লক্ষ','12':'বার','9':'নয়'}
        if n in special:
            return special[n]
        return ' '.join(BN_DIGITS[d] for d in n)
    if n == '1.5':
        return 'এক দশমিক পাঁচ'
    return n


def matrix_speech(tex: str) -> str:
    """Convert a bmatrix LaTeX chunk into natural Bengali."""
    tex = tex.replace(r'\vec{v}', 'ভেক্টর ভি').replace(r'\vec{w}', 'ভেক্টর ডব্লিউ')
    tex = tex.replace(r'\hat{i}', 'আই হ্যাট').replace(r'\hat{j}', 'জে হ্যাট')
    tex = tex.replace(r'\hat{k}', 'কে হ্যাট')
    tex = tex.replace(r'\qquad', ', ').replace(r'\cdot', ' গুণ ')
    tex = tex.replace('\\$3{,}00{,}000', 'তিন লক্ষ ডলার')
    tex = tex.replace('2{,}600', 'দুই হাজার ছয়শত')
    tex = tex.replace(r'\text{ ft}^2', ' বর্গফুট').replace(r'\text{ft}^2', ' বর্গফুট')
    tex = tex.replace(r'\text{house}', 'হাউস')
    tex = tex.replace(r'\text{}', '')
    tex = re.sub(r'\\text\{([^}]*)\}', r'\1', tex)
    tex = tex.replace(r'\begin{bmatrix}', '').replace(r'\end{bmatrix}', '')
    tex = tex.replace('\\\\', ' ; ')

    # handle column matrices: "a ; b" => "উপরে a এবং নিচে b"
    parts = [p.strip() for p in tex.split(';')]
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # replace digits with words inside the part
        p2 = re.sub(r'(?<![A-Za-z])\d+(?:[.,]\d+)?(?![A-Za-z])', lambda m: num_words(m.group()), p)
        p2 = p2.replace('x', 'এক্স').replace('y', 'ওয়াই')
        p2 = p2.replace('+', ' যোগ ').replace('-', ' মাইনাস ')
        p2 = re.sub(r'\s+', ' ', p2).strip()
        out.append(p2)
    if len(out) >= 2:
        return 'কলাম ভেক্টর উপরে ' + out[0] + ' এবং নিচে ' + out[1] + '।'
    return ' '.join(out)


def tex_to_speech(tex: str) -> str:
    t = tex.strip()
    # Exact house-price vector (must be handled before any digit/x replacement)
    if r'\text{house}' in t and r'\begin{bmatrix}' in t:
        return ('ভেক্টর ভি হাউস সমান কলাম ভেক্টর উপরে দুই হাজার ছয়শত বর্গফুট, '
                'এবং নিচে দাম তিন লক্ষ ডলার।')
    # whole-expression specials
    if r'\begin{bmatrix}' in t and ('=' in t or '+' in t or r'\vec' in t or r'\hat' in t):
        s = t
        s = s.replace(r'\vec{v}', 'ভেক্টর ভি').replace(r'\vec{w}', 'ভেক্টর ডব্লিউ')
        s = s.replace(r'\hat{i}', 'আই হ্যাট').replace(r'\hat{j}', 'জে হ্যাট')
        s = s.replace(r'\qquad', ', ').replace(r'\cdot', ' গুণ ')
        s = s.replace(r'\begin{bmatrix}', '').replace(r'\end{bmatrix}', '').replace('\\\\', ' ; ')
        s = re.sub(r'(?<![A-Za-z])\d+(?:[.,]\d+)?(?![A-Za-z])', lambda m: num_words(m.group()), s)
        s = s.replace('x', 'এক্স').replace('y', 'ওয়াই')
        s = s.replace('+', ' যোগ ').replace('-', ' মাইনাস ').replace('=', ' সমান ')
        s = s.replace(';', ', ')
        return re.sub(r'\s+', ' ', s).strip() + '।'
    if r'\frac{1}{3}' in t:
        return 'এক তৃতীয়াংশ'
    if t.startswith('-1.5'):
        return 'মাইনাস এক দশমিক পাঁচ'
    if t in ('(0, 0)', '(0,0)'):
        return 'শূন্য কমা শূন্য'
    if t == 'x':
        return 'এক্স'
    if t == 'y':
        return 'ওয়াই'
    if t == 'xy':
        return 'এক্স ওয়াই'
    if re.fullmatch(r'\d+\s*\+\s*\d+', t):
        a, b = re.split(r'\+', t)
        return f'{num_words(a)} যোগ {num_words(b)}'
    if re.fullmatch(r'\d+\s*-\s*\d+', t):
        a, b = re.split('-', t)
        return f'{num_words(a)} বিয়োগ {num_words(b)}'
    if r'\vec{v}' in t:
        return 'ভেক্টর ভি'
    if r'\vec{w}' in t:
        return 'ভেক্টর ডব্লিউ'
    if r'\begin{bmatrix}' in t:
        return matrix_speech(t)
    return t


def replace_tex(text: str) -> str:
    def repl(m):
        return tex_to_speech(m.group(1))
    return re.sub(r'⟦TEX:(.*?)⟧', repl, text, flags=re.S)


def spoken(block: dict, idx: int, sec_i: int) -> str:
    t = block['type']
    raw = replace_tex(block['text'])
    raw = re.sub(r'\n+', ' ', raw)
    raw = raw.replace('—', ', ').replace('–', ', ')
    raw = raw.replace('"', '').replace("'", '').replace('[', '').replace(']', '')
    raw = raw.replace('(', '').replace(')', '')
    raw = re.sub(r'\s+', ' ', raw).strip()
    # Remove any residual LaTeX fragments that slipped through conversion
    raw = re.sub(r'\\[A-Za-z]+', '', raw)
    raw = raw.replace('{', '').replace('}', '').replace('$', '')
    raw = re.sub(r'\s+', ' ', raw).strip()
    raw = raw.strip(' ,;:।')
    if t == 'h2':
        return f'{ORDINAL[sec_i]} পরিচ্ছেদ: {raw}।'
    if t == 'chapter-quote':
        return f'উদ্ধৃতি: {raw}।'
    if t == 'figure':
        return f'চিত্র প্রদর্শনী: {raw}।'
    if t == 'callout':
        return f'বিশেষ নোট: {raw}।'
    if t == 'formula-box':
        return f'গাণিতিক সূত্র: {raw}।'
    return raw + ('।' if not raw.endswith(('।', '?', '!')) else '')


def get_dur(path):
    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                        '-of','default=noprint_wrappers=1:nokey=1', path],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # ffprobe reports seconds; the manifest contract is milliseconds.
    return float(r.stdout.strip()) * 1000.0


async def main():
    with open(BLOCKS_JSON, encoding='utf-8') as f:
        sections = json.load(f)

    # Backup existing assets
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for name in ['manifest.json', 'manifest.js']:
        src = f'{AUDIO_DIR}/{name}'
        if os.path.exists(src):
            shutil.copy2(src, f'{BACKUP_DIR}/{name}')
    for mp3 in os.listdir(AUDIO_DIR):
        if mp3.endswith('.mp3') and not os.path.exists(f'{BACKUP_DIR}/{mp3}'):
            shutil.copy2(f'{AUDIO_DIR}/{mp3}', f'{BACKUP_DIR}/{mp3}')
    print('Backup created at', BACKUP_DIR)

    manifest_sections = {}
    for si, sec in enumerate(sections):
        sid = sec['id']
        tmpdir = f'{AUDIO_DIR}/_tmp_{sid}'
        os.makedirs(tmpdir, exist_ok=True)
        audio_file = f'sec_{si+1:02d}_{sid}.mp3'
        cue_list, chunk_paths, cur = [], [], 0.0

        for bi, block in enumerate(sec['blocks']):
            text = spoken(block, bi, si)
            chunk = f'{tmpdir}/cue_{bi:02d}.mp3'
            ok = False
            for attempt in range(5):
                try:
                    await edge_tts.Communicate(text, VOICE).save(chunk)
                    if os.path.exists(chunk) and os.path.getsize(chunk) > 200 and get_dur(chunk) > 0.2:
                        ok = True
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.4)
            if not ok:
                print(f'  WARN cue {sid}/{bi} failed, using fallback text')
                await edge_tts.Communicate(text[:80] or 'ভেক্টর।', VOICE).save(chunk)
            dur = get_dur(chunk)
            cue_list.append({
                'index': bi, 'type': block['type'], 'text': text,
                'start_ms': round(cur,1), 'end_ms': round(cur+dur,1), 'duration_ms': round(dur,1)
            })
            chunk_paths.append(chunk)
            cur += dur + GAP_MS

        lf = f'{tmpdir}/list.txt'
        with open(lf, 'w', encoding='utf-8') as f:
            for p in chunk_paths:
                # ffmpeg resolves concat entries relative to the list file,
                # so use bare filenames (chunks live in the same temp folder).
                f.write(f"file '{os.path.basename(p)}'\n")
        subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',lf,'-c','copy',
                        f'{AUDIO_DIR}/{audio_file}'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        manifest_sections[sid] = {
            'title': sec['title'], 'audio_file': audio_file,
            'total_duration_ms': round(cur,1), 'cues': cue_list
        }
        print(f'  {sid}: {len(cue_list)} cues, {cur/1000:.1f}s')

        for p in chunk_paths:
            try: os.remove(p)
            except OSError: pass
        try: os.remove(lf)
        except OSError: pass
        try: os.rmdir(tmpdir)
        except OSError: pass

    manifest = {
        'course': 'linear_algebra', 'lesson': 'lesson_01', 'voice': VOICE,
        'mode': 'authentic_teacher', 'sections': manifest_sections
    }
    with open(f'{AUDIO_DIR}/manifest.json','w',encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    with open(f'{AUDIO_DIR}/manifest.js','w',encoding='utf-8') as f:
        f.write('window.TEACHER_AUDIO_MANIFEST = ' + json.dumps(manifest, ensure_ascii=False, indent=2) + ';\n')
    print('\nDONE — new DOM-matched teacher audio + manifest written.')


if __name__ == '__main__':
    asyncio.run(main())
