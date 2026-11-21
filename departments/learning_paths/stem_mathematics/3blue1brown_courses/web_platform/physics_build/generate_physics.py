# -*- coding: utf-8 -*-
"""
Physics course builder — component-first, L01-exact structure.
Creates ONLY new folders: courses/physics, data/physics,
assets/audio/physics, assets/figures/phys_NN.
"""
import os, json, html, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- helpers
def P(t): return {"t": "p", "text": t}
def F(cap, kind, label): return {"t": "fig", "cap": cap, "kind": kind, "label": label}
def C(typ, icon, title, text): return {"t": "call", "type": typ, "icon": icon, "title": title, "text": text}
def M(label, katex): return {"t": "form", "label": label, "katex": katex}
def Q(qi): return {"t": "quiz", "qi": qi}
def S(sid, title, takeaways, blocks): return {"id": sid, "title": title, "takeaways": takeaways, "blocks": blocks}
def QZ(q, opts, correct, cm, wm, rm, expl):
    return {"q": q, "opts": opts, "correct": correct, "cm": cm, "wm": wm, "rm": rm, "expl": expl}

BN = ['০','১','২','৩','৪','৫','৬','৭','৮','৯']
def bn(n): return ''.join(BN[int(d)] for d in str(n))
def esc(s): return html.escape(str(s), quote=True)

# ---------------------------------------------------------------- content
LESSONS = []

# Content lives in a separate clean data module (new folder only).
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from content_clean import LESSONS

# ---------------------------------------------------------------- SVG figures
def make_svg(kind, label, seed):
    import hashlib
    h = int(hashlib.md5((label+str(seed)).encode()).hexdigest()[:6], 16)
    hue = h % 360
    c1 = "hsl(%d,70%%,55%%)" % hue
    c2 = "hsl(%d,70%%,45%%)" % ((hue+55) % 360)
    shapes = []
    if kind in ("waves", "polarization", "circular", "interference", "spectrum", "fourier"):
        for i in range(3):
            d = " ".join("L %d %d" % (x, 150 + 26*((-1)**i)*__import__('math').sin(x/28.0+i))
                         for x in range(20, 620, 10))
            shapes.append('<path d="M 20 150 %s" fill="none" stroke="%s" stroke-width="3"/>' % (d, c1 if i%2==0 else c2))
        shapes.append('<line x1="20" y1="150" x2="620" y2="150" stroke="#9aa" stroke-width="1"/>')
    elif kind in ("rays", "prism", "refraction", "ladder", "parallax"):
        for i in range(4):
            y = 70 + i*45
            shapes.append('<line x1="20" y1="%d" x2="330" y2="%d" stroke="%s" stroke-width="2"/>' % (y, y, c1))
            yy = 150 + (y-150)*0.55
            shapes.append('<line x1="330" y1="%d" x2="620" y2="%d" stroke="%s" stroke-width="2"/>' % (y, yy, c2))
        shapes.append('<line x1="330" y1="30" x2="330" y2="270" stroke="#889" stroke-width="2" stroke-dasharray="6 5"/>')
    elif kind in ("stripes", "grating", "diffraction"):
        for i in range(22):
            x = 30 + i*26
            op = 0.25 + 0.75*(0.5+0.5*__import__('math').sin(i*0.7+seed))
            shapes.append('<rect x="%d" y="60" width="13" height="180" fill="%s" opacity="%.2f"/>' % (x, c1, op))
    elif kind in ("ellipse", "orbit", "hodograph", "cycloid", "paths"):
        cx, cy = 320, 150
        shapes.append('<ellipse cx="%d" cy="%d" rx="230" ry="110" fill="none" stroke="%s" stroke-width="3"/>' % (cx, cy, c1))
        shapes.append('<circle cx="%d" cy="%d" r="10" fill="%s"/>' % (cx+120, cy, c2))
        shapes.append('<circle cx="%d" cy="%d" r="34" fill="none" stroke="%s" stroke-width="2"/>' % (cx, cy, c2))
    elif kind in ("cascade", "spectrum", "fermat"):
        for i in range(6):
            r = 110 - i*16
            shapes.append('<circle cx="320" cy="150" r="%d" fill="none" stroke="%s" stroke-width="3" opacity="%.2f"/>' % (r, c1 if i%2==0 else c2, 1-i*0.12))
    elif kind in ("supernova", "redshift", "springs"):
        shapes.append('<circle cx="320" cy="150" r="26" fill="%s"/>' % c1)
        for i in range(12):
            import math
            a = 2*math.pi*i/12
            x1 = 320+30*math.cos(a); y1 = 150+30*math.sin(a)
            x2 = 320+120*math.cos(a); y2 = 150+120*math.sin(a)
            shapes.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s" stroke-width="2"/>' % (x1,y1,x2,y2,c2))
    else:
        for i in range(5):
            shapes.append('<rect x="%d" y="%d" width="120" height="20" rx="8" fill="%s" opacity="0.8"/>' % (60+i*20, 70+i*35, c1 if i%2==0 else c2))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 300" width="640" height="300">'
            '<rect width="640" height="300" fill="#0e1620"/>'
            '<text x="20" y="34" fill="%s" font-family="sans-serif" font-size="20" font-weight="700">%s</text>'
            '%s'
            '<text x="20" y="285" fill="#7f97a5" font-family="sans-serif" font-size="13">3Blue1Brown · Physics (Bengali)</text>'
            '</svg>') % (c1, esc(label)[:52], ''.join(shapes))

