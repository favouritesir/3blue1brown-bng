/* ============================================================
   3Blue1Brown Bengali Platform — Lesson Page Core JS
   Handles: Theme, Mode Toggle, Audio, Search, Quizzes
   ============================================================ */

/* ---------- Theme Toggle ---------- */
(function initTheme() {
  const stored = localStorage.getItem('3b1b-theme') || 'dark';
  if (stored === 'dark') {
    document.documentElement.classList.add('dark');
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    document.documentElement.setAttribute('data-theme', 'light');
  }
})();

function toggleTheme() {
  const isDark = document.documentElement.classList.toggle('dark');
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  localStorage.setItem('3b1b-theme', isDark ? 'dark' : 'light');
  const btn = document.getElementById('themeBtn');
  if (btn) {
    btn.textContent = isDark ? '🌙' : '☀️';
    btn.title = isDark ? 'লাইট মোড' : 'ডার্ক মোড';
  }
}

/* ---------- Bengali Font Switcher (Hind Siliguri vs Noto Serif Bengali) ---------- */
function toggleFont() {
  const currentFont = document.documentElement.getAttribute('data-font') || 'sans';
  const newFont = currentFont === 'serif' ? 'sans' : 'serif';
  document.documentElement.setAttribute('data-font', newFont);
  localStorage.setItem('3b1b-font', newFont);

  const btn = document.getElementById('fontBtn');
  if (btn) {
    btn.textContent = newFont === 'serif' ? 'অ (সেরিফ)' : 'অ (সানস)';
    btn.title = newFont === 'serif' ? 'হিন্দ শিলিগুড়ি সানস ফন্টে পরিবর্তন' : 'নোটো সেরিফ বাংলা ফন্টে পরিবর্তন';
  }
}

function initFont() {
  const savedFont = localStorage.getItem('3b1b-font') || 'sans';
  document.documentElement.setAttribute('data-font', savedFont);
  const btn = document.getElementById('fontBtn');
  if (btn) {
    btn.textContent = savedFont === 'serif' ? 'অ (সেরিফ)' : 'অ (সানস)';
    btn.title = savedFont === 'serif' ? 'হিন্দ শিলিগুড়ি সানস ফন্টে পরিবর্তন' : 'নোটো সেরিফ বাংলা ফন্টে পরিবর্তন';
  }
}

/* ---------- Navbar Scroll Effect ---------- */
window.addEventListener('scroll', () => {
  const nav = document.querySelector('.site-nav');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 40);
}, { passive: true });

/* ---------- Single Active Media Guard ----------
   Rule: only ONE media element (video or audio) may play at a time.
   The main <video> player is primary; narration/dubbed audio is dedicated.
   No simultaneous audio + video auto-play. */
function pauseAllMediaExcept(exceptEl) {
  document.querySelectorAll('video, audio').forEach(m => {
    if (m !== exceptEl && !m.paused) { try { m.pause(); } catch (e) {} }
  });
  // Pause YouTube embeds (no dual audio with local media)
  document.querySelectorAll('iframe').forEach(ifr => {
    try {
      if (ifr.contentWindow) ifr.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
    } catch (e) {}
  });
  // Pause teacher narration engine (its own Audio element + speechSynthesis)
  if (window.narrationEngine && window.narrationEngine.isPlaying) {
    try { window.narrationEngine.pause(); } catch (e) {}
  }
}
function pauseAllMedia() { pauseAllMediaExcept(null); }
// Capture-phase: any media element that starts playing pauses everything else
document.addEventListener('play', (e) => {
  const el = e.target;
  if (el && (el.tagName === 'VIDEO' || el.tagName === 'AUDIO')) {
    pauseAllMediaExcept(el);
  }
}, true);

/* ---------- Read / Watch Mode Toggle ---------- */
function setMode(mode) {
  document.body.className = document.body.className
    .replace(/\bmode-\w+/g, '').trim();
  document.body.classList.add('mode-' + mode);

  document.querySelectorAll('.mode-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.mode === mode);
  });

  localStorage.setItem('3b1b-mode', mode);
  pauseAllMedia(); // switching modes must not leave media playing in the background

  if (mode === 'watch') {
    const wv = document.getElementById('watchLocalVideo');
    const wyt = document.getElementById('watchYtEmbed');
    if (wv) wv.style.display = 'block';
    if (wyt) wyt.style.display = 'none';
  }
}

