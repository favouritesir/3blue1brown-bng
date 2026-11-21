# 🏛️ Dub Studio & BRF Orchestration & Agent Architecture Framework

**Document Version:** 2.0.0 (Ratified EGM Architecture Standard)  
**Status:** Implementation Ready (P0 EGM Remediation Complete)  
**Governing Standard:** `master-voice-dubbing` Skill & EGM Production Directives  
**Date:** 2026-11-05  

---

## 0. Scope & Foundational Governance

### 0.1 Domain Boundaries & Terminology
- **BRF (Bengali Rendering Framework):** Dub Studio-র মূল মাল্টিমোডাল অডিও-ভিজ্যুয়াল লোকালাইজেশন ফ্রেমওয়ার্ক, যা সোর্স কন্টেন্ট (ভিডিও, লেকচার, কার্টুন, একাডেমিক অ্যানিমেশন) গ্রহণ করে স্বয়ংক্রিয়ভাবে স্টুডিও-গ্রেড বাংলা ডাবিং ও মাল্টিমিডিয়া প্ল্যাটফর্মে রূপান্তর করে।
- **Hierarchy of Authority:**
  - এই ফ্রেমওয়ার্কটি সরাসরি `instructions.md` (§5–9) এবং `master-voice-dubbing` স্কিল দ্বারা পরিচালিত। কোনো দ্বন্দ্ব দেখা দিলে গ্লোবাল ইন্সট্রাকশন ও অডিও ইঞ্জিনিয়ারিং স্ট্যান্ডার্ড অগ্রাধিকার পাবে।
- **In-Scope Content Types:**
  1. *একাডেমিক ও লেকচার:* 3Blue1Brown, Khan Academy, MIT OpenCourseWare, লেকচার ও ডার্ক-মোড স্লাইড।
  2. *মাল্টি-ক্যারেক্টার ও ড্রামা:* Steve & Maggie, কিডস অ্যানিমেশন, কার্টুন ও ডায়ালগভিত্তিক নাটক।
- **Out-of-Scope:**
  - ক্লায়েন্ট-সাইড ওয়েব কম্পোনেন্ট ডেভেলপমেন্ট (`<b1b-navbar>`, `<b1b-hero-player>` ইত্যাদি) এই পাইপলাইনের বাইরে স্বাধীনভাবে কাজ করবে।

---

## 1. Core Principles (কোর নীতিমালা)

### ক. লিড অর্কেস্ট্রেটর সর্বদা ব্লকিং-মুক্ত থাকবে (Lead Orchestrator Always Free)
- প্রাইমারি এজেন্ট নিজে কোনো দীর্ঘ বা ভারী কাজ (প্রতিটি লাইন অনুবাদ, ভারী অডিও জেনারেশন, এফএফএমপেক রেন্ডারিং) সরাসরি ব্লকিং অবস্থায় করবে না।
- লিড এজেন্ট কাজগুলোকে সুনির্দিষ্টভাবে বিশ্লেষণ করে নন-ব্লকিং ব্যাকগ্রাউন্ড **সাব-এজেন্ট (Sub-Agents)** স্পন করবে।
- প্রতিটি কাজের প্রকৃতি অনুযায়ী সাব-এজেন্টদের জন্য ডেডিকেটেড মডেল অ্যাসাইন থাকবে।

### খ. নিখুঁত শিক্ষণীয় বাংলা (Zero Machine Translation)
- সাধারণ ট্রান্সলেটর (Google Translate / MyMemory ইত্যাদি) কোনোভাবেই সরাসরি ফাইনাল স্ক্রিপ্টে ব্যবহার করা যাবে না।
- অনুবাদ হতে হবে সাবলীল, প্রাঞ্জল ও প্রাসঙ্গিক বাংলা (Native Pedagogical & Academic Bengali)।
- কোনো কৃত্রিম, আক্ষরিক বা রোবটিক শব্দচয়ন থাকবে না।

