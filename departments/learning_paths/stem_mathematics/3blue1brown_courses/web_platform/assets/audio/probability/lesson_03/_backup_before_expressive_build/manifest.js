window.TEACHER_AUDIO_MANIFEST = {
  "course": "probability",
  "lesson": "lesson_03",
  "voice": "bn-BD-PradeepNeural",
  "mode": "authentic_teacher",
  "sections": {
    "sec-bernoulli-intro": {
      "title": "বার্নৌলি ট্রায়াল: সাফল্যের দ্বিমুখী ভিত্তি",
      "audio_file": "sec-bernoulli-intro.mp3",
      "total_duration_ms": 26302.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "বার্নৌলি ট্রায়াল: সাফল্যের দ্বিমুখী ভিত্তি",
          "start_ms": 0.0,
          "end_ms": 3408.0,
          "duration_ms": 3408.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "বার্নৌলি ট্রায়াল হলো দ্বিমুখী ফলাফলের ক্ষুদ্রতম অবিভাজ্য গাণিতিক একক।",
          "start_ms": 3758.0,
          "end_ms": 8630.0,
          "duration_ms": 4872.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "সাফল্যের সম্ভাবনা p এবং ব্যর্থতার সম্ভাবনা 1 p এর যোগফল সর্বদা ১.০।",
          "start_ms": 8980.0,
          "end_ms": 14716.0,
          "duration_ms": 5736.0
        },
        {
          "index": 3,
          "type": "p",
          "text": "একাধিক স্বাধীন বার্নৌলি ট্রায়ালের সমন্বয়ে দ্বিপদী বিন্যাস গঠিত হয়।",
          "start_ms": 15066.0,
          "end_ms": 19722.0,
          "duration_ms": 4656.0
        },
        {
          "index": 4,
          "type": "formula-box",
          "text": "একক বার্নৌলি ট্রায়াল সম্ভাবনা: P(X = 1) = p, \\qquad P(X = 0) = 1 p",
          "start_ms": 20072.0,
          "end_ms": 25952.0,
          "duration_ms": 5880.0
        }
      ]
    },
    "sec-probability-tree": {
      "title": "সম্ভাব্যতার পথজালিকা ও বৃক্ষচিত্র (Probability Tree)",
      "audio_file": "sec-probability-tree.mp3",
      "total_duration_ms": 38004.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "সম্ভাব্যতার পথজালিকা ও বৃক্ষচিত্র (Probability Tree)",
          "start_ms": 0.0,
          "end_ms": 4296.0,
          "duration_ms": 4296.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "প্রতিটি ট্রায়াল সম্ভাবনা বৃক্ষকে দ্বিগুণ করে তোলে, ফলে n ট্রায়ালে 2^n পথ তৈরি হয়।",
          "start_ms": 4646.0,
          "end_ms": 10142.0,
          "duration_ms": 5496.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "একটি নির্দিষ্ট পথ নির্দেশ করতে kটি সাফল্য এবং n kটি ব্যর্থতার সম্ভাবনা সরাসরি গুণ হয়।",
          "start_ms": 10492.0,
          "end_ms": 16516.0,
          "duration_ms": 6024.0
        },
        {
          "index": 3,
          "type": "p",
          "text": "মোট সম্ভাব্যতা পরিমাপের জন্য আমাদের জানতে হবে: ঠিক কতটি ভিন্ন পথ একই সংখ্যক সাফল্যে পৌঁছায়।",
          "start_ms": 16866.0,
          "end_ms": 23586.0,
          "duration_ms": 6720.0
        },
        {
          "index": 4,
          "type": "formula-box",
          "text": "সমগ্র সম্ভাব্য পথের সংখ্যা: \\text{মোট পথ} = 2^n \\qquad (\\text{নিরপেক্ষ মুদ্রার জন্য})",
          "start_ms": 23936.0,
          "end_ms": 30776.0,
          "duration_ms": 6840.0
        },
        {
          "index": 5,
          "type": "formula-box",
          "text": "যেকোনো একটি সুনির্দিষ্ট পথের সম্ভাবনা: P(\\text{Specific Path}) = p^k (1 p)^{n k}",
          "start_ms": 31126.0,
          "end_ms": 37654.0,
          "duration_ms": 6528.0
        }
      ]
    },
    "sec-combinatorics-paths": {
      "title": "কম্বিনেটোরিক্স: পথ গণনার জ্যামিতি ও n Choose k",
      "audio_file": "sec-combinatorics-paths.mp3",
      "total_duration_ms": 43620.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "কম্বিনেটোরিক্স: পথ গণনার জ্যামিতি ও n Choose k",
          "start_ms": 0.0,
          "end_ms": 4032.0,
          "duration_ms": 4032.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "দ্বিপদী সহগ \\binom{n}{k} মূলত একই সংখ্যক সাফল্যে পৌঁছানোর সমান্তরাল পথের সংখ্যা গুনে দেয়।",
          "start_ms": 4382.0,
          "end_ms": 11150.0,
          "duration_ms": 6768.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "ফ্যাক্টোরিয়াল অনুপাত n! / (k!(n k)!) অপ্রয়োজনীয় অভ্যন্তরীণ ক্রমের দ্বৈত গণনা বাতিল করে।",
          "start_ms": 11500.0,
          "end_ms": 18484.0,
          "duration_ms": 6984.0
        },
        {
          "index": 3,
          "type": "p",
          "text": "প্রতিটি পথ সমান সম্ভাবনাময় হওয়ায় মোট পথকে একক পথের সম্ভাবনা দিয়ে গুণ করলেই কাঙ্ক্ষিত উত্তর পাওয়া যায়।",
          "start_ms": 18834.0,
          "end_ms": 25650.0,
          "duration_ms": 6816.0
        },
        {
          "index": 4,
          "type": "formula-box",
          "text": "দ্বিপদী সহগ (Binomial Coefficient): \\binom{n}{k} = \\frac{n!}{k!(n k)!}",
          "start_ms": 26000.0,
          "end_ms": 32456.0,
          "duration_ms": 6456.0
        },
        {
          "index": 5,
          "type": "formula-box",
          "text": "৩ টসে ২ হেডের সমাবেশ: \\binom{3}{2} = \\frac{3!}{2! \\cdot 1!} = \\frac{6}{2 \\cdot 1} = 3",
          "start_ms": 32806.0,
          "end_ms": 43270.0,
          "duration_ms": 10464.0
        }
      ]
    },
    "sec-pascals-triangle": {
      "title": "প্যাসকেলের ত্রিভুজ: প্রতিটি সংখ্যার পেছনের সম্ভাব্যতা",
      "audio_file": "sec-pascals-triangle.mp3",
      "total_duration_ms": 36924.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "প্যাসকেলের ত্রিভুজ: প্রতিটি সংখ্যার পেছনের সম্ভাব্যতা",
          "start_ms": 0.0,
          "end_ms": 4152.0,
          "duration_ms": 4152.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "প্যাসকেলের ত্রিভুজের প্রতিটি সংখ্যা হলো একাধিক দ্বিমুখী পথ একত্রিত হওয়ার প্রত্যক্ষ ফল।",
          "start_ms": 4502.0,
          "end_ms": 10334.0,
          "duration_ms": 5832.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "যেকোনো সারির সংখ্যাগুলোর যোগফল 2^n, যা নিরপেক্ষ মুদ্রার মোট স্যাম্পল স্পেসের সমান।",
          "start_ms": 10684.0,
          "end_ms": 16588.0,
          "duration_ms": 5904.0
        },
        {
          "index": 3,
          "type": "p",
          "text": "ত্রিভুজটির অনুভূমিক প্রোফাইল n বাড়ার সাথে সাথে একটি মসৃণ ঘণ্টার আকৃতি ধারণ করে।",
          "start_ms": 16938.0,
          "end_ms": 22458.0,
          "duration_ms": 5520.0
        },
        {
          "index": 4,
          "type": "formula-box",
          "text": "প্যাসকেলের পুনরাবৃত্তিমূলক সম্পর্ক (Pascal's Identity): \\binom{n}{k} = \\binom{n 1}{k 1} + \\binom{n 1}{k}",
          "start_ms": 22808.0,
          "end_ms": 31016.0,
          "duration_ms": 8208.0
        },
        {
          "index": 5,
          "type": "formula-box",
          "text": "সারির মোট উপাদান যোগফল: \\sum_{k=0}^{n} \\binom{n}{k} = 2^n",
          "start_ms": 31366.0,
          "end_ms": 36574.0,
          "duration_ms": 5208.0
        }
      ]
    },
    "sec-binomial-pmf": {
      "title": "দ্বিপদী সম্ভাব্যতা ভর ফাংশন (Binomial PMF)",
      "audio_file": "sec-binomial-pmf.mp3",
      "total_duration_ms": 43154.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "দ্বিপদী সম্ভাব্যতা ভর ফাংশন (Binomial পিএমএফ)",
          "start_ms": 0.0,
          "end_ms": 3936.0,
          "duration_ms": 3936.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "দ্বিপদী বিন্যাস মূলত পথের সংখ্যা এবং একক পথের সম্ভাবনার গুণফল।",
          "start_ms": 4286.0,
          "end_ms": 9086.0,
          "duration_ms": 4800.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "দ্বিপদী গড়ের মান n p, যা সাধারণ কাণ্ডজ্ঞানের সাথে সরাসরি মিলে যায়।",
          "start_ms": 9436.0,
          "end_ms": 14500.0,
          "duration_ms": 5064.0
        },
        {
          "index": 3,
          "type": "p",
          "text": "পরিমিত ব্যবধান \\sigma = \\sqrt{n p (1 p)} দ্বারা নির্ধারিত হয় চূড়াটি কতটা চওড়া হবে।",
          "start_ms": 14850.0,
          "end_ms": 20994.0,
          "duration_ms": 6144.0
        },
        {
          "index": 4,
          "type": "formula-box",
          "text": "দ্বিপদী সম্ভাব্যতা ভর ফাংশন (Binomial পিএমএফ): P(X = k) = \\binom{n}{k} p^k (1 p)^{n k}, \\qquad k \\in \\{0, 1, 2, \\dots, n\\}",
          "start_ms": 21344.0,
          "end_ms": 31808.0,
          "duration_ms": 10464.0
        },
        {
          "index": 5,
          "type": "formula-box",
          "text": "গাণিতিক প্রত্যাশা বা গড় (Mean): EX = \\mu = n \\cdot p",
          "start_ms": 32158.0,
          "end_ms": 36118.0,
          "duration_ms": 3960.0
        },
        {
          "index": 6,
          "type": "formula-box",
          "text": "ভেদাঙ্ক বা ভ্যারিয়্যান্স (Variance): \\text{Var}(X) = \\sigma^2 = n \\cdot p \\cdot (1 p)",
          "start_ms": 36468.0,
          "end_ms": 42804.0,
          "duration_ms": 6336.0
        }
      ]
    },
    "sec-galton-board": {
      "title": "গ্যালটন বোর্ড: পিন থেকে জন্ম নেওয়া ঘণ্টা আকৃতির কার্ভ",
      "audio_file": "sec-galton-board.mp3",
      "total_duration_ms": 48156.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "গ্যালটন বোর্ড: পিন থেকে জন্ম নেওয়া ঘণ্টা আকৃতির কার্ভ",
          "start_ms": 0.0,
          "end_ms": 4200.0,
          "duration_ms": 4200.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "গ্যালটন বোর্ডে প্রতিটি পিনের সংঘর্ষ একটি স্বাধীন বার্নৌলি ট্রায়াল হিসেবে কাজ করে।",
          "start_ms": 4550.0,
          "end_ms": 9926.0,
          "duration_ms": 5376.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "নিচের খোপে মার্বেলগুলোর উচ্চতা সরাসরি প্যাসকেলের ত্রিভুজের দ্বিপদী সহগ প্রদর্শন করে।",
          "start_ms": 10276.0,
          "end_ms": 16180.0,
          "duration_ms": 5904.0
        },
        {
          "index": 3,
          "type": "p",
          "text": "এই পরীক্ষাটি পরবর্তী অধ্যায় ০৪ ও ০৬ এর সেন্ট্রাল লিমিট থিওরেম এবং নরমাল কার্ভের প্রত্যক্ষ ভিত্তিপ্রস্তর স্থাপন করে।",
          "start_ms": 16530.0,
          "end_ms": 24906.0,
          "duration_ms": 8376.0
        },
        {
          "index": 4,
          "type": "formula-box",
          "text": "গ্যালটন বোর্ডের পিন সংঘর্ষ সম্ভাবনা: P(\\text{ডানে}) = p = 0.5, \\qquad P(\\text{বাঁয়ে}) = 1 p = 0.5",
          "start_ms": 25256.0,
          "end_ms": 34544.0,
          "duration_ms": 9288.0
        },
        {
          "index": 5,
          "type": "formula-box",
          "text": "ডি মইভ্র লাপ্লাস উপপাদ্য (আসন্নায়ন): \\lim_{n \\to \\infty} \\binom{n}{k} p^k (1 p)^{n k} \\approx \\frac{1}{\\sqrt{2\\pi n p(1 p)}} e^{ \\frac{(k np)^2}{2np(1 p)}}",
          "start_ms": 34894.0,
          "end_ms": 47806.0,
          "duration_ms": 12912.0
        }
      ]
    },
    "sec-simulator": {
      "title": "ইন্টারেক্টিভ গ্যালটন ও দ্বিপদী বিন্যাস ল্যাব",
      "audio_file": "sec-simulator.mp3",
      "total_duration_ms": 15978.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "ইন্টারেক্টিভ গ্যালটন ও দ্বিপদী বিন্যাস ল্যাব",
          "start_ms": 0.0,
          "end_ms": 3312.0,
          "duration_ms": 3312.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "ট্রায়াল সংখ্যা n যত বাড়ে, দ্বিপদী স্তম্ভগুলো তত ঘন ও সূক্ষ্ম হয়ে মসৃণ কার্ভের আকার নেয়।",
          "start_ms": 3662.0,
          "end_ms": 9758.0,
          "duration_ms": 6096.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "গড় মান n p এর অবস্থানই নির্ধারণ করে কার্ভের সর্বোচ্চ চূড়া কোথায় অবস্থিত হবে।",
          "start_ms": 10108.0,
          "end_ms": 15628.0,
          "duration_ms": 5520.0
        }
      ]
    },
    "sec-quizzes": {
      "title": "ধারণা যাচাই ও ৩টি KaTeX কুইজ",
      "audio_file": "sec-quizzes.mp3",
      "total_duration_ms": 3566.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "ধারণা যাচাই ও ৩টি KaTeX কুইজ",
          "start_ms": 0.0,
          "end_ms": 3216.0,
          "duration_ms": 3216.0
        }
      ]
    }
  }
};
