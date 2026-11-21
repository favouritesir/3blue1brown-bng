# লেকচার ০১ — কম্পোনেন্ট ইনভেন্টরি ও মাইগ্রেশন ম্যাপ

> স্ট্যাটাস: **অডিট সম্পন্ন** · তৈরি: ২০২৬-১১-১৯ · কোর্স: `linear_algebra` · লেকচার: `lesson_01`
> উদ্দেশ্য: লেকচার ০১-কে ওয়েব-কম্পোনেন্ট-ভিত্তিক আর্কিটেকচারে মাইগ্রেট করা এবং বাকি ৫২টি লেকচারের জন্য ক্যানোনিকাল টেমপ্লেট হিসেবে প্রতিষ্ঠা করা।

---

## ১. বর্তমান অবস্থা (Baseline Audit)

| পর্যবেক্ষণ | ফলাফল |
|:---|:---|
| `lesson_01.html` কম্পোনেন্ট ব্যবহার করে? | ❌ **না** — সম্পূর্ণ র কম্পোনেন্টসহ র বা Raw HTML + inline `<script>` |
| `lesson_components.js` লোড করা আছে? | ❌ **না** — কেবল sandbox demo-তে আছে |
| কম্পোনেন্ট লাইব্রেরি অবস্থা | ✅ ২২টি কম্পোনেন্ট তৈরি, কিন্তু **প্রোডাকশনে কখনো ব্যবহৃত হয়নি** |
| ন্যারেশন ইঞ্জিন | ✅ কাজ করে, কিন্তু DOM পার্সিংয়ের সময় কম্পোনেন্ট-রেন্ডার্ড ব্লক ধরতে পারবে না (setTimeout সমস্যা) |

---

## ২. লেকচার ০১-এ ব্যবহৃত সমস্ত UI ব্লক → কম্পোনেন্ট ম্যাপিং

### ২.১ বিদ্যমান কম্পোনেন্ট (পুনর্ব্যবহারযোগ্য)

| # | Raw HTML ব্লক (বর্তমান) | কম্পোনেন্ট | অবস্থা | মাইগ্রেশন নোট |
|:--:|:---|:---|:---:|:---|
| ১ | `<div id="searchOverlay">` | `<b1b-search-overlay>` | ✅ আছে | সরাসরি প্রতিস্থাপন |
| ২ | `<nav class="site-nav">` (সম্পূর্ণ) | `<b1b-navbar>` + `<b1b-stepper>` | ✅ আছে | attributes দিয়ে কনফিগার; মোবাইল স্টেপার CSS কম্পোনেন্টেই আছে |
| ৩ | `<div class="lesson-hero">` (ভিডিও + মেটাডাটা) | `<b1b-hero-player>` | ✅ আছে | `video-src`, `yt-id` ইত্যাদি অ্যাট্রিবিউট |
| ৪ | `<div class="toc-card">` | `<b1b-toc-sidebar variant="card">` | ✅ আছে | `<a>` চাইল্ড হিসেবে লিংক |
| ৫ | `<div class="chapter-quote">` | `<b1b-quote author="...">` | ✅ আছে | ⚠️ **সিঙ্ক্রোনাস রেন্ডার ফিক্স দরকার** |
| ৬ | `<figure class="lesson-figure">` | `<b1b-figure src alt caption>` | ✅ আছে | चित्र ব্যাখ্যা caption-এ |
| ৭ | `<div class="callout callout-*">` | `<b1b-callout type icon title>` | ✅ আছে | ⚠️ **সিঙ্ক্রোনাস রেন্ডার ফিক্স দরকার** |
|  eighth | `<div class="formula-box">$$...$$</div>` | `<b1b-formula math="...">` | ✅ আছে | KaTeX অ্যাট্রিবিউট |
| ৯ | `<div class="quiz-block">` × ৩ | `<b1b-quiz>` + `<div slot="option">` | ✅ আছে | সঠিক/ভুল ব্যাখ্যা অ্যাট্রিবিউটে |
| ১০ | `<div class="watch-mode-panel">` | `<b1b-watch-panel>` | ✅ আছে | প্লেলিস্ট slot |
| ১১ | `<div class="chapter-nav-cards">` | `<b1b-chapter-nav>` | ✅ আছে | prev/next অ্যাট্রিবিউট |
| ১২ | `<footer class="site-footer">` | `<b1b-footer>` | ✅ আছে | ক্রেডিট |
| ১৩ | ফ্লোটিং অডিও পিল | `narration_engine.js` (JS ইঞ্জিন) | ✅ আছে | DOM-নির্ভর, কম্পোনেন্ট নয় |
| ১৪ | ব্যাক-টু-টপ বাটন | `<b1b-back-to-top>` | ✅ আছে | `lesson.js`-এর সাথে ডুপ্লিকেট গার্ড আছে |

### ২.২ নতুন করে তৈরি করতে হবে (গ্যাপ)