/* ---------- Global Lesson Nav Binding Helper (Compatible with Web Components) ---------- */
function initLessonNavEvents() {
  initFont();
  const savedMode = localStorage.getItem('3b1b-mode') || 'read';
  setMode(savedMode);

  // Mode buttons
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.onclick = () => setMode(btn.dataset.mode);
  });

  // Search button
  const searchOpenBtn = document.getElementById('searchOpenBtn');
  const searchOverlay = document.getElementById('searchOverlay');
  const searchInput   = document.getElementById('searchInput');
  if (searchOpenBtn && searchOverlay && searchInput) {
    searchOpenBtn.onclick = () => {
      searchOverlay.classList.add('open');
      searchInput.focus();
    };
  }
}
window.initLessonNavEvents = initLessonNavEvents;

document.addEventListener('DOMContentLoaded', () => {
  initLessonNavEvents();

  // Strict Single-Audio/Video Authority Guard
  // Any playing video automatically pauses teacher narration & other videos
  document.querySelectorAll('video').forEach(vid => {
    vid.addEventListener('play', () => {
      // Pause all other HTML5 videos
      document.querySelectorAll('video').forEach(other => {
        if (other !== vid && !other.paused) other.pause();
      });
      // Pause teacher reading narration
      if (window.narrationEngine && window.narrationEngine.isPlaying) {
        window.narrationEngine.pause();
      }
      // Pause any active YouTube iframes
      document.querySelectorAll('iframe').forEach(ifr => {
        try {
          ifr.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
        } catch (e) {}
      });
    });
  });

  // Ensure default hero state is always local Bengali video
  switchHeroVideo('local');
  switchWatchVideo('local');

  // ═══════════════════════════════════════════════════════════════════════
  // Video Keyboard Controls (Capture Phase to eliminate double-toggle)
  // Space: Play/Pause video or focus video
  // ArrowLeft/ArrowRight: Seek ±5s, ArrowUp/ArrowDown: Volume, M: Mute, F: Fullscreen
  // ═══════════════════════════════════════════════════════════════════════
  window.addEventListener('keydown', (e) => {
    // 1. Ignore if typing in text inputs or textareas
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

    // 2. Identify the currently active/visible video
    const isWatchMode = document.body.classList.contains('mode-watch');
    let activeVid = null;
    if (isWatchMode) {
      activeVid = document.querySelector('#watchLocalVideo video') || document.querySelector('video');
    } else {
      activeVid = document.getElementById('mainVideo') || document.querySelector('#heroLocalBox video') || document.querySelector('video');
    }

    // 3. Spacebar Handling
    if (e.code === 'Space' || e.key === ' ' || e.keyCode === 32) {
      // If teacher narration floating pill is open and active, let narration_engine handle it
      const pill = document.getElementById('narrationPill') || (window.narrationEngine && window.narrationEngine.pillEl);
      if (pill && pill.classList.contains('is-visible')) {
        return;
      }

      // Stop native double-toggle and prevent page scroll
      e.preventDefault();
      e.stopPropagation();
      if (e.stopImmediatePropagation) e.stopImmediatePropagation();

      // If user had focused on a button or link, blur it so it doesn't re-click
      if (document.activeElement && ['BUTTON', 'A'].includes(document.activeElement.tagName)) {
        document.activeElement.blur();
      }

      // Handle HTML5 video
      if (activeVid) {
        // Ensure the video element is focused so other shortcuts (Arrow keys, etc.) work
        if (document.activeElement !== activeVid) {
          try { activeVid.focus(); } catch (err) {}
        }

        if (activeVid.paused) {
          const p = activeVid.play();
          if (p && p.catch) p.catch(() => {});
        } else {
          activeVid.pause();
        }
        return;
      }

      // If YouTube iframe is active, send pause/play command
      const heroYt = document.getElementById('heroYtBox');
      const isHeroYt = heroYt && !heroYt.classList.contains('hidden') && heroYt.style.display !== 'none';
      const ifr = isHeroYt ? heroYt.querySelector('iframe') : (isWatchMode ? document.getElementById('watchYtEmbed') : null);
      if (ifr && ifr.contentWindow) {
        ifr.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
      }
      return;
    }

    // 4. Mute toggle ('M')
    if (e.key.toLowerCase() === 'm' && activeVid) {
      e.preventDefault();
      activeVid.muted = !activeVid.muted;
      return;
    }

    // 5. Fullscreen toggle ('F')
    if (e.key.toLowerCase() === 'f' && activeVid) {
      e.preventDefault();
      if (document.fullscreenElement) document.exitFullscreen();
      else if (activeVid.requestFullscreen) activeVid.requestFullscreen();
      return;
    }

    // 6. Arrow keys on video if not already focused
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.code) && activeVid) {
      const pill = document.getElementById('narrationPill') || (window.narrationEngine && window.narrationEngine.pillEl);
      if (!pill || !pill.classList.contains('is-visible')) {
        if (document.activeElement !== activeVid) {
          try { activeVid.focus(); } catch (err) {}
        }
      }
    }
  }, true); // Capture phase = true to preempt browser/shadow DOM double-toggle
});

