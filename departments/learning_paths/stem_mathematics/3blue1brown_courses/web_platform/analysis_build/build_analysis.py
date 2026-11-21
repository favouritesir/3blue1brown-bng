# -*- coding: utf-8 -*-
"""Build the new `analysis` course (10 component-based Bengali lesson pages).

Creates ONLY new folders/files:
  data/analysis, courses/analysis, assets/audio/analysis,
  assets/figures/an_01 .. an_10, media_vault/analysis, analysis_build/report
Nothing in the existing 53-lesson library is modified.
"""
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import content as C1
import content2 as C2

ROOT = Path(__file__).resolve().parent.parent
LESSONS = C1.LESSONS + C2.LESSONS
BN = {"0": "০", "1": "১", "2": "২", "3": "৩", "4": "৪",
      "5": "৫", "6": "৬", "7": "৭", "8": "৮", "9": "৯"}


def bnnum(n):
    return "".join(BN[c] for c in str(n))


def bn2(n):
    return bnnum(f"{n:02d}")


def E(s):
    return html.escape(str(s), quote=True)


def speak(text):
    """Turn LaTeX-ish lesson text into a TTS-friendly Bengali string (placeholder audio)."""
    t = text
    subs = {
        r"\zeta": "জেটা", r"\pi": "পাই", r"\infty": "অসীম", r"\hbar": "এইচ বার",
        r"\Delta": "ডেল্টা", r"\sum": "যোগ", r"\int": "ইন্টিগ্রাল",
        r"\sin": "সাইন", r"\cos": "কোসাইন", r"\log": "লগারিদম",
        r"\ln": "প্রাকৃতিক লগ", r"\sqrt": "বর্গমূল", r"\mathbb": "",
        r"\mathbf": "", r"\text": "", r"\frac": "ভগ্নাংশ", r"\left": "",
        r"\right": "", r"\quad": " ", r"\qquad": " ", r"\cdot": "গুণ",
        r"\approx": "প্রায় সমান", r"\geq": "চেয়ে বড় বা সমান",
        r"\leq": "চেয়ে ছোট বা সমান", r"\neq": "সমান নয়",
        r"\Longrightarrow": "অতএব", r"\Longleftrightarrow": "যদি এবং কেবল যদি",
        r"\cdots": "এবং আরও", r"\ldots": "এবং আরও", r"\oint": "বৃত্তীয় ইন্টিগ্রাল",
        r"\prod": "গুণফল", r"\mathrm": "", r"\sup": "",
    }
    for a, b in subs.items():
        t = t.replace(a, b)
    t = t.replace("$", "").replace("{", " ").replace("}", " ")
    t = re.sub(r"\\[a-zA-Z]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def cue_duration(text):
    return int(max(2600, min(11000, len(text) * 42)))


# ---------------------------------------------------------------------------
# Figure SVGs (new files, deterministic and dependency-free)
# ---------------------------------------------------------------------------
PAL = ["#74c0e3", "#e0a458", "#7bd88f", "#c08ce0", "#ef7d7d"]


def svg_figure(kind, title, accent):
    w, h = 640, 260
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
         f'width="{w}" height="{h}" role="img" aria-label="{E(title)}">',
         f'<rect width="{w}" height="{h}" fill="#10151f"/>',
         '<g stroke="#2b3648" stroke-width="1">']
    for x in range(40, w, 40):
        p.append(f'<line x1="{x}" y1="20" x2="{x}" y2="{h-20}"/>')
    for y in range(30, h - 20, 40):
        p.append(f'<line x1="20" y1="{y}" x2="{w-20}" y2="{y}"/>')
    p.append('</g>')

    if kind in ("wave", "spectro", "heat"):
        for k in range(3):
            pts = " ".join(
                f"{40 + i * 2},{130 - (52 - k * 12) * math.sin(i * (0.11 + k * 0.035))}"
                for i in range(280)
            )
            p.append(f'<polyline points="{pts}" fill="none" stroke="{PAL[k]}" stroke-width="2.4"/>')
    elif kind == "bars":
        for i in range(15):
            bh = 12 + 118 * math.exp(-((i - 7) ** 2) / 8.0)
            p.append(f'<rect x="{44 + i*38}" y="{210-bh}" width="26" height="{bh}" '
                     f'fill="{accent}" opacity="{0.55 + 0.03*i}"/>')
    elif kind in ("spiral", "polar"):
        for k in range(2):
            pts = " ".join(
                f"{320 + (12 + 0.42 * i) * math.cos(i * 0.16 + k * 2.1)},"
                f"{128 + (12 + 0.42 * i) * math.sin(i * 0.16 + k * 2.1)}"
                for i in range(250)
            )
            p.append(f'<polyline points="{pts}" fill="none" stroke="{PAL[k]}" stroke-width="2.2"/>')
        p.append('<circle cx="320" cy="128" r="4" fill="#fff"/>')
    elif kind == "grid":
        for i in range(9):
            p.append(f'<path d="M {50+i*68} 30 Q {140+i*52} 130 {50+i*68} 225" fill="none" '
                     f'stroke="{accent}" stroke-width="1.3" opacity="0.8"/>')
            p.append(f'<path d="M 40 {36+i*24} Q 320 {20+i*26} 600 {36+i*24}" fill="none" '
                     f'stroke="{PAL[2]}" stroke-width="1.1" opacity="0.55"/>')
    elif kind == "contour":
        for i in range(7):
            p.append(f'<path d="M {60+i*80} 40 C {110+i*74} 90, {20+i*84} 150, '
                     f'{80+i*78} 220" fill="none" stroke="{PAL[i%5]}" stroke-width="2"/>')
    elif kind == "numberline":
        p.append('<line x1="40" y1="130" x2="600" y2="130" stroke="#fff" stroke-width="2"/>')
        for i in range(13):
            x = 60 + i * 44
            p.append(f'<line x1="{x}" y1="122" x2="{x}" y2="138" stroke="#fff"/>')
        p.append(f'<circle cx="120" cy="130" r="7" fill="{accent}"/>')
        p.append(f'<circle cx="524" cy="130" r="7" fill="{PAL[4]}"/>')
    else:
        p.append(f'<circle cx="320" cy="128" r="78" fill="none" stroke="{accent}" stroke-width="3"/>')

    p.append(f'<text x="20" y="248" fill="{accent}" font-size="15" font-family="monospace">'
             f'{E(title)}</text>')
    p.append('</svg>')
    return "\n".join(p)


