/**
 * 3Blue1Brown Bengali Web Platform — Main JavaScript
 * Interactive UI: theme toggle, navbar scroll, search overlay,
 * course filtering, lesson list, progress tracking, toast system.
 */

'use strict';

/* ============================================================
   1. CONFIGURATION & STATE
   ============================================================ */
const APP = {
  version: '1.0.0',
  name: 'গণিত শেখার প্ল্যাটফর্ম',
  theme: 'dark',       // 'dark' | 'light'
  searchOpen: false,
  mobileNavOpen: false,
  progress: {},        // { courseId: { lessonId: boolean } }
  currentLesson: null,
};

/* ============================================================
   2. DOM READY BOOTSTRAP
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavbar();
  initSearch();
  initCourseCards();
  initInteractivePlayer();
  initTopicsCollection();
  initBackToTop();
  initProgressBars();
  initScrollAnimations();
  initMathRenderer();
  loadProgress();
  console.info(`%c${APP.name} v${APP.version} — প্ল্যাটফর্ম সক্রিয়`, 'color:#4f8ef7;font-weight:bold;font-size:14px;');
});

/* ============================================================
   3. THEME TOGGLE
   ============================================================ */
function initTheme() {
  const savedTheme = localStorage.getItem('3b1b-theme') || 'dark';
  applyTheme(savedTheme);

  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const newTheme = APP.theme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('3b1b-theme', newTheme);
      toast(newTheme === 'dark' ? '🌙 ডার্ক মোড সক্রিয়' : '☀️ লাইট মোড সক্রিয়', 'info');
    });
  }
}

function applyTheme(theme) {
  APP.theme = theme;
  document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : 'dark');
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    themeBtn.setAttribute('aria-label', theme === 'dark' ? 'লাইট মোডে যান' : 'ডার্ক মোডে যান');
    themeBtn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    themeBtn.title = theme === 'dark' ? 'লাইট মোড' : 'ডার্ক মোড';
  }
}

/* ============================================================
   4. NAVBAR — Scroll shadow & mobile hamburger
   ============================================================ */
function initNavbar() {
  const navbar = document.getElementById('navbar');
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobileNav');

  if (!navbar) return;

  // Scroll shadow
  const onScroll = () => {
    navbar.classList.toggle('scrolled', window.scrollY > 12);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Hamburger toggle
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', () => {
      APP.mobileNavOpen = !APP.mobileNavOpen;
      mobileNav.classList.toggle('open', APP.mobileNavOpen);
      hamburger.setAttribute('aria-expanded', String(APP.mobileNavOpen));

      // Animate hamburger lines
      const lines = hamburger.querySelectorAll('span');
      if (APP.mobileNavOpen) {
        lines[0].style.transform = 'translateY(7px) rotate(45deg)';
        lines[1].style.opacity  = '0';
        lines[2].style.transform = 'translateY(-7px) rotate(-45deg)';
      } else {
        lines[0].style.transform = '';
        lines[1].style.opacity  = '';
        lines[2].style.transform = '';
      }
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (APP.mobileNavOpen && !navbar.contains(e.target) && !mobileNav.contains(e.target)) {
        APP.mobileNavOpen = false;
        mobileNav.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Active nav link highlighting by section
  const navLinks = document.querySelectorAll('.navbar__link[data-section]');
  if (navLinks.length) {
    const sections = Array.from(navLinks).map(l => document.getElementById(l.dataset.section)).filter(Boolean);

    const sectionObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navLinks.forEach(l => l.classList.remove('active'));
          const activeLink = document.querySelector(`.navbar__link[data-section="${entry.target.id}"]`);
          if (activeLink) activeLink.classList.add('active');
        }
      });
    }, { rootMargin: '-40% 0px -55% 0px', threshold: 0 });

    sections.forEach(s => sectionObserver.observe(s));
  }
}

/* ============================================================
   5. SEARCH OVERLAY & EXPANDED 3B1B INDEX
   ============================================================ */
function initSearch() {
  const overlay     = document.getElementById('searchOverlay');
  const openBtn     = document.getElementById('searchBtn');
  const closeBtn    = document.getElementById('searchClose');
  const searchInput = document.getElementById('searchInput');
  const results     = document.getElementById('searchResults');

  if (!overlay) return;

  const searchData = buildSearchIndex();

  function openSearch() {
    APP.searchOpen = true;
    overlay.classList.add('open');
    if (searchInput) {
      searchInput.value = '';
      searchInput.focus();
    }
    renderResults(searchData.slice(0, 7), results);
  }

  function closeSearch() {
    APP.searchOpen = false;
    overlay.classList.remove('open');
    if (searchInput) searchInput.value = '';
  }

  openBtn?.addEventListener('click', openSearch);
  closeBtn?.addEventListener('click', closeSearch);

  // Keyboard shortcut: Ctrl+K or /
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      APP.searchOpen ? closeSearch() : openSearch();
    }
    if (e.key === 'Escape' && APP.searchOpen) closeSearch();
  });

  // Backdrop click to close
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeSearch();
  });

  // Live search
  searchInput?.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) {
      renderResults(searchData.slice(0, 7), results);
      return;
    }
    const matched = searchData.filter(item => {
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchTrail = item.trail.toLowerCase().includes(q);
      const matchTags  = item.tags ? item.tags.some(t => t.toLowerCase().includes(q)) : false;
      return matchTitle || matchTrail || matchTags;
    });
    renderResults(matched.slice(0, 12), results);
  });

  renderResults(searchData.slice(0, 7), results);
}

