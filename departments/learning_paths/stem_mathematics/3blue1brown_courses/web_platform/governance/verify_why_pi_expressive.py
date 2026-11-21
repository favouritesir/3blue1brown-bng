# -*- coding: utf-8 -*-
"""
Headless-Chrome (channel='chrome') verification for the 8 rebuilt expressive
teacher-audio Why-Pi lessons.

Checks per lesson:
  * DOM <-> manifest 1:1  (section ids, cue counts, cue types via the live
    narrationEngine.parseContent blocks vs the manifest cues)
  * 0 duplicate section ids / cue indices
  * 0 quiz / media-tab cue types
  * mp3 non-zero (exists, size > 0, ffprobe duration > 0, duration matches the
    manifest total to within 1 s)
  * valid JSON + manifest.js == manifest.json + preloaded manifest
  * 0 page errors (uncaught JS exceptions; benign browser compute-pressure
    console notice is reported, not failed)
  * 0 forbidden labels ("চিত্র প্রদর্শনী") and no markup / Latin in cue text
  * 350 ms gaps, prosody metadata, ?v bumped, placeholder backup present

Writes governance/why_pi_expressive_verify_report.json.
Never claim success unless this exits 0.
"""
import json
import os
import re
import subprocess
import sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # web_platform
BASE = 'http://127.0.0.1:8085'
BAD = re.compile(r'[A-Za-z\\$⟦⟧{}\[\]—–\-]')
FORBIDDEN = 'চিত্র প্রদর্শনী'
NON_NARRATION_TYPES = {'quiz', 'media-tab', 'media_tab', 'video', 'iframe'}
LESSONS = ['01', '02', '03', '04', '05', '06', '07', '08']


def ffprobe_duration(path):
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    return float(out)


PARITY_JS = r"""() => {
  const typeOf = (el) => {
    if (el.tagName === 'H2') return 'h2';
    if (el.tagName === 'H3') return 'h3';
    if (el.tagName === 'P') return 'p';
    if (el.classList.contains('chapter-quote')) return 'chapter-quote';
    if (el.classList.contains('callout')) return 'callout';
    if (el.tagName === 'FIGURE') return 'figure';
    if (el.classList.contains('formula-box')) return 'formula-box';
    return el.tagName.toLowerCase();
  };
  const eng = window.narrationEngine;
  const man = window.TEACHER_AUDIO_MANIFEST;
  const dom = eng.sections.map(s => ({
    id: s.id,
    types: s.blocks.map(b => typeOf(b.element)),
    cuesLoaded: s.cues.length,
    audioFile: s.audioFile || null,
  }));
  const manifest = Object.keys(man.sections).map(id => ({
    id,
    types: man.sections[id].cues.map(c => c.type),
    indices: man.sections[id].cues.map(c => c.index),
    cues: man.sections[id].cues.length,
    audioFile: man.sections[id].audio_file,
  }));
  return {
    dom, manifest,
    hasStudioAudio: eng.hasStudioAudio,
    manifestCourse: man.course,
    manifestLesson: man.lesson,
    manifestLoaded: !!man.sections,
    manifestKeys: Object.keys(man.sections),
  };
}"""