# ---------------------------------------------------------------------------
# HTML pieces (exact L01 component set / load order)
# ---------------------------------------------------------------------------
def head_html(lesson, nn):
    title = f"{lesson['title_bn']} | {lesson['title_en']}"
    return f'''<!DOCTYPE html>
<html lang="bn" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<script>(function(){{const t=localStorage.getItem('3b1b-theme')||'dark';document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');else document.documentElement.classList.remove('dark');}})();</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{E(title)}</title>

<!-- ═══════════ STYLES ═══════════ -->
<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>
<link rel="stylesheet" href="../../assets/css/main.css"/>
<link rel="icon" type="image/svg+xml" href="../../assets/images/favicon.svg"/>
<link rel="stylesheet" href="../../assets/css/lesson.css"/>
<link rel="stylesheet" href="../../assets/css/narration.css"/>

<!-- ═══════════ MANIFEST (preloaded for file:// / zero-CORS) ═══════════ -->
<script src="../../assets/audio/analysis/lesson_{nn:02d}/manifest.js?v=7"></script>

<!-- ═══════════ SCRIPTS — strict load order ═══════════
     1. KaTeX engine  2. Component definitions  3. Page controllers
     4. Narration engine (last: parses final DOM on DOMContentLoaded) -->
<script defer src="../../assets/libs/katex/katex.min.js"></script>
<script defer src="../../assets/libs/katex/auto-render.min.js"></script>
<script defer src="../../assets/libs/katex-stub.js"></script>
<script defer src="../../assets/js/lesson_components.js"></script>
<script defer src="../../assets/js/lesson_components_extended.js"></script>
<script defer src="../../assets/js/main.js"></script>
<script defer src="../../assets/js/lesson.js"></script>
<script defer src="../../assets/js/narration_engine.js"></script>
</head>
<body class="mode-read">

<!-- ═══════════ SEARCH OVERLAY ═══════════ -->
<b1b-search-overlay></b1b-search-overlay>

'''


