# -*- coding: utf-8 -*-
"""
Build the NEW "number_theory" course (3 official 3B1B lessons) from scratch.

Everything produced here lives in brand-new folders only:
  data/number_theory/
  courses/number_theory/
  assets/audio/number_theory/
  assets/figures/nt_0N/            (inline SVG figures are embedded in HTML)

No existing lesson, component library or shared asset is modified.
"""
from pathlib import Path
import json
import math
import re

ROOT = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics\3blue1brown_courses\web_platform")
COURSE = "number_theory"

DATA_DIR = ROOT / "data" / COURSE
COURSE_DIR = ROOT / "courses" / COURSE
AUDIO_DIR = ROOT / "assets" / "audio" / COURSE

for d in (DATA_DIR, COURSE_DIR, AUDIO_DIR):
    d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Tiny inline SVG figure helpers (all figures are embedded in the lesson HTML)
# --------------------------------------------------------------------------- #
_SVG_MARKER_COUNTER = [0]


def _svg(inner, label):
    # Each inline SVG needs a globally unique marker id: duplicate DOM ids are
    # a verification failure and can make arrowheads point at the wrong def.
    _SVG_MARKER_COUNTER[0] += 1
    mid = "nt-arrow-%d" % _SVG_MARKER_COUNTER[0]
    inner = inner.replace('id="ah"', 'id="%s"' % mid).replace("url(#ah)", "url(#%s)" % mid)
    return (
        '<svg viewBox="0 0 400 220" xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="%s" style="width:100%%;max-width:440px;height:auto;'
        'background:#0e1622;border:1px solid #27364a;border-radius:10px">'
        '<defs><marker id="%s" markerWidth="8" markerHeight="8" refX="6" refY="3" '
        'orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8afdff"/></marker></defs>'
        % (label, mid) + inner + "</svg>"
    )


def spiral_svg(step=0.31, count=210, phase=0.0):
    pts = []
    for i in range(count):
        r = 1.5 + i * 0.44
        a = i * step + phase
        x = 200 + r * math.cos(a)
        y = 110 + r * math.sin(a)
        pts.append("%.1f,%.1f" % (x, y))
    grid = "".join(
        '<line x1="%d" y1="0" x2="%d" y2="220" stroke="#1d2939" stroke-width="1"/>' % (x, x)
        for x in range(0, 401, 40)
    ) + "".join(
        '<line x1="0" y1="%d" x2="400" y2="%d" stroke="#1d2939" stroke-width="1"/>' % (y, y)
        for y in range(0, 221, 40)
    )
    return _svg(
        grid
        + '<polyline points="%s" fill="none" stroke="#8afdff" stroke-width="2" opacity="0.9"/>' % " ".join(pts)
        + '<circle cx="200" cy="110" r="3.5" fill="#ffd166"/>'
        + '<text x="206" y="105" fill="#ffd166" font-size="11">(0,0)</text>'
        + '<text x="8" y="18" fill="#8afdff" font-size="12">r = θ, এক ধাপ = ১ রেডিয়ান</text>',
        "আর্কিমিডিয় সর্পিল",
    )


def rays_svg(n=44, gaps=()):
    lines = []
    for i in range(n):
        if i in gaps:
            continue
        a = 2 * math.pi * i / n
        x = 200 + 190 * math.cos(a)
        y = 110 + 95 * math.sin(a)
        lines.append(
            '<line x1="200" y1="110" x2="%.1f" y2="%.1f" stroke="#8afdff" '
            'stroke-width="1.4" opacity="0.75"/>' % (x, y)
        )
    return _svg(
        "".join(lines)
        + '<circle cx="200" cy="110" r="3" fill="#ffd166"/>'
        + '<text x="8" y="18" fill="#ffd166" font-size="12">মডুলার অবশিষ্ট শ্রেণি → সরল রশ্নি</text>',
        "অবশিষ্ট শ্রেণির রশ্নি",
    )


def lattice_svg():
    dots = []
    for x in range(-5, 6):
        for y in range(-5, 6):
            if x * x + y * y <= 24:
                px, py = 200 + x * 15, 110 - y * 15
                prime_like = (x * x + y * y) in (5, 13, 17, 25)
                col = "#ffd166" if prime_like else "#8afdff"
                dots.append('<circle cx="%d" cy="%d" r="2.6" fill="%s"/>' % (px, py, col))
    return _svg(
        '<circle cx="200" cy="110" r="77" fill="none" stroke="#4361ee" stroke-width="1.6" stroke-dasharray="4 3"/>'
        + '<line x1="200" y1="18" x2="200" y2="202" stroke="#27364a"/>'
        + '<line x1="108" y1="110" x2="292" y2="110" stroke="#27364a"/>'
        + "".join(dots)
        + '<text x="8" y="18" fill="#ffd166" font-size="12">বৃত্তের ভেতরের গাউসিয়ান বিন্দু ~ πR²</text>',
        "গাউসিয়ান বৃত্ত",
    )


def bars_svg(vals, colors=None):
    bars = []
    for i, v in enumerate(vals):
        x = 24 + i * (352 / max(len(vals), 1))
        h = v * 110
        col = (colors or ["#8afdff"] * len(vals))[i]
        bars.append(
            '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" rx="2"/>'
            % (x, 175 - h, min(26, 330 / max(len(vals), 1) - 4), h, col)
        )
    return _svg(
        '<line x1="20" y1="175" x2="380" y2="175" stroke="#8afdff"/>'
        + "".join(bars)
        + '<text x="8" y="18" fill="#ffd166" font-size="12">হিস্টোগ্রাম: প্রতিটি শ্রেণির মৌলিক সংখ্যার অনুপাত</text>',
        "মৌলিক বণ্টন হিস্টোগ্রাম",
    )


def triangle_svg():
    return _svg(
        '<polygon points="90,170 90,50 250,170" fill="none" stroke="#8afdff" stroke-width="2"/>'
        '<rect x="50" y="130" width="40" height="40" fill="none" stroke="#ffd166"/>'
        '<rect x="90" y="10" width="160" height="40" fill="none" stroke="#ffd166"/>'
        '<rect x="250" y="130" width="40" height="40" fill="none" stroke="#ffd166"/>'
        '<text x="66" y="158" fill="#ffd166" font-size="13">a²</text>'
        '<text x="160" y="36" fill="#ffd166" font-size="13">b²</text>'
        '<text x="290" y="158" fill="#ffd166" font-size="13">c²</text>'
        '<text x="10" y="205" fill="#8afdff" font-size="12">a² + b² = c² — তিন বর্গের ক্ষেত্রফলের সমতা</text>',
        "পিথাগোরীয় ত্রিভুজ",
    )


def unit_circle_svg():
    return _svg(
        '<circle cx="160" cy="110" r="80" fill="none" stroke="#8afdff" stroke-width="2"/>'
        '<line x1="40" y1="190" x2="300" y2="30" stroke="#ffd166" stroke-width="1.6" marker-end="url(#ah)"/>'
        '<circle cx="96" cy="62" r="4" fill="#ffd166"/>'
        '<text x="100" y="55" fill="#ffd166" font-size="12">(x, y)</text>'
        '<circle cx="80" cy="110" r="4" fill="#8afdff"/>'
        '<text x="50" y="132" fill="#8afdff" font-size="11">(−1, 0)</text>'
        '<text x="8" y="18" fill="#ffd166" font-size="12">(-1,0) দিয়ে কাটা রেখার ঢাল t → পরিমেয় বিন্দু</text>',
        "একক বৃত্ত ও পরিমেয় বিন্দু",
    )


def complex_svg():
    grid = "".join(
        '<line x1="%d" y1="0" x2="%d" y2="220" stroke="#1d2939"/>' % (x, x)
        for x in range(0, 401, 25)
    ) + "".join(
        '<line x1="0" y1="%d" x2="400" y2="%d" stroke="#1d2939"/>' % (y, y)
        for y in range(0, 221, 25)
    )
    return _svg(
        grid
        + '<line x1="60" y1="160" x2="150" y2="40" stroke="#ffd166" stroke-width="2" marker-end="url(#ah)"/>'
        + '<line x1="60" y1="160" x2="60" y2="40" stroke="#8afdff" stroke-width="1"/>'
        + '<line x1="60" y1="160" x2="150" y2="160" stroke="#8afdff" stroke-width="1"/>'
        + '<circle cx="150" cy="40" r="4" fill="#ffd166"/>'
        + '<text x="156" y="36" fill="#ffd166" font-size="13">a + bi</text>'
        + '<circle cx="150" cy="280" r="4" fill="#8afdff"/>'
        + '<text x="8" y="18" fill="#ffd166" font-size="12">a + bi-এর নর্ম = a² + b²</text>',
        "জটিল তল",
    )


def series_svg():
    vals = [1, 0.667, 0.867, 0.724, 0.835, 0.744, 0.821, 0.754, 0.811, 0.764]
    pts = " ".join("%.1f,%.1f" % (30 + i * 36, 120 - (v - 0.78) * 500) for i, v in enumerate(vals))
    return _svg(
        '<line x1="20" y1="120" x2="385" y2="120" stroke="#ffd166" stroke-dasharray="5 4"/>'
        '<polyline points="%s" fill="none" stroke="#8afdff" stroke-width="2"/>' % pts
        + '<text x="8" y="18" fill="#ffd166" font-size="12">আংশিক যোগফল π/4-এর চারপাশে দোলা খাচ্ছে</text>',
        "লাইবনিটজ ধারা",
    )


def product_svg():
    rings = "".join(
        '<circle cx="200" cy="110" r="%d" fill="none" stroke="#8afdff" opacity="%0.2f"/>'
        % (18 + i * 13, 0.9 - i * 0.09)
        for i in range(7)
    )
    return _svg(
        rings
        + '<text x="205" y="114" fill="#ffd166" font-size="14">π/4</text>'
        + '<text x="8" y="18" fill="#ffd166" font-size="12">প্রতিটি মৌলিক সংখ্যা এক একটি গুণনীয়ক</text>',
        "অয়লার গুণফল",
    )


# --------------------------------------------------------------------------- #
# Content builders
# --------------------------------------------------------------------------- #
def P(html, say):
    return ("p", html, say)


def Q(text, author, say):
    return ("quote", text, author, say)


def F(svg, caption, say):
    return ("figure", svg, caption, say)


def C(kind, icon, title, body, say):
    return ("callout", kind, icon, title, body, say)


def M(latex, say):
    return ("formula", latex, say)


def H(text, say):
    return ("h3", text, say)


def Z(qid):
    return ("quiz", qid)


QUIZ_TYPES = {"p", "quote", "figure", "callout", "formula", "h3"}


def cue_type(block):
    return block[0]


def render_blocks(sec, quizzes):
    out = []
    for b in sec["blocks"]:
        kind = b[0]
        if kind == "p":
            out.append("<p>%s</p>" % b[1])
        elif kind == "quote":
            out.append('<b1b-quote author="%s">%s</b1b-quote>' % (b[2], b[1]))
        elif kind == "figure":
            out.append(
                '<b1b-figure alt="%s" caption="%s">%s</b1b-figure>'
                % (b[3], b[2], b[1])
            )
        elif kind == "callout":
            out.append(
                '<b1b-callout type="%s" icon="%s" title="%s"><p>%s</p></b1b-callout>'
                % (b[1], b[2], b[3], b[4])
            )
        elif kind == "formula":
            out.append('<b1b-formula math="%s"></b1b-formula>' % b[1])
        elif kind == "h3":
            out.append('<h3 style="font-size:1.25rem;font-weight:700;margin:24px 0 12px;color:var(--theme);">%s</h3>' % b[1])
        elif kind == "quiz":
            q = quizzes[b[1]]
            opts = "\n".join('          <div slot="option">%s</div>' % o for o in q["options"])
            out.append(
                '<b1b-quiz\n'
                '          question="%s"\n'
                '          correct="%d"\n'
                '          correct-msg="%s"\n'
                '          wrong-msg="%s"\n'
                '          reveal-msg="%s">\n%s\n        </b1b-quiz>'
                % (q["question"], q["correct"], q["correct_msg"], q["wrong_msg"],
                   q["reveal_msg"], opts)
            )
    return "\n\n        ".join(out)


CUE_TYPE_MAP = {"quote": "chapter-quote", "formula": "formula-box"}