/* ---------- Hero Video Switcher ---------- */
function switchHeroVideo(mode) {
  const localBox = document.getElementById('heroLocalBox');
  const ytBox    = document.getElementById('heroYtBox');
  const btnLocal = document.getElementById('heroBtn-local');
  const btnYt    = document.getElementById('heroBtn-yt');
  if (!localBox || !ytBox) return;

  if (mode === 'local') {
    // Stop / pause YouTube iframe
    const ifr = ytBox.querySelector('iframe');
    if (ifr) {
      ifr.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
    }
    localBox.classList.remove('hidden');
    localBox.style.display = 'block';
    ytBox.classList.remove('active');
    ytBox.classList.add('hidden');
    ytBox.style.display = 'none';
    btnLocal && btnLocal.classList.add('active');
    btnYt && btnYt.classList.remove('active');
  } else {
    // Pause local video and reading narration
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
}

/* ---------- Watch Panel Video Switcher ---------- */
function switchWatchVideo(mode) {
  const lv  = document.getElementById('watchLocalVideo');
  const yt  = document.getElementById('watchYtEmbed');
  const bL  = document.getElementById('watchBtn-local');
  const bY  = document.getElementById('watchBtn-yt');

  if (mode === 'local') {
    const ifr = yt && yt.querySelector('iframe');
    if (ifr) {
      ifr.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
    }
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
}

/* ---------- Audio Player ---------- */
document.addEventListener('DOMContentLoaded', () => {
  const audio    = document.getElementById('bgAudio') || document.querySelector('audio');
  const playBtn  = document.getElementById('audioPlayBtn');
  const fillEl   = document.getElementById('audioFill');
  const timeEl   = document.getElementById('audioTime');
  const bar      = document.getElementById('audioBarOuter');
  if (!audio) return;

  const fmtTime = s => {
    const m = Math.floor(s / 60), sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
  };

  let playing = false;

  playBtn && playBtn.addEventListener('click', () => {
    if (audio.paused) { audio.play(); playing = true; }
    else { audio.pause(); playing = false; }
    updatePlayIcon();
  });

  function updatePlayIcon() {
    if (!playBtn) return;
    playBtn.innerHTML = playing
      ? `<svg viewBox="0 0 24 24" fill="white" width="18" height="18">
           <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
         </svg>`
      : `<svg viewBox="0 0 24 24" fill="white" width="18" height="18">
           <path d="M8 5v14l11-7z"/>
         </svg>`;
  }

  audio.addEventListener('timeupdate', () => {
    if (!audio.duration) return;
    const pct = (audio.currentTime / audio.duration) * 100;
    if (fillEl) fillEl.style.width = pct + '%';
    if (timeEl) timeEl.textContent = fmtTime(audio.currentTime) + ' / ' + fmtTime(audio.duration);

    // Update active bookmark pill
    const cur = audio.currentTime;
    const pills = document.querySelectorAll('.bookmark-pill[data-time]');
    let activePill = null;
    pills.forEach(p => {
      const t = parseFloat(p.dataset.time || '0');
      if (t <= cur) activePill = p;
    });
    if (activePill) {
      pills.forEach(p => p.classList.remove('active'));
      activePill.classList.add('active');
    }
  });

  audio.addEventListener('ended', () => { playing = false; updatePlayIcon(); });

  // Audio play/pause authority: when narration audio plays, it is the ONLY media;
  // when it pauses, keep the icon in sync (also covers pauses triggered elsewhere)
  audio.addEventListener('play', () => { playing = true; updatePlayIcon(); pauseAllMediaExcept(audio); });
  audio.addEventListener('pause', () => { playing = false; updatePlayIcon(); });

  bar && bar.addEventListener('click', e => {
    const rect = bar.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    const targetTime = ratio * (audio.duration || 0);
    audio.currentTime = targetTime;
    const video = document.getElementById('mainVideo');
    if (video) video.currentTime = targetTime;
  });

  // Speed buttons
  document.querySelectorAll('.speed-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const rate = parseFloat(btn.dataset.rate);
      audio.playbackRate = rate;
      const video = document.getElementById('mainVideo');
      if (video) video.playbackRate = rate;
      document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
    });
  });

  // Volume
  const volSlider = document.getElementById('volSlider');
  volSlider && volSlider.addEventListener('input', () => {
    audio.volume = parseFloat(volSlider.value);
  });

  // Audio Authority & Safety:
  // In watch mode or hero video playback, mainVideo has sole audio authority.
  // bgAudio is optional and only synced if bgAudio element exists and is active.
  if (mainVideo) {
    mainVideo.muted = false; // Video has full sound authority
  }

  // Dual-Track Synced Playback (Only if bgAudio is present)
  if (mainVideo && audio) {
    mainVideo.addEventListener('play', () => {
      // If narration engine is speaking, pause it
      if (window.narrationEngine && window.narrationEngine.isPlaying) {
        window.narrationEngine.pause();
      }
    });
    mainVideo.addEventListener('pause', () => {
      if (!audio.paused) {
        audio.pause();
        playing = false;
        updatePlayIcon();
      }
    });
    mainVideo.addEventListener('seeking', () => {
      if (Math.abs(audio.currentTime - mainVideo.currentTime) > 0.3) {
        audio.currentTime = mainVideo.currentTime;
      }
    });
  }

  updatePlayIcon();
});