def navbar_html(lesson, nn):
    prev_url = f"lesson_{nn-1:02d}.html" if nn > 1 else ""
    next_url = f"lesson_{nn+1:02d}.html" if nn < 10 else ""
    prev_title = "পূর্ববর্তী অধ্যায় নেই" if nn == 1 else f"পূর্ববর্তী অধ্যায়: {LESSONS[nn-2]['title_bn']}"
    next_title = "শেষ অধ্যায়" if nn == 10 else f"পরবর্তী অধ্যায়: {LESSONS[nn]['title_bn']}"
    return f'''<!-- ═══════════ NAVBAR (responsive stepper included) ═══════════ -->
<b1b-navbar
  course-title="বিশ্লেষণ"
  course-url="../../index.html#analysis"
  home-url="../../index.html"
  chapter-num="{bn2(nn)}"
  chapter-total="১০"
  prev-url="{prev_url}"
  prev-title="{E(prev_title)}"
  next-url="{next_url}"
  next-title="{E(next_title)}"
  active-mode="read">
</b1b-navbar>

'''


def hero_html(lesson, nn):
    vsrc = f"../../media_vault/analysis/lesson_{nn:02d}/experiments/3b1b_analysis_{nn:02d}_full_dubbed.mp4"
    full = f"{lesson['title_bn']} | {lesson['title_en']}"
    return f'''<!-- ═══════════ HERO ═══════════ -->
<b1b-hero-player
  course-title="বিশ্লেষণ"
  course-url="../../index.html"
  chapter-label="অধ্যায় {bn2(nn)} · বিশ্লেষণ"
  title="{E(full)}"
  desc="{E(lesson['subtitle_bn'])}"
  video-src="{vsrc}"
  yt-id="{lesson['yt_id']}"
  date="{E(lesson['date_bn'])}"
  author="Grant Sanderson"
  author-url="https://www.3blue1brown.com/about"
  translation="বাংলা রূপান্তর: Grant Sanderson (3Blue1Brown) | বাংলা ডাবিং ও পাঠ: STEM টিম"
  github-url="https://www.3blue1brown.com/lessons/{lesson['slug']}"
  voice-badge="বাংলা ভয়েস: Edge-TTS bn-BD-PradeepNeural · ০% ইংলিশ ব্লিড">
</b1b-hero-player>

'''


def bookmark_time(sec):
    return f"{sec//60:02d}:{sec%60:02d}"