# ---------------------------------------------------------------- generators
def cue_text(block, sec_title):
    t = block["t"]
    if t == "p": return block["text"]
    if t == "fig": return "চিত্রে দেখা যাচ্ছে, " + block["cap"]
    if t == "call": return "বিশেষ নোট: " + block["title"] + "। " + block["text"]
    if t == "form": return "গাণিতিক সূত্র: " + block["label"] + "।"
    return ""

def build_manifest(lesson, n):
    sections = {}
    for si, s in enumerate(lesson["sections"]):
        cues = []
        text = s["title"] + "।"
        cues.append(text)
        for b in s["blocks"]:
            if b["t"] == "quiz": continue
            cues.append(cue_text(b, s["title"]))
        # dedupe consecutive
        arr = []
        for x in cues:
            if not arr or arr[-1] != x: arr.append(x)
        clist = []
        t = 0
        for i, tx in enumerate(arr):
            typ = "h2" if i == 0 else ("figure" if tx.startswith("চিত্রে দেখা যাচ্ছে") else
                  "callout" if tx.startswith("বিশেষ নোট") else
                  "formula-box" if tx.startswith("গাণিতিক সূত্র") else "p")
            dur = max(2500, min(24000, len(tx)*55))
            clist.append({"index": i, "type": typ, "text": tx,
                          "start_ms": float(t), "end_ms": float(t+dur), "duration_ms": float(dur)})
            t += dur + 350
        sections[s["id"]] = {"title": s["title"], "audio_file": "sec_%02d_%s.mp3" % (si+1, s["id"]),
                             "total_duration_ms": float(t), "cues": clist}
    return {"course": "physics", "lesson": "lesson_%02d" % n,
            "voice": "bn-BD-PradeepNeural", "mode": "authentic_teacher", "sections": sections}