/* ---------- KaTeX Auto-render ---------- */
document.addEventListener('DOMContentLoaded', () => {
  function tryRender() {
    if (typeof renderMathInElement === 'function') {
      renderMathInElement(document.body, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$',  right: '$',  display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true  }
        ],
        throwOnError: false
      });
      // Also ensure math inside quiz options and questions is rendered
      document.querySelectorAll('.quiz-block').forEach(b => {
        renderMathInElement(b, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$',  right: '$',  display: false }
          ],
          throwOnError: false
        });
      });
    } else {
      setTimeout(tryRender, 50);
    }
  }
  tryRender();
});

/* ---------- Quiz Widget ---------- */
document.querySelectorAll('.quiz-block').forEach(block => {
  // Wait for DOM ready
  document.addEventListener('DOMContentLoaded', () => init3b1bQuiz(block));
  init3b1bQuiz(block);
});

function init3b1bQuiz(block) {
  if (block.dataset.customBound === 'true') return;
  const options   = block.querySelectorAll('.quiz-option');
  const checkBtn  = block.querySelector('.quiz-check-btn');
  const revealBtn = block.querySelector('.quiz-reveal-btn');
  const feedback  = block.querySelector('.quiz-feedback');
  const correct   = parseInt(block.dataset.correct || '0', 10);
  let selected    = null;

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
      if (typeof renderMathInElement === 'function') {
        renderMathInElement(feedback, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$',  right: '$',  display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true }
          ],
          throwOnError: false
        });
      }
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
      if (typeof renderMathInElement === 'function') {
        renderMathInElement(feedback, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$',  right: '$',  display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true }
          ],
          throwOnError: false
        });
      }
    }
  });
}