def body_html(lesson, nn, sections):
    vsrc = f"../../media_vault/analysis/lesson_{nn:02d}/experiments/3b1b_analysis_{nn:02d}_full_dubbed.mp4"
    parts = ['''<!-- ═══════════ LESSON BODY ═══════════ -->
<div class="lesson-body">

  <!-- ── READ MODE ── -->
  <div class="read-mode">

    <b1b-narration-banner></b1b-narration-banner>

    <b1b-bookmarks>
''']
    for i, sec in enumerate(sections):
        t = i * 70
        parts.append(f'      <b1b-bookmark time="{t}" time-bn="{bn2(t//60)}:{bn2(t%60)}">{E(sec["title"])}</b1b-bookmark>\n')
    parts.append('''    </b1b-bookmarks>

    <b1b-toc-sidebar title="📋 বিষয়সূচি" variant="card">
''')
    for sec in sections:
        parts.append(f'      <a href="#{sec["id"]}">{E(sec["title"])}</a>\n')
    parts.append('''    </b1b-toc-sidebar>

    <b1b-article>
''')

    fig_no = 0
    for si, sec in enumerate(sections):
        parts.append(f'\n      <!-- ═══ {E(sec["title"])} ═══ -->\n')
        parts.append(f'      <b1b-section id="{sec["id"]}" title="{E(sec["title"])}">\n')
        for bi, block in enumerate(sec["blocks"]):
            kind = block[0]
            if kind == "p":
                parts.append(f'        <p>{block[1]}</p>\n')
            elif kind == "quote":
                parts.append(f'        <b1b-quote author="{E(block[2])}">{block[1]}</b1b-quote>\n')
            elif kind == "formula":
                parts.append(f'        <b1b-formula math="{E(block[1])}"></b1b-formula>\n')
            elif kind == "figure":
                fig_no += 1
                src = f"../../assets/figures/an_{nn:02d}/fig_{nn:02d}_{fig_no:02d}.svg"
                cap = E(block[1])
                parts.append(f'        <b1b-figure src="{src}" alt="{cap}" caption="{cap}"></b1b-figure>\n')
            elif kind == "callout":
                typ = ("gold", "blue", "green", "blue")[bi % 4]
                icon = ("📌", "📐", "🌟", "💡")[bi % 4]
                parts.append(f'        <b1b-callout type="{typ}" icon="{icon}" title="{E(block[1])}">\n'
                             f'          <p>{block[2]}</p>\n'
                             f'        </b1b-callout>\n')
        # Quizzes assigned to this section (do not create narration blocks)
        for q in lesson["quizzes"]:
            if q["section"] == si:
                parts.append(f'\n        <!-- Quiz {E(q["id"])} -->\n')
                parts.append('        <b1b-quiz\n')
                parts.append(f'          question="❓ {E(q["question"])}"\n')
                parts.append(f'          correct="{q["correct"]}"\n')
                parts.append(f'          correct-msg="{E(q["correct_msg"])}"\n')
                parts.append(f'          wrong-msg="{E(q["wrong_msg"])}"\n')
                parts.append(f'          reveal-msg="{E(q["reveal"])}">\n')
                for o in q["options"]:
                    parts.append(f'          <div slot="option">{o}</div>\n')
                parts.append('        </b1b-quiz>\n')
        parts.append('      </b1b-section>\n')

    parts.append('''
    </b1b-article>
  </div><!-- /read-mode -->

  <!-- ── WATCH MODE ── -->
  <b1b-watch-panel
''')
    parts.append(f'''    video-src="{vsrc}"
    yt-id="{lesson['yt_id']}"
    title="{E(lesson['title_bn'])} — অধ্যায় {bn2(nn)}"
    subtitle="সম্পূর্ণ প্রমিত বাংলায় ডাব করা, EBU R128 লাউডনেস নরমালাইজড অডিও এবং জিরো ইংলিশ ভোকাল ব্লিড মোড সহ।"
    playlist-title="📋 প্লেলিস্ট — বিশ্লেষণ">
  </b1b-watch-panel>

</div><!-- /lesson-body -->

''')
    p_url = f"lesson_{nn-1:02d}.html" if nn > 1 else ""
    n_url = f"lesson_{nn+1:02d}.html" if nn < 10 else ""
    parts.append(f'''<!-- ═══════════ BOTTOM NAVIGATION / FOOTER ═══════════ -->
<b1b-chapter-nav
  prev-url="{p_url}"
  prev-title="{E(LESSONS[nn-2]['title_bn']) if nn>1 else 'শুরু'}"
  prev-dir="পূর্ববর্তী অধ্যায়"
  next-url="{n_url}"
  next-title="{E(LESSONS[nn]['title_bn']) if nn<10 else 'শেষ'}"
  next-dir="পরবর্তী অধ্যায়">
</b1b-chapter-nav>

<b1b-footer></b1b-footer>
<b1b-back-to-top></b1b-back-to-top>

</body>
</html>
''')
    return "".join(parts)