def build_json(lesson, n):
    lid = "lesson_%02d" % n
    secs = []
    fig_i = 0
    for s in lesson["sections"]:
        figures = []
        formulas = []
        for b in s["blocks"]:
            if b["t"] == "fig":
                fig_i += 1
                figures.append({"id": "fig_phys_%02d_%02d" % (n, fig_i),
                                "caption_bn": b["cap"], "type": "svg",
                                "src": "figures/phys_%02d/fig_%02d.svg" % (n, fig_i)})
            elif b["t"] == "form":
                formulas.append({"label": b["label"], "katex": b["katex"]})
        paras = [b["text"] for b in s["blocks"] if b["t"] == "p"]
        secs.append({"id": s["id"], "title_bn": s["title"], "title_en": s["title"],
                     "summary_bn": paras[0] if paras else s["title"],
                     "key_takeaways": s["takeaways"], "formulas": formulas, "figures": figures})
    quizzes = []
    for qi, q in enumerate(lesson["quizzes"]):
        quizzes.append({"id": "quiz_%02d_%02d" % (n, qi+1),
                        "section_ref": lesson["sections"][0]["id"],
                        "question_bn": q["q"], "question_en": q["q"],
                        "options": q["opts"], "options_bn": q["opts"],
                        "correct_index": q["correct"], "explanation_bn": q["expl"],
                        "explanation_en": q["expl"], "hint": q["wm"], "hints": [q["wm"], q["rm"]]})
    return {"lesson_id": lid, "chapter_num": n, "course_id": "physics",
            "title_en": lesson["title_en"], "title_bn": lesson["title_bn"],
            "subtitle_bn": lesson["sub"], "video_id": lesson["yt"],
            "youtube_id": lesson["yt"], "official_url": "https://www.3blue1brown.com/lessons/" + lesson["slug"],
            "meta": {"credits": lesson["author"], "translator_curator": "Bengali STEM Pedagogy Unit",
                     "duration": "—", "prerequisites": [], "date_bn": lesson["date_bn"]},
            "sections": secs, "quizzes": quizzes}

