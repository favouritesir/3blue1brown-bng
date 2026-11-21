/**
 * 3Blue1Brown Bengali Platform — Isolated Web Components Library (R&D Sandbox)
 * 
 * Modular Custom Elements replicating 100% of the visual fidelity, CSS layout,
 * and interactivity of the 3Blue1Brown Bengali lesson experience.
 * 
 * Components defined:
 *  - <b1b-search-overlay>: Floating search modal with Ctrl+K shortcut
 *  - <b1b-stepper>: Chapter progression pill stepper (e.g. ০১ / ০৫)
 *  - <b1b-navbar>: Fixed header with exact Pi creature SVG, breadcrumbs, stepper, mode pills & actions
 *  - <b1b-hero-player>: Two-column 3B1B hero with dual-mode video switcher & lesson metadata
 *  - <b1b-watch-panel>: Theater mode player with dual-mode switcher & playlist drawer
 *  - <b1b-quiz>: Self-scoring interactive math quiz with KaTeX auto-render
 *  - <b1b-chapter-nav>: Bottom chapter progression cards (prev/next)
 *  - <b1b-footer>: Official platform footer with credits and KaTeX notice
 */

(function() {
  'use strict';

  // Canonical course sizes — single source of truth for chapter steppers.
  // Pages still carry `chapter-total="০৫"` from an early prototype; the navbar
  // derives the real total from here so every lesson auto-fixes in one place.
  const B1B_COURSES = {
    linear_algebra: { total: 15, name: 'লিনিয়ার অ্যালজেব্রা' },
    calculus: { total: 12, name: 'ক্যালকুলাস' },
    neural_networks: { total: 4, name: 'নিউরাল নেটওয়ার্ক' },
    differential_equations: { total: 6, name: 'ডিফারেনশিয়াল সমীকরণ' },
    probability: { total: 6, name: 'সম্ভাব্যতা তত্ত্ব' },
    lockdown_math: { total: 10, name: 'লকডাউন ম্যাথ' }
  };
  const BN_DIGITS = ['০','১','২','৩','৪','৫','৬','৭','৮','৯'];
  const toBn = (n) => String(n).split('').map(d => BN_DIGITS[+d] || d).join('');
  const fromBn = (s) => parseInt(String(s || '').split('').map(d => {
    const i = BN_DIGITS.indexOf(d);
    return i >= 0 ? String(i) : d;
  }).join(''), 10);
  const courseKeyFromPath = () => {
    const m = window.location.pathname.replace(/\\/g, '/').match(/\/courses\/([^/]+)\//);
    return m ? m[1] : null;
  };

  // Inject Custom Element layout CSS
  const compStyles = document.createElement('style');
  compStyles.id = 'b1b-components-base-styles';
  compStyles.textContent = `
    b1b-navbar, b1b-hero-player, b1b-watch-panel, b1b-chapter-nav, b1b-chapter-list, b1b-media-tab, b1b-quiz, b1b-footer, b1b-search-overlay, b1b-section, b1b-callout, b1b-figure, b1b-formula, b1b-quote, b1b-toc-sidebar, b1b-interactive-lab, b1b-back-to-top {
      display: block;
    }
    b1b-watch-panel > [slot="playlist"] {
      display: none !important;
    }
    body.mode-read b1b-watch-panel {
      display: none !important;
    }
    body.mode-watch b1b-chapter-list,
    body.mode-watch .chapter-list-card {
      display: none !important;
    }
    b1b-chapter-list:not([data-rendered]) {
      display: none !important;
    }
    @media (max-width: 1024px) {
      .nav-breadcrumb > a,
      .nav-breadcrumb > span:not(.nav-step-label) {
        display: none !important;
      }
      .nav-breadcrumb {
        flex: initial;
        margin: 0 auto;
      }
    }
    @media (max-width: 768px) {
      :root {
        --navbar-h: 56px;
      }
      .site-nav {
        height: var(--navbar-h);
        overflow-x: hidden;
      }
      .nav-inner {
        padding: 0 8px !important;
        gap: 6px !important;
        justify-content: space-between !important;
      }
      .nav-logo {
        gap: 6px !important;
        flex-shrink: 0 !important;
      }
      .pi-logo {
        width: 32px !important;
        height: 32px !important;
      }
      .logo-title {
        font-size: 0.8rem !important;
      }
      .logo-sub {
        display: none !important;
      }
      .nav-breadcrumb {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0 !important;
        flex: 1 1 auto !important;
        margin: 0 !important;
      }
      .nav-breadcrumb > a,
      .nav-breadcrumb > span:not(.nav-step-label) {
        display: none !important;
      }
      .nav-chapter-stepper,
      b1b-stepper .nav-chapter-stepper {
        display: inline-flex !important;
        margin-left: 0 !important;
        padding: 2px 6px !important;
        gap: 3px !important;
        border-radius: 14px !important;
        box-shadow: 0 1px 6px rgba(116, 192, 227, 0.22) !important;
        background: linear-gradient(135deg, rgba(116, 192, 227, 0.25), rgba(79, 195, 247, 0.15)) !important;
      }
      .nav-step-btn {
        width: 22px !important;
        height: 22px !important;
      }
      .nav-step-btn svg {
        width: 11px !important;
        height: 11px !important;
        stroke-width: 3.5 !important;
      }
      .nav-step-label {
        font-size: 0.74rem !important;
        font-weight: 800 !important;
        padding: 0 3px !important;
      }
      .nav-actions {
        gap: 4px !important;
        flex-shrink: 0 !important;
      }
      .mode-toggle {
        padding: 2px !important;
        gap: 1px !important;
        border-radius: 12px !important;
      }
      .mode-toggle .mode-btn {
        padding: 3px 6px !important;
        font-size: 0.75rem !important;
        border-radius: 10px !important;
      }
      .mode-toggle .mode-btn .mode-label {
        display: none !important;
      }
      .font-toggle-btn {
        padding: 3px 6px !important;
        font-size: 0.72rem !important;
        border-radius: 10px !important;
      }
      .icon-btn {
        width: 26px !important;
        height: 26px !important;
        font-size: 0.8rem !important;
        border-radius: 8px !important;
      }
    }
    @media (max-width: 580px) {
      .logo-title {
        display: none !important;
      }
      .nav-inner {
        padding: 0 8px !important;
        gap: 6px !important;
      }
    }
    @media (max-width: 440px) {
      .font-toggle-btn {
        display: none !important;
      }
      .nav-inner {
        padding: 0 6px !important;
        gap: 4px !important;
      }
    }
    /* Media Tab styles */
    .media-tab-container {
      margin: 28px 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }
    .media-tab-nav {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-alt, #1a1a24);
      border: 1px solid var(--border, rgba(255,255,255,0.12));
      padding: 5px;
      border-radius: var(--radius-md, 12px);
      margin-bottom: 16px;
    }
    .media-tab-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 18px;
      border-radius: var(--radius-sm, 8px);
      border: none;
      background: transparent;
      color: var(--text-muted, #8b949e);
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      font-family: inherit;
    }
    .media-tab-btn:hover {
      color: var(--text, #f0f6fc);
      background: rgba(255, 255, 255, 0.05);
    }
    .media-tab-btn.active {
      background: var(--theme, #74C0E3);
      color: #0b0f19;
      box-shadow: 0 2px 8px rgba(116, 192, 227, 0.3);
    }
    .media-tab-pane {
      display: none;
      width: 100%;
      max-width: 760px;
      border-radius: var(--radius-md, 12px);
      overflow: hidden;
      box-shadow: var(--shadow, 0 8px 24px rgba(0,0,0,0.3));
      border: 1px solid var(--border, rgba(255,255,255,0.12));
      background: #000;
    }
    .media-tab-pane.active {
      display: block;
      animation: b1bFadeIn 0.25s ease;
    }
    .media-tab-pane img,
    .media-tab-pane video {
      display: block;
      width: 100%;
      height: auto;
      border-radius: var(--radius-md, 12px);
    }
    .media-tab-caption {
      font-size: 0.86rem;
      color: var(--text-muted, #8b949e);
      margin-top: 10px;
      font-style: italic;
      font-weight: 500;
      text-align: center;
      max-width: 760px;
    }
    @keyframes b1bFadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }
    /* Bottom Chapter List component styles */
    .chapter-list-card {
      max-width: 1100px;
      margin: 0 auto 48px;
      padding: 0 24px;
    }
    .chapter-list-inner {
      background: var(--bg-alt, #151821);
      border: 1px solid var(--border, rgba(255,255,255,0.12));
      border-radius: var(--radius-lg, 16px);
      overflow: hidden;
      box-shadow: var(--shadow, 0 4px 16px rgba(0,0,0,0.2));
    }
    .chapter-list-header {
      padding: 16px 24px;
      border-bottom: 1px solid var(--border, rgba(255,255,255,0.12));
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .chapter-list-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text, #f0f6fc);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .chapter-list-course-link {
      font-size: 0.82rem;
      color: var(--theme, #74C0E3);
      text-decoration: none;
      font-weight: 600;
    }
    .chapter-list-course-link:hover {
      text-decoration: underline;
    }
  `;
  if (!document.getElementById('b1b-components-base-styles')) {
    document.head.appendChild(compStyles);
  }

  /* ============================================================
     1. EXACT PI CREATURE SVG LOGO
     ============================================================ */
  const PI_CREATURE_SVG = `
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
  `;

  /* ============================================================
     2. <b1b-search-overlay>
     ============================================================ */
  class B1bSearchOverlay extends HTMLElement {
    connectedCallback() {
      if (this.querySelector('#searchOverlay')) return;
      this.innerHTML = `
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
      `;
    }
  }

  /* ============================================================
     3. <b1b-stepper>
     ============================================================ */
  class B1bStepper extends HTMLElement {
    static get observedAttributes() {
      return ['current', 'total', 'prev-url', 'prev-title', 'next-url', 'next-title'];
    }

    connectedCallback() {
      this.render();
    }

    attributeChangedCallback() {
      this.render();
    }

    render() {
      const current = this.getAttribute('current') || '০১';
      const ck = courseKeyFromPath();
      const cfg = ck ? B1B_COURSES[ck] : null;
      const total = cfg ? toBn(cfg.total) : (this.getAttribute('total') || '০৫');
      const prevUrl = this.getAttribute('prev-url') || '';
      const prevTitle = this.getAttribute('prev-title') || 'পূর্ববর্তী অধ্যায় নেই';
      const nextUrl = this.getAttribute('next-url') || '';
      const nextTitle = this.getAttribute('next-title') || 'পরবর্তী অধ্যায়';

      const prevHtml = prevUrl && prevUrl !== '#'
        ? `<a href="${prevUrl}" class="nav-step-btn" title="${prevTitle}">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
           </a>`
        : `<span class="nav-step-btn disabled" title="${prevTitle}">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
           </span>`;

      const nextHtml = nextUrl && nextUrl !== '#'
        ? `<a href="${nextUrl}" class="nav-step-btn" title="${nextTitle}">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
           </a>`
        : `<span class="nav-step-btn disabled" title="${nextTitle}">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
           </span>`;

      this.innerHTML = `
        <div class="nav-chapter-stepper">
          ${prevHtml}
          <span class="nav-step-label">${current} / ${total}</span>
          ${nextHtml}
        </div>
      `;
    }
  }

  /* ============================================================
     4. <b1b-navbar>
     ============================================================ */
  class B1bNavbar extends HTMLElement {
    static get observedAttributes() {
      return [
        'course-title', 'course-url', 'home-url', 'chapter-num', 'chapter-total',
        'prev-url', 'prev-title', 'next-url', 'next-title', 'active-mode'
      ];
    }

    connectedCallback() {
      this.render();
      this.bindEvents();
    }

    attributeChangedCallback() {
      this.render();
      this.bindEvents();
    }

    render() {
      const ck = courseKeyFromPath();
      const cfg = ck ? B1B_COURSES[ck] : null;
      const courseTitle = cfg ? cfg.name : (this.getAttribute('course-title') || 'লিনিয়ার অ্যালজেব্রা');
      const courseUrl   = this.getAttribute('course-url') || '../../index.html#linear-algebra';
      const homeUrl     = this.getAttribute('home-url') || '../../index.html';
      // Derive chapter number from the URL unless explicitly supplied; total
      // ALWAYS comes from the canonical config (ignores stale ০৫ attributes).
      const urlNum = (window.location.pathname.match(/lesson_(\d+)\.html/) || [])[1];
      const chapterNum  = this.getAttribute('chapter-num') || (urlNum ? toBn(parseInt(urlNum, 10)) : '০১');
      const chapterTotal = cfg ? toBn(cfg.total) : (this.getAttribute('chapter-total') || '০৫');

      // Prev/next links: derive from the canonical course map so stale
      // prototype attributes (e.g. lesson_05 → lesson_04) cannot survive.
      const n = fromBn(chapterNum);
      let prevUrl = this.getAttribute('prev-url') || '';
      let nextUrl = this.getAttribute('next-url') || 'lesson_02.html';
      if (cfg && Number.isFinite(n)) {
        prevUrl = n > 1 ? `lesson_${String(n - 1).padStart(2, '0')}.html` : '';
        nextUrl = n < cfg.total ? `lesson_${String(n + 1).padStart(2, '0')}.html` : '';
      }
      const prevTitle = prevUrl ? 'পূর্ববর্তী অধ্যায়' : 'পূর্ববর্তী অধ্যায় নেই';
      const nextTitle = nextUrl ? 'পরবর্তী অধ্যায়' : 'শেষ অধ্যায়';
      const activeMode  = this.getAttribute('active-mode') || 'read';

      const prevHtml = prevUrl && prevUrl !== '#'
        ? `<a href="${prevUrl}" class="nav-step-btn" title="${prevTitle}">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
           </a>`
        : `<span class="nav-step-btn disabled" title="${prevTitle}">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
           </span>`;

      const nextHtml = nextUrl && nextUrl !== '#'
        ? `<a href="${nextUrl}" class="nav-step-btn" title="${nextTitle}">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
           </a>`
        : `<span class="nav-step-btn disabled" title="${nextTitle}">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
           </span>`;

      const isDark = document.documentElement.classList.contains('dark') || document.documentElement.getAttribute('data-theme') === 'dark';
      const themeIcon = isDark ? '🌙' : '☀️';

      const font = document.documentElement.getAttribute('data-font') || 'sans';
      const fontLabel = font === 'serif' ? 'অ (সেরিফ)' : 'অ (সানস)';

      this.innerHTML = `
        <nav class="site-nav" id="siteNav">
          <div class="nav-inner">
            <a class="nav-logo" href="${homeUrl}">
              ${PI_CREATURE_SVG}
              <div class="logo-text">
                <span class="logo-title">৩ব্লু১ব্রাউন বাংলা</span>
                <span class="logo-sub">${courseTitle}</span>
              </div>
            </a>

            <div class="nav-breadcrumb">
              <a href="${homeUrl}">হোম</a>
              <span>/</span>
              <a href="${courseUrl}">${courseTitle}</a>
              <span>/</span>
              <span>অধ্যায় ${chapterNum}</span>
              <b1b-stepper
                current="${chapterNum}"
                total="${chapterTotal}"
                prev-url="${prevUrl}"
                prev-title="${prevTitle}"
                next-url="${nextUrl}"
                next-title="${nextTitle}">
              </b1b-stepper>
            </div>

            <div class="nav-actions">
              <!-- Mode Toggle -->
              <div class="mode-toggle">
                <button class="mode-btn ${activeMode === 'read' ? 'active' : ''}" data-mode="read"><span class="mode-icon">📖</span> <span class="mode-label">পড়ুন</span></button>
                <button class="mode-btn ${activeMode === 'watch' ? 'active' : ''}" data-mode="watch"><span class="mode-icon">📺</span> <span class="mode-label">দেখুন</span></button>
              </div>
              <a href="../../board.html" class="icon-btn" title="📊 মিশন কন্ট্রোল ও লাইভ ট্র্যাকার বোর্ড" style="text-decoration:none;font-size:0.9rem;">📊</a>
              <button class="icon-btn" id="searchOpenBtn" title="অনুসন্ধান (Ctrl+K)">🔍</button>
              <button class="font-toggle-btn" id="fontBtn" onclick="toggleFont()" title="ফন্ট পরিবর্তন (হিন্দ শিলিগুড়ি / নোটো সেরিফ)">${fontLabel}</button>
              <button class="icon-btn" id="themeBtn" onclick="toggleTheme()" title="থিম পরিবর্তন">${themeIcon}</button>
            </div>
          </div>
        </nav>
      `;
    }

    bindEvents() {
      // Connect mode buttons with setMode
      const modeBtns = this.querySelectorAll('.mode-btn');
      modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const mode = btn.dataset.mode;
          if (typeof window.setMode === 'function') {
            window.setMode(mode);
          } else {
            document.body.className = document.body.className.replace(/\bmode-\w+/g, '').trim();
            document.body.classList.add('mode-' + mode);
            modeBtns.forEach(b => b.classList.toggle('active', b === btn));
            localStorage.setItem('3b1b-mode', mode);
          }
          this.setAttribute('active-mode', mode);
          this.dispatchEvent(new CustomEvent('b1b-mode-change', { detail: { mode }, bubbles: true }));
        });
      });

      // Search button
      const searchBtn = this.querySelector('#searchOpenBtn');
      if (searchBtn) {
        searchBtn.addEventListener('click', () => {
          const overlay = document.getElementById('searchOverlay');
          const input   = document.getElementById('searchInput');
          if (overlay) {
            overlay.classList.add('open');
            input && input.focus();
          }
        });
      }
    }
  }

  /* ============================================================
     5. <b1b-hero-player>
     ============================================================ */
  class B1bHeroPlayer extends HTMLElement {
    static get observedAttributes() {
      return [
        'course-title', 'course-url', 'chapter-label', 'title', 'desc',
        'video-src', 'yt-id', 'date', 'author', 'author-url', 'translation',
        'github-url', 'voice-badge'
      ];
    }

    connectedCallback() {
      this.render();
      this.bindEvents();
    }

    attributeChangedCallback() {
      this.render();
      this.bindEvents();
    }

    render() {
      const courseTitle  = this.getAttribute('course-title') || 'লিনিয়ার অ্যালজেব্রা';
      const courseUrl    = this.getAttribute('course-url') || '../../index.html';
      const chapterLabel = this.getAttribute('chapter-label') || 'অধ্যায় ০১ · লিনিয়ার অ্যালজেব্রার সারমর্ম';
      const title        = this.getAttribute('title') || 'ভেক্টর আসলে কী? | Vectors, what even are they? (Essence of linear algebra, chapter 1)';
      const desc         = this.getAttribute('desc') || 'ভেক্টরের তিনটি ভিন্ন ব্যাখ্যা — পদার্থবিদ, কম্পিউটার বিজ্ঞানী ও গণিতবিদের দৃষ্টিভঙ্গি থেকে — এবং ভেক্টর যোগ ও স্কেলার গুণনের অন্তর্দৃষ্টি।';
      const videoSrc     = this.getAttribute('video-src') || '../../media_vault/lesson_01/3b1b_lesson_01_bangla_dubbed_video.mp4';
      const ytId         = this.getAttribute('yt-id') || 'fNk_zzaMoSs';
      const date         = this.getAttribute('date') || '৬ আগস্ট, ২০১৬';
      const author       = this.getAttribute('author') || 'Grant Sanderson';
      const authorUrl    = this.getAttribute('author-url') || 'https://www.3blue1brown.com/about';
      const translation  = this.getAttribute('translation') || 'বাংলা রূপান্তর: Grant Sanderson (3Blue1Brown) | বাংলা ডাবিং ও পাঠ: STEM টিম';
      const githubUrl    = this.getAttribute('github-url') || 'https://github.com/3b1b/videos/blob/master/_2016/eola/chapter1.py';
      const voiceBadge   = this.getAttribute('voice-badge') || 'বাংলা ভয়েস: Edge-TTS bn-BD-PradeepNeural · ০% ইংলিশ ব্লিড';

      this.innerHTML = `
        <div class="lesson-hero">
          <div class="hero-bg-canvas"></div>
          <div class="hero-inner">
            <a class="back-link" href="${courseUrl}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
              ${courseTitle}
            </a>

            <div class="hero-grid">
              <!-- Left: Video Player -->
              <div>
                <div class="hero-video-wrap">
                  <div id="heroLocalBox" class="local-video">
                    <video id="mainVideo" controls preload="metadata" src="${videoSrc}"></video>
                  </div>
                  <div id="heroYtBox" class="yt-overlay">
                    <iframe src="https://www.youtube.com/embed/${ytId}"
                            allowfullscreen allow="autoplay; encrypted-media"></iframe>
                  </div>
                </div>
                <div class="video-switcher">
                  <button id="heroBtn-local" class="vsw-btn active" onclick="switchHeroVideo('local')">🇧🇩 বাংলা ডাবড (লোকাল)</button>
                  <button id="heroBtn-yt" class="vsw-btn" onclick="switchHeroVideo('yt')">▶ অরিজিনাল ভিডিও</button>
                </div>
              </div>

              <!-- Right: Metadata -->
              <div class="hero-meta fade-up delay-1">
                <div class="chapter-label">${chapterLabel}</div>
                <h1 class="hero-title">${title}</h1>
                <p class="hero-desc">${desc}</p>
                <div class="meta-list">
                  <div class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    ${date}
                  </div>
                  <div class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    পাঠ রচনা: <a href="${authorUrl}" target="_blank">${author}</a>
                  </div>
                  <div class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    ${translation}
                  </div>
                  <div class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                    <a href="${githubUrl}" target="_blank">সোর্স কোড (GitHub)</a>
                  </div>
                  <div class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
                    ${voiceBadge}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    bindEvents() {
      // Fallback switchHeroVideo if lesson.js not yet bound
      if (typeof window.switchHeroVideo !== 'function') {
        window.switchHeroVideo = function(mode) {
          const localBox = document.getElementById('heroLocalBox');
          const ytBox    = document.getElementById('heroYtBox');
          const btnLocal = document.getElementById('heroBtn-local');
          const btnYt    = document.getElementById('heroBtn-yt');
          if (!localBox || !ytBox) return;

          if (mode === 'local') {
            const ifr = ytBox.querySelector('iframe');
            if (ifr) ifr.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
            localBox.classList.remove('hidden');
            localBox.style.display = 'block';
            ytBox.classList.remove('active');
            ytBox.classList.add('hidden');
            ytBox.style.display = 'none';
            btnLocal && btnLocal.classList.add('active');
            btnYt && btnYt.classList.remove('active');
          } else {
            const vid = localBox.querySelector('video');
            if (vid) vid.pause();
            if (window.narrationEngine && window.narrationEngine.isPlaying) {
              window.narrationEngine.pause();
            }
            localBox.classList.add('hidden');
            localBox.style.display = 'none';
            ytBox.classList.remove('hidden');
            ytBox.classList.add('active');
            ytBox.style.display = 'block';
            btnYt && btnYt.classList.add('active');
            btnLocal && btnLocal.classList.remove('active');
          }
        };
      }
    }
  }

  /* ============================================================
     6. <b1b-watch-panel>
     ============================================================ */
  class B1bWatchPanel extends HTMLElement {
    static get observedAttributes() {
      return ['video-src', 'yt-id', 'title', 'subtitle', 'playlist-title'];
    }

    connectedCallback() {
      setTimeout(() => {
        this.render();
        this.bindEvents();
      }, 0);
    }

    attributeChangedCallback() {
      if (this._rendered) {
        this.render();
        this.bindEvents();
      }
    }

    render() {
      this._rendered = true;
      const videoSrc = this.getAttribute('video-src') || '../../media_vault/lesson_01/3b1b_lesson_01_bangla_dubbed_video.mp4';
      const ytId     = this.getAttribute('yt-id') || 'fNk_zzaMoSs';
      const title    = this.getAttribute('title') || 'ভেক্টর আসলে কী? | Vectors, what even are they? — অধ্যায় ১';
      const subtitle = this.getAttribute('subtitle') || 'সম্পূর্ণ প্রমিত বাংলায় ডাব করা, EBU R128 লাউডনেস নরমালাইজড অডিও এবং জিরো ইংলিশ ভোকাল ব্লিড মোড সহ।';
      const playlistTitle = this.getAttribute('playlist-title') || '📋 প্লেলিস্ট — লিনিয়ার অ্যালজেব্রা';

      // Capture slotted playlist or render default 5 chapters
      const slotted = this.querySelector('[slot="playlist"]');
      let playlistHtml = '';
      if (slotted) {
        playlistHtml = slotted.innerHTML;
        slotted.remove();
      } else {
        playlistHtml = `
          <a class="playlist-item active" href="lesson_01.html">
            <div class="playlist-num">১</div>
            <div class="playlist-item-info">
              <div class="playlist-item-title">ভেক্টর আসলে কী?</div>
              <div class="playlist-item-meta">অধ্যায় ১ · চলমান</div>
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
          <a class="playlist-item" href="lesson_04.html">
            <div class="playlist-num">৪</div>
            <div class="playlist-item-info">
              <div class="playlist-item-title">ম্যাট্রিক্স গুণন — রূপান্তরের রচনা</div>
              <div class="playlist-item-meta">অধ্যায় ৪</div>
            </div>
          </a>
          <a class="playlist-item" href="lesson_05.html">
            <div class="playlist-num">৫</div>
            <div class="playlist-item-info">
              <div class="playlist-item-title">ত্রিমাত্রিক রৈখিক রূপান্তর</div>
              <div class="playlist-item-meta">অধ্যায় ৫</div>
            </div>
          </a>
        `;
      }

      this.innerHTML = `
        <div class="watch-mode-panel">
          <div class="watch-grid">
            <div>
              <div class="theater-player">
                <div id="watchLocalVideo">
                  <video controls preload="metadata" style="width:100%;height:100%" src="${videoSrc}"></video>
                </div>
                <iframe id="watchYtEmbed" style="display:none;width:100%;height:100%;border:none"
                        src="https://www.youtube.com/embed/${ytId}" allowfullscreen></iframe>
              </div>
              <div class="theater-switcher">
                <button id="watchBtn-local" class="vsw-btn active" onclick="switchWatchVideo('local')">🇧🇩 বাংলা ডাবড</button>
                <button id="watchBtn-yt" class="vsw-btn" onclick="switchWatchVideo('yt')">▶ অরিজিনাল ভিডিও</button>
              </div>
              <div class="theater-info">
                <h3>${title}</h3>
                <p>${subtitle}</p>
              </div>
            </div>

            <!-- Playlist Drawer -->
            <div class="playlist-drawer">
              <div class="playlist-header">${playlistTitle}</div>
              ${playlistHtml}
            </div>
          </div>
        </div>
      `;
    }

    bindEvents() {
      if (typeof window.switchWatchVideo !== 'function') {
        window.switchWatchVideo = function(mode) {
          const lv = document.getElementById('watchLocalVideo');
          const yt = document.getElementById('watchYtEmbed');
          const bL = document.getElementById('watchBtn-local');
          const bY = document.getElementById('watchBtn-yt');

          if (mode === 'local') {
            const ifr = yt && (yt.tagName === 'IFRAME' ? yt : yt.querySelector('iframe'));
            if (ifr && ifr.contentWindow) ifr.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
            if (lv) lv.style.display = 'block';
            if (yt) yt.style.display = 'none';
            bL && bL.classList.add('active');
            bY && bY.classList.remove('active');
          } else {
            const v = lv && lv.querySelector('video');
            if (v) v.pause();
            if (window.narrationEngine && window.narrationEngine.isPlaying) {
              window.narrationEngine.pause();
            }
            if (lv) lv.style.display = 'none';
            if (yt) yt.style.display = 'block';
            bY && bY.classList.add('active');
            bL && bL.classList.remove('active');
          }
        };
      }
    }
  }

  /* ============================================================
     7. <b1b-chapter-nav>
     ============================================================ */
  class B1bChapterNav extends HTMLElement {
    static get observedAttributes() {
      return ['prev-url', 'prev-title', 'prev-dir', 'next-url', 'next-title', 'next-dir'];
    }

    connectedCallback() {
      this.render();
    }

    attributeChangedCallback() {
      this.render();
    }

    render() {
      const ck = courseKeyFromPath();
      const cfg = ck ? B1B_COURSES[ck] : null;
      const n = fromBn((window.location.pathname.match(/lesson_(\d+)\.html/) || [])[1] || '');
      let prevUrl   = this.getAttribute('prev-url') || '';
      let nextUrl   = this.getAttribute('next-url') || 'lesson_02.html';
      if (cfg && Number.isFinite(n)) {
        prevUrl = n > 1 ? `lesson_${String(n - 1).padStart(2, '0')}.html` : '';
        nextUrl = n < cfg.total ? `lesson_${String(n + 1).padStart(2, '0')}.html` : '';
      }
      const prevTitle = this.getAttribute('prev-title') || 'শুরু';
      const prevDir   = this.getAttribute('prev-dir') || 'পূর্ববর্তী অধ্যায়';
      const nextTitle = this.getAttribute('next-title') || 'পরবর্তী অধ্যায়';
      const nextDir   = this.getAttribute('next-dir') || 'পরবর্তী অধ্যায়';

      const prevHtml = prevUrl && prevUrl !== '#'
        ? `<a class="chapter-nav-card prev-card" href="${prevUrl}">
             <div class="nav-arrow">←</div>
             <div>
               <div class="nav-dir">${prevDir}</div>
               <div class="nav-title">${prevTitle}</div>
             </div>
           </a>`
        : `<div class="chapter-nav-card disabled">
             <div class="nav-arrow">←</div>
             <div>
               <div class="nav-dir">${prevDir}</div>
               <div class="nav-title">${prevTitle}</div>
             </div>
           </div>`;

      const nextHtml = nextUrl && nextUrl !== '#'
        ? `<a class="chapter-nav-card next-card" href="${nextUrl}">
             <div class="nav-arrow">→</div>
             <div>
               <div class="nav-dir">${nextDir}</div>
               <div class="nav-title">${nextTitle}</div>
             </div>
           </a>`
        : `<div class="chapter-nav-card disabled">
             <div class="nav-arrow">→</div>
             <div>
               <div class="nav-dir">${nextDir}</div>
               <div class="nav-title">${nextTitle}</div>
             </div>
           </div>`;

      this.innerHTML = `
        <div class="chapter-nav-cards">
          ${prevHtml}
          ${nextHtml}
        </div>
      `;
    }
  }

  /* ============================================================
     8. <b1b-quiz>
     ============================================================ */
  class B1bQuiz extends HTMLElement {
    static get observedAttributes() {
      return ['question', 'correct', 'correct-msg', 'wrong-msg', 'reveal-msg'];
    }

    connectedCallback() {
      // SYNCHRONOUS render prevents flash-of-unstyled content and keeps the
      // quiz DOM stable before lesson.js/narration_engine.js initialize.
      if (this.dataset.rendered) return;
      this.dataset.rendered = 'true';
      this.render();
      this.initQuizLogic();
    }

    render() {
      const question   = this.getAttribute('question') || '❓ প্রশ্ন:';
      const correct    = this.getAttribute('correct') || '0';
      const correctMsg = this.getAttribute('correct-msg') || 'চমৎকার! সঠিক উত্তর!';
      const wrongMsg   = this.getAttribute('wrong-msg') || 'ভুল হয়েছে। আবার চেষ্টা করো!';
      const revealMsg  = this.getAttribute('reveal-msg') || 'সঠিক উত্তর যাচাই করো।';

      // Read slotted options or children
      const optionNodes = Array.from(this.querySelectorAll('[slot="option"], b1b-option, .quiz-option-text'));
      let optionsHtml = '';
      if (optionNodes.length > 0) {
        optionsHtml = optionNodes.map((opt, i) => `
          <div class="quiz-option" data-idx="${i}">
            <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
            <div class="quiz-label">${opt.innerHTML}</div>
          </div>
        `).join('');
      } else {
        // Fallback default options
        optionsHtml = `
          <div class="quiz-option" data-idx="0">
            <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
            <div class="quiz-label">বিকল্প ১</div>
          </div>
          <div class="quiz-option" data-idx="1">
            <div class="quiz-radio"><div class="quiz-radio-dot"></div></div>
            <div class="quiz-label">বিকল্প ২</div>
          </div>
        `;
      }

      this.innerHTML = `
        <div class="quiz-block"
             data-correct="${correct}"
             data-correct-msg="${correctMsg}"
             data-wrong-msg="${wrongMsg}"
             data-reveal-msg="${revealMsg}">
          <div class="quiz-q">${question}</div>
          <div class="quiz-options">
            ${optionsHtml}
          </div>
          <div class="quiz-actions">
            <button class="quiz-check-btn" disabled>যাচাই করো</button>
            <button class="quiz-reveal-btn">উত্তর দেখাও</button>
          </div>
          <div class="quiz-feedback"></div>
        </div>
      `;
    }

    initQuizLogic() {
      const block     = this.querySelector('.quiz-block');
      if (!block) return;
      block.dataset.customBound = 'true';
      const options   = block.querySelectorAll('.quiz-option');
      const checkBtn  = block.querySelector('.quiz-check-btn');
      const revealBtn = block.querySelector('.quiz-reveal-btn');
      const feedback  = block.querySelector('.quiz-feedback');
      const correct   = parseInt(block.dataset.correct || '0', 10);
      let selected    = null;

      function renderKaTeX(target) {
        if (!target) return;
        if (typeof window.renderMathInElement === 'function') {
          window.renderMathInElement(target, {
            delimiters: [
              { left: '$$', right: '$$', display: true },
              { left: '$',  right: '$',  display: false },
              { left: '\\(', right: '\\)', display: false },
              { left: '\\[', right: '\\]', display: true }
            ],
            throwOnError: false
          });
        } else {
          let retries = 0;
          const pollTimer = setInterval(() => {
            retries++;
            if (typeof window.renderMathInElement === 'function') {
              clearInterval(pollTimer);
              window.renderMathInElement(target, {
                delimiters: [
                  { left: '$$', right: '$$', display: true },
                  { left: '$',  right: '$',  display: false },
                  { left: '\\(', right: '\\)', display: false },
                  { left: '\\[', right: '\\]', display: true }
                ],
                throwOnError: false
              });
            } else if (retries > 25) {
              clearInterval(pollTimer);
            }
          }, 60);
        }
      }

      options.forEach((opt, i) => {
        opt.addEventListener('click', () => {
          if (opt.classList.contains('locked')) return;
          options.forEach(o => o.classList.remove('selected'));
          opt.classList.add('selected');
          selected = i;
          if (checkBtn) checkBtn.disabled = false;
        });
      });

      checkBtn && checkBtn.addEventListener('click', () => {
        if (selected === null) return;
        options.forEach((opt, i) => {
          opt.classList.add('locked');
          if (i === correct) opt.classList.add('correct');
          else if (i === selected && i !== correct) opt.classList.add('wrong');
        });
        if (feedback) {
          feedback.classList.add('show');
          if (selected === correct) {
            feedback.classList.add('correct-fb');
            feedback.classList.remove('wrong-fb');
            feedback.innerHTML = '✅ ' + (block.dataset.correctMsg || 'চমৎকার! সঠিক উত্তর!');
          } else {
            feedback.classList.add('wrong-fb');
            feedback.classList.remove('correct-fb');
            feedback.innerHTML = '❌ ' + (block.dataset.wrongMsg || 'ভুল হয়েছে। আবার চেষ্টা করো!');
          }
          renderKaTeX(feedback);
        }
        if (checkBtn) checkBtn.disabled = true;
      });

      revealBtn && revealBtn.addEventListener('click', () => {
        options.forEach((opt, i) => {
          opt.classList.add('locked');
          if (i === correct) opt.classList.add('correct');
        });
        if (feedback) {
          feedback.classList.add('show', 'correct-fb');
          feedback.classList.remove('wrong-fb');
          feedback.innerHTML = '💡 ' + (block.dataset.revealMsg || ('সঠিক উত্তর: ' + (correct + 1) + 'নং বিকল্প'));
          renderKaTeX(feedback);
        }
      });

      // Render math on entire quiz block immediately
      renderKaTeX(block);
    }
  }

  /* ============================================================
     9. <b1b-footer>
     ============================================================ */
  class B1bFooter extends HTMLElement {
    connectedCallback() {
      this.innerHTML = `
        <footer class="site-footer">
          <p>৩ব্লু১ব্রাউন বাংলা প্ল্যাটফর্ম · <a href="https://www.3blue1brown.com" target="_blank">3blue1brown.com</a> থেকে অনুপ্রাণিত</p>
          <p>মূল পাঠ: Grant Sanderson · বাংলা ডাবিং: Edge-TTS bn-BD-PradeepNeural · গণিত: KaTeX v0.16.11 (অফলাইন)</p>
        </footer>
      `;
    }
  }

  /* ============================================================
     10. REGISTER CUSTOM ELEMENTS IN REGISTRY
     ============================================================ */
  if (!customElements.get('b1b-search-overlay')) {
    customElements.define('b1b-search-overlay', B1bSearchOverlay);
  }
  if (!customElements.get('b1b-stepper')) {
    customElements.define('b1b-stepper', B1bStepper);
  }
  if (!customElements.get('b1b-navbar')) {
    customElements.define('b1b-navbar', B1bNavbar);
  }
  if (!customElements.get('b1b-hero-player')) {
    customElements.define('b1b-hero-player', B1bHeroPlayer);
  }
  if (!customElements.get('b1b-watch-panel')) {
    customElements.define('b1b-watch-panel', B1bWatchPanel);
  }
  if (!customElements.get('b1b-chapter-nav')) {
    customElements.define('b1b-chapter-nav', B1bChapterNav);
  }
  if (!customElements.get('b1b-quiz')) {
    customElements.define('b1b-quiz', B1bQuiz);
  }
  if (!customElements.get('b1b-footer')) {
    customElements.define('b1b-footer', B1bFooter);
  }

  // Export for programmatic usage if needed
  window.B1bComponents = {
    PI_CREATURE_SVG,
    B1bSearchOverlay,
    B1bStepper,
    B1bNavbar,
    B1bHeroPlayer,
    B1bWatchPanel,
    B1bChapterNav,
    B1bQuiz,
    B1bFooter
  };

  /* ============================================================
     11. <b1b-quote> : Chapter & Mathematical Quotes
     Attributes:
       - author : 'হের্মান ওয়াইল'
     ============================================================ */
  class B1bQuote extends HTMLElement {
    connectedCallback() {
      // SYNCHRONOUS render is a hard contract: narration_engine.js parses the
      // DOM on DOMContentLoaded and must see .chapter-quote immediately.
      if (this.dataset.rendered) return;
      this.dataset.rendered = 'true';
      const author = this.getAttribute('author') || '';
      let text = this.getAttribute('text') || this.innerHTML.trim();
      text = text.replace(/^<p[^>]*>/i, '').replace(/<\/p>$/i, '').trim();

      this.innerHTML = `
        <div class="chapter-quote">
          <span class="quote-mark">"</span>
          <p>${text}</p>
          ${author ? `<p class="attrib">— ${author}</p>` : ''}
        </div>
      `;
    }
  }

  /* ============================================================
     12. <b1b-callout> : Highlight / Notes / Warning Boxes
     Attributes:
       - type  : 'blue' | 'gold' | 'green' | 'purple' | 'red'
       - icon  : '📐', '💻', '💡', '⚠️'
       - title : 'পদার্থবিজ্ঞানের দৃষ্টিভঙ্গি'
     ============================================================ */
  class B1bCallout extends HTMLElement {
    connectedCallback() {
      // SYNCHRONOUS render — required for 1:1 DOM-to-audio cue parity.
      if (this.dataset.rendered) return;
      this.dataset.rendered = 'true';
      const type  = this.getAttribute('type') || 'blue';
      const icon  = this.getAttribute('icon');
      const title = this.getAttribute('title') || '';
      const titleText = icon ? `${icon} ${title}` : title;
      const content = this.innerHTML;

      this.innerHTML = `
        <div class="callout callout-${type}">
          ${titleText ? `<div class="callout-title">${titleText}</div>` : ''}
          <div class="callout-body">${content}</div>
        </div>
      `;
      if (typeof window.renderMathInElement === 'function') {
        window.renderMathInElement(this, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$',  right: '$',  display: false }
          ],
          throwOnError: false
        });
      }
    }
  }

  /* ============================================================
     13. <b1b-figure> : Diagrams, SVGs, and Visual Captions
     Attributes:
       - src   : Image / SVG path
       - alt   : Alt description
       - caption: Detailed pedagogical caption
     ============================================================ */
  class B1bFigure extends HTMLElement {
    connectedCallback() {
      // Guard against double-render: parent components move child nodes on
      // render (disconnect/reconnect), which would wrap the figure twice.
      if (this.dataset.rendered) return;
      this.dataset.rendered = 'true';
      const src = this.getAttribute('src');
      const alt = this.getAttribute('alt') || '৩ব্লু১ব্রাউন চিত্র';
      const caption = this.getAttribute('caption');
      const inner = this.innerHTML.trim();

      const mediaHtml = src ? `<img src="${src}" alt="${alt}"/>` : inner;
      const capHtml = caption ? `<figcaption>${caption}</figcaption>` : '';

      this.innerHTML = `
        <figure class="lesson-figure">
          ${mediaHtml}
          ${capHtml}
        </figure>
      `;
    }
  }

  /* ============================================================
     14. <b1b-formula> : Centered Mathematical Equation Box
     Attributes:
       - math  : LaTeX formula string (e.g. '\vec{v} = \begin{bmatrix} x \\ y \end{bmatrix}')
     ============================================================ */
  class B1bFormula extends HTMLElement {
    connectedCallback() {
      const math = this.getAttribute('math') || this.innerHTML;
      const cleanMath = math.trim().replace(/^\$\$|\$\$$/g, '');
      this.innerHTML = `
        <div class="formula-box">
          $$${cleanMath}$$
        </div>
      `;
      if (typeof window.renderMathInElement === 'function') {
        window.renderMathInElement(this, {
          delimiters: [{ left: '$$', right: '$$', display: true }],
          throwOnError: false
        });
      }
    }
  }

  /* ============================================================
     15. <b1b-section> : Reading Section Container
     Attributes:
       - id          : 'sec-interpretations'
       - title       : 'ভেক্টরের তিনটি দৃষ্টিভঙ্গি'
     ============================================================ */
  class B1bSection extends HTMLElement {
    connectedCallback() {
      // Guard: parent components (e.g. <b1b-article>) re-create children when
      // they render. Without this guard a section would be wrapped twice.
      if (this.dataset.rendered) return;
      this.dataset.rendered = 'true';
      const secId = this.getAttribute('id') || '';
      const title = this.getAttribute('title') || '';
      const noNarration = this.getAttribute('data-no-narration') === 'true';
      this.removeAttribute('id');

      // IMPORTANT: move the existing child nodes (do NOT re-parse innerHTML).
      // Re-parsing would create brand-new <b1b-quiz> instances that skip their
      // connectedCallback (because data-rendered was serialized) and therefore
      // lose their click handlers.
      const section = document.createElement('section');
      if (secId) section.id = secId;
      if (noNarration) section.setAttribute('data-no-narration', 'true');
      section.innerHTML = `
        <div class="section-header-wrap">
          ${title ? `<h2>${title}</h2>` : ''}
          <div class="section-narration-bar">
            <button class="btn-section-narrate" type="button">
              <svg fill="currentColor" height="14" viewbox="0 0 24 24" width="14"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"></path></svg>
              🔊 শিক্ষক অডিও শুনুন
            </button>
          </div>
        </div>
      `;
      while (this.firstChild) section.appendChild(this.firstChild);
      this.innerHTML = '';
      this.appendChild(section);
    }
  }

  /* ============================================================
     16. <b1b-toc-sidebar> : Table of Contents (Card or Sidebar)
     Attributes:
       - title   : '📋 বিষয়সূচি'
       - variant : 'card' | 'sidebar'
     ============================================================ */
  class B1bTocSidebar extends HTMLElement {
    connectedCallback() {
      const title = this.getAttribute('title') || '📋 বিষয়সূচি';
      const variant = this.getAttribute('variant') || 'card';
      const items = this.querySelectorAll('a');
      let linksHtml = '';
      items.forEach(a => {
        const href = a.getAttribute('href') || '#';
        const text = a.textContent.trim();
        linksHtml += `<a href="${href}" class="${variant === 'sidebar' ? 'toc-sidebar-link' : ''}">${text}</a>`;
      });

      if (variant === 'sidebar') {
        this.innerHTML = `
          <aside class="toc-sidebar-card">
            <div class="toc-sidebar-header">
              <span class="toc-sidebar-icon">📑</span>
              <h4>${title}</h4>
            </div>
            <nav class="toc-sidebar-nav">
              ${linksHtml}
            </nav>
          </aside>
        `;
      } else {
        this.innerHTML = `
          <div class="toc-card fade-up">
            <div class="toc-title">${title}</div>
            <nav class="toc-list">
              ${linksHtml}
            </nav>
          </div>
        `;
      }
    }
  }

  /* ============================================================
     17. <b1b-interactive-lab> : Interactive Canvas/SVG Simulation Lab
     Attributes:
       - title      : 'ভেক্টর কোঅর্ডিনেট সমতল — ড্র্যাগ করে পরীক্ষা করো!'
       - wrapper-id : 'vecVizWrapper'
     ============================================================ */
  class B1bInteractiveLab extends HTMLElement {
    connectedCallback() {
      setTimeout(() => {
        if (this.dataset.rendered) return;
        this.dataset.rendered = 'true';
        const title = this.getAttribute('title') || 'ভেক্টর কোঅর্ডিনেট সমতল — ড্র্যাগ করে পরীক্ষা করো!';
        const wrapperId = this.getAttribute('wrapper-id') || 'vecVizWrapper';
        const inner = this.innerHTML;

        this.innerHTML = `
          <div class="viz-wrapper" id="${wrapperId}">
            <div class="viz-header">
              <div class="viz-header-left">
                <span>🔬 ${title}</span>
              </div>
              <div class="viz-header-tools">
                <button type="button" class="viz-tool-btn" onclick="resetVectorVisualizer()">↺ রিসেট</button>
                <button type="button" class="viz-tool-btn" id="fsToggleBtnL01" onclick="toggleVizFullscreen('${wrapperId}')">⛶ ফুলস্ক্রিন</button>
              </div>
            </div>
            ${inner}
          </div>
        `;

        if (typeof window.initSvgVisualizer === 'function') {
          window.initSvgVisualizer();
        }
      }, 0);
    }
  }

  /* ============================================================
     18. <b1b-back-to-top> : Smart Scroll To Top Floating Button
     ============================================================ */
  class B1bBackToTop extends HTMLElement {
    connectedCallback() {
      // Avoid duplicate button if lesson.js already created #jumpToTopBtn or will create it
      if (document.getElementById('jumpToTopBtn')) {
        this.innerHTML = '';
        this.style.display = 'none';
        return;
      }
      this.innerHTML = `
        <button id="b1bBackToTopBtn" class="jump-to-top-btn" title="পৃষ্ঠার শুরুতে ফিরে যান" aria-label="পৃষ্ঠার শুরুতে ফিরে যান">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="18 15 12 9 6 15"></polyline>
          </svg>
          <span class="jump-tooltip">উপরে যান</span>
        </button>
      `;

      const btn = this.querySelector('#b1bBackToTopBtn');
      this._checkScroll = () => {
        // If lesson.js created jumpToTopBtn later, remove this one to prevent duplicates
        if (document.getElementById('jumpToTopBtn') && btn) {
          this.innerHTML = '';
          this.style.display = 'none';
          return;
        }
        if (window.scrollY > 300) {
          btn.classList.add('visible');
        } else {
          btn.classList.remove('visible');
        }
      };

      window.addEventListener('scroll', this._checkScroll, { passive: true });
      this._checkScroll();

      btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    disconnectedCallback() {
      if (this._checkScroll) {
        window.removeEventListener('scroll', this._checkScroll);
      }
    }
  }

  /* ============================================================
     19. <b1b-series-card> : Homepage Course Series Card
     Attributes:
       - title, lessons, level, desc, url, color
     ============================================================ */
  class B1bSeriesCard extends HTMLElement {
    connectedCallback() {
      const title   = this.getAttribute('title') || 'কোর্স শিরোনাম';
      const lessons = this.getAttribute('lessons') || '০টি পাঠ';
      const level   = this.getAttribute('level') || 'ইন্টারমিডিয়েট';
      const desc    = this.getAttribute('desc') || '';
      const url     = this.getAttribute('url') || '#';
      const color   = this.getAttribute('color') || 'var(--theme)';
      const icon    = this.getAttribute('icon') || '📐';

      this.innerHTML = `
        <a class="series-card" href="${url}" style="border-top: 3px solid ${color};">
          <div class="series-card-header">
            <div class="series-card-icon" style="background:${color}22; color:${color};">${icon}</div>
            <span class="series-card-badge">${level}</span>
          </div>
          <h3 class="series-card-title">${title}</h3>
          <p class="series-card-desc">${desc}</p>
          <div class="series-card-footer">
            <span class="series-card-count">📚 ${lessons}</span>
            <span class="series-card-arrow" style="color:${color};">শুরু করুন →</span>
          </div>
        </a>
      `;
    }
  }

  /* ============================================================
     20. <b1b-media-tab> : Dual Image / Video Toggle Switcher
     Supports:
       <b1b-media-tab>
         <div slot="image"><img ... /></div>
         <div slot="video"><video controls ...></video></div>
         <div slot="caption">ক্যাপশন...</div>
       </b1b-media-tab>
     ============================================================ */
  class B1bMediaTab extends HTMLElement {
    static get observedAttributes() {
      return ['active-tab', 'caption'];
    }

    connectedCallback() {
      setTimeout(() => {
        if (this.dataset.rendered) return;
        this.dataset.rendered = 'true';
        this.render();
      }, 0);
    }

    disconnectedCallback() {
      // Pause only. Never remove `src`: parent components (e.g. <b1b-section>)
      // move child nodes on render, which disconnects/reconnects this element.
      // Stripping src here permanently breaks the video after re-insertion.
      const vid = this.querySelector('video');
      if (vid) {
        try { vid.pause(); } catch (e) {}
      }
    }

    render() {
      const activeTab = this.getAttribute('active-tab') || 'image';
      const attrCaption = this.getAttribute('caption') || '';

      // Find slotted content
      const imageSlot = this.querySelector('[slot="image"]') || this.querySelector('img');
      const videoSlot = this.querySelector('[slot="video"]') || this.querySelector('video');
      const captionSlot = this.querySelector('[slot="caption"]') || this.querySelector('figcaption');

      if (imageSlot && !imageSlot.getAttribute('loading')) {
        imageSlot.setAttribute('loading', 'lazy');
      }
      if (videoSlot && !videoSlot.getAttribute('preload')) {
        videoSlot.setAttribute('preload', 'none');
      }

      const imageContent = imageSlot ? (imageSlot.outerHTML || imageSlot.innerHTML) : '';
      const videoContent = videoSlot ? (videoSlot.outerHTML || videoSlot.innerHTML) : '';
      const captionContent = captionSlot ? captionSlot.innerHTML : attrCaption;

      const hasImage = !!imageContent;
      const hasVideo = !!videoContent;

      // Determine initial active tab
      const isVideoActive = activeTab === 'video' || (!hasImage && hasVideo);

      this.innerHTML = `
        <div class="media-tab-container">
          <div class="media-tab-nav" role="tablist" aria-label="চিত্র ও ভিডিও প্রদর্শন">
            <button type="button" class="media-tab-btn tab-btn-img ${!isVideoActive ? 'active' : ''}" data-tab="image" role="tab" aria-selected="${!isVideoActive}">
              <span>🖼️ Image</span>
            </button>
            <button type="button" class="media-tab-btn tab-btn-vid ${isVideoActive ? 'active' : ''}" data-tab="video" role="tab" aria-selected="${isVideoActive}">
              <span>🎬 Video</span>
            </button>
          </div>
          <div class="media-tab-pane pane-image ${!isVideoActive ? 'active' : ''}" data-pane="image">
            ${imageContent}
          </div>
          <div class="media-tab-pane pane-video ${isVideoActive ? 'active' : ''}" data-pane="video">
            ${videoContent}
          </div>
          ${captionContent ? `<figcaption class="media-tab-caption">${captionContent}</figcaption>` : ''}
        </div>
      `;

      this.bindEvents();
    }

    bindEvents() {
      const btnImg = this.querySelector('.tab-btn-img');
      const btnVid = this.querySelector('.tab-btn-vid');
      const paneImg = this.querySelector('.pane-image');
      const paneVid = this.querySelector('.pane-video');

      const switchTab = (tab) => {
        if (tab === 'image') {
          btnImg && btnImg.classList.add('active');
          btnImg && btnImg.setAttribute('aria-selected', 'true');
          btnVid && btnVid.classList.remove('active');
          btnVid && btnVid.setAttribute('aria-selected', 'false');

          paneImg && paneImg.classList.add('active');
          paneVid && paneVid.classList.remove('active');

          // Pause video if playing
          if (paneVid) {
            const vid = paneVid.querySelector('video');
            if (vid) vid.pause();
          }
        } else {
          // Pause any other global audio/video playing
          if (window.narrationEngine && window.narrationEngine.isPlaying) {
            window.narrationEngine.pause();
          }
          document.querySelectorAll('video, audio').forEach(media => {
            if (media !== paneVid && !paneVid.contains(media) && !media.paused) {
              media.pause();
            }
          });

          btnVid && btnVid.classList.add('active');
          btnVid && btnVid.setAttribute('aria-selected', 'true');
          btnImg && btnImg.classList.remove('active');
          btnImg && btnImg.setAttribute('aria-selected', 'false');

          paneVid && paneVid.classList.add('active');
          paneImg && paneImg.classList.remove('active');
        }

        this.setAttribute('active-tab', tab);
        this.dispatchEvent(new CustomEvent('b1b-media-tab-change', {
          detail: { tab },
          bubbles: true
        }));
      };

      btnImg && btnImg.addEventListener('click', () => switchTab('image'));
      btnVid && btnVid.addEventListener('click', () => switchTab('video'));
    }
  }

  /* ============================================================
     21. <b1b-chapter-list> & <b1b-playlist> : Bottom Series Chapter Card
     Displays the complete playlist drawer below chapter nav
     ============================================================ */
  class B1bChapterList extends HTMLElement {
    static get observedAttributes() {
      return ['title', 'course-url', 'course-label'];
    }

    connectedCallback() {
      setTimeout(() => {
        if (this.dataset.rendered) return;
        this.dataset.rendered = 'true';
        this.render();
      }, 0);
    }

    render() {
      const title = this.getAttribute('title') || '📋 সম্পূর্ণ কোর্স সূচি ও অধ্যায় তালিকা';
      const courseUrl = this.getAttribute('course-url') || '';
      const courseLabel = this.getAttribute('course-label') || 'সকল অধ্যায় দেখুন →';

      const items = Array.from(this.querySelectorAll('.playlist-item, [slot="item"]'));
      let itemsHtml = '';
      if (items.length > 0) {
        itemsHtml = items.map(el => el.outerHTML).join('');
      } else {
        itemsHtml = this.innerHTML.trim();
      }

      this.innerHTML = `
        <div class="chapter-list-card fade-up">
          <div class="chapter-list-inner">
            <div class="chapter-list-header">
              <div class="chapter-list-title">
                <span>${title}</span>
              </div>
              ${courseUrl ? `<a class="chapter-list-course-link" href="${courseUrl}">${courseLabel}</a>` : ''}
            </div>
            <div class="playlist-items-container">
              ${itemsHtml}
            </div>
          </div>
        </div>
      `;
    }
  }

  /* ============================================================
     22. Progressive SPA Lesson Shell Router (B1bRouter)
     Enables dynamic view switching without full page reload:
     - Retains shell (Navbar, KaTeX engine, Audio Player, Theme)
     - Fetches and injects new lesson content smoothly
     - Automatic KaTeX re-render on route update
     - Falls back gracefully to standard MPA links for SEO & direct hits
     ============================================================ */
  const B1bRouter = {
    init() {
      if (window.__b1bRouterInitialized) return;
      window.__b1bRouterInitialized = true;

      // Intercept local chapter navigation links
      document.addEventListener('click', (e) => {
        const link = e.target.closest('a[href]');
        if (!link) return;

        // Ignore modified clicks or external links
        if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || link.target === '_blank') return;

        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('javascript:')) return;

        // Check if link points to another lesson in web_platform
        if (href.endsWith('.html') || href.includes('.html#')) {
          try {
            const targetUrl = new URL(href, window.location.href);
            if (targetUrl.origin === window.location.origin) {
              e.preventDefault();
              this.navigate(targetUrl.href);
            }
          } catch (err) {
            // Proceed normally
          }
        }
      });

      // Handle browser back / forward
      window.addEventListener('popstate', (e) => {
        if (e.state && e.state.url) {
          this.loadLesson(e.state.url, false);
        } else {
          this.loadLesson(window.location.href, false);
        }
      });
    },

    async navigate(url) {
      const success = await this.loadLesson(url, true);
      if (!success) {
        window.location.href = url; // Fallback to standard navigation
      }
    },

    async loadLesson(url, pushHistory = true) {
      try {
        const res = await fetch(url);
        if (!res.ok) return false;
        const html = await res.text();
        const doc = new DOMParser().parseFromString(html, 'text/html');

        // Update document title
        if (doc.title) document.title = doc.title;

        // Update Hero player attributes if present
        const oldHero = document.querySelector('b1b-hero-player');
        const newHero = doc.querySelector('b1b-hero-player');
        if (oldHero && newHero) {
          Array.from(newHero.attributes).forEach(attr => {
            oldHero.setAttribute(attr.name, attr.value);
          });
        }

        // Update Navbar attributes if present
        const oldNav = document.querySelector('b1b-navbar');
        const newNav = doc.querySelector('b1b-navbar');
        if (oldNav && newNav) {
          Array.from(newNav.attributes).forEach(attr => {
            oldNav.setAttribute(attr.name, attr.value);
          });
        }

        // Update Read-mode article content
        const oldArticle = document.querySelector('.article, .lesson-body .read-mode');
        const newArticle = doc.querySelector('.article, .lesson-body .read-mode');
        if (oldArticle && newArticle) {
          oldArticle.innerHTML = newArticle.innerHTML;
        }

        // Update Chapter Nav cards
        const oldChapterNav = document.querySelector('b1b-chapter-nav');
        const newChapterNav = doc.querySelector('b1b-chapter-nav');
        if (oldChapterNav && newChapterNav) {
          Array.from(newChapterNav.attributes).forEach(attr => {
            oldChapterNav.setAttribute(attr.name, attr.value);
          });
        }

        // Re-run KaTeX auto-render on the swapped content
        if (typeof window.renderMathInElement === 'function') {
          window.renderMathInElement(document.body, {
            delimiters: [
              { left: '$$', right: '$$', display: true },
              { left: '$',  right: '$',  display: false },
              { left: '\\(', right: '\\)', display: false },
              { left: '\\[', right: '\\]', display: true }
            ],
            throwOnError: false
          });
        }

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Push state if requested
        if (pushHistory) {
          history.pushState({ url }, '', url);
        }

        return true;
      } catch (err) {
        console.warn('[B1bRouter] Soft navigation failed, falling back:', err);
        return false;
      }
    }
  };

  // Auto-init router when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => B1bRouter.init());
  } else {
    B1bRouter.init();
  }

  // Register the new components
  customElements.define('b1b-quote', B1bQuote);
  customElements.define('b1b-callout', B1bCallout);
  customElements.define('b1b-figure', B1bFigure);
  customElements.define('b1b-formula', B1bFormula);
  customElements.define('b1b-section', B1bSection);
  customElements.define('b1b-toc-sidebar', B1bTocSidebar);
  customElements.define('b1b-interactive-lab', B1bInteractiveLab);
  customElements.define('b1b-back-to-top', B1bBackToTop);
  customElements.define('b1b-series-card', B1bSeriesCard);
  customElements.define('b1b-media-tab', B1bMediaTab);
  customElements.define('b1b-chapter-list', B1bChapterList);
  class B1bPlaylist extends B1bChapterList {}
  customElements.define('b1b-playlist', B1bPlaylist);

  // Extend window.B1bComponents
  if (window.B1bComponents) {
    Object.assign(window.B1bComponents, {
      B1bMediaTab,
      B1bChapterList,
      B1bRouter
    });
  }

})();
