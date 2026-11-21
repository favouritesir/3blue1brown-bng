import os

lessons_data = [
    {
        "id": "02",
        "title": "রৈখিক সমন্বয়, স্প্যান এবং ভিত্তি ভেক্টর",
        "title_en": "Linear combinations, span, and basis vectors",
        "desc": "ভেক্টরের স্কেলার গুণন এবং যোগফল দিয়ে নতুন ভেক্টর তৈরি করাকে বলি রৈখিক সমন্বয় বা লিনিয়ার কম্বিনেশন। এই পাঠে জানব স্প্যান মানে কী, ভিত্তি ভেক্টর কীভাবে পুরো স্থানকে সংজ্ঞায়িত করে এবং রৈখিক নির্ভরতা বলতে কী বোঝায়।",
        "yt": "k7RM-ot2NWY",
        "prev": "lesson_01.html",
        "next": "lesson_03.html"
    },
    {
        "id": "03",
        "title": "রৈখিক রূপান্তর এবং ম্যাট্রিক্স",
        "title_en": "Linear transformations and matrices",
        "desc": "লিনিয়ার ট্রান্সফরমেশন আসলে কী? গ্রিডের রেখাগুলো সোজা এবং সমান দূরত্বের রেখে পুরো দ্বিমাত্রিক স্থানকে কীভাবে রূপান্তর করা যায় এবং ম্যাট্রিক্স কীভাবে সেই রূপান্তরের সংক্ষিপ্ত গাণিতিক ভাষা হিসেবে কাজ করে তা শিখুন।",
        "yt": "kYB8IZa5AuE",
        "prev": "lesson_02.html",
        "next": "lesson_04.html"
    },
    {
        "id": "04",
        "title": "ম্যাট্রিক্স গুণন আসলে রূপান্তরের রচনা",
        "title_en": "Matrix multiplication as composition",
        "desc": "ম্যাট্রিক্স গুণনের জটিল অ্যালজেব্রিক নিয়ম মুখস্থ করার দিন শেষ! একের পর এক রূপান্তর (রোটেশন ও শিয়ার) কীভাবে একত্রে একটি সামগ্রিক ম্যাট্রিক্স তৈরি করে এবং কেন ম্যাট্রিক্স গুণন ডান থেকে বামে কাজ করে তার চাক্ষুষ অন্তর্দৃষ্টি।",
        "yt": "XkY2DOUCWMU",
        "prev": "lesson_03.html",
        "next": "lesson_05.html"
    },
    {
        "id": "05",
        "title": "ত্রিমাত্রিক স্থানে রৈখিক রূপান্তর",
        "title_en": "Three-dimensional linear transformations",
        "desc": "ত্রিমাত্রিক স্থানে রৈখিক রূপান্তর কীভাবে ঘটে? ৩×৩ ম্যাট্রিক্স আসলে কীভাবে আই হ্যাট, জে হ্যাট এবং কে হ্যাট—এই তিনটি ত্রিমাত্রিক ভিত্তি ভেক্টরের স্থানান্তরকে ধরে রাখে তা দৃশ্যমানভাবে জানুন।",
        "yt": "rHLEWRxRGiM",
        "prev": "lesson_04.html",
        "next": "../../index.html"
    }
]

