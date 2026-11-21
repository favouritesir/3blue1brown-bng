# 3Blue1Brown: Essence of Linear Algebra — Lesson 01
## মাস্টার বাংলা ডাবিং স্ক্রিপ্ট ও অডিও পাইপলাইন স্পেসিফিকেশন (Music-Free Pure Dub)

**মূল কোর্স:** Essence of Linear Algebra (Chapter 01: Vectors, what even are they?)  
**মূল বক্তা ও স্রষ্টা:** Grant Sanderson (3Blue1Brown)  
**অনুবাদ ও বাচনভঙ্গি অভিযোজন:** সিনিয়র স্ক্রিপ্ট অ্যাডাপ্টার অ্যান্ড ভয়েস স্পেশালিস্ট, বাংলা রিসোর্স ফ্যাক্টরি (BRF)  
**অডিও প্রোফাইল:** **Music-Free Pure Halal Audio** (১০০% ব্যাকগ্রাউন্ড মিউজিক অপসারণ, অরিজিনাল সাউন্ড ইফেক্ট ও ট্রানজিশন ক্লিক অক্ষুণ্ণ)  
**কোর ভয়েস মডেল:** Microsoft Neural Voice `bn-BD-PradeepNeural` (Warm, pedagogical, precise male timbre)  
**মোট কিউ সংখ্যা:** ৯৮টি সুবিন্যস্ত স্পোকেন কিউ  
**ভিডিও মোট দৈর্ঘ্য:** ৯ মিনিট ৫১ সেকেন্ড (৫৯১.১৫ সেকেন্ড)  

---

### 🎙️ ভয়েস কাস্টিং ও পার্সোনা ম্যাপিং (Voice Persona Architecture)

| চরিত্র / ভূমিকা | সোর্স পার্সোনা | নির্ধারিত Neural Voice ID | পিচ ও রেট মডিউলেশন | বাচনভঙ্গির ধরন (Delivery Tone) |
|---|---|---|---|---|
| **মূল বক্তা (Narrator)** | Grant Sanderson | `bn-BD-PradeepNeural` | Pitch: `+0Hz`, Rate: `Dynamic Sync (0.85x - 1.35x)` | বন্ধুত্বপূর্ণ, চিন্তাশীল, সাবলীল শিক্ষাদানের সুর (Pedagogical & Intuitive) |
| **টেকনিক্যাল টার্মিনোলজি** | Standard Math Terms | Retained English Pronunciation | Pitch: `Default` | Linear Algebra, Vector, Origin, Component, Scalar, Span, Bases |

---

### 📋 কিউ-বাই-কিউ মাস্টার ডাবিং স্ক্রিপ্ট (Timestamped Dialogue & Cues)