function buildSearchIndex() {
  return [
    // --- Linear Algebra Dubbed Lessons ---
    {
      icon: '📐',
      title: 'ভেক্টর কী? — মূল ধারণার পরিচয়',
      trail: 'লিনিয়ার অ্যালজেব্রা › পাঠ ০১',
      badge: 'বাংলা ডাবড',
      href: 'courses/linear_algebra/lesson_01.html',
      tags: ['vector', 'ভেক্টর', 'স্থানাঙ্ক', 'পদার্থবিজ্ঞান', 'লিনিয়ার অ্যালজেব্রা', 'la_01', 'lesson 1']
    },
    {
      icon: '📐',
      title: 'রৈখিক সমন্বয়, স্প্যান ও ভিত্তি ভেক্টর',
      trail: 'লিনিয়ার অ্যালজেব্রা › পাঠ ০২',
      badge: 'বাংলা ডাবড',
      href: 'courses/linear_algebra/lesson_02.html',
      tags: ['linear combination', 'span', 'basis', 'স্প্যান', 'ভিত্তি ভেক্টর', 'আই হ্যাট', 'জে হ্যাট', 'la_02']
    },
    {
      icon: '📐',
      title: 'রৈখিক রূপান্তর এবং ম্যাট্রিক্স',
      trail: 'লিনিয়ার অ্যালজেব্রা › পাঠ ০৩',
      badge: 'বাংলা ডাবড',
      href: 'courses/linear_algebra/lesson_03.html',
      tags: ['linear transformation', 'matrix', 'ম্যাট্রিক্স', 'রূপান্তর', 'গ্রিড', 'ডিটারমিন্যান্ট', 'la_03']
    },
    {
      icon: '📐',
      title: 'ম্যাট্রিক্স গুণন — রূপান্তরের রচনা',
      trail: 'লিনিয়ার অ্যালজেব্রা › পাঠ ০৪',
      badge: 'বাংলা ডাবড',
      href: 'courses/linear_algebra/lesson_04.html',
      tags: ['matrix multiplication', 'composition', 'ম্যাট্রিক্স গুণন', 'কম্পোজিশন', 'গুণ', 'la_04']
    },
    {
      icon: '📐',
      title: 'ত্রিমাত্রিক স্থানে রৈখিক রূপান্তর',
      trail: 'লিনিয়ার অ্যালজেব্রা › পাঠ ০৫',
      badge: 'বাংলা ডাবড',
      href: 'courses/linear_algebra/lesson_05.html',
      tags: ['3d transformations', 'ত্রিমাত্রিক', '3D', 'ঘূর্ণন', 'rotation', 'la_05']
    },
    {
      icon: '📐',
      title: 'ডিটারমিন্যান্ট — আয়তন ও ক্ষেত্রফল স্কেলিং',
      trail: 'লিনিয়ার অ্যালজেব্রা › অধ্যায় ০৬',
      badge: 'কোর্স অধ্যায়',
      href: 'courses/linear_algebra/index.html',
      tags: ['determinant', 'ডিটারমিন্যান্ট', 'area', 'volume', 'নির্ণায়ক']
    },
    {
      icon: '📐',
      title: 'আইগেনভ্যালু ও আইগেনভেক্টর',
      trail: 'লিনিয়ার অ্যালজেব্রা › অধ্যায় ১৪',
      badge: 'কোর্স অধ্যায়',
      href: 'courses/linear_algebra/index.html',
      tags: ['eigenvalues', 'eigenvectors', 'আইগেনভ্যালু', 'আইগেনভেক্টর', 'Av=λv']
    },
    {
      icon: '📐',
      title: 'বিপরীত ম্যাট্রিক্স, কলাম স্পেস ও নাল স্পেস',
      trail: 'লিনিয়ার অ্যালজেব্রা › অধ্যায় ০৭',
      badge: 'কোর্স অধ্যায়',
      href: 'courses/linear_algebra/index.html',
      tags: ['inverse', 'column space', 'null space', 'বিপরীত ম্যাট্রিক্স', 'রৈখিক সমীকরণ']
    },
    {
      icon: '📐',
      title: 'ডট প্রোডাক্ট ও ক্রস প্রোডাক্টের জ্যামিতি',
      trail: 'লিনিয়ার অ্যালজেব্রা › অধ্যায় ০৯-১০',
      badge: 'কোর্স অধ্যায়',
      href: 'courses/linear_algebra/index.html',
      tags: ['dot product', 'cross product', 'ডট গুণন', 'ক্রস গুণন']
    },

    // --- Calculus Series ---
    {
      icon: '∫',
      title: 'ক্যালকুলাসের মূল সারমর্ম ও প্যারাডক্স',
      trail: 'ক্যালকুলাস › অধ্যায় ০১',
      badge: 'কোর্স অধ্যায়',
      topicId: 'calculus',
      tags: ['calculus', 'ক্যালকুলাস', 'ডেরিভেটিভ', 'ঢাল', 'লিমিট', 'essence of calculus']
    },
    {
      icon: '∫',
      title: 'ডেরিভেটিভের জ্যামিতিক সংজ্ঞায়ন ও সূত্র',
      trail: 'ক্যালকুলাস › অধ্যায় ০২',
      badge: 'ক্যালকুলাস',
      topicId: 'calculus',
      tags: ['derivative', 'পাওয়ার রুল', 'অবকলন', 'slope']
    },
    {
      icon: '∫',
      title: 'চেইন রুল ও প্রোডাক্ট রুলের দৃশ্যমান প্রমাণ',
      trail: 'ক্যালকুলাস › অধ্যায় ০৪',
      badge: 'ক্যালকুলাস',
      topicId: 'calculus',
      tags: ['chain rule', 'product rule', 'চেইন রুল', 'যৌগিক অবকলন']
    },
    {
      icon: '∫',
      title: 'ইন্টিগ্রেশন ও ক্যালকুলাসের মৌলিক উপপাদ্য',
      trail: 'ক্যালকুলাস › অধ্যায় ০৮',
      badge: 'ক্যালকুলাস',
      topicId: 'calculus',
      tags: ['integration', 'ইন্টিগ্রাল', 'সমাকলন', 'fundamental theorem of calculus']
    },
    {
      icon: '∫',
      title: 'টেলর সিরিজ ও পলিনোমিয়াল আসন্নায়ন',
      trail: 'ক্যালকুলাস › অধ্যায় ১১',
      badge: 'ক্যালকুলাস',
      topicId: 'calculus',
      tags: ['taylor series', 'টেলর সিরিজ', 'approximation', 'বহুপদী']
    },

    // --- Neural Networks ---
    {
      icon: '🧠',
      title: 'নিউরাল নেটওয়ার্ক আসলে কী? — ডিপ লার্নিং ভূমিকা',
      trail: 'নিউরাল নেটওয়ার্ক › অধ্যায় ০১',
      badge: 'এআই ও গণিত',
      topicId: 'neural-networks',
      tags: ['neural network', 'deep learning', 'নিউরাল নেটওয়ার্ক', 'কৃত্রিম বুদ্ধিমত্তা', 'ai']
    },
    {
      icon: '🧠',
      title: 'গ্রেডিয়েন্ট ডিসেন্ট কীভাবে শেখে?',
      trail: 'নিউরাল নেটওয়ার্ক › অধ্যায় ০২',
      badge: 'এআই ও গণিত',
      topicId: 'neural-networks',
      tags: ['gradient descent', 'গ্রেডিয়েন্ট ডিসেন্ট', 'loss function', 'অপ্টিমাইজেশন']
    },
    {
      icon: '🧠',
      title: 'ব্যাকপ্রোপাগেশন আসলে কী করে?',
      trail: 'নিউরাল নেটওয়ার্ক › অধ্যায় ০৩',
      badge: 'এআই ও গণিত',
      topicId: 'neural-networks',
      tags: ['backpropagation', 'ব্যাকপ্রোপাগেশন', 'ক্যালকুলাস', 'weights', 'biases']
    },
    {
      icon: '🧠',
      title: 'ট্রান্সফরমার ও অ্যাটেনশন মেকানিজম (LLM)',
      trail: 'নিউরাল নেটওয়ার্ক › অধ্যায় ০৫',
      badge: 'এআই ও গণিত',
      topicId: 'neural-networks',
      tags: ['transformer', 'attention', 'ট্রান্সফরমার', 'এলএলএম', 'gpt']
    },

    // --- Differential Equations & Physics ---
    {
      icon: '📈',
      title: 'ডিফারেনশিয়াল সমীকরণ কী ও কেন?',
      trail: 'ডিফারেনশিয়াল সমীকরণ › অধ্যায় ০১',
      badge: 'কোর্স অধ্যায়',
      topicId: 'differential-equations',
      tags: ['differential equations', 'ডিফারেনশিয়াল সমীকরণ', 'ode', 'pde']
    },
    {
      icon: '📈',
      title: 'তাপ সমীকরণ ও ফুরিয়ার রূপান্তর (Fourier Transform)',
      trail: 'ডিফারেনশিয়াল সমীকরণ › অধ্যায় ০৩',
      badge: 'কোর্স অধ্যায়',
      topicId: 'differential-equations',
      tags: ['heat equation', 'fourier transform', 'ফুরিয়ার ট্রান্সফর্ম', 'তাপ সমীকরণ']
    },
    {
      icon: '⚛️',
      title: 'ব্র্যাকিটক্রোন বক্ররেখা ও আলোর প্রতিসরণ',
      trail: 'পদার্থবিজ্ঞান › অপটিক্স',
      badge: 'পদার্থবিজ্ঞান',
      topicId: 'physics',
      tags: ['brachistochrone', 'snell law', 'পদার্থবিজ্ঞান', 'স্নেল', 'আলো']
    },

    // --- Probability & Statistics ---
    {
      icon: '🎲',
      title: 'সম্ভাব্যতা প্রথম নীতি থেকে — অনিশ্চয়তার জ্যামিতি',
      trail: 'সম্ভাব্যতার মূলভাব › অধ্যায় ০১',
      badge: 'নতুন সিরিজ',
      topicId: 'probability',
      tags: ['probability', 'সম্ভাব্যতা', 'পরিসংখ্যান', 'chance']
    },
    {
      icon: '🎲',
      title: 'বেইজের উপপাদ্য (Bayes Theorem) দৃশ্যমান ব্যাখ্যা',
      trail: 'সম্ভাব্যতার মূলভাব › অধ্যায় ০২',
      badge: 'সম্ভাব্যতা',
      topicId: 'probability',
      tags: ['bayes', 'বেইজ', 'conditional probability', 'বেইজিয়ান']
    },

    // --- Puzzles, Pi & Number Theory ---
    {
      icon: 'π',
      title: 'ব্লকের সংঘর্ষে পাই (π) গণনা — বাউন্স প্যারাডক্স',
      trail: 'কেন পাই? › সেরা ভিডিও',
      badge: 'সেরা ভিডিও',
      topicId: 'why-pi',
      tags: ['pi', 'পাই', 'কেন পাই', 'collision', 'বাউন্স']
    },
    {
      icon: 'π',
      title: 'ব্যাসেল সমস্যা ও পাই^২ / ৬ এর আলো ভিত্তিক প্রমাণ',
      trail: 'কেন পাই? › বাশেল সমস্যা',
      badge: 'সেরা ভিডিও',
      topicId: 'why-pi',
      tags: ['basel problem', 'ব্যাসেল', 'pi squared', 'অসীম ধারা']
    },
    {
      icon: '🔢',
      title: 'রিমান হাইপোথিসিস ও জিটা ফাংশন অ্যানালাইসিস',
      trail: 'সংখ্যা তত্ত্ব › রিমান জিটা',
      badge: 'সংখ্যা তত্ত্ব',
      topicId: 'number-theory',
      tags: ['riemann hypothesis', 'zeta function', 'রিমান', 'জিটা ফাংশন', 'মৌলিক সংখ্যা']
    },
    {
      icon: '💻',
      title: 'পাবলিক-কি ক্রিপ্টোগ্রাফি (RSA) ও প্রাইম নাম্বার',
      trail: 'কম্পিউটার সায়েন্স › ক্রিপ্টো',
      badge: 'সিএস',
      topicId: 'computer-science',
      tags: ['cryptography', 'rsa', 'ক্রিপ্টোগ্রাফি', 'প্রাইম', 'নিরাপত্তা']
    },

    // --- Geometry, Topology, Fractals & Group Theory ---
    {
      icon: '🍩',
      title: 'টপোলজি ও অয়লার ক্যারেক্টারিস্টিক (V - E + F = 2)',
      trail: 'টপোলজি › রাবার-শিট জ্যামিতি',
      badge: 'টপোলজি',
      topicId: 'topology',
      tags: ['topology', 'টপোলজি', 'euler characteristic', 'মোবিউস স্ট্রিপ']
    },
    {
      icon: '❄️',
      title: 'ম্যান্ডেলব্রোট সেট ও ফ্র্যাক্টাল ডাইমেনশন',
      trail: 'ফ্র্যাক্টাল › জটিল গতিবিদ্যা',
      badge: 'ফ্র্যাক্টাল',
      topicId: 'fractals',
      tags: ['fractals', 'mandelbrot', 'ফ্র্যাক্টাল', 'ম্যান্ডেলব্রোট']
    },
    {
      icon: '💎',
      title: 'গ্রুপ তত্ত্ব, প্রতিসাম্য ও মনস্টার গ্রুপ',
      trail: 'গ্রুপ তত্ত্ব › বিমূর্ত বীজগণিত',
      badge: 'গ্রুপ তত্ত্ব',
      topicId: 'group-theory',
      tags: ['group theory', 'গ্রুপ তত্ত্ব', 'symmetry', 'প্রতিসাম্য', 'monster group']
    },
    {
      icon: '🏠',
      title: 'কোয়াটারনিয়ন ও ৪ডি ঘূর্ণন — লকডাউন ম্যাথ',
      trail: 'লকডাউন ম্যাথ › লাইভ ক্লাস',
      badge: 'লকডাউন',
      topicId: 'lockdown-math',
      tags: ['quaternion', 'কোয়াটারনিয়ন', 'lockdown math', '4d', 'ঘূর্ণন']
    },
    {
      icon: '🎙️',
      title: 'গণিত উপস্থাপনা ও মানিম (Manim) অ্যানিমেশন ইঞ্জিনের দর্শন',
      trail: 'বক্তৃতা ও আলোচনা',
      badge: 'বক্তৃতা',
      topicId: 'talks',
      tags: ['talks', 'manim', 'বক্তৃতা', 'গ্রান্ট স্যান্ডারসন', 'টিচিং']
    }
  ];
}

