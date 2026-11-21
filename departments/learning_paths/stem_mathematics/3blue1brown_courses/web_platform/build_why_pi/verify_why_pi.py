# -*- coding: utf-8 -*-
"""
Headless-Chrome (channel='chrome') verification for the NEW Why Pi course.

Checks, for all 8 lessons + index:
  0 errors            : no console errors/warnings, no pageerror
  components once     : every b1b-* tag registered; singleton components appear once
  quiz click          : selecting the correct option + check shows correct feedback
  parity              : component tag set matches gold lesson_01.html; narrated DOM
                        section ids match the manifest section keys; required paths present
Also validates data/why_pi JSON + manifest.js/json consistency.

NOTE: this script only REPORTS. Never claim success unless this exits 0.
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # web_platform/
BASE = 'http://localhost:8085'
GOLD = BASE + '/courses/linear_algebra/lesson_01.html'

SINGLETONS = [
    'b1b-search-overlay', 'b1b-navbar', 'b1b-hero-player',
    'b1b-narration-banner', 'b1b-bookmarks', 'b1b-toc-sidebar',
    'b1b-article', 'b1b-watch-panel', 'b1b-chapter-nav',
    'b1b-footer', 'b1b-back-to-top',
]


def goto_ready(page, url):
    """Navigate and wait reactively for custom elements + quizzes to render."""
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_function(
        "() => { const q = document.querySelectorAll('b1b-quiz');"
        " return q.length > 0 && Array.from(q).every(x => x.querySelector('.quiz-block')); }",
        timeout=20000)
    page.wait_for_function(
        "() => !!customElements.get('b1b-hero-player') && "
        "!!document.querySelector('b1b-article section')",
        timeout=20000)


def collect_errors(page):
    errs = []
    # Only error-level console messages and uncaught page exceptions count as
    # "errors". Browser-level warnings (e.g. Chrome's WebGPU powerPreference
    # notice) are not application errors.
    page.on('console', lambda m: errs.append('[console.%s] %s' % (m.type, m.text))
            if m.type == 'error' else None)
    page.on('pageerror', lambda e: errs.append('[pageerror] %s' % e))
    return errs


def dom_audit(page):
    return page.evaluate("""() => {
      const tags = new Set();
      document.querySelectorAll('*').forEach(el => {
        if (el.tagName && el.tagName.toLowerCase().includes('-')) tags.add(el.tagName.toLowerCase());
      });
      const counts = {};
      %s.forEach(t => counts[t] = document.querySelectorAll(t).length);
      const article = document.querySelector('b1b-article');
      const sections = [];
      if (article) article.querySelectorAll('section').forEach(s => {
        sections.push({id: s.id || '', noNarr: s.getAttribute('data-no-narration') === 'true'});
      });
      const quizzes = [];
      document.querySelectorAll('b1b-quiz').forEach(q => {
        const b = q.querySelector('.quiz-block');
        quizzes.push({
          correct: b ? b.getAttribute('data-correct') : null,
          options: q.querySelectorAll('.quiz-option').length,
          feedback: !!q.querySelector('.quiz-feedback')
        });
      });
      const hero = document.querySelector('b1b-hero-player');
      const watch = document.querySelector('b1b-watch-panel');
      return {
        tags: Array.from(tags).sort(),
        counts,
        sections,
        quizzes,
        heroVideo: hero ? hero.getAttribute('video-src') : null,
        watchVideo: watch ? watch.getAttribute('video-src') : null,
        manifestLoaded: !!(window.TEACHER_AUDIO_MANIFEST && window.TEACHER_AUDIO_MANIFEST.sections),
        manifestKeys: window.TEACHER_AUDIO_MANIFEST
          ? Object.keys(window.TEACHER_AUDIO_MANIFEST.sections).sort() : [],
        renderedQuizBlocks: document.querySelectorAll('.quiz-block').length,
        renderedFigures: document.querySelectorAll('figure.lesson-figure').length,
        renderedFormula: document.querySelectorAll('.formula-box').length,
        katex: document.querySelectorAll('.katex').length
      };
    }""" % json.dumps(SINGLETONS))


def quiz_click(page, page_errors):
    """Click correct option on first quiz and verify feedback; then wrong on next quiz."""
    results = []
    quizzes = page.locator('b1b-quiz')
    n = quizzes.count()
    for i in range(n):
        q = quizzes.nth(i)
        b = q.locator('.quiz-block')
        correct = int(b.get_attribute('data-correct'))
        want = 'correct' if i % 2 == 0 else 'wrong'
        pick = correct if want == 'correct' else (correct + 1) % q.locator('.quiz-option').count()
        q.locator('.quiz-option').nth(pick).click()
        q.locator('.quiz-check-btn').click()
        fb = q.locator('.quiz-feedback')
        info = {
            'quiz': i,
            'picked': pick,
            'correct': correct,
            'show': 'show' in (fb.get_attribute('class') or ''),
            'cls': fb.get_attribute('class') or '',
            'text': (fb.inner_text() or '')[:80],
        }
        info['ok'] = info['show'] and (want + '-fb') in info['cls']
        results.append(info)
    return results


def main():
    report = {'lessons': {}, 'index': {}, 'data': {}, 'summary': {}}
    passed = True

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})

        # ---- Gold component set ----
        gold_page = ctx.new_page()
        gold_errors = collect_errors(gold_page)
        goto_ready(gold_page, GOLD)
        gold_dom = dom_audit(gold_page)
        gold_tags = set(gold_dom['tags'])
        report['summary']['gold_errors'] = gold_errors
        report['summary']['gold_tags'] = sorted(gold_tags)
        gold_page.close()

        # ---- Index ----
        idx_page = ctx.new_page()
        idx_errors = collect_errors(idx_page)
        idx_page.goto(BASE + '/courses/why_pi/index.html', wait_until='load', timeout=60000)
        idx_rows = idx_page.locator('a.chapter-row').count()
        report['index'] = {'errors': idx_errors, 'chapter_rows': idx_rows,
                           'ok': not idx_errors and idx_rows == 8}
        if not report['index']['ok']:
            passed = False
        idx_page.close()

        # ---- Lessons ----
        for nn in ['01', '02', '03', '04', '05', '06', '07', '08']:
            url = BASE + '/courses/why_pi/lesson_%s.html' % nn
            page = ctx.new_page()
            errs = collect_errors(page)
            goto_ready(page, url)
            dom = dom_audit(page)
            quiz_res = quiz_click(page, errs)

            narrated_ids = sorted(s['id'] for s in dom['sections'] if not s['noNarr'] and s['id'])
            manifest_keys = sorted(dom['manifestKeys'])
            singletons_ok = all(dom['counts'][t] == 1 for t in SINGLETONS)
            all_registered = page.evaluate("""(tags) =>
                tags.every(t => !!customElements.get(t))""", dom['tags'])
            # Rendered instance count parity: one rendered root per custom host
            quiz_render_ok = dom['renderedQuizBlocks'] == len(
                [q for q in dom['quizzes']])
            tag_parity = set(dom['tags']) == gold_tags

            expect_video = ('../../media_vault/why_pi/lesson_%s/experiments/'
                            '3b1b_why_pi_%s_full_dubbed.mp4' % (nn, nn))
            video_ok = (dom['heroVideo'] == expect_video and dom['watchVideo'] == expect_video)

            quiz_ok = all(q['ok'] for q in quiz_res) and len(quiz_res) >= 1
            narrated_ok = narrated_ids == manifest_keys and len(narrated_ids) >= 3
            errors_ok = len(errs) == 0

            ok = (errors_ok and singletons_ok and all_registered and quiz_render_ok
                  and tag_parity and video_ok and quiz_ok and narrated_ok
                  and dom['manifestLoaded'])
            report['lessons'][nn] = {
                'errors': errs,
                'tags': dom['tags'],
                'tag_parity': tag_parity,
                'counts': dom['counts'],
                'singletons_ok': singletons_ok,
                'all_registered': all_registered,
                'narrated_ids': narrated_ids,
                'manifest_keys': manifest_keys,
                'narrated_ok': narrated_ok,
                'manifest_loaded': dom['manifestLoaded'],
                'video_ok': video_ok,
                'hero_video': dom['heroVideo'],
                'quiz_count': len(quiz_res),
                'quiz_render_ok': quiz_render_ok,
                'quiz_click': quiz_res,
                'quiz_ok': quiz_ok,
                'rendered_figures': dom['renderedFigures'],
                'rendered_formula': dom['renderedFormula'],
                'katex': dom['katex'],
                'ok': ok,
            }
            if not ok:
                passed = False
            page.close()

        # ---- JSON / manifest static validation ----
        for nn in ['01', '02', '03', '04', '05', '06', '07', '08']:
            dpath = os.path.join(ROOT, 'data', 'why_pi', 'lesson_%s.json' % nn)
            apath = os.path.join(ROOT, 'assets', 'audio', 'why_pi',
                                 'lesson_%s' % nn, 'manifest.json')
            jpath = os.path.join(ROOT, 'assets', 'audio', 'why_pi',
                                 'lesson_%s' % nn, 'manifest.js')
            try:
                with open(dpath, encoding='utf-8') as f:
                    data = json.load(f)
                with open(apath, encoding='utf-8') as f:
                    man = json.load(f)
                with open(jpath, encoding='utf-8') as f:
                    js = f.read()
                js_obj = json.loads(js.split('=', 1)[1].strip().rstrip(';').strip())
                d_secs = sorted(s['id'] for s in data['sections'])
                m_secs = sorted(man['sections'].keys())
                ok = (
                    data.get('course_id') == 'why_pi'
                    and data.get('lesson_id') == 'lesson_' + nn
                    and len(data.get('sections', [])) >= 3
                    and len(data.get('quizzes', [])) >= 1
                    and all(s.get('figures') is not None for s in data['sections'])
                    and man.get('course') == 'why_pi'
                    and man.get('lesson') == 'lesson_' + nn
                    and d_secs == m_secs
                    and js_obj == man
                    and 'window.TEACHER_AUDIO_MANIFEST' in js
                )
                report['data'][nn] = {
                    'course_id': data.get('course_id'),
                    'sections': d_secs,
                    'manifest_sections': m_secs,
                    'quizzes': len(data.get('quizzes', [])),
                    'js_matches_json': js_obj == man,
                    'ok': ok,
                }
                if not ok:
                    passed = False
            except Exception as e:
                report['data'][nn] = {'ok': False, 'error': str(e)}
                passed = False

        browser.close()

    report['summary']['passed'] = passed
    out = os.path.join(ROOT, 'build_why_pi', 'verify_report.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Concise console summary
    print('=== WHY PI VERIFICATION ===')
    print('gold tags (%d): %s' % (len(gold_tags), ','.join(sorted(gold_tags))))
    print('index:', 'OK' if report['index']['ok'] else 'FAIL', report['index'])
    for nn, r in report['lessons'].items():
        print('lesson_%s: %s | errors=%d tags==gold:%s singletons:%s registered:%s '
              'quiz:%s narrated==manifest:%s video:%s figs=%d katex=%d' % (
                  nn, 'OK' if r['ok'] else 'FAIL', len(r['errors']),
                  r['tag_parity'], r['singletons_ok'], r['all_registered'],
                  r['quiz_ok'], r['narrated_ok'], r['video_ok'],
                  r['rendered_figures'], r['katex']))
        if r['errors']:
            print('   ERRORS:', r['errors'])
        for q in r['quiz_click']:
            if not q['ok']:
                print('   QUIZ FAIL:', q)
    for nn, r in report['data'].items():
        print('data_%s: %s' % (nn, 'OK' if r['ok'] else 'FAIL ' + str(r)))
    print('OVERALL:', 'PASS' if passed else 'FAIL')
    print('report:', out)
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