### গ. ফোনেটিক সুরক্ষাকবচ (Phonetic Acronym Safeguard)
- ল্যাটিন বর্ণমালা ও সংক্ষিপ্ত রূপগুলো টিটিএস ইঞ্জিনে যাতে বিকৃত না হয়, সেজন্য বাংলায় লিপ্যন্তর বাধ্যতামূলক:
  - `AI` ➔ **`এআই`**, `3D` ➔ **`থ্রিডি`**, `2D` ➔ **`টুডি`**, `API` ➔ **`এপিআই`**, `UI` ➔ **`ইউআই`**
  - `x-অক্ষ` ➔ **`এক্স অক্ষ`**, `y-অক্ষ` ➔ **`ওয়াই অক্ষ`**, `z-অক্ষ` ➔ **`জেড অক্ষ`**
  - $\hat{i}$ ➔ **`আই হ্যাট`**, $\hat{j}$ ➔ **`জে হ্যাট`**, $\hat{k}$ ➔ **`কে হ্যাট`**
  - $dx, dt, df$ ➔ **`ডি এক্স`**, **`ডি টি`**, **`ডি এফ`**

### ঘ. ফোল্ডার ট্যাক্সোনমি ও সংস্করণ সুরক্ষা (Clean Taxonomy & Non-Destructive Versioning)
```text
departments/
├── media_production/
│   └── youtube_channels/
│       └── <channel_name>/
│           └── <topic_or_playlist>/
│               └── <content_slug>/
├── learning_paths/
│   └── stem_mathematics/
│       └── <organization_or_author>/  (e.g., 3blue1brown_courses)
│           └── <course_name>/          (e.g., essence_of_linear_algebra)
│               └── <lesson_name>/
├── research_academic/
│   ├── websites/
│   └── academic_institutions/
├── books_docs/
│   └── publishers_and_authors/
└── rnd_lab/
```
- পূর্ববর্তী কার্যকরী সংস্করণ ধ্বংস বা মুছে ফেলা সম্পূর্ণ নিষিদ্ধ। নতুন সংস্করণগুলো সুনির্দিষ্ট নামের প্রত্যয় (`..._Google_AI_Studio_Dubbed.mp4`, `..._Edge_Dubbed.mp4`) দিয়ে সংরক্ষণ করতে হবে।

---

## 2. সাব-এজেন্ট আর্কিটেকচার ও মডেল নির্বাচন (Sub-Agent Allocation)

```
                    ┌───────────────────────────────┐
                    │       সোর্স ভিডিও / অডিও       │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      সোর্স ইনজেশন ও মেটাডেটা   │
                    └───────┬───────────────┬───────┘
                            │               │
                            ▼               ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│       অডিও স্টেম সেপারেশন       │   │     স্ক্রিপ্ট অ্যাডাপ্টেশন       │
│ (Demucs 2-Stem + Wiener Filter) │   │ (Gemini 1.5 Pro / GPT-4o Class) │
└─────────────────┬───────────────┘   └─────────────┬───────────────────┘
                  │                                 │
                  │ Pristine SFX Bed                │ TimedScript Contract (JSON)
                  │                                 ▼
                  │                   ┌─────────────────────────────────┐
                  │                   │       ভয়েস ইঞ্জিন রাউটার        │
                  │                   │ (Edge-TTS / Gemini Flash TTS)   │
                  │                   └─────────────┬───────────────────┘
                  │                                 │ Continuous Master Chunks
                  │                                 ▼
                  │                   ┌─────────────────────────────────┐
                  │                   │     ডিএসপি স্লাইসিং ও সিঙ্ক      │
                  │                   │  (NVIDIA Mistral Large 4 1T)    │
                  └───────────────┬───┴─────────────┬───────────────────┘
                                  │                 │
                                  ▼                 ▼
                          ┌─────────────────────────────────┐
                          │    অডিও-ভিজ্যুয়াল মাক্সিং ও মাস্টার │
                          │   (EBU R128 -14 LUFS Normalizer)│
                          └─────────────────┬───────────────┘
                                            │ Muxed Video / Master Audio
                                            ▼
                          ┌─────────────────────────────────┐
                          │    স্বয়ংক্রিয় কিউএ ভেরিফিকেশন    │
                          │ (Gemini Multimodal + DSP Gates) │
                          └─────────────────┬───────────────┘
                                            │
                           ┌────────────────┴────────────────┐
                           ▼                                 ▼
                 [PASS: Production Verified]       [FAIL: Escalation Event]
```