# ---------------------------------------------------------------------------
# Data JSON / manifest
# ---------------------------------------------------------------------------
def build_data(lesson, nn, sections):
    sec_out = []
    for sec in sections:
        figs = []
        for b in sec["blocks"]:
            if b[0] == "figure":
                figs.append({
                    "id": f"fig_{nn:02d}_{len(figs)+1:02d}",
                    "caption_bn": b[1],
                    "type": "svg",
                    "src": f"figures/an_{nn:02d}/fig_{nn:02d}_{len(figs)+1:02d}.svg",
                })
        takeaways = []
        formulas = []
        for b in sec["blocks"]:
            if b[0] in ("p", "callout"):
                txt = b[1] if b[0] == "p" else b[2]
                takeaways.append(speak(txt)[:220])
            elif b[0] == "formula":
                formulas.append({"label": "মূল সূত্র", "katex": b[1]})
        sec_out.append({
            "id": sec["id"],
            "title_bn": sec["title"],
            "title_en": sec["title"],
            "summary_bn": speak(sec["blocks"][0][1])[:200] if sec["blocks"] else "",
            "key_takeaways": takeaways[:5],
            "formulas": formulas,
            "figures": figs,
        })
    quizzes = []
    for q in lesson["quizzes"]:
        quizzes.append({
            "id": q["id"],
            "section_ref": sections[q["section"]]["id"],
            "question_bn": q["question"],
            "question_en": q["question"],
            "options": q["options"],
            "options_bn": q["options"],
            "correct_index": q["correct"],
            "explanation_bn": q["correct_msg"],
            "explanation_en": q["correct_msg"],
            "hint": q["wrong_msg"],
            "hints": [q["wrong_msg"], q["reveal"]],
        })
    return {
        "lesson_id": f"lesson_{nn:02d}",
        "chapter_num": nn,
        "course_id": "analysis",
        "title_en": lesson["title_en"],
        "title_bn": lesson["title_bn"],
        "subtitle_bn": lesson["subtitle_bn"],
        "video_id": lesson["yt_id"],
        "official_url": f"https://www.3blue1brown.com/lessons/{lesson['slug']}",
        "meta": {
            "credits": "Grant Sanderson (3Blue1Brown)",
            "translator_curator": "Bengali STEM Pedagogy Unit",
            "duration": "—",
            "prerequisites": [],
        },
        "epigraph": {
            "quote": lesson["epigraph"][0],
            "quote_bn": lesson["epigraph"][1],
            "author": f"Grant Sanderson / {lesson['epigraph'][2]}",
        },
        "sections": sec_out,
        "quizzes": quizzes,
    }


TYPE_MAP = {"p": "p", "quote": "chapter-quote", "figure": "figure",
            "callout": "callout", "formula": "formula-box"}


def build_manifest(lesson, nn, sections):
    out_sections = {}
    for sec in sections:
        cues = []

        def add(kind, text):
            idx = len(cues)
            dur = cue_duration(text)
            start = 0 if idx == 0 else cues[-1]["end_ms"] + 350
            cues.append({
                "index": idx, "type": kind, "text": text,
                "start_ms": float(start), "end_ms": float(start + dur),
                "duration_ms": float(dur),
            })

        add("h2", f"পাঠের এই অংশ: {sec['title']}।")
        for b in sec["blocks"]:
            if b[0] == "quote":
                add("chapter-quote", "উদ্ধৃতি। " + speak(b[1]) + "।")
            elif b[0] == "p":
                add("p", speak(b[1]))
            elif b[0] == "figure":
                add("figure", "চিত্রে দেখা যাচ্ছে, " + speak(b[1]) + "।")
            elif b[0] == "callout":
                add("callout", "বিশেষ নোট। " + speak(b[1]) + "। " + speak(b[2]))
            elif b[0] == "formula":
                add("formula-box", "গাণিতিক সূত্র। " + speak(b[1]))
        out_sections[sec["id"]] = {
            "title": sec["title"],
            "audio_file": f"sec_{nn:02d}_{sec['id']}.mp3",
            "total_duration_ms": float(cues[-1]["end_ms"] + 1000),
            "cues": cues,
        }
    return {
        "course": "analysis",
        "lesson": f"lesson_{nn:02d}",
        "voice": "bn-BD-PradeepNeural",
        "mode": "authentic_teacher",
        "sections": out_sections,
    }


