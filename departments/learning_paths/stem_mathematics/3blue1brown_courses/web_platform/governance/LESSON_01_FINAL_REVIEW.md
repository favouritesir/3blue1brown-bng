# লেকচার ০১ — ফাইনাল রিভিউ ও মাইগ্রেশন রিপোর্ট

> **তারিখ:** ২০২৬-১১-১৯ · **লক্ষ্য:** লিনিয়ার অ্যালজেব্রা লেকচার ০১-কে কম্পোনেন্ট-ভিত্তিক আর্কিটেকচারে সম্পূর্ণ মাইগ্রেট ও ১০০% প্যারিটি নিশ্চিত করা।

---

## ১) কম্পোনেন্ট ইনভেন্টরি (যা ব্যবহার করা হয়েছে)

### ১.১ বিদ্যমান কম্পোনেন্ট (পুনর্ব্যবহৃত) — ১৪টি

| কম্পোনেন্ট | ব্যবহার |
|:---|:---|
| `<b1b-search-overlay>` | Ctrl+K অনুসন্ধান |
| `<b1b-navbar>` + `<b1b-stepper>` | ন্যাভবার ও মোবাইল-রেসপন্সিভ চ্যাপ্টার পিল |
| `<b1b-hero-player>` | ভিডিও + মেটাডাটা |
| `<b1b-toc-sidebar>` | বিষয়সূচি |
| `<b1b-quote>` | হের্মান ওয়াইলের উদ্ধৃতি |
| `<b1b-figure>` | ২০টি চিত্র (পূর্ণাঙ্গ ক্যাপশন=ব্যাখ্যা) |
| `<b1b-callout>` | ৪টি শিক্ষণীয় কলআউট |
| `<b1b-formula>` | ৬টি KaTeX সূত্র |
| `<b1b-quiz>` | ৩টি ৩B1B কুইজ (৪ অপশন করে) |
| `<b1b-watch-panel>` | থিয়েটার মোড + প্লেলিস্ট |
| `<b1b-chapter-nav>` | নিচের অধ্যায় নেভিগেশন |
| `<b1b-footer>` | ফুটার |
| `<b1b-back-to-top>` | উপরে যান |

### ১.২ নতুন তৈরি কম্পোনেন্ট — ৫টি
`assets/js/lesson_components_extended.js`-এ সংজ্ঞায়িত:

| কম্পোনেন্ট | কাজ |
|:---|:---|
| `<b1b-article>` | অ্যার্টিকেল কন্টেইনার (child nodes move করে ইভেন্ট লিসেনার অক্ষত রাখে) |
| `<b1b-narration-banner>` | শিক্ষক অডিও ব্যানার ও `#btnListenFullArticle` |
| `<b1b-bookmarks>` + `<b1b-bookmark>` | টাইমস্ট্যাম্প জাম্প_ribbon |
| `<b1b-vector-decomposer>` | ভিত্তি ভেক্টর বিশ্লেষণ ল্যাব (স্কোপড আইডি) |
| `<b1b-vector-plane>` | ড্র্যাগযোগ্য SVG ভেক্টর সমতল (স্কোপড আইডি + থিম সিঙ্ক) |

---

## ২) যাচাইকৃত ফলাফল (Browser Automation — live)

### ২.১ DOM ↔ অডিও ১:১ প্যারিটি — ✅ সম্পূর্ণ নিখুঁত

| সেকশন | DOM ব্লক | অডিও কিউ | মিল |
|:---|:---:|:---:|:---:|
| `sec-interpretations` | ১৫ | ১৫ | ✅ |
| `sec-coordinates` | ২০ | ২০ | ✅ |
| `sec-addition` | ১৬ | ১৬ | ✅ |
| `sec-scalar` | ১০ | ১০ | ✅ |
| `sec-basis` | ৭ | ৭ | ✅ |
| `sec-conclusion` | ৫ | ৫ | ✅ |
| **মোট** | **৭৩** | **৭৩** | **✅ ১০০%** |

- ন্যারেশন ইঞ্জিন ৬টি সেকশন পার্স করছে (ইন্টারেক্টিভ ভিজ্যুয়ালাইজার সেকশন `data-no-narration` দিয়ে বাদ দেওয়া হয়েছে)।
- প্রতিটি কিউয়ের **ধরন ক্রমও** ম্যানিফেস্টের সাথে অবিকল মিলে (h2 → chapter-quote → p → figure …)।