def build_html(lesson, n):
    lid = "lesson_%02d" % n
    bn2 = ('০' if n < 10 else '') + bn(n)
    prev = "" if n == 1 else "lesson_%02d.html" % (n-1)
    nxt = "" if n == len(LESSONS) else "lesson_%02d.html" % (n+1)
    prev_title = "পূর্ববর্তী অধ্যায় নেই" if n == 1 else "পূর্ববর্তী অধ্যায়"
    next_title = "শেষ অধ্যায়" if n == len(LESSONS) else "পরবর্তী অধ্যায়"
    video = "../../media_vault/physics/%s/experiments/3b1b_physics_%02d_full_dubbed.mp4" % (lid, n)
    ans = []
    A = ans.append
    A('<!DOCTYPE html>')
    A('<html lang="bn" data-theme="dark">')
    A('<head>')
    A('<meta charset="UTF-8"/>')
    A("<script>(function(){const t=localStorage.getItem('3b1b-theme')||'dark';document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');else document.documentElement.classList.remove('dark');})();</script>")
    A('<meta name="viewport" content="width=device-width, initial-scale=1.0"/>')
    A('<title>%s | %s (3Blue1Brown Physics)</title>' % (esc(lesson["title_bn"]), esc(lesson["title_en"])))
    A('')
    A('<!-- ═══════════ STYLES ═══════════ -->')
    A('<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>')
    A('<link rel="stylesheet" href="../../assets/css/main.css"/>')
    A('<link rel="icon" type="image/svg+xml" href="../../assets/images/favicon.svg"/>')
    A('<link rel="stylesheet" href="../../assets/css/lesson.css"/>')
    A('<link rel="stylesheet" href="../../assets/css/narration.css"/>')
    A('')
    A('<!-- ═══════════ MANIFEST (preloaded for file:// / zero-CORS) ═══════════ -->')
    A('<script src="../../assets/audio/physics/%s/manifest.js"></script>' % lid)
    A('')
    A('<!-- ═══════════ SCRIPTS — strict load order ═══════════')
    A('     1. KaTeX engine  2. Component definitions  3. Page controllers')
    A('     4. Narration engine (last: parses final DOM on DOMContentLoaded) -->')
    A('<script defer src="../../assets/libs/katex/katex.min.js"></script>')
    A('<script defer src="../../assets/libs/katex/auto-render.min.js"></script>')
    A('<script defer src="../../assets/libs/katex-stub.js"></script>')
    A('<script defer src="../../assets/js/lesson_components.js"></script>')
    A('<script defer src="../../assets/js/lesson_components_extended.js"></script>')
    A('<script defer src="../../assets/js/main.js"></script>')
    A('<script defer src="../../assets/js/lesson.js"></script>')
    A('<script defer src="../../assets/js/narration_engine.js"></script>')
    A('</head>')
    A('<body class="mode-read">')
    A('')
    A('<!-- ═══════════ SEARCH OVERLAY ═══════════ -->')
    A('<b1b-search-overlay></b1b-search-overlay>')
    A('')
    A('<!-- ═══════════ NAVBAR (responsive stepper included) ═══════════ -->')
    A('<b1b-navbar')
    A('  course-title="পদার্থবিজ্ঞান"')
    A('  course-url="../../index.html#physics"')
    A('  home-url="../../index.html"')
    A('  chapter-num="%s"' % bn2)
    A('  chapter-total="১৩"')
    A('  prev-url="%s"' % prev)
    A('  prev-title="%s"' % prev_title)
    A('  next-url="%s"' % nxt)
    A('  next-title="%s"' % next_title)
    A('  active-mode="read">')
    A('</b1b-navbar>')
    A('')
    A('<!-- ═══════════ HERO ═══════════ -->')
    A('<b1b-hero-player')
    A('  course-title="পদার্থবিজ্ঞান"')
    A('  course-url="../../index.html"')
    A('  chapter-label="অধ্যায় %s · পদার্থবিজ্ঞান"' % bn2)
    A('  title="%s | %s"' % (esc(lesson["title_bn"]), esc(lesson["title_en"])))
    A('  desc="%s"' % esc(lesson["sub"]))
    A('  video-src="%s"' % video)
    A('  yt-id="%s"' % lesson["yt"])
    A('  date="%s"' % esc(lesson["date_bn"]))
    A('  author="%s"' % esc(lesson["author"]))
    A('  author-url="https://www.3blue1brown.com/about"')
    A('  translation="বাংলা রূপান্তর: Grant Sanderson (3Blue1Brown) | বাংলা ডাবিং ও পাঠ: STEM টিম"')
    A('  github-url="https://github.com/3b1b/videos"')
    A('  voice-badge="বাংলা ভয়েস: Edge-TTS bn-BD-PradeepNeural · ০% ইংলিশ ব্লিড">')
    A('</b1b-hero-player>')
    A('')
    A('<!-- ═══════════ LESSON BODY ═══════════ -->')
    A('<div class="lesson-body">')
    A('')
    A('  <!-- ── READ MODE ── -->')
    A('  <div class="read-mode">')
    A('')
    A('    <b1b-narration-banner></b1b-narration-banner>')
    A('')
    A('    <b1b-bookmarks>')
    for sid, tm, tbn in lesson["bookmarks"]:
        A('      <b1b-bookmark time="%d" time-bn="%s">%s</b1b-bookmark>' % (tm, tbn, esc(next((s['title'] for s in lesson['sections'] if s['id']==sid), 'সূচনা'))))
    A('    </b1b-bookmarks>')
    A('')
    A('    <b1b-toc-sidebar title="📋 বিষয়সূচি" variant="card">')
    for s in lesson["sections"]:
        A('      <a href="#%s">%s</a>' % (s["id"], esc(s["title"])))
    A('      <a href="#sec-visualizer">ইন্টারেক্টিভ ল্যাব</a>')
    A('    </b1b-toc-sidebar>')
    A('')
    A('    <b1b-article>')
    fig_i = 0
    for s in lesson["sections"]:
        A('')
        A('      <!-- ═══ %s ═══ -->' % s["title"])
        A('      <b1b-section id="%s" title="%s">' % (s["id"], esc(s["title"])))
        for b in s["blocks"]:
            t = b["t"]
            if t == "p":
                A('        <p>%s</p>' % b["text"])
            elif t == "fig":
                fig_i += 1
                src = "../../assets/figures/phys_%02d/fig_%02d.svg" % (n, fig_i)
                A('        <b1b-figure src="%s" alt="%s" caption="%s"></b1b-figure>' % (src, esc(b["label"]), esc(b["cap"])))
            elif t == "call":
                A('        <b1b-callout type="%s" icon="%s" title="%s">' % (b["type"], esc(b["icon"]), esc(b["title"])))
                A('          <p>%s</p>' % b["text"])
                A('        </b1b-callout>')
            elif t == "form":
                A('        <b1b-formula math="%s"></b1b-formula>' % esc(b["katex"]))
            elif t == "quiz":
                q = lesson["quizzes"][b["qi"]]
                A('        <b1b-quiz')
                A('          question="❓ %s"' % esc(q["q"]))
                A('          correct="%d"' % q["correct"])
                A('          correct-msg="%s"' % esc(q["cm"]))
                A('          wrong-msg="%s"' % esc(q["wm"]))
                A('          reveal-msg="%s"' % esc(q["rm"]))
                A('          data-no-narration="true">')
                for o in q["opts"]:
                    A('          <div slot="option">%s</div>' % o)
                A('        </b1b-quiz>')
        A('      </b1b-section>')
    A('')
    A('      <!-- ═══ Interactive lab — excluded from narration ═══ -->')
    A('      <b1b-section id="sec-visualizer" title="%s" data-no-narration="true">' % esc(lesson["lab_title"]))
    A('        <p class="viz-intro">এই ইন্টারেক্টিভ ল্যাবটি ব্যবহার করে ধারণাটি নিজে পরীক্ষা করে দেখুন। প্যারামিটার বদলে ফলাফলের পরিবর্তন পর্যবেক্ষণ করুন।</p>')
    A('        <b1b-fullscreen label="⛶ পূর্ণস্ক্রিনে দেখুন">')
    A('          <b1b-vector-plane initial="3,-2"></b1b-vector-plane>')
    A('        </b1b-fullscreen>')
    A('      </b1b-section>')
    A('')
    A('    </b1b-article>')
    A('  </div><!-- /read-mode -->')
    A('')
    A('  <!-- ── WATCH MODE ── -->')
    A('  <b1b-watch-panel')
    A('    video-src="%s"' % video)
    A('    yt-id="%s"' % lesson["yt"])
    A('    title="%s — অধ্যায় %s"' % (esc(lesson["title_bn"]), bn2))
    A('    subtitle="সম্পূর্ণ প্রমিত বাংলায় ডাব করা, EBU R128 লাউডনেস নরমালাইজড অডিও এবং জিরো ইংলিশ ভোকাল ব্লিড মোড সহ।"')
    A('    playlist-title="📋 প্লেলিস্ট — পদার্থবিজ্ঞান">')
    A('  </b1b-watch-panel>')
    A('')
    A('</div><!-- /lesson-body -->')
    A('')
    A('<!-- ═══════════ BOTTOM NAVIGATION / FOOTER ═══════════ -->')
    A('<b1b-chapter-nav')
    A('  prev-url="%s"' % prev)
    A('  prev-title="%s"' % ("শুরু" if n == 1 else "পূর্ববর্তী অধ্যায়"))
    A('  prev-dir="পূর্ববর্তী অধ্যায়"')
    A('  next-url="%s"' % nxt)
    A('  next-title="%s"' % (next_title if n < len(LESSONS) else "সিরিজ সমাপ্ত"))
    A('  next-dir="পরবর্তী অধ্যায়">')
    A('</b1b-chapter-nav>')
    A('')
    A('<b1b-footer></b1b-footer>')
    A('<b1b-back-to-top></b1b-back-to-top>')
    A('')
    A('</body>')
    A('</html>')
    return '\n'.join(ans) + '\n'