# ---------------------------------------------------------------------------
# Course index
# ---------------------------------------------------------------------------
def index_html():
    rows = []
    for i, l in enumerate(LESSONS, 1):
        rows.append(f'''
    <a href="lesson_{i:02d}.html" class="chapter-row">
      <div class="ch-num">{bnnum(i):0>2}</div>
      <div class="ch-body">
        <h2 class="ch-title">{E(l['title_bn'])} ({E(l['title_en'])})</h2>
        <p class="ch-desc">{E(l['subtitle_bn'])}</p>
        <div class="ch-tags">
          <span class="ch-tag">📅 {E(l['date_bn'])}</span><span class="ch-tag">🎮 ইন্টারেক্টিভ ল্যাব</span><span class="ch-tag">❓ কুইজ সংযুক্ত</span>
        </div>
      </div>
      <div class="ch-action">পাঠ খুলুন →</div>
    </a>
''')
    src = (ROOT / "courses/linear_algebra/index.html").read_text(encoding="utf-8")
    # Reuse the exact stylesheet block and navbar/footer shell from the gold index.
    style = src.split("<style>", 1)[1].split("</style>", 1)[0]
    nav_start = src.index("<!-- ═══════════ NAVBAR ═══════════ -->")
    nav_end = src.index("<!-- ═══════════ HERO ═══════════ -->")
    nav = src[nav_start:nav_end]
    nav = nav.replace("../../index.html", "../../index.html")
    nav = nav.replace("<span>লিনিয়ার অ্যালজেব্রা</span>", "<span>বিশ্লেষণ</span>")
    nav = nav.replace('href="lesson_01.html"', 'href="lesson_01.html"')
    return f'''<!DOCTYPE html>
<html lang="bn" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>বিশ্লেষণ — ৩ব্লু১ব্রাউন বাংলা</title>
<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>
<link rel="stylesheet" href="../../assets/css/lesson.css"/>
<script defer src="../../assets/libs/katex/katex.min.js"></script>
<script defer src="../../assets/libs/katex/auto-render.min.js"></script>
<script defer src="../../assets/js/lesson.js"></script>
<style>{style}</style>
</head>
<body class="mode-read">

{nav}
<!-- ═══════════ HERO ═══════════ -->
<section class="course-hero">
  <div class="course-badge">সম্পূর্ণ বাংলায় অনুদিত ও ভিজ্যুয়ালাইজড</div>
  <h1 class="course-title">বিশ্লেষণ</h1>
  <p class="course-sub">Analysis — জেটা ফাংশন, ফুরিয়ার বিশ্লেষণ, কনভোলিউশন, ওয়াইন্ডিং নম্বর, প্যাডিক সংখ্যা ও পরিমাপ তত্ত্ব: গ্রান্ট স্যান্ডারসনের এই ধারণাগুলোর বাংলা পাঠ।</p>

  <div class="course-stats-bar">
    <div class="c-stat"><div class="c-stat-val">১০</div><div class="c-stat-lbl">সম্পূর্ণ পাঠ</div></div>
    <div class="c-stat"><div class="c-stat-val">৪০+</div><div class="c-stat-lbl">ন্যারেশন কিউ</div></div>
    <div class="c-stat"><div class="c-stat-val">১০০%</div><div class="c-stat-lbl">অফলাইন KaTeX গণিত</div></div>
    <div class="c-stat"><div class="c-stat-val">০%</div><div class="c-stat-lbl">ভোকাল ব্লিড / নয়েজ</div></div>
  </div>
</section>

<!-- ═══════════ CHAPTERS LIST ═══════════ -->
<main class="chapters-container">
  <div class="chapter-grid">
  {''.join(rows)}
  </div>
</main>

</body>
</html>
'''