def manifest_for(lesson):
    sections = {}
    for idx, sec in enumerate(lesson["sections"], 1):
        cues = []
        t = 0
        # The narration engine always emits the section <h2> as the first cue.
        h2_text = "(%d) %s" % (idx, sec["title"])
        h2_dur = int(max(2600, min(26000, len(h2_text) * 78)))
        cues.append({
            "index": 0,
            "type": "h2",
            "text": h2_text,
            "start_ms": 0.0,
            "end_ms": float(h2_dur),
            "duration_ms": float(h2_dur),
        })
        t = h2_dur
        for b in sec["blocks"]:
            if b[0] not in QUIZ_TYPES:
                continue
            say = b[-1]
            dur = int(max(2600, min(26000, len(say) * 78)))
            if cues:
                t += 350
            cues.append({
                "index": len(cues),
                "type": CUE_TYPE_MAP.get(b[0], b[0]),
                "text": say,
                "start_ms": float(t),
                "end_ms": float(t + dur),
                "duration_ms": float(dur),
            })
            t += dur
        sections[sec["id"]] = {
            "title": sec["title"],
            "audio_file": "sec_%02d_%s.mp3" % (idx, sec["id"]),
            "total_duration_ms": float(t + 350),
            "cues": cues,
        }
    return {
        "course": COURSE,
        "lesson": "lesson_%02d" % lesson["num"],
        "voice": "bn-BD-PradeepNeural",
        "mode": "authentic_teacher",
        "sections": sections,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="bn" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<script>(function(){const t=localStorage.getItem('3b1b-theme')||'dark';document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');else document.documentElement.classList.remove('dark');})();</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>@@TITLE@@</title>

<!-- ═══════════ STYLES ═══════════ -->
<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>
<link rel="stylesheet" href="../../assets/css/main.css"/>
<link rel="icon" type="image/svg+xml" href="../../assets/images/favicon.svg"/>
<link rel="stylesheet" href="../../assets/css/lesson.css"/>
<link rel="stylesheet" href="../../assets/css/narration.css"/>

<!-- ═══════════ MANIFEST (preloaded for file:// / zero-CORS) ═══════════ -->
<script src="../../assets/audio/number_theory/lesson_@@NN@@/manifest.js?v=1"></script>

<!-- ═══════════ SCRIPTS — strict load order ═══════════ -->
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

<b1b-search-overlay></b1b-search-overlay>

<b1b-navbar
  course-title="সংখ্যা তত্ত্ব"
  course-url="../../index.html#number-theory"
  home-url="../../index.html"
  chapter-num="@@BN@@"
  chapter-total="০৩"
  prev-url="@@PREV@@"
  prev-title="@@PREV_TITLE@@"
  next-url="@@NEXT@@"
  next-title="@@NEXT_TITLE@@"
  active-mode="read">
</b1b-navbar>

<b1b-hero-player
  course-title="সংখ্যা তত্ত্ব"
  course-url="../../index.html"
  chapter-label="অধ্যায় @@BN@@ · সংখ্যা তত্ত্ব"
  title="@@TITLE@@"
  desc="@@DESC@@"
  video-src="../../media_vault/number_theory/lesson_@@NN@@/experiments/3b1b_number_theory_@@NN@@_full_dubbed.mp4"
  yt-id="@@YT@@"
  date="@@DATE@@"
  author="Grant Sanderson"
  author-url="https://www.3blue1brown.com/about"
  translation="বাংলা রূপান্তর: Grant Sanderson (3Blue1Brown) | বাংলা ডাবিং ও পাঠ: STEM টিম"
  github-url="@@GITHUB@@"
  voice-badge="বাংলা ভয়েস: Edge-TTS bn-BD-PradeepNeural · ০% ইংলিশ ব্লিড">
</b1b-hero-player>

<div class="lesson-body">

  <div class="read-mode">

    <b1b-narration-banner></b1b-narration-banner>

    <b1b-bookmarks>
@@BOOKMARKS@@
    </b1b-bookmarks>

    <b1b-toc-sidebar title="📋 বিষয়সূচি" variant="card">
@@TOC@@
    </b1b-toc-sidebar>

    <b1b-article>
@@SECTIONS@@

      <!-- ── Interactive lab : intentionally outside narration ── -->
      <b1b-section id="sec-lab" title="@@LAB_TITLE@@" data-no-narration="true">
        <p class="viz-intro">@@LAB_DESC@@</p>
        <b1b-fullscreen label="⛶ পূর্ণস্ক্রিনে দেখুন">
          <nt-math-lab mode="@@LAB_MODE@@"></nt-math-lab>
        </b1b-fullscreen>
      </b1b-section>

    </b1b-article>
  </div>

  <b1b-watch-panel
    video-src="../../media_vault/number_theory/lesson_@@NN@@/experiments/3b1b_number_theory_@@NN@@_full_dubbed.mp4"
    yt-id="@@YT@@"
    title="@@TITLE@@ — অধ্যায় @@BN@@"
    subtitle="সম্পূর্ণ প্রমিত বাংলায় ডাব করা, EBU R128 লাউডনেস নরমালাইজড অডিও এবং জিরো ইংলিশ ভোকাল ব্লিড মোড সহ।"
    playlist-title="📋 প্লেলিস্ট — সংখ্যা তত্ত্ব">
  </b1b-watch-panel>

</div>

<b1b-chapter-nav
  prev-url="@@PREV@@"
  prev-title="@@PREV_TITLE@@"
  prev-dir="পূর্ববর্তী অধ্যায়"
  next-url="@@NEXT@@"
  next-title="@@NEXT_TITLE@@"
  next-dir="পরবর্তী অধ্যায়">
</b1b-chapter-nav>

<b1b-footer></b1b-footer>
<b1b-back-to-top></b1b-back-to-top>

<!-- Page-specific interactive lab component (NEW element; no library override) -->
<script>
(function () {
  if (customElements.get('nt-math-lab')) return;
  class NtMathLab extends HTMLElement {
    connectedCallback() {
      if (this.dataset.rendered) return;
      this.dataset.rendered = 'true';
      const mode = this.getAttribute('mode') || 'spiral';
      this.innerHTML =
        '<div style="background:#0e1622;border:1px solid #27364a;border-radius:12px;padding:14px;color:#dbe7f3">' +
          '<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px">' +
            '<label style="font-size:13px">N = <input type="range" min="20" max="320" value="140" ' +
              'style="width:180px;vertical-align:middle"/><b class="val" style="color:#ffd166">140</b></label>' +
            '<button class="replay" style="padding:6px 12px;border-radius:8px;border:1px solid #4361ee;' +
              'background:#16233a;color:#dbe7f3;cursor:pointer">🔄 পুনরাঙ্কন</button>' +
          '</div>' +
          '<canvas width="640" height="360" style="width:100%;height:auto;background:#0a1018;border-radius:8px"></canvas>' +
          '<p class="hint" style="font-size:12px;color:#8fa6bf;margin:8px 0 0"></p>' +
        '</div>';
      const range = this.querySelector('input');
      const val = this.querySelector('.val');
      const canvas = this.querySelector('canvas');
      const hint = this.querySelector('.hint');
      const ctx = canvas.getContext('2d');
      const draw = () => {
        const n = +range.value;
        val.textContent = n;
        ctx.clearRect(0, 0, 640, 360);
        ctx.strokeStyle = '#1d2939';
        ctx.lineWidth = 1;
        for (let x = 0; x <= 640; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 360); ctx.stroke(); }
        for (let y = 0; y <= 360; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(640, y); ctx.stroke(); }
        ctx.save();
        ctx.translate(320, 180);
        const prime = (k) => { if (k < 2) return false; for (let d = 2; d * d <= k; d++) if (k % d === 0) return false; return true; };
        if (mode === 'spiral') {
          ctx.strokeStyle = '#8afdff'; ctx.lineWidth = 1.4; ctx.beginPath();
          for (let i = 0; i < 240; i++) {
            const r = 2 + i * 0.62, a = i * 0.31;
            const x = r * Math.cos(a), y = r * Math.sin(a);
            if (!i) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          }
          ctx.stroke();
          ctx.fillStyle = '#ffd166';
          for (let p = 2; p <= n; p++) {
            if (!prime(p)) continue;
            const r = 1.6 + p * 0.62, a = p * 0.31;
            ctx.beginPath(); ctx.arc(r * Math.cos(a), r * Math.sin(a), 2.2, 0, 7); ctx.fill();
          }
          hint.textContent = 'হলুদ বিন্দুগুলো মৌলিক সংখ্যা। N বাড়ালে আর্কিমিডিয় সর্পিলের ওপর নতুন বাহু ও রশ্নি ফুটে ওঠে।';
        } else if (mode === 'triples') {
          let shown = 0;
          ctx.font = '12px sans-serif';
          for (let m = 2; m <= 26 && shown < n / 6; m++) {
            for (let k = 1; k < m; k++) {
              if ((m - k) % 2 === 0) continue;
              const g = (a, b) => b ? g(b, a % b) : a;
              if (g(m, k) !== 1) continue;
              const a = m * m - k * k, b = 2 * m * k, c = m * m + k * k;
              const s = 150 / c;
              ctx.strokeStyle = '#8afdff'; ctx.lineWidth = 1;
              ctx.beginPath(); ctx.moveTo(-b * s, a * s); ctx.lineTo(0, 0); ctx.lineTo(b * s, 0); ctx.lineTo(-b * s, a * s); ctx.stroke();
              ctx.fillStyle = '#ffd166';
              ctx.fillText(a + ',' + b + ',' + c, -b * s + 4, a * s - 4);
              if (++shown > 28) break;
            }
          }
          hint.textContent = 'প্রতিটি ত্রিভুজ (m²−k², 2mk, m²+k²) সূত্র থেকে এসেছে — m ও k বিজোড়-জোড় ভিন্ন এবং সহ-মৌলিক।';
        } else {
          const target = Math.PI / 4;
          const pts = [];
          let sum = 0;
          for (let i = 0; i < n; i++) {
            sum += (i % 2 ? -1 : 1) / (2 * i + 1);
            pts.push(sum);
          }
          ctx.strokeStyle = '#ffd166'; ctx.setLineDash([5, 5]); ctx.beginPath();
          ctx.moveTo(-280, -target * 160); ctx.lineTo(280, -target * 160); ctx.stroke();
          ctx.setLineDash([]);
          ctx.strokeStyle = '#8afdff'; ctx.lineWidth = 1.6; ctx.beginPath();
          pts.forEach((v, i) => { const x = -280 + i * (560 / pts.length), y = -v * 160; if (!i) ctx.moveTo(x, y); else ctx.lineTo(x, y); });
          ctx.stroke();
          ctx.fillStyle = '#ffd166'; ctx.font = '13px sans-serif';
          ctx.fillText('π/4 ≈ 0.785398', -270, -target * 160 - 8);
          hint.textContent = 'আংশিক যোগফল π/4-এর ওপর দিয়ে দোলা খেয়ে ক্রমশ কাছে আসছে — এটি লাইবনিটজের ধারা।';
        }
        ctx.restore();
      };
      range.addEventListener('input', draw);
      this.querySelector('.replay').addEventListener('click', draw);
      draw();
    }
  }
  customElements.define('nt-math-lab', NtMathLab);
})();
</script>

</body>
</html>
"""


def render_html(lesson):
    n = lesson["num"]
    nn = "%02d" % n
    bn = ["০১", "০২", "০৩"][n - 1]
    sec_html = []
    for sec in lesson["sections"]:
        sec_html.append(
            '<b1b-section id="%s" title="%s">\n        %s\n      </b1b-section>'
            % (sec["id"], sec["title"], render_blocks(sec, lesson["quizzes"]))
        )
    bookmarks = "\n".join(
        '      <b1b-bookmark time="%d" time-bn="%s">%s</b1b-bookmark>'
        % (b[0], b[1], b[2])
        for b in lesson["bookmarks"]
    )
    toc = "\n".join('      <a href="#%s">%s</a>' % (s["id"], s["title"]) for s in lesson["sections"])
    toc += '\n      <a href="#sec-lab">%s</a>' % lesson["lab"]["title"]
    prev_url = "lesson_%02d.html" % (n - 1) if n > 1 else ""
    next_url = "lesson_%02d.html" % (n + 1) if n < 3 else ""
    if n == 1:
        prev_title = "পূর্ববর্তী অধ্যায় নেই"
    else:
        prev_title = lesson["prev_title"]
    next_title = lesson["next_title"] if n < 3 else "শেষ অধ্যায়"

    repl = {
        "@@TITLE@@": lesson["title_bn"] + " | " + lesson["title_en"],
        "@@NN@@": nn,
        "@@BN@@": bn,
        "@@DESC@@": lesson["subtitle_bn"],
        "@@YT@@": lesson["yt"],
        "@@DATE@@": lesson["date"],
        "@@GITHUB@@": lesson["github"],
        "@@BOOKMARKS@@": bookmarks,
        "@@TOC@@": toc,
        "@@SECTIONS@@": "\n\n      ".join(sec_html),
        "@@LAB_TITLE@@": lesson["lab"]["title"],
        "@@LAB_DESC@@": lesson["lab"]["desc"],
        "@@LAB_MODE@@": lesson["lab"]["mode"],
        "@@PREV@@": prev_url,
        "@@PREV_TITLE@@": prev_title,
        "@@NEXT@@": next_url,
        "@@NEXT_TITLE@@": next_title,
    }
    out = HTML_TEMPLATE
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def render_index(lessons):
    cards = []
    for l in lessons:
        nn = "%02d" % l["num"]
        cards.append(
            '        <a class="course-card" href="lesson_%s.html">\n'
            '          <div class="course-card-thumb"><img src="https://img.youtube.com/vi/%s/hqdefault.jpg" '
            'alt="%s" loading="lazy"/></div>\n'
            '          <div class="course-card-body">\n'
            '            <span class="course-card-num">অধ্যায় %s</span>\n'
            '            <h3>%s</h3>\n'
            '            <p>%s</p>\n'
            '            <span class="course-card-cta">পড়ুন ও শুনুন →</span>\n'
            '          </div>\n'
            '        </a>' % (nn, l["yt"], l["title_bn"], ["০১", "০২", "০৩"][l["num"] - 1],
                             l["title_bn"], l["subtitle_bn"])
        )
    return r"""<!DOCTYPE html>
<html lang="bn" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<script>(function(){const t=localStorage.getItem('3b1b-theme')||'dark';document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');else document.documentElement.classList.remove('dark');})();</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>সংখ্যা তত্ত্ব — 3Blue1Brown বাংলা</title>
<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>
<link rel="stylesheet" href="../../assets/css/main.css"/>
<link rel="stylesheet" href="../../assets/css/lesson.css"/>
</head>
<body class="mode-read">
<b1b-search-overlay></b1b-search-overlay>
<b1b-navbar course-title="সংখ্যা তত্ত্ব" course-url="index.html" home-url="../../index.html"
  chapter-num="০১" chapter-total="০৩" active-mode="read"></b1b-navbar>
<main class="course-index">
  <header class="course-index-hero">
    <p class="eyebrow">3BLUE1BROWN · NUMBER THEORY</p>
    <h1>সংখ্যা তত্ত্ব</h1>
    <p>মৌলিক সংখ্যার সর্পিল, পিথাগোরীয় ট্রিপল এবং পাই-এর লুকোন নিয়মিততা — তিনটি অধ্যায়ে সম্পূর্ণ বাংলা ডাবিং, ইন্টারেক্টিভ ল্যাব ও কুইজ সহ।</p>
  </header>
  <section class="course-grid">
@@CARDS@@
  </section>
</main>
<script defer src="../../assets/libs/katex/katex.min.js"></script>
<script defer src="../../assets/libs/katex/auto-render.min.js"></script>
<script defer src="../../assets/libs/katex-stub.js"></script>
<script defer src="../../assets/js/lesson_components.js"></script>
<script defer src="../../assets/js/lesson_components_extended.js"></script>
<script defer src="../../assets/js/main.js"></script>
<script defer src="../../assets/js/lesson.js"></script>
<b1b-footer></b1b-footer>
</body>
</html>
""".replace("@@CARDS@@", "\n".join(cards))


# =========================================================================== #
# LESSON 01 — prime-spirals
# =========================================================================== #
L1_QUIZZES = {
    "q_polar": {
        "question": "❓ বিন্দু (3, 7π/2)-এর সমান নয় — এমন বিন্দু কোনটি? (Which other point in polar coordinates does this point not equal?)",
        "options": [
            r"$(3, \frac{3\pi}{2})$",
            r"$(-3, \frac{5\pi}{2})$",
            r"$(3, -\frac{\pi}{2})$",
            r"$(3, \frac{5\pi}{2})$",
        ],
        "correct": 3,
        "correct_msg": "চমৎকার! 7π/2 = 2π + 3π/2, তাই একই জায়গা (3, 3π/2) ও (3, −π/2)। (−3, 5π/2)-ও একই বিন্দু, কারণ ঋণাত্মক r কোণে π যোগ করার সমান। কিন্তু (3, 5π/2) = (3, π/2) — উপরের দিকে, ভিন্ন বিন্দু।",
        "wrong-msg": "",
        "wrong_msg": "মনে রেখো: কোণে 2π যোগ করলে বিন্দু একই থাকে; r ঋণাত্মক হলে কোণে π যোগ করতে হয়। 7π/2 কে 2π + 3π/2 হিসেবে ভাবো।",
        "reveal_msg": "সঠিক উত্তর (3, 5π/2) — এটি (3, π/2), অর্থাৎ ঊর্ধ্ব অক্ষে অবস্থিত, বাকিগুলো নিচের অক্ষে।",
    },
    "q_mod6": {
        "question": "❓ ৩৮১ সংখ্যাটি মডুলো 6-এর কোন অবশিষ্ট শ্রেণির?",
        "options": [r"$6k+0$", r"$6k+1$", r"$6k+2$", r"$6k+3$", r"$6k+4$", r"$6k+5$"],
        "correct": 3,
        "correct_msg": "ঠিক! 381 ÷ 6 = 63 ভাগশেষ 3, অর্থাৎ 381 = 6×63 + 3। তাই এটি 6k+3 শ্রেণির — আর 3 দিয়ে বিভাজ্য হওয়ায় এটি মৌলিকও নয়।",
        "wrong_msg": "6 দিয়ে ভাগ করে ভাগশেষ বের করো: 381 = 6 × 63 + 3।",
        "reveal_msg": "সঠিক উত্তর 6k+3।",
    },
    "q_bin71": {
        "question": "❓ বৃহত্তর সর্পিলে (r mod 710) ৭১-তম হিস্টোগ্রাম বিনে কতটি মৌলিক সংখ্যা পড়বে?",
        "options": ["কেবল একটি", "প্রায় ২৮০টি", "কোনোটিই নয়", "অসংখ্য"],
        "correct": 0,
        "correct_msg": "হ্যাঁ! 71 হলো 710-এর একটি উৎপাদক। 71 নিজে ওই বিনে পড়ে, কিন্তু 71-এর পরবর্তী প্রতিটি 710k+71 সংখ্যা 71 দিয়ে বিভাজ্য — তাই আর কোনো মৌলিক নয়।",
        "wrong_msg": "710 = 2 × 5 × 71। যে শ্রেণির অবশিষ্ট 71 দিয়ে বিভাজ্য, সেখানে 71 ছাড়া অন্য কোনো মৌলিক থাকতে পারে না।",
        "reveal_msg": "সঠিক উত্তর: কেবল একটি (71 নিজে)।",
    },
    "q_quadrant": {
        "question": "❓ 710k+60 শ্রেণিটি ওপরের ছবিতে কোন চতুর্ভুজে দেখা যাবে?",
        "options": ["১ম (উপর-ডানে)", "২য় (উপর-বাঁয়ে)", "৩য় (নিচ-বাঁয়ে)", "৪র্থ (নিচ-ডানে)"],
        "correct": 2,
        "correct_msg": "সঠিক! 710 রেডিয়ান প্রায় 113 পূর্ণ ঘুরনি, তাই 710k রশ্নি প্রায় x-অক্ষে। বাকি 60 রেডিয়ান = 60 − 9(2π) ≈ 3.45 রেডিয়ান ≈ 198°, অর্থাৎ ৩য় চতুর্ভুজ (নিচ-বাঁয়ে)।",
        "wrong_msg": "60 কে 2π দিয়ে ভাগ করো: 60 ≈ 9 × 2π + 3.45। 3.45 রেডিয়ান π-এর চেয়ে বড় কিন্তু 3π/2-এর চেয়ে ছোট।",
        "reveal_msg": "সঠিক উত্তর: ৩য় চতুর্ভুজ (নিচ-বাঁয়ে)।",
    },
    "q_limit": {
        "question": r"❓ $\lim_{x\to\infty}\frac{\pi(x;6,1)}{\pi(x)}$ এর মান কত?",
        "options": [r"$\frac{1}{2}$", r"$\frac{1}{3}$", r"$\frac{1}{4}$", r"$\frac{1}{5}$", r"$\frac{1}{6}$"],
        "correct": 0,
        "correct_msg": "চমৎকার! φ(6) = 2 (কেবল 1 ও 5 ছয়ের সাথে সহ-মৌলিক), তাই অনুপাত 1/φ(6) = 1/2। 2 ও 3 ছাড়া সব মৌলিক 6k+1 বা 6k+5 আকারের।",
        "wrong_msg": "ডিরিখলের সূত্রে অনুপাত = 1/φ(N)। φ(6) বের করো — 1 থেকে 6-এর মধ্যে 6-এর সাথে সহ-মৌলিক সংখ্যা কয়টি?",
        "reveal_msg": r"সঠিক উত্তর $\frac{1}{2}$।",
    },
}

L1 = {
    "num": 1,
    "slug": "prime-spirals",
    "yt": "EK32jo7i5LQ",
    "date": "৮ অক্টোবর, ২০১৯",
    "github": "https://github.com/3b1b/videos/blob/master/_2019/spirals.py",
    "title_bn": "কেন মৌলিক সংখ্যা এই সর্পিল তৈরি করে?",
    "title_en": "Why do prime numbers make these spirals?",
    "subtitle_bn": "ধ্রুবক-নির্দেশক অঙ্কন, অবশিষ্ট শ্রেণি, ইউলারের টোশিয়েন্ট ফাংশন ও ডিরিখলের উপপাদ্য",
    "prev_title": "",
    "next_title": "পরবর্তী অধ্যায়: সমস্ত পিথাগোরীয় ট্রিপল",
    "epigraph": {
        "quote": "The role primes play in math is similar to the role atoms play in chemistry.",
        "quote_bn": "গণিতে মৌলিক সংখ্যার ভূমিকা রসায়নে পরমাণুর মতো।",
        "author": "গ্রান্ট স্যান্ডারসন",
    },
    "bookmarks": [
        (0, "০০:০০", "মৌলিক সংখ্যা ও মেরু-নির্দেশক"),
        (95, "০১:৩৫", "(p, p) বিন্দু ও আর্কিমিডিয় সর্পিল"),
        (260, "০৪:২০", "ছয়ের সর্পিল ও অবশিষ্ট শ্রেণি"),
        (450, "০৭:৩০", "ইউলারের টোশিয়েন্ট ও ৭১০ রশ্নি"),
        (640, "১০:৪০", "ডিরিখলের উপপাদ্য"),
        (800, "১৩:২০", "উলাম সর্পিল ও 3D অন্বেষণ"),
    ],
    "lab": {
        "title": "ইন্টারেক্টিভ ল্যাব — মৌলিক সর্পিল",
        "desc": "স্লাইডার ঘুরিয়ে N বাড়াও এবং মেরু-নির্দেশক তলে মৌলিক সংখ্যাগুলোর অবস্থান পর্যবেক্ষণ করো। সরল বাহু আর ফাঁকা রশ্নিগুলো কীভাবে তৈরি হয় তা নিজে দেখো।",
        "mode": "spiral",
    },
    "quizzes": L1_QUIZZES,
    "sections": [
        {
            "id": "sec-polar-plots",
            "title": "মেরু-নির্দেশক ও (p, p) বিন্দু",
            "blocks": [
                P("কেন গণিতবিদরা মৌলিক সংখ্যা নিয়ে এত আগ্রহী? কারণ গুণনের ক্ষেত্রে এগুলোই পূর্ণসংখ্যার মৌলিক বিল্ডিং ব্লক, এবং অনেক সমস্যা আগে মৌলিক সংখ্যার জন্য সমাধান করে তারপর সাধারণীকরণ করা যায়। কিন্তু সত্যি বলতে, মৌলিক সংখ্যা কঠিন হওয়াতেই এর প্রতি আকর্ষণ অনেক বেশি — এদের নিয়ে অসংখ্য অমীমাংসিত সমস্যা রয়েছে।",
                  "কেন গণিতবিদরা মৌলিক সংখ্যা নিয়ে এত আগ্রহী? গুণনের ক্ষেত্রে এগুলোই পূর্ণসংখ্যার মৌলিক বিল্ডিং ব্লক। আরও বড় কথা, এগুলো কঠিন — মৌলিক সংখ্যা নিয়ে অসংখ্য অমীমাংসিত সমস্যা আছে।"),
                Q("সংখ্যাকে স্থানাঙ্ক হিসেবে উপস্থাপন করা একটি সহিংস কাজ।", "হের্মান ওয়াইল",
                  "উদ্ধৃতি, সংখ্যাকে স্থানাঙ্ক হিসেবে উপস্থাপন করা একটি সহিংস কাজ। বলেছেন হের্মান ওয়াইল।"),
                P("মেরু-নির্দেশক ব্যবস্থায় কোনো বিন্দুকে xy-স্থানাঙ্ক দিয়ে নয়, বরং মূলবিন্দু থেকে দূরত্ব r এবং অনুভূমিক রেখার সাথে কোণ θ দিয়ে চিহ্নিত করা হয়। কোণ সাধারণত রেডিয়ানে মাপা হয় — π মানে আধা ঘুরনি, 2π মানে এক পূর্ণ চক্কর। একই বিন্দুর একাধিক মেরু-নির্দেশক থাকতে পারে, কারণ কোণে 2π যোগ করলে অবস্থান বদলায় না।",
                  "মেরু-নির্দেশক ব্যবস্থায় বিন্দুকে দূরত্ব r আর কোণ θ দিয়ে চিহ্নিত করা হয়। কোণ রেডিয়ানে মাপা হয়, π মানে আধা ঘুরনি আর 2π মানে পূর্ণ চক্কর। কোণে 2π যোগ করলে বিন্দু একই থাকে।"),
                F(spiral_svg(), "মূলবিন্দু থেকে শুরু হওয়া সর্পিল: প্রতি ধাপে কোণ বাড়ে ১ রেডিয়ান এবং দূরত্ব বাড়ে ১ একক — একে আর্কিমিডিয় সর্পিল বলে। ছবিতে কেন্দ্রের কাছে বিন্দুগুলো ঘন আর বাইরের দিকে ক্রমশ ছড়িয়ে যাচ্ছে তা লক্ষ্য করো। এই গঠনই পুরো অধ্যায়ের ভিত্তি।",
                  "ছবিতে মূলবিন্দু থেকে শুরু হওয়া একটি সর্পিল দেখা যাচ্ছে। প্রতি ধাপে কোণ বাড়ে এক রেডিয়ান আর দূরত্ব বাড়ে এক একক, তাই বিন্দুগুলো ঘুরতে ঘুরতে বাইরের দিকে এগিয়ে যায়। এই আর্কিমিডিয় সর্পিল বোঝা ছাড়া পরের কোনো প্যাটার্ন বোঝা যাবে না।"),
                Z("q_polar"),
                P("এখন এমন সব বিন্দু অঙ্কন করি যাদের r ও θ উভয়ই একই মৌলিক সংখ্যা p — অর্থাৎ (r, θ) = (p, p)। প্রথমে সব পূর্ণসংখ্যা নিয়ে দেখি: (1,1) মূলবিন্দু থেকে ১ একক দূরে ১ রেডিয়ান কোণে, (2,2) দ্বিগুণ দূরত্বে দ্বিগুণ কোণে, (3,3) আরও এক রেডিয়ান ঘুরে। প্রতি ধাপই ঘড়ির কাঁটার মতো ১ রেডিয়ান ঘোরে আর এক একক লম্বা হয়।",
                  "এখন অঙ্কন করি (p, p) বিন্দু, অর্থাৎ দূরত্ব আর কোণ দুটোই একই মৌলিক সংখ্যা। আগে সব পূর্ণসংখ্যা নিয়ে দেখি: প্রতি ধাপে এক রেডিয়ান ঘোরে আর এক একক লম্বা হয়।"),
                F(spiral_svg(0.31, 150), "প্রতিটি ধাপ ১ রেডিয়ান — এক-ষষ্ঠ ঘুরনিরও কম — এবং ১ একক বৃদ্ধি পায়। বাইরের দিকে বিন্দুগুলো মসৃণ বক্ররেখা তৈরি করে, যার নাম আর্কিমিডিয় সর্পিল। মনে রেখো, সর্পিলটি মৌলিক সংখ্যার কারণে নয়, পূর্ণসংখ্যার ক্রমের কারণেই তৈরি হয়।",
                  "এই ছবিতে দেখা যাচ্ছে প্রতি ধাপ ১ রেডিয়ান ঘোরে আর এক একক বাড়ে। ফলে বাইরের দিকে বিন্দুগুলো মসৃণ বক্ররেখা গড়ে তোলে — একে আর্কিমিডিয় সর্পিল বলে। মনে রাখতে হবে এই সর্পিল মৌলিক সংখ্যার কারণে নয়, পূর্ণসংখ্যার ক্রমের কারণেই তৈরি।"),
                P("এবার কেবল মৌলিক সংখ্যাগুলো রেখে বাকিগুলো বাদ দিই। প্রথমে সবই এলোমেলো মনে হয় — স্বাভাবিকই, মৌলিক সংখ্যা তো অপ্রত্যাশিত আচরণের জন্য বিখ্যাত। কিন্তু যখনই আমরা দূরে সরে ছবিটা বড় করে দেখি, স্পষ্ট গ্যালাক্সি-মতো সর্পিল বাহু ফুটে ওঠে; আবার তারও বাইরে সরল রশ্নিরা দেখা যায়, প্রায় চারটির গুচ্ছে, মাঝে মাঝে একটি ???? বাদ পড়ে। মৌলিক সংখ্যা থেকে ২০টি সর্পিল আর ২৮০টি রশ্নি গণনা করা যায়।",
                  "এবার শুধু মৌলিক সংখ্যা রেখে বাকি বাদ দিই। কাছ থেকে সব এলোমেলো মনে হলেও দূরে সরে দেখলে স্পষ্ট গ্যালাক্সির মতো সর্পিল বাহু আর তার ওপরে সরল রশ্নি দেখা যায়। রশ্নিগুলো প্রায় চারটির গুচ্ছে আসে, মাঝে মাঝে একটির ফাঁক থাকে। গণনা করলে ২০টি সর্পিল আর ২৮০টি রশ্নি পাওয়া যায়।"),
                F(rays_svg(20), "দূরে সরে দেখলে সর্পিলের বদলে সরল রশ্নিরা ফুটে ওঠে — প্রায় ২০টি বাহু এখানে দেখানো হয়েছে। রশ্নিগুলো কেন চার চার করে আসে এবং কেন কয়েকটির ???? বাদ পড়ে, সেই প্রশ্নই আমাদের অবশিষ্ট শ্রেণির দিকে নিয়ে যাবে। ছবির প্রতিটি রশ্নি আসলে একেকটি গাণিতিক শ্রেণির প্রতীক।",
                  "দূরে সরে দেখলে সর্পিলের বদলে সরল রশ্নি ফুটে ওঠে, এখানে প্রায় কুড়িটি বাহু দেখানো হয়েছে। রশ্নিগুলো কেন চার চার করে আসে আর কেন কয়েকটির ???? বাদ পড়ে — এই প্রশ্নই আমাদের অবশিষ্ট শ্রেণির দিকে নিয়ে যাবে। প্রতিটি রশ্নি একেকটি গাণিতিক শ্রেণির প্রতীক।"),
            ],
        },
        {
            "id": "sec-residue-spirals",
            "title": "ছয়ের সর্পিল ও অবশিষ্ট শ্রেণি",
            "blocks": [
                P(" ছোট স্কেলে আগে ৬টি ছোট সর্পিল দেখা যায় — ৬-এর গুণিতকগুলো এক বাহু তৈরি করে, তারপর ৬-এর গুণিতকের ১ বেশি সংখ্যারা দ্বিতীয় বাহু, ২ বেশি সংখ্যারা তৃতীয় বাহু, ইত্যাদি। কারণ হলো প্রতি ধাপে ১ রেডিয়ান ঘোরে, তাই ৬ ধাপে মোট ৬ রেডিয়ান ঘোরে — যা 2π-এর কাছাকাছি, অর্থাৎ প্রায় এক পূর্ণ চক্কর। প্রতিবার ৬ করে এগোলে কোণ খুব কম বদলায়, তাই মনে হয় যেন একটিমাত্র বাঁকা রেখা।",
                  "ছোট স্কেলে ৬টি সর্পিল দেখা যায়। ৬-এর গুণিতকেরা এক বাহু, ১ বেশি সংখ্যারা দ্বিতীয় বাহু। কারণ ৬ ধাপে ৬ রেডিয়ান ঘোরে, যা 2π-এর কাছাকাছি — প্রায় এক পূর্ণ চক্কর। তাই কোণের সামান্য পরিবর্তনে মনে হয় একটিমাত্র বাঁকা রেখা।"),
                F(spiral_svg(6 * 0.31 / 6 * 1.0, 120), "এখানে ৬টি বাহু স্পষ্ট — প্রতিটি বাহুই একটি নির্দিষ্ট ভাগশেষের সংখ্যা নিয়ে গঠিত। ৬ ধাপ পরপর নেওয়ার অর্থ হলো একই ভাগশেষ বারবার পাওয়া; কোণ প্রায় এক চক্কর হওয়ায় ওই বিন্দুগুলো একই রশ্নির ওপর পড়ে। এই সরল পর্যবেক্ষণটিই বড় প্যাটার্নের চাবিকাঠি।",
                  "এই ছবিতে ৬টি বাহু স্পষ্ট, প্রতিটি এক নির্দিষ্ট ভাগশেষের সংখ্যা নিয়ে গঠিত। ছয় ধাপ পরপর নেওয়ার অর্থ একই ভাগশেষ বারবার পাওয়া; কোণ প্রায় এক চক্কর হওয়ায় ওই বিন্দুগুলো একই রশ্নিতে পড়ে। এই সরল পর্যবেক্ষণই বড় প্যাটার্নের চাবিকাঠি।"),
                P("মৌলিক সংখ্যার দিকে নজর দিলে এই ছয়টি বাহুর মধ্যে কেবল দুটি বেঁচে থাকে। মৌলিক সংখ্যা ৬-এর গুণিতক হতে পারে না; ৬k+২ ও ৬k+৪ আকারের সংখ্যা সবই জোড়, আর ৬k+৩ আকারের সবই ৩ দিয়ে বিভাজ্য। কেবল ৬k+১ ও ৬k+৫ তে মৌলিক সংখ্যা পড়তে পারে (ব্যতিক্রম ২ ও ৩)।",
                  "মৌলিক সংখ্যার দিকে তাকালে ছয়টি বাহুর মধ্যে কেবল দুটি বেঁচে থাকে। মৌলিক সংখ্যা ছয়ের গুণিতক হতে পারে না; 6k+2 আর 6k+4 সব জোড়, 6k+3 সব ৩ দিয়ে বিভাজ্য। শুধু 6k+1 আর 6k+5-এ মৌলিক পড়তে পারে, ২ ও ৩ ছাড়া।"),
                C("blue", "📌", "অবশিষ্ট শ্রেণি (Residue Class) কী?",
                  "যেসব সংখ্যাকে কোনো N দিয়ে ভাগ করলে একই ভাগশেষ পাওয়া যায়, তাদের নিয়ে একটিমাত্র অবশিষ্ট শ্রেণি গঠিত হয়। 'মডুলো 6' মানে '৬ দিয়ে ভাগের পর'। যেমন ২০ কে ৬ দিয়ে ভাগ করলে ৬ × ৩ + ২ পাই, তাই ২০-এর ভাগশেষ ২ মডুলো ৬; ৬k+2 শ্রেণিতে আছে ২, ৮, ১৪, ২০, ২৬…। গণিতবিদদের এই শব্দটি আসলে '৬-এর গুণিতকের ২ বেশি সংখ্যা' ছাড়া কিছু নয় — কিন্তু নাম থাকলে কথা বলা সুবিধাজনক হয়।",
                  "বিশেষ নোট, অবশিষ্ট শ্রেণি কী। যেসব সংখ্যাকে কোনো এন দিয়ে ভাগ করলে একই ভাগশেষ পাওয়া যায়, তাদের নিয়ে এক অবশিষ্ট শ্রেণি গঠিত হয়। মডুলো 6 মানে ৬ দিয়ে ভাগের পর। ২০ কে ৬ দিয়ে ভাগ করলে ভাগশেষ ২, তাই ২০ হলো 6k+2 শ্রেণির। এই শব্দটি আসলে ৬-এর গুণিতকের ২ বেশি সংখ্যা ছাড়া কিছু নয়।"),
                M(r"6k+2:\ \{2,8,14,20,26,32,38,\dots\}",
                  "উদাহরণ, দ্বিতীয় অবশিষ্ট শ্রেণি মডুলো ছয়: 6k+2, অর্থাৎ ২, ৮, ১৪, ২০, ২৬, ৩২, ৩৮, ইত্যাদি।"),
                Z("q_mod6"),
                P("একই যুক্তি বড় স্কেলে চলে যায়। ৬ ধাপ প্রায় এক চক্কর হওয়ায় ছয়ের সর্পিল তৈরি হলো; ৪৪ ধাপ অনেক বেশি কাছাকাছি — ৪৪/২π প্রায় ৭.০০, অর্থাৎ ৪৪/৭ হলো 2π-এর কাছাকাছি, যা আমাদের পরিচিত ২২/৭-এর মতোই। ৪৪ ধাপে কোণ প্রায় সাত পূর্ণ ঘুরনি হয়, তাই প্রতিটি বাহু আগেরটির চেয়ে সামান্য কোণে ঘুরে — ফলে আবার একটিমাত্র মৃদু সর্পিল দেখা যায়।",
                  "একই যুক্তি বড় স্কেলেও চলে। ৪৪ ধাপে মোট কোণ ৪৪ রেডিয়ান, যা 2π দিয়ে ভাগ করলে প্রায় ৭ পূর্ণ ঘুরনি — অর্থাৎ ৪৪/৭ হলো 2π-এর কাছাকাছি, ঠিক ২২/৭-এর মতো। তাই বাহুগুলো দেখতে প্রায় সোজা হয়।"),
                M(r"\frac{44}{7}\approx 2\pi\qquad\Longleftrightarrow\qquad \frac{22}{7}\approx\pi",
                  "সূত্র, ৪৪ ভাগ ৭ প্রায় 2π-এর সমান, আর ২২ ভাগ ৭ প্রায় পাই-এর সমান।"),
                F(rays_svg(44, gaps=(0, 2, 4, 6, 8, 11, 22, 33)), " মডুলো 44-এর ৪৪টি অবশিষ্ট শ্রেণির মধ্যে কেবল ২০টি বাহু মৌলিক সংখ্যার জন্য উন্মুক্ত — বাকিগুলো জোড় বা ১১ দিয়ে বিভাজ্য হওয়ায় বাদ পড়ে (চিত্রে কয়েকটি ফাঁক দেখানো হয়েছে)। প্রতিটি বাহু প্রায় সোজা, কারণ ৪৪ ধাপে কোণ প্রায় সাত পূর্ণ চক্কর হয়। ছবিটি মনে রেখো: গাণিতিক শ্রেণিগুলোই জ্যামিতিক বাহুতে রূপ নিচ্ছে।",
                  "মডুলো ৪৪-এর ৪৪টি শ্রেণির মধ্যে কেবল ২০টি বাহু মৌলিক সংখ্যার জন্য উন্মুক্ত, বাকিগুলো জোড় বা ১১ দিয়ে বিভাজ্য — চিত্রে কয়েকটি ফাঁক দেখানো হয়েছে। বাহুগুলো প্রায় সোজা, কারণ ৪৪ ধাপে প্রায় সাত পূর্ণ চক্কর হয়। গাণিতিক শ্রেণি এখানে জ্যামিতিক বাহুতে রূপ নিচ্ছে।"),
            ],
        },
        {
            "id": "sec-totient-710",
            "title": "সহ-মৌলিকতা, টোশিয়েন্ট ও ৭১০ রশ্নি",
            "blocks": [
                P("আগে বলা হয়েছিল, যে বাহুগুলোতে মৌলিক থাকতে পারে সেগুলো হলো — ৪৪-এর সাথে যাদের কোনো সাধারণ উৎপাদক নেই। একে বলা হয় relatively prime বা coprime, অর্থাৎ সহ-মৌলিক। ১ থেকে ৪৪-এর মধ্যে ৪৪-ের সাথে সহ-মৌলিক সংখ্যা আছে ২০টি — একে গণিতের ভাষায় লেখা হয় φ(44) = 20। গ্রিক φ অক্ষরটি ইউলারের টোশিয়েন্ট ফাংশন, যা N-এর সাথে সহ-মৌলিক ১ থেকে N-এর সংখ্যা গণনা করে।",
                  "যে বাহুগুলোতে মৌলিক থাকতে পারে, তাদের সাথে ৪৪-এর কোনো সাধারণ উৎপাদক নেই — একে বলা হয় সহ-মৌলিক। ১ থেকে ৪৪-এর মধ্যে এরকম ২০টি সংখ্যা আছে, লেখা হয় φ(44) = ২০। গ্রিক ফাই অক্ষরটি ইউলারের টোশিয়েন্ট ফাংশন।"),
                M(r"\phi(44)=20,\qquad \phi(10)=|\{1,3,7,9\}|=4",
                  "সূত্র, ফাই অব ৪৪ সমান কুড়ি, আর ফাই অব ১০ সমান চার কারণ ১, ৩, ৭, ৯ সংখ্যাগুলো ১০-এর সাথে সহ-মৌলিক।"),
                P("আরও বাইরে ৭১০ রেডিয়ান অসাধারণভাবে পূর্ণ ঘুরনির কাছে — ৭১০/২π = ১১৩.০০০০০৯, অর্থাৎ ৭১০/১১৩ হলো 2π-এর এক অত্যন্ত ভালো আসন্ন মান, যা ৩৫৫/১১৩-এর সমতুল্য। ফলে ৭১০ ধাপে এগোলে পরের বিন্দুর কোণ আগেরটির প্রায় হুবহু মতো হয়; অনেক দূর পর্যন্ত বিন্দুগুলো সোজা রশ্নিতে পড়ে। কেবল অনেক পরে গিয়ে সামান্য বাঁক দেখা যায় — এটি ৩৫৫/১১৩ কতটা ভালো আসন্ন মান তা প্রমাণ করে।",
                  "আরও বাইরে ৭১০ রেডিয়ান প্রায় পূর্ণ ঘুরনি — ৭১০ ভাগ 2π প্রায় ১১৩.০০০০০৯, অর্থাৎ ৭১০/১১৩ হলো 2π-এর খুব ভালো আসন্ন মান, যা ৩৫৫/১১৩-এর সমান। তাই ৭১০ ধাপে এগোলে কোণ প্রায় অপরিবর্তিত থাকে আর বিন্দুগুলো সোজা রশ্নিতে পড়ে।"),
                M(r"\frac{710}{113}\approx 2\pi\qquad\Longleftrightarrow\qquad \frac{355}{113}\approx\pi",
                  "সূত্র, ৭১০ ভাগ ১১৩ প্রায় 2π, আর ৩৫৫ ভাগ ১১৩ প্রায় পাই — একটি বিখ্যাত ও অসাধারণ নিখুঁত আসন্ন মান।"),
                F(rays_svg(24, gaps=(1, 3, 5, 17, 19)), " এখানে রশ্নিগুলো প্রায় চারটির গুচ্ছে এসেছে, মাঝে মাঝে এক ???? বাদ পড়েছে — ঠিক যেমনটি মূল প্রশ্নে দেখা গিয়েছিল। কারণ হলো ৭১০ = ২ × ৫ × ৭১: জোড় শ্রেণি বাদ, তারপর ৫ দিয়ে বিভাজ্য শ্রেণি বাদ (প্রতি পঞ্চম রশ্নি), এবং শেষে ৭১ দিয়ে বিভাজ্য চারটি শ্রেণি বাদ। ছবিতে প্রতিটি ফাঁকের পেছনে একটি উৎপাদক আছে।",
                  "এখানে রশ্নিগুলো প্রায় চারটির গুচ্ছে এসেছে, মাঝে মাঝে একটি ???? বাদ পড়েছে — ঠিক যেমনটি মূল প্রশ্নে দেখা গিয়েছিল। কারণ ৭১০ = ২ × ৫ × ৭১: জোড় শ্রেণি বাদ, তারপর পাঁচ দিয়ে বিভাজ্য শ্রেণি বাদ, শেষে ৭১ দিয়ে বিভাজ্য চারটি শ্রেণি বাদ। প্রতিটি ফাঁকের পেছনে একটি উৎপাদক আছে।"),
                Z("q_bin71"),
                Z("q_quadrant"),
                P("তাহলে ২৮০ সংখ্যাটি কোথা থেকে এলো? ১ থেকে ৭১০-এর মধ্যে ৭১০-এর সাথে সহ-মৌলিক সংখ্যার সংখ্যা itself φ(710) = 280। অর্থাৎ ২৮০টি শ্রেণিকে আমরা শুধু বিভাজ্যতা দিয়ে বাতিল করতে পারি না — বাকি শ্রেণিগুলোতে মৌলিক থাকতে পারে। ছবিতে দেখা যায় মৌলিকগুলো এই ২৮০টি শ্রেণির মধ্যে বেশ সমানভাবে ছড়িয়ে আছে; প্রতিটি বর্ণ একটি শ্রেণিকে নির্দেশ করে। এই 'সমান বণ্টন'-ই ডিরিখলের উপপাদ্যের মূল বিষয়।",
                  "২৮০ সংখ্যাটি কোথা থেকে এলো? ১ থেকে ৭১০-এর মধ্যে ৭১০-এর সাথে সহ-মৌলিক সংখ্যা φ(710) = ২৮০। অর্থাৎ ২৮০টি শ্রেণিকে শুধু বিভাজ্যতা দিয়ে বাতিল করা যায় না। ছবিতে দেখা যায় মৌলিকগুলো এই শ্রেণিগুলোর মধ্যে সমানভাবে ছড়িয়ে আছে — এই সমান বণ্টনই ডিরিখলের উপপাদ্যের মূল বিষয়।"),
                M(r"\phi(710)=\phi(2\cdot5\cdot71)=1\cdot4\cdot70=280",
                  "সূত্র, ফাই অব ৭১০ সমান ২, ৫ ও ৭১-এর ফাই-এর গুণফল, অর্থাৎ ১ গুণ ৪ গুণ ৭০ সমান ২৮০।"),
            ],
        },
        {
            "id": "sec-dirichlet",
            "title": "ডিরিখলের উপপাদ্য",
            "blocks": [
                P("সরল এক উদাহরণ নিই — মডুলো ১০। দশমিক পদ্ধতিতে এটি শেষ অঙ্ক অনুযায়ী সংখ্যা ভাগ করার মতো। ২ ছাড়া কোনো মৌলিকের শেষ অঙ্ক জোড় হতে পারে না; ৫ ছাড়া শেষ অঙ্ক ৫-ও হতে পারে না। তাই ৫-এর চেয়ে বড় মৌলিকের শেষ অঙ্ক অবশ্যই ১, ৩, ৭ বা ৯।",
                  "মডুলো ১০ নিয়ে দেখি — এটি শেষ অঙ্ক অনুযায়ী সংখ্যা ভাগ করার মতো। ২ ছাড়া মৌলিকের শেষ অঙ্ক জোড় হতে পারে না, ৫ ছাড়া শেষ অঙ্ক ৫-ও নয়। তাই বড় মৌলিকের শেষ অঙ্ক ১, ৩, ৭ বা ৯।"),
                F(bars_svg([0.25, 0.25, 0.26, 0.24], ["#8afdff", "#ffd166", "#8afdff", "#ffd166"]), " হিস্টোগ্রামে মৌলিক সংখ্যা বাড়ার সাথে সাথে ১, ৩, ৭, ৯ — এই চারটি শেষ অঙ্কের অনুপাত প্রায় ২৫% করে দাঁড়াচ্ছে। অর্থাৎ প্রতিটি অনুমোদিত শ্রেণিতে মৌলিক প্রায় সমানভাবে বণ্টিত। ব্লু ও হলুদ দণ্ডগুলোর দিকে তাকিয়ো: কোনোটিই বেশি দখল করতে পারছে না। এটি দেখতে সহজ, কিন্তু প্রমাণ করা অত্যন্ত কঠিন।",
                  "এই হিস্টোগ্রামে মৌলিক বাড়ার সাথে ১, ৩, ৭, ৯ শেষ অঙ্কের অনুপাত প্রায় ২৫% করে দাঁড়াচ্ছে। অর্থাৎ প্রতিটি অনুমোদিত শ্রেণিতে মৌলিক সমানভাবে বণ্টিত। দণ্ডগুলোর দিকে তাকালে দেখা যায় কোনোটিই বেশি দখল করতে পারছে না — দেখতে সহজ, প্রমাণ করা কঠিন।"),
                P("গণিতবিদরা এই পর্যবেক্ষণকে এভাবে লেখেন: x পর্যন্ত সব মৌলিকের মধ্যে যেগুলো ১ মডুলো ১০, তাদের অনুপাত x-এর অসীমের দিকে যাওয়ার সাথে সাথে ১/৪-এর কাছে পৌঁছায়। সাধারণভাবে N ও r-এর জন্য, যেখানে r আর N সহ-মৌলিক, অনুপাত হয় ১/φ(N)। এখানে π(x) চিহ্নটি পরম পাই নয় — এটি prime-counting function, অর্থাৎ নির্দিষ্ট সীমার নিচে মৌলিক সংখ্যা গণনা করে।",
                  "গণিতবিদরা লেখেন, x পর্যন্ত মৌলিকের মধ্যে ১ মডুলো ১০-এর অনুপাত অসীমে ১/৪-এ পৌঁছায়। সাধারণভাবে এটি ১/φ(এন)। এখানে পাই-চিহ্নটি পরম পাই নয়, বরং মৌলিক-গণনা ফাংশন।"),
                M(r"\lim_{x\to\infty}\frac{\#\{p\le x:\ p\equiv r\ (\mathrm{mod}\ N)\}}{\#\{p\le x\}}=\frac{1}{\phi(N)}",
                  "সূত্র, অসীমের সীমায় মডুলো এন-এর r শ্রেণির মৌলিকের অনুপাত এক ভাগ ফাই অব এন।"),
                Z("q_limit"),
                C("gold", "📜", "ডিরিখলের অবদান (1837)",
                  "উপরের 'সাধারণ' অনুপাতটি প্রমাণ করা কঠিন। ডিরিখল slightly ভিন্ন ঘনত্ব ব্যবহার করেছিলেন — মৌলিক সংখ্যা p-এর 1/p^s যোগ, যেখানে s > 0 এবং s → 1⁺। এই রূপটি গাণিতিকভাবে বেশ সহজে নিয়ন্ত্রণ করা যায়। তার আসল অর্জন ছিল এটি প্রমাণ করা যে, r ও N সহ-মৌলিক হলে ওই শ্রেণিতে অসংখ্য মৌলিক আছে। যেমন '১ দিয়ে শেষ হওয়া অসংখ্য মৌলিক আছে' — এটি প্রমাণ করতে তিনি দেখিয়েছিলেন মোট মৌলিকের এক-চতুর্থাংশই ১ দিয়ে শেষ হয়। প্রমাণে কম্পলেক্স অ্যানালিসিসের গভীর ব্যবহার হয়।",
                  "বিশেষ নোট, ডিরিখলের অবদান। ১৮৩৭ সালে তিনি দেখিয়েছিলেন r ও এন সহ-মৌলিক হলে ওই শ্রেণিতে অসংখ্য মৌলিক আছে। তিনি এক ভিন্ন ঘনত্ব ব্যবহার করেছিলেন — এক_over_p-এর পাওয়ার সাম, যা গাণিতিকভাবে নিয়ন্ত্রণ করা সহজ। প্রমাণে কম্পলেক্স অ্যানালিসিসের গভীর ব্যবহার হয়।"),
            ],
        },
        {
            "id": "sec-conclusion",
            "title": "অনিবার্চিত থেকে গুরুত্বপূর্ণ পর্যন্ত",
            "blocks": [
                P("এখানে একটা কথা বলে রাখা ভালো — মূল ডেটা-ভিজ্যুয়ালাইজেশনের এই খেলাটির কোনো বিশেষ গুরুত্ব নেই। (p, p) বিন্দু অঙ্কন করা স্বাভাবিক কিছু নয়, আর প্রাথমিক রহস্যের বেশিরভাগই এসেছে পূর্ণসংখ্যার রেডিয়ান নিয়ে কাজ করার কারণে। কিন্তু এই রকম খেলা করার ফলে যদি ডিরিখলের উপপাদ্যের মতো গভীর কিছুর পথে পৌঁছানো যায়, তবে তার মূল্য অস্বীকার করা যায় না।",
                  "এখানে বলে রাখি, মূল ডেটা-ভিজ্যুয়ালাইজেশনের এই খেলার কোনো বিশেষ গুরুত্ব নেই। (p, p) বিন্দু অঙ্কন স্বাভাবিক নয়, আর প্রাথমিক রহস্যের বেশিরভাগ এসেছে পূর্ণসংখ্যার রেডিয়ান নিয়ে কাজ থেকে। কিন্তু এই খেলা যদি ডিরিখলের মতো গভীর উপপাদ্যের পথ দেখায়, তবে তার মূল্য আছে।"),
                P("এই প্রশ্নটিকে 3D-তে নিয়ে যাওয়া যায় — গোলীয় নির্দেশক ব্যবস্থায় বিন্দু হলো (p cos p sin p, p sin²p, p cos p)। কয়েক হাজার মৌলিক নিয়ে অঙ্কন করলে 2D-র গ্যালাক্সি আবার দেখা যায়, কিন্তু এখন বাহুগুলো ভেতরে-বাইরে বোনা এক ইনফিনিটি সর্পিলের মতো। ১১ ও ৩৩ শ্রেণি আবার বাদ পড়ে। ছোট প্রশ্নগুলোকে ভেঙে সহজ অংশে ভাগ করেই বড় প্রশ্নের উত্তর খোঁজা হয় — এটি গণিত অন্বেষণের এক সুন্দর শিক্ষা।",
                  "প্রশ্নটিকে 3D-তে নিয়ে যাওয়া যায়। গোলীয় নির্দেশক ব্যবস্থায় কয়েক হাজার মৌলিক অঙ্কন করলে 2D-র গ্যালাক্সি আবার দেখা যায়, কিন্তু বাহুগুলো এখন ভেতরে-বাইরে বোনা ইনফিনিটি সর্পিলের মতো। ১১ ও ৩৩ শ্রেণি আবার বাদ পড়ে। বড় প্রশ্নকে ছোট অংশে ভেঙে বোঝাই গণিত অন্বেষণের শিক্ষা।"),
                F(spiral_svg(0.19, 180, 0.8), " 3D গোলীয় অঙ্কনের 2D প্রক্ষেপণে সর্পিল বাহুগুলো পারস্পরিকভাবে বোনা হয় — যেন এক অসীম সর্পিল গ্যালাক্সি। আগের 2D ছবির চেনা বাহু এখানেও চেনা যায়, কিন্তু গভীরতা যোগ হয়েছে। মনে রেখো, 3D প্যাটার্নটি আগের দুই প্রশ্ন থেকে সম্পূর্ণ আলাদা একটি নতুন প্রশ্ন তুলে ধরে।",
                  "এই ছবিটি 3D গোলীয় অঙ্কনের 2D প্রক্ষেপণ — সর্পিল বাহুগুলো পারস্পরিকভাবে বোনা হয়ে এক অসীম সর্পিল গ্যালাক্সি তৈরি করেছে। আগের 2D ছবির চেনা বাহু এখানেও দেখা যায়, কিন্তু গভীরতা যোগ হয়েছে। এটি আগের প্রশ্নগুলো থেকে সম্পূর্ণ নতুন একটি প্রশ্ন তুলে ধরে।"),
                P("শেষে উলাম সর্পিলের কথা — ১ থেকে শুরু করে সংখ্যাগুলোকে কেন্দ্র থেকে বাইরের দিকে গ্রিডে সর্পিল আকারে লিখে মৌলিকগুলো চার দ্বারা ঘিরে দিলে কিছু তির্যক রেখা ফুটে ওঠে। আমাদের এখানকার সর্পিলের সাথে এটি মিলে না — আমাদেরটি রৈখিক ফাংশন (যেমন 44x+1) থেকে আসে, আর উলাম সর্পিলে দেখা যায় কিছু দ্বিঘাত ফাংশনে মৌলিক বেশি পড়ে। এর সাথে সম্পর্কিত আছে Chebotarev ঘনত্ব উপপাদ্য। অর্থাৎ মৌলিক সংখ্যার ভেতরে অনেক প্যাটার্ন আছে আর গণিতবিদরা সেগুলো অনেকটাই বুঝেছেন — 'অদ্ভুত' হওয়ার খ্যাতি সত্ত্বেও।",
                  "শেষে উলাম সর্পিলের কথা। সংখ্যাগুলোকে কেন্দ্র থেকে বাইরে সর্পিল আকারে লিখে মৌলিক ঘিরলে তির্যক রেখা ফুটে ওঠে। আমাদের সর্পিল রৈখিক ফাংশন থেকে এলেও উলাম সর্পিলে দ্বিঘাত ফাংশনে মৌলিক বেশি পড়ে — এর সাথে Chebotarev ঘনত্ব উপপাদ্য সম্পর্কিত। মৌলিকের ভেতরে অনেক প্যাটার্ন আছে আর গণিতবিদরা সেগুলো বুঝেছেন।"),
            ],
        },
    ],
}


# =========================================================================== #
# LESSON 02 — pythagorean-triples
# =========================================================================== #
L2_QUIZZES = {
    "q_primitive": {
        "question": "❓ নিচের কোনটি একটি আদিম (primitive) পিথাগোরীয় ট্রিপল?",
        "options": ["(6, 8, 10)", "(9, 12, 15)", "(8, 15, 17)", "(10, 24, 26)"],
        "correct": 2,
        "correct_msg": "সঠিক! (8, 15, 17)-এর তিনটি সংখ্যার কোনো সাধারণ উৎপাদক নেই — gc.d = 1। বাকিগুলো (3,4,5), (3,4,5), (5,12,13)-এর গুণিতক।",
        "wrong_msg": "আদিম মানে তিনটি সংখ্যার gc.d = 1। 6,8,10 কে 2 দিয়ে ভাগ করা যায়; 9,12,15 কে 3 দিয়ে; 10,24,26 কে 2 দিয়ে।",
        "reveal_msg": "সঠিক উত্তর (8, 15, 17) — এটি মূল ট্রিপল, অন্যগুলো এর গুণিতক।",
    },
    "q_euclid": {
        "question": "❓ ইউক্লিডের সূত্রে m = 2, n = 1 বসালে কোন ট্রিপল পাওয়া যায়?",
        "options": ["(3, 4, 5)", "(5, 12, 13)", "(8, 15, 17)", "(7, 24, 25)"],
        "correct": 0,
        "correct_msg": "চমৎকার! a = m²−n² = 4−1 = 3, b = 2mn = 4, c = m²+n² = 5। পাওয়া গেল পরিচিত ৩-৪-৫ ত্রিভুজ।",
        "wrong_msg": "সূত্রটি মনে রেখো: a = m² − n², b = 2mn, c = m² + n²। m = 2, n = 1 বসিয়ে হিসাব করো।",
        "reveal_msg": "সঠিক উত্তর (3, 4, 5)।",
    },
    "q_m3n2": {
        "question": "❓ m = 3, n = 2-এর জন্য ইউক্লিডের সূত্র থেকে কী পাওয়া যায়?",
        "options": ["(5, 12, 13)", "(8, 15, 17)", "(7, 24, 25)", "(20, 21, 29)"],
        "correct": 0,
        "correct_msg": "ঠিক! 3²−2² = 5, 2×3×2 = 12, 3²+2² = 13 — অর্থাৎ ৫-১২-১৩ ত্রিভুজ, যা আমরা পরিচিত ত্রিভুজ হিসেবে জানতাম।",
        "wrong_msg": "m = 3, n = 2 বসাও: 9−4 = 5, 12, 9+4 = 13।",
        "reveal_msg": "সঠিক উত্তর (5, 12, 13)।",
    },
    "q_mod4": {
        "question": "❓ কোন মৌলিক সংখ্যাটি দুটি পূর্ণবর্গের যোগফল হিসেবে লেখা যায়?",
        "options": ["7", "11", "13", "19"],
        "correct": 2,
        "correct_msg": "সঠিক! 13 = 4 + 9 = 2² + 3²। 7, 11, 19 — তিনটিই 4k+3 আকারের মৌলিক, যেগুলো কখনো দুই বর্গের যোগফল হতে পারে না।",
        "wrong_msg": "4k+3 আকারের মৌলিক (যেমন 7, 11, 19) দুই বর্গের যোগফল হতে পারে না। 13 হলো 4k+1 আকারের।",
        "reveal_msg": "সঠিক উত্তর 13 = 2² + 3²।",
    },
}

L2 = {
    "num": 2,
    "slug": "pythagorean-triples",
    "yt": "QJYmyhnaaek",
    "date": "২৬ মে, ২০১৭",
    "github": "https://github.com/3b1b/videos/blob/master/_2017/triples.py",
    "title_bn": "সমস্ত পিথাগোরীয় ট্রিপলের দৃশ্যায়ন",
    "title_en": "All possible pythagorean triples, visualized",
    "subtitle_bn": "৩-৪-৫ থেকে জটিল সংখ্যা: a² + b² = c²-এর সম্পূর্ণ সমাধানের জ্যামিতিক পথ",
    "prev_title": "পূর্ববর্তী অধ্যায়: মৌলিক সংখ্যার সর্পিল",
    "next_title": "পরবর্তী অধ্যায়: পাই হিডিং ইন প্রাইম রেগুলারিটিজ",
    "epigraph": {
        "quote": "There is a way to understand all triplets (a, b, c) satisfying a² + b² = c² — and it uses complex numbers in a clever way.",
        "quote_bn": "a² + b² = c² পূরণকারী সব ট্রিপল বোঝার একটি পথ আছে — আর তা জটিল সংখ্যা ব্যবহার করে।",
        "author": "3Blue1Brown",
    },
    "bookmarks": [
        (0, "০০:০০", "পরিচিত ত্রিভুজ ও প্রশ্ন"),
        (110, "০১:৫০", "একক বৃত্ত ও পরিমেয় বিন্দু"),
        (250, "০৪:১০", "ইউক্লিডের সূত্র"),
        (400, "০৬:৪০", "জটিল সংখ্যা ও গাউসিয়ান পূর্ণসংখ্যা"),
        (560, "০৯:২০", "সমস্ত ট্রিপলের মানচিত্র"),
    ],
    "lab": {
        "title": "ইন্টারেক্টিভ ল্যাব — ট্রিপল জেনারেটর",
        "desc": "m ও n-এর বিভিন্ন জোড়া বেছে সরাসরি আদিম ট্রিপল তৈরি হতে দেখো। প্রতিটি ত্রিভুজের চারপাশে বর্গগুলোর ক্ষেত্রফল যোগ হয়ে কীভাবে বড় বর্গ তৈরি করে তা পর্যবেক্ষণ করো।",
        "mode": "triples",
    },
    "quizzes": L2_QUIZZES,
    "sections": [
        {
            "id": "sec-familiar-triangles",
            "title": "পরিচিত ত্রিভুজ ও মূল প্রশ্ন",
            "blocks": [
                P("স্কুলে আমরা কয়েকটি বিশেষ সমকোণী ত্রিভুজ শিখি — ৩-৪-৫, ৫-১২-১৩, ৮-১৫-১৭। পিথাগোরাসের সূত্র বলে, বাহু তিনটি a, b, c হলে a² + b² = c², যেখানে c হলো অতিভুজ। প্রশ্ন হলো: এই ধরনের কতগুলো ট্রিপল আছে? আর কি কোনো পদ্ধতি আছে যা দিয়ে সবগুলো বের করা যায়?",
                  "স্কুলে আমরা ৩-৪-৫, ৫-১২-১৩, ৮-১৫-১৭ ত্রিভুজ শিখি। পিথাগোরাসের সূত্র a² + b² = c²। প্রশ্ন, এই রকম কতগুলো ট্রিপল আছে আর সবগুলো বের করার পদ্ধতি কি?") ,
                F(triangle_svg(), " তিনটি বর্গ ত্রিভুজের তিন বাহুর ওপর আঁকা হয়েছে। দুটি ছোট বর্গের ক্ষেত্রফল (a² ও b²) যোগ করলে বড় বর্গের ক্ষেত্রফল (c²)-এর সমান হয় — এটি পিথাগোরাসের সূত্রের জ্যামিতিক রূপ। ছবিতে ৩-৪-৫ ত্রিভুজের ক্ষেত্রে ৯ + ১৬ = ২৫ দেখা যায়।",
                  "এই ছবিতে তিন বাহুর ওপর তিনটি বর্গ আঁকা হয়েছে। দুটি ছোট বর্গের ক্ষেত্রফল a² ও b² যোগ করলে বড় বর্গের c²-এর সমান হয়। ৩-৪-৫ ত্রিভুজের ক্ষেত্রে ৯ + ১৬ = ২৫ — এটি সূত্রের জ্যামিতিক প্রমাণ।"),
                M(r"a^2+b^2=c^2",
                  "মূল সূত্র, a-এর বর্গ যোগ b-এর বর্গ সমান c-এর বর্গ।"),
                P("কোনো ট্রিপলকে ২, ৩ বা যেকোনো সংখ্যা দিয়ে গুণ করলে নতুন ট্রিপল পাওয়া যায় — ৩-৪-৫ থেকে ৬-৮-১০, ৯-১২-১৫ ইত্যাদি। এগুলোকে আমরা 'অমূল' বলে বাদ দিই। আসল আগ্রহ হলো আদিম ট্রিপল, যেখানে a, b, c-এর কোনো সাধারণ উৎপাদক নেই (gc.d = 1)। সব আদিম ট্রিপল পেলে বাকিগুলো গুণ করে বের করা যায়।",
                  "কোনো ট্রিপলকে ২ বা ৩ দিয়ে গুণ করলে নতুন ট্রিপল পাওয়া যায়, যেমন ৬-৮-১০। এগুলো বাদ দিয়ে আমরা আদিম ট্রিপল খুঁজি, যাদের কোনো সাধারণ উৎপাদক নেই। সব আদিম ট্রিপল পেলে বাকি সব বের করা যায়।"),
                Z("q_primitive"),
            ],
        },
        {
            "id": "sec-unit-circle",
            "title": "একক বৃত্ত, পরিমেয় বিন্দু ও ইউক্লিডের সূত্র",
            "blocks": [
                P("c দিয়ে ভাগ করে সমীকরণকে সরল করি: (a/c)² + (b/c)² = 1। অর্থাৎ আমাদের কাজ হলো একক বৃত্ত x² + y² = 1-এ এমন সব বিন্দু খোঁজা যাদের x ও y পরিমেয় সংখ্যা। ((−1, 0)) বিন্দু থেকে যেকোনো পরিমেয় ঢাল t-এর একটি সরল রেখা টানলে সেটি বৃত্তকে আরেকটি বিন্দুতে ছেদ করে — আর সেই ছেদবিন্দুটি অবশ্যই পরিমেয় হয়।",
                  "সমীকরণকে c দিয়ে ভাগ করি: (a/c)² + (b/c)² = 1। কাজ এখন একক বৃত্তে পরিমেয় বিন্দু খোঁজা। (−1, 0) বিন্দু থেকে পরিমেয় ঢাল t-এর রেখা টানলে বৃত্তকে যে বিন্দুতে ছেদ করে তা অবশ্যই পরিমেয়।"),
                F(unit_circle_svg(), " ছবিতে (−1, 0) বিন্দু দিয়ে একটি রেখা বৃত্ততে কাটা হয়েছে এবং ছেদবিন্দু (x, y) চিহ্নিত করা হয়েছে। রেখার ঢাল t যুক্তিসঙ্গত হলে ছেদবিন্দুর স্থানাঙ্কও যুক্তিসঙ্গত হয়। এই সরল জ্যামিতিক কৌশলটিই পরবর্তীতে পূর্ণসংখ্যার সূত্রে রূপ নেয়।",
                  "ছবিতে (−1, 0) বিন্দু দিয়ে একটি রেখা বৃত্ত কেটেছে ও ছেদবিন্দু চিহ্নিত হয়েছে। রেখার ঢাল t পরিমেয় হলে ছেদবিন্দুও পরিমেয় হয়। এই জ্যামিতিক কৌশলই পরে পূর্ণসংখ্যার সূত্রে রূপ নেয়।"),
                P("রেখার সমীকরণ y = t(x + 1) কে x² + y² = 1-এ বসিয়ে সমাধান করলে পাই x = (1 − t²)/(1 + t²) এবং y = 2t/(1 + t²)। এখন t-কে পরিমেয় m/n আকারে লিখলে ভগ্নাংশ সরল করে পাই a = m² − n², b = 2mn, c = m² + n²। এটি ইউক্লিডের বিখ্যাত সূত্র — m ও n যেকোনো ধনাত্মক পূর্ণসংখ্যা হলে একটি পিথাগোরীয় ট্রিপল পাওয়া যায়।",
                  "রেখার সমীকরণ y = t(x+1) বসিয়ে পাই x = (1−t²)/(1+t²), y = 2t/(1+t²)। t = m/n লিখলে পাওয়া যায় ইউক্লিডের সূত্র a = m²−n², b = 2mn, c = m²+n²।"),
                M(r"x=\frac{1-t^2}{1+t^2},\quad y=\frac{2t}{1+t^2}",
                  "সূত্র, একক বৃত্তে পরিমেয় ছেদবিন্দুর স্থানাঙ্ক x সমান (১ − t²) ভাগ (১ + t²), y সমান 2t ভাগ (১ + t²)।"),
                M(r"(a,b,c)=(m^2-n^2,\ 2mn,\ m^2+n^2)",
                  "ইউক্লিডের সূত্র, a সমান m-এর বর্গ মাইনাস n-এর বর্গ, b সমান 2mn, c সমান m-এর বর্গ যোগ n-এর বর্গ।"),
                Z("q_euclid"),
                Z("q_m3n2"),
                C("green", "🌱", "আদিম হওয়ার শর্ত",
                  "প্রত্যেকটি আদিম ট্রিপল ঠিক একটি করে জোড়া (m, n) থেকে আসে, যেখানে m > n, gc.d(m, n) = 1 এবং m ও n একজোড়া বিজোড়-জোড় — অর্থাৎ দুটোই একই সম হলে ট্রিপলটি আদিম হয় না। উদাহরণস্বরূপ m = 2, n = 1 থেকে (3,4,5); m = 3, n = 2 থেকে (5,12,13); m = 4, n = 1 থেকে (15,8,17)। এই শর্তগুলো মানলে কোনো ট্রিপল দুবার আসবে না বা বাদ যাবে না।",
                  "বিশেষ নোট, আদিম হওয়ার শর্ত। প্রতিটি আদিম ট্রিপল ঠিক একটি জোড়া (m, n) থেকে আসে, যেখানে gc.d এক আর m ও n এক জোড়া বিজোড়-জোড়। m=2,n=1 থেকে ৩-৪-৫; m=3,n=2 থেকে ৫-১২-১৩।"),
            ],
        },
        {
            "id": "sec-complex-numbers",
            "title": "জটিল সংখ্যা ও গাউসিয়ান পূর্ণসংখ্যা",
            "blocks": [
                P("একই সমীকরণকে জটিল সংখ্যার ভাষায় লেখা যায়: a² + b² = (a + bi)(a − bi)। এখানে a + bi ও a − bi পরস্পরের conjugate, আর তাদের গুণফল একটিমাত্র বাস্তব সংখ্যা c²। ফলে পিথাগোরীয় ট্রিপল খোঁজার মানে হলো — এমন একটি গাউসিয়ান পূর্ণসংখ্যা (a + bi) খোঁজা যার নর্ম a² + b² একটি পূর্ণবর্গ।",
                  "একই সমীকরণ জটিল সংখ্যায় লেখা যায়, a² + b² = (a + bi)(a − bi)। দুটি conjugate-এর গুণফল বাস্তব c²। তাই ট্রিপল খোঁজার মানে এমন গাউসিয়ান পূর্ণসংখ্যা খোঁজা যার নর্ম একটি পূর্ণবর্গ।"),
                F(complex_svg(), " জটিল তলে এক বিন্দু a + bi দেখানো হয়েছে, সাথে তার অনুভূমিক ও উল্লম্ব উপাদান a ও b। বিন্দুটির মূলবিন্দু থেকে দূরত্বের বর্গই হলো |a + bi|² = a² + b²। ছবিতে এই দূরত্ব ও বর্গের সম্পর্কটি মনে রাখো — গাউসিয়ান পূর্ণসংখ্যার অনন্য factorization-এর মূল এখানেই।",
                  "জটিল তলে a + bi বিন্দু আর তার a ও b উপাদান দেখানো হয়েছে। মূলবিন্দু থেকে দূরত্বের বর্গ |a+bi|² = a²+b²। গাউসিয়ান পূর্ণসংখ্যার factorization-এর মূল এই সম্পর্কেই আছে।"),
                M(r"(a+bi)(a-bi)=a^2+b^2=c^2",
                  "সূত্র, a প্লাস বাই আই গুণ a মাইনাস বাই আই সমান a-এর বর্গ যোগ b-এর বর্গ সমান c-এর বর্গ।"),
                P("গাউসিয়ান পূর্ণসংখ্যার ring-এ অনন্য factorization প্রযোজ্য — যেমন সাধারণ পূর্ণসংখ্যায় প্রতিটি সংখ্যা মৌলিকের গুণফলে ভেঙে যায়। 5-কে ভেঙে লেখা যায় (2 + i)(2 − i); আবার 3 কে ভাঙা যায় না — 3 হলো গাউসিয়ান মৌলিক। নিয়ম হলো: 4k + 1 আকারের মৌলিক দুই গুণনীয়কে ভেঙে যায়, কিন্তু 4k + 3 আকারের মৌলিক অভেদ্য থাকে।",
                  "গাউসিয়ান পূর্ণসংখ্যায় অনন্য factorization প্রযোজ্য। 5 কে ভাঙা যায় (2+i)(2−i), কিন্তু 3 অভেদ্য। নিয়ম, 4k+1 মৌলিক ভেঙে যায় আর 4k+3 অভেদ্য থাকে।"),
                C("purple", "🔍", "কেন 4k+3 মৌলিক বাধা?",
                  "c² একটি পূর্ণবর্গ, তাই তার factorization-এ প্রতিটি গাউসিয়ান মৌলিকের ঘাত জোড় হতে হবে। 4k+3 আকারের মৌলিক গাউসিয়ান অভেদ্য হওয়ায় c²-এ এটি জোড় ঘাতেই থাকবে — ফলে (a+bi)-তেও এটি জোড় ঘাতে থাকবে, অর্থাৎ a ও b উভয়ই ওই মৌলিক দিয়ে বিভাজ্য হবে। তখন gc.d(a,b) ≠ 1 হয়ে যায়। তাই আদিম ট্রিপলে 4k+3 মৌলিক c-কে ভাগ করতে পারে না।",
                  "বিশেষ নোট, 4k+3 মৌলিক কেন বাধা। c² পূর্ণবর্গ হওয়ায় প্রতিটি গাউসিয়ান মৌলিকের ঘাত জোড় হতে হবে। 4k+3 অভেদ্য হওয়ায় এটি a ও b উভয়কেই ভাগ করে — ফলে gc.d একের বেশি হয়। তাই আদিম ট্রিপলে এটি c-কে ভাগ করতে পারে না।"),
                M(r"(m+ni)^2=(m^2-n^2)+2mni\ \Longrightarrow\ (a,b,c)=(m^2-n^2,\,2mn,\,m^2+n^2)",
                  "সূত্র, m প্লাস এন আই-এর বর্গ থেকে আসে ইউক্লিডের ট্রিপল।"),
                Z("q_mod4"),
            ],
        },
        {
            "id": "sec-all-triples",
            "title": "সমস্ত ট্রিপলের মানচিত্র",
            "blocks": [
                P("এখন সব টুকরো মিলছে। যেকোনো আদিম ট্রিপলের (a + bi) অবশ্যই কোনো গাউসিয়ান পূর্ণসংখ্যার বর্গের (একক গুণক ছাড়া) সমান — কারণ c²-এর factorization-এ প্রতিটি মৌলিকের ঘাত জোড় এবং a+bi ও a−bi পরস্পর সহ-মৌলিক। ফলে (a + bi) = ±(m + ni)² বা ±i(m + ni)², যা থেকেই ইউক্লিডের সূত্রটি আবার পাওয়া যায়। অর্থাৎ m > n, gc.d = 1, বিজোড়-জোড় ভিন্ন — এই তিন শর্ত পূরণকারী প্রতিটি জোড়া ঠিক একটি আদিম ট্রিপল দেয়।",
                  "এখন সব টুকরো মিলছে। যেকোনো আদিম ট্রিপলে a+bi অবশ্যই কোনো গাউসিয়ান পূর্ণসংখ্যার বর্গ — কারণ c²-এর প্রতিটি মৌলিকের ঘাত জোড়। তাই (a+bi) = ±(m+ni)², যা থেকে ইউক্লিডের সূত্র আসে। তিন শর্ত মানলে প্রতিটি (m,n) ঠিক একটি আদিম ট্রিপল দেয়।"),
                F(triangle_svg(), " চিত্রটি আবার দেখো — এখন বর্গগুলোর ক্ষেত্রফল শুধু সংখ্যা নয়, বরং জটিল সংখ্যার নর্মের গুণফল। বাঁয়ের বর্গ a², ওপরের বর্গ b² আর ডানের বর্গ c² — তিনটি মিলে পিথাগোরীয় সম্পর্ক প্রকাশ করে। বড় আদিম ট্রিপলগুলোও এই একই কাঠামো মেনে চলে, শুধু m ও n বড় হয়।",
                  "এই চিত্রে বর্গগুলোর ক্ষেত্রফল এখন জটিল সংখ্যার নর্মের গুণফল। বাঁয়ে a², ওপরে b², ডানে c² — তিনটি মিলে পিথাগোরীয় সম্পর্ক। বড় আদিম ট্রিপলও একই কাঠামো মেনে চলে, শুধু m ও n বড় হয়।"),
                P("এই জোড়া-নির্মাণ থেকে ট্রিপলের একটি 'বৃক্ষ' তৈরি হয় — মূলে (3,4,5), তার থেকে শাখা হিসেবে (5,12,13), (8,15,17), (7,24,25), (20,21,29) ইত্যাদি বের হয়। প্রতিটি শাখার আকার বাড়তে থাকে এবং কোনো ট্রিপল দুবার আসে না। পাশাপাশি একক বৃত্তের পরিমেয় বিন্দু আর জটিল বর্গ — একই বস্তুর দুই রূপ।",
                  "এই নির্মাণ থেকে ট্রিপলের এক বৃক্ষ তৈরি হয় — মূলে ৩-৪-৫, শাখায় ৫-১২-১৩, ৮-১৫-১৭, ৭-২৪-২৫ ইত্যাদি। কোনো ট্রিপল দুবার আসে না। একক বৃত্তের পরিমেয় বিন্দু আর জটিল বর্গ — একই বস্তুর দুই রূপ।"),
            ],
        },
        {
            "id": "sec-conclusion",
            "title": "বীজগণিত ও জ্যামিতির মিলন",
            "blocks": [
                P("আমরা শুরু করেছিলাম তিনটি সংখ্যার এক সরল সমীকরণ দিয়ে — a² + b² = c²। শেষ করছি জটিল সংখ্যার অনন্য factorization-এ। একক বৃত্তের পরিমেয় বিন্দু, জোড়া পূর্ণবর্গ, আর গাউসিয়ান বর্গ — এগুলো সব একই গল্পের বিভিন্ন অধ্যায়। কোনো কိ Sharma-অনুমান ছাড়াই সব পিথাগোরীয় ট্রিপলের সম্পূর্ণ তালিকা বের করা গেল, কারণ factorization আমাদের বলে দেয় কোনটির অস্তিত্ব আছে আর কোনটির নেই।",
                  "শুরু করেছিলাম a² + b² = c² দিয়ে, শেষ করছি জটিল সংখ্যার factorization-এ। একক বৃত্তের পরিমেয় বিন্দু আর গাউসিয়ান বর্গ — সব একই গল্পের অন্য অধ্যায়। কোনো অনুমান ছাড়াই সব ট্রিপলের তালিকা বের করা গেল।"),
                P("এই পদ্ধতি শক্তিশালী কারণ এটি কেবল বের করে না, বোঝায়ও — কেন 4k+3 মৌলিক আদিম ট্রিপলে আসতে পারে না, কেন কোনো দুটি (m,n) একই ট্রিপল দেয় না, কেন প্রতিটি আদিম ট্রিপল ঠিক একবারই আসে। গণিতে এমন অনেক সমস্যা আছে যেখানে 'সব সমাধান বের করা'র চেয়ে 'কেন আর নেই' বোঝাটা কঠিন — পিথাগোরীয় ট্রিপল সেই ধরনের এক উজ্জ্বল উদাহরণ।",
                  "এই পদ্ধতি শক্তিশালী কারণ এটি বোঝায় কেন 4k+3 মৌলিক আসতে পারে না, কেন কোনো দুটি (m,n) একই ট্রিপল দেয় না। গণিতে 'কেন আর নেই' বোঝাটা প্রায়ই 'সব বের করা'র চেয়ে কঠিন — পিথাগোরীয় ট্রিপল তার এক উজ্জ্বল উদাহরণ।"),
            ],
        },
    ],
}


# =========================================================================== #
# LESSON 03 — leibniz-formula
# =========================================================================== #
L3_QUIZZES = {
    "q_series": {
        "question": r"❓ $1-\frac{1}{3}+\frac{1}{5}-\frac{1}{7}+\cdots$ ধারাটির মান কত?",
        "options": [r"$\frac{\pi}{2}$", r"$\frac{\pi}{4}$", r"$\frac{\pi}{8}$", r"$\frac{4}{\pi}$"],
        "correct": 1,
        "correct_msg": "সঠিক! arctan(1) = π/4 এবং arctan-এর ধারা 1 − 1/3 + 1/5 − … — তাই যোগফল π/4। কিন্তু প্রশ্ন হলো বৃত্ত আকস্মিকভাবে এখানে কী করছে?",
        "wrong_msg": "arctan x = x − x³/3 + x⁵/5 − …; x = 1 বসালে পাওয়া যায় π/4।",
        "reveal_msg": r"সঠিক উত্তর $\frac{\pi}{4}$।",
    },
    "q_sum2squares": {
        "question": "❓ নিচের কোন মৌলিক সংখ্যাটি দুটি পূর্ণবর্গের যোগফল?",
        "options": ["7", "11", "13", "19"],
        "correct": 2,
        "correct_msg": "হ্যাঁ! 13 = 2² + 3²। 4k+1 আকারের মৌলিকই কেবল দুই বর্গের যোগফল হতে পারে; 7, 11, 19 সবই 4k+3।",
        "wrong_msg": "4k+3 আকারের মৌলিক কখনো দুই বর্গের যোগফল নয়। 13 = 4×3+1 আকারের।",
        "reveal_msg": "সঠিক উত্তর 13 = 4 + 9।",
    },
    "q_factor5": {
        "question": r"❓ অয়লারের গুণফলে $p\equiv 1\pmod 4$ মৌলিকের জন্য গুণনীয়ক কত?",
        "options": [r"$\frac{p}{p-1}$", r"$\frac{p}{p+1}$", r"$\frac{p-1}{p}$", r"$1-\frac{1}{p}$"],
        "correct": 0,
        "correct_msg": "সঠিক! 1-এর জন্য χ₄(p) = 1, তাই (1 − 1/p)⁻¹ = p/(p−1)। p = 5-এর জন্য গুণনীয়ক 5/4। 3-এর মতো মৌলিকের ক্ষেত্রে χ₄ = −1, তাই ফ্যাক্টর p/(p+1)।",
        "wrong_msg": "χ₄(p) = 1 হলে ফ্যাক্টর (1 − 1/p)⁻¹ = p/(p−1); χ₄ = −1 হলে p/(p+1)।",
        "reveal_msg": r"সঠিক উত্তর $\frac{p}{p-1}$।",
    },
    "q_lattice": {
        "question": "❓ বৃত্তের ভেতরের গাউসিয়ান বিন্দু (lattice point) সংখ্যা R বড় হলে কতের কাছাকাছি হয়?",
        "options": ["πR", "πR²", "2πR", "R²"],
        "correct": 1,
        "correct_msg": "সঠিক! বৃত্তের ক্ষেত্রফল πR², আর প্রতিটি একক বর্গে প্রায় একটি করে বিন্দু থাকে — তাই মোট বিন্দু ≈ πR²। এই সরল ধারণাটিই শেষ পর্যন্ত π-এর গুণফল সূত্রের দিকে নিয়ে যায়।",
        "wrong_msg": "বৃত্তের ক্ষেত্রফল πR²; ঘনত্ব ~1 হওয়ায় বিন্দুর সংখ্যাও ~πR²।",
        "reveal_msg": "সঠিক উত্তর πR²।",
    },
}

L3 = {
    "num": 3,
    "slug": "leibniz-formula",
    "yt": "NaL_Cb42WyY",
    "date": "১৯ মে, ২০১৭",
    "github": "https://github.com/3b1b/videos/blob/master/_2017/leibniz.py",
    "title_bn": "মৌলিক নিয়মিততায় লুকোনো পাই",
    "title_en": "Pi hiding in prime regularities",
    "subtitle_bn": "লাইবনিটজের ধারা, গাউসিয়ান পূর্ণসংখ্যা ও মৌলিক সংখ্যার গুণফল থেকে পাই-এর জন্ম",
    "prev_title": "পূর্ববর্তী অধ্যায়: পিথাগোরীয় ট্রিপল",
    "next_title": "",
    "epigraph": {
        "quote": "At first, 1 − 1/3 + 1/5 − 1/7 + … seems unrelated to circles, but in fact there is a circle hiding here.",
        "quote_bn": "প্রথমে মনে হয় ১ − ১/৩ + ১/৫ − …-এর সাথে বৃত্তের কোনো সম্পর্ক নেই, কিন্তু আসলে এখানে এক বৃত্ত লুকিয়ে আছে।",
        "author": "3Blue1Brown",
    },
    "bookmarks": [
        (0, "০০:০০", "লাইবনিটজের ধারা ও বৃত্ত"),
        (130, "০২:১০", "arctan ও গুণোত্তর ধারা"),
        (280, "০৪:৪০", "গাউসিয়ান বিন্দু ও বৃত্ত"),
        (440, "০৭:২০", "মৌলিক ও দুই বর্গের যোগফল"),
        (610, "১০:১০", "অয়লারের গুণফল সূত্র"),
        (760, "১২:৪০", "দুই ধারার মিলন ও উপসংহার"),
    ],
    "lab": {
        "title": "ইন্টারেক্টিভ ল্যাব — ধারা ও আংশিক যোগফল",
        "desc": "পদ সংখ্যা বাড়িয়ে লাইবনিটজের ধারার আংশিক যোগফল π/4-এর কাছে কীভাবে আসছে তা দেখো। প্রতিটি নতুন পদ আগেরটির বিপরীত দিকে ঠেলে দেয় — এই দোলনাই ধারার বৈশিষ্ট্য।",
        "mode": "leibniz",
    },
    "quizzes": L3_QUIZZES,
    "sections": [
        {
            "id": "sec-leibniz-series",
            "title": "লাইবনিটজের ধারা ও লুকোনো বৃত্ত",
            "blocks": [
                P("১৬৭০-এর দশকে গটফ্রিড লাইবনিটজ একটি আশ্চর্য সূত্র আবিষ্কার করেছিলেন: ১ − ১/৩ + ১/৫ − ১/৭ + ১/৯ − … = π/4। বাঁ দিকে কেবল সাদামাটা ভগ্নাংশ, ডান দিকে বৃত্তের পরিধি আর ব্যাসের অনুপাত — দেখে মনে হয় না এদের কোনো সম্পর্ক আছে। কিন্তু এই অধ্যায়ে আমরা দেখব, এই 'অসম্ভব' সমীকরণের পেছনে আছে জটিল সংখ্যা আর মৌলিক সংখ্যার গভীর নিয়মিততা।",
                  "লাইবনিটজ আবিষ্কার করেছিলেন ১ মাইনাস ১/৩ প্লাস ১/৫ মাইনাস ১/৭ … সমান পাই/৪। বাঁ দিকে ভগ্নাংশ, ডান দিকে বৃত্ত — এর পেছনে আছে জটিল সংখ্যা আর মৌলিকের গভীর নিয়ম।"),
                M(r"\sum_{n=0}^{\infty}\frac{(-1)^n}{2n+1}=1-\frac13+\frac15-\frac17+\cdots=\frac{\pi}{4}",
                  "সূত্র, লাইবনিটজের ধারা, ১ মাইনাস এক তৃতীয়াংশ প্লাস এক পঞ্চমাংশ ইত্যাদি সমান পাই/৪।"),
                F(series_svg(), " গ্রাফে আংশিক যোগফলগুলো π/4-এর (হলুদ ড্যাশ্ড রেখা) ওপর দিয়ে দোলে — প্রথম পদ ১, তারপর ০.৬৬৭, ০.৮৬৭, ০.৭২৪… করে ক্রমশ কাছে আসে। প্রতিটি নতুন পদ আগের চেয়ে ছোট, তাই দোলনের প্রশস্ততা কমতে থাকে। ছবিটি মনে রেখো: অসীম ধারা কীভাবে একটিমাত্র সংখ্যায় স্থির হয় তা এখানে দেখা যায়।",
                  "গ্রাফে আংশিক যোগফল পাই/৪-এর ওপর দিয়ে দোলে — ১, ০.৬৬৭, ০.৮৬৭, ০.৭২৪ করে ক্রমশ কাছে আসে। প্রতিটি নতুন পদ ছোট হওয়ায় দোলন কমে যায়। অসীম ধারা কীভাবে এক সংখ্যায় স্থির হয় এখানে দেখা যায়।"),
                P("এই সূত্রের সহজ ব্যাখ্যা আসে arctan ফাংশন থেকে। জ্যামিতিক ধারা 1/(1+t²) = 1 − t² + t⁴ − … কে 0 থেকে 1 পর্যন্ত ইন্টিগ্রেট করলে পাই arctan(1) = 1 − 1/3 + 1/5 − …। আর arctan(1) = π/4, কারণ ৪৫ ডিগ্রি কোণের tangent হলো ১। অর্থাৎ বৃত্তটি এসেছে ট্রিগনোমেট্রির দরজা দিয়ে — কিন্তু প্রশ্ন থেকেই যায়, মৌলিক সংখ্যা এখানে কোথা থেকে আসে?",
                  "ব্যাখ্যা আসে arctan থেকে। 1/(1+t²) ধারাকে 0 থেকে 1 পর্যন্ত ইন্টিগ্রেট করলে arctan(1) পাই, যা π/4। বৃত্ত এলো ট্রিগনোমেট্রি দিয়ে, কিন্তু মৌলিক সংখ্যা কোথা থেকে আসে?"),
                M(r"\arctan x=\int_0^x\frac{dt}{1+t^2}=x-\frac{x^3}{3}+\frac{x^5}{5}-\cdots",
                  "সূত্র, arctan x সমান 0 থেকে x পর্যন্ত 1/(1+t²)-এর ইন্টিগ্রাল, যার ধারা x মাইনাস x³/3 প্লাস x⁵/5।"),
                Z("q_series"),
            ],
        },
        {
            "id": "sec-gaussian",
            "title": "গাউসিয়ান পূর্ণসংখ্যা ও দুই বর্গের যোগফল",
            "blocks": [
                P("জটিল তলে পূর্ণসংখ্যার বিন্দুগুলো (a + bi) এক একটি বর্গাকার জালি তৈরি করে — একে গাউসিয়ান পূর্ণসংখ্যা বলে।-radius R-এর বৃত্তের ভেতরে কতগুলো বিন্দু আছে? ক্ষেত্রফল πR² আর প্রতি একক বর্গে প্রায় একটি বিন্দু — তাই উত্তর প্রায় πR²। এই সরল ধারণাটিই শেষ পর্যন্ত π-এর সূত্রে রূপ নেবে।",
                  "জটিল তলে গাউসিয়ান পূর্ণসংখ্যার বিন্দুরা বর্গাকার জালি তৈরি করে। আর R ব্যাসার্ধের বৃত্তের ভেতরে বিন্দু সংখ্যা প্রায় πR² — বৃত্তের ক্ষেত্রফলের সমান।"),
                F(lattice_svg(), " ছবিতে বৃত্তের ভেতরে জালির বিন্দুগুলো দেখানো হয়েছে; হলুদ বিন্দুগুলো এমন সংখ্যা যারা দুই বর্গের যোগফল (যেমন 5 = 1²+2², 13 = 2²+3²)। বাইরের ড্যাশ্ড বৃত্ত R-এর সীমা। বিন্দুগুলোর ঘনত্ব প্রায় একই — তাই মোট সংখ্যা ক্ষেত্রফল πR²-এর সমান হয়। এই গণনাই পরের সব সূত্রের ভিত্তি।",
                  "ছবিতে বৃত্তের ভেতরে জালির বিন্দু আর হলুদ বিন্দু দেখা যাচ্ছে, যারা দুই বর্গের যোগফল যেমন ৫ বা ১৩। বিন্দুর ঘনত্ব প্রায় সমান, তাই মোট সংখ্যা ক্ষেত্রফল πR²-এর সমান। এই গণনাই পরের সূত্রের ভিত্তি।"),
                Z("q_lattice"),
                P("প্রতিটি গাউসিয়ান পূর্ণসংখ্যার নর্ম N(a + bi) = a² + b²। প্রশ্ন এখন দাঁড়ায়: কোন কোন পূর্ণসংখ্যা n-এর জন্য a² + b² = n সমাধান আছে? গাউসিয়ান পূর্ণসংখ্যায় factorization n = (a+bi)(a−bi)। যেহেতু অনন্য factorization প্রযোজ্য, n-কে দুই বর্গে লেখার সংখ্যা নির্ভর করে n-এর মৌলিক উৎপাদকের ওপর — বিশেষ করে 4k+1 আর 4k+3 শ্রেণির মৌলিকের ওপর।",
                  "গাউসিয়ান নর্ম N(a+bi) = a²+b²। কোন n-এর জন্য a²+b² = n সমাধান আছে? factorization n = (a+bi)(a−bi) থেকে দেখা যায় উত্তর নির্ভর করে মৌলিক উৎপাদকের ওপর, বিশেষ করে 4k+1 ও 4k+3 শ্রেণির।"),
                M(r"N(a+bi)=a^2+b^2=(a+bi)(a-bi)",
                  "সূত্র, নর্ম a²+b² সমান (a+bi) গুণ (a−bi)।"),
                C("gold", "🧮", "মৌলিকের দুই শ্রেণি",
                  "যে মৌলিক 4k+1 আকারের (যেমন 5, 13, 17), তা গাউসিয়ান পূর্ণসংখ্যায় দুই গুণনীয়কে ভেঙে যায় — 5 = (2+i)(2−i)। আর যে মৌলিক 4k+3 আকারের (যেমন 3, 7, 11), তা অভেদ্য থেকে যায়। তাই n কে দুই বর্গের যোগফল লিখতে হলে 4k+3 মৌলিকগুলোকে জোড় ঘাতে থাকতে হয়; 4k+1 মৌলিকগুলো ইচ্ছামতো যোগ দিতে পারে। এই দুই শ্রেণির ভিন্ন আচরণই π-এর গুণফল সূত্রের চাবিকাঠি।",
                  "বিশেষ নোট, মৌলিকের দুই শ্রেণি। 4k+1 মৌলিক ভেঙে যায়, যেমন ৫ = (2+i)(2−i)। 4k+3 মৌলিক অভেদ্য — তাই তাদের জোড় ঘাতে থাকতে হয়। 4k+1 মৌলিক ইচ্ছামতো যোগ দিতে পারে। এই দুই শ্রেণির ভিন্ন আচরণই গুণফল সূত্রের চাবিকাঠি।"),
                Z("q_sum2squares"),
            ],
        },
        {
            "id": "sec-product",
            "title": "অয়লারের গুণফলে পাই",
            "blocks": [
                P("এখন বৃত্তের ভেতরের বিন্দু সংখ্যা দুইভাবে গণনা করি। একদিকে πR²। অন্যদিকে প্রতিটি গাউসিয়ান পূর্ণসংখ্যার নর্ম n-এর জন্য r₂(n) সংখ্যক উপায়ে বিন্দু পাওয়া যায় — অর্থাৎ মোট ∑_{n≤R²} r₂(n)। 4k+1 মৌলিকের কারণে r₂(n) বাড়ে, 4k+3 মৌলিকের কারণে কমে। R → ∞ হলে এই দুই গণনার মিল থেকে π/4-এর এক গুণফল রূপ পাওয়া যায় — ঠিক যেমন অয়লার বেসেল সমস্যায় পেয়েছিলেন।",
                  "বৃত্তের ভেতরের বিন্দু দুইভাবে গণনা করি — πR² আর ∑r₂(n)। 4k+1 মৌলিক r₂ বাড়ায়, 4k+3 কমায়। সীমায় মিল থেকে পাই π/4-এর গুণফল রূপ, ঠিক বেসেল সমস্যার মতো।"),
                F(product_svg(), " বলয়গুলো ধাপে ধাপে মৌলিকগুলোর গুণনীয়ক যোগ করতে দেখায় — ৫-এর ফ্যাক্টর ৫/৪, ১৩-এর ১৩/১২, আর ৩-এর ৩/৪, ৭-এর ৭/৮। হলুদ কেন্দ্র π/4-এর লক্ষ্য। প্রতিটি বলয় আগের আসন্ন মানকে আরও নিখুঁত করে। ছবিটি মনে রেখো: অসীম সংখ্যক মৌলিকের ছোট ছোট সংশোধন মিলে একটি বৃত্তের পরিমাপ তৈরি করছে।",
                  "বলয়গুলো ধাপে ধাপে মৌলিকের গুণনীয়ক যোগ করে — ৫-এর ৫/৪, ১৩-এর ১৩/১২, ৩-এর ৩/৪, ৭-এর ৭/৮। হলুদ কেন্দ্র π/4। অসীম মৌলিকের ছোট সংশোধন মিলে বৃত্তের পরিমাপ তৈরি করছে।"),
                M(r"\frac{\pi}{4}=\prod_{p\equiv 1\ (4)}\frac{p}{p-1}\ \cdot\prod_{p\equiv 3\ (4)}\frac{p}{p+1}",
                  "সূত্র, পাই/৪ সমান 4k+1 মৌলিকের p/(p−1) গুণফল, 4k+3 মৌলিকের p/(p+1) গুণফল।"),
                P("সূত্রটি পড়া যায় এভাবে — প্রতিটি 4k+1 মৌলিক π/4-কে p/(p−1) গুণ বাড়ায়, আর প্রতিটি 4k+3 মৌলিক p/(p+1) গুণ কমায়। 5-এর জন্য 5/4, 13-এর জন্য 13/12; 3-এর জন্য 3/4, 7-এর জন্য 7/8। এই দুই ধরনের সংশোধনের ভারসাম্যেই π/4 দাঁড়িয়ে আছে। আবার χ₄(n) চিহ্ন ব্যবহার করে একটিমাত্র সূত্রে লেখা যায়: π/4 = ∏_p (1 − χ₄(p)/p)⁻¹, যেখানে χ₄(2) = 0, χ₄(4k+1) = 1, χ₄(4k+3) = −1।",
                  "সূত্র পড়ো — 4k+1 মৌলিক p/(p−1) গুণ বাড়ায়, 4k+3 প/(p+1) কমায়। ৫-এর ৫/৪, ৩-এর ৩/৪। χ₄ চিহ্ন দিয়ে লেখা যায় π/4 = ∏(1 − χ₄(p)/p)⁻¹।"),
                M(r"\frac{\pi}{4}=\prod_{p}\left(1-\frac{\chi_4(p)}{p}\right)^{-1},\qquad \chi_4(p)=\begin{cases}0,&p=2\\ 1,&p\equiv1\,(4)\\ -1,&p\equiv3\,(4)\end{cases}",
                  "সূত্র, পাই/₄ সমান সব মৌলিক জুড়ে (১ − কাই₄(p)/p)-এর বিপরীতের গুণফল, যেখানে কাই₄ ২-এর জন্য ০, 4k+1-এ ১, 4k+3-এ মাইনাস ১।"),
                Z("q_factor5"),
            ],
        },
        {
            "id": "sec-conclusion",
            "title": "দুই ধারার মিলন ও উপসংহার",
            "blocks": [
                P("এখন লাইবনিটজের মূল ধারাটি আবার দেখো — ১ − ১/৩ + ১/৫ − …। এই '+ − + −' চিহ্নের পর্যায়ক্রম আসলে χ₄(n)-এর মতোই: 4k+1 সংখ্যা ধনাত্মক, 4k+3 ঋণাত্মক, জোড় সংখ্যা বাদ। আর arctan-এর ধারা ও গাউসিয়ান পূর্ণসংখ্যার গুণফল — দুটি সম্পূর্ণ ভিন্ন পথ একসাথে এগিয়ে গিয়ে একই π/4-এ পৌঁছায়। এটি গণিতের সবচেয়ে সুন্দর মিলনগুলোর একটি।",
                  "লাইবনিটজের '+ − + −' চিহ্নের পর্যায়ক্রম আসলে χ₄-এর মতোই। arctan-এর ধারা ও গাউসিয়ান factorization — দুই ভিন্ন পথ একই পাই/৪-এ পৌঁছায়। এটি গণিতের সুন্দর মিলন।"),
                P("আরও এক কথা — একই কৌশল বেসেল সমস্যায় (1 + 1/4 + 1/9 + … = π²/6) কাজ করে, শুধু সেখানে χ₄-এর বদলে সব মৌলিক অংশ নেয়। আধুনিক সংখ্যাতত্ত্বে L-ফাংশন, Dirichlet-এর ধারা আর Chebotarev ঘনত্ব — সবই এই একই ধারণার বিস্তারিত রূপ। যেটি শুরুতে একটা অদ্ভুত ভগ্নাংশের ধারা মনে হয়েছিল, তা আজ বৃত্ত, মৌলিক ও জটিল সংখ্যার এক গভীর সংযোগের দরজা।",
                  "একই কৌশল বেসেল সমস্যায়ও কাজ করে। আধুনিক সংখ্যাতত্ত্বের L-ফাংশন ঠিক এই ধারণার বিস্তারিত রূপ। যেটি শুরুতে অদ্ভুত ধারা মনে হয়েছিল, তা বৃত্ত, মৌলিক ও জটিল সংখ্যার গভীর সংযোগ।"),
            ],
        },
    ],
}

LESSONS = [L1, L2, L3]


# U+0964/U+0965 (দণ্ড) are shared by Bengali and Devanagari — exclude them.
FOREIGN_SCRIPT = re.compile(r"[\u0900-\u0963\u0966-\u097f\u4e00-\u9fff\u3040-\u30ff]")
LATIN_JAM = re.compile(r"(?<=[\u0980-\u09ff])[A-Za-z]{2,}|[A-Za-z]{2,}(?=[\u0980-\u09ff])")


def assert_clean_bengali(obj, label):
    """Guard against stray Devanagari/CJK/Latin fragments in Bengali narration."""
    text = json.dumps(obj, ensure_ascii=False)
    bad = FOREIGN_SCRIPT.findall(text) + LATIN_JAM.findall(text)
    if bad:
        raise ValueError("%s: stray script artifacts %r" % (label, bad[:12]))


def main():
    for lesson in LESSONS:
        n = lesson["num"]
        nn = "%02d" % lesson["num"]
        audio_dir = AUDIO_DIR / ("lesson_" + nn)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # 1. Data JSON
        manifest = manifest_for(lesson)
        data = {
            "lesson_id": "lesson_" + nn,
            "chapter_num": n,
            "course_id": COURSE,
            "title_en": lesson["title_en"],
            "title_bn": lesson["title_bn"],
            "subtitle_bn": lesson["subtitle_bn"],
            "video_id": lesson["yt"],
            "youtube_id": lesson["yt"],
            "official_url": "https://www.3blue1brown.com/lessons/" + lesson["slug"],
            "slug": lesson["slug"],
            "meta": {
                "credits": "Grant Sanderson (3Blue1Brown)",
                "translator_curator": "Bengali STEM Pedagogy Unit",
                "date": lesson["date"],
                "source_url": lesson["github"],
                "prerequisites": [],
            },
            "epigraph": lesson["epigraph"],
            "bookmarks": [
                {"time": b[0], "time_bn": b[1], "label_bn": b[2]}
                for b in lesson["bookmarks"]
            ],
            "toc": [{"href": "#" + s["id"], "label_bn": s["title"]} for s in lesson["sections"]]
                   + [{"href": "#sec-lab", "label_bn": lesson["lab"]["title"]}],
            "sections": [
                {
                    "id": s["id"],
                    "title_bn": s["title"],
                    "title_en": s["id"].replace("-", " ").title(),
                    "block_types": [b[0] for b in s["blocks"] if b[0] in QUIZ_TYPES],
                    "narrated": True,
                }
                for s in lesson["sections"]
            ]
            + [{
                "id": "sec-lab",
                "title_bn": lesson["lab"]["title"],
                "title_en": "Interactive Lab",
                "narrated": False,
                "mode": lesson["lab"]["mode"],
                "desc_bn": lesson["lab"]["desc"],
            }],
            "quizzes": [
                {
                    "id": qid,
                    "question_bn": q["question"],
                    "options_bn": q["options"],
                    "correct_index": q["correct"],
                    "correct_feedback_bn": q["correct_msg"],
                    "wrong_feedback_bn": q["wrong_msg"],
                    "reveal_bn": q["reveal_msg"],
                }
                for qid, q in lesson["quizzes"].items()
            ],
            "figures": [
                {
                    "id": "fig_%02d_%02d" % (n, i),
                    "caption_bn": b[2],
                    "type": "svg-inline",
                }
                for i, s in enumerate(lesson["sections"], 1)
                for b in s["blocks"] if b[0] == "figure"
            ],
            "video_src": "../../media_vault/number_theory/lesson_%s/experiments/3b1b_number_theory_%s_full_dubbed.mp4" % (nn, nn),
        }
        assert_clean_bengali(data, "lesson_" + nn)
        assert_clean_bengali(manifest, "lesson_" + nn + " manifest")

        (DATA_DIR / ("lesson_" + nn + ".json")).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        # 2. HTML
        (COURSE_DIR / ("lesson_" + nn + ".html")).write_text(
            render_html(lesson), encoding="utf-8"
        )

        # 3. Manifests (JSON + preload JS) — narrated IDs match the HTML exactly
        (audio_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (audio_dir / "manifest.js").write_text(
            "window.TEACHER_AUDIO_MANIFEST = "
            + json.dumps(manifest, ensure_ascii=False, indent=2)
            + ";\n",
            encoding="utf-8",
        )
        print("built lesson_%s : %d narrated sections, %d cues" % (
            nn, len(lesson["sections"]),
            sum(len(s["cues"]) for s in manifest["sections"].values())))

    (COURSE_DIR / "index.html").write_text(render_index(LESSONS), encoding="utf-8")
    print("built courses/number_theory/index.html")


if __name__ == "__main__":
    main()