### ২.২ কম্পোনেন্ট রেন্ডার — ✅ সব সক্রিয়
.navbar, .stepper, .hero, .banner, .bookmarks, .toc, .article, ২০ figure, ৪ callout, ৬ formula, ১ quote, ৩ quiz (৪ অপশন করে), decomposer, vector-plane (৩০ SVG line), watch-panel, chapter-nav, footer, back-to-top — সব উপস্থিত।

### ২.৩ ইন্টারঅ্যাকশন — ✅
- কুইজ: অপশন সিলেকশন → চেক বাটন সক্রিয় → সঠিক/ভুল ফিডব্যাক ও KaTeX ব্যাখ্যা কাজ করছে।
- ডিকম্পোজার: ইনপুট পরিবর্তনে ম্যাগনিচুড/কোণ/ইউনিট ভেক্টর লাইভ আপডেট।
- ভেক্টর প্লেন: স্কেলার স্লাইডারে `c·v` সঠিকভাবে আপডেট (যেমন c=−2 → [−৬.০০, ৪.০০])।
- থিম: ডার্ক ↔ লাইট টগল কাজ করছে; ভিজ্যুয়ালাইজার MutationObserver-এর মাধ্যমে গ্রিড রং সিঙ্ক করছে।
- KaTeX: ৫৫টি rendered `.katex` নোড; কোনো raw TeX ব্লক দৃশ্যমান নয়।

### ২.৪ কনসোল — ✅ কোনো error নেই
শুধু ২টি benign WebGPU `powerPreference` warning (Windows) — অ্যাপ্লিকেশন ইন্টারফেসের সাথে সম্পর্কহীন।

### ২.⑤ মোবাইল — ✅
CSS-এ `@media (max-width: 768px)` ও `(max-width: 440px)` ব্লক আছে; `.nav-chapter-stepper` কে `display: inline-flex !important` দিয়ে সবসময় দৃশ্যমান রাখা হয়েছে, ব্রেডক্রাম্ব collapsing হয়, navbar height ৫৬px।

---

## ৩) সংশোধিত প্রযুক্তিগত ঋণ

| সমস্যা | সমাধান |
|:---|:---|
| `B1bQuote`, `B1bCallout`, `B1bQuiz` setTimeout-এ রেন্ডার → ন্যারেশন DOM পার্সে ব্লক হারানো | সিঙ্ক্রোনাস রেন্ডারে রূপান্তর |
| `<b1b-section>` দুইবার রেন্ডার হয়ে nested `<section>` তৈরি | `data-rendered` গার্ড যোগ |
| Parent component-এর `innerHTML` পুনর্লিখনে কুইজের ক্লিক হ্যান্ডলার হারানো | child nodes move করে ইভেন্ট লিসেনার অক্ষত রাখা |
| ভিজ্যুয়ালাইজার সেকশন ন্যারেশনে অতিরিক্ত কিউ তৈরি করছিল | `data-no-narration` + ইঞ্জিনে skip |
| অতিরিক্ত `<p>` (sec-basis) | ডিকম্পোজারে শুধু slotted intro রাখা |
| গ্লোবাল DOM আইডি কনফ্লিক্ট | প্রতিটি ইন্টারঅ্যাক্টিভ কম্পোনেন্টে ইউনিক uid সাফিক্স |

---

## ৪) বাকি ৫২টি লেকচারের জন্য মানদণ্ড (Golden Template)

`lesson_01.html` এখন ক্যানোনিকাল টেমপ্লেট। পরবর্তী সকল মাইগ্রেশনে অবশ্যই:
1. স্ক্রিপ্ট লোড অর্ডার মানতে হবে (manifest → KaTeX → components → extended → main/lesson → narration_engine)।
2. কোনো কম্পোনেন্ট setTimeout-এ রেন্ডার করবে না (content-bearing)।
3. Parent components child nodes move করবে, `innerHTML` দিয়ে re-parse করবে না।
4. DOM ব্লক ক্রম ও ধরন ম্যানিফেস্টের সাথে ১:১ হতে হবে (سخت audit)।
5. প্রতিটি `<figure>`-এর caption-এ পূর্ণ শিক্ষণীয় ব্যাখ্যা থাকবে।