| # | টাইমকোড (Start ➔ End) | দৈর্ঘ্য | মূল ইংরেজি বাক্য (Original 3B1B Narration) | প্রাকৃতিক বাংলা স্পোকেন স্ক্রিপ্ট (Natural Spoken Bangla) |
|---|---|---|---|---|
| **01** | `00:10.92 ➔ 00:15.22` | 4.30s | The fundamental, root-of-it-all building block for linear algebra is the vector. | **লিনিয়ার বীজগণিতের একেবারে গোড়ার বা মৌলিক ভিত্তিপ্রস্তর হলো—ভেক্টর।** |
| **02** | `00:15.72 ➔ 00:19.84` | 4.12s | So it's worth making sure that we're all on the same page about what exactly a vector is. | **তাই শুরুতেই স্পষ্ট করে নেওয়া ভালো যে, ভেক্টর আসলে ঠিক কী জিনিস।** |
| **03** | `00:20.38 ➔ 00:26.48` | 6.10s | You see, broadly speaking, there are three distinct but related ideas about vectors, which I'll call the physics student perspective, | **আসলে মোটা দাগে বলতে গেলে, ভেক্টর নিয়ে তিনটি ভিন্ন কিন্তু পরস্পরের সাথে যুক্ত দৃষ্টিভঙ্গি রয়েছে; যার প্রথমটি হলো পদার্থবিজ্ঞানের ছাত্রের দৃষ্টিভঙ্গি,** |
| **04** | `00:26.48 ➔ 00:30.10` | 3.62s | the computer science student perspective, and the mathematician's perspective. | **দ্বিতীয়টি কম্পিউটার সায়েন্সের ছাত্রের দৃষ্টিভঙ্গি, আর তৃতীয়টি গণিতবিদদের দৃষ্টিভঙ্গি।** |
| **05** | `00:30.88 ➔ 00:34.40` | 3.52s | The physics student perspective is that vectors are arrows pointing in space. | **পদার্থবিজ্ঞানের শিক্ষার্থীদের কাছে ভেক্টর হলো মহাশূন্যে বা স্পেসে নির্দেশিত একটি তীরচিহ্ন।** |
| **06** | `00:34.94 ➔ 00:43.16` | 8.22s | What defines a given vector is its length and the direction it's pointing, but as long as those two facts are the same, you can move it all around, and it's still the same vector. | **একটি নির্দিষ্ট ভেক্টরকে সংজ্ঞায়িত করে তার দৈর্ঘ্য এবং তার অভিমুখ; যতক্ষণ এই দুটি বিষয় একই থাকছে, আপনি একে যেকোনো জায়গায় স্থানান্তর করতে পারেন—ভেক্টর কিন্তু একই থাকবে।** |
| **07** | `00:44.04 ➔ 00:50.04` | 6.00s | Vectors that live in the flat plane are two-dimensional, and those sitting in broader space that you and I live in are three-dimensional. | **একটি সমতলে থাকা ভেক্টরগুলো দ্বিমাত্রিক বা 2D, আর আমাদের চারপাশের ত্রিমাত্রিক স্পেসে থাকা ভেক্টরগুলো 3D।** |
| **08** | `00:51.72 ➔ 00:55.64` | 3.92s | The computer science perspective is that vectors are ordered lists of numbers. | **অন্যদিকে, কম্পিউটার সায়েন্সের দৃষ্টিভঙ্গি হলো—ভেক্টর মূলত সংখ্যার একটি সুশৃঙ্খল তালিকা বা লিস্ট।** |
| **09** | `00:55.64 ➔ 01:02.76` | 7.12s | For example, let's say you were doing some analytics about house prices, and the only features you cared about were square footage and price. | **ধরুন, আপনি বাড়ির দাম নিয়ে কিছু অ্যানালিটিক্স করছেন, যেখানে আপনার প্রধান বিবেচ্য বিষয় হলো বাড়ির স্কয়ার ফিট এবং তার দাম।** |
| **10** | `01:03.02 ➔ 01:08.68` | 5.66s | You might model each house with a pair of numbers, the first indicating square footage and the second indicating price. | **তখন আপনি প্রতিটি বাড়িকে এক জোড়া সংখ্যা দিয়ে প্রকাশ করতে পারেন; প্রথম সংখ্যাটি স্কয়ার ফিট এবং দ্বিতীয়টি তার দাম নির্দেশ করবে।** |
| **11** | `01:09.32 ➔ 01:11.04` | 1.72s | Notice the order matters here. | **লক্ষ্য করুন, এখানে সংখ্যার ক্রম বা অর্ডার কিন্তু খুবই গুরুত্বপূর্ণ।** |
| **12** | `01:12.40 ➔ 01:19.69` | 7.29s | In the lingo, you'd be modeling houses as two-dimensional vectors, where in this context, vector is pretty much just a fancy word for list, | **টেকনিক্যাল ভাষায়, আপনি বাড়িগুলোকে দ্বিমাত্রিক ভেক্টর হিসেবে মডেল করছেন; যেখানে ভেক্টর শব্দটি মূলত লিস্ট বা তালিকারই একটি গাণিতিক রূপ,** |
| **13** | `01:19.69 ➔ 01:24.04` | 4.35s | and what makes it two-dimensional is the fact that the length of that list is two. | **আর এটি দ্বিমাত্রিক হওয়ার কারণ হলো, এই লিস্টে ঠিক দুটি উপাদান রয়েছে।** |
| **14** | `01:25.64 ➔ 01:33.65` | 8.01s | The mathematician, on the other hand, seeks to generalize both these views, basically saying that a vector can be anything where there's a sensible notion of adding | **গণিতবিদরা আবার এই দুই দৃষ্টিভঙ্গিকে এক সুতোয় বেঁধে সাধারণ রূপ দিতে চান। তাঁদের মতে, যেকোনো কিছুকেই ভেক্টর বলা যাবে, যদি সেখানে যোগ করার একটি স্পষ্ট নিয়ম থাকে—** |
| **15** | `01:33.65 ➔ 01:38.82` | 5.17s | two vectors and multiplying a vector by a number, operations that I'll talk about later on in this video. | **অর্থাৎ দুটি ভেক্টরের যোগ এবং কোনো সংখ্যা দিয়ে ভেক্টরকে গুণ করা; যে অপারেশনগুলো নিয়ে আমি একটু পরেই বিস্তারিত কথা বলব।** |
| **16** | `01:39.58 ➔ 01:47.94` | 8.36s | The details of this view are rather abstract, and I actually think it's healthy to ignore it until the last video of this series, favoring a more concrete setting in the interim. | **এই ধারণাটি কিছুটা বিমূর্ত বা অ্যাবস্ট্র্যাক্ট, তাই সিরিজের শেষ ভিডিওর আগ পর্যন্ত এটিকে কিছুটা সরিয়ে রেখে আরও বাস্তবসম্মত দৃষ্টিভঙ্গিতে এগোনোই ভালো হবে।** |
| **17** | `01:48.40 ➔ 01:54.15` | 5.75s | But the reason I bring it up here is that it hints at the fact that the ideas of vector addition and multiplication by | **তবে এখন এর উল্লেখ করার কারণ হলো, ভেক্টর যোগ এবং সংখ্যা দিয়ে গুণ করার এই ধারণাটি—** |
| **18** | `01:54.15 ➔ 01:57.22` | 3.07s | numbers will play an important role throughout linear algebra. | **পুরো লিনিয়ার বীজগণিত জুড়েই অত্যন্ত গুরুত্বপূর্ণ ভূমিকা পালন করবে।** |
| **19** | `01:58.00 ➔ 02:04.04` | 6.04s | But before I talk about those operations, let's just settle in on a specific thought to have in mind when I say the word vector. | **তবে সেই অপারেশনে যাওয়ার আগে, যখনই আমি 'ভেক্টর' শব্দটি উচ্চারণ করব, মনে কোন ছবিটি রাখবেন তা আগে ঠিক করে নেওয়া যাক।** |
| **20** | `02:04.74 ➔ 02:10.21` | 5.47s | Given the geometric focus that I'm shooting for here, whenever I introduce a new topic involving vectors, | **যেহেতু আমাদের মূল লক্ষ্য জ্যামিতিক অন্তর্দৃষ্টি তৈরি করা, তাই ভেক্টর নিয়ে যেকোনো নতুন বিষয় তোলার সময়—** |
| **21** | `02:10.21 ➔ 02:16.97` | 6.77s | I want you to first think about an arrow, and specifically, think about that arrow inside a coordinate system, like the xy-plane, | **আমি চাই প্রথমে আপনি একটি তীরচিহ্নের কথা ভাবুন; আরও স্পষ্ট করে বললে, xy-প্লেনের মতো একটি কোঅর্ডিনেট সিস্টেমে থাকা তীরচিহ্নের কথা,** |
| **22** | `02:16.97 ➔ 02:18.90` | 1.93s | with its tail sitting at the origin. | **যার লেজ বা শুরুটা আটকে আছে মূলবিন্দুতে।** |
| **23** | `02:19.68 ➔ 02:24.92` | 5.24s | This is a little bit different from the physics student perspective, where vectors can freely sit anywhere they want in space. | **এটি পদার্থবিজ্ঞানের সাধারণ দৃষ্টিভঙ্গি থেকে কিছুটা আলাদা; যেখানে ভেক্টর মহাশূন্যে যেখানে খুশি মুক্তভাবে থাকতে পারে।** |
| **24** | `02:25.42 ➔ 02:30.32` | 4.90s | In linear algebra, it's almost always the case that your vector will be rooted at the origin. | **লিনিয়ার বীজগণিতে প্রায় সবসময়ই ভেক্টরের লেজ মূলবিন্দু বা অরিজিনে স্থায়ী রাখা হয়।** |
| **25** | `02:30.94 ➔ 02:37.59` | 6.65s | Then, once you understand a new concept in the context of arrows in space, we'll translate it over to the list of numbers point of view, | **স্পেসে তীরচিহ্ন হিসেবে ধারণাটি বুঝে নেওয়ার পর, আমরা সেটিকে সংখ্যার তালিকার দৃষ্টিভঙ্গিতে রূপান্তর করব,** |
| **26** | `02:37.59 ➔ 02:40.62` | 3.03s | which we can do by considering the coordinates of the vector. | **যা আমরা করতে পারি ভেক্টরের স্থানাঙ্ক বা কোঅর্ডিনেটগুলো বিবেচনা করে।** |
| **27** | `02:41.44 ➔ 02:48.61` | 7.17s | Now, while I'm sure that many of you are already familiar with this coordinate system, it's worth walking through explicitly, since this is where all of the important | **যদিও আমি নিশ্চিত আপনাদের অনেকেই এই কোঅর্ডিনেট সিস্টেমের সাথে পরিচিত, তবুও এটি আরেকবার স্পষ্ট করে দেখে নেওয়া দরকার; কারণ—** |
| **28** | `02:48.61 ➔ 02:51.68` | 3.07s | back and forth happens between the two perspectives of linear algebra. | **লিনিয়ার বীজগণিতের দুটি প্রধান দৃষ্টিভঙ্গির মধ্যকার আদান-প্রদান ঠিক এখানেই ঘটে।** |
| **29** | `02:52.74 ➔ 02:59.58` | 6.84s | Focusing our attention on two dimensions for the moment, you have a horizontal line, called the x-axis, and a vertical line, called the y-axis. | **আপাতত দ্বিমাত্রিক বা 2D তলের দিকে তাকালে, আপনি একটি অনুভূমিক রেখা পাবেন যাকে বলে x-অক্ষ, এবং একটি উল্লম্ব রেখা যাকে বলে y-অক্ষ।** |
| **30** | `03:00.26 ➔ 03:05.52` | 5.26s | The place where they intersect is called the origin, which you should think of as the center of space and the root of all vectors. | **যে বিন্দুতে তারা পরস্পরকে ছেদ করে তাকে বলে মূলবিন্দু বা অরিজিন; এটিকে আপনি সমস্ত ভেক্টরের মূল কেন্দ্রস্থল ভাবতে পারেন।** |
| **31** | `03:06.38 ➔ 03:11.36` | 4.98s | After choosing an arbitrary length to represent one, you make tick marks on each axis to represent this distance. | **একক দূরত্ব বোঝাতে একটি নির্দিষ্ট দৈর্ঘ্য নির্বাচন করে, প্রতিটি অক্ষে সমান দূরত্বের দাগ বা টিক মার্ক দেওয়া হয়।** |
| **32** | `03:12.32 ➔ 03:19.41` | 7.09s | When I want to convey the idea of 2D space as a whole, which you'll see comes up a lot in these videos, I'll extend these tick marks to make grid lines, but right now, | **পুরো দ্বিমাত্রিক স্পেসের সামগ্রিক ধারণা দিতে আমি এই দাগগুলোকে বাড়িয়ে গ্রিড লাইন বানিয়ে নেব, যা এই ভিডিওগুলোতে প্রায়ই দেখবেন; তবে এই মুহূর্তে—** |
| **33** | `03:19.41 ➔ 03:21.36` | 1.95s | they'll actually get a little bit in the way. | **সেগুলো আমাদের মূল চিত্রে কিছুটা বাধা তৈরি করতে পারে।** |
| **34** | `03:22.00 ➔ 03:30.16` | 8.16s | The coordinates of a vector is a pair of numbers that basically gives instructions for how to get from the tail of that vector at the origin to its tip. | **ভেক্টরের কোঅর্ডিনেট হলো এমন এক জোড়া সংখ্যা, যা মূলত মূলবিন্দু থেকে সেই ভেক্টরের শীর্ষবিন্দু বা ডগায় পৌঁছানোর পথনির্দেশ দেয়।** |
| **35** | `03:30.88 ➔ 03:36.31` | 5.43s | The first number tells you how far to walk along the x-axis, positive numbers indicating rightward motion, | **প্রথম সংখ্যাটি বলে x-অক্ষ বরাবর কত দূর হাঁটতে হবে; ধনাত্মক সংখ্যা হলে ডানদিকে,** |
| **36** | `03:36.31 ➔ 03:42.87` | 6.56s | negative numbers indicating leftward motion, and the second number tells you how far to walk parallel to the y-axis after that, | **ঋণাত্মক সংখ্যা হলে বামদিকে; আর দ্বিতীয় সংখ্যাটি বলে এরপরে y-অক্ষের সমান্তরালে কত দূর এগোতে হবে,** |
| **37** | `03:42.87 ➔ 03:47.58` | 4.71s | positive numbers indicating upward motion, and negative numbers indicating downward motion. | **যেখানে ধনাত্মক সংখ্যা নির্দেশ করে উপরের দিক এবং ঋণাত্মক সংখ্যা নির্দেশ করে নিচের দিক।** |
| **38** | `03:48.14 ➔ 03:54.34` | 6.20s | To distinguish vectors from points, the convention is to write this pair of numbers vertically with square brackets around them. | **সাধারণ বিন্দুর সাথে পার্থক্য বোঝাতে, প্রচলিত নিয়ম অনুযায়ী এই সংখ্যাজোড়াকে থার্ড ব্র্যাকেট দিয়ে উল্লম্বভাবে বা কলাম আকারে লেখা হয়।** |
| **39** | `03:56.34 ➔ 04:03.68` | 7.34s | Every pair of numbers gives you one and only one vector, and every vector is associated with one and only one pair of numbers. | **প্রতিটি সংখ্যাজোড়ার জন্য ঠিক একটি অনন্য ভেক্টর পাওয়া যায়, এবং প্রতিটি ভেক্টরের জন্য নির্ধারিত থাকে ঠিক একটি সংখ্যাজোড়া।** |
| **40** | `04:04.64 ➔ 04:05.50` | 0.86s | What about in three dimensions? | **তাহলে ত্রিমাত্রিক বা 3D স্পেসের ক্ষেত্রে কী ঘটবে?** |
| **41** | `04:06.20 ➔ 04:12.86` | 6.66s | Well, you add a third axis, called the z-axis, which is perpendicular to both the x and y-axes, and in this case, | **সেক্ষেত্রে আমরা তৃতীয় একটি অক্ষ যোগ করি যার নাম z-অক্ষ, যা x এবং y উভয় অক্ষের সাথেই লম্বভাবে থাকে; আর তখন—** |
| **42** | `04:12.86 ➔ 04:16.34` | 3.48s | each vector is associated with ordered triplet of numbers. | **প্রতিটি ভেক্টরকে তিনটি সংখ্যার একটি সুশৃঙ্খল ট্রিপলেট দিয়ে প্রকাশ করা হয়।** |
| **43** | `04:16.86 ➔ 04:23.28` | 6.42s | The first tells you how far to move along the x-axis, the second tells you how far to move parallel to the y-axis, | **প্রথমটি বলে x-অক্ষ বরাবর কত দূর যেতে হবে, দ্বিতীয়টি বলে y-অক্ষের সমান্তরালে কত দূর চলতে হবে,** |
| **44** | `04:23.28 ➔ 04:27.68` | 4.40s | and the third one tells you how far to then move parallel to this new z-axis. | **আর তৃতীয়টি বলে নতুন এই z-অক্ষের সমান্তরালে কতটা উপরে বা নিচে সরতে হবে।** |
| **45** | `04:28.40 ➔ 04:35.56` | 7.16s | Every triplet of numbers gives you one unique vector in space, and every vector in space gives you exactly one triplet of numbers. | **প্রতিটি তিন-সংখ্যার ট্রিপলেট স্পেসে একটি অনন্য ভেক্টর দেয়, আর স্পেসের প্রতিটি ভেক্টরের জন্য রয়েছে ঠিক একটি নির্দিষ্ট ট্রিপলেট।** |
| **46** | `04:36.90 ➔ 04:40.10` | 3.20s | All right, so back to vector addition and multiplication by numbers. | **বেশ, এবার ফেরা যাক ভেক্টর যোগ এবং সংখ্যা দিয়ে গুণ করার সেই মূল আলোচনায়।** |
| **47** | `04:40.46 ➔ 04:44.78` | 4.32s | After all, every topic in linear algebra is going to center around these two operations. | **কারণ লিনিয়ার বীজগণিতের প্রতিটি বিষয়ই এই দুটি মৌলিক অপারেশনের ওপর ভিত্তি করে আবর্তিত হয়।** |
| **48** | `04:45.44 ➔ 04:47.64` | 2.20s | Luckily, each one's pretty straightforward to define. | **সৌভাগ্যবশত, এই দুটিকে সংজ্ঞায়িত করা কিন্তু বেশ সহজ ও সরাসরি।** |
| **49** | `04:48.48 ➔ 04:53.56` | 5.08s | Let's say we have two vectors, one pointing up and a little to the right, and the other one pointing right and down a bit. | **ধরুন আমাদের দুটি ভেক্টর আছে—একটি উপরের দিকে ও কিছুটা ডানে নির্দেশ করছে, আর অন্যটি ডানে এবং কিছুটা নিচের দিকে।** |
| **50** | `04:53.96 ➔ 04:59.68` | 5.72s | To add these two vectors, move the second one so that its tail sits at the tip of the first one. | **এই দুটি ভেক্টর যোগ করতে দ্বিতীয় ভেক্টরটিকে এমনভাবে সরান যাতে তার লেজ গিয়ে বসে প্রথম ভেক্টরের মাথায়।** |
| **51** | `05:00.30 ➔ 05:08.74` | 8.44s | Then, if you draw a new vector from the tail of the first one to where the tip of the second one sits, that new vector is their sum. | **এরপর প্রথম ভেক্টরের লেজ থেকে দ্বিতীয় ভেক্টরের শীর্ষবিন্দু পর্যন্ত যদি একটি নতুন তীরচিহ্ন আঁকেন, তবে সেই নতুন ভেক্টরটিই হলো তাদের যোগফল।** |
| **52** | `05:12.08 ➔ 05:18.86` | 6.78s | This definition of addition, by the way, is pretty much the only time in linear algebra where we let vectors stray away from the origin. | **বলে রাখা ভালো, ভেক্টর যোগের এই পদ্ধতির সময়ই কেবল লিনিয়ার বীজগণিতে ভেক্টরকে মূলবিন্দু ছেড়ে অন্য জায়গায় সরানোর সুযোগ দেওয়া হয়।** |
| **53** | `05:19.72 ➔ 05:21.48` | 1.76s | Now, why is this a reasonable thing to do? | **এখন প্রশ্ন হলো, এটি কেন একটি যুক্তিসঙ্গত পদ্ধতি?** |
| **54** | `05:21.74 ➔ 05:24.02` | 2.28s | Why this definition of addition and not some other one? | **ভেক্টর যোগের জন্য এই নির্দিষ্ট নিয়মটিই কেন নেওয়া হলো, অন্য কোনো নিয়ম কেন নয়?** |
| **55** | `05:25.52 ➔ 05:32.68` | 7.16s | Well, the way I like to think about it is that each vector represents a certain movement, a step with a certain distance and direction in space. | **আমি যেভাবে এটি ভাবতে পছন্দ করি তা হলো—প্রতিটি ভেক্টর স্পেসের মাঝে একটি নির্দিষ্ট দূরত্ব ও অভিমুখের ধাপ বা মুভমেন্ট নির্দেশ করে।** |
| **56** | `05:33.98 ➔ 05:41.15` | 7.17s | If you take a step along the first vector, then take a step in the direction and distance described by the second vector, the overall effect is just | **আপনি যদি প্রথম ভেক্টর বরাবর এক ধাপ হাঁটেন, এবং সেখান থেকে দ্বিতীয় ভেক্টরের দিক ও দূরত্ব অনুযায়ী আরেক ধাপ হাঁটেন, তবে তার সামগ্রিক ফলাফল—** |
| **57** | `05:41.15 ➔ 05:44.78` | 3.63s | the same as if you moved along the sum of those two vectors to start with. | **একেবারে শুরুতে এই দুই ভেক্টরের যোগফল বরাবর সরাসরি হেঁটে যাওয়ার সমান হবে।** |
| **58** | `05:45.26 ➔ 05:49.46` | 4.20s | You could think about this as an extension of how we think about adding numbers on a number line. | **এটিকে আপনি সংখ্যারেখায় সাধারণ সংখ্যা যোগ করারই একটি চমৎকার বর্ধিত রূপ ভাবতে পারেন।** |
| **59** | `05:50.18 ➔ 05:57.96` | 7.78s | One way that we teach kids to think about this, say with 2 plus 5, is to think of moving two steps to the right followed by another five steps to the right. | **যেমন বাচ্চাদের ২ যোগ ৫ শেখানোর সময় বলা হয়—প্রথমে ডানদিকে ২ ধাপ যাও, তারপর আরও ৫ ধাপ ডানে এগোও।** |
| **60** | `05:57.96 ➔ 06:01.72` | 3.76s | The overall effect is the same as if you just took seven steps to the right. | **সামগ্রিক ফলাফল দাঁড়ায়—একবারে সরাসরি ৭ ধাপ ডানদিকে যাওয়ার সমান।** |
| **61** | `06:02.66 ➔ 06:05.48` | 2.82s | In fact, let's see how vector addition looks numerically. | **আসুন এবার দেখা যাক সংখ্যাতাত্ত্বিক দিক থেকে ভেক্টর যোগ দেখতে কেমন লাগে।** |
| **62** | `06:06.02 ➔ 06:12.46` | 6.44s | The first vector here has coordinates 1, 2, and the second one has coordinates 3, negative 1. | **এখানে প্রথম ভেক্টরটির কোঅর্ডিনেট হলো [১, ২], আর দ্বিতীয় ভেক্টরটির কোঅর্ডিনেট হলো [৩, -১]।** |
| **63** | `06:14.36 ➔ 06:21.42` | 7.06s | When you take the vector sum using this tip-to-tail method, you can think of a four-step path from the origin to the tip of the second vector. | **টিপ-টু-টেইল পদ্ধতিতে যোগ করার সময়, মূলবিন্দু থেকে দ্বিতীয় ভেক্টরের শীর্ষবিন্দু পর্যন্ত চার ধাপের একটি পথ কল্পনা করতে পারেন:** |
| **64** | `06:21.84 ➔ 06:25.62` | 3.78s | Walk 1 to the right, then 2 up, then 3 to the right, then 1 down. | **ডানদিকে ১ ধাপ, উপরে ২ ধাপ, আবার ডানে ৩ ধাপ, এবং নিচে ১ ধাপ।** |
| **65** | `06:26.92 ➔ 06:35.11` | 8.19s | Reorganizing these steps so that you first do all of the rightward motion, then do all the vertical motion, you can read it as saying first | **এই ধাপগুলোকে পুনর্বিন্যাস করে যদি সব ডানদিকের গতি আগে এবং উল্লম্ব গতি পরে নেওয়া হয়, তবে দাঁড়ায়—** |
| **66** | `06:35.11 ➔ 06:38.18` | 3.07s | move 1 plus 3 to the right, then move 2 minus 1 up. | **প্রথমে ডানদিকে ১ যোগ ৩ ধাপ, এরপর উপরে ২ বিয়োগ ১ ধাপ।** |
| **67** | `06:40.08 ➔ 06:44.92` | 4.84s | So the new vector has coordinates 1 plus 3 and 2 plus negative 1. | **ফলে নতুন যোগফল ভেক্টরের কোঅর্ডিনেট দাঁড়ায় ১ যোগ ৩, এবং ২ যোগ ঋণাত্মক ১।** |
| **68** | `06:45.60 ➔ 06:52.70` | 7.10s | In general, vector addition in this list of numbers conception looks like matching up their terms and adding each one together. | **সাধারণভাবে, সংখ্যার তালিকার দৃষ্টিকোণ থেকে ভেক্টর যোগ মানে হলো অনুরূপ পজিশনের সংখ্যাগুলোকে সরাসরি যোগ করে দেওয়া।** |
| **69** | `06:54.64 ➔ 06:58.36` | 3.72s | The other fundamental vector operation is multiplication by a number. | **ভেক্টরের অপর মৌলিক অপারেশনটি হলো কোনো সংখ্যা দিয়ে তাকে গুণ করা।** |
| **70** | `06:58.86 ➔ 07:01.38` | 2.52s | Now this is best understood just by looking at a few examples. | **কয়েকটি সহজ উদাহরণ দেখলেই বিষয়টি সবচেয়ে চমৎকারভাবে বোঝা যায়।** |
| **71** | `07:01.84 ➔ 07:09.62` | 7.78s | If you take the number 2 and multiply it by a given vector, it means you stretch out that vector so that it's two times as long as when you started. | **আপনি যদি একটি ভেক্টরকে ২ দিয়ে গুণ করেন, তার মানে আপনি সেটিকে টেনে প্রসারিত করে আগের চেয়ে দ্বিগুণ লম্বা করে দিলেন।** |
| **72** | `07:10.50 ➔ 07:16.86` | 6.36s | If you multiply that vector by, say, one-third, it means you squish it down so that it's one-third the original length. | **যদি ভেক্টরটিকে এক-তৃতীয়াংশ (১/৩) দিয়ে গুণ করেন, তবে তা সংকুচিত হয়ে মূল দৈর্ঘ্যের এক-তৃতীয়াংশ হয়ে যাবে।** |
| **73** | `07:17.64 ➔ 07:21.26` | 3.62s | When you multiply it by a negative number, like negative 1.8, | **আর যদি কোনো ঋণাত্মক সংখ্যা দিয়ে গুণ করা হয়, যেমন ঋণাত্মক ১.৮—** |
| **74** | `07:21.26 ➔ 07:26.30` | 5.04s | then the vector first gets flipped around, then stretched out by that factor of 1.8. | **তখন ভেক্টরটি প্রথমে ঠিক উল্টো দিকে ঘুরে যাবে, এবং তারপর ১.৮ গুণ প্রসারিত হবে।** |
| **75** | `07:27.36 ➔ 07:31.93` | 4.57s | This process of stretching or squishing or sometimes reversing the direction of | **ভেক্টরকে এভাবে প্রসারিত করা, সংকুচিত করা কিংবা তার দিক উল্টে দেওয়ার এই প্রক্রিয়াকেই—** |
| **76** | `07:31.93 ➔ 07:36.68` | 4.75s | a vector is called scaling, and whenever you catch a number like two or one-third | **বলা হয় স্কেলিং (Scaling); আর যখনই আপনি ২, কিংবা এক-তৃতীয়াংশ,** |
| **77** | `07:36.68 ➔ 07:41.14` | 4.46s | or negative 1.8 acting like this, scaling some vector, you call it a scalar. | **কিংবা ঋণাত্মক ১.৮-এর মতো কোনো সংখ্যাকে কোনো ভেক্টর স্কেল করতে দেখবেন, তাকে বলা হয় স্কেলার (Scalar)।** |
| **78** | `07:41.94 ➔ 07:46.20` | 4.26s | In fact, throughout linear algebra, one of the main things that numbers do is scale | **আসলে পুরো লিনিয়ার বীজগণিত জুড়ে সংখ্যার প্রধান কাজই হলো ভেক্টরকে স্কেল করা,** |
| **79** | `07:46.20 ➔ 07:51.18` | 4.98s | vectors, so it's common to use the word scalar pretty much interchangeably with the word number. | **তাই 'সংখ্যা' এবং 'স্কেলার' শব্দ দুটিকে প্রায় সমার্থক হিসেবেই ব্যবহার করা হয়ে থাকে।** |
| **80** | `07:52.02 ➔ 07:59.58` | 7.56s | Numerically, stretching out a vector by a factor of, say, 2, corresponds with multiplying each of its components by that factor, 2. | **সংখ্যার হিসাবে, কোনো ভেক্টরকে ২ গুণ প্রসারিত করা মানে হলো তার প্রতিটি কম্পোনেন্ট বা উপাদানকে ২ দিয়ে গুণ করা।** |
| **81** | `08:00.30 ➔ 08:08.48` | 8.18s | So in the conception of vectors as lists of numbers, multiplying a given vector by a scalar means multiplying each one of those components by that scalar. | **সুতরাং সংখ্যার তালিকার দৃষ্টিকোণ থেকে, স্কেলার গুণন মানে হলো ভেক্টরের প্রতিটি উপাদানকে আলাদাভাবে সেই স্কেলার দিয়ে গুণ করা।** |
| **82** | `08:10.22 ➔ 08:17.06` | 6.84s | You'll see in the following videos what I mean when I say linear algebra topics tend to revolve around these two fundamental operations, | **পরবর্তী ভিডিওগুলোতে আপনি আরও স্পষ্ট বুঝতে পারবেন কেন আমি বলেছিলাম—লিনিয়ার বীজগণিতের সবকিছুই মূলত এই দুটি মৌলিক অপারেশনের চারপাশে ঘোরে:** |
| **83** | `08:17.06 ➔ 08:19.22` | 2.16s | vector addition and scalar multiplication. | **ভেক্টর যোগ এবং স্কেলার গুণন।** |
| **84** | `08:19.98 ➔ 08:25.29` | 5.31s | And I'll talk more in the last video about how and why the mathematician thinks only about these operations, | **আর এই সিরিজের শেষ পর্বে আমি আরও বিস্তারিত বলব গণিতবিদরা কীভাবে এবং কেন কেবল এই অপারেশনগুলো নিয়েই ভাবেন,** |
| **85** | `08:25.29 ➔ 08:29.12` | 3.83s | independent and abstracted away from however you choose to represent vectors. | **ভেক্টরকে আপনি যেভাবেই প্রকাশ করুন না কেন, তার রূপভেদ থেকে সম্পূর্ণ স্বাধীন ও বিমূর্তভাবে।** |
| **86** | `08:29.80 ➔ 08:37.21` | 7.41s | In truth, it doesn't matter whether you think about vectors as fundamentally being arrows in space, like I'm suggesting you do, that happen to have a nice numerical | **সত্যি বলতে, ভেক্টরকে আপনি স্পেসের তীরচিহ্ন ভাবছেন যার একটি চমৎকার সংখ্যাতাত্ত্বিক রূপ আছে—যেমনটা আমি পরামর্শ দিচ্ছি,** |
| **87** | `08:37.21 ➔ 08:42.00` | 4.79s | representation, or fundamentally as lists of numbers that happen to have a nice geometric interpretation. | **নাকি সংখ্যার তালিকা ভাবছেন যার একটি চমৎকার জ্যামিতিক রূপ আছে—তাতে আসলে কোনো তফাত পড়ে না।** |
| **88** | `08:42.52 ➔ 08:49.72` | 7.20s | The usefulness of linear algebra has less to do with either one of these views than it does with the ability to translate back and forth between them. | **লিনিয়ার বীজগণিতের আসল কার্যকারিতা কেবল একটি দৃষ্টিভঙ্গিতে সীমাবদ্ধ নয়; বরং এই দুই রূপের মাঝে অবলীলায় আদান-প্রদান করতে পারার দক্ষতাই এর মূল শক্তি।** |
| **89** | `08:50.14 ➔ 08:56.99` | 6.85s | It gives the data analyst a nice way to conceptualize many lists of numbers in a visual way, which can seriously clarify patterns | **এটি একজন ডেটা অ্যানালিস্টকে বিশাল সংখ্যার তালিকাকে চোখের সামনে ভিজ্যুয়ালাইজ করার সুযোগ দেয়, যা ডেটার মধ্যকার লুকানো প্যাটার্ন স্পষ্ট করতে—** |
| **90** | `08:56.99 ➔ 09:00.28` | 3.29s | in data and give a global view of what certain operations do. | **এবং বিভিন্ন গাণিতিক অপারেশনের সামগ্রিক প্রভাব বুঝতে দারুণ সাহায্য করে।** |
| **91** | `09:00.82 ➔ 09:07.74` | 6.92s | And on the flip side, it gives people like physicists and computer graphics programmers a language to describe space and the manipulation | **অন্যদিকে, পদার্থবিদ ও কম্পিউটার গ্রাফিক্স প্রোগ্রামারদের এটি একটি শক্তিশালী ভাষা দেয়, যার মাধ্যমে স্পেস এবং তার বিভিন্ন পরিবর্তনকে—** |
| **92** | `09:07.74 ➔ 09:11.38` | 3.64s | of space using numbers that can be crunched and run through a computer. | **কম্পিউটারে গণনাকৃত সংখ্যার মাধ্যমে নিখুঁতভাবে পরিচালনা করা সম্ভব হয়।** |
| **93** | `09:12.30 ➔ 09:20.07` | 7.77s | When I do math-y animations, for example, I start by thinking about what's actually going on in space, and then get the computer to represent things numerically, | **উদাহরণস্বরূপ, আমি যখন এই গাণিতিক অ্যানিমেশনগুলো তৈরি করি, আমি প্রথমে চিন্তা করি স্পেসের মাঝে জ্যামিতিকভাবে ঠিক কী ঘটছে; তারপর কম্পিউটারকে দিয়ে তা সংখ্যায় রূপান্তর করাই,** |
| **94** | `09:20.07 ➔ 09:23.06` | 2.99s | thereby figuring out where to place the pixels on the screen. | **যাতে কম্পিউটার স্ক্রিনের ঠিক কোন পিক্সেলটি কোথায় জ্বলবে তা সঠিকভাবে বের করতে পারে।** |
| **95** | `09:23.48 ➔ 09:26.58` | 3.10s | And doing that usually relies on a lot of linear algebra understanding. | **আর এটি নিখুঁতভাবে করার জন্য লিনিয়ার বীজগণিতের গভীর বোঝাপড়ার ওপর ভরসা করতে হয়।** |
| **96** | `09:27.84 ➔ 09:38.96` | 11.12s | So there are your vector basics, and in the next video I'll start getting into some | **তো এই ছিল ভেক্টরের একেবারে মৌলিক ভিত্তি; আর এর পরবর্তী ভিডিওতে আমি শুরু করব—** |
| **97** | `09:38.96 ➔ 09:49.94` | 10.98s | pretty neat concepts surrounding vectors like span, bases, and linear dependence. | **ভেক্টরের চারপাশের অসাধারণ কিছু ধারণা, যেমন: স্প্যান (Span), বেসিস (Bases), এবং লিনিয়ার ডিপেন্ডেন্স (Linear Dependence)।** |
| **98** | `09:49.94 ➔ 09:51.82` | 1.88s | See you then! | **দেখা হচ্ছে তাহলে পরবর্তী পর্বে!** |