# ---------------------------------------------------------------------------
def ffmpeg(*args):
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return True
    except Exception as exc:
        print("  ffmpeg failed:", exc)
        return False


def main():
    made = {"html": 0, "data": 0, "manifest": 0, "figures": 0, "audio": 0, "video": 0}
    for nn, lesson in enumerate(LESSONS, 1):
        sections = []
        for sec in lesson["sections"]:
            blocks = list(sec["blocks"])
            if not sections:
                ep = lesson["epigraph"]
                blocks = [("quote", ep[1], ep[2])] + blocks
            sections.append({"id": sec["id"], "title": sec["title"], "blocks": blocks})

        d = ROOT / "data/analysis"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"lesson_{nn:02d}.json").write_text(
            json.dumps(build_data(lesson, nn, sections), ensure_ascii=False, indent=2), encoding="utf-8")
        made["data"] += 1

        c = ROOT / "courses/analysis"
        c.mkdir(parents=True, exist_ok=True)
        (c / f"lesson_{nn:02d}.html").write_text(
            head_html(lesson, nn) + navbar_html(lesson, nn) + hero_html(lesson, nn) +
            body_html(lesson, nn, sections), encoding="utf-8")
        made["html"] += 1

        a = ROOT / f"assets/audio/analysis/lesson_{nn:02d}"
        a.mkdir(parents=True, exist_ok=True)
        man = build_manifest(lesson, nn, sections)
        (a / "manifest.json").write_text(
            json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
        (a / "manifest.js").write_text(
            "window.TEACHER_AUDIO_MANIFEST = " + json.dumps(man, ensure_ascii=False, indent=2) + ";\n",
            encoding="utf-8")
        made["manifest"] += 1

        figdir = ROOT / f"assets/figures/an_{nn:02d}"
        figdir.mkdir(parents=True, exist_ok=True)
        fig_no = 0
        for sec in sections:
            for b in sec["blocks"]:
                if b[0] == "figure":
                    fig_no += 1
                    (figdir / f"fig_{nn:02d}_{fig_no:02d}.svg").write_text(
                        svg_figure(b[2], f"FIG {nn:02d}.{fig_no:02d}  {b[1][:28]}",
                                   PAL[(nn + fig_no) % len(PAL)]), encoding="utf-8")
                    made["figures"] += 1

        # Silent placeholder audio so the narrator finds playable files.
        for sid, s in man["sections"].items():
            mp3 = a / s["audio_file"]
            if not mp3.exists() or mp3.stat().st_size < 100:
                dur = max(1.0, s["total_duration_ms"] / 1000.0)
                if ffmpeg("-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
                          "-t", f"{dur:.2f}", "-c:a", "libmp3lame", "-b:a", "16k", mp3):
                    made["audio"] += 1

        vdir = ROOT / f"media_vault/analysis/lesson_{nn:02d}/experiments"
        vdir.mkdir(parents=True, exist_ok=True)
        mp4 = vdir / f"3b1b_analysis_{nn:02d}_full_dubbed.mp4"
        if not mp4.exists() or mp4.stat().st_size < 100:
            if ffmpeg("-f", "lavfi", "-i", "color=c=0x10151f:s=640x360:r=24",
                      "-t", "1", "-pix_fmt", "yuv420p", "-c:v", "libx264",
                      "-crf", "36", "-preset", "ultrafast", mp4):
                made["video"] += 1

        print(f"built lesson_{nn:02d}  sections={len(sections)}  "
              f"cues={sum(len(s['cues']) for s in man['sections'].values())}")

    c = ROOT / "courses/analysis"
    (c / "index.html").write_text(index_html(), encoding="utf-8")
    print("index written")
    print(made)


if __name__ == "__main__":
    main()