| # | Raw HTML ব্লক (বর্তমান) | নতুন কম্পোনেন্ট | কারণ |
|:--:|:---|:---|:---|
| ১ | `<div class="narration-card">` (শিক্ষক অডিও ব্যানার) | **`<b1b-narration-banner>`** | `#btnListenFullArticle` বাটন এনক্যাপসুলেট করা দরকার |
| ২ | `<div class="bookmark-ribbon">` + chips | **`<b1b-bookmarks>`** + `<b1b-bookmark>` | টাইমস্ট্যাম্প জাম্প লজিক পুনর্ব্যবহারযোগ্য |
| ৩ | `<div class="section-header-wrap">` + narrate button | **`<b1b-section-header>`** (বা `b1b-section`-এ ইন্টিগ্রেট) | প্রতি সেকশনে অডিও বাটন স্বয়ংক্রিয় |
| ৪ | `<div class="interactive-calc-box" id="vectorDecomposerBox">` + inline script | **`<b1b-vector-decomposer>`** | ইনলাইন JS-কে স্কোপড কম্পোনেন্টে রূপান্তর |
|  fifth | `<section id="sec-visualizer">` + inline SVG controller | **`<b1b-vector-plane>`** | ড্র্যাগ/স্লাইডার/থিম লজিক এনক্যাপসুলেট |
| ৬ | `<article class="article">` | **`<b1b-article>`** | সামগ্রিক_container, TOC/ন্যারেশন হুক |

---

## ৩. সমালোচনামূলক প্রযুক্তিগত ঋণ (Critical Tech Debt)

### ৩.১ setTimeout-জনিত ন্যারেশন সিঙ্ক ভাঙ্গন
`B1bQuote`, `B1bCallout`, `B1bQuiz` তাদের `connectedCallback`-এ `setTimeout(..., 0)` ব্যবহার করে।
`narration_engine.js` `DOMContentLoaded`-এ একবারই `parseContent()` চালায়। ফলে কম্পোনেন্ট-রেন্ডার্ড
`.chapter-quote` ও `.callout` ব্লকগুলো **ধরা পড়বে না** → DOM ব্লক সংখ্যা ও ম্যানিফেস্ট কিউ সংখ্যার মিল ভেঙে যাবে।

**সমাধান:** এই তিনটি কম্পোনেন্টকে **সিঙ্ক্রোনাস** রেন্ডারে রূপান্তর করা (guard সহ)।

### ৩.২gulp ফাইল-স্কোপ আইডি
ইনলাইন ভিজ্যুয়ালাইজার `decompX`, `decompY`, `svgVectorLine` ইত্যাদি গ্লোবাল আইডি ব্যবহার করে।
একাধিক কম্পোনেন্ট ইনস্ট্যান্সে কনফ্লিক্ট হবে।

**সমাধান:** প্রতিটি কম্পোনেন্ট ইনস্ট্যান্সের জন্য ইউনিক সাফিক্স (`this._uid`) তৈরি করে স্কোপড আইডি।

### ৩.৩ অডিও টাইম-সিঙ্ক (ডাবড ভিডিও)
`run_3b1b_dubbing_pipeline.py`-এ `current_time += actual_stretched_dur` করা হয়, কিন্তু `atempo` 0.85–1.35-এ ক্ল্যাম্প করা হয়।
ফলে দীর্ঘ বাংলা বাক্য target window-এ না ফিট হলে **ক্রমান্বয়ে ড্রিফ্ট (cumulative drift)** জমা হয়।

**সমাধান:** আলাদা实验 পাইপলাইন — প্রতিটি কিউ silicones-এ exact sample-এ `atrim`/`apad` দিয়ে নির্দিষ্ট দৈর্য্যে আনা হবে এবং `adelay` দিয়ে নির্দিষ্ট অফসেটে বসানো হবে (কোনো ক্রমান্বয়ী হিসাব নেই)। মূল পাইপলাইন অক্ষত থাকবে।

---

## ৪. মাইগ্রেশন পরবর্তী কাঠামো (Target Architecture)

```html
<b1b-search-overlay></b1b-search-overlay>
<b1b-navbar ...></b1b-navbar>
<b1b-hero-player ...></b1b-hero-player>

<div class="lesson-body">
  <div class="read-mode">
    <b1b-narration-banner></b1b-narration-banner>
    <b1b-bookmarks>...</b1b-bookmarks>
    <b1b-toc-sidebar variant="card">...</b1b-toc-sidebar>

    <b1b-article>
      <b1b-section id="sec-interpretations" title="...">
        <b1b-quote ...></b1b-quote>
        <p>...</p>
        <b1b-figure ...></b1b-figure>
        <b1b-callout ...>...</b1b-callout>
      </b1b-section>
      ...
      <b1b-section id="sec-basis">
        <b1b-vector-decomposer></b1b-vector-decomposer>
      </b1b-section>
      <b1b-section id="sec-visualizer">
        <b1b-vector-plane></b1b-vector-plane>
      </b1b-section>
    </b1b-article>
  </div>

  <b1b-watch-panel ...></b1b-watch-panel>
</div>

<b1b-chapter-nav ...></b1b-chapter-nav>
<b1b-footer></b1b-footer>
<b1b-back-to-top></b1b-back-to-top>
```

---

## ৫. স্ক্রিপ্ট লোড অর্ডার (কঠোর)

1. `manifest.js` (sync — ন্যারেশন ম্যানিফেস্ট)
2. `katex.min.css`, `main.css`, `lesson.css`, `narration.css`
3. `katex.min.js`, `auto-render.min.js`, `katex-stub.js` (defer)
4. **`lesson_components.js`** (sync — কম্পোনেন্ট ডেফিনিশন)
5. **`lesson_components_extended.js`** (sync — নতুন কম্পোনেন্ট)
6. `main.js`, `lesson.js` (defer)
7. `narration_engine.js` (defer — সবার শেষে, DOM পার্সের জন্য)
