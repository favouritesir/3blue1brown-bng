window.TEACHER_AUDIO_MANIFEST = {
  "course": "computer_science",
  "lesson": "lesson_08",
  "voice": "bn-BD-PradeepNeural",
  "mode": "authentic_teacher",
  "sections": {
    "sec-sir": {
      "title": "১. S, I, R — তিনটি ভাগ",
      "audio_file": "sec_01_sec-sir.mp3",
      "total_duration_ms": 32414.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "১. S, I, R — তিনটি ভাগ",
          "start_ms": 0.0,
          "end_ms": 3916.0,
          "duration_ms": 3916.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "মহামারি মডেলে জনসংখ্যাকে তিন ভাগে ভাগ করা হয়—Suspected (S, সংক্রমিত হতে পারে), Infected (I, বর্তমানে অসুস্থ) ও Recovered (R, সেরে গেছে বা মারা গেছে)। সময়ের সাথে এই তিনের অনুপাত বদলাতে থাকে।",
          "start_ms": 4266.0,
          "end_ms": 18266.0,
          "duration_ms": 14000.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "SIR মডেল—তিনটি পুকুরের মতো ভাগ",
          "start_ms": 18616.0,
          "end_ms": 23156.0,
          "duration_ms": 4540.0
        },
        {
          "index": 3,
          "type": "callout",
          "text": "রোগের বিস্তার নির্ভর করে কতজন সংক্রমিত আর কতজন সংবেদনশীল একে অপরের সাথে মিলছে তার ওপর।",
          "start_ms": 23506.0,
          "end_ms": 32414.0,
          "duration_ms": 8908.0
        }
      ]
    },
    "sec-eq": {
      "title": "২. মডেলের সমীকরণ",
      "audio_file": "sec_02_sec-eq.mp3",
      "total_duration_ms": 35254.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "২. মডেলের সমীকরণ",
          "start_ms": 0.0,
          "end_ms": 3448.0,
          "duration_ms": 3448.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "সংক্রমিত হওয়ার হার $S$ ও $I$-র গুণফলের সমানুপাতিক—কারণ বেশি মানুষ মিললে বেশি সংক্রমণ। আবার অসুস্থ মানুষ সেরে যাওয়ার হার $I$-র সমানুপাতিক।",
          "start_ms": 3798.0,
          "end_ms": 16840.0,
          "duration_ms": 13042.0
        },
        {
          "index": 2,
          "type": "formula-box",
          "text": "গাণিতিক সূত্র।",
          "start_ms": 17190.0,
          "end_ms": 20482.0,
          "duration_ms": 3292.0
        },
        {
          "index": 3,
          "type": "figure",
          "text": "SIR বক্ররেখা—সময়ের সাথে তিন ভাগের পরিবর্তন",
          "start_ms": 20832.0,
          "end_ms": 26386.0,
          "duration_ms": 5554.0
        },
        {
          "index": 4,
          "type": "p",
          "text": "এই সরল সমীকরণগুলোই পুরো মহামারির গতিপথ প্রভাবিত করে—ধন্যবাদ কম্পিউটার সিমুলেশনের।",
          "start_ms": 26736.0,
          "end_ms": 35254.0,
          "duration_ms": 8518.0
        }
      ]
    },
    "sec-r0": {
      "title": "৩. $R_0$ — মূল সংখ্যা",
      "audio_file": "sec_03_sec-r0.mp3",
      "total_duration_ms": 33850.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "৩. $R_0$ — মূল সংখ্যা",
          "start_ms": 0.0,
          "end_ms": 3838.0,
          "duration_ms": 3838.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "একজন অসুস্থ মানুষ গড়ে যতজনকে সংক্রমিত করে, তা হলো $R_0$। যদি $R_0>1$, মহামারি ছড়ায়; যদি $R_0<1$, সেটি শেষ হয়ে যায়। সাধারণত $R_0=\\beta/\\gamma$।",
          "start_ms": 4188.0,
          "end_ms": 17854.0,
          "duration_ms": 13666.0
        },
        {
          "index": 2,
          "type": "formula-box",
          "text": "গাণিতিক সূত্র।",
          "start_ms": 18204.0,
          "end_ms": 21496.0,
          "duration_ms": 3292.0
        },
        {
          "index": 3,
          "type": "figure",
          "text": "$R_0$ বেশি হলে সংক্রমণ বক্ররেখা খাড়া হয়",
          "start_ms": 21846.0,
          "end_ms": 27244.0,
          "duration_ms": 5398.0
        },
        {
          "index": 4,
          "type": "chapter-quote",
          "text": "একটি ছোট্ট সংখ্যা—$R_0$—পুরো নীতির দিক নির্ধারণ করে।",
          "start_ms": 27594.0,
          "end_ms": 33850.0,
          "duration_ms": 6256.0
        }
      ]
    },
    "sec-sim": {
      "title": "৪. সিমুলেশন ও অনিশ্চয়তা",
      "audio_file": "sec_04_sec-sim.mp3",
      "total_duration_ms": 31456.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "৪. সিমুলেশন ও অনিশ্চয়তা",
          "start_ms": 0.0,
          "end_ms": 4072.0,
          "duration_ms": 4072.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "কম্পিউটারে আমরা লাখো ''এজেন্ট'' তৈরি করে তাদের মাঝে রোগ ছড়িয়ে দিতে পারি। প্রতিটি সিমুলেশনে ফল কিছুটা আলাদা হয়—এতে বোঝা যায় ভবিষ্যৎ কতটা অনিশ্চিত।",
          "start_ms": 4422.0,
          "end_ms": 18244.0,
          "duration_ms": 13822.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "এজেন্ট-ভিত্তিক মহামারি সিমুলেশন",
          "start_ms": 18594.0,
          "end_ms": 23212.0,
          "duration_ms": 4618.0
        },
        {
          "index": 3,
          "type": "callout",
          "text": "মডেল ভবিষ্যৎ ''ভবিষ্যদ্বাণী'' করে না—এটি দেখায় কোন পরিস্থিতি কতটা সম্ভব।",
          "start_ms": 23562.0,
          "end_ms": 31456.0,
          "duration_ms": 7894.0
        }
      ]
    },
    "sec-flatten": {
      "title": "৫. বক্ররেখা চ্যাপ্টা করা",
      "audio_file": "sec_05_sec-flatten.mp3",
      "total_duration_ms": 35300.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "৫. বক্ররেখা চ্যাপ্টা করা",
          "start_ms": 0.0,
          "end_ms": 4072.0,
          "duration_ms": 4072.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "দূরত্ব, মাস্ক বা টিকা কমালে $\\beta$ কমে—ফলে $R_0$ কমে। সংক্রমিতদের সংখ্যার শীর্ষ নিচে নামে ও সময়ে ছড়িয়ে পড়ে। এটিই ''flatten the curve''—হাসপাতালের চাপ কমায়।",
          "start_ms": 4422.0,
          "end_ms": 18422.0,
          "duration_ms": 14000.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "খাড়া বনাম চ্যাপ্টা সংক্রমণ বক্ররেখা",
          "start_ms": 18772.0,
          "end_ms": 23780.0,
          "duration_ms": 5008.0
        },
        {
          "index": 3,
          "type": "p",
          "text": "আচরণের ছোট পরিবর্তন মডেলে বড় প্রভাব ফেলে—এই শিক্ষা কেবল মহামারি নয়, অনেক সামাজিক ব্যবস্থার ক্ষেত্রেও প্রয়োজনীয়।",
          "start_ms": 24130.0,
          "end_ms": 35300.0,
          "duration_ms": 11170.0
        }
      ]
    }
  }
};