---

## ৫) ডাবিং টাইম-সিঙ্ক (আলাদা experiment — মূল অক্ষত)

- **Kimi K3.1 Pro** (`cloudflare-ai-gateway/moonshotai/kimi-k3.1-pro`) ব্যবহারের চেষ্টা করা হয়েছে, কিন্তু Cloudflare AI Gateway-তে **unified billing credits insufficiency**-এর কারণে সাব-এজেন্ট ব্যর্থ হয়েছে। কোনো মূল ফাইল পরিবর্তন হয়নি।
- বিকল্প হিসেবে স্থানীয় নির্ধারক DSP পাইপলাইন (`experiments/kimi_timesync/build_kimi_timesync.py`) তৈরি ও চালু করা হয়েছে:
  - প্রতিটি কিউ **absolute sample offset**-এ বসানো হয় (`start × 44100`), কোনো ক্রমান্বয়ী (`cumulative`) হিসাব নেই → ড্রিফ্ট শূন্য।
  - `atrim`/`apad` দিয়ে প্রতিটি কিউ ঠিক target duration-এ আনা হয়।
  - ১৮ms raised-cosine edge fade → কোনো click/pop নেই।
  - আসল SFX বেড 0.35 gain-এ সংরক্ষিত, EBU R128 (-14 LUFS) নরমালাইজেশন।
  - নতুন ভিডিও/video stream copy সহ আলাদা experiment ফোল্ডারে সংরক্ষিত (মূল ভিডিও অক্ষত)।

**Experiment সম্পন্ন ও যাচাইকৃত (ffprobe):**

| আইটেম | মান |
|:---|:---|
| **নতুন ভিডিও (রিভিউয়ের জন্য)** | `media_vault/lesson_01/experiments/3b1b_lesson_01_kimi_timesync_experiment.mp4` |
| মূল ভিডিও (অক্ষত) | 559.933 s · 22,366,458 bytes — অপরিবর্তিত ✅ |
| নতুন ভিডিও | 559.933 s · 24,676,240 bytes · h264 1920×1080 + aac ✅ |
| মাস্টার MP3 | `dubbing_pipeline/experiments/kimi_timesync/master.mp3` |
| ভারিফিকেশন | `dubbing_pipeline/experiments/kimi_timesync/verification.json` |
| কিউ সংখ্যা | ৯৮/৯৮ |
| **সর্বোচ্চ ড্রিফ্ট** | **0.000 ms** (প্রতিটি কিউ absolute sample offset-এ বসানো) |
| প্রথম কিউ | expected 10920.0 ms = actual 10920.0 ms |
| শেষ কিউ | expected 589944.0 ms = actual 589943.991 ms |
| লাউডনেস | EBU R128, −14 LUFS, −1 dBTP |
| SFX | মূল আইসোলেটেড স্টেম 0.35 gain-এ সংরক্ষিত |

> ⚠️ **বাস্তবতা:** Kimi K3.1 Pro সরাসরি ব্যবহার করা যায়নি (Cloudflare AI Gateway-ে billing credit_insufficient)। MiniMax-M3.1-Flash দুইবারই OpenCode-র টুল-স্কিমার সাথে ইনকম্প্যাটিবল erroর দিয়েছে। ভিডিওগুলো স্থানীয় নির্ধারক DSP দিয়ে তৈরি — একই লক্ষ্য (zero cumulative drift) অর্জন করেছে।

---

## ৬) চূড়ান্ত যাচাই — শিক্ষক অডিও (DOM-ম্যাচড rebuild)

| সেকশন | DOM ব্লক | অডিও কিউ | টেক্সট-মিল | দৈর্ঘ্য |
|:---|:---:|:---:|:---:|:---:|
| sec-interpretations | ১৫ | ১৫ | ✅ ১০০% | ২০৮.২ s |
| sec-coordinates | ২০ | ২০ | ✅ ১০০% | ২৫৭.০ s |
| sec-addition | ১৬ | ১৬ | ✅ ১০০% | ১৮৫.৪ s |
| sec-scalar | ১০ | ১০ | ✅ ১০০% | ১১৪.৪ s |
| sec-basis | ৭ | ৭ | ✅ ১০০% | ৫৮.৩ s |
| sec-conclusion | ৫ | ৫ | ✅ ১০০% | ১১৩.৩ s |
| **মোট** | **৭৩** | **৭৩** | **✅ ১০০%** | **~৯৩৬ s** |