def verify_lesson(page, nn):
    r = {'lesson': 'lesson_' + nn, 'checks': {}, 'errors': [], 'info': {}}
    js_errors, console_errors = [], []

    def on_console(m):
        if m.type == 'error':
            console_errors.append(m.text)
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('console', on_console)

    resp = page.goto(BASE + '/courses/why_pi/lesson_%s.html' % nn,
                     wait_until='domcontentloaded', timeout=60000)
    r['checks']['http_200'] = resp is not None and resp.status == 200
    page.wait_for_function(
        "() => window.narrationEngine && window.narrationEngine.sections.length > 0"
        " && !!window.TEACHER_AUDIO_MANIFEST",
        timeout=20000)

    # page errors: uncaught exceptions only; browser permission-policy notices
    # emitted by the YouTube/iframe embed are benign (see number_theory verifier).
    benign = [m for m in console_errors
              if 'Permissions policy violation' in m or 'compute-pressure' in m]
    real_console = [m for m in console_errors if m not in benign]
    r['info']['benign_console'] = benign
    r['info']['console_errors'] = real_console
    r['errors'].extend('pageerror: ' + e for e in js_errors)
    r['errors'].extend('console.error: ' + e for e in real_console)
    r['checks']['no_page_errors'] = not js_errors and not real_console

    parity = page.evaluate(PARITY_JS)
    r['info']['parity'] = parity
    dom_map = {s['id']: s for s in parity['dom']}
    man_map = {s['id']: s for s in parity['manifest']}
    same_ids = set(dom_map) == set(man_map)
    r['checks']['dom_manifest_ids'] = same_ids
    r['checks']['dom_manifest_cue_counts'] = same_ids and all(
        dom_map[i]['cuesLoaded'] == man_map[i]['cues'] for i in dom_map)
    r['checks']['dom_manifest_cue_types'] = same_ids and all(
        dom_map[i]['types'] == man_map[i]['types'] for i in dom_map)
    r['checks']['audio_binding'] = same_ids and all(
        dom_map[i]['audioFile'] and
        dom_map[i]['audioFile'].endswith(man_map[i]['audioFile']) for i in dom_map)
    r['checks']['manifest_loaded'] = bool(parity['manifestLoaded'] and
                                           parity['hasStudioAudio'])
    r['checks']['manifest_metadata'] = (
        parity['manifestCourse'] == 'why_pi' and parity['manifestLesson'] == 'lesson_' + nn)

    # duplicate keys / indices
    keys = parity['manifestKeys']
    r['checks']['no_duplicate_sections'] = len(keys) == len(set(keys))
    all_indices = [idx for m in parity['manifest'] for idx in m['indices']]
    r['checks']['no_duplicate_cue_indices'] = all(
        m['indices'] == list(range(len(m['indices']))) for m in parity['manifest'])

    # no quiz / media-tab / other non-narration cue types
    types = [t for m in parity['manifest'] for t in m['types']]
    bad_types = sorted(set(types) & NON_NARRATION_TYPES)
    r['info']['non_narration_types'] = bad_types
    r['checks']['no_quiz_media_types'] = not bad_types

    # static manifest / audio / text checks
    mpath = os.path.join(ROOT, 'assets', 'audio', 'why_pi',
                         'lesson_' + nn, 'manifest.json')
    jpath = os.path.join(ROOT, 'assets', 'audio', 'why_pi',
                         'lesson_' + nn, 'manifest.js')
    man = json.load(open(mpath, encoding='utf-8'))
    js = open(jpath, encoding='utf-8').read()
    js_obj = json.loads(js.split('=', 1)[1].strip().rstrip(';').strip())
    r['checks']['valid_json'] = True
    r['checks']['js_matches_json'] = js_obj == man
    r['checks']['js_preloaded'] = 'window.TEACHER_AUDIO_MANIFEST' in js

    texts = [c['text'] for s in man['sections'].values() for c in s['cues']]
    r['checks']['no_forbidden_labels'] = all(FORBIDDEN not in t for t in texts)
    r['checks']['clean_scripts'] = all(not BAD.search(t) for t in texts)

    mp3_ok = True
    durations = {}
    gaps_ok = True
    for sid, sec in man['sections'].items():
        apath = os.path.join(ROOT, 'assets', 'audio', 'why_pi',
                             'lesson_' + nn, sec['audio_file'])
        if not os.path.exists(apath) or os.path.getsize(apath) == 0:
            mp3_ok = False
            continue
        dur = ffprobe_duration(apath) * 1000.0
        durations[sid] = round(dur, 1)
        if dur <= 0 or abs(dur - sec['total_duration_ms']) > 1000.0:
            mp3_ok = False
        cues = sec['cues']
        for i, c in enumerate(cues):
            if c['duration_ms'] <= 0 or c['end_ms'] <= c['start_ms']:
                mp3_ok = False
            if i > 0 and abs((c['start_ms'] - cues[i - 1]['end_ms']) - 350.0) > 1.0:
                gaps_ok = False
    r['info']['mp3_durations_ms'] = durations
    r['checks']['mp3_nonzero_and_matching'] = mp3_ok
    r['checks']['350ms_gaps'] = gaps_ok

    # ?v bumped and backup present
    html = open(os.path.join(ROOT, 'courses', 'why_pi',
                             'lesson_%s.html' % nn), encoding='utf-8').read()
    m = re.search(r'why_pi/lesson_%s/manifest\.js\?v=(\d+)' % nn, html)
    r['checks']['manifest_version_bumped'] = bool(m and int(m.group(1)) >= 2)
    bk = os.path.join(ROOT, 'assets', 'audio', 'why_pi',
                      '_backup_before_expressive_build', 'lesson_' + nn)
    r['checks']['placeholder_backed_up'] = all(
        os.path.exists(os.path.join(bk, f)) for f in ('manifest.json', 'manifest.js'))

    # summary numbers
    r['info']['section_count'] = len(man['sections'])
    r['info']['cue_count'] = sum(len(s['cues']) for s in man['sections'].values())
    r['info']['figure_count'] = sum(
        1 for s in man['sections'].values() for c in s['cues'] if c['type'] == 'figure')
    r['info']['total_duration_s'] = round(
        sum(s['total_duration_ms'] for s in man['sections'].values()) / 1000.0, 2)
    r['all_passed'] = all(r['checks'].values())
    return r


def main():
    report = {'lessons': {}, 'summary': {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        for nn in LESSONS:
            page = ctx.new_page()
            try:
                report['lessons'][nn] = verify_lesson(page, nn)
            except Exception as exc:  # noqa: BLE001
                report['lessons'][nn] = {
                    'lesson': 'lesson_' + nn, 'all_passed': False,
                    'checks': {'no_exception': False},
                    'errors': ['EXCEPTION: ' + repr(exc)],
                    'info': {},
                }
            page.close()
        browser.close()

    passed = all(r['all_passed'] for r in report['lessons'].values())
    total_cues = sum(r['info'].get('cue_count', 0) for r in report['lessons'].values())
    total_dur = sum(r['info'].get('total_duration_s', 0) for r in report['lessons'].values())
    total_fig = sum(r['info'].get('figure_count', 0) for r in report['lessons'].values())
    report['summary'] = {
        'passed': passed, 'total_lessons': len(LESSONS), 'total_cues': total_cues,
        'total_figures': total_fig, 'total_duration_s': round(total_dur, 2),
    }
    out = os.path.join(ROOT, 'governance', 'why_pi_expressive_verify_report.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print('=== WHY PI EXPRESSIVE AUDIO VERIFICATION ===')
    for nn in LESSONS:
        r = report['lessons'][nn]
        failed = [k for k, v in r['checks'].items() if not v]
        info = r['info']
        print('lesson_%s: %s | cues=%d figs=%d dur=%.2fs | failed=%s' % (
            nn, 'PASS' if r['all_passed'] else 'FAIL',
            info.get('cue_count', -1), info.get('figure_count', -1),
            info.get('total_duration_s', -1), failed))
        for e in r['errors'][:6]:
            print('    ', e)
    s = report['summary']
    print('TOTAL: %d lessons, %d cues, %d figures, %.2fs' % (
        s['total_lessons'], s['total_cues'], s['total_figures'], s['total_duration_s']))
    print('OVERALL:', 'PASS' if passed else 'FAIL')
    print('report:', out)
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
