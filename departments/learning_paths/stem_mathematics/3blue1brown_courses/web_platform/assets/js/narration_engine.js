/**
 * ============================================================================
 * 3Blue1Brown Bengali Web Platform — Interactive Smart Narration Engine
 * "শিক্ষক ভয়েস ডাবিং ও লাইভ কারাওকে হাইলাইটার"
 *
 * Dual Engine Architecture:
 * 1. Studio Teacher Audio Engine (Primary):
 *    Plays real, studio-grade natural Bengali Teacher Audio MP3s (synthesized
 *    via Edge-TTS bn-BD-PradeepNeural with expressive pedagogical pauses & warmth)
 *    synchronized with cues for live sentence/block highlighting & auto-scrolling.
 *
 * 2. Phonetic Client Synthesis Engine (Fallback):
 *    Falls back smoothly to Web SpeechSynthesis API with clean phonetic Bengali
 *    rules whenever offline or if pre-rendered audio cannot be fetched.
 *
 * Features:
 * - Full Lesson & Per-Section Read Aloud
 * - Floating Audio Control Pill (Play/Pause, Step, Speed 1x/1.25x/1.5x, Section Nav)
 * - Real-Time Karaoke / Block Highlighting with Smooth Auto-Scroll
 * - Mutually Exclusive Playback with Hero/Theater Video (#mainVideo)
 * ============================================================================
 */