function renderResults(data, container) {
  if (!container) return;
  if (!data.length) {
    container.innerHTML = `<div style="padding:1.5rem;text-align:center;color:var(--text-muted);font-size:0.875rem;">কোনো ফলাফল পাওয়া যায়নি। অন্য শব্দ দিয়ে খুঁজুন।</div>`;
    return;
  }
  container.innerHTML = data.map((item, idx) => `
    <div class="search-result-item" data-search-idx="${idx}" role="option" tabindex="0">
      <div class="search-result-item__icon">${item.icon}</div>
      <div class="search-result-item__info">
        <div class="search-result-item__title">${item.title}</div>
        <div class="search-result-item__trail">${item.trail}</div>
      </div>
      ${item.badge ? `<span class="search-result-item__badge">${item.badge}</span>` : ''}
    </div>
  `).join('');

  // Wire click to navigate or open modal
  container.querySelectorAll('.search-result-item').forEach((row, i) => {
    const item = data[i];
    row.addEventListener('click', () => {
      const overlay = document.getElementById('searchOverlay');
      if (overlay) overlay.classList.remove('open');
      APP.searchOpen = false;

      if (item.href) {
        window.location.href = item.href;
      } else if (item.topicId) {
        openTopicModal(item.topicId);
      }
    });
    row.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        row.click();
      }
    });
  });
}

/* ============================================================
   6. COURSE TRACK CARDS — hover & click navigation
   ============================================================ */
function initCourseCards() {
  const cards = document.querySelectorAll('.track-card[data-href]');
  cards.forEach(card => {
    card.addEventListener('click', () => {
      const href = card.dataset.href;
      if (href) window.location.href = href;
    });
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        card.click();
      }
    });
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'button');
  });
}

/* ============================================================
   7. INTERACTIVE LESSON PREVIEW PLAYER & CONTROLS
   ============================================================ */
const LESSON_MEDIA = [
  {
    id: 'la_01',
    num: '০১',
    title: 'ভেক্টর কী? — মূল ধারণার পরিচয়',
    desc: 'লিনিয়ার অ্যালজেব্রা সিরিজের প্রথম পাঠে ভেক্টরের তিনটি দৃষ্টিভঙ্গি জানুন — পদার্থবিজ্ঞানী, গণিতবিদ ও কম্পিউটার বিজ্ঞানীর চোখে। স্থানাঙ্ক ও জ্যামিতির নিখুঁত সমন্বয়।',
    dur: '৯:৫২ মিনিট',
    durationSec: 592,
    videoSrc: 'media_vault/lesson_01/3b1b_lesson_01_bangla_dubbed_video.mp4',
    youtubeId: 'fNk_zzaMoSs',
    pageUrl: 'courses/linear_algebra/lesson_01.html'
  },
  {
    id: 'la_02',
    num: '০২',
    title: 'রৈখিক সমন্বয়, স্প্যান ও ভিত্তি ভেক্টর',
    desc: 'দুটি ভেক্টর মিলে কীভাবে সম্পূর্ণ সমতল বা ত্রিমাত্রিক শূন্যস্থান তৈরি করতে পারে? ভিত্তি ভেক্টর (î, ĵ) এবং রৈখিক স্বাধীনতার সহজ ভিজ্যুয়ালাইজেশন।',
    dur: '৯:৫৯ মিনিট',
    durationSec: 599,
    videoSrc: 'media_vault/lesson_02/3b1b_lesson_02_bangla_dubbed_video.mp4',
    youtubeId: 'k7RM-ot2NWY',
    pageUrl: 'courses/linear_algebra/lesson_02.html'
  },
  {
    id: 'la_03',
    num: '০৩',
    title: 'রৈখিক রূপান্তর এবং ম্যাট্রিক্স',
    desc: 'ম্যাট্রিক্স কেবল সংখ্যার বাক্স নয় — এটি সমতলের স্থানিক সংকোচন, প্রসারণ ও ঘূর্ণনের এক জাদুকরী নির্দেশিকা। গ্রিড রূপান্তর কীভাবে কাজ করে লক্ষ্য করুন।',
    dur: '১০:৫৯ মিনিট',
    durationSec: 659,
    videoSrc: 'media_vault/lesson_03/3b1b_lesson_03_bangla_dubbed_video.mp4',
    youtubeId: 'kYB8IZa5AuE',
    pageUrl: 'courses/linear_algebra/lesson_03.html'
  },
  {
    id: 'la_04',
    num: '০৪',
    title: 'ম্যাট্রিক্স গুণন — রূপান্তরের রচনা',
    desc: 'কেন ম্যাট্রিক্স গুণন এমন অস্বাভাবিকভাবে সারি ও কলাম বরাবর হয়? রূপান্তরের পর রূপান্তর (কম্পোজিশন) প্রয়োগ করার জ্যামিতিক সত্য জানুন।',
    dur: '১০:০৩ মিনিট',
    durationSec: 603,
    videoSrc: 'media_vault/lesson_04/3b1b_lesson_04_bangla_dubbed_video.mp4',
    youtubeId: 'XkY2DOUCWMU',
    pageUrl: 'courses/linear_algebra/lesson_04.html'
  },
  {
    id: 'la_05',
    num: '০৫',
    title: 'ত্রিমাত্রিক স্থানে রৈখিক রূপান্তর',
    desc: 'ত্রিমাত্রিক স্থানে তিনটি ভিত্তি ভেক্টর (î, ĵ, k̂) কীভাবে ৩×৩ ম্যাট্রিক্স হিসেবে সম্পূর্ণ স্পেসকে স্থানান্তরিত ও ঘূর্ণন করায় — পূর্ণ বাংলা ডাবিং।',
    dur: '৪:৪৬ মিনিট',
    durationSec: 286,
    videoSrc: 'media_vault/lesson_05/3b1b_lesson_05_bangla_dubbed_video.mp4',
    youtubeId: 'rHLEWRxRGiM',
    pageUrl: 'courses/linear_algebra/lesson_05.html'
  }
];

