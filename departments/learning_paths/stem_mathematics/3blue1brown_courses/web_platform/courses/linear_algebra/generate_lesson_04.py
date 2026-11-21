"""Build pristine, authentic Bengali edition of lesson_04.html matching lesson_03.html standard."""
import os

html_content = '''<!DOCTYPE html>
<html lang="bn" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>অধ্যায় ০৪ — ম্যাট্রিক্স গুণন ও রূপান্তরের সংযোজন | লিনিয়ার অ্যালজেব্রা | ৩ব্লু১ব্রাউন বাংলা</title>
<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>
<link rel="stylesheet" href="../../assets/css/lesson.css"/>
<script defer src="../../assets/libs/katex/katex.min.js"></script>
<script defer src="../../assets/libs/katex/auto-render.min.js"></script>
<script defer src="../../assets/js/lesson.js"></script>
<style>
  .comp-lab-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(116, 192, 227, 0.12);
    border: 1px solid var(--theme);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--theme);
    margin-bottom: 12px;
  }
  .matrix-calc-grid {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    flex-wrap: wrap;
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 20px;
    border-radius: var(--radius-md);
    margin: 20px 0;
  }
  .matrix-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  .matrix-box-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-muted);
  }
  .matrix-brackets {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 12px;
    border-left: 3px solid var(--theme);
    border-right: 3px solid var(--theme);
    padding: 8px 14px;
    background: var(--bg-alt);
    border-radius: 6px;
    font-family: monospace;
    font-size: 1.15rem;
    font-weight: bold;
    text-align: center;
  }
  .matrix-brackets.res {
    border-color: #ffd54f;
    color: #ffd54f;
  }
  .op-symbol {
    font-size: 1.6rem;
    font-weight: bold;
    color: var(--text-muted);
  }
  .swap-order-btn {
    background: linear-gradient(135deg, #74C0E3 0%, #4f8ef7 100%);
    color: #0b132b;
    border: none;
    padding: 8px 18px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.88rem;
    cursor: pointer;
    transition: all 0.25s ease;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .swap-order-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(116, 192, 227, 0.4);
  }
</style>
</head>
<body class="mode-read">

<!-- ═══════════ SEARCH OVERLAY ═══════════ -->
<div id="searchOverlay" class="search-overlay">
  <div class="search-box">
    <div class="search-input-row">
      <span class="search-icon">🔍</span>
      <input id="searchInput" class="search-input" placeholder="অধ্যায় খুঁজুন…" autocomplete="off"/>
      <button id="searchCloseBtn" class="search-close">ESC</button>
    </div>
    <div id="searchResults" class="search-results"></div>
  </div>
</div>

<!-- ═══════════ NAVBAR ═══════════ -->
<nav class="site-nav" id="siteNav">
  <div class="nav-inner">
    <a class="nav-logo" href="../../index.html">
      <svg class="pi-logo" viewBox="-50 -50 100 100" aria-label="৩ব্লু১ব্রাউন">
        <path fill="#74C0E3" d="M 0 0 L 0 -50 A 50 50 0 1 1 -50 0 z"/>
        <path fill="#8C6239" d="M 0 0 L 0 -50 A 50 50 0 0 0 -50 0 z"/>
        <circle cx="0" cy="0" r="22" fill="#000"/>
        <circle cx="-8" cy="-6" r="7" fill="#fff"/>
        <circle cx="8" cy="-6" r="7" fill="#fff"/>
        <circle cx="-7" cy="-6" r="3.5" fill="#000"/>
        <circle cx="9" cy="-6" r="3.5" fill="#000"/>
        <path d="M -10 6 Q 0 14 10 6" stroke="#fff" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      </svg>
      <div class="logo-text">
        <span class="logo-title">৩ব্লু১ব্রাউন বাংলা</span>
        <span class="logo-sub">লিনিয়ার অ্যালজেব্রা</span>
      </div>
    </a>

    <div class="nav-breadcrumb">
      <a href="../../index.html">হোম</a>
      <span>/</span>
      <a href="../../index.html#linear-algebra">লিনিয়ার অ্যালজেব্রা</a>
      <span>/</span>
      <span>অধ্যায় ০৪</span>
      <div class="nav-chapter-stepper">
        <a href="lesson_03.html" class="nav-step-btn" title="পূর্ববর্তী অধ্যায়: রৈখিক রূপান্তর ও ম্যাট্রিক্স">
          <svg viewBox="0 0 24 24" fill="none"><path d="M15 18l-6-6 6-6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </a>
        <span class="nav-step-label">০৪ / ০৫</span>
        <a href="lesson_05.html" class="nav-step-btn" title="পরবর্তী অধ্যায়: ত্রিমাত্রিক রৈখিক রূপান্তর">
          <svg viewBox="0 0 24 24" fill="none"><path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </a>
      </div>
    </div>

    <div class="nav-actions">
      <div class="mode-toggle">
        <button class="mode-btn active" data-mode="read">📖 পড়ুন</button>
        <button class="mode-btn" data-mode="watch">📺 দেখুন</button>
      </div>
      <button class="icon-btn" id="searchOpenBtn" title="অনুসন্ধান (Ctrl+K)">🔍</button>
      <button class="icon-btn" id="themeBtn" onclick="toggleTheme()" title="থিম পরিবর্তন">🌙</button>
    </div>
  </div>
</nav>

<!-- ═══════════ HERO — 2-column ═══════════ -->
<div class="lesson-hero">
  <div class="hero-bg-canvas"></div>
  <div class="hero-inner">
    <a class="back-link" href="../../index.html">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
      লিনিয়ার অ্যালজেব্রা
    </a>

    <div class="hero-grid">
      <!-- Left: Video Player -->
      <div>
        <div class="hero-video-wrap">
          <div id="heroLocalBox" class="local-video">
            <video id="mainVideo" controls preload="metadata"
                   src="../../media_vault/lesson_04/3b1b_lesson_04_bangla_dubbed_video.mp4">
            </video>
          </div>
          <div id="heroYtBox" class="yt-overlay">
            <iframe src="https://www.youtube.com/embed/XkY2DOUCWMU"
                    allowfullscreen allow="autoplay; encrypted-media"></iframe>
          </div>
        </div>
        <div class="video-switcher">
          <button id="heroBtn-local" class="vsw-btn active" onclick="switchHeroVideo('local')">🇧🇩 বাংলা ডাবড (লোকাল)</button>
          <button id="heroBtn-yt" class="vsw-btn" onclick="switchHeroVideo('yt')">▶ মূল ইউটিউব</button>
        </div>
      </div>

      <!-- Right: Metadata -->
      <div class="hero-meta fade-up delay-1">
        <div class="chapter-label">অধ্যায় ০৪ · লিনিয়ার অ্যালজেব্রার সারমর্ম</div>
        <h1 class="hero-title">ম্যাট্রিক্স গুণন — রূপান্তরের রচনা</h1>
        <p class="hero-desc">দুটি ম্যাট্রিক্সের গুণফল আসলে দুটি রূপান্তরকে পরপর প্রয়োগ করা। কেন গুণন ক্রমনির্ভর ($AB \neq BA$)? কেন এভাবে গুণ করা হয়? এই পাঠে পাবো সেই গভীর দৃশ্যমান জ্যামিতিক ব্যাখ্যা।</p>
        <div class="meta-list">
          <div class="meta-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            ১৫ আগস্ট, ২০১৬
          </div>
          <div class="meta-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            ১০:০৩ মিনিট
          </div>
          <div class="meta-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            ম্যাট্রিক্স গুণন, সংযোজন ও অ্যাসোসিয়েটিভিটি
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ═══════════ MASTER AUDIO BAR ═══════════ -->
<div class="master-audio-bar">
  <div class="audio-inner">
    <button class="audio-play-btn" id="audioPlayBtn">▶</button>
    <div class="audio-track-info">
      <div class="audio-track-title">অধ্যায় ০৪ — মাস্টার বাংলা ভয়েস ট্র্যাক (স্টুডিও মাস্টার)</div>
      <div class="audio-track-sub">Edge-TTS (bn-BD-PradeepNeural) · EBU R128 নরম্যালাইজড · জিরো ভোকাল ব্লিড</div>
    </div>
    <div class="audio-scrub-wrap">
      <div class="audio-scrub-bar" id="audioScrubBar">
        <div class="audio-scrub-fill" id="audioScrubFill"></div>
      </div>
      <div class="audio-time">
        <span id="audioCur">0:00</span> / <span id="audioDur">10:03</span>
      </div>
    </div>
    <div class="audio-speed-wrap">
      <button class="speed-btn active" data-speed="1">1×</button>
      <button class="speed-btn" data-speed="1.25">1.25×</button>
      <button class="speed-btn" data-speed="1.5">1.5×</button>
    </div>
    <input type="range" class="audio-vol" id="audioVol" min="0" max="1" step="0.05" value="1" title="ভলিউম"/>
  </div>
  <audio id="lessonAudio" preload="metadata" src="../../assets/audio/3b1b_lesson_04_bangla_dubbed_master.mp3"></audio>
</div>

<!-- ═══════════ LESSON BODY ═══════════ -->
<div class="lesson-body">

  <!-- ── READ MODE (default) ── -->
  <div class="read-mode">

    <!-- Table of Contents Card -->
    <div class="toc-card fade-up">
      <div class="toc-title">📋 বিষয়সূচি</div>
      <nav class="toc-list">
        <a href="#sec-composition">১. একের পর এক রূপান্তর — কম্পোজিশন</a>
        <a href="#sec-order-matters">২. ক্রম কেন গুরুত্বপূর্ণ? ($AB \neq BA$)</a>
        <a href="#sec-algebraic-computation">৩. প্রতীকী গণনা ও ভিত্তি ভেক্টর ট্র্যাকিং</a>
        <a href="#sec-associativity">৪. ম্যাট্রিক্স গুণনের সংযোগ বিধি (Associativity)</a>
        <a href="#sec-visualizer">৫. ইন্টারেক্টিভ কম্পোজিশন ল্যাব</a>
        <a href="#sec-quizzes">৬. অনুশীলন প্রশ্নমালা ও স্ব-মূল্যায়ন</a>
      </nav>
    </div>

    <!-- Article Content -->
    <article class="article">

      <!-- Chapter Quote -->
      <div class="chapter-quote">
        <span class="quote-mark">"</span>
        <p>ম্যাট্রিক্স গুণন কোনো মুখস্থ করার খটমটে নিয়ম নয়; এটি আসলে একটি রূপান্তরের ঠিক পর আরেকটি রূপান্তর প্রয়োগ করার জ্যামিতিক প্রক্রিয়া মাত্র।</p>
        <p class="attrib">— গ্রান্ট স্যান্ডারসন (Grant Sanderson)</p>
      </div>

      <!-- ─── SECTION 1: Applying One Transformation After Another ─── -->
      <section id="sec-composition">
        <h2>১. একের পর এক রূপান্তর — কম্পোজিশন</h2>

        <p>গত পর্বে আমরা দেখেছি কীভাবে যেকোনো রৈখিক রূপান্তরকে একটি ২×২ ম্যাট্রিক্সের সাহায্যে প্রকাশ করা যায়—যেখানে ম্যাট্রিক্সের কলাম দুটি হলো রূপান্তরিত ভিত্তি ভেক্টর $\hat{i}$ এবং $\hat{j}$-এর অবতরণ স্থানাঙ্ক।</p>

        <p>তবে বাস্তব গণিত এবং পদার্থবিজ্ঞানে প্রায়শই একটি রূপান্তর সম্পন্ন করার পর তার ওপর <strong>আরেকটি রূপান্তর</strong> কার্যকর করার প্রয়োজন পড়ে। ধরা যাক, আপনি প্রথমে সমতলকে ঘড়ির কাঁটার বিপরীতে ৯০° ঘোরালেন (Rotation), এবং তার পরপরই সমতলের ওপর একটি অনুভূমিক শিয়ার (Shear) প্রয়োগ করলেন।</p>

        <!-- Media Tab 1: rotate_shear_sequence -->
        <div class="media-tab-container">
          <div class="media-tab-nav">
            <button class="media-tab-btn active" onclick="switchMediaTab(this, 'img')">
              <svg width="18" height="18" viewBox="0 0 256 256" fill="currentColor"><path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40Zm0,16V158.75l-26.07-26.06a16,16,0,0,0-22.63,0l-20,20-44-44a16,16,0,0,0-22.62,0L40,149.37V56ZM40,172l52-52,80,80H40Zm176,28H194.63l-36-36,20-20L216,181.38V200ZM144,100a12,12,0,1,1,12,12A12,12,0,0,1,144,100Z"/></svg>
              <span>চিত্র (SVG)</span>
            </button>
            <button class="media-tab-btn" onclick="switchMediaTab(this, 'vid')">
              <svg width="18" height="18" viewBox="0 0 256 256" fill="currentColor"><path d="M164.44,105.34l-48-32A8,8,0,0,0,104,80v64a8,8,0,0,0,12.44,6.66l48-32a8,8,0,0,0,0-13.32ZM120,129.05V95l25.58,17ZM216,40H40A16,16,0,0,0,24,56V168a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40Zm0,128H40V56H216V168Zm16,40a8,8,0,0,1-8,8H32a8,8,0,0,1,0-16H224A8,8,0,0,1,232,208Z"/></svg>
              <span>অ্যানিমেশন (MP4)</span>
            </button>
          </div>
          <div class="media-tab-pane active" data-pane="img">
            <img src="figures/matrix-multiplication/rotate_shear_sequence.svg" alt="ঘূর্ণনের পর শিয়ার রূপান্তর"/>
          </div>
          <div class="media-tab-pane" data-pane="vid">
            <video loop muted playsinline controls src="figures/matrix-multiplication/rotate_shear_composition.mp4"></video>
          </div>
        </div>

        <p>শুরু থেকে শেষ পর্যন্ত পুরো ক্রিয়াটি কিন্তু সামগ্রিকভাবে আরেকটি নতুন একক রৈখিক রূপান্তর! এই সামগ্রিক রূপান্তরটিকে দুটি রূপান্তরের <strong>সংযোজন (Composition)</strong> বলা হয়।</p>

        <p>যেহেতু এটিও একটি রৈখিক রূপান্তর, তাই এর নিজস্ব একটি একক ম্যাট্রিক্স থাকা উচিত। সেই ম্যাট্রিক্সটি আমরা কীভাবে বের করব? বরাবরের মতোই সহজ—শুধুমাত্র ট্র্যাক করুন $\hat{i}$ এবং $\hat{j}$ শেষ পর্যন্ত কোথায় গিয়ে পৌঁছাল!</p>

        <figure class="lesson-figure">
          <img src="figures/matrix-multiplication/rotate_shear_record.svg" alt="ভিত্তি ভেক্টরের চূড়ান্ত গন্তব্য লিপিবদ্ধকরণ"/>
          <figcaption>ঘূর্ণন ও শিয়ার শেষে $\hat{i}$ পৌঁছায় $(1, 1)$-এ এবং $\hat{j}$ পৌঁছায় $(-1, 0)$-এ</figcaption>
        </figure>

        <div class="formula-box">
          $$\begin{bmatrix} 1 & 1 \\ 0 & 1 \end{bmatrix} \begin{bmatrix} 0 & -1 \\ 1 & 0 \end{bmatrix} = \begin{bmatrix} 1 & -1 \\ 1 & 0 \end{bmatrix}$$
        </div>

        <div class="callout callout-info">
          <strong>💡 ডান থেকে বামে পড়ার ঐতিহ্য:</strong> ফাংশন নোটেশনের কারণে ম্যাট্রিক্স গুণন সর্বদাই ডান থেকে বামে কার্যকর হয়। $B A \vec{v}$ এর অর্থ হলো—প্রথমে ভেক্টর $\vec{v}$-এর ওপর রূপান্তর $A$ প্রয়োগ করা হয়েছে, এবং তারপর তার ফলাফলের ওপর রূপান্তর $B$ প্রয়োগ করা হয়েছে।
        </div>
      </section>

      <!-- ─── SECTION 2: Why Order Matters ─── -->
      <section id="sec-order-matters">
        <h2>২. ক্রম কেন গুরুত্বপূর্ণ? ($AB \neq BA$)</h2>

        <p>বাস্তব সংখ্যার গুণনে $3 \times 5$ এবং $5 \times 3$ সম্পূর্ণ একই মান দেয়—যাকে আমরা গুণনের বিনিময় বিধি (Commutative Property) বলি। কিন্তু ম্যাট্রিক্স গুণনে <strong>ক্রম পরিবর্তন করলে ফলাফল সম্পূর্ণ বদলে যায়!</strong></p>

        <p>জ্যামিতিকভাবে এটি বোঝা অত্যন্ত স্পষ্ট: প্রথমে ৯০° ঘূর্ণন করে তারপর শিয়ার দিলে স্থানটি যেভাবে বাঁকে, প্রথমে শিয়ার করে তারপর ৯০° ঘোরালে স্থানটি মোটেও সেভাবে থাকে না!</p>

        <figure class="lesson-figure">
          <img src="figures/matrix-multiplication/rotate_shear_swap.svg" alt="রূপান্তরের ক্রম পরিবর্তনের দৃশ্যমান পার্থক্য"/>
          <figcaption>ক্রম পরিবর্তনের প্রমাণ: ঘূর্ণন + শিয়ার $\neq$ শিয়ার + ঘূর্ণন</figcaption>
        </figure>

        <div class="formula-box">
          $$AB \neq BA \quad \text{(ম্যাট্রিক্স গুণন বিনিময় বিধি মেনে চলে না)}$$
        </div>

        <p>গণিত শিক্ষার্থীদের সবচেয়ে বড় বিভ্রান্তি দূর হয় যখন তারা এটি জ্যামিতিকভাবে চিন্তা করে: স্থানকে ভিন্ন ক্রমে নাড়ালে ভিত্তি ভেক্টরগুলো সম্পূর্ণ আলাদা জায়গায় অবতরণ করে।</p>
      </section>

      <!-- ─── SECTION 3: Algebraic Computation ─── -->
      <section id="sec-algebraic-computation">
        <h2>৩. প্রতীকী গণনা ও ভিত্তি ভেক্টর ট্র্যাকিং</h2>

        <p>প্রতিবার ছবি না এঁকে খাতায় কীভাবে আমরা দুটি ম্যাট্রিক্স গুণ করব? অধিকাংশ পাঠ্যবই শিক্ষার্থীদের সারি ও কলামের গুণ ও যোগ মুখস্থ করতে বলে। কিন্তু আসুন দেখা যাক এর পেছনের আসল যুক্তি কী।</p>

        <figure class="lesson-figure">
          <img src="figures/matrix-multiplication/compound_multiply.svg" alt="ম্যাট্রিক্স গুণনের বীজগণিতীয় রূপ"/>
          <figcaption>প্রথম ম্যাট্রিক্সের কলামগুলোতে দ্বিতীয় রূপান্তর প্রয়োগ করাই গুণনের প্রকৃত অর্থ</figcaption>
        </figure>

        <p>ধরা যাক দুটি ম্যাট্রিক্স $M_1$ এবং $M_2$ গুণ করতে হবে:</p>

        <div class="formula-box">
          $$\begin{bmatrix} a & b \\ c & d \end{bmatrix} \begin{bmatrix} e & f \\ g & h \end{bmatrix} = \begin{bmatrix} ae + bg & af + bh \\ ce + dg & cf + dh \end{bmatrix}$$
        </div>

        <p>বামপাশের ম্যাট্রিক্সটি নির্দেশ করে রূপান্তরটি কীভাবে কাজ করে, আর ডানপাশের ম্যাট্রিক্সের প্রথম কলাম $\begin{bmatrix} e \\ g \end{bmatrix}$ হলো প্রথম রূপান্তরের পর $\hat{i}$-এর অবস্থান। সুতরাং এই ভেক্টরের ওপর দ্বিতীয় রূপান্তর প্রয়োগ করলে প্রথম কলামটি পাওয়া যায় $e\begin{bmatrix} a \\ c \end{bmatrix} + g\begin{bmatrix} b \\ d \end{bmatrix}$ হিসেবে!</p>
      </section>

      <!-- ─── SECTION 4: Associativity ─── -->
      <section id="sec-associativity">
        <h2>৪. ম্যাট্রিক্স গুণনের সংযোগ বিধি (Associativity)</h2>

        <p>যদিও ম্যাট্রিক্স গুণন বিনিময় বিধি মানে না ($AB \neq BA$), তবে এটি <strong>সংযোগ বিধি (Associative Property)</strong> অক্ষরে অক্ষরে পালন করে:</p>

        <div class="formula-box">
          $$(AB)C = A(BC)$$
        </div>

        <p>বীজগণিত দিয়ে এটি প্রমাণ করতে গেলে বহু পৃষ্ঠার ক্লান্তিকর হিসাব করতে হয়। কিন্তু জ্যামিতিক দৃষ্টিভঙ্গিতে এটি <strong>স্বতঃসিদ্ধ সত্য!</strong></p>

        <div class="media-tab-container">
          <div class="media-tab-pane active" data-pane="vid">
            <video loop muted playsinline controls src="figures/matrix-multiplication/associativity.mp4" style="width:100%;border-radius:8px;"></video>
          </div>
        </div>

        <p>কারণ তিনটি রূপান্তর $C$, তারপর $B$, এবং সবশেষে $A$ প্রয়োগ করার অর্থ হলো মহাবিশ্বের স্থানে একই তিনটি রূপান্তর একই ক্রমে সম্পন্ন করা। আপনি প্রথম দুটিকে আগে মনে মনে জোড়া লাগান কিংবা শেষের দুটিকে আগে হিসাব করুন—স্থানটির চূড়ান্ত রূপান্তর হুবহু একই থাকবে!</p>
      </section>

      <!-- ─── SECTION 5: Interactive Visualizer Lab ─── -->
      <section id="sec-visualizer">
        <h2>৫. ইন্টারেক্টিভ কম্পোজিশন ল্যাব</h2>
        <p>নিচের ল্যাবে আপনি দুটি রূপান্তরকে ধাপে ধাপে কার্যকর হতে দেখতে পারবেন। দেখুন কীভাবে ঘূর্ণন এবং শিয়ার একত্রিত হয়ে নতুন স্থান গঠন করে, এবং ক্রম অদল-বদল (Swap Order) করলে স্থানটি কতটা ভিন্ন রূপ নেয়!</p>

        <div class="viz-wrapper" id="compVizWrapper">
          <div class="viz-header">
            <div class="viz-header-left">
              <span>🔬 ম্যাট্রিক্স কম্পোজিশন সিমুলেটর — $A \times B$ বনাম $B \times A$</span>
            </div>
            <div class="viz-header-tools">
              <button class="viz-tool-btn" onclick="setCompStep(0)">আদি গ্রিড</button>
              <button class="viz-tool-btn" onclick="setCompStep(1)">১ম রূপান্তর</button>
              <button class="viz-tool-btn" onclick="setCompStep(2)">চূড়ান্ত সংযোজন</button>
              <button class="swap-order-btn" onclick="toggleCompOrder()">🔄 ক্রম বদলান (Swap Order)</button>
              <button class="viz-tool-btn" id="fsToggleBtn" onclick="toggleVizFullscreen('compVizWrapper')">⛶ ফুলস্ক্রিন</button>
            </div>
          </div>

          <div class="matrix-calc-grid">
            <div class="matrix-box">
              <span class="matrix-box-label" id="lblMat2">২য় রূপান্তর ($M_2$)</span>
              <div class="matrix-brackets" id="boxMat2">
                <span>1</span><span>1</span>
                <span>0</span><span>1</span>
              </div>
            </div>
            <span class="op-symbol">×</span>
            <div class="matrix-box">
              <span class="matrix-box-label" id="lblMat1">১ম রূপান্তর ($M_1$)</span>
              <div class="matrix-brackets" id="boxMat1">
                <span>0</span><span>-1</span>
                <span>1</span><span>0</span>
              </div>
            </div>
            <span class="op-symbol">=</span>
            <div class="matrix-box">
              <span class="matrix-box-label">যৌথ ম্যাট্রিক্স (Composite $C$)</span>
              <div class="matrix-brackets res" id="boxMatRes">
                <span>1</span><span>-1</span>
                <span>1</span><span>0</span>
              </div>
            </div>
          </div>

          <div class="viz-canvas-container">
            <canvas id="compCanvas" class="viz-canvas"></canvas>
          </div>

          <div class="viz-controls">
            <div style="font-size:0.9rem; color:var(--text-muted); text-align:center;" id="compStatusText">
              বর্তমান মোড: ঘূর্ণন ৯০° (প্রথমে) ➔ তারপর অনুভূমিক শিয়ার (দ্বিতীয়)
            </div>
          </div>
        </div>
      </section>

      <!-- ─── SECTION 6: Quizzes ─── -->
      <section id="sec-quizzes">
        <h2>৬. অনুশীলন প্রশ্নমালা ও স্ব-মূল্যায়ন</h2>

        <!-- Quiz 1 -->
        <div class="quiz-block"
             data-correct="2"
             data-correct-msg="অসাধারণ! ম্যাট্রিক্স গুণন ডান থেকে বামে কার্যকর হয়। সুতরাং $AB\vec{v}$ এর অর্থ প্রথমে $B$ প্রয়োগ করা এবং তারপর $A$।"
             data-wrong-msg="একটু স্মরণ করুন: ফাংশন লেখার নিয়ম কী? $f(g(x))$-এ কোন ফাংশনটি আগে এক্সের ওপর কাজ করে?"
             data-reveal-msg="সঠিক উত্তর: প্রথমে রূপান্তর B কার্যকর হবে, তারপর রূপান্তর A। ফাংশন নোটেশনের ঐতিহ্যের কারণে ম্যাট্রিক্স গুণন ডান থেকে বামে পরিচালিত হয়।">
          <div class="quiz-q">❓ গাণিতিক প্রকাশ $A B \vec{v}$-এ ভেক্টর $\vec{v}$-এর ওপর কোন রূপান্তরটি আগে কার্যকর হবে?</div>
          <div class="quiz-options">
            <div class="quiz-option" data-idx="0">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">প্রথমে $A$, তারপর $B$</div>
            </div>
            <div class="quiz-option" data-idx="1">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">উভয় রূপান্তর একসাথে একই মুহূর্তে</div>
            </div>
            <div class="quiz-option" data-idx="2">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">প্রথমে $B$, তারপর $A$</div>
            </div>
            <div class="quiz-option" data-idx="3">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">যে কোনোটি আগে করা যায়, কোনো পার্থক্য নেই</div>
            </div>
          </div>
          <div class="quiz-actions">
            <button class="quiz-check-btn" disabled>যাচাই করো</button>
            <button class="quiz-reveal-btn">উত্তর দেখাও</button>
          </div>
          <div class="quiz-feedback"></div>
        </div>

        <!-- Quiz 2 -->
        <div class="quiz-block"
             data-correct="1"
             data-correct-msg="একদম সঠিক! ম্যাট্রিক্স গুণন সাধারণ সংখ্যার মতো বিনিময় বিধি মেনে চলে না, কারণ জ্যামিতিকভাবে রূপান্তরের ক্রম পরিবর্তনের ফলে চূড়ান্ত স্থান ভিন্ন হয়।"
             data-wrong-msg="ভেবে দেখুন, ৯০° ঘূর্ণন করে শিয়ার দিলে স্থানটি যেখানে পৌঁছায়, আগে শিয়ার করে পরে ঘোরালে কি একই ফলাফল পাওয়া যায়?"
             data-reveal-msg="সঠিক উত্তর: মিথ্যা ($AB$ সাধারণত $BA$-এর সমান নয়)। একে নন-কমিউটেটিভিটি বলা হয়।">
          <div class="quiz-q">❓ সত্য বা মিথ্যা: যেকোনো দুটি বর্গ ম্যাট্রিক্স $A$ এবং $B$-এর জন্য সর্বদাই $AB = BA$ সত্য।</div>
          <div class="quiz-options">
            <div class="quiz-option" data-idx="0">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">সত্য — সংখ্যার গুণনের মতোই এটি সর্বদাই সমান হয়</div>
            </div>
            <div class="quiz-option" data-idx="1">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">মিথ্যা — ম্যাট্রিক্স গুণন ক্রমনির্ভর ($AB \neq BA$)</div>
            </div>
          </div>
          <div class="quiz-actions">
            <button class="quiz-check-btn" disabled>যাচাই করো</button>
            <button class="quiz-reveal-btn">উত্তর দেখাও</button>
          </div>
          <div class="quiz-feedback"></div>
        </div>

        <!-- Quiz 3 -->
        <div class="quiz-block"
             data-correct="0"
             data-correct-msg="চমৎকার! $(AB)C$ এবং $A(BC)$ উভয়ই মহাবিশ্বের স্থানে একই তিনটি রূপান্তর একই ক্রমে ($C \to B \to A$) সম্পন্ন করে, তাই ফলাফল সর্বদাই সমান।"
             data-wrong-msg="একটু ভাবুন: তিনটি রূপান্তরের প্রয়োগের ক্রম কি এখানে বদলে গেছে, নাকি শুধু হিসাবের বন্ধনী বদলেছে?"
             data-reveal-msg="সঠিক উত্তর: সংযোগ বিধি সর্বদাই সত্য $(AB)C = A(BC)$। রূপান্তরের জ্যামিতিক প্রক্রিয়া একই থাকায় বন্ধনীর অবস্থান ফলাফলে কোনো পরিবর্তন আনে না।">
          <div class="quiz-q">❓ সংযোগ বিধি $(AB)C = A(BC)$ সম্পর্কে নিচের কোন উক্তিটি জ্যামিতিকভাবে সত্য?</div>
          <div class="quiz-options">
            <div class="quiz-option" data-idx="0">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">এটি সর্বদাই সত্য, কারণ তিনটি রূপান্তরের সার্বিক প্রয়োগের ক্রম অপরিবর্তিত থাকে</div>
            </div>
            <div class="quiz-option" data-idx="1">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">এটি কখনোই সত্য নয়, কারণ ম্যাট্রিক্স গুণন বিনিময় বিধি মানে না</div>
            </div>
            <div class="quiz-option" data-idx="2">
              <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
              <div class="quiz-label">এটি কেবল তখনই সত্য হয় যখন ম্যাট্রিক্সগুলোর ডিটারমিন্যান্ট শূন্য হয়</div>
            </div>
          </div>
          <div class="quiz-actions">
            <button class="quiz-check-btn" disabled>যাচাই করো</button>
            <button class="quiz-reveal-btn">উত্তর দেখাও</button>
          </div>
          <div class="quiz-feedback"></div>
        </div>

      </section>

    </article>
  </div><!-- /read-mode -->

  <!-- ── WATCH MODE PANEL ── -->
  <div class="watch-mode-panel">
    <div class="watch-grid">
      <div>
        <div class="theater-player">
          <div id="watchLocalVideo">
            <video controls preload="metadata" style="width:100%;height:100%"
                   src="../../media_vault/lesson_04/3b1b_lesson_04_bangla_dubbed_video.mp4"></video>
          </div>
          <iframe id="watchYtEmbed" style="display:none;width:100%;height:100%;border:none"
                  src="https://www.youtube.com/embed/XkY2DOUCWMU" allowfullscreen></iframe>
        </div>
        <div class="theater-switcher">
          <button id="watchBtn-local" class="vsw-btn active" onclick="switchWatchVideo('local')">🇧🇩 বাংলা ডাবড</button>
          <button id="watchBtn-yt" class="vsw-btn" onclick="switchWatchVideo('yt')">▶ মূল ইউটিউব</button>
        </div>
        <div class="theater-info">
          <h3>ম্যাট্রিক্স গুণন — রূপান্তরের রচনা — অধ্যায় ৪</h3>
          <p>সম্পূর্ণ বাংলায় ডাব করা, EBU R128 লাউডনেস নরমালাইজড অডিও সহ।</p>
        </div>
      </div>

      <!-- Playlist Drawer -->
      <div class="playlist-drawer">
        <div class="playlist-header">📋 প্লেলিস্ট — লিনিয়ার অ্যালজেব্রা</div>
        <a class="playlist-item" href="lesson_01.html">
          <div class="playlist-num">১</div>
          <div class="playlist-item-info">
            <div class="playlist-item-title">ভেক্টর আসলে কী?</div>
            <div class="playlist-item-meta">অধ্যায় ১</div>
          </div>
        </a>
        <a class="playlist-item" href="lesson_02.html">
          <div class="playlist-num">২</div>
          <div class="playlist-item-info">
            <div class="playlist-item-title">রৈখিক সমন্বয়, স্প্যান ও ভিত্তি</div>
            <div class="playlist-item-meta">অধ্যায় ২</div>
          </div>
        </a>
        <a class="playlist-item" href="lesson_03.html">
          <div class="playlist-num">৩</div>
          <div class="playlist-item-info">
            <div class="playlist-item-title">রৈখিক রূপান্তর ও ম্যাট্রিক্স</div>
            <div class="playlist-item-meta">অধ্যায় ৩</div>
          </div>
        </a>
        <a class="playlist-item active" href="lesson_04.html">
          <div class="playlist-num">৪</div>
          <div class="playlist-item-info">
            <div class="playlist-item-title">ম্যাট্রিক্স গুণন — রূপান্তরের রচনা</div>
            <div class="playlist-item-meta">অধ্যায় ৪ · চলমান</div>
          </div>
        </a>
        <a class="playlist-item" href="lesson_05.html">
          <div class="playlist-num">৫</div>
          <div class="playlist-item-info">
            <div class="playlist-item-title">ত্রিমাত্রিক রৈখিক রূপান্তর</div>
            <div class="playlist-item-meta">অধ্যায় ৫</div>
          </div>
        </a>
      </div>
    </div>
  </div><!-- /watch-mode-panel -->

</div><!-- /lesson-body -->

<!-- ═══════════ BOTTOM CHAPTER NAVIGATION ═══════════ -->
<div class="chapter-nav-cards">
  <a class="chapter-nav-card" href="lesson_03.html">
    <div class="nav-arrow">←</div>
    <div>
      <div class="nav-dir">পূর্ববর্তী অধ্যায়</div>
      <div class="nav-title">অধ্যায় ০৩ — রৈখিক রূপান্তর ও ম্যাট্রিক্স</div>
    </div>
  </a>
  <a class="chapter-nav-card next-card" href="lesson_05.html">
    <div class="nav-arrow">→</div>
    <div>
      <div class="nav-dir">পরবর্তী অধ্যায়</div>
      <div class="nav-title">অধ্যায় ০৫ — ত্রিমাত্রিক রৈখিক রূপান্তর</div>
    </div>
  </a>
</div>

<!-- ═══════════ FOOTER ═══════════ -->
<footer class="site-footer">
  <p>৩ব্লু১ব্রাউন বাংলা প্ল্যাটফর্ম · <a href="https://www.3blue1brown.com" target="_blank">3blue1brown.com</a> থেকে অনুপ্রাণিত</p>
  <p>মূল পাঠ: Grant Sanderson · বাংলা ডাবিং: Edge-TTS bn-BD-PradeepNeural · গণিত: KaTeX v0.16.11 (অফলাইন)</p>
</footer>

<!-- ═══════════ COMPOSITION VISUALIZER CANVAS SCRIPT ═══════════ -->
<script>
(function () {
  const canvas = document.getElementById('compCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const SCALE = 45;
  let W, H;

  function resize() {
    W = canvas.parentElement.clientWidth || 600;
    H = 440;
    canvas.width = W;
    canvas.height = H;
    draw();
  }
  window.addEventListener('resize', resize);

  const CX = () => W / 2;
  const CY = () => H / 2;

  // Transformations:
  // Rot90: [[0, -1], [1, 0]]
  // Shear: [[1, 1], [0, 1]]
  const rotM = { a: 0, b: -1, c: 1, d: 0, name: "ঘূর্ণন ৯০°" };
  const shearM = { a: 1, b: 1, c: 0, d: 1, name: "অনুভূমিক শিয়ার" };

  let isRotFirst = true;
  let curStep = 2; // 0: identity, 1: first trans, 2: composite

  function multiply(m2, m1) {
    return {
      a: m2.a * m1.a + m2.b * m1.c,
      b: m2.a * m1.b + m2.b * m1.d,
      c: m2.c * m1.a + m2.d * m1.c,
      d: m2.c * m1.b + m2.d * m1.d
    };
  }

  function updateRibbon() {
    const m1 = isRotFirst ? rotM : shearM;
    const m2 = isRotFirst ? shearM : rotM;
    const res = multiply(m2, m1);

    document.getElementById('lblMat1').textContent = `১ম: ${m1.name}`;
    document.getElementById('lblMat2').textContent = `২য়: ${m2.name}`;

    document.getElementById('boxMat1').innerHTML = `<span>${m1.a}</span><span>${m1.b}</span><span>${m1.c}</span><span>${m1.d}</span>`;
    document.getElementById('boxMat2').innerHTML = `<span>${m2.a}</span><span>${m2.b}</span><span>${m2.c}</span><span>${m2.d}</span>`;
    document.getElementById('boxMatRes').innerHTML = `<span>${res.a}</span><span>${res.b}</span><span>${res.c}</span><span>${res.d}</span>`;

    const statusEl = document.getElementById('compStatusText');
    if (curStep === 0) {
      statusEl.textContent = "ধাপ ০: আদি সমতল স্থানাঙ্ক গ্রিড (কোনো রূপান্তর কার্যকর হয়নি)";
    } else if (curStep === 1) {
      statusEl.textContent = `ধাপ ১: কেবল ১ম রূপান্তর [${m1.name}] প্রয়োগ করা হয়েছে`;
    } else {
      statusEl.textContent = `ধাপ ২: ১ম [${m1.name}]-এর পর ২য় [${m2.name}] সমন্বিত হয়েছে (${isRotFirst ? 'ঘূর্ণন ➔ শিয়ার' : 'শিয়ার ➔ ঘূর্ণন'})`;
    }
  }

  window.setCompStep = function(step) {
    curStep = step;
    updateRibbon();
    draw();
  };

  window.toggleCompOrder = function() {
    isRotFirst = !isRotFirst;
    updateRibbon();
    draw();
  };

  function getCurrentMatrix() {
    if (curStep === 0) return { a: 1, b: 0, c: 0, d: 1 };
    const m1 = isRotFirst ? rotM : shearM;
    if (curStep === 1) return m1;
    const m2 = isRotFirst ? shearM : rotM;
    return multiply(m2, m1);
  }

  function arrow(sx, sy, ex, ey, col, lw) {
    lw = lw || 3.0;
    const dx = ex - sx, dy = ey - sy, len = Math.hypot(dx, dy);
    if (len < 2) return;
    const ang = Math.atan2(dy, dx), hs = 11;
    ctx.save();
    ctx.strokeStyle = col; ctx.fillStyle = col;
    ctx.lineWidth = lw; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey); ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - hs * Math.cos(ang - 0.45), ey - hs * Math.sin(ang - 0.45));
    ctx.lineTo(ex - hs * Math.cos(ang + 0.45), ey - hs * Math.sin(ang + 0.45));
    ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  function draw() {
    if (!W) return;
    const isDark = document.documentElement.classList.contains('dark') || document.documentElement.getAttribute('data-theme') === 'dark';
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = isDark ? '#0b0c16' : '#f8f9fe';
    ctx.fillRect(0, 0, W, H);

    const cx = CX(), cy = CY();

    // Standard Cartesian Background Grid
    ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    ctx.lineWidth = 1;
    for (let x = cx % SCALE; x < W; x += SCALE) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    for (let y = cy % SCALE; y < H; y += SCALE) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

    const M = getCurrentMatrix();
    const ix = M.a, iy = M.c;
    const jx = M.b, jy = M.d;

    // Transformed Grid lines
    ctx.lineWidth = 1.2;
    const R = 18;
    for (let k = -R; k <= R; k++) {
      ctx.strokeStyle = (k === 0) ? (isDark ? 'rgba(105,240,174,0.45)' : 'rgba(46,125,50,0.4)') : (isDark ? 'rgba(79,195,247,0.18)' : 'rgba(2,119,189,0.18)');
      ctx.beginPath();
      const p1x = cx + (k * ix - R * jx) * SCALE, p1y = cy - (k * iy - R * jy) * SCALE;
      const p2x = cx + (k * ix + R * jx) * SCALE, p2y = cy - (k * iy + R * jy) * SCALE;
      ctx.moveTo(p1x, p1y); ctx.lineTo(p2x, p2y); ctx.stroke();

      ctx.strokeStyle = (k === 0) ? (isDark ? 'rgba(233,69,96,0.45)' : 'rgba(194,24,91,0.4)') : (isDark ? 'rgba(255,213,79,0.18)' : 'rgba(245,127,23,0.18)');
      ctx.beginPath();
      const q1x = cx + (-R * ix + k * jx) * SCALE, q1y = cy - (-R * iy + k * jy) * SCALE;
      const q2x = cx + (R * ix + k * jx) * SCALE, q2y = cy - (R * iy + k * jy) * SCALE;
      ctx.moveTo(q1x, q1y); ctx.lineTo(q2x, q2y); ctx.stroke();
    }

    // Transformed Unit Square
    ctx.fillStyle = isDark ? 'rgba(255, 213, 79, 0.22)' : 'rgba(255, 179, 0, 0.25)';
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + ix * SCALE, cy - iy * SCALE);
    ctx.lineTo(cx + (ix + jx) * SCALE, cy - (iy + jy) * SCALE);
    ctx.lineTo(cx + jx * SCALE, cy - jy * SCALE);
    ctx.closePath();
    ctx.fill();

    // Basis Vectors
    const scrIx = cx + ix * SCALE, scrIy = cy - iy * SCALE;
    const scrJx = cx + jx * SCALE, scrJy = cy - jy * SCALE;

    arrow(cx, cy, scrIx, scrIy, '#69f0ae', 3.5);
    arrow(cx, cy, scrJx, scrJy, '#ffd54f', 3.5);

    ctx.font = 'bold 13px sans-serif';
    ctx.fillStyle = '#69f0ae';
    ctx.fillText(`î [${ix.toFixed(1)}, ${iy.toFixed(1)}]`, scrIx + 8, scrIy - 6);
    ctx.fillStyle = '#ffd54f';
    ctx.fillText(`ĵ [${jx.toFixed(1)}, ${jy.toFixed(1)}]`, scrJx + 8, scrJy - 6);
  }

  updateRibbon();
  resize();
})();
</script>

</body>
</html>
'''

output_path = 'departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/linear_algebra/lesson_04.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully wrote {len(html_content)} bytes to {output_path}")