template = """<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>অধ্যায় {id} — {title} | লিনিয়ার অ্যালজেব্রা</title>
  <link rel="stylesheet" href="../../assets/css/main.css" />
  <!-- Official KaTeX (Vendored Locally — 100% Offline & Pure LaTeX Rendering) -->
  <link rel="stylesheet" href="../../assets/libs/katex/katex.min.css" />
  <script defer src="../../assets/libs/katex/katex.min.js"></script>
  <script defer src="../../assets/libs/katex/auto-render.min.js" onload="renderMathInElement(document.body, {{delimiters: [{{left: '$$', right: '$$', display: true}}, {{left: '$', right: '$', display: false}}]}});"></script>
  <style>
    :root {{
      --bg: #1a1a2e;
      --surface: #16213e;
      --card: #0f3460;
      --accent: #e94560;
      --blue: #4fc3f7;
      --yellow: #ffd54f;
      --green: #69f0ae;
      --text: #e0e0e0;
      --muted: #9e9e9e;
      --radius: 12px;
    }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Noto Sans Bengali', sans-serif; line-height: 1.8; margin: 0; }}
    .site-header {{ background: var(--surface); border-bottom: 2px solid var(--accent); padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
    .site-header a {{ color: var(--blue); text-decoration: none; }}
    .nav-btn {{ background: var(--card); color: var(--text); border: 1px solid var(--accent); border-radius: 6px; padding: 6px 14px; text-decoration: none; font-size: 0.85rem; }}
    .nav-btn:hover {{ background: var(--accent); color: #fff; }}
    .hero {{ background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 60%); padding: 48px 24px; text-align: center; }}
    .hero h1 {{ font-size: 2.2rem; color: #fff; margin-bottom: 8px; }}
    .container {{ max-width: 900px; margin: 0 auto; padding: 24px 16px; }}
    .player-card {{ background: var(--card); border-radius: var(--radius); padding: 20px; margin-bottom: 32px; border: 1px solid rgba(255,255,255,0.08); }}
    .article-card {{ background: var(--surface); border-radius: var(--radius); padding: 32px; margin-bottom: 32px; border-left: 4px solid var(--blue); }}
    .formula-box {{ background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px; text-align: center; font-size: 1.2rem; margin: 20px 0; border: 1px solid rgba(79,195,247,0.2); }}
  </style>
</head>
<body>

<header class="site-header">
  <div>
    <a href="../../index.html">← মূল পাতা</a> &nbsp;/&nbsp; <a href="../../index.html#tracks">লিনিয়ার অ্যালজেব্রা</a> &nbsp;/&nbsp; <span>অধ্যায় {id}</span>
  </div>
  <div style="display:flex; gap:10px;">
    <a href="{prev}" class="nav-btn">◀ পূর্ববর্তী</a>
    <a href="{next}" class="nav-btn">পরবর্তী ▶</a>
  </div>
</header>

<section class="hero">
  <div style="color:var(--accent); font-weight:bold; margin-bottom:8px;">অধ্যায় {id}</div>
  <h1>{title}</h1>
  <p style="color:var(--muted);">{title_en}</p>
</section>

<div class="container">

  <!-- Video & Audio Player Switcher -->
  <div class="player-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
      <span style="font-weight:bold; color:var(--blue); font-size:1.05rem;">📺 সম্পূর্ণ বাংলা ডাবড ভিডিও ও অডিও প্লেয়ার</span>
      <div style="display:flex; gap:8px;">
        <button id="btnLocal" onclick="switchMedia('local')" style="background:var(--accent); color:#fff; border:none; padding:6px 14px; border-radius:6px; cursor:pointer; font-size:0.85rem; font-weight:bold;">বাংলা ডাবড ভিডিও (HD)</button>
        <button id="btnYt" onclick="switchMedia('yt')" style="background:var(--surface); color:var(--text); border:1px solid rgba(255,255,255,0.2); padding:6px 14px; border-radius:6px; cursor:pointer; font-size:0.85rem;">মূল ইউটিউব ভিডিও</button>
      </div>
    </div>

    <!-- 1080p Pure Dubbed Local Video -->
    <div id="localBox" style="border-radius:8px; overflow:hidden; background:#000; margin-bottom:14px;">
      <video id="vPlayer" controls style="width:100%; display:block; max-height:480px;" src="../../media_vault/lesson_{id}/3b1b_lesson_{id}_bangla_dubbed_video.mp4"></video>
    </div>

    <!-- YouTube Embed -->
    <div id="ytBox" style="display:none; border-radius:8px; overflow:hidden; height:450px; margin-bottom:14px;">
      <iframe id="ytFrame" style="width:100%; height:100%; border:none;" src="https://www.youtube.com/embed/{yt}" allowfullscreen></iframe>
    </div>

    <!-- Pure Audio Master -->
    <div style="background:rgba(0,0,0,0.25); border-radius:8px; padding:12px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
      <span style="font-size:0.9rem; color:var(--yellow);">🎙️ স্টুডিও মাস্টার বাংলা অডিও (০% ব্যাকগ্রাউন্ড মিউজিক • ১০০% খাঁটি কথা):</span>
      <audio controls style="height:36px;" src="../../media_vault/lesson_{id}/3b1b_lesson_{id}_bangla_master.mp3"></audio>
    </div>

    <script>
      function switchMedia(type) {{
        const v = document.getElementById('vPlayer');
        const lBox = document.getElementById('localBox');
        const yBox = document.getElementById('ytBox');
        const bL = document.getElementById('btnLocal');
        const bY = document.getElementById('btnYt');
        if(type === 'local') {{
          lBox.style.display = 'block';
          yBox.style.display = 'none';
          bL.style.background = 'var(--accent)';
          bL.style.color = '#fff';
          bY.style.background = 'var(--surface)';
          bY.style.color = 'var(--text)';
        }} else {{
          v.pause();
          lBox.style.display = 'none';
          yBox.style.display = 'block';
          bY.style.background = 'var(--accent)';
          bY.style.color = '#fff';
          bL.style.background = 'var(--surface)';
          bL.style.color = 'var(--text)';
        }}
      }}
    </script>
  </div>

  <!-- Deep Dive Educational Article -->
  <article class="article-card">
    <h2 style="color:var(--blue); margin-top:0;">মূল ধারণার বিশদ ব্যাখ্যা</h2>
    <p>{desc}</p>

    <div class="formula-box">
      $$\\vec{{v}} = c_1 \\hat{{i}} + c_2 \\hat{{j}}$$
    </div>

    <h3 style="color:var(--yellow);">গাণিতিক সারসংক্ষেপ</h3>
    <p>আমরা জানি যে কোনো সমতলে $\\hat{{i}}$ হলো এক্স অক্ষ বরাবর একক ভেক্টর এবং $\\hat{{j}}$ হলো ওয়াই অক্ষ বরাবর একক ভেক্টর। এই দুটি ভিত্তি ভেক্টরের স্কেলার গুণিতক যোগ করে আমরা যে কোনো ভেক্টর তৈরি করতে পারি।</p>
    
    <div class="formula-box">
      $$\\begin{{bmatrix}} a & b \\\\ c & d \\end{{bmatrix}} \\begin{{bmatrix}} x \\\\ y \\end{{bmatrix}} = x \\begin{{bmatrix}} a \\\\ c \\end{{bmatrix}} + y \\begin{{bmatrix}} b \\\\ d \\end{{bmatrix}}$$
    </div>
  </article>

</div>

</body>
</html>"""

out_dir = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/linear_algebra"
for l in lessons_data:
    content = template.format(**l)
    path = os.path.join(out_dir, f"lesson_{l['id']}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {path}")