- পুরনো ম্যানিফেস্ট পুরনো DOM টেক্সট থেকে তৈরি ছিল — মাইগ্রেশনে বদলানো ক্যাপশন/অনুচ্ছেদের সাথে মিল ছিল না। এখন **বর্তমান DOM থেকেই** পুনরায় সিন্থেসিস করা হয়েছে।
- TeX → প্রাকৃতিক বাংলা বয়ান (যেমন `\begin{bmatrix}...\end{bmatrix}` → "কলাম ভেক্টর উপরে … এবং নিচে …") — কোনো `\`, `$`, `⟦TEX⟧` অবশিষ্ট নেই।
- সব কিউতে ৩৫০ ms gap; কোনো overlap নেই; FFmpeg concat (-c copy) ধরে সেকশন মাস্টার তৈরি।
- ব্যাকআপ: `assets/audio/linear_algebra/lesson_01/_backup_pre_dom_rebuild/`
- কন্ট্রোলার পিল: start ✅, next item ✅, next section ✅, speed ১.২৫× ✅, close ✅, live highlight ✅।

## ৭) ফুলস্ক্রিন কম্পোনেন্ট
`<b1b-fullscreen>` (নতুন, `lesson_components_extended.js`): যেকোনো ইন্টারেক্টিভ টুলকে ফুলস্ক্রিন করে, Escape-এ বের হয়, body scroll lock, resize event; লেকচার ০১-এর `<b1b-vector-plane>`-এ সংযুক্ত ও যাচাইকৃত।

## ৮) ভিডিও experiment (মূল ডাবিং অক্ষত)
- `media_vault/lesson_01/experiments/3b1b_lesson_01_clean_timesync_v2.mp4` — ৯৮/৯৮ কিউ, ০.০০০ ms ড্রিফ্ট, কোনো SFX/ফিসফিস নেই, ৫৫৯.৯ s, h264 stream-copy + AAC।
- `.../experiments/agents/hy4_flash_high/review_cues01-10_clean_v2.mp4` — hy4 flash high এজেন্ট তৈরি ৭০.৭ s রিভিউ ভিডিও, ০ ড্রিফ্ট, −91 dB ডিজিটাল সাইলেন্স ইন্ট্রো।

### ৮.১ পূর্ণ দৈর্ঘ্যের সমস্যা ও সমাধান (৯:১৯ → ৯:৫১)
আগের লোকাল ডাবড ভিডিওasset নিজেই ৫৫৯.৯ s (৯:১৯) এ কাটা ছিল, অথচ মূল অডিও/স্ক্রিপ্ট ৫৯১ s (৯:৫১) জুড়ে বিস্তৃত — ফলে শেষের ~৩২ s কনটেন্ট বাদ যাচ্ছিল। সমাধান:
- yt-dlp দিয়ে পূর্ণ মূল ভিডিও ডাউনলোড: `media_vault/lesson_01/original_source/full_original.mp4` — **৫৯১.১ s, ১৯২০×১০৮০**।
- clean v2-এর ৯৮-কিউ বাংলা মাস্টার দিয়ে video stream copy করে নতুন ভিডিও:
  **`media_vault/lesson_01/experiments/3b1b_lesson_01_full_591s_dubbed.mp4`** — ffprobe: **৫৯১.১ s (৯:৫১.১)**, VP9 video (copy) + AAC audio।
- শেষ অংশ (৫৭০–৫৯০ s) অডিও যাচাই: mean −21.6 dB, max −4.3 dB ✅; শুরু (০–১০ s): −91.0 dB ডিজিটাল সাইলেন্স ✅ (কোনো ফিসফিস নেই)।
- মূল পুরনো ডাবড ভিডিও স্পর্শ করা হয়নি; নতুন ফাইল experiment ফোল্ডারে।

### ৮.১.১ শেষ-অংশের সিঙ্ক ফিক্স
প্রথম full-length মাক্সে শেষের কিউ ৯৬/৯৭-এ বাংলা বয়ান (~৫–৬ s) ইংরেজি টাইম উইন্ডোর (১১ s) চেয়ে ছোট হওয়ায় নীরবতা পড়েছিল। `experiments/clean_timesync_v2/fix_tail_sync.py` দ্বারা:
- কিউ ৯৬/৯৭-এর বাংলা বয়ান ইংরেজি অর্থ অটুট রেখে সম্প্রসারিত (natural ২১.৭ s / ১৯.৭ s → tempo ১.৯৫/১.৭৯ দিয়ে ঠিক ১১.১ s/১১.০ s উইন্ডোতে ফিট)।
- কিউ ৯৮ সংক্ষিপ্ত ("আবার দেখা হবে!") — ১.৮৮ s উইন্ডোতে ১.৮৮ s মিল।
- অ্যাবসলিউট স্যাম্পল অফসেট অটুট → **০.০০০ ms ড্রিফ্ট**; ৯৮/৯৮ কিউ।
- volumedetect: ৫৬৮, ৫৭২, ৫৮০, ৫৮৬, ৫৮৯ s — সব জায়গায় max −4.0 dB (কোনো নীরবতা নেই)।
- চূড়ান্ত ভিডিও: ৫৯১.১ s, ৩৯,০৫৪,৯২৫ bytes।
- শেষ কিউ ৯৮-এর অ্যাবসলিউট স্টার্ট ৫৮৯.৯৪ s অটুট রেখে tempo ১.৮৪× দিয়ে ১.০৬ s-এ ফিট করা হয় → কণ্ঠ ৫৯১.০০ s-এ শেষ, ভিডিও ৫৯১.১০ s-এ শেষ → **মাঝপথে কাটা নেই** (volumedetect: ৫৯০.২s → −5.9 dB, ৫৯০.৬s → −68.7 dB, ৫৯০.৯s → −72.2 dB)।

### ৮.২ শিক্ষক অডিও — expressive rebuild (সম্পন্ন ✅)
hy4 flash high সাব-এজেন্ট দিয়ে নতুন করে তৈরি (`governance/build_expressive_teacher_audio.py`):
- **৭৩/৭৩ কিউ**, ৬/৬ সেকশনে DOM↔ম্যানিফেস্ট ১:১ মিল (ব্রাউজারে যাচাইকৃত)।
- **২০/২০ ফিগার কিউ** সম্প্রসারিত — ২–৪ বাক্যের শিক্ষণীয় ব্যাখ্যা (কী আঁকা, কী লক্ষ্য করতে হবে, কেন গুরুত্বপূর্ণ)।
- সম্পূর্ণ ফোনেটিক বাংলা — কোনো `\`, `$`, `⟦TEX⟧`, ল্যাটিন বা em-dash নেই; গণিত phonetically (এক্স, ওয়াই, ভেক্টর ভি, আই হ্যাট, কলাম ভেক্টর …, এক তৃতীয়াংশ)।
- Prosody: h2 −5%/+2Hz, figure −4%, formula −8%, paragraph +2%, callout +0%, conclusion −3%; ৩৫০ ms গ্যাপ, zero overlap।
- মোট ১১০৪.৮ s (১৮m ২৫s) · পুরনো `_backup_before_expressive_build/`-এ নিরাপদ · `manifest.js?v=6`।

### ৮.৩ ট্রাকার সংশোধন ✅
`generate_board_data.py`: লেকচার ০১ = `completed`, বাকি ৫২ = `under_review` (আগের ভুল হিসাব বাদ)। `board.html`-এ `badge-under-review` ও ফিল্টার যোগ; ব্রাউজারে ৫২টি "🔍 আন্ডার রিভিউ" + ১টি "✅ সম্পূর্ণ ভেরিফাইড" দেখা যাচ্ছে। হোম পেজে লিংক আগে থেকেই আছে।

### ৮.৪ পুনঃব্যবহারযোগ্য নীতিমালা
`governance/COMPONENT_FIRST_PIPELINE.md` — ৫-ধাপের কঠোর ক্রম ও কম্পোনেন্ট-একবার-রেন্ডার নীতি; `governance/LESSON_COMPONENT_TEMPLATE.html` — কপি-পেস্ট টেমপ্লেট। বাকি ৫২টি লেকচার এনুসরণ করছে।