/* ---------- Search Overlay ---------- */
const LESSON_INDEX = [
  { title: 'ভেক্টর আসলে কী?', path: 'courses/linear_algebra/lesson_01.html', course: 'লিনিয়ার অ্যালজেব্রা', icon: '→' },
  { title: 'রৈখিক সমন্বয়, স্প্যান ও ভিত্তি ভেক্টর', path: 'courses/linear_algebra/lesson_02.html', course: 'লিনিয়ার অ্যালজেব্রা', icon: '⊕' },
  { title: 'রৈখিক রূপান্তর ও ম্যাট্রিক্স', path: 'courses/linear_algebra/lesson_03.html', course: 'লিনিয়ার অ্যালজেব্রা', icon: '↕' },
  { title: 'ম্যাট্রিক্স গুণন — রূপান্তরের রচনা', path: 'courses/linear_algebra/lesson_04.html', course: 'লিনিয়ার অ্যালজেব্রা', icon: '×' },
  { title: 'ত্রিমাত্রিক রৈখিক রূপান্তর', path: 'courses/linear_algebra/lesson_05.html', course: 'লিনিয়ার অ্যালজেব্রা', icon: '⊗' },
  { title: 'ডিফারেনশিয়াল সমীকরণ কী? — পরিবর্তনের ভাষা', path: 'courses/differential_equations/lesson_01.html', course: 'ডিফারেনশিয়াল সমীকরণ', icon: '📈' },
  { title: 'সম্ভাব্যতা আসলে কী? — অনিশ্চয়তার জ্যামিতি', path: 'courses/probability/lesson_01.html', course: 'সম্ভাব্যতার মূলভাব', icon: '🎲' },
];

document.addEventListener('DOMContentLoaded', () => {
  const overlay  = document.getElementById('searchOverlay');
  const input    = document.getElementById('searchInput');
  const results  = document.getElementById('searchResults');
  const openBtn  = document.getElementById('searchOpenBtn');
  const closeBtn = document.getElementById('searchCloseBtn');

  function openSearch() { overlay && overlay.classList.add('open'); input && input.focus(); }
  function closeSearch() { overlay && overlay.classList.remove('open'); }

  openBtn  && openBtn.addEventListener('click', openSearch);
  closeBtn && closeBtn.addEventListener('click', closeSearch);
  overlay  && overlay.addEventListener('click', e => { if (e.target === overlay) closeSearch(); });
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); openSearch(); }
    if (e.key === 'Escape') closeSearch();
  });

  input && input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    if (!results) return;
    const hits = q
      ? LESSON_INDEX.filter(l => l.title.toLowerCase().includes(q) || l.path.includes(q) || (l.course && l.course.toLowerCase().includes(q)))
      : LESSON_INDEX;
    const isSub = window.location.pathname.includes('/courses/');
    results.innerHTML = hits.map(h => {
      const href = isSub ? `../../${h.path}` : h.path;
      return `
      <a class="search-result" href="${href}">
        <div class="sr-icon">${h.icon}</div>
        <div><div class="sr-title">${h.title}</div><div class="sr-path">${h.course || 'পাঠ্যক্রম'}</div></div>
      </a>`;
    }).join('');
  });

  // Initial populate
  if (results && input) input.dispatchEvent(new Event('input'));
});