(function (global) {
  'use strict';

  // ── Phonetic Bengali Math Dictionary & Transliteration Rules (for Fallback) ──
  const PHONETIC_RULES = [
    // Acronyms
    { pattern: /\bAI\b/gi, replacement: 'এআই' },
    { pattern: /\b3D\b/gi, replacement: 'থ্রিডি' },
    { pattern: /\b2D\b/gi, replacement: 'টুডি' },
    { pattern: /\b1D\b/gi, replacement: 'ওয়ানডি' },
    { pattern: /\bEGM\b/gi, replacement: 'ইজিএম' },
    { pattern: /\bSEO\b/gi, replacement: 'এসইও' },
    { pattern: /\bAPI\b/gi, replacement: 'এপিআই' },
    { pattern: /\bUI\b/gi, replacement: 'ইউআই' },
    { pattern: /\bML\b/gi, replacement: 'এমএল' },
    { pattern: /\bFPS\b/gi, replacement: 'এফপিএস' },
    { pattern: /\bSVG\b/gi, replacement: 'এসভিজি' },
    { pattern: /\bHTML\b/gi, replacement: 'এইচটিএমএল' },
    { pattern: /\bJS\b/gi, replacement: 'জাভাস্ক্রিপ্ট' },
    { pattern: /\bGitHub\b/gi, replacement: 'গিটহাব' },
    { pattern: /\bGrant Sanderson\b/gi, replacement: 'গ্রান্ট স্যান্ডারসন' },

    // Math Axes & Coordinates
    { pattern: /x-অক্ষ/gi, replacement: 'এক্স অক্ষ' },
    { pattern: /y-অক্ষ/gi, replacement: 'ওয়াই অক্ষ' },
    { pattern: /z-অক্ষ/gi, replacement: 'জেড অক্ষ' },
    { pattern: /\bx অক্ষ\b/gi, replacement: 'এক্স অক্ষ' },
    { pattern: /\by অক্ষ\b/gi, replacement: 'ওয়াই অক্ষ' },
    { pattern: /\bz অক্ষ\b/gi, replacement: 'জেড অক্ষ' },
    { pattern: /x,\s*y/gi, replacement: 'এক্স ও ওয়াই' },
    { pattern: /\(x,\s*y\)/gi, replacement: 'স্থানাঙ্ক এক্স কমা ওয়াই' },

    // Basis Vectors & Vectors
    { pattern: /\\hat\{i\}|î|i-hat|i হ্যাট/gi, replacement: 'আই হ্যাট' },
    { pattern: /\\hat\{j\}|ĵ|j-hat|j হ্যাট/gi, replacement: 'জে হ্যাট' },
    { pattern: /\\hat\{k\}|k̂|k-hat|k হ্যাট/gi, replacement: 'কে হ্যাট' },
    { pattern: /\\vec\{v\}|\bv\b(?=\s+ভেক্টর|ভেক্টর\s+v)/gi, replacement: 'ভেক্টর ভি' },
    { pattern: /\\vec\{w\}|\bw\b(?=\s+ভেক্টর|ভেক্টর\s+w)/gi, replacement: 'ভেক্টর ডব্লিউ' },
    { pattern: /\\vec\{u\}|\bu\b(?=\s+ভেক্টর|ভেক্টর\s+u)/gi, replacement: 'ভেক্টর ইউ' },
    { pattern: /\\vec\{0\}/gi, replacement: 'শূন্য ভেক্টর' },

    // Spaces & Common Math Symbols
    { pattern: /\\mathbb\{R\}\^2|\bR\^2\b/gi, replacement: 'টুডি রিয়েল স্পেস' },
    { pattern: /\\mathbb\{R\}\^3|\bR\^3\b/gi, replacement: 'থ্রিডি রিয়েল স্পেস' },
    { pattern: /\\mathbb\{R\}\^n|\bR\^n\b/gi, replacement: 'এন মাত্রিক স্পেস' },
    { pattern: /\\approx/gi, replacement: 'প্রায় সমান' },
    { pattern: /\\neq/gi, replacement: 'সমান নয়' },
    { pattern: /\\in/gi, replacement: 'এর সদস্য' },
    { pattern: /\\theta/gi, replacement: 'থিটা' },
    { pattern: /\\lambda/gi, replacement: 'ল্যাম্বডা' },
    { pattern: /\\det/gi, replacement: 'ডিটারমিন্যান্ট বা নির্ণায়ক' },

    // Fractions & Square Roots
    { pattern: /\\frac\{([^}]+)\}\{([^}]+)\}/gi, replacement: '$2 ভাগের $1' },
    { pattern: /\\sqrt\{([^}]+)\}/gi, replacement: 'বর্গমূল $1' },

    // Matrices / Column Vectors in LaTeX
    { pattern: /\\begin\{bmatrix\}\s*([^\\\s&]+)\s*\\\\\s*([^\\\s&]+)\s*\\end\{bmatrix\}/gi, replacement: 'কলাম ভেক্টর: উপর সারিতে $1 এবং নিচের সারিতে $2' },
    { pattern: /\\begin\{bmatrix\}\s*([^&]+)&\s*([^\\\n]+)\\\\\s*([^&]+)&\s*([^\\\n]+)\s*\\end\{bmatrix\}/gi, replacement: 'টু বাই টু ম্যাট্রিক্স: প্রথম সারিতে $1 ও $2, দ্বিতীয় সারিতে $3 ও $4' },

    // Scalar notation
    { pattern: /\bk\b(?=\s*=|\s*স্কেলার)/gi, replacement: 'স্কেলার কে' },
    { pattern: /\bc_1\b/gi, replacement: 'সি ওয়ান' },
    { pattern: /\bc_2\b/gi, replacement: 'সি টু' },

    // Basic Operators cleanup
    { pattern: /\+/g, replacement: ' যোগ ' },
    { pattern: /−|-/g, replacement: ' বিয়োগ ' },
    { pattern: /=/g, replacement: ' সমান ' },
    { pattern: /×|\\times|\\cdot/g, replacement: ' গুণ ' }
  ];

  function cleanPhoneticText(rawText) {
    if (!rawText) return '';
    let text = rawText
      .replace(/https?:\/\/\S+/g, '')
      .replace(/```[\s\S]*?```/g, ' কোড ব্লক ')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/[{}[\]\\_]/g, ' ');

    for (const rule of PHONETIC_RULES) {
      text = text.replace(rule.pattern, rule.replacement);
    }
    return text.replace(/\s+/g, ' ').trim();
  }

  // ── Engine Implementation ──
  class SmartNarrationEngine {
    constructor() {
      // Audio Element for Teacher MP3s
      this.audioPlayer = new Audio();
      this.audioPlayer.preload = 'auto';

      // Fallback Web Speech
      this.synth = window.speechSynthesis || null;
      this.bengaliVoice = null;

      // Manifest & Content State
      this.manifest = null;
      this.hasStudioAudio = false;

      // Dynamically detect course ID and lesson ID from URL
      // e.g., /courses/linear_algebra/lesson_01.html -> course: linear_algebra, lesson: lesson_01
      const pathParts = window.location.pathname.replace(/\\/g, '/').split('/');
      let courseKey = 'linear_algebra';
      let lessonKey = 'lesson_01';
      
      const coursesIdx = pathParts.indexOf('courses');
      if (coursesIdx !== -1 && pathParts.length > coursesIdx + 2) {
        courseKey = pathParts[coursesIdx + 1];
        const filePart = pathParts[coursesIdx + 2];
        const match = filePart.match(/lesson_\d+/i);
        if (match) lessonKey = match[0].toLowerCase();
      } else {
        const fileName = pathParts[pathParts.length - 1] || 'lesson_01.html';
        const match = fileName.match(/lesson_\d+/i);
        if (match) lessonKey = match[0].toLowerCase();
      }

      // Calculate correct relative root path dynamically (courses/ is 2 levels deep, sandbox_components/ is 1 level)
      let rootRel = '../../';
      if (pathParts.includes('sandbox_components')) {
        rootRel = '../';
      } else if (coursesIdx === -1 && !window.location.pathname.includes('/courses/')) {
        rootRel = '../';
      }

      // Structured clean path: assets/audio/{course}/{lesson}/
      this.audioBasePath = `${rootRel}assets/audio/${courseKey}/${lessonKey}/`;
      this.fallbackAudioBasePath = `${rootRel}assets/audio/${lessonKey}/`;

      this.sections = [];
      this.currentSectionIdx = 0;
      this.currentItemIdx = 0;
      this.isPlaying = false;
      this.playbackRate = 1.0;
      this.activeElement = null;

      // Time tracker for studio audio synchronization
      this.timeUpdateHandler = null;

      // DOM UI Elements
      this.pillEl = null;
      this.playPauseBtn = null;
      this.sectionTitleEl = null;
      this.progressTextEl = null;

      this.audioPlayer.addEventListener('play', () => {
      this.pauseMainVideos();
      // Pause YouTube iframes
      document.querySelectorAll('iframe').forEach(ifr => {
        try {
          ifr.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
        } catch (e) {}
      });
    });

    this.init();
    }

    init() {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.setup());
      } else {
        this.setup();
      }
    }

    async setup() {
      this.initVoiceFallback();
      if (this.synth && this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = () => this.initVoiceFallback();
      }

      this.parseContent();
      this.createFloatingPill();
      this.bindTopCard();
      this.bindSectionButtons();
      this.attachVideoGuard();
      this.setupAudioListeners();

      // Attempt to load teacher audio manifest
      await this.loadManifest();

      // Restore user narration state if page was reloaded
      this.restoreState();
    }

    async loadManifest() {
      // 1. Check if pre-injected via script tag (Works 100% in file:// protocol without CORS blockage)
      if (window.TEACHER_AUDIO_MANIFEST && window.TEACHER_AUDIO_MANIFEST.sections) {
        this.manifest = window.TEACHER_AUDIO_MANIFEST;
        this.hasStudioAudio = true;
        this.bindManifestToSections();
        this.updatePillBadge(true);
        console.info('Studio teacher audio loaded via preloaded manifest script.');
        return;
      }

      // 2. Fetch fallback for http:// / localhost environments
      try {
        let manifestUrl = `${this.audioBasePath}manifest.json`;
        let res = await fetch(manifestUrl);
        if (!res.ok && this.fallbackAudioBasePath) {
          manifestUrl = `${this.fallbackAudioBasePath}manifest.json`;
          res = await fetch(manifestUrl);
          if (res.ok) {
            this.audioBasePath = this.fallbackAudioBasePath;
          }
        }
        if (res.ok) {
          this.manifest = await res.json();
          this.hasStudioAudio = true;
          this.bindManifestToSections();
          this.updatePillBadge(true);
          console.info('Studio teacher audio loaded successfully from:', this.audioBasePath);
        }
      } catch (err) {
        console.info('Studio teacher audio manifest fetch blocked (e.g. file:// CORS), falling back:', err);
        this.hasStudioAudio = false;
        this.updatePillBadge(false);
      }
    }

    bindManifestToSections() {
      if (!this.manifest || !this.manifest.sections) return;
      this.sections.forEach(sec => {
        const mSec = this.manifest.sections[sec.id];
        if (mSec) {
          sec.audioFile = `${this.audioBasePath}${mSec.audio_file}`;
          sec.cues = mSec.cues || [];
        }
      });
    }

    initVoiceFallback() {
      if (!this.synth) return;
      const voices = this.synth.getVoices();
      if (!voices || voices.length === 0) return;

      const bnVoice = voices.find(v =>
        v.lang === 'bn-BD' ||
        v.lang === 'bn-IN' ||
        v.lang.startsWith('bn') ||
        /bangla|bengali/i.test(v.name)
      );

      if (bnVoice) {
        this.bengaliVoice = bnVoice;
      } else {
        this.bengaliVoice = voices.find(v => v.lang.startsWith('hi') || v.default) || voices[0];
      }
    }

    /**
     * Parses the article DOM into structured sections and reading blocks
     */
    parseContent() {
      this.sections = [];
      const sectionElements = document.querySelectorAll('.article > section, article section');

      sectionElements.forEach((secEl, sIdx) => {
        // Interactive-only sections (e.g. the vector plane lab) are not part
        // of the narrated article and must not be counted as cue sections.
        if (secEl.getAttribute('data-no-narration') === 'true') return;
        const titleEl = secEl.querySelector('h2');
        const sectionTitle = titleEl ? titleEl.innerText.trim() : `সেকশন ${sIdx + 1}`;
        const secId = secEl.id || `sec-${sIdx}`;

        const blocks = [];
        const readableNodes = secEl.querySelectorAll(
          'h2, h3, p, .chapter-quote, .callout, figure.lesson-figure, .code-showcase, .formula-box'
        );

        readableNodes.forEach(node => {
          if (node.tagName === 'P' && (node.closest('.callout') || node.closest('.chapter-quote'))) {
            return;
          }

          let spokenText = '';
          if (node.classList.contains('chapter-quote')) {
            spokenText = 'উদ্ধৃতি: ' + node.innerText;
          } else if (node.classList.contains('callout')) {
            const title = node.querySelector('.callout-title');
            spokenText = 'বিশেষ নোট: ' + (title ? title.innerText + '। ' : '') + node.innerText;
          } else if (node.matches('figure.lesson-figure')) {
            const cap = node.querySelector('figcaption');
            const img = node.querySelector('img');
            // Natural teacher phrasing — never announce a label like "চিত্র প্রদর্শনী"।
            spokenText = 'চিত্রে দেখা যাচ্ছে, ' + (cap ? cap.innerText : (img ? img.alt : 'লিনিয়ার অ্যালজেব্রা গ্রাফিক্স'));
          } else if (node.classList.contains('code-showcase')) {
            const codeTitle = node.querySelector('.code-title');
            spokenText = 'কোড মডেলিং: ' + (codeTitle ? codeTitle.innerText : 'ভেক্টর প্রোগ্রামিং অ্যালগরিদম');
          } else if (node.classList.contains('formula-box')) {
            spokenText = 'গাণিতিক সূত্র: ' + node.innerText;
          } else {
            spokenText = node.innerText;
          }

          spokenText = cleanPhoneticText(spokenText);

          if (spokenText && spokenText.length > 2) {
            blocks.push({
              element: node,
              text: spokenText
            });
          }
        });

        if (blocks.length > 0) {
          this.sections.push({
            id: secId,
            title: sectionTitle,
            element: secEl,
            blocks: blocks,
            audioFile: null,
            cues: []
          });
        }
      });
    }

    /**
     * Binds top banner button "🎙️ সম্পূর্ণ পাঠ শুনুন"
     */
    bindTopCard() {
      const topBtn = document.getElementById('btnListenFullArticle') ||
                     document.querySelector('.btn-read-full');
      if (topBtn) {
        topBtn.addEventListener('click', () => {
          this.startFromBeginning();
        });
      }
    }

    /**
     * Injects or binds inline buttons for each section
     */
    bindSectionButtons() {
      this.sections.forEach((sec, idx) => {
        let btnBar = sec.element.querySelector('.section-narration-bar');
        let btn = sec.element.querySelector('.btn-section-narrate');

        if (!btn) {
          btnBar = document.createElement('div');
          btnBar.className = 'section-narration-bar';

          btn = document.createElement('button');
          btn.className = 'btn-section-narrate';
          btn.type = 'button';
          btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg> 🔊 এই সেকশনটি শুনুন`;
          
          btnBar.appendChild(btn);

          const h2 = sec.element.querySelector('h2');
          if (h2 && h2.nextSibling) {
            sec.element.insertBefore(btnBar, h2.nextSibling);
          } else {
            sec.element.prepend(btnBar);
          }
        }

        btn.addEventListener('click', () => {
          this.playSection(idx);
        });
      });
    }

    /**
     * Floating Audio Player Widget
     */
    createFloatingPill() {
      if (document.getElementById('smartAudioPill')) return;

      const pill = document.createElement('div');
      pill.id = 'smartAudioPill';
      pill.className = 'smart-audio-floating-pill';
      pill.innerHTML = `
        <div class="pill-status-col">
          <div class="pill-wave-anim">
            <span class="pill-wave-bar"></span>
            <span class="pill-wave-bar"></span>
            <span class="pill-wave-bar"></span>
          </div>
          <div class="pill-meta-info">
            <span class="pill-section-name" id="pillSectionTitle">শিক্ষক ভয়েস ডাবিং</span>
            <span class="pill-progress-text" id="pillProgressText">প্রস্তুত</span>
          </div>
        </div>

        <div class="pill-controls">
          <button class="pill-btn" id="pillPrevSecBtn" title="পূর্ববর্তী সেকশন">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
          </button>
          <button class="pill-btn" id="pillPrevItemBtn" title="পূর্ববর্তী অনুচ্ছেদ / বাক্য">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>
          </button>
          <button class="pill-btn pill-play-pause" id="pillPlayPauseBtn" title="প্লে / পজ">
            <svg id="pillPlayIcon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            <svg id="pillPauseIcon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="display:none;"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
          </button>
          <button class="pill-btn" id="pillNextItemBtn" title="পরবর্তী অনুচ্ছেদ / বাক্য">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/></svg>
          </button>
          <button class="pill-btn" id="pillNextSecBtn" title="পরবর্তী সেকশন">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
          </button>
        </div>

        <div class="pill-speed-group">
          <button class="pill-speed-btn is-active" data-speed="1.0">১×</button>
          <button class="pill-speed-btn" data-speed="1.25">১.২৫×</button>
          <button class="pill-speed-btn" data-speed="1.5">১.৫×</button>
        </div>

        <button class="pill-btn pill-close" id="pillCloseBtn" title="বন্ধ করুন">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      `;

      document.body.appendChild(pill);
      this.pillEl = pill;
      this.playPauseBtn = pill.querySelector('#pillPlayPauseBtn');
      this.sectionTitleEl = pill.querySelector('#pillSectionTitle');
      this.progressTextEl = pill.querySelector('#pillProgressText');

      // Bind Pill Events
      this.playPauseBtn.addEventListener('click', () => this.togglePlayPause());
      pill.querySelector('#pillPrevSecBtn').addEventListener('click', () => this.prevSection());
      pill.querySelector('#pillNextSecBtn').addEventListener('click', () => this.nextSection());
      pill.querySelector('#pillPrevItemBtn').addEventListener('click', () => this.prevItem());
      pill.querySelector('#pillNextItemBtn').addEventListener('click', () => this.nextItem());
      pill.querySelector('#pillCloseBtn').addEventListener('click', () => this.stopAndClose());

      // Speed Buttons
      pill.querySelectorAll('.pill-speed-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          pill.querySelectorAll('.pill-speed-btn').forEach(b => b.classList.remove('is-active'));
          btn.classList.add('is-active');
          this.playbackRate = parseFloat(btn.dataset.speed || '1.0');
          this.audioPlayer.playbackRate = this.playbackRate;
          if (this.isPlaying && !this.hasStudioAudio) {
            this.speakFallbackItem();
          }
        });
      });

      // ── Global keyboard navigation (robust) ────────────────────────────
      // Active only while the narration pill is visible. Uses `e.key` (with
      // `e.code` as fallback) so it works across keyboard layouts. When a
      // control inside the pill has focus, Space/Enter are left to that
      // button's native click handler — otherwise we would toggle twice.
      this._onKeyDown = (e) => {
        if (!(this.pillEl && this.pillEl.classList.contains('is-visible'))) return;

        const t = e.target;
        const tag = t && t.tagName ? t.tagName.toUpperCase() : '';
        const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(tag) ||
                       (t && t.isContentEditable);
        if (typing) return;

        const key = e.key || '';
        const code = e.code || '';
        const nativeControl = ['BUTTON', 'A'].includes(tag);
        const insidePill = !!(this.pillEl && t && this.pillEl.contains(t));
        const isSpace = key === ' ' || key === 'Spacebar' || code === 'Space';

        // Only let a focused control INSIDE the pill handle Space/Enter itself.
        // A button elsewhere on the page (e.g. the "listen" card) must not
        // swallow the shortcut — that was the double-toggle / no-toggle bug.
        if (nativeControl && insidePill && (isSpace || key === 'Enter')) return;

        if (isSpace) {
          e.preventDefault();
          this.togglePlayPause();
        } else if (key === 'ArrowRight' || code === 'ArrowRight') {
          e.preventDefault(); this.nextItem();
        } else if (key === 'ArrowLeft' || code === 'ArrowLeft') {
          e.preventDefault(); this.prevItem();
        } else if (key === 'ArrowDown' || code === 'ArrowDown') {
          e.preventDefault(); this.nextSection();
        } else if (key === 'ArrowUp' || code === 'ArrowUp') {
          e.preventDefault(); this.prevSection();
        } else if (key === 'Home') {
          e.preventDefault();
          this.currentSectionIdx = 0; this.currentItemIdx = 0; this.jumpToCurrentItem();
        } else if (key === 'End') {
          e.preventDefault();
          const last = this.sections.length - 1;
          if (last >= 0) {
            this.currentSectionIdx = last;
            this.currentItemIdx = Math.max(0, this.sections[last].blocks.length - 1);
            this.jumpToCurrentItem();
          }
        } else if (key === 'Escape' || code === 'Escape') {
          e.preventDefault(); this.stopAndClose();
        } else if (key === '+' || key === '=' || key === ']' ) {
          e.preventDefault(); this._cycleSpeed(1);
        } else if (key === '-' || key === '_' || key === '[') {
          e.preventDefault(); this._cycleSpeed(-1);
        }
      };
      window.addEventListener('keydown', this._onKeyDown);

      // Speed helper used by +/- keyboard shortcuts.
      this._cycleSpeed = (dir) => {
        const speeds = [1.0, 1.25, 1.5];
        let idx = speeds.indexOf(this.playbackRate);
        if (idx < 0) idx = 0;
        idx = Math.min(speeds.length - 1, Math.max(0, idx + dir));
        const rate = speeds[idx];
        this.playbackRate = rate;
        this.audioPlayer.playbackRate = rate;
        if (this.pillEl) {
          this.pillEl.querySelectorAll('.pill-speed-btn').forEach(b => {
            b.classList.toggle('is-active', parseFloat(b.dataset.speed) === rate);
          });
        }
        this.updatePillUI();
      };
    }

    updatePillBadge(isStudio) {
      if (!this.progressTextEl) return;
      if (isStudio) {
        this.progressTextEl.textContent = 'স্টুডিও শিক্ষক ভয়েস প্রস্তুত';
      }
    }

    setupAudioListeners() {
      // Synchronize cues with HTML Audio currentTime
      this.audioPlayer.addEventListener('timeupdate', () => {
        // Ignore time updates while a programmatic seek is settling —
        // otherwise a stale currentTime overwrites the item we just jumped to.
        if (this._suppressTimeUpdate) return;
        if (!this.isPlaying || !this.hasStudioAudio) return;
        const curMs = this.audioPlayer.currentTime * 1000.0;
        const sec = this.sections[this.currentSectionIdx];
        if (!sec || !sec.cues || sec.cues.length === 0) return;

        // Find active cue with tight bounding and boundary tolerance
        let activeCueIdx = -1;
        for (let i = 0; i < sec.cues.length; i++) {
          const cue = sec.cues[i];
          const nextCue = sec.cues[i + 1];
          // End time threshold extends cleanly up to next cue start to avoid flicker
          const effectiveEnd = nextCue ? nextCue.start_ms : (cue.end_ms + 250);
          if (curMs >= cue.start_ms && curMs < effectiveEnd) {
            activeCueIdx = i;
            break;
          }
        }

        if (activeCueIdx !== -1 && activeCueIdx !== this.currentItemIdx) {
          this.currentItemIdx = activeCueIdx;
          if (sec.blocks[this.currentItemIdx]) {
            this.setActiveElement(sec.blocks[this.currentItemIdx].element);
          }
          this.updatePillUI();
          this.saveState();
        }
      });

      this.audioPlayer.addEventListener('ended', () => {
        if (!this.isPlaying || this._suppressTimeUpdate) return;
        // Proceed to next section or finish
        if (this.currentSectionIdx + 1 < this.sections.length) {
          this.currentSectionIdx++;
          this.currentItemIdx = 0;
          this.playCurrentSectionAudio();
        } else {
          this.stopAndClose();
        }
      });

      this.audioPlayer.addEventListener('error', (e) => {
        console.warn('Audio file error, falling back to speech synthesis:', e);
        this.fallbackToSpeechSynth();
      });
    }

    attachVideoGuard() {
      const videos = document.querySelectorAll('video, #mainVideo');
      videos.forEach(v => {
        v.addEventListener('play', () => {
          if (this.isPlaying) {
            this.pause();
          }
        });
      });

      document.querySelectorAll('.mode-btn').forEach(b => {
        b.addEventListener('click', () => {
          if (b.dataset.mode === 'watch' && this.isPlaying) {
            this.pause();
          }
        });
      });
    }

    pauseMainVideos() {
      // Pause ALL page media (video AND audio) — narration must be the only sound
      document.querySelectorAll('video, audio').forEach(v => {
        if (!v.paused) v.pause();
      });
    }

    startFromBeginning() {
      this.currentSectionIdx = 0;
      this.currentItemIdx = 0;
      this.playCurrent();
    }

    playSection(sectionIdx) {
      if (sectionIdx < 0 || sectionIdx >= this.sections.length) return;
      this.currentSectionIdx = sectionIdx;
      this.currentItemIdx = 0;
      this.playCurrent();
    }

    playCurrent() {
      this.pauseMainVideos();
      this.showPill();
      this.isPlaying = true;

      const sec = this.sections[this.currentSectionIdx];
      if (this.hasStudioAudio && sec && sec.audioFile) {
        this.playCurrentSectionAudio();
      } else {
        this.fallbackToSpeechSynth();
      }
      this.updatePillUI();
    }

    playCurrentSectionAudio() {
      const sec = this.sections[this.currentSectionIdx];
      if (!sec || !sec.audioFile) {
        this.fallbackToSpeechSynth();
        return;
      }

      // Check if we need to load a new audio track
      const currentSrc = this.audioPlayer.getAttribute('src');
      if (currentSrc !== sec.audioFile) {
        this.audioPlayer.src = sec.audioFile;
        this.audioPlayer.playbackRate = this.playbackRate;
      }

      // Seek to current cue if starting midway
      if (sec.cues && sec.cues[this.currentItemIdx]) {
        this.audioPlayer.currentTime = (sec.cues[this.currentItemIdx].start_ms / 1000.0);
      } else {
        this.audioPlayer.currentTime = 0;
      }

      // Highlight first block
      if (sec.blocks[this.currentItemIdx]) {
        this.setActiveElement(sec.blocks[this.currentItemIdx].element);
      }

      this.audioPlayer.play().then(() => {
        if (this.pillEl) this.pillEl.classList.add('is-speaking');
        this.updatePillUI();
      }).catch(err => {
        console.warn('Autoplay failed or audio not loaded, trying fallback speech:', err);
        this.fallbackToSpeechSynth();
      });
    }

    fallbackToSpeechSynth() {
      if (!this.synth) return;
      this.speakFallbackItem();
    }

    speakFallbackItem() {
      if (!this.synth) return;
      this.synth.cancel();

      const sec = this.sections[this.currentSectionIdx];
      if (!sec) {
        this.stopAndClose();
        return;
      }

      const item = sec.blocks[this.currentItemIdx];
      if (!item) {
        if (this.currentSectionIdx + 1 < this.sections.length) {
          this.currentSectionIdx++;
          this.currentItemIdx = 0;
          this.speakFallbackItem();
        } else {
          this.stopAndClose();
        }
        return;
      }

      this.setActiveElement(item.element);
      this.updatePillUI();

      const utterance = new SpeechSynthesisUtterance(item.text);
      if (this.bengaliVoice) utterance.voice = this.bengaliVoice;
      utterance.rate = this.playbackRate;
      utterance.pitch = 1.0;

      utterance.onstart = () => {
        if (this.pillEl) this.pillEl.classList.add('is-speaking');
      };

      utterance.onend = () => {
        if (this.pillEl) this.pillEl.classList.remove('is-speaking');
        if (this.isPlaying) {
          this.currentItemIdx++;
          this.speakFallbackItem();
        }
      };

      utterance.onerror = (e) => {
        console.warn('SpeechSynthesis error:', e);
        if (this.pillEl) this.pillEl.classList.remove('is-speaking');
        if (this.isPlaying) {
          this.currentItemIdx++;
          this.speakFallbackItem();
        }
      };

      this.synth.speak(utterance);
    }

    setActiveElement(el) {
      if (this.activeElement) {
        this.activeElement.classList.remove('active-narration-highlight');
      }
      this.activeElement = el;
      if (el) {
        el.classList.add('active-narration-highlight');
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }

    togglePlayPause() {
      if (this.isPlaying) {
        this.pause();
      } else {
        this.isPlaying = true;
        const sec = this.sections[this.currentSectionIdx];
        if (this.hasStudioAudio && sec && sec.audioFile) {
          this.audioPlayer.play();
          if (this.pillEl) this.pillEl.classList.add('is-speaking');
        } else {
          this.speakFallbackItem();
        }
        this.updatePillUI();
      }
    }

    pause() {
      this.isPlaying = false;
      this.audioPlayer.pause();
      if (this.synth) this.synth.cancel();
      if (this.pillEl) this.pillEl.classList.remove('is-speaking');
      this.updatePillUI();
    }

    prevItem() {
      if (this.currentItemIdx > 0) {
        this.currentItemIdx--;
      } else if (this.currentSectionIdx > 0) {
        this.currentSectionIdx--;
        const prevSec = this.sections[this.currentSectionIdx];
        this.currentItemIdx = Math.max(0, (prevSec.blocks ? prevSec.blocks.length - 1 : 0));
      }
      this.jumpToCurrentItem();
    }

    nextItem() {
      const sec = this.sections[this.currentSectionIdx];
      if (sec && this.currentItemIdx + 1 < sec.blocks.length) {
        this.currentItemIdx++;
      } else if (this.currentSectionIdx + 1 < this.sections.length) {
        this.currentSectionIdx++;
        this.currentItemIdx = 0;
      }
      this.jumpToCurrentItem();
    }

    jumpToCurrentItem() {
      const sec = this.sections[this.currentSectionIdx];
      if (!sec) return;

      // Update active DOM highlight immediately
      if (sec.blocks && sec.blocks[this.currentItemIdx]) {
        this.setActiveElement(sec.blocks[this.currentItemIdx].element);
      }
      this.updatePillUI();

      if (this.hasStudioAudio && sec.audioFile) {
        // Switch audio track if needed
        const curSrc = this.audioPlayer.getAttribute('src');
        if (curSrc !== sec.audioFile) {
          this.audioPlayer.src = sec.audioFile;
          this.audioPlayer.playbackRate = this.playbackRate;
        }

        const cue = sec.cues && sec.cues[this.currentItemIdx];
        // Suppress stale timeupdate/ended events until the seek settles.
        this._suppressTimeUpdate = true;
        if (cue) {
          this.audioPlayer.currentTime = (cue.start_ms / 1000.0) + 0.05;
        }
        const release = () => { this._suppressTimeUpdate = false; };
        this.audioPlayer.addEventListener('seeked', release, { once: true });
        // Safety release in case 'seeked' never fires (e.g. same position).
        clearTimeout(this._seekReleaseTimer);
        this._seekReleaseTimer = setTimeout(release, 350);

        if (this.isPlaying) {
          this.audioPlayer.play().catch(e => console.warn('Audio play caught:', e));
        }
      } else {
        if (this.isPlaying) {
          this.speakFallbackItem();
        }
      }
    }

    prevSection() {
      if (this.currentSectionIdx > 0) {
        this.currentSectionIdx--;
        this.currentItemIdx = 0;
        // jumpToCurrentItem handles play/seek; calling playCurrentSectionAudio
        // as well re-seeks from 0 (that produced the wrong item after ↑/↓).
        this.jumpToCurrentItem();
      }
    }

    nextSection() {
      if (this.currentSectionIdx + 1 < this.sections.length) {
        this.currentSectionIdx++;
        this.currentItemIdx = 0;
        this.jumpToCurrentItem();
      }
    }

    stopAndClose() {
      this.pause();
      if (this.activeElement) {
        this.activeElement.classList.remove('active-narration-highlight');
        this.activeElement = null;
      }
      if (this.pillEl) {
        this.pillEl.classList.remove('is-visible');
      }
      document.querySelectorAll('.btn-section-narrate').forEach(b => b.classList.remove('is-active'));
      try {
        localStorage.removeItem('3b1b-narration-state-' + window.location.pathname);
      } catch (e) {}
    }

    showPill() {
      if (this.pillEl) {
        this.pillEl.classList.add('is-visible');
      }
      this.saveState();
    }

    saveState() {
      try {
        const state = {
          isVisible: this.pillEl && this.pillEl.classList.contains('is-visible'),
          sectionIdx: this.currentSectionIdx,
          itemIdx: this.currentItemIdx,
          currentTime: this.audioPlayer ? this.audioPlayer.currentTime : 0
        };
        localStorage.setItem('3b1b-narration-state-' + window.location.pathname, JSON.stringify(state));
      } catch (e) {}
    }

    restoreState() {
      try {
        const saved = localStorage.getItem('3b1b-narration-state-' + window.location.pathname);
        if (!saved) return;
        const state = JSON.parse(saved);
        if (state && state.isVisible) {
          this.currentSectionIdx = state.sectionIdx || 0;
          this.currentItemIdx = state.itemIdx || 0;
          this.showPill();
          const sec = this.sections[this.currentSectionIdx];
          if (sec && sec.blocks[this.currentItemIdx]) {
            this.setActiveElement(sec.blocks[this.currentItemIdx].element, false);
          }
          if (sec && sec.audioFile && this.hasStudioAudio) {
            this.audioPlayer.src = sec.audioFile;
            if (state.currentTime) {
              this.audioPlayer.currentTime = state.currentTime;
            }
          }
          this.updatePillUI();
        }
      } catch (e) {}
    }

    updatePillUI() {
      if (!this.pillEl) return;

      const playIcon = this.pillEl.querySelector('#pillPlayIcon');
      const pauseIcon = this.pillEl.querySelector('#pillPauseIcon');
      if (playIcon && pauseIcon) {
        playIcon.style.display = this.isPlaying ? 'none' : 'block';
        pauseIcon.style.display = this.isPlaying ? 'block' : 'none';
      }

      const sec = this.sections[this.currentSectionIdx];
      if (sec) {
        if (this.sectionTitleEl) {
          this.sectionTitleEl.textContent = sec.title;
        }
        if (this.progressTextEl) {
          const bnTotal = (sec.blocks.length).toLocaleString('bn-BD');
          const bnCur = (this.currentItemIdx + 1).toLocaleString('bn-BD');
          const engineTag = this.hasStudioAudio ? '🎙️ শিক্ষক অডিও' : '⚡ সিন্থেসিস';
          this.progressTextEl.textContent = `${engineTag} · অনুচ্ছেদ ${bnCur} / ${bnTotal}`;
        }

        document.querySelectorAll('.btn-section-narrate').forEach(b => b.classList.remove('is-active'));
        const activeBtn = sec.element.querySelector('.btn-section-narrate');
        if (activeBtn) activeBtn.classList.add('is-active');
      }
    }
  }

  // Auto-instantiate and export
  global.SmartNarrationEngine = SmartNarrationEngine;
  global.narrationEngine = new SmartNarrationEngine();

})(typeof window !== 'undefined' ? window : this);