let activeLessonIndex = 0;
let currentSourceMode = 'local'; // 'local' | 'youtube'

function formatBengaliTime(seconds) {
  if (isNaN(seconds) || seconds < 0) seconds = 0;
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  const bnDigits = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'];
  const toBn = n => String(n).split('').map(d => bnDigits[d] !== undefined ? bnDigits[d] : d).join('');
  const padSec = s < 10 ? '০' + toBn(s) : toBn(s);
  return `${toBn(m)}:${padSec}`;
}

function initInteractivePlayer() {
  const video          = document.getElementById('previewVideo');
  const iframe         = document.getElementById('previewIframe');
  const mainPlayBtn    = document.getElementById('mainPlayBtn');
  const mainPlayBtn2   = document.getElementById('mainPlayBtn2');
  const progressBar    = document.getElementById('playerProgressBar');
  const progressFill   = document.getElementById('playerProgressFill');
  const timeDisplay    = document.getElementById('playerTime');
  const prevBtn        = document.getElementById('playerPrevBtn');
  const nextBtn        = document.getElementById('playerNextBtn');
  const srcToggleBtn   = document.getElementById('playerSourceToggle');
  const ccBtn          = document.getElementById('playerCcBtn');
  const fullscreenBtn  = document.getElementById('playerFullscreenBtn');
  const container      = document.getElementById('playerMediaContainer');
  const lessonItems    = document.querySelectorAll('#playerLessonList .lesson-item');

  if (!video || !lessonItems.length) return;

  function loadLesson(index, autoplay = false) {
    if (index < 0) index = 0;
    if (index >= LESSON_MEDIA.length) index = LESSON_MEDIA.length - 1;
    activeLessonIndex = index;
    const item = LESSON_MEDIA[index];
    APP.currentLesson = item.id;

    // Update Text Header & Desc
    const titleEl = document.getElementById('playerCurrentTitle');
    const descEl  = document.getElementById('playerCurrentDesc');
    const linkEl  = document.getElementById('playerLessonPageLink');
    if (titleEl) titleEl.textContent = item.title;
    if (descEl)  descEl.textContent  = item.desc;
    if (linkEl)  linkEl.href         = item.pageUrl;

    // Update List Active State
    lessonItems.forEach((li, i) => {
      const isActive = i === index;
      li.classList.toggle('active', isActive);
      li.setAttribute('aria-current', isActive ? 'true' : 'false');
      const st = li.querySelector('.lesson-item__status');
      if (st) st.textContent = isActive ? '▶' : '▷';
    });

    // Update Video Source
    if (currentSourceMode === 'local') {
      video.style.display = 'block';
      if (iframe) iframe.style.display = 'none';
      video.src = item.videoSrc;
      video.load();
      if (autoplay) {
        video.play().then(() => updatePlayButtonState(true)).catch(() => updatePlayButtonState(false));
      } else {
        updatePlayButtonState(false);
      }
    } else {
      video.pause();
      video.style.display = 'none';
      if (iframe) {
        iframe.style.display = 'block';
        iframe.src = `https://www.youtube.com/embed/${item.youtubeId}?autoplay=${autoplay ? 1 : 0}&rel=0`;
      }
      updatePlayButtonState(autoplay);
    }

    if (progressFill) progressFill.style.width = '0%';
    if (timeDisplay) timeDisplay.textContent = `০:০০ / ${formatBengaliTime(item.durationSec)}`;
  }

  function updatePlayButtonState(isPlaying) {
    if (mainPlayBtn) {
      mainPlayBtn.innerHTML = isPlaying ? '⏸' : '▶';
      mainPlayBtn.setAttribute('aria-label', isPlaying ? 'বিরতি দিন' : 'চালু করুন');
      mainPlayBtn.style.opacity = isPlaying ? '0' : '1';
    }
    if (mainPlayBtn2) {
      mainPlayBtn2.innerHTML = isPlaying ? '⏸ বিরতি' : '▶ চালু';
    }
  }

  // Hover effect to show center play button when playing
  if (container) {
    container.addEventListener('mouseenter', () => {
      if (mainPlayBtn && !video.paused) mainPlayBtn.style.opacity = '0.9';
    });
    container.addEventListener('mouseleave', () => {
      if (mainPlayBtn && !video.paused) mainPlayBtn.style.opacity = '0';
    });
  }

  function togglePlay() {
    if (currentSourceMode === 'youtube') {
      // Toggle back to local for full HTML5 playback
      currentSourceMode = 'local';
      if (srcToggleBtn) srcToggleBtn.textContent = '1080p লোকাল';
      loadLesson(activeLessonIndex, true);
      toast('🎬 লোকাল বাংলা ডাবড প্লেয়ারে স্যুইচ করা হয়েছে', 'info', 2000);
      return;
    }

    if (video.paused || video.ended) {
      video.play().then(() => {
        updatePlayButtonState(true);
      }).catch(err => {
        console.warn('Playback error:', err);
        updatePlayButtonState(false);
      });
    } else {
      video.pause();
      updatePlayButtonState(false);
    }
  }

  mainPlayBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    togglePlay();
  });
  mainPlayBtn2?.addEventListener('click', (e) => {
    e.stopPropagation();
    togglePlay();
  });

  // Time & Progress update
  video.addEventListener('timeupdate', () => {
    if (!video.duration || isNaN(video.duration)) return;
    const pct = (video.currentTime / video.duration) * 100;
    if (progressFill) progressFill.style.width = `${pct}%`;
    if (timeDisplay) {
      timeDisplay.textContent = `${formatBengaliTime(video.currentTime)} / ${formatBengaliTime(video.duration)}`;
    }
  });

  video.addEventListener('play',  () => updatePlayButtonState(true));
  video.addEventListener('pause', () => updatePlayButtonState(false));
  video.addEventListener('ended', () => {
    updatePlayButtonState(false);
    markLessonComplete('linear_algebra', LESSON_MEDIA[activeLessonIndex].id);
    if (activeLessonIndex < LESSON_MEDIA.length - 1) {
      toast('🎉 পাঠ শেষ হয়েছে! পরবর্তী পাঠ চালু হচ্ছে...', 'success', 2500);
      setTimeout(() => loadLesson(activeLessonIndex + 1, true), 1200);
    } else {
      toast('🎉 লিনিয়ার অ্যালজেব্রার প্রথম ৫টি পাঠ সম্পন্ন হয়েছে!', 'success', 4000);
    }
  });

  // Progress Bar Seek
  if (progressBar) {
    progressBar.addEventListener('click', (e) => {
      const rect = progressBar.getBoundingClientRect();
      const pos  = (e.clientX - rect.left) / rect.width;
      const targetPct = Math.max(0, Math.min(1, pos));
      if (video.duration) {
        video.currentTime = targetPct * video.duration;
      }
      if (progressFill) progressFill.style.width = `${targetPct * 100}%`;
    });
  }

  // Prev / Next Buttons
  prevBtn?.addEventListener('click', () => {
    if (activeLessonIndex > 0) {
      loadLesson(activeLessonIndex - 1, !video.paused);
    } else {
      toast('এটি সিরিজের প্রথম পাঠ', 'info', 1500);
    }
  });
  nextBtn?.addEventListener('click', () => {
    if (activeLessonIndex < LESSON_MEDIA.length - 1) {
      loadLesson(activeLessonIndex + 1, !video.paused);
    } else {
      toast('এটি প্রথম ৫টি পাঠের শেষ পাঠ', 'info', 1500);
    }
  });

  // Local / YouTube Source Switcher
  srcToggleBtn?.addEventListener('click', () => {
    if (currentSourceMode === 'local') {
      currentSourceMode = 'youtube';
      srcToggleBtn.textContent = 'YouTube মোড';
      loadLesson(activeLessonIndex, true);
      toast('▶️ YouTube এম্বেডে স্যুইচ করা হয়েছে', 'info', 2000);
    } else {
      currentSourceMode = 'local';
      srcToggleBtn.textContent = '1080p লোকাল';
      loadLesson(activeLessonIndex, true);
      toast('🔊 1080p লোকাল বাংলা মাস্টার ট্র্যাকে স্যুইচ করা হয়েছে', 'success', 2000);
    }
  });

  // CC / Audio Info Button
  ccBtn?.addEventListener('click', () => {
    toast('🔊 স্টুডিও মাস্টার বাংলা কণ্ঠ (bn-BD-PradeepNeural) সক্রিয়', 'info', 2500);
  });

  // Fullscreen
  fullscreenBtn?.addEventListener('click', () => {
    if (!document.fullscreenElement) {
      container?.requestFullscreen?.().catch(() => {});
    } else {
      document.exitFullscreen?.().catch(() => {});
    }
  });

  // Wire Lesson List Clicks
  lessonItems.forEach((item, index) => {
    item.addEventListener('click', (e) => {
      // If user clicked directly on the "পাঠ পৃষ্ঠা" anchor, don't hijack
      if (e.target.closest('.lesson-item__link-badge')) return;
      loadLesson(index, true);
      toast(`📖 পাঠ ${LESSON_MEDIA[index].num} লোড হচ্ছে...`, 'info', 1500);
    });
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        loadLesson(index, true);
      }
    });
  });

  // Initialize with first lesson
  loadLesson(0, false);
}

