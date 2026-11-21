# কম্পোনেন্ট-ফার্স্ট প্রোডাকশন পাইপলাইন (v4.0)

> কার্যকর: ২০২৬-১১-২০ · মানদণ্ড: **লেকচার ০১** · সকল ৫৩টি লেকচারের জন্য বাধ্যতামূলক।

## ১. অপরিবর্তনীয় নীতিমালা

1. **সব কনটেন্ট কম্পোনেন্ট-ভিত্তিক** — প্রতিটি লেকচার `governance/LESSON_COMPONENT_TEMPLATE.html` অনুসরণ করবে। Raw HTML ব্লক (`<nav>`, `<figure class=...>`, `<div class=quiz-block>` ইত্যাদি) ব্যবহার নিষিদ্ধ।
2. **কম্পোনেন্ট একবারই রেন্ডার হবে** — প্রতি লেকচারে কম্পোনেন্টগুলো শুধু একবার connect হবে; `setTimeout`-ভিত্তিক/parent `innerHTML` re-parse নিষিদ্ধ (লেকচার ০১-এ এই বাগগুলো ঠিক করা হয়েছে)।
3. **লাইব্রেরি একক উৎস** — `assets/js/lesson_components.js` ও `lesson_components_extended.js`-এ কোনো ডিজাইন/ফাংশনালিটি ঠিক করলে সব লেকচারে অটো প্রযোজ্য হবে। কোনো লেকচারে কম্পোনেন্ট ওভাররাইট/প্যাচ করা যাবে না।
4. **ট্র্যাকার** — `generate_board_data.py`: শুধু লেকচার ০১ `completed`; বাকি সব যেগুলোর অ্যাসেট আছে `under_review`। হোম পেজে `board.html` লিংক থাকবে।
5. **মাইগ্রেশন ক্রম ও পুরনো ফাইল** — সকল লেকচার এক এক করে কম্পোনেন্ট সিস্টেমে আনা হবে। মাইগ্রেশনের সময় পুরনো static HTML `.bak_pre_component` হিসেবে অস্থায়ীভাবে রাখা যেতে পারে, কিন্তু **কম্পোনেন্ট-ভিত্তিক সংস্করণ সম্পূর্ণ যাচাইকৃত ও ওকে হওয়ার পর পুরনো static ফাইল মুছে দিতে হবে** — কারণ ভবিষ্যতে যেকোনো সমস্যা কম্পোনেন্ট-ভিত্তিক সাইটকেই অফিশিয়াল 3Blue1Brown-এর সাথে তুলনা করে ঠিক করা হবে।
6. **অফিশিয়াল উৎস + এক্সট্রা মান** — প্রতিটি লেকচারে (ক) অফিশিয়াল `https://www.3blue1brown.com/lessons/<slug>`-এর **সম্পূর্ণ কনটেন্ট** (zero text dropping, সমস্ত কুইজ/অপশন, সূত্র, উদ্ধৃতি, সেকশন ক্রম) এবং (খ) **লেকচার ০১-এর মতো এক্সট্রা ফিচার ও দরকারি শিক্ষণীয় নোট/ব্যাখ্যা** থাকতে হবে:
   - প্রতিটি ফিগারে ২–৪ বাক্যের শিক্ষণীয় ব্যাখ্যা (কী আঁকা, কী লক্ষ্য করতে হবে, কেন গুরুত্বপূর্ণ),
   - টাইমস্ট্যাম্প বুকমার্ক, TOC, শিক্ষক-অডিও ব্যানার,
   - সঠিক 3B1B কুইজ + সমৃদ্ধ বাংলা ফিডব্যাক,
   - ইন্টারেক্টিভ ক্যানভাস/সিমুলেটর ল্যাব (ফুলস্ক্রিন-সহ), ইনসাইট/কলআউট নোট,
   - এক্সপ্রেসিভ টিচার অডিও (একই মানদণ্ডে)।
   লেকচার ০১ (`/lessons/vectors`), ০২ (`/lessons/span`), ০৩ (`/lessons/linear-transformations`) অফিশিয়াল উৎস যাচাইকৃত।

## ২. প্রতিটি লেকচারের ৫-ধাপ (কঠোর ক্রম)

| ধাপ | কাজ | ওকে হওয়ার শর্ত |
|:---:|:---|:---|
| **১** | কম্পোনেন্ট-ভিত্তিক HTML + কনটেন্ট (টেক্সট, ফিগার ক্যাপশন=শিক্ষণীয় ব্যাখ্যা, কুইজ, ল্যাব) + একই সাথে ভিডিও ডাবিং/রিভিউ | DOM↔manifest ১:১; সব ইমেজ/ভিডিও লোড; ২০টির মতো ফিগার ব্যাখ্যা |
| **২** | স্বয়ংক্রিয় + নিজস্ব চেক (কম্পোনেন্ট, থিমিং, পিল, নেভিগেশন শর্টকাট, সিঙ্ক, ভিডিও দৈর্ঘ্য) | কোনো error নেই; ভিডিও পূর্ণ দৈর্ঘ্য; কথা কাটা/fisisfis নেই |
| **৩** | শুধু তখনই শিক্ষক অডিও (expressive: figure explanation, pronunciation, pause, prosody) | ৭৩+ কিউ, টেক্সট-মিল ১০০%, ব্যাকআপ নিরাপদ |
| **৪** | ফাইনাল পুঙ্খানুপুঙ্খ চেক (�াইভ ব্রাউজার + ffprobe + JSON) | সব ফলাফল রিপোর্টে লেখা |
| **৫** | ট্র্যাকারে `completed` | board_data.json + board.html আপডেট |