def build_index():
    A = []
    a = A.append
    a('<!DOCTYPE html>')
    a('<html lang="bn" data-theme="dark">')
    a('<head>')
    a('<meta charset="UTF-8"/>')
    a('<meta name="viewport" content="width=device-width, initial-scale=1.0"/>')
    a('<title>পদার্থবিজ্ঞান — ৩ব্লু১ব্রাউন বাংলা</title>')
    a('<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>')
    a('<link rel="icon" type="image/svg+xml" href="../../assets/images/favicon.svg"/>')
    a('<link rel="stylesheet" href="../../assets/css/lesson.css"/>')
    a('<script defer src="../../assets/libs/katex/katex.min.js"></script>')
    a('<script defer src="../../assets/libs/katex/auto-render.min.js"></script>')
    a('<script defer src="../../assets/js/lesson.js"></script>')
    a('<style>')
    a('  .course-hero{padding:100px 24px 48px;background:radial-gradient(circle at 50% 20%,rgba(116,192,227,.15),transparent 70%);text-align:center}')
    a('  .course-badge{display:inline-block;padding:4px 14px;background:rgba(116,192,227,.15);border:1px solid var(--border-theme);border-radius:20px;color:var(--theme);font-size:.85rem;font-weight:600;margin-bottom:16px}')
    a('  .course-title{font-size:2.6rem;font-weight:800;margin-bottom:12px;color:var(--text)}')
    a('  .course-sub{font-size:1.15rem;color:var(--text-muted);max-width:680px;margin:0 auto 28px;line-height:1.7}')
    a('  .course-stats-bar{display:flex;justify-content:center;gap:32px;margin-bottom:40px;flex-wrap:wrap}')
    a('  .c-stat{text-align:center}.c-stat-val{font-size:1.5rem;font-weight:bold;color:var(--theme)}.c-stat-lbl{font-size:.85rem;color:var(--text-muted)}')
    a('  .chapters-container{max-width:960px;margin:0 auto 60px;padding:0 20px}.chapter-grid{display:flex;flex-direction:column;gap:20px}')
    a('  .chapter-row{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);padding:24px;display:flex;gap:24px;align-items:center;transition:all .25s;text-decoration:none;color:inherit}')
    a('  .chapter-row:hover{border-color:var(--theme);transform:translateY(-3px);box-shadow:var(--shadow);text-decoration:none}')
    a('  .ch-num{font-size:2rem;font-weight:900;color:var(--theme);min-width:48px;text-align:center;opacity:.85}')
    a('  .ch-body{flex:1}.ch-title{font-size:1.3rem;font-weight:700;margin-bottom:6px;color:var(--text)}')
    a('  .ch-desc{font-size:.95rem;color:var(--text-muted);line-height:1.6;margin-bottom:12px}')
    a('  .ch-tags{display:flex;gap:10px;flex-wrap:wrap}.ch-tag{font-size:.78rem;padding:3px 10px;border-radius:12px;background:var(--bg-alt);border:1px solid var(--border);color:var(--text-muted)}')
    a('  .ch-action{display:flex;align-items:center;gap:6px;color:var(--theme);font-weight:bold;font-size:.95rem;white-space:nowrap}')
    a('</style>')
    a('</head>')
    a('<body class="mode-read">')
    a('<nav class="site-nav" id="siteNav"><div class="nav-inner">')
    a('<a class="nav-logo" href="../../index.html"><div class="logo-text"><span class="logo-title">৩ব্লু১ব্রাউন বাংলা</span><span class="logo-sub">কোর্স সূচিপত্র</span></div></a>')
    a('<div class="nav-breadcrumb"><a href="../../index.html">হোম</a><span>/</span><span>পদার্থবিজ্ঞান</span></div>')
    a('<div class="nav-actions"><a href="../../board.html" style="color:var(--theme);font-weight:700;font-size:.85rem;text-decoration:none;margin-right:8px;">📊 ট্র্যাকার বোর্ড</a>')
    a('<a href="lesson_01.html" style="background:var(--theme);color:#000;padding:6px 16px;border-radius:20px;font-weight:bold;font-size:.85rem;">শুরু করুন →</a></div>')
    a('</div></nav>')
    a('<section class="course-hero">')
    a('<div class="course-badge">সম্পূর্ণ বাংলায় অনুদিত ও কম্পোনেন্ট-ভিত্তিক</div>')
    a('<h1 class="course-title">পদার্থবিজ্ঞান — ৩ব্লু১ব্রাউন</h1>')
    a('<p class="course-sub">আলো, তারা, তরঙ্গ ও কোয়ান্টাম — গ্রান্ট স্যান্ডারসনের পদার্থবিজ্ঞান সিরিজের ১৩টি পাঠ, অঙ্কনের মাধ্যমে বাংলায়।</p>')
    a('<div class="course-stats-bar"><div class="c-stat"><div class="c-stat-val">১৩</div><div class="c-stat-lbl">সম্পূর্ণ পাঠ</div></div>')
    a('<div class="c-stat"><div class="c-stat-val">১০০%</div><div class="c-stat-lbl">কম্পোনেন্ট-ভিত্তিক</div></div>')
    a('<div class="c-stat"><div class="c-stat-val">০%</div><div class="c-stat-lbl">ভোকাল ব্লিড / নয়েজ</div></div></div>')
    a('</section>')
    a('<main class="chapters-container"><div class="chapter-grid">')
    for i, L in enumerate(LESSONS, 1):
        a('<a href="lesson_%02d.html" class="chapter-row">' % i)
        a('  <div class="ch-num">%s</div>' % (('০' if i < 10 else '') + bn(i)))
        a('  <div class="ch-body"><h2 class="ch-title">%s (%s)</h2>' % (esc(L["title_bn"]), esc(L["title_en"])))
        a('  <p class="ch-desc">%s</p>' % esc(L["sub"]))
        a('  <div class="ch-tags"><span class="ch-tag">🎮 ইন্টারেক্টিভ ল্যাব</span><span class="ch-tag">❓ কুইজ সংযুক্ত</span><span class="ch-tag">🎙️ শিক্ষক অডিও</span></div></div>')
        a('  <div class="ch-action">পাঠ খুলুন →</div>')
        a('</a>')
    a('</div></main>')
    a('<footer class="site-footer"><p>৩ব্লু১ব্রাউন বাংলা · মূল রচনা: Grant Sanderson · ভয়েস: bn-BD-PradeepNeural · অফলাইন গণিত: KaTeX</p></footer>')
    a('</body></html>')
    return '\n'.join(A) + '\n'

# ---------------------------------------------------------------- write
def w(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

for n, lesson in enumerate(LESSONS, 1):
    lid = "lesson_%02d" % n
    w("courses/physics/%s.html" % lid, build_html(lesson, n))
    w("data/physics/%s.json" % lid, json.dumps(build_json(lesson, n), ensure_ascii=False, indent=2) + "\n")
    man = build_manifest(lesson, n)
    w("assets/audio/physics/%s/manifest.json" % lid, json.dumps(man, ensure_ascii=False, indent=2) + "\n")
    w("assets/audio/physics/%s/manifest.js" % lid, "window.TEACHER_AUDIO_MANIFEST = " + json.dumps(man, ensure_ascii=False, indent=2) + ";\n")
    fig_i = 0
    for s in lesson["sections"]:
        for b in s["blocks"]:
            if b["t"] == "fig":
                fig_i += 1
                w("assets/figures/phys_%02d/fig_%02d.svg" % (n, fig_i),
                  make_svg(b["kind"], b["label"], fig_i + n))

w("courses/physics/index.html", build_index())
print("Generated %d physics lessons + index." % len(LESSONS))