/* ============================================================
   8. TOPICS COLLECTIONS & PARITY MODAL SYSTEM
   ============================================================ */
const TOPIC_DETAILS = {
  'all': {
    title: 'সকল বিষয় ও কোর্স (All Topics & Lessons)',
    icon: '🌐',
    desc: '৩ব্লু১ব্রাউনের সমস্ত গণিত, পদার্থবিজ্ঞান, কম্পিউটার সায়েন্স ও দর্শন ভিত্তিক ভিডিও সংকলন। আমাদের প্ল্যাটফর্ম এগুলোর উচ্চমানের বাংলা রূপান্তর তৈরি করছে।',
    chapters: [
      'লিনিয়ার অ্যালজেব্রা (১৫ পাঠ • পাঠ ১-৫ সম্পূর্ণ বাংলা ডাবিং)',
      'ক্যালকুলাস (১২ পাঠ)',
      'নিউরাল নেটওয়ার্ক (৮ পাঠ)',
      'ডিফারেনশিয়াল সমীকরণ ও লকডাউন ম্যাথ',
      'সম্ভাব্যতা ও পরিসংখ্যান (নতুন ২০২৫-২৬)',
      'টপোলজি, ফ্র্যাক্টাল, সংখ্যাতত্ত্ব ও গণিত অলিম্পিয়াড পাজল'
    ],
    officialUrl: 'https://www.3blue1brown.com/#lessons',
    actionText: 'সকল পাঠ সূচি দেখুন ↗'
  },
  'best-of': {
    title: 'সেরা ভিডিও (Best of 3Blue1Brown)',
    icon: '⭐',
    desc: '৩Blue1Brown-এর সবচেয়ে জনপ্রিয়, উদ্দীপক ও বিখ্যাত ভিডিওগুলোর সংকলন। গণিতকে কেবল সূত্র নয় — এক শিল্প হিসেবে আবিষ্কার করার শ্রেষ্ঠ সূচনা।',
    chapters: [
      'ব্লকের সংঘর্ষে পাই (π) আবিষ্কার — অবিশ্বাস্য বাউন্স মেকানিক্স',
      'ব্যাসেল সমস্যার আলোভিত্তিক প্রমাণ (∑ 1/n² = π²/6)',
      'রিমান হাইপোথিসিসের দৃশ্যমান ভ্রমণ ও নন-ট্রিভিয়াল শূন্যস্থান',
      'কীভাবে বিটকয়েন গাণিতিকভাবে সুরক্ষিত কাজ করে'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=best-of',
    actionText: 'অফিসিয়াল কালেকশন দেখুন ↗'
  },
  'neural-networks': {
    title: 'নিউরাল নেটওয়ার্ক (Neural Networks)',
    icon: '🧠',
    desc: 'ডিপ লার্নিং ও কৃত্রিম বুদ্ধিমত্তা কীভাবে কাজ করে — সংখ্যা সনাক্তকরণ থেকে শুরু করে আধুনিক এলএলএম (LLM) ও ট্রান্সফরমারের ভেতরের পূর্ণাঙ্গ গাণিতিক অন্তর্দৃষ্টি।',
    chapters: [
      'অধ্যায় ১: কিন্তু নিউরাল নেটওয়ার্ক আসলে কী?',
      'অধ্যায় ২: গ্রেডিয়েন্ট ডিসেন্ট কীভাবে কৃত্রিম বুদ্ধিমত্তাকে শেখায়',
      'অধ্যায় ৩: ব্যাকপ্রোপাগেশন ক্যালকুলাসের দৃশ্যমান প্রয়োগ',
      'অধ্যায় ৪: ব্যাকপ্রোপাগেশনের গাণিতিক সমীকরণ ও ভেক্টরাইজেশন',
      'অধ্যায় ৫: ট্রান্সফরমার কীভাবে শব্দ অনুধাবন করে (Attention is All You Need)'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=neural-networks',
    actionText: 'কোর্স রোডম্যাপে যান ↗'
  },
  'linear-algebra': {
    title: 'লিনিয়ার অ্যালজেব্রার মূলভাব (Essence of Linear Algebra)',
    icon: '📐',
    desc: '১৫টি অধ্যায়ে সাজানো বিশ্বখ্যাত লিনিয়ার অ্যালজেব্রা কোর্স। ১ম থেকে ৫ম পাঠ বাংলায় পূর্ণাঙ্গ ডাবিং ও ইন্টারঅ্যাক্টিভ সিমুলেশন সহ প্ল্যাটফর্মে সরাসরি উপলব্ধ।',
    chapters: [
      'পাঠ ০১: ভেক্টর আসলে কী? (বাংলা ডাবড)',
      'পাঠ ০২: রৈখিক সমন্বয়, স্প্যান ও ভিত্তি ভেক্টর (বাংলা ডাবড)',
      'পাঠ ০৩: রৈখিক রূপান্তর ও ম্যাট্রিক্স (বাংলা ডাবড)',
      'পাঠ ০৪: ম্যাট্রিক্স গুণন — রূপান্তরের রচনা (বাংলা ডাবড)',
      'পাঠ ০৫: ত্রিমাত্রিক স্থানে রৈখিক রূপান্তর (বাংলা ডাবড)',
      'অধ্যায় ০৬-১৫: ডিটারমিন্যান্ট, ইনভার্স, আইগেনভ্যালু ও ডট প্রোডাক্ট'
    ],
    internalUrl: 'courses/linear_algebra/index.html',
    actionText: 'লিনিয়ার অ্যালজেব্রা সূচিপত্র খুলুন →'
  },
  'calculus': {
    title: 'ক্যালকুলাসের মূলভাব (Essence of Calculus)',
    icon: '∫',
    desc: '১২টি অধ্যায়ের দৃশ্যমান মাস্টারপিস। সূত্র মুখস্থ না করে জ্যামিতিক ক্ষেত্রফল ও পরিবর্তনের হারের মাধ্যমে অবকলন ও সমাকলনের মূল গল্প অনুভব করুন।',
    chapters: [
      'অধ্যায় ১: ক্যালকুলাসের সারমর্ম ও জ্যামিতিক অন্তর্দৃষ্টি',
      'অধ্যায় ২: পরিবর্তনের ক্ষণস্থায়ী হার ও ডেরিভেটিভের জ্যামিতি',
      'অধ্যায় ৩: প্রোডাক্ট রুল ও চেইন রুল কেন সত্য?',
      'অধ্যায় ৪: সূচকীয় ফাংশন ও অয়লার সংখ্যা e-এর ডেরিভেটিভ',
      'অধ্যায় ৫: ইন্টিগ্রেশন ও ক্যালকুলাসের মৌলিক উপপাদ্য',
      'অধ্যায় ৬: টেলর সিরিজ পলিনোমিয়াল'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=calculus',
    actionText: 'অফিসিয়াল ক্যালকুলাস কালেকশন ↗'
  },
  'differential-equations': {
    title: 'ডিফারেনশিয়াল সমীকরণ (Differential Equations)',
    icon: '📈',
    desc: 'মহাবিশ্বের পরিবর্তনের ভাষা। তাপ প্রবাহের সমীকরণ, পেন্ডুলামের গতিশীল ভারসাম্য ও বাস্তব বিশ্বের জটিল ব্যবস্থার গাণিতিক মডেলিং।',
    chapters: [
      'ডিফারেনশিয়াল সমীকরণ কী ও কেন?',
      'ফুরিয়ার সিরিজ ও তাপ সমীকরণ (Fourier Series & Heat Eq)',
      'লিনিয়ার সিস্টেম ও ফেজ স্পেস ট্রাজেক্টরি',
      'পেন্ডুলামের নন-লিনিয়ার গতি ও এনার্জি গ্রাফ'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=differential-equations',
    actionText: 'সমীকরণ কালেকশন দেখুন ↗'
  },
  'analysis': {
    title: 'গাণিতিক অ্যানালাইসিস (Mathematical Analysis)',
    icon: '🔍',
    desc: 'অসীম ধারা, সীমা ও জটিল রূপান্তরের গভীর প্রমাণ। যেখানে সাধারণ বীজগাণিতিক অনুভূতি শেষ হয়, সেখান থেকেই অ্যানালাইসিসের যাত্রা শুরু।',
    chapters: [
      'অসীম ধারার যোগফল ও প্যারাডক্স',
      'কমপ্লেক্স অ্যানালাইসিস ও কোশি-রিম্যান সমীকরণ',
      'হিলবার্ট স্পেস ও অসীম মাত্রার ভিত্তি',
      'কনফর্মাল ম্যাপিং ও জটিল রূপান্তর'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=analysis',
    actionText: 'অ্যানালাইসিস কালেকশন ↗'
  },
  'physics': {
    title: 'পদার্থবিজ্ঞান সিমুলেশন (Physics Simulations)',
    icon: '⚛️',
    desc: 'পদার্থবিজ্ঞানের নিয়মগুলোকে খাঁটি গাণিতিক সৌন্দর্য ও অ্যানিমেশনের মাধ্যমে উন্মোচিত করা। কোয়ান্টাম ওয়েভফাংশন থেকে আপেক্ষিকতা।',
    chapters: [
      'ব্র্যাকিটক্রোন বক্ররেখা — দ্রুততম অবতরণের পথ',
      'স্নেলের প্রতিসরণ সূত্র ও ফার্মার নীতি',
      'কোয়ান্টাম মেকানিক্সের দৃশ্যমান ওয়েভফাংশন',
      'সাধারণ আপেক্ষিকতা ও স্থান-কালের বক্রতা'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=physics',
    actionText: 'পদার্থবিজ্ঞান দেখুন ↗'
  },
  'computer-science': {
    title: 'কম্পিউটার সায়েন্স (Computer Science & Algorithms)',
    icon: '💻',
    desc: 'কম্পিউটিংয়ের তাত্ত্বিক ভিত্তি — ক্রিপ্টোগ্রাফি, কোডিং থিওরি, তথ্য তত্ত্ব ও জটিল অ্যালগরিদমের অভ্যন্তরীণ কাঠামো।',
    chapters: [
      'হ্যামিং কোড ও ত্রুটি সংশোধন তত্ত্ব (Error Correction)',
      'আরএসএ (RSA) এনক্রিপশন ও মডুলার পাওয়ারিং',
      'অ্যালগরিদমের টাইম কমপ্লেক্সিটি ও বিগ-ও নোটিশন',
      'শ্যানন এনট্রপি ও তথ্য তত্ত্বের মূল নীতি'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=computer-science',
    actionText: 'কম্পিউটার সায়েন্স দেখুন ↗'
  },
  'why-pi': {
    title: 'কেন পাই? (Why Pi? — Mysteries of π)',
    icon: 'π',
    desc: 'বৃত্তের পরিধি আর ব্যাসের অনুপাত পাই (π) কীভাবে সংখ্যা তত্ত্ব, সংঘর্ষ এবং কোয়ান্টাম সমীকরণে বারবার আবির্ভূত হয়? তার রোমাঞ্চকর ব্যাখ্যা।',
    chapters: [
      'ব্লকের স্থিতিস্থাপক সংঘর্ষে পাই গণনার রহস্য',
      'ব্যাসেল সমস্যার আলোভিত্তিক জ্যামিতিক প্রমাণ',
      'বুফনের সূঁচ পরীক্ষা ও সম্ভাব্যতা থেকে পাই',
      'ওয়ালিস গুণফল ও গাউসিয়ান ইন্টিগ্রাল'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=why-pi',
    actionText: 'পাই সিরিজ দেখুন ↗'
  },
  'puzzles': {
    title: 'ধাঁধা ও সমস্যা সমাধান (Math Puzzles)',
    icon: '🧩',
    desc: 'আন্তর্জাতিক গণিত অলিম্পিয়াড, পুতনাম প্রতিযোগিতা এবং গভীর গাণিতিক বুদ্ধির চ্যালেঞ্জিং সমস্যাগুলোর উদ্ভাবনী ভিজ্যুয়াল সমাধান।',
    chapters: [
      'লকার প্যারাডক্স ও পারফেক্ট স্কয়ার',
      'হার্ডেস্ট ম্যাথ অলিম্পিয়াড কোয়েশ্চেন (IMO Windmill)',
      'স্নেক পাজল ও সম্ভাবনা ভিত্তিক ভারসাম্য',
      'মন্টি হল প্যারাডক্সের দৃশ্যমান রূপ'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=puzzles',
    actionText: 'ম্যাথ পাজল দেখুন ↗'
  },
  'geometry': {
    title: 'জ্যামিতি (Geometry & Visual Proofs)',
    icon: '📐',
    desc: 'ইউক্লিডীয় উপপাদ্য থেকে উচ্চমাত্রিক প্রক্ষেপণ। যেখানে প্রতিটি জ্যামিতিক সত্য একটি জীবন্ত ছবির মতো ধরা দেয়।',
    chapters: [
      'উচ্চমাত্রিক গোলকের আয়তন প্যারাডক্স',
      'প্রজেক্টিভ জিওমেট্রি ও দ্বৈততা নীতি',
      'অ-ইউক্লিডীয় তল ও পরাবৃত্তীয় জ্যামিতি',
      'পিথাগোরাসের দৃশ্যমান উপপাদ্য'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=geometry',
    actionText: 'জ্যামিতি কালেকশন ↗'
  },
  'topology': {
    title: 'টপোলজি (Topology — Rubber Sheet Geometry)',
    icon: '🍩',
    desc: 'দূরত্ব বা আকার নয় — কেবল সংযোগ ও ছিদ্রের জ্যামিতি। কাপ ও ডোনাট কেন একই, এবং হেয়ারি বল উপপাদ্যের বাস্তব তাৎপর্য।',
    chapters: [
      'অয়লার ক্যারেক্টারিস্টিক ও পলিহেড্রা সূত্র (V - E + F = 2)',
      'হেয়ারি বল উপপাদ্য ও পৃথিবীর আবহাওয়ার ঘূর্ণন',
      'মোবিউস স্ট্রিপ ও ক্লাইন বোটল',
      'টরাস ও উচ্চমাত্রিক ম্যানিফোল্ড'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=topology',
    actionText: 'টপোলজি কালেকশন ↗'
  },
  'fractals': {
    title: 'ফ্র্যাক্টাল ও মাত্রা (Fractals & Complex Dynamics)',
    icon: '❄️',
    desc: 'প্রকৃতির অসীম জটিলতার মধ্যে লুকিয়ে থাকা সহজ নিয়ম। ম্যান্ডেলব্রোট সেট, ভগ্নাংশ মাত্রা ও কোস্টলাইন প্যারাডক্স।',
    chapters: [
      'ফ্র্যাক্টাল ডাইমেনশন কী? (1.26 মাত্রার রেখা)',
      'ম্যান্ডেলব্রোট সেট ও জটিল সংখ্যার পুনরাবৃত্তি',
      'জুলিয়া সেট ও ক্যাওস থিওরি',
      'কোচ স্নোফ্লেক ও অসীম পরিসীমা'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=fractals',
    actionText: 'ফ্র্যাক্টাল কালেকশন ↗'
  },
  'probability': {
    title: 'সম্ভাব্যতা ও অনিশ্চয়তার জ্যামিতি (Probability)',
    icon: '🎲',
    desc: '২০২৫-২৬ সালের সর্বাধুনিক ৩Blue1Brown সিরিজ। সম্ভাব্যতাকে ভাগ্যের খেলা না দেখে জ্যামিতিক ক্ষেত্রফল হিসেবে অনুভব করুন।',
    chapters: [
      'সম্ভাব্যতার মৌলিক নীতি ও ভেন ডায়াগ্রামের ক্ষেত্রফল',
      'বেইজের উপপাদ্য (Bayes Theorem) ও আধুনিক এআই পরিসংখ্যান',
      'সেন্ট্রাল লিমিট থিওরেম ও বেল কার্ভের বিস্তার',
      'দৈব চলক ও শর্তসাপেক্ষ প্রত্যাশা'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=probability',
    actionText: 'সম্ভাব্যতা সিরিজ ↗'
  },
  'group-theory': {
    title: 'গ্রুপ তত্ত্ব ও প্রতিসাম্য (Group Theory & Symmetry)',
    icon: '💎',
    desc: 'বিমূর্ত বীজগণিতের সবচেয়ে রাজকীয় শাখা — প্রতিসাম্যের গাণিতিক কাঠামো ও মনস্টার গ্রুপের বিস্ময়।',
    chapters: [
      'প্রতিসাম্য অপারেশন ও গ্রুপ অ্যাবস্ট্রাকশন',
      'পারমুটেশন গ্রুপ ও রুবিকস কিউব সলভিং',
      'মনস্টার গ্রুপ ও মুনশাইন কনজেকচার',
      'কোয়ার্টারনিয়ন ও ঘূর্ণন প্রতিসাম্য'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=group-theory',
    actionText: 'গ্রুপ তত্ত্ব কালেকশন ↗'
  },
  'number-theory': {
    title: 'সংখ্যা তত্ত্ব (Number Theory & Primes)',
    icon: '🔢',
    desc: 'গণিতের রাণী সংখ্যা তত্ত্ব। মৌলিক সংখ্যার রহস্যময় বিন্যাস, রিমান জিটা ফাংশন ও ইউক্লিডীয় অ্যালগরিদম।',
    chapters: [
      'প্রাইম নাম্বারের বণ্টন ও মৌলিক সংখ্যা উপপাদ্য',
      'মডুলার অ্যারিথমেটিক ও ফার্মার লিটল থিওরেম',
      'রিমান হাইপোথিসিস ও ক্রিটিক্যাল স্ট্রিপের রহস্য',
      'ডায়োফ্যান্টাইন সমীকরণ'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=number-theory',
    actionText: 'সংখ্যা তত্ত্ব কালেকশন ↗'
  },
  'lockdown-math': {
    title: 'লকডাউন ম্যাথ (Lockdown Math Live Series)',
    icon: '🏠',
    desc: 'গ্রান্ট স্যান্ডারসনের সরাসরি ইন্টারেক্টিভ লাইভ সেশন — ত্রিকোণমিতি, জটিল সংখ্যা, ফিবোনাচ্চি ও চমৎকার গাণিতিক ব্যাখ্যা।',
    chapters: [
      'জটিল সংখ্যার জ্যামিতিক রূপ ও গুণন',
      'অয়লারের সূত্র (e^{iπ} + 1 = 0) এর প্রমাণ',
      'ফিবোনাচ্চি সংখ্যা ও গোল্ডেন রেশিও',
      'ত্রিকোণমিতির দৃশ্যমান ভিত্তি'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=lockdown-math',
    actionText: 'লকডাউন ম্যাথ দেখুন ↗'
  },
  'guest-videos': {
    title: 'অতিথি ও যৌথ ভিডিও (Guest Videos & Collaborations)',
    icon: '🤝',
    desc: 'Numberphile, Stand-up Maths, Quanta Magazine এবং শীর্ষ গণিতবিদদের সাথে যৌথ প্রযোজনার বিশেষ বিশ্লেষণসমূহ।',
    chapters: [
      'কুর্টজগেজাগ্ট সহযোগিতায় আলোর গতি ও স্থান-কাল',
      'Numberphile-এ অদ্ভুত গাণিতিক অনুপাত',
      'ম্যাথ পাজলারদের সাথে পুতনাম সমাধান',
      'অ্যালেক সানডারসনের বৈজ্ঞানিক আলোচনা'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=guest-videos',
    actionText: 'গেস্ট ভিডিও কালেকশন ↗'
  },
  'talks': {
    title: 'বক্তৃতা ও আলোচনা (Talks & Lectures)',
    icon: '🎙️',
    desc: 'গ্রান্ট স্যান্ডারসনের মূল দর্শন — গণিত কীভাবে শেখানো উচিত, কেন ভিজ্যুয়ালাইজেশন জরুরি এবং ওপেন-সোর্স মানিম (Manim) ইঞ্জিন তৈরির ইতিহাস।',
    chapters: [
      'গণিত শিক্ষার মূল দর্শন ও রূপক সৃষ্টির কৌশল',
      'মানিম (Manim) অ্যানিমেশন ইঞ্জিনের উৎপত্তি ও স্থাপত্য',
      'স্ট্যানফোর্ড ও এমআইটি আমন্ত্রিত বক্তৃতা',
      'এআই যুগে গণিত শিক্ষার ভবিষ্যৎ'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=talks',
    actionText: 'বক্তৃতা তালিকা দেখুন ↗'
  },
  'other-channels': {
    title: 'অন্যান্য চ্যানেলে (On Other Channels)',
    icon: '📺',
    desc: 'লেক্স ফ্রিডম্যান পডকাস্ট, ভেরিটাসিয়াম ও অন্যান্য আন্তর্জাতিক চ্যানেলে গ্রান্ট স্যান্ডারসনের গভীর সাক্ষাৎকার ও অংশগ্রহণ।',
    chapters: [
      'লেক্স ফ্রিডম্যান পডকাস্ট: গণিত, এআই ও মহাবিশ্ব',
      'ভেরিটাসিয়াম: অপটিক্যাল প্যারাডক্স ও বিদ্যুৎ প্রবাহ',
      'কোয়ান্টাম ম্যাগাজিন সাক্ষাৎকার',
      'কম্পিউটারফাইল বিশেষ পর্ব'
    ],
    officialUrl: 'https://www.3blue1brown.com/?topic=other-channels',
    actionText: 'অন্যান্য ভিডিও দেখুন ↗'
  }
};

function openTopicModal(topicId) {
  const data = TOPIC_DETAILS[topicId];
  if (!data) return;

  const overlay     = document.getElementById('topicModalOverlay');
  const iconEl      = document.getElementById('modalTopicIcon');
  const titleEl     = document.getElementById('modalTopicTitle');
  const subEl       = document.getElementById('modalTopicSub');
  const descEl      = document.getElementById('modalTopicDesc');
  const chaptersEl  = document.getElementById('modalTopicChapters');
  const actionLink  = document.getElementById('modalActionLink');
  const closeBtn    = document.getElementById('modalTopicClose');

  if (!overlay) return;

  if (iconEl)     iconEl.textContent = data.icon || '📚';
  if (titleEl)    titleEl.textContent = data.title;
  if (subEl)      subEl.textContent = `3Blue1Brown Collection • ${data.chapters?.length || 4}+ কী অধ্যায়`;
  if (descEl)     descEl.textContent = data.desc;

  if (chaptersEl) {
    chaptersEl.innerHTML = (data.chapters || []).map(ch => `
      <li class="topic-modal__chapter-item">
        <span style="color:var(--accent-blue);font-weight:bold;">✦</span>
        <span>${ch}</span>
      </li>
    `).join('');
  }

  if (actionLink) {
    if (data.internalUrl) {
      actionLink.href = data.internalUrl;
      actionLink.target = '_self';
      actionLink.textContent = data.actionText || 'কোর্সে যান →';
    } else {
      actionLink.href = data.officialUrl || 'https://www.3blue1brown.com';
      actionLink.target = '_blank';
      actionLink.rel = 'noopener';
      actionLink.textContent = data.actionText || 'অফিসিয়াল পেজ ↗';
    }
  }

  overlay.classList.add('open');

  const closeModal = () => {
    overlay.classList.remove('open');
  };

  closeBtn?.addEventListener('click', closeModal, { once: true });
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  }, { once: true });
}

function initTopicsCollection() {
  const cards = document.querySelectorAll('.topic-card[data-topic-id]');
  cards.forEach(card => {
    const tid = card.dataset.topicId;
    card.addEventListener('click', () => {
      openTopicModal(tid);
    });
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openTopicModal(tid);
      }
    });
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'button');
  });

  // Filter Bar Functionality
  const filterBtns = document.querySelectorAll('.topic-filter-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');

      const filter = btn.dataset.filter;
      cards.forEach(card => {
        const cat = card.dataset.category;
        const tid = card.dataset.topicId;
        if (filter === 'all') {
          card.style.display = 'flex';
        } else if (filter === cat || filter === tid) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
}

/* ============================================================
   9. BACK TO TOP BUTTON
   ============================================================ */
function initBackToTop() {
  const btn = document.getElementById('backToTop');
  if (!btn) return;

  const onScroll = () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ============================================================
   8. PROGRESS BARS — animated fill on intersection
   ============================================================ */
function initProgressBars() {
  const fills = document.querySelectorAll('.track-card__progress-fill[data-progress]');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const fill = entry.target;
        const pct  = parseInt(fill.dataset.progress, 10) || 0;
        // Delayed start for visual effect
        setTimeout(() => { fill.style.width = pct + '%'; }, 200);
        observer.unobserve(fill);
      }
    });
  }, { threshold: 0.2 });

  fills.forEach(fill => {
    fill.style.width = '0%';
    observer.observe(fill);
  });
}

/* ============================================================
   9. SCROLL ANIMATIONS — Intersection Observer fade-in
   ============================================================ */
function initScrollAnimations() {
  const items = document.querySelectorAll('.animate-fade-up');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  items.forEach(el => {
    el.style.animationPlayState = 'paused';
    observer.observe(el);
  });
}

/* ============================================================
   10. MATH RENDERER STUB (Lightweight offline KaTeX alternative)
   ============================================================ */
function initMathRenderer() {
  // Process elements marked with class 'math-render'
  const mathEls = document.querySelectorAll('.math-render');

  mathEls.forEach(el => {
    const src  = el.dataset.tex || el.textContent;
    const mode = el.dataset.mode || 'inline'; // 'inline' | 'display'

    // Try KaTeX if available (loaded via CDN stub in libs/)
    if (window.katex) {
      try {
        katex.render(src, el, {
          throwOnError: false,
          displayMode: mode === 'display',
          output: 'html',
        });
        return;
      } catch (_) { /* fall through to text render */ }
    }

    // Fallback: styled text
    el.classList.add(mode === 'display' ? 'math-display' : 'math-inline');
    el.textContent = src;
  });
}

/* ============================================================
   11. PROGRESS STORAGE — localStorage persistence
   ============================================================ */
function loadProgress() {
  try {
    const saved = localStorage.getItem('3b1b-progress');
    if (saved) APP.progress = JSON.parse(saved);
  } catch (_) { APP.progress = {}; }
  syncProgressUI();
}

function markLessonComplete(courseId, lessonId) {
  if (!APP.progress[courseId]) APP.progress[courseId] = {};
  APP.progress[courseId][lessonId] = true;
  try {
    localStorage.setItem('3b1b-progress', JSON.stringify(APP.progress));
  } catch (_) {}
  syncProgressUI();
  toast('✅ পাঠ সম্পন্ন হিসেবে চিহ্নিত!', 'success');
}

function syncProgressUI() {
  // Update lesson status icons
  document.querySelectorAll('.lesson-item[data-lesson-id][data-course-id]').forEach(item => {
    const courseId  = item.dataset.courseId;
    const lessonId  = item.dataset.lessonId;
    const statusEl  = item.querySelector('.lesson-item__status');
    const isDone    = APP.progress[courseId]?.[lessonId];
    if (statusEl) statusEl.textContent = isDone ? '✅' : '▷';
    item.classList.toggle('completed', !!isDone);
  });

  // Update badge counts
  document.querySelectorAll('[data-course-id-progress]').forEach(badge => {
    const courseId = badge.dataset.courseIdProgress;
    const total    = parseInt(badge.dataset.total, 10) || 0;
    const done     = Object.values(APP.progress[courseId] || {}).filter(Boolean).length;
    badge.textContent = `${done} / ${total} সম্পন্ন`;
  });
}

/* ============================================================
   12. TOAST NOTIFICATION SYSTEM
   ============================================================ */
function toast(message, type = 'info', duration = 3000) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const el = document.createElement('div');
  el.className = `toast toast--${type}`;
  el.textContent = message;

  container.appendChild(el);

  setTimeout(() => {
    el.style.animation = `toastOut ${250}ms ease forwards`;
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }, duration);
}

/* ============================================================
   13. GLOBAL KEYBOARD PLAY/PAUSE SHORTCUT
   ============================================================ */
document.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && (e.target === document.body || e.target.classList.contains('player-controls__progress'))) {
    e.preventDefault();
    const mainPlayBtn = document.getElementById('mainPlayBtn');
    mainPlayBtn?.click();
  }
});

/* ============================================================
   14. SMOOTH SCROLL for anchor links
   ============================================================ */
document.addEventListener('click', (e) => {
  const anchor = e.target.closest('a[href^="#"]');
  if (!anchor) return;
  const target = document.querySelector(anchor.getAttribute('href'));
  if (target) {
    e.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});

/* ============================================================
   15. CURRICULUM DATA LOADER (async JSON fetch)
   ============================================================ */
async function loadCurriculum(path = 'curriculum_index.json') {
  try {
    const res  = await fetch(path);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn('পাঠ্যক্রম লোড করা যায়নি:', err.message);
    return null;
  }
}

/* ============================================================
   16. KEYBOARD ACCESSIBILITY
   ============================================================ */
document.addEventListener('keydown', (e) => {
  // Escape closes all overlays
  if (e.key === 'Escape') {
    if (APP.searchOpen) document.getElementById('searchClose')?.click();
    if (APP.mobileNavOpen) document.getElementById('hamburger')?.click();
  }
});

/* ============================================================
   17. RESIZE HANDLER — close mobile nav on resize up
   ============================================================ */
window.addEventListener('resize', () => {
  if (window.innerWidth > 768 && APP.mobileNavOpen) {
    APP.mobileNavOpen = false;
    document.getElementById('mobileNav')?.classList.remove('open');
    const hamburger = document.getElementById('hamburger');
    if (hamburger) {
      hamburger.setAttribute('aria-expanded', 'false');
      hamburger.querySelectorAll('span').forEach(s => s.style.cssText = '');
    }
  }
}, { passive: true });

/* ============================================================
   18. PUBLIC API (exposed for other scripts & console)
   ============================================================ */
window.BengaliMath = {
  toast,
  markLessonComplete,
  loadCurriculum,
  applyTheme,
  getProgress: () => ({ ...APP.progress }),
  version: APP.version,
};
