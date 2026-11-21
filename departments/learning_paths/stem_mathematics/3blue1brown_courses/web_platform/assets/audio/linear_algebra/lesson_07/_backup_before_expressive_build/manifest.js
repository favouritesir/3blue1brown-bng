window.TEACHER_AUDIO_MANIFEST = {
  "course": "linear_algebra",
  "lesson": "lesson_07",
  "voice": "bn-BD-PradeepNeural",
  "mode": "authentic_teacher",
  "sections": {
    "sec_01_linear_systems": {
      "title": "জ্যামিতিক দৃষ্টিকোণ থেকে লিনিয়ার সমীকরণ জোট",
      "audio_file": "sec_01_linear_systems.mp3",
      "cues_file": "sec_01_linear_systems_cues.json",
      "total_duration_ms": 101600.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "প্রথম পরিচ্ছেদ: জ্যামিতিক দৃষ্টিকোণ থেকে লিনিয়ার সমীকরণ জোট।",
          "en": "Chapter 1: Linear Systems from a Geometric Perspective.",
          "formula": null,
          "duration_ms": 4200.0,
          "start_ms": 0.0,
          "end_ms": 4200.0
        },
        {
          "index": 1,
          "type": "chapter-quote",
          "text": "গণিতবিদদের মতে: সমীকরণ সমাধান কেবল প্রতীকের শুকনো কাটাকাটি নয়; এটি হলো স্থানকে তার আদি অবস্থানে দেখার এক দূরদর্শী শিল্প।",
          "en": "Solving systems of equations is not mere algebraic symbol manipulation; it is the art of seeing space before it was transformed.",
          "formula": "A\\vec{x} = \\vec{v}",
          "duration_ms": 11500.0,
          "start_ms": 4550.0,
          "end_ms": 16050.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "শিক্ষার্থী বন্ধুরা, লিনিয়ার অ্যালজেব্রা কেন বিজ্ঞান ও প্রযুক্তির প্রতিটি শাখায় এত ব্যাপক ব্যবহৃত হয়? তার অন্যতম প্রধান কারণ হলো লিনিয়ার সমীকরণ জোট সমাধানের অভূতপূর্ব সক্ষমতা।",
          "en": "Why is linear algebra so ubiquitously applied across science and engineering? One of the foremost reasons is its unmatched power in solving systems of linear equations.",
          "formula": null,
          "duration_ms": 14200.0,
          "start_ms": 16400.0,
          "end_ms": 30600.0
        },
        {
          "index": 3,
          "type": "p",
          "text": "স্কুল-কলেজে আমরা একগাদা অজানা চলক নিয়ে একাধিক সমীকরণ সমাধানের নিয়ম শিখেছি। যেমন: টু এক্স যোগ টু ওয়াই সমান মাইনাস ফোর, এবং এক্স যোগ থ্রি ওয়াই সমান মাইনাস ওয়ান।",
          "en": "In traditional algebra, we learn procedures to solve multiple equations with unknown variables, such as 2x + 2y = -4 and x + 3y = -1.",
          "formula": "\\begin{cases} 2x + 2y = -4 \\\\ x + 3y = -1 \\end{cases}",
          "duration_ms": 13800.0,
          "start_ms": 30950.0,
          "end_ms": 44750.0
        },
        {
          "index": 4,
          "type": "formula-box",
          "text": "ম্যাট্রিক্সের চমৎকার নিয়মে এই সমীকরণগুলোকে একটি একক ভেক্টর সম্পর্কে সাজানো যায়: ম্যাট্রিক্স এ গুণ ভেক্টর এক্স সমান ভেক্টর ভি। এখানে এ হলো সহগ ম্যাট্রিক্স, এক্স হলো অজানা ভেক্টর, এবং ভি হলো পরিচিত ফলাফল ভেক্টর।",
          "en": "Using matrix multiplication, these equations consolidate into a single elegant expression: A times vector x equals vector v, where A is the coefficient matrix, x is the unknown vector, and v is the target vector.",
          "formula": "\\begin{bmatrix} 2 & 2 \\\\ 1 & 3 \\end{bmatrix} \\begin{bmatrix} x \\\\ y \\end{bmatrix} = \\begin{bmatrix} -4 \\\\ -1 \\end{bmatrix}",
          "duration_ms": 18500.0,
          "start_ms": 45100.0,
          "end_ms": 63600.0
        },
        {
          "index": 5,
          "type": "figure",
          "text": "পাশের চিত্রে লক্ষ্য করুন: আমরা যখন এ গুণ ভেক্টর এক্স সমান ভি লিখি, জ্যামিতিকভাবে এর অর্থ হলো ম্যাট্রিক্স এ স্থানকে একটি সুনির্দিষ্ট উপায়ে রূপান্তরিত করছে।",
          "en": "Looking at the visual diagram, writing A times vector x equals v geometrically means that matrix A acts as a linear transformation warping the space.",
          "formula": null,
          "duration_ms": 11200.0,
          "start_ms": 63950.0,
          "end_ms": 75150.0
        },
        {
          "index": 6,
          "type": "insight-box",
          "text": "সুতরাং সমীকরণটি সমাধান করার আসল জ্যামিতিক প্রশ্নটি হলো: রূপান্তরের পূর্বে কোন ভেক্টর এক্সটি ঠিক এমন স্থানে ছিল, যা এ রূপান্তরের পর হুবহু ভেক্টর ভি-এর ওপর গিয়ে পড়েছে?",
          "en": "Therefore, the true geometric problem is: which vector x, before the transformation was applied, landed directly on vector v after the transformation?",
          "formula": "\\text{Question: Which } \\vec{x} \\text{ lands on } \\vec{v}?",
          "duration_ms": 14600.0,
          "start_ms": 75500.0,
          "end_ms": 90100.0
        },
        {
          "index": 7,
          "type": "p",
          "text": "এই প্রশ্নটির উত্তর নির্ভর করে রূপান্তর এ স্থানটিকে কীভাবে পরিচালিত করেছে—স্থানটি কি পূর্ণ মাত্রায় বিস্তৃত আছে, নাকি চ্যাপ্টা হয়ে তার মাত্রা হারিয়ে ফেলেছে?",
          "en": "The answer to this question depends fundamentally on what transformation A does to space—does it preserve full dimensions, or squish space into a lower dimension?",
          "formula": null,
          "duration_ms": 10800.0,
          "start_ms": 90450.0,
          "end_ms": 101250.0
        }
      ]
    },
    "sec_02_inverse_matrices": {
      "title": "বিপরীত ম্যাট্রিক্স: রূপান্তরকে পূর্বাবস্থায় ফিরিয়ে আনা",
      "audio_file": "sec_02_inverse_matrices.mp3",
      "cues_file": "sec_02_inverse_matrices_cues.json",
      "total_duration_ms": 125900.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "দ্বিতীয় পরিচ্ছেদ: বিপরীত ম্যাট্রিক্স ও রূপান্তরের পূর্বাবস্থা।",
          "en": "Chapter 2: The Inverse Matrix and Undoing Transformations.",
          "formula": null,
          "duration_ms": 4500.0,
          "start_ms": 0.0,
          "end_ms": 4500.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "ধরা যাক ম্যাট্রিক্স এ-এর ডিটারমিন্যান্ট শূন্য নয়। অর্থাৎ রূপান্তরটি স্থানকে চ্যাপ্টা করে এক মাত্রা বা শূন্য মাত্রায় সংকুচিত করেনি; সমতল সমতলেই রয়ে গেছে।",
          "en": "Suppose the determinant of matrix A is non-zero. This means the transformation did not squish space into a lower dimension; the plane remains a plane.",
          "formula": "\\det(A) \\neq 0",
          "duration_ms": 12800.0,
          "start_ms": 4850.0,
          "end_ms": 17650.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "যেহেতু স্থান সংকুচিত হয়নি, তাই আমরা পুরো রূপান্তরটিকে একদম হুবহু উল্টো দিকে চালিয়ে সমতলকে তার পূর্বের অবস্থায় ফিরিয়ে আনতে পারি! এই উল্টো রূপান্তরটিকেই বলা হয় এ-এর বিপরীত রূপান্তর বা এ ইনভার্স।",
          "en": "Because space wasn't compressed, we can play the transformation backwards to return space to its original state. This reverse transformation is called the inverse of A, denoted A inverse.",
          "formula": "A^{-1}",
          "duration_ms": 16400.0,
          "start_ms": 18000.0,
          "end_ms": 34400.0
        },
        {
          "index": 3,
          "type": "figure",
          "text": "স্ক্রিনে লক্ষ্য করুন: ম্যাট্রিক্স এ যদি সমতলকে নব্বই ডিগ্রি ঘড়ির কাঁটার বিপরীতে ঘোরায়, তবে এ ইনভার্স ঠিক নব্বই ডিগ্রি ঘড়ির কাঁটার দিকে ফিরিয়ে নিয়ে আসবে।",
          "en": "On screen, observe that if matrix A rotates the plane 90 degrees counterclockwise, A inverse rotates it 90 degrees clockwise back to start.",
          "formula": null,
          "duration_ms": 12200.0,
          "start_ms": 34750.0,
          "end_ms": 46950.0
        },
        {
          "index": 4,
          "type": "formula-box",
          "text": "যদি আপনি প্রথমে এ রূপান্তর প্রয়োগ করেন এবং ঠিক তারপর এ ইনভার্স রূপান্তর প্রয়োগ করেন, তবে স্থানের কোনো ভেক্টরই বিন্দুমাত্র নড়বে না। গণিতে একে বলা হয় আইডেন্টিটি বা অভেদক রূপান্তর।",
          "en": "If you apply transformation A followed immediately by A inverse, every vector stays exactly where it began. In mathematics, this is the identity transformation.",
          "formula": "A^{-1} A = I = \\begin{bmatrix} 1 & 0 \\\\ 0 & 1 \\end{bmatrix}",
          "duration_ms": 16500.0,
          "start_ms": 47300.0,
          "end_ms": 63800.0
        },
        {
          "index": 5,
          "type": "insight-box",
          "text": "অতএব এ গুণ এক্স সমান ভি সমীকরণটি সমাধানের জন্য আমাদের কেবল উভয় পাশে এ ইনভার্স প্রয়োগ করতে হবে। ফলে আমরা এক নিমেষেই পেয়ে যাই: এক্স সমান এ ইনভার্স গুণ ভি!",
          "en": "Therefore, to solve A times x equals v, we simply apply A inverse to both sides of the equation, immediately yielding x equals A inverse times v!",
          "formula": "A\\vec{x} = \\vec{v} \\implies \\vec{x} = A^{-1}\\vec{v}",
          "duration_ms": 15200.0,
          "start_ms": 64150.0,
          "end_ms": 79350.0
        },
        {
          "index": 6,
          "type": "h3",
          "text": "ডিটারমিন্যান্ট শূন্য হলে কেন বিপরীত ম্যাট্রিক্স থাকতে পারে না?",
          "en": "Why can there be no inverse when the determinant is zero?",
          "formula": null,
          "duration_ms": 4600.0,
          "start_ms": 79700.0,
          "end_ms": 84300.0
        },
        {
          "index": 7,
          "type": "p",
          "text": "কিন্তু যদি ডিটারমিন্যান্ট শূন্য হয়, তখন কী ঘটবে? ডিটারমিন্যান্ট শূন্য মানে রূপান্তরটি পুরো দ্বিমাত্রিক সমতলকে চ্যাপ্টা করে একটি একমাত্রিক সরলরেখায় বা একক বিন্দুতে পরিণত করেছে।",
          "en": "What happens if the determinant is zero? A zero determinant means the transformation squished the entire 2D plane into a 1D line or a single point.",
          "formula": "\\det(A) = 0",
          "duration_ms": 13900.0,
          "start_ms": 84650.0,
          "end_ms": 98550.0
        },
        {
          "index": 8,
          "type": "figure",
          "text": "একমাত্রিক রেখাকে টেনে আবার দ্বিমাত্রিক সমতলে ফিরিয়ে আনার কোনো একক রূপান্তর তৈরি করা অসম্ভব! কারণ একটি রেখার একক বিন্দুকে সমতলের অসংখ্য বিন্দুতে ম্যাপিং করতে হবে, যা কোনো বৈধ ফাংশনের নিয়ম মানে না।",
          "en": "It is impossible to un-squish a 1D line back into a 2D plane with a single transformation, because an individual point on the line would have to map to an entire line of points, violating the definition of a function.",
          "formula": null,
          "duration_ms": 16800.0,
          "start_ms": 98900.0,
          "end_ms": 115700.0
        },
        {
          "index": 9,
          "type": "p",
          "text": "এই কারণেই যখন ডিটারমিন্যান্ট শূন্য হয়, তখন ম্যাট্রিক্সটির কোনো ইনভার্স বা বিপরীত ম্যাট্রিক্স থাকতে পারে না।",
          "en": "This is precisely why, whenever the determinant is zero, the matrix has no inverse.",
          "formula": "\\det(A) = 0 \\implies A^{-1} \\text{ does not exist}",
          "duration_ms": 9500.0,
          "start_ms": 116050.0,
          "end_ms": 125550.0
        }
      ]
    },
    "sec_03_rank_and_column_space": {
      "title": "র‍্যাংক এবং কলাম স্পেস: রূপান্তরের সম্ভাব্য আউটপুট ক্ষেত্র",
      "audio_file": "sec_03_rank_and_column_space.mp3",
      "cues_file": "sec_03_rank_and_column_space_cues.json",
      "total_duration_ms": 91800.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "তৃতীয় পরিচ্ছেদ: র‍্যাংক এবং কলাম স্পেসের জ্যামিতিক রূপ।",
          "en": "Chapter 3: The Geometry of Rank and Column Space.",
          "formula": null,
          "duration_ms": 4300.0,
          "start_ms": 0.0,
          "end_ms": 4300.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "যখন কোনো রূপান্তরের মাধ্যমে সমতল চ্যাপ্টা হয়ে যায়, তখন তার আউটপুট ঠিক কেমন হতে পারে? রূপান্তর প্রয়োগ করার পর যত সম্ভাব্য আউটপুট ভেক্টর তৈরি হতে পারে, তাদের সমগ্র সেটকে বলা হয় কলাম স্পেস।",
          "en": "When a transformation squishes space, what does the output look like? The set of all possible outputs that a transformation can give is called the column space of the matrix.",
          "formula": "\\text{Col}(A) = \\{ A\\vec{v} : \\vec{v} \\in \\mathbb{R}^n \\}",
          "duration_ms": 16200.0,
          "start_ms": 4650.0,
          "end_ms": 20850.0
        },
        {
          "index": 2,
          "type": "p",
          "text": "কিন্তু এটিকে কলাম স্পেস নাম দেওয়া হলো কেন? কারণ আমরা জানি ম্যাট্রিক্সের প্রতিটি কলাম আসলে রূপান্তরের পর বেসিস ভেক্টরগুলো কোথায় গিয়ে পৌঁছায় তা নির্দেশ করে।",
          "en": "Why is it called the column space? Because the columns of a matrix tell you where the standard basis vectors land after the transformation.",
          "formula": null,
          "duration_ms": 11800.0,
          "start_ms": 21200.0,
          "end_ms": 33000.0
        },
        {
          "index": 3,
          "type": "insight-box",
          "text": "আর যেকোনো ভেক্টরের রূপান্তর হলো ওই কলামগুলোরই একটি রৈখিক সমাবেশ বা লিনিয়ার কম্বিনেশন! সুতরাং কলাম স্পেসের সহজ অর্থ হলো: ম্যাট্রিক্সের কলামগুলোর স্প্যান বা বিস্তার।",
          "en": "Every transformed vector is simply a linear combination of those transformed basis vectors! Thus, the column space is literally the span of the columns of the matrix.",
          "formula": "\\text{Column Space} = \\text{Span}(\\text{Columns of } A)",
          "duration_ms": 14900.0,
          "start_ms": 33350.0,
          "end_ms": 48250.0
        },
        {
          "index": 4,
          "type": "h3",
          "text": "র‍্যাংক: আউটপুট স্পেসের প্রকৃত মাত্রা।",
          "en": "Rank: The True Dimension of Output Space.",
          "formula": null,
          "duration_ms": 3600.0,
          "start_ms": 48600.0,
          "end_ms": 52200.0
        },
        {
          "index": 5,
          "type": "p",
          "text": "রূপান্তরের পর এই আউটপুট স্পেসের মাত্রা বা ডাইমেনশন কত—তা নির্দেশ করার গাণিতিক পরিমাপটির নামই হলো র‍্যাংক।",
          "en": "The dimension of this output space is called the rank of the transformation.",
          "formula": "\\text{Rank}(A) = \\dim(\\text{Col}(A))",
          "duration_ms": 10500.0,
          "start_ms": 52550.0,
          "end_ms": 63050.0
        },
        {
          "index": 6,
          "type": "figure",
          "text": "যদি আউটপুট একটি একমাত্রিক সরলরেখা হয়, তবে ম্যাট্রিক্সের র‍্যাংক হলো এক। আর যদি আউটপুটটি পুরো দ্বিমাত্রিক সমতল জুড়েই বিস্তৃত থাকে, তবে তার র‍্যাংক হলো দুই।",
          "en": "If the output is compressed into a one-dimensional line, the rank is 1. If the output fills the entire two-dimensional plane, the rank is 2.",
          "formula": "\\text{Line} \\implies \\text{Rank 1}, \\quad \\text{Plane} \\implies \\text{Rank 2}",
          "duration_ms": 13800.0,
          "start_ms": 63400.0,
          "end_ms": 77200.0
        },
        {
          "index": 7,
          "type": "p",
          "text": "ত্রিমাত্রিক স্থানে যদি আউটপুট স্থান সংকুচিত না হয়ে পূর্ণ থ্রিডি স্পেস থাকে, তবে র‍্যাংক তিন। আর যখন র‍্যাংক ম্যাট্রিক্সের কলাম সংখ্যার সমান হয়, তখন তাকে আমরা বলি ফুল র‍্যাংক।",
          "en": "In 3D, if the output is not compressed and occupies full 3D space, the rank is 3. When the rank equals the number of columns, the matrix is said to be full rank.",
          "formula": "\\text{Full Rank} \\iff \\text{Rank}(A) = n",
          "duration_ms": 13900.0,
          "start_ms": 77550.0,
          "end_ms": 91450.0
        }
      ]
    },
    "sec_04_null_space": {
      "title": "নাল স্পেস বা শূন্য স্পেস: মূলবিন্দুতে সংকুচিত ভেক্টরের জগৎ",
      "audio_file": "sec_04_null_space.mp3",
      "cues_file": "sec_04_null_space_cues.json",
      "total_duration_ms": 103150.0,
      "cues": [
        {
          "index": 0,
          "type": "h2",
          "text": "চতুর্থ পরিচ্ছেদ: নাল স্পেস বা শূন্য স্পেস এবং সমাধানের জ্যামিতি।",
          "en": "Chapter 4: The Null Space (Kernel) and the Geometry of Solutions.",
          "formula": null,
          "duration_ms": 4800.0,
          "start_ms": 0.0,
          "end_ms": 4800.0
        },
        {
          "index": 1,
          "type": "p",
          "text": "যখন কোনো রৈখিক রূপান্তরের ডিটারমিন্যান্ট শূন্য হয় এবং সমতল সংকুচিত হয়ে একটি সরলরেখায় পরিণত হয়, তখন মূলবিন্দু ছাড়াও অসংখ্য ভেক্টর নিশ্চয়ই মূলবিন্দুর ওপর গিয়ে আছড়ে পড়ে।",
          "en": "When a linear transformation squishes space into a line (det = 0), then besides the origin, a whole bunch of other vectors must land squarely on the origin as well.",
          "formula": null,
          "duration_ms": 14700.0,
          "start_ms": 5150.0,
          "end_ms": 19850.0
        },
        {
          "index": 2,
          "type": "figure",
          "text": "পাশের অ্যানিমেশনে লক্ষ্য করুন: সমতলের একটি সম্পূর্ণ সরলরেখায় অবস্থিত সমস্ত ভেক্টর রূপান্তরের পর সংকুচিত হয়ে মূলবিন্দু শূন্যে গিয়ে মিলিত হচ্ছে।",
          "en": "In the animation, watch how an entire line of vectors in the 2D plane collapses directly into the origin under the transformation.",
          "formula": null,
          "duration_ms": 12500.0,
          "start_ms": 20200.0,
          "end_ms": 32700.0
        },
        {
          "index": 3,
          "type": "formula-box",
          "text": "যে সমস্ত ইনপুট ভেক্টর রূপান্তরের পর সরাসরি মূলবিন্দু বা শূন্য ভেক্টরে পরিণত হয়, তাদের সমগ্র সেটকে বলা হয় ওই ম্যাট্রিক্সের নাল স্পেস বা শূন্য স্পেস। একে অনেকে কার্নেলও বলে থাকেন।",
          "en": "The set of all input vectors that end up landing on the origin is called the null space or kernel of the matrix.",
          "formula": "\\text{Null}(A) = \\{ \\vec{x} \\in \\mathbb{R}^n : A\\vec{x} = \\vec{0} \\}",
          "duration_ms": 17200.0,
          "start_ms": 33050.0,
          "end_ms": 50250.0
        },
        {
          "index": 4,
          "type": "insight-box",
          "text": "সমীকরণ জোট সমাধানের ক্ষেত্রে নাল স্পেসের ভূমিকা অত্যন্ত গুরুত্বপূর্ণ। যদি এ গুণ এক্স সমান ভি সমীকরণের একটি নির্দিষ্ট সমাধান এক্স নট থাকে, তবে এক্স নটের সাথে নাল স্পেসের যেকোনো ভেক্টর যোগ করলেও তা একটি সম্পূর্ণ নির্ভুল সমাধান দেবে!",
          "en": "When solving systems of equations, the null space plays a crucial role. If you have a specific solution x_0 to Ax = v, adding any vector from the null space to x_0 produces another valid solution!",
          "formula": "A(\\vec{x}_0 + \\vec{n}) = A\\vec{x}_0 + A\\vec{n} = \\vec{v} + \\vec{0} = \\vec{v}",
          "duration_ms": 20100.0,
          "start_ms": 50600.0,
          "end_ms": 70700.0
        },
        {
          "index": 5,
          "type": "p",
          "text": "কারণ নাল স্পেসের ভেক্টর রূপান্তরের পর শূন্য হয়ে যায়, তাই এটি ফলাফলে কোনো হেরফের ঘটায় না। অর্থাৎ নাল স্পেস আমাদের সমাধানের সম্পূর্ণ জ্যামিতিক ক্ষেত্র ও স্বাধীনতার মাত্রা উপহার দেয়।",
          "en": "Because vectors in the null space map to zero, adding them changes nothing about the output. Thus, the null space tells you the full geometric freedom of solutions.",
          "formula": null,
          "duration_ms": 14500.0,
          "start_ms": 71050.0,
          "end_ms": 85550.0
        },
        {
          "index": 6,
          "type": "p",
          "text": "এই গভীর উপলব্ধিটি আমাদের স্পষ্ট করে দেয়: লিনিয়ার অ্যালজেব্রায় বিপরীত ম্যাট্রিক্স, কলাম স্পেস এবং নাল স্পেস কোনো বিচ্ছিন্ন সূত্র নয়—বরং এরা স্থানকে রূপান্তর ও সংকোচনের এক অবিচ্ছেদ্য এবং সুসংহত জ্যামিতিক গল্প!",
          "en": "This profound realization shows that inverse matrices, column space, and null space are not isolated formulas, but a unified geometric narrative of how transformations warp space.",
          "formula": null,
          "duration_ms": 16900.0,
          "start_ms": 85900.0,
          "end_ms": 102800.0
        }
      ]
    }
  }
};
