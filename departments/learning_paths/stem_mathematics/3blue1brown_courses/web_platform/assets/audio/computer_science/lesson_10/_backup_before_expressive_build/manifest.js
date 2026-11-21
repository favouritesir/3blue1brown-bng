window.TEACHER_AUDIO_MANIFEST = {
  "course": "computer_science",
  "lesson": "lesson_10",
  "voice": "bn-BD-PradeepNeural",
  "mode": "authentic_teacher",
  "sections": {
    "sec-xor": {
      "title": "১. সবকিছু XOR",
      "audio_file": "sec_01_sec-xor.mp3",
      "total_duration_ms": 34786.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "১. সবকিছু XOR",
          "start_ms": 0.0,
          "end_ms": 3214.0,
          "duration_ms": 3214.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "প্যারিটি হিসাব আসলে XOR-এর খেলা। একাধিক বিটের XOR তখনই ১ হয় যখন ১-এর সংখ্যা বিজোড় হয়। তাই প্যারিটি বিটগুলোকে কয়েকটি XOR হিসেবে লেখা যায়।",
          "start_ms": 3564.0,
          "end_ms": 16762.0,
          "duration_ms": 13198.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "XOR-এর সত্যের সারণি",
          "start_ms": 17112.0,
          "end_ms": 20794.0,
          "duration_ms": 3682.0
        },
        {
          "index": 3,
          "type": "formula-box",
          "text": "গাণিতিক সূত্র।",
          "start_ms": 21144.0,
          "end_ms": 24436.0,
          "duration_ms": 3292.0
        },
        {
          "index": 4,
          "type": "p",
          "text": "কোড তৈরি ও যাচাই—দুটোই এখন কেবল XOR-এর মাধ্যমে করা যায়। কম্পিউটারের জন্য এটি অত্যন্ত সস্তা ও দ্রুত।",
          "start_ms": 24786.0,
          "end_ms": 34786.0,
          "duration_ms": 10000.0
        }
      ]
    },
    "sec-matrix": {
      "title": "২. প্যারিটি-চেক ম্যাট্রিক্স",
      "audio_file": "sec_02_sec-matrix.mp3",
      "total_duration_ms": 34552.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "২. প্যারিটি-চেক ম্যাট্রিক্স",
          "start_ms": 0.0,
          "end_ms": 4306.0,
          "duration_ms": 4306.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "তিনটি প্যারিটি সমীকরণকে একটিমাত্র ম্যাট্রিক্স $H$ দিয়ে লেখা যায়। সঠিক কোডওয়ার্ড $c$-র ক্ষেত্রে $Hc^{T}=0$ হয়—এটি হলো কোডের ''পরীক্ষা''।",
          "start_ms": 4656.0,
          "end_ms": 17698.0,
          "duration_ms": 13042.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "প্যারিটি-চেক ম্যাট্রিক্স $H$",
          "start_ms": 18048.0,
          "end_ms": 22432.0,
          "duration_ms": 4384.0
        },
        {
          "index": 3,
          "type": "formula-box",
          "text": "গাণিতিক সূত্র।",
          "start_ms": 22782.0,
          "end_ms": 26074.0,
          "duration_ms": 3292.0
        },
        {
          "index": 4,
          "type": "callout",
          "text": "$H$-এর কলামগুলোকে ১ থেকে ৭ পর্যন্ত বাইনারি সংখ্যা হিসেবে সাজালে ম্যাজিক ঘটে।",
          "start_ms": 26424.0,
          "end_ms": 34552.0,
          "duration_ms": 8128.0
        }
      ]
    },
    "sec-syndrome": {
      "title": "৩. সিনড্রোম = ভুলের ঠিকানা",
      "audio_file": "sec_03_sec-syndrome.mp3",
      "total_duration_ms": 36446.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "৩. সিনড্রোম = ভুলের ঠিকানা",
          "start_ms": 0.0,
          "end_ms": 4228.0,
          "duration_ms": 4228.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "প্রাপ্ত শব্দ $r=c+e$ হলে $Hr^{T}=He^{T}$—অর্থাৎ সিনড্রোম নির্ভর করে শুধু ভুলের ওপর। ত্রুটি যদি $i$-তম বিটে হয়, সিনড্রোম হয় $H$-এর $i$-তম কলাম, যা ঠিক $i$-র বাইনারি রূপ।",
          "start_ms": 4578.0,
          "end_ms": 18578.0,
          "duration_ms": 14000.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "সিনড্রোম সরাসরি বাইনারিতে অবস্থান দিচ্ছে",
          "start_ms": 18928.0,
          "end_ms": 24248.0,
          "duration_ms": 5320.0
        },
        {
          "index": 3,
          "type": "formula-box",
          "text": "গাণিতিক সূত্র।",
          "start_ms": 24598.0,
          "end_ms": 27890.0,
          "duration_ms": 3292.0
        },
        {
          "index": 4,
          "type": "chapter-quote",
          "text": "সুন্দর মডেল এমনভাবে সাজানো হয় যেন উত্তরটি নিজেই প্রশ্নের ভেতরে লুকিয়ে থাকে।",
          "start_ms": 28240.0,
          "end_ms": 36446.0,
          "duration_ms": 8206.0
        }
      ]
    },
    "sec-general": {
      "title": "৪. সাধারণীকরণ $(2^r-1,\\,2^r-1-r)$",
      "audio_file": "sec_04_sec-general.mp3",
      "total_duration_ms": 37148.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "৪. সাধারণীকরণ $(2^r-1,\\,2^r-1-r)$",
          "start_ms": 0.0,
          "end_ms": 4774.0,
          "duration_ms": 4774.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "একই কৌশল যেকোনো $r$-এর জন্য কাজ করে—$2^r-1$ বিটের ব্লকে $r$টি প্যারিটি যোগ করে মাত্র একটি বিটের ভুল সংশোধন করা যায়। $r=3$ দিলে আমাদের পরিচিত (7,4) কোড পাই।",
          "start_ms": 5124.0,
          "end_ms": 19124.0,
          "duration_ms": 14000.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "বিভিন্ন $r$-এর জন্য হ্যামিং কোড",
          "start_ms": 19474.0,
          "end_ms": 24092.0,
          "duration_ms": 4618.0
        },
        {
          "index": 3,
          "type": "formula-box",
          "text": "গাণিতিক সূত্র।",
          "start_ms": 24442.0,
          "end_ms": 27734.0,
          "duration_ms": 3292.0
        },
        {
          "index": 4,
          "type": "p",
          "text": "বিটের সংখ্যা বাড়লে ''ওভারহেড'' ($r/n$) কমে যায়—ফলে দীর্ঘ বার্তায় এই কোড আরও দক্ষ হয়।",
          "start_ms": 28084.0,
          "end_ms": 37148.0,
          "duration_ms": 9064.0
        }
      ]
    },
    "sec-elegance": {
      "title": "৫. কেন এত সুন্দর",
      "audio_file": "sec_05_sec-elegance.mp3",
      "total_duration_ms": 29194.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "৫. কেন এত সুন্দর",
          "start_ms": 0.0,
          "end_ms": 3448.0,
          "duration_ms": 3448.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "ভুলের অবস্থান আর তার বাইনারি কোড—এই দুটিকে একই করে দেওয়াই হ্যামিং কোডের শ্রেষ্ঠত্ব। কোনো জটিল অনুসন্ধান নেই; একটি ম্যাট্রিক্স গুণেই উত্তর চলে আসে।",
          "start_ms": 3798.0,
          "end_ms": 17464.0,
          "duration_ms": 13666.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "গণিতের সৌন্দর্য—সরলতা ও দক্ষতা",
          "start_ms": 17814.0,
          "end_ms": 22354.0,
          "duration_ms": 4540.0
        },
        {
          "index": 3,
          "type": "callout",
          "text": "সঠিক কাঠামো বাছাই করলে জটিল সমস্যাও সরল গণিতে রূপ নেয়।",
          "start_ms": 22704.0,
          "end_ms": 29194.0,
          "duration_ms": 6490.0
        }
      ]
    }
  }
};