/* ---------- Floating TOC Drawer Engine ---------- */
function initFloatingToc() {
  // If TOC drawer already exists, don't recreate
  if (document.getElementById('floatingTocBtn')) return;

  // Find all sections or h2 in article
  const headers = document.querySelectorAll('.article section, .article h2');
  if (!headers || headers.length === 0) return;

  const btn = document.createElement('button');
  btn.id = 'floatingTocBtn';
  btn.className = 'floating-toc-btn';
  btn.title = 'সূচিপত্র খুলুন';
  btn.setAttribute('aria-label', 'সূচিপত্র');
  btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <line x1="8" y1="6" x2="21" y2="6"></line>
    <line x1="8" y1="12" x2="21" y2="12"></line>
    <line x1="8" y1="18" x2="21" y2="18"></line>
    <line x1="3" y1="6" x2="3.01" y2="6"></line>
    <line x1="3" y1="12" x2="3.01" y2="12"></line>
    <line x1="3" y1="18" x2="3.01" y2="18"></line>
  </svg>`;

  const overlay = document.createElement('div');
  overlay.className = 'toc-drawer-overlay';
  overlay.id = 'tocDrawerOverlay';

  const drawer = document.createElement('div');
  drawer.className = 'toc-drawer';
  drawer.id = 'tocDrawer';

  let linksHtml = '';
  headers.forEach(h => {
    let id = h.id;
    let title = '';
    if (h.tagName === 'SECTION') {
      const h2 = h.querySelector('h2');
      if (h2) title = h2.textContent.trim();
      if (!id && h2 && h2.id) id = h2.id;
    } else if (h.tagName === 'H2') {
      title = h.textContent.trim();
    }
    if (id && title) {
      linksHtml += `<a href="#${id}" class="toc-drawer-link">
        <span>•</span>
        <span>${title}</span>
      </a>`;
    }
  });

  drawer.innerHTML = `
    <div class="toc-drawer-header">
      <div class="toc-drawer-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="8" y1="6" x2="21" y2="6"></line>
          <line x1="8" y1="12" x2="21" y2="12"></line>
          <line x1="8" y1="18" x2="21" y2="18"></line>
        </svg>
        <span>সূচিপত্র</span>
      </div>
      <button class="toc-drawer-close" id="tocDrawerClose">✕</button>
    </div>
    <div class="toc-drawer-body">
      ${linksHtml}
    </div>
  `;

  document.body.appendChild(btn);
  document.body.appendChild(overlay);
  document.body.appendChild(drawer);

  function openDrawer() {
    overlay.classList.add('open');
    drawer.classList.add('open');
  }
  function closeDrawer() {
    overlay.classList.remove('open');
    drawer.classList.remove('open');
  }

  btn.addEventListener('click', openDrawer);
  overlay.addEventListener('click', closeDrawer);
  drawer.querySelector('#tocDrawerClose').addEventListener('click', closeDrawer);

  drawer.querySelectorAll('.toc-drawer-link').forEach(link => {
    link.addEventListener('click', () => {
      closeDrawer();
    });
  });
}

document.addEventListener('DOMContentLoaded', initFloatingToc);

/* ---------- Fullscreen Visualizer Engine ---------- */
function toggleVizFullscreen(wrapperId) {
  const el = document.getElementById(wrapperId);
  if (!el) return;
  const isFs = el.classList.toggle('fullscreen');
  const btn = el.querySelector('#fsToggleBtn') || el.querySelector('#fsToggleBtnL01');
  if (btn) {
    btn.innerHTML = isFs ? '✕ বন্ধ করো' : '⛶ ফুলস্ক্রিন';
  }
  // Dispatch resize event so canvas redraws crisply at full resolution
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
  }, 100);
}

/* ---------- 3B1B Media Tab (Image / Video) Switcher ---------- */
function switchMediaTab(btn, tabType) {
  const container = btn.closest('.media-tab-container');
  if (!container) return;
  
  // Update buttons
  container.querySelectorAll('.media-tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  
  // Update panes
  container.querySelectorAll('.media-tab-pane').forEach(p => {
    p.classList.remove('active');
    const vid = p.querySelector('video');
    if (vid) vid.pause();
  });
  pauseAllMedia(); // switching tabs must not leave other media playing
  
  const activePane = container.querySelector(`.media-tab-pane[data-pane="${tabType}"]`);
  if (activePane) {
    activePane.classList.add('active');
    const vid = activePane.querySelector('video');
    if (vid) {
      vid.currentTime = 0;
      vid.play().catch(() => {});
    }
  }
}

/* ---------- Jump to Top Engine ---------- */
function initJumpToTop() {
  if (document.getElementById('jumpToTopBtn') || document.getElementById('b1bBackToTopBtn')) return;
  const btn = document.createElement('button');
  btn.id = 'jumpToTopBtn';
  btn.className = 'jump-to-top-btn';
  btn.title = 'পৃষ্ঠার শুরুতে ফিরে যান';
  btn.setAttribute('aria-label', 'পৃষ্ঠার শুরুতে ফিরে যান');
  btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="18 15 12 9 6 15"></polyline>
  </svg><span class="jump-tooltip">উপরে যান</span>`;

  document.body.appendChild(btn);

  const checkScroll = () => {
    if (window.scrollY > 300) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  };

  window.addEventListener('scroll', checkScroll, { passive: true });
  checkScroll();

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initJumpToTop);
} else {
  initJumpToTop();
}

/* =========================================================
   Interactive Video Timestamp Bookmarks Engine
   ========================================================= */