---

### ⚙️ অডিও পাইপলাইন ও মিউজিক অপসারণ আর্কিটেকচার (Audio Pipeline Specs)

1. **Stem Separation & Music Elimination:**
   - **DSP Center-Channel Isolation:** `stereotools=mode=ms>ll:mlev=1.2:slev=0.015625` দিয়ে দুই পাশের স্টেরিও পিয়ানো/প্যাড মিউজিক শতভাগ নির্মূল।
   - **Adaptive Bandpass & Denoiser:** `highpass=f=95`, `lowpass=f=7500`, এবং `afftdn=nf=-25` ফিল্টারের মাধ্যমে কণ্ঠ ও সাউন্ড ইফেক্ট সংরক্ষণ করে যেকোনো অবশিষ্ট ব্যাকগ্রাউন্ড হারমোনিক অপসারণ।
   - **SFX Extraction:** অ্যানিমেশন ক্লিক, চকবোর্ড ট্রানজিশন ও টাইপিং সাউন্ড `highpass=f=3200,agate` দিয়ে আলাদা `sfx_isolated.wav` স্টেম হিসেবে প্রস্তুত।

2. **Neural Voice Synthesis:**
   - Edge-TTS এসিঙ্ক্রোনাস ব্যাচ প্রসেসিং দিয়ে ৯৮টি কিউয়ের অডিও ফাইল প্রস্তুতকরণ।
   - FFmpeg `atempo` ফিল্টার স্বয়ংক্রিয়ভাবে অরিজিনাল ভিজ্যুয়াল টাইমিংয়ের সাথে মিল রেখে অডিওর গতি সমন্বয় করে (০.৮৫x থেকে ১.৩৫x এর মাঝে সীমাবদ্ধ, যাতে পিচ অক্ষুণ্ণ থাকে)।

3. **Master Dubbed Audio Mix:**
   - মূল ভিডিওর ঠিক `00:10.92` সেকেন্ডে প্রথম সংলাপ শুরু হয়ে নিখুঁতভাবে শেষ কিউ `09:51.82` পর্যন্ত টাইম-সিঙ্কড।
   - কোনো ব্যাকগ্রাউন্ড বাদ্যযন্ত্রের সুর ছাড়া ১০০% হালাল ও প্রফেশনাল অডিও ডেলিভারি।