**ধাপ ২ শেষ না হলে ধাপ ৩-এ হাত দেওয়া যাবে না।**

## ৩. সাধারণ সমস্যা → সমাধান (লেকচার ০১-এ প্রমাণিত)

| সমস্যা | লাইব্রেরি-স্তরে সমাধান |
|:---|:---|
| ক্যানভাস/টুল থিমিং | `b1b-vector-plane`-এ MutationObserver + scoped IDs |
| কন্ট্রোল পিল ফাংশনালিটি / শর্টকাট | `narration_engine.js` (এক জায়গায়) |
| সিঙ্ক | absolute sample offset + ৩৫০ ms gap, কখনো cumulative নয় |
| ছবির ব্যাখ্যা | figure caption-এ ২–৪ বাক্য শিক্ষণীয় ব্যাখ্যা (expressive audio-তে ২০টি ফিগার) |
| ভিডিও দৈর্ঘ্য | পূর্ণ মূল ভিডিও ডাউনলোড + video stream copy, `-shortest` সাবধানে |
| বারবার রেন্ডার | connectedCallback guard + child nodes move |
| কীবোর্ড নেভিগেশন (Space double-toggle, ↑/↓ ভুল আইটেম, End-এ পিল বন্ধ) | `narration_engine.js`: focus inside-pill check, `_suppressTimeUpdate` around seeks, prev/next-এ একক jump, Home/End/+/− |
| স্টেপার `০৫ / ০৫` ও ভুল prev/next লিংক | `lesson_components.js`-এ `B1B_COURSES` কনফিগ — total/prev/next সব পেজে অটো ডেরাইভ |
| কৃত্রিম "চিত্র প্রদর্শনী" বয়ান | সব expressive builder + fallback engine → প্রাকৃতিক "চিত্রে দেখা যাচ্ছে, …" |
| ভিডিও ডাবিংয়ে দীর্ঘ নীরব pocket (pad-only + timeline stretch) | **`IMPROVED_DUB_FILL_POLICY.md`** — atempo floor ০.৮, script expansion, `median_fill ≥ ০.৭২` |

## ৪. মডিল ব্যবহার নীতি
- `opencode/hy4-flash-free#high` — কনটেন্ট ও ভিডিও এজেন্ট (প্রমাণিত)।
- MiniMax / Kimi / Mistral — প্রয়োজনেমতো; MiniMax-M3.1-Flash OpenCode টুল-স্কিমার সাথে ইনকম্প্যাটিবল (ব্যর্থ), Kimi-তে ক্রেডিট নেই — তাই অগ্রাধিকার hy4 flash high।

## ৫. সমান্তরালতা ও অগ্রগতি
- **একসাথে ২টি লেকচার** নিয়ে কাজ করা হবে; প্রতিটি লেকচারের জন্য ২টি করে এজেন্ট (কনটেন্ট + ভিডিও) = মোট ৪টি এজেন্ট সমান্তরালে।
- ✅ লেকচার ০১ — completed (৭৩/৭৩, expressive audio, ৯:৫১)।
- ✅ লেকচার ০২ — completed (৬৬/৬৬, expressive audio, ৯:৫৮.৭)।
- ✅ লেকচার ০৩ — completed (৩২/৩২, expressive audio, ১০:৫৮)।
- ✅ লেকচার ০৪ — completed (৫২/৫২, expressive audio, ১০:০৩ পূর্ণ দৈর্ঘ্য)।
- ✅ লেকচার ০৫ — completed (৩৮/৩৮, expressive audio, ৪:৪৫)।
- ✅ লেকচার ০৬ — completed (৩৪/৩৪, expressive audio, ১০:০২)।
- ✅ লেকচার ০৭ — completed (৩৩/৩৩, expressive audio, ১২:০৮)।
- ✅ লেকচার ০৮ — completed (২৪/২৪, expressive audio, ৪:২৬)।
- ✅ লেকচার ০৯ — completed (৩২/৩২, expressive audio, ১৪:১১)।
- ✅ লেকচার ১০ — completed (৩৭/৩৭, expressive audio, ৮:৫২)।
- ✅ লেকচার ১১ — completed (২৪/২৪, expressive audio, ১৩:০৯)।
- ✅ লেকচার ১২ — content ✅ ২৫/২৫, video ✅ ১২:১১; expressive audio ⏳।
- ✅ লেকচার ১৩ — content ✅, video ✅ ১২:৫০; expressive audio ⏳।
- ⏳ লেকচার ১৪ — content + video এজেন্ট চলমান (eigenvectors, `PFDu9oVAE-g`)।
- ⏳ লেকচার ১৫ — content + video এজেন্ট চলমান (abstract vector spaces, `TgKwz5b66Lg`) — সিরিজ ফিনালে।
- ⏳ Calculus L01 — content + video এজেন্ট চলমান (`WUvTyaaNkzM`) — LA শেষ হওয়ার অপেক্ষায় নই, পাশাপাশি শুরু।
- **LA বাকি (L13–L15) + Calculus, Neural Networks, DiffEq, Probability, Lockdown Math (আরও ৩৮ লেকচার)** — একই ৫-ধাপ নীতি; সবসময় কমপক্ষে ৪ এজেন্ট চালু।

**ট্র্যাকার:** `governance/completed_lessons.json` — সম্পন্ন লেকচারের ID যোগ করে `generate_board_data.py` চালালেই board_data/board.html আপডেট হয় (বর্তমানে ৯ completed / ৪৪ under_review)।