### সাব-এজেন্ট ডেডিকেটেড রোলস:
1. **Script Adapter & Cultural Translator:**
   - **মডেল:** Gemini 1.5 Pro / Claude 3.5 Sonnet / GPT-4o
   - **দায়িত্ব:** ভাবানুবাদ, কালচারাল অ্যাডাপ্টেশন, ফোনেটিক সেফগার্ড নিশ্চিতকরণ এবং `TimedScript` আউটপুট।
2. **Dedicated DSP & Separation Engineer:**
   - **মডেল:** NVIDIA Mistral Large 4 1T
   - **দায়িত্ব:** Demucs v4 2-স্টেম নিউরাল সেপারেশন, ওয়েনার ফিল্টারিং, সাইলেন্স ডেলিমিটার ডিটেকশন, সাইডচেইন গেটিং, $\le 20\text{ms}$ ড্রিফট সিঙ্ক এবং `SyncMap` জেনারেশন।
3. **Multimodal QA & Compliance Auditor:**
   - **মডেল:** Gemini 1.5 Pro (Multimodal)
   - **দায়িত্ব:** লিপ-সিঙ্ক ভ্যালিডেশন, লাউডনেস অডিট ($-14\text{ LUFS}$), কোনো ইংলিশ ভয়েস ব্লিড আছে কিনা তা যাচাই এবং `QAReport` তৈরি।

---

## 3. টাইপড ইন্টার-এজেন্ট হ্যান্ডঅফ কন্ট্রাক্টস (JSON Schemas)

### ৩.১ `TimedScript` স্কিমা (Script Adapter ➔ Voice Engine Router)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TimedScript",
  "type": "object",
  "required": ["metadata", "cues"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["source_id", "source_duration_ms", "voice_engine", "character_registry"],
      "properties": {
        "source_id": { "type": "string" },
        "source_duration_ms": { "type": "number", "minimum": 0 },
        "voice_engine": { "type": "string", "enum": ["edge_tts", "gemini_flash_tts"] },
        "character_registry": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "required": ["voice_id", "gender", "pitch", "rate"],
            "properties": {
              "voice_id": { "type": "string" },
              "gender": { "type": "string", "enum": ["male", "female", "neutral"] },
              "pitch": { "type": "string" },
              "rate": { "type": "string" }
            }
          }
        }
      }
    },
    "cues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["cue_id", "character", "start_ms", "end_ms", "text_bn", "phonetic_safeguard_verified"],
        "properties": {
          "cue_id": { "type": "string" },
          "character": { "type": "string" },
          "start_ms": { "type": "number", "minimum": 0 },
          "end_ms": { "type": "number", "minimum": 0 },
          "text_en": { "type": "string" },
          "text_bn": { "type": "string" },
          "phonetic_safeguard_verified": { "type": "boolean" },
          "acting_tags": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

### ৩.২ `SyncMap` স্কিমা (DSP Slicing Engine ➔ Audio Muxer)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SyncMap",
  "type": "object",
  "required": ["job_id", "drift_max_ms", "slices"],
  "properties": {
    "job_id": { "type": "string" },
    "drift_max_ms": { "type": "number", "maximum": 20.0 },
    "slices": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["cue_id", "target_start_ms", "target_end_ms", "actual_duration_ms", "atempo_factor", "audio_path"],
        "properties": {
          "cue_id": { "type": "string" },
          "target_start_ms": { "type": "number" },
          "target_end_ms": { "type": "number" },
          "actual_duration_ms": { "type": "number" },
          "atempo_factor": { "type": "number", "minimum": 0.8, "maximum": 1.25 },
          "crossfade_ms": { "type": "number", "enum": [25.0, 30.0] },
          "audio_path": { "type": "string" }
        }
      }
    }
  }
}
```

### ৩.৩ `QAReport` স্কিমা (Automated QA ➔ Lead Orchestrator)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "QAReport",
  "type": "object",
  "required": ["job_id", "verdict", "metrics", "violations"],
  "properties": {
    "job_id": { "type": "string" },
    "verdict": { "type": "string", "enum": ["PASS", "FAIL", "REQUIRES_HUMAN_REVIEW"] },
    "metrics": {
      "type": "object",
      "required": ["integrated_lufs", "true_peak_dbtp", "max_drift_ms", "vocal_bleed_detected"],
      "properties": {
        "integrated_lufs": { "type": "number", "minimum": -14.5, "maximum": -13.5 },
        "true_peak_dbtp": { "type": "number", "maximum": -1.0 },
        "max_drift_ms": { "type": "number", "maximum": 20.0 },
        "vocal_bleed_detected": { "type": "boolean" },
        "phonetic_transliteration_errors": { "type": "integer", "maximum": 0 }
      }
    },
    "violations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["gate", "severity", "description"],
        "properties": {
          "gate": { "type": "string" },
          "severity": { "type": "string", "enum": ["CRITICAL", "MAJOR", "MINOR"] },
          "description": { "type": "string" },
          "timestamp_ms": { "type": "number" }
        }
      }
    }
  }
}
```