function jumpToLessonTime(seconds, triggerElement) {
  const parsedSeconds = Math.max(0, Number(seconds) || 0);

  // 1. Local HTML5 Video (#mainVideo or inside #heroLocalBox or #watchLocalVideo)
  const mainVideo = document.getElementById('mainVideo');
  const heroLocalVid = document.querySelector('#heroLocalBox video');
  const watchLocalVid = document.querySelector('#watchLocalVideo video');
  const localVid = mainVideo || heroLocalVid || watchLocalVid;

  // 2. Audio Narration/Master Track (#bgAudio)
  const audio = document.getElementById('bgAudio');

  // 3. YouTube Embeds (Hero iframe or Watch panel iframe)
  const heroYtIframe = document.getElementById('heroYtIframe') ||
                       document.getElementById('mainHeroFrame') ||
                       document.getElementById('mainYtFrame') ||
                       document.querySelector('#heroYtBox iframe') ||
                       document.querySelector('#heroLocalBox iframe');
  const watchYtEmbed = document.getElementById('watchYtEmbed') ||
                       document.querySelector('#watchYtEmbed iframe');

  // Check which mode is currently active
  const heroLocalBox = document.getElementById('heroLocalBox');
  const heroYtBox = document.getElementById('heroYtBox');
  const isYtActiveInHero = heroYtBox && !heroYtBox.classList.contains('hidden') && heroYtBox.classList.contains('active');
  const isWatchMode = document.body.classList.contains('mode-watch');

  // Seek & Play Local Video if available and visible
  let localVideoPlayed = false;
  if (localVid) {
    try {
      localVid.currentTime = parsedSeconds;
      const playPromise = localVid.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => {});
      }
      localVideoPlayed = true;
    } catch (e) {}
  }

  // Seek Audio if present and playing/active
  if (audio) {
    try {
      audio.currentTime = parsedSeconds;
    } catch (e) {}
  }

  // Handle YouTube iframe seek / start
  const seekYtIframe = (iframe) => {
    if (!iframe) return;
    try {
      // YouTube iFrame postMessage API
      iframe.contentWindow.postMessage(JSON.stringify({
        event: 'command',
        func: 'seekTo',
        args: [parsedSeconds, true]
      }), '*');
      iframe.contentWindow.postMessage(JSON.stringify({
        event: 'command',
        func: 'playVideo',
        args: []
      }), '*');
    } catch (e) {}

    // Fallback: If YouTube iframe is the primary/only player (no local video)
    // or if postMessage fails due to enablejsapi not having hooked yet, update src if not started
    if (!localVid && iframe.src) {
      try {
        const url = new URL(iframe.src);
        url.searchParams.set('start', Math.floor(parsedSeconds));
        url.searchParams.set('autoplay', '1');
        if (!url.searchParams.has('enablejsapi')) {
          url.searchParams.set('enablejsapi', '1');
        }
        // Only reload src if not already at roughly that timestamp
        iframe.src = url.toString();
      } catch (err) {}
    }
  };

  if (isWatchMode && watchYtEmbed && watchYtEmbed.style.display !== 'none') {
    seekYtIframe(watchYtEmbed);
  } else if (isYtActiveInHero && heroYtIframe) {
    seekYtIframe(heroYtIframe);
  } else if (!localVid) {
    // If there is no local video element on this page at all (e.g., pure YouTube lesson), seek the hero YouTube iframe
    seekYtIframe(heroYtIframe);
  }

  // Update active status across all bookmark chips/pills
  document.querySelectorAll('.bookmark-chip, .bookmark-pill').forEach(chip => {
    chip.classList.remove('active');
  });

  const activeTarget = triggerElement || (typeof event !== 'undefined' && event && event.currentTarget);
  if (activeTarget && activeTarget.classList) {
    activeTarget.classList.add('active');
  } else {
    // Attempt to match chip by onclick parameter
    document.querySelectorAll(`.bookmark-chip[onclick*="${parsedSeconds}"]`).forEach(c => c.classList.add('active'));
  }

  // Smooth scroll up to the video container
  const targetScrollEl = isWatchMode
    ? (document.querySelector('.watch-video-wrap') || document.querySelector('.hero-video-wrap'))
    : document.querySelector('.hero-video-wrap');

  if (targetScrollEl) {
    targetScrollEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// Make jumpToLessonTime available globally on window
window.jumpToLessonTime = jumpToLessonTime;