---

## 4. অডিও প্রসেসিং ও ডিএসপি পাইপলাইন স্পেসিফিকেশন

1. **নিউরাল স্টেম সেপারেশন (Demucs v4):**
   - মূল অডিও থেকে ভোকাল ও ব্যাকগ্রাউন্ড মিউজিক/এফএক্স আলাদা করতে Demucs v4 (htdemucs_ft) ব্যবহৃত হবে।
   - শুধুমাত্র ম্যাগনিচিউড ওয়েনার ফিল্টারিং প্রয়োগ হবে, যাতে অরিজিনাল ফেজ ১০০% অবিকৃত থাকে।
   - আউটপুট: 24-bit PCM WAV @ 48kHz, -0.4 dBFS পিক।
2. **ভোকাল ব্লিড প্রতিরোধে হার্ড ডায়ালগ গেটিং (Zero Vocal Bleed):**
   - বাংলা কণ্ঠ চলাকালীন সময়ে মূল ইংরেজি ভোকাল ট্র্যাক পুরোপুরি নিঃশব্দ (0.0 ভলিউম / $-\infty\text{ dB}$) থাকবে।
   - সংলাপের মধ্যবর্তী বিরতি ও ফোলি/সাউন্ড ইফেক্টের সময় অরিজিনাল এসএফএক্স ফুল ভলিউমে ও স্বচ্ছতায় বাজবে।
3. **কন্টিনিউয়াস মাস্টার ব্লক ও অ্যাকোস্টিক সাইলেন্স ডেলিমিটার:**
   - গুগল এআই স্টুডিও ব্যবহারের সময় প্রতিটি লাইনের আলাদা রিকোয়েস্ট নিষিদ্ধ। ৩ থেকে ৫ মিনিটের কন্টিনিউয়াস মাস্টার ব্লকে পাঠাতে হবে।
   - প্রতিটি ডায়ালগের মাঝে সুনির্দিষ্ট অ্যাকোস্টিক ডেলিমিটার (`\n\n... ... ...\n\n`) থাকবে, যা টিটিএসকে ১.০ থেকে ১.৫ সেকেন্ডের সম্পূর্ণ নীরবতা বজায় রাখতে বাধ্য করে।
4. **ডিটারমিনিস্টিক স্লাইসিং ও সিঙ্ক্রোনাইজেশন:**
   - সাইলেন্স ডিটেকশন ($< -50\text{ dBFS}$, সময় $> 800\text{ms}$) ব্যবহার করে মূল ব্লক থেকে ১:১ ডায়ালগ অংশ কেটে নেওয়া হবে।
   - পারসেপচুয়াল সিঙ্ক টলারেন্স: সর্বোচ্চ অডিও ড্রিফট $\le 20\text{ms}$। প্রয়োজনবোধে মৃদু পিচ-সংরক্ষিত `atempo` ($\le 1.25\times$) প্রয়োগ হবে।
   - ট্রানজিশনে ক্লিক বা পপ শব্দ রোধ করতে ২৫ms থেকে ৩০ms রেইজড-কোসাইন ক্রসফেড প্রয়োগ হবে।
5. **মাস্টার লাউডনেস নর্মালাইজেশন:**
   - EBU R128 দুই-পাস লাউডনেস ফিল্টারিং:
     - ইন্টিগ্রেটেড লাউডনেস: $-14.0\text{ LUFS}$ ($\pm 0.5\text{ LUFS}$)
     - ট্রু পিক: $-1.0\text{ dBTP}$
     - লাউডনেস রেঞ্জ (LRA): $\le 11\text{ LU}$

---

## 5. রেসিলিয়েন্সি, এরর হ্যান্ডলিং ও সিআই গেটস

### ৫.১ অটোমেটেড সিআই কোয়ালিটি গেটস (৬টি বাধ্যতামূলক ফিল্টার)
| গেট | যাচাইয়ের মানদণ্ড | ব্যর্থতার ফলাফল |
|:---|:---|:---|
| **Gate 1: Loudness** | Integrated LUFS $[-14.5, -13.5]$, True Peak $\le -1.0\text{ dBTP}$ | রিজেক্ট ও রি-নর্মালাইজ |
| **Gate 2: Drift** | ঠোঁটের নড়াচড়া ও অডিও সিঙ্কের সর্বোচ্চ বিচ্যুতি $\le 20\text{ms}$ | রিজেক্ট ও রি-সিঙ্ক |
| **Gate 3: Bleed** | বাংলা সংলাপে মূল ইংরেজি কণ্ঠের উপস্থিতি $0.0\text{ dB}$ | রিজেক্ট ও রি-গেট |
| **Gate 4: Phonetic** | কোনো কাঁচা ইংরেজি সংক্ষিপ্ত রূপ (`AI`, `3D`, `x-অক্ষ`) না থাকা | রিজেক্ট ও স্ক্রিপ্ট সংশোধন |
| **Gate 5: Gender Lock** | ক্যারেক্টার রেজিস্ট্রির সাথে টিটিএস কণ্ঠের লিঙ্গ ও স্বর সঙ্গতিপূর্ণ থাকা | রিজেক্ট ও রি-সিন্থেসিস |
| **Gate 6: Clean Workspace**| টেম্পোরারি ফাইল স্বয়ংক্রিয়ভাবে মুছে ফেলা ও স্ট্যান্ডার্ড ফোল্ডারে ফাইল সেভ | বিল্ড ফেইল্ড |

### ৫.২ এরর পলিসি ও এস্কেলেশন
- **অটোমেটিক রিট্রাই:** নেটওয়ার্ক টাইমআউট বা কোটা এররে (429/503) এক্সপোনেনশিয়াল ব্যাকঅফ সহ ৩ বার রিট্রাই (১ সে., ৪ সে., ১৬ সে.)।
- **চেকপয়েন্ট ও রিজিউম:** প্রতিটি টাস্কের হ্যাশ (`sha256(source_id + cue_id + script_rev)`) দিয়ে ইন্টারমিডিয়েট ফাইল ক্যাশ থাকবে, ফলে কোনো জব বন্ধ হলেও পূর্ববর্তী কাজ পুনরায় করতে হবে না।
- **ডেড-লেটার এস্কেলেশন:** ৩ বার ব্যর্থ হলে জবটি ডেড-লেটার রেকর্ডে যাবে এবং হিউম্যান অপারেটরের জন্য `EscalationEvent` ট্রিগার করবে।
