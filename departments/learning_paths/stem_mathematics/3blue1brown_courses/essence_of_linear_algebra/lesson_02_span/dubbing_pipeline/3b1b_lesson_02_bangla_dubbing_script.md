# 3Blue1Brown লেসন ০২: মাস্টার বাংলা ডাবিং স্ক্রিপ্ট (Dubbing Script)
**অধ্যায়:** Linear combinations, span, and basis vectors
**কণ্ঠ:** bn-BD-PradeepNeural (Grant Sanderson Persona)
**মোট কিউ সংখ্যা:** 63 টি

---

### [কিউ 01] 12.20s ➔ 18.92s (ব্যাপ্তি: 6.72s)
**মূল ইংরেজি:** In the last video along with the ideas of vector addition and scalar multiplication I described Vector coordinates where there's this back and

**বাংলা ডায়ালগ:** গত ভিডিওতে ভেক্টর যোগ ও স্কেলার গুণনের ধারণার পাশাপাশি আমরা ভেক্টর স্থানাঙ্ক বা কোঅর্ডিনেট নিয়ে আলোচনা করেছিলাম।

---

### [কিউ 02] 18.92s ➔ 30.52s (ব্যাপ্তি: 11.60s)
**মূল ইংরেজি:** forth between for example pairs of numbers and two-dimensional vectors now I imagine the vector coordinates were already familiar to a lot of you but there's another kind of interesting way to think about these coordinates which

**বাংলা ডায়ালগ:** যেখানে সংখ্যার জোড়া এবং দ্বিমাত্রিক ভেক্টরের মধ্যে পারস্পরিক সম্পর্ক দেখানো হয়। আপনাদের অনেকের কাছেই হয়তো কোঅর্ডিনেট পরিচিত, তবে এগুলোকে দেখার চমৎকার আরেকটি দৃষ্টিভঙ্গি রয়েছে।

---

### [কিউ 03] 30.52s ➔ 42.48s (ব্যাপ্তি: 11.96s)
**মূল ইংরেজি:** is pretty Central to linear algebra when you have a pair of numbers that's meant to describe a vector like 3 -2 I want you to think about each coordinate as a scalar meaning think about how each one

**বাংলা ডায়ালগ:** যা লিনিয়ার বীজগণিতের একেবারে কেন্দ্রীয় বিষয়। যখন তিন কমা মাইনাস দুই এর মতো কোনো সংখ্যার জোড়া থাকে, তখন প্রতিটি কোঅর্ডিনেটকে একেকটি স্কেলার হিসেবে ভাবুন।

---

### [কিউ 04] 42.48s ➔ 54.20s (ব্যাপ্তি: 11.72s)
**মূল ইংরেজি:** stretches or squishes vectors in the XY coordinate system there are two very special vectors the one pointing to the right with length one commonly called ihat or the unit Vector in the X

**বাংলা ডায়ালগ:** অর্থাৎ ভাবুন কীভাবে তারা ভেক্টরকে প্রসারিত বা সংকুচিত করে। এক্স-ওয়াই কোঅর্ডিনেট সিস্টেমে দুটি বিশেষ ভেক্টর রয়েছে: ডানদিকে এক একক দৈর্ঘ্যের ভেক্টরকে বলা হয় আই-হ্যাট (i-hat) বা এক্স-অক্ষের ইউনিট ভেক্টর।

---

### [কিউ 05] 54.20s ➔ 63.76s (ব্যাপ্তি: 9.56s)
**মূল ইংরেজি:** Direction and the one pointing straight up with length one commonly called J hat or the unit Vector in the y direction now think of the x coordinate

**বাংলা ডায়ালগ:** আর সোজা উপরের দিকে নির্দেশ করা এক একক দৈর্ঘ্যের ভেক্টরটি হলো জে-হ্যাট (j-hat) বা ওয়াই-অক্ষের ইউনিট ভেক্টর। এবার এক্স-কোঅর্ডিনেটের কথা ভাবুন।

---

### [কিউ 06] 63.76s ➔ 70.80s (ব্যাপ্তি: 7.04s)
**মূল ইংরেজি:** of our Vector as a scaler that scales IH hat stretching it by a factor of three and the y-coordinate as a scaler that

**বাংলা ডায়ালগ:** এটি এমন এক স্কেলার যা আই-হ্যাটকে ৩ গুণ লম্বা করে, আর ওয়াই-কোঅর্ডিনেট এমন এক স্কেলার যা...

---

### [কিউ 07] 70.80s ➔ 81.08s (ব্যাপ্তি: 10.28s)
**মূল ইংরেজি:** scales J hat flipping it and stretching it by a factor of two in this sense the vector that these coordinates describe is the sum of two scaled vectors that's

**বাংলা ডায়ালগ:** জে-হ্যাটকে উল্টো দিকে ঘুরিয়ে দ্বিগুণ প্রসারিত করে। অর্থাৎ, এই কোঅর্ডিনেট দিয়ে বর্ণিত ভেক্টরটি আসলে দুটি স্কেলড ভেক্টরের যোগফল।

---

### [কিউ 08] 81.08s ➔ 90.96s (ব্যাপ্তি: 9.88s)
**মূল ইংরেজি:** a surprisingly important concept this idea of adding together two scaled vectors those two vectors IH hat and J hat have a special name by the way

**বাংলা ডায়ালগ:** দুটি স্কেলড ভেক্টরকে এভাবে যোগ করার ধারণাটি অত্যন্ত গুরুত্বপূর্ণ। প্রসঙ্গত, এই আই-হ্যাট ও জে-হ্যাট ভেক্টর দুটির একটি বিশেষ নাম রয়েছে।

---

### [কিউ 09] 90.96s ➔ 99.00s (ব্যাপ্তি: 8.04s)
**মূল ইংরেজি:** together they're called the basis of a coordinate system what this means basically is that when you think about coordinates as scalers the basis vectors

**বাংলা ডায়ালগ:** একসাথে এদেরকে বলা হয় একটি কোঅর্ডিনেট সিস্টেমের বেসিস (Basis)। এর অর্থ হলো, কোঅর্ডিনেটগুলো স্কেলার হলে বেসিস ভেক্টরগুলোই হলো সেই উপাদান—

---

### [কিউ 10] 99.00s ➔ 106.52s (ব্যাপ্তি: 7.52s)
**মূল ইংরেজি:** are what those scalers actually you know scale there's also a more technical definition but I'll get to that

**বাংলা ডায়ালগ:** যাদেরকে সেই স্কেলারগুলো মূলত স্কেল করে। এর একটি আনুষ্ঠানিক টেকনিক্যাল সংজ্ঞাও রয়েছে, যা আমরা একটু পরে দেখবো।

---

### [কিউ 11] 106.52s ➔ 115.48s (ব্যাপ্তি: 8.96s)
**মূল ইংরেজি:** later by Framing our coordinate system in terms of these two special basis vectors it raises a pretty interesting and subtle point we could have chosen

**বাংলা ডায়ালগ:** এই দুটি বিশেষ বেসিস ভেক্টরের মাধ্যমে স্থানকে ব্যাখ্যা করার ফলে দারুণ একটি বিষয় স্পষ্ট হয়: আমরা চাইলেই কিন্তু সম্পূর্ণ ভিন্ন বেসিস ভেক্টর বেছে নিতে পারতাম!

---

### [কিউ 12] 115.48s ➔ 124.96s (ব্যাপ্তি: 9.48s)
**মূল ইংরেজি:** different basis vectors and gotten a completely reasonable new coord system for example take some Vector pointing up and to the right along with some other

**বাংলা ডায়ালগ:** এবং তার মাধ্যমে সম্পূর্ণ নতুন ও যুক্তিযুক্ত একটি স্থানাঙ্ক ব্যবস্থা তৈরি করতে পারতাম। উদাহরণস্বরূপ, ডান-উপরে নির্দেশক একটি ভেক্টর এবং ডান-নিচে নির্দেশক অন্য একটি ভেক্টর নিন।

---

### [কিউ 13] 124.96s ➔ 133.44s (ব্যাপ্তি: 8.48s)
**মূল ইংরেজি:** Vector pointing down and to the right in some way take a moment to think about all the different vectors that you can get by choosing two scalers using each

**বাংলা ডায়ালগ:** একটু ভাবুন তো, যেকোনো দুটি স্কেলার বেছে নিয়ে এই দুটি ভেক্টরকে স্কেল করে যোগ করলে আপনি কোন কোন ভেক্টর তৈরি করতে পারবেন?

---

### [কিউ 14] 133.44s ➔ 143.67s (ব্যাপ্তি: 10.23s)
**মূল ইংরেজি:** one to scale one of the vectors then adding together what you get which two dimensional vectors can you reach by altering the choices of

**বাংলা ডায়ালগ:** স্কেলারের মান ইচ্ছেমতো পরিবর্তন করে আপনি দ্বিমাত্রিক স্থানের কোন কোন ভেক্টরে পৌঁছাতে সক্ষম হবেন?

---

### [কিউ 15] 143.68s ➔ 151.32s (ব্যাপ্তি: 7.64s)
**মূল ইংরেজি:** scalers the answer is that you can reach every possible two-dimensional vector and I think it's a good puzzle to plate

**বাংলা ডায়ালগ:** উত্তর হলো: আপনি দ্বিমাত্রিক স্থানের প্রতিটি সম্ভাব্য ভেক্টরেই পৌঁছাতে পারবেন! বিষয়টি নিয়ে চিন্তা করা এক চমৎকার ধাঁধা।

---

### [কিউ 16] 151.32s ➔ 160.16s (ব্যাপ্তি: 8.84s)
**মূল ইংরেজি:** y a new pair of basis vectors like this still gives us a valid way to go back and forth between Pairs of numbers and two-dimensional vectors but the

**বাংলা ডায়ালগ:** এমন নতুন বেসিস ভেক্টর জোড়াও সংখ্যার জোড়া এবং ২ডি ভেক্টরের মধ্যে রূপান্তর করতে সক্ষম, তবে—

---

### [কিউ 17] 160.16s ➔ 168.36s (ব্যাপ্তি: 8.20s)
**মূল ইংরেজি:** association is definitely different from the one that you get using the more standard basis of ihat and jhat this is something I'll go into much more detail

**বাংলা ডায়ালগ:** স্ট্যান্ডার্ড আই-হ্যাট ও জে-হ্যাটের তুলনায় এদের সংখ্যার মান অবশ্যই ভিন্ন হবে। পরবর্তী এক অধ্যায়ে আমরা চেঞ্জ অফ বেসিস নিয়ে বিস্তারিত জানবো।

---

### [কিউ 18] 168.36s ➔ 179.24s (ব্যাপ্তি: 10.88s)
**মূল ইংরেজি:** on later describing the exact relationship between different coordinate systems but for right now I just want you to appreciate the fact that anytime we describe vectors numerically it depends on an implicit

**বাংলা ডায়ালগ:** আপাতত শুধু এটুকু উপলব্ধি করলেই চলবে যে, ভেক্টরকে সংখ্যায় প্রকাশ করার প্রতিটি উপায় নির্ভর করে আমরা কোন বেসিস ভেক্টর নির্বাচন করেছি তার ওপর।

---

### [কিউ 19] 179.24s ➔ 190.32s (ব্যাপ্তি: 11.08s)
**মূল ইংরেজি:** choice of what basis vectors we're using so anytime that you're scaling two vectors and adding them like this it's called a linear combination of those two

**বাংলা ডায়ালগ:** সুতরাং, যখনই আপনি দুটি ভেক্টরকে স্কেল করে যোগ করেন, তখন তাকে বলা হয় ওই ভেক্টর দুটির লিনিয়ার কম্বিনেশন (Linear Combination)।

---

### [কিউ 20] 190.32s ➔ 198.12s (ব্যাপ্তি: 7.80s)
**মূল ইংরেজি:** vectors where does this word linear come from why does this have anything to do with lines well this isn't the atomology but one way I like to think about it is

**বাংলা ডায়ালগ:** লিনিয়ার শব্দটি কোথা থেকে এলো? সরলরেখার সাথে এর সম্পর্ক কী? এটি আক্ষরিক ব্যুৎপত্তি না হলেও, আমি যেভাবে ভাবি তা হলো—

---

### [কিউ 21] 198.12s ➔ 208.07s (ব্যাপ্তি: 9.95s)
**মূল ইংরেজি:** that if you fix one of those scalers and let the other one change its value freely the tip of the resulting Vector draws a straight

**বাংলা ডায়ালগ:** যদি একটি স্কেলারকে স্থির রেখে অন্য স্কেলারের মান মুক্তভাবে পরিবর্তন করা হয়, তবে লব্ধি ভেক্টরের শীর্ষবিন্দু একটি সরলরেখা আঁকে।

---

### [কিউ 22] 208.08s ➔ 217.04s (ব্যাপ্তি: 8.96s)
**মূল ইংরেজি:** line now if you let both scalers range freely and consider every possible Vector that you can get there are two things that can happen for most pairs of

**বাংলা ডায়ালগ:** এখন উভয় স্কেলারকেই যদি মুক্তভাবে পরিবর্তন হতে দেওয়া হয়, তবে দুটি ঘটনা ঘটতে পারে। বেশিরভাগ ভেক্টরজোড়ের ক্ষেত্রে—

---

### [কিউ 23] 217.04s ➔ 224.92s (ব্যাপ্তি: 7.88s)
**মূল ইংরেজি:** vectors you'll be able to reach every possible point in the plane every two-dimensional Vector is within your grasp however in The Unlucky case where

**বাংলা ডায়ালগ:** আপনি সমতলের প্রতিটি বিন্দুতেই পৌঁছাতে পারবেন; পুরো ২ডি তল আপনার হাতের মুঠোয় চলে আসবে। কিন্তু যদি দুর্ভাগ্যের বিষয় এমন ঘটে—

---

### [কিউ 24] 224.92s ➔ 232.96s (ব্যাপ্তি: 8.04s)
**মূল ইংরেজি:** your two original vectors happen to line up the tip of the resulting Vector is limited to just this single line passing through the

**বাংলা ডায়ালগ:** যে আদি ভেক্টর দুটি একই সরলরেখা বরাবর অবস্থান করছে, তবে লব্ধি ভেক্টরের শীর্ষবিন্দু কেবল মূলবিন্দুগামী সেই রেখাটিতেই আটকে থাকবে।

---

### [কিউ 25] 232.96s ➔ 245.00s (ব্যাপ্তি: 12.04s)
**মূল ইংরেজি:** origin actually technically there's a third possibility too both your vectors could be zero in which case you'd just be stuck at the origin here's some more terminology the set of all possible vectors that you can

**বাংলা ডায়ালগ:** অবশ্য তৃতীয় সম্ভাবনাও আছে: উভয় ভেক্টরই শূন্য হলে আপনি শুধুই মূলবিন্দুতে আটকে থাকবেন। এবার একটি পারিভাষিক শব্দ লক্ষ্য করুন: লিনিয়ার কম্বিনেশনের মাধ্যমে—

---

### [কিউ 26] 245.00s ➔ 253.47s (ব্যাপ্তি: 8.47s)
**মূল ইংরেজি:** reach with a linear combination of a given pair of vectors is called the span of those two

**বাংলা ডায়ালগ:** একটি নির্দিষ্ট ভেক্টরজোড় দিয়ে পৌঁছানো যায় এমন সমস্ত সম্ভাব্য ভেক্টরের সেটকেই বলা হয় তাদের স্প্যান (Span)।

---

### [কিউ 27] 253.48s ➔ 263.36s (ব্যাপ্তি: 9.88s)
**মূল ইংরেজি:** vectors so restating what we just saw in this lingo the span of most pairs of 2D vectors is all vectors of 2D space but when they line up their span is all

**বাংলা ডায়ালগ:** সহজ ভাষায়: অধিকাংশ ২ডি ভেক্টরজোড়ের স্প্যান হলো সমগ্র দ্বিমাত্রিক স্থান, কিন্তু তারা সমরেখ হলে তাদের স্প্যান কেবল একটি একক সরলরেখা।

---

### [কিউ 28] 263.36s ➔ 273.00s (ব্যাপ্তি: 9.64s)
**মূল ইংরেজি:** vectors whose tip sit on a certain line remember how I said that linear algebra revolves around vector addition and scalar multiplication well the span

**বাংলা ডায়ালগ:** মনে আছে তো, লিনিয়ার বীজগণিত মূলত আবর্তিত হয় ভেক্টর যোগ ও স্কেলার গুণনকে ঘিরে? স্প্যানের ধারণাটি আসলে ঠিক এই প্রশ্নেরই উত্তর খোঁজে—

---

### [কিউ 29] 273.00s ➔ 281.32s (ব্যাপ্তি: 8.32s)
**মূল ইংরেজি:** of two vectors is basically a way of asking what are all the possible vectors you can reach using only these two fundamental operations vector addition

**বাংলা ডায়ালগ:** যে কেবলমাত্র এই দুটি মৌলিক অপারেশন—ভেক্টর যোগ ও স্কেলার গুণন ব্যবহার করে আপনি কোন কোন ভেক্টরে পৌঁছাতে সক্ষম?

---

### [কিউ 30] 281.32s ➔ 289.80s (ব্যাপ্তি: 8.48s)
**মূল ইংরেজি:** and scalar multiplication this is a good time to talk about how people commonly think about vectors as points it gets really crowded to think about a whole

**বাংলা ডায়ালগ:** এখানে ভেক্টরকে বিন্দু হিসেবে ভাবার বিষয়টি পরিষ্কার করা দরকার। একগাদা ভেক্টরকে একসাথে তীরের মতো আঁকলে দৃশ্যপট ভীষণ ঘিঞ্জি হয়ে পড়ে।

---

### [কিউ 31] 289.80s ➔ 298.00s (ব্যাপ্তি: 8.20s)
**মূল ইংরেজি:** collection of vectors sitting on a line and more crowded still to think about all two dimensional vectors all at once filling up the plane so when dealing

**বাংলা ডায়ালগ:** আর একটি রেখা বা পুরো তলের সমস্ত তীরচিহ্ন একসাথে কল্পনা করা আরও বেশি জটিল। তাই ভেক্টরের বিশাল সংগ্রহের ক্ষেত্রে—

---

### [কিউ 32] 298.00s ➔ 308.48s (ব্যাপ্তি: 10.48s)
**মূল ইংরেজি:** with collections of vectors like this it's common to represent each one with just a point in Space the point at the tip of that Vector where as usual I want you thinking about that Vector with its

**বাংলা ডায়ালগ:** প্রতিটি ভেক্টরকে স্থানে কেবল একটি বিন্দু হিসেবে উপস্থাপন করা হয়—ভেক্টরের শীর্ষবিন্দুটি দিয়ে। যেখানে ভেক্টরের লেজ সর্বদা মূলবিন্দুতেই স্থির থাকে।

---

### [কিউ 33] 308.48s ➔ 319.11s (ব্যাপ্তি: 10.63s)
**মূল ইংরেজি:** tail on the origin that way if you want to think about every possible Vector whose tip sits on a certain line just think about the line

**বাংলা ডায়ালগ:** এতে করে একটি নির্দিষ্ট রেখা বরাবর সমস্ত ভেক্টর নিয়ে ভাবতে চাইলে, সরাসরি কেবল সেই সরলরেখাটির কথাই চিন্তা করা যথেষ্ট।

---

### [কিউ 34] 319.12s ➔ 330.52s (ব্যাপ্তি: 11.40s)
**মূল ইংরেজি:** itself likewise to think about all possible two-dimensional vectors all at once conceptualize each one as the point where its tip sits so in effect what you'll be thinking about is the infinite

**বাংলা ডায়ালগ:** একইভাবে সমগ্র দ্বিমাত্রিক স্থানের সমস্ত ভেক্টরকে একবারে কল্পনা করার জন্য তীর বাদ দিয়ে অসীম সমতল চাদরটির কথা ভাবাই সবচেয়ে সুবিধাজনক।

---

### [কিউ 35] 330.52s ➔ 339.44s (ব্যাপ্তি: 8.92s)
**মূল ইংরেজি:** flat sheet of two-dimensional space itself leaving the arrows out of it in general if you're thinking about a vector on its own think of it as an

**বাংলা ডায়ালগ:** সাধারণ নিয়ম হলো: একটিমাত্র ভেক্টর ভাবলে তীর হিসেবে ভাবুন, আর ভেক্টরের কালেকশন বা স্প্যান ভাবলে শীর্ষবিন্দু হিসেবে ভাবুন।

---

### [কিউ 36] 339.44s ➔ 348.00s (ব্যাপ্তি: 8.56s)
**মূল ইংরেজি:** arrow and if you're dealing with a collection of vectors it's convenient to think of them all as points so for our span example the span of most pairs of

**বাংলা ডায়ালগ:** অতএব বেশিরভাগ ক্ষেত্রে দুটি ভেক্টরের স্প্যান হলো অসীম দ্বিমাত্রিক সমতল, আর তারা সমরেখ হলে তাদের স্প্যান হলো একটি সরলরেখা।

---

### [কিউ 37] 348.00s ➔ 357.55s (ব্যাপ্তি: 9.55s)
**মূল ইংরেজি:** vectors ends up being the entire infinite sheet of two-dimensional space but if they line up their span is just a

**বাংলা ডায়ালগ:** এবার আসুন বিষয়টি ত্রিমাত্রিক স্থানে দেখা যাক।

---

### [কিউ 38] 357.56s ➔ 368.32s (ব্যাপ্তি: 10.76s)
**মূল ইংরেজি:** line the idea of span gets a lot more interesting if we start thinking about vectors in threedimensional space for example if you take two vectors in 3D space that are not pointing in the same

**বাংলা ডায়ালগ:** ত্রিমাত্রিক স্থানে স্প্যানের ধারণাটি দারুণ আকর্ষণীয় রূপ নেয়। ধরুন থ্রিডি স্পেসে দুটি ভেক্টর রয়েছে যারা একই দিকে নির্দেশ করছে না।

---

### [কিউ 39] 368.32s ➔ 377.80s (ব্যাপ্তি: 9.48s)
**মূল ইংরেজি:** direction what does it mean to take their span well their span is the collection of all possible linear combinations of

**বাংলা ডায়ালগ:** তাদের স্প্যান বলতে আসলে কী বোঝায়? তাদের স্প্যান হলো ওই দুটি ভেক্টরের সমস্ত সম্ভাব্য লিনিয়ার কম্বিনেশনের সমষ্টি।

---

### [কিউ 40] 377.80s ➔ 387.00s (ব্যাপ্তি: 9.20s)
**মূল ইংরেজি:** those two vectors meaning all possible vectors you get by scaling each of the two of them in some way and then adding them together you can kind of Imagine

**বাংলা ডায়ালগ:** অর্থাৎ তাদের যথাক্রমে স্কেল করে যোগ করলে যত ভেক্টর পাওয়া সম্ভব। কল্পনা করুন দুটি নব ঘুরিয়ে স্কেলার দুটির মান বদলানো হচ্ছে—

---

### [কিউ 41] 387.00s ➔ 395.04s (ব্যাপ্তি: 8.04s)
**মূল ইংরেজি:** turning two different knobs to change the two SC scalers defining the linear combination adding the scaled vectors and following the tip of the resulting

**বাংলা ডায়ালগ:** আর লব্ধি ভেক্টরের শীর্ষবিন্দুর গতিপথ অনুসরণ করা হচ্ছে।

---

### [কিউ 42] 395.04s ➔ 405.28s (ব্যাপ্তি: 10.24s)
**মূল ইংরেজি:** Vector that tip will Trace out some kind of flat sheet cutting through the origin of three-dimensional space this flat sheet is the span of the two vectors or

**বাংলা ডায়ালগ:** সেই শীর্ষবিন্দুটি ত্রিমাত্রিক স্থানের মধ্য দিয়ে মূলবিন্দুগামী একটি সমতল চাদর বা ফ্ল্যাট শিট এঁকে ফেলবে। এই চাদরটিই হলো তাদের স্প্যান।

---

### [কিউ 43] 405.28s ➔ 413.84s (ব্যাপ্তি: 8.56s)
**মূল ইংরেজি:** more precisely the set of all possible vectors whose tips sit on that flat sheet is the span of your two vectors isn't that a beautiful mental

**বাংলা ডায়ালগ:** নিখুঁতভাবে বললে, এই সমতলের উপর অবস্থিত শীর্ষবিন্দু বিশিষ্ট সমস্ত ভেক্টরের সেটই হলো স্প্যান। অসাধারণ এক দৃশ্য, তাই না?

---

### [কিউ 44] 413.84s ➔ 422.76s (ব্যাপ্তি: 8.92s)
**মূল ইংরেজি:** image so what happens if we add a third vector and consider the span of all three of those guys a linear combination of three vectors is

**বাংলা ডায়ালগ:** এখন যদি আমরা তৃতীয় আরেকটি ভেক্টর যুক্ত করি, তবে এই তিনটি ভেক্টরের স্প্যান কেমন হবে? তিনটি ভেক্টরের লিনিয়ার কম্বিনেশনও একইভাবে সংজ্ঞায়িত—

---

### [কিউ 45] 422.76s ➔ 429.12s (ব্যাপ্তি: 6.36s)
**মূল ইংরেজি:** defined pretty much the same way as it is for two you'll choose three different scalers scale each of those vectors and

**বাংলা ডায়ালগ:** তিনটি স্কেলার বেছে নিয়ে তিনটি ভেক্টরকে গুণ করে পরস্পরের সাথে যোগ করা।

---

### [কিউ 46] 429.12s ➔ 439.88s (ব্যাপ্তি: 10.76s)
**মূল ইংরেজি:** then add them all together and again the span of these vectors is the set of all possible

**বাংলা ডায়ালগ:** এবং আবারও, তাদের স্প্যান হলো সমস্ত সম্ভাব্য লিনিয়ার কম্বিনেশনের সেট।

---

### [কিউ 47] 439.88s ➔ 447.80s (ব্যাপ্তি: 7.92s)
**মূল ইংরেজি:** linear combinations two different things could happen here if your third Vector happens

**বাংলা ডায়ালগ:** এখানে দুটি ভিন্ন সম্ভাবনা তৈরি হয়:

---

### [কিউ 48] 447.80s ➔ 456.36s (ব্যাপ্তি: 8.56s)
**মূল ইংরেজি:** to be sitting on the span of the first two then the span doesn't change you're sort of trapped on that same flat sheet in other words adding a scaled version

**বাংলা ডায়ালগ:** যদি তৃতীয় ভেক্টরটি প্রথম দুটি ভেক্টরের তৈরি সমতলের ভেতরেই অবস্থিত হয়, তবে স্প্যানে কোনো পরিবর্তন আসে না; আপনি ওই একই সমতলে আটকে থাকেন।

---

### [কিউ 49] 456.36s ➔ 463.96s (ব্যাপ্তি: 7.60s)
**মূল ইংরেজি:** of that third Vector to the linear combination doesn't really give you access to any new vectors but if you just randomly choose

**বাংলা ডায়ালগ:** অর্থাৎ তৃতীয় ভেক্টর যোগ করলেও কোনো নতুন মাত্রার দ্বার উন্মোচিত হয় না। কিন্তু আপনি যদি এমন একটি তৃতীয় ভেক্টর নেন—

---

### [কিউ 50] 463.96s ➔ 472.92s (ব্যাপ্তি: 8.96s)
**মূল ইংরেজি:** a third Vector it's almost certainly not sitting on the span of those first two then since it's pointing in a separate Direction it unlocks access to every

**বাংলা ডায়ালগ:** যা ওই সমতলে নেই এবং ভিন্ন দিকে নির্দেশ করছে, তবে তা পুরো ত্রিমাত্রিক স্থানের প্রতিটি বিন্দুতে পৌঁছানোর পথ উন্মুক্ত করে দেয়!

---

### [কিউ 51] 472.92s ➔ 477.36s (ব্যাপ্তি: 4.44s)
**মূল ইংরেজি:** possible three dimensional Vector one way I like to think about this is that

**বাংলা ডায়ালগ:** এটিকে এভাবে ভাবা যেতে পারে—

---

### [কিউ 52] 477.36s ➔ 487.04s (ব্যাপ্তি: 9.68s)
**মূল ইংরেজি:** as you scale that new third vector it moves around that span sheet of the first two sweeping it through all of space another way to think about it is

**বাংলা ডায়ালগ:** তৃতীয় ভেক্টরটি স্কেল করার সাথে সাথে আগের সমতলটিকে পুরো ত্রিমাত্রিক শূন্যে সুইপ করিয়ে দেয়।

---

### [কিউ 53] 487.04s ➔ 495.95s (ব্যাপ্তি: 8.91s)
**মূল ইংরেজি:** that you're making full use of the three freely changing scalers that you have at your disposal to access the full three dimensions of

**বাংলা ডায়ালগ:** যার মাধ্যমে তিনটি স্কেলারের পূর্ণ সদ্ব্যবহার করে ৩টি স্বাধীন মাত্রায় প্রবেশ করা সম্ভব হয়।

---

### [কিউ 54] 495.96s ➔ 504.00s (ব্যাপ্তি: 8.04s)
**মূল ইংরেজি:** space now in the case where the third Vector was already sitting on the span of the first two or the case where two vectors happen to line up we want some

**বাংলা ডায়ালগ:** এখন যে ক্ষেত্রে তৃতীয় ভেক্টরটি আগের সমতলেই অবস্থান করছিল, বা দুটি ভেক্টর পরস্পর সমরেখ ছিল—সেখানে একটি ভেক্টর আসলে অতিরিক্ত বা অপ্রয়োজনীয়।

---

### [কিউ 55] 504.00s ➔ 512.36s (ব্যাপ্তি: 8.36s)
**মূল ইংরেজি:** terminology to describe the fact that at least one of these vectors is redundant not adding anything to our span whenever this happens where you have

**বাংলা ডায়ালগ:** কারণ তা স্প্যানে নতুন কোনো মাত্রা যোগ করছে না। যখন এমন একাধিক ভেক্টর থাকে যাদের যেকোনো একটিকে বাদ দিলেও স্প্যান কমে না—

---

### [কিউ 56] 512.36s ➔ 523.48s (ব্যাপ্তি: 11.12s)
**মূল ইংরেজি:** multiple vectors and you could remove one without reducing the span the relevant terminology is to say that they are linearly dependent another way of phrasing that would be to say that one of the vectors

**বাংলা ডায়ালগ:** তখন সেই ভেক্টরগুলোকে বলা হয় লিনিয়ারলি ডিপেনডেন্ট (Linearly Dependent)। অন্যভাবে বললে, অন্তত একটি ভেক্টরকে বাকিদের লিনিয়ার কম্বিনেশন হিসেবে প্রকাশ করা যায়।

---

### [কিউ 57] 523.48s ➔ 531.87s (ব্যাপ্তি: 8.39s)
**মূল ইংরেজি:** can be expressed as a linear combination of the others since it's already in the span of the

**বাংলা ডায়ালগ:** কারণ এটি ইতোমধ্যে বাকিদের স্প্যানেই অবস্থান করছিল।

---

### [কিউ 58] 531.88s ➔ 546.43s (ব্যাপ্তি: 14.55s)
**মূল ইংরেজি:** others on the other hand if each Vector really does add another dimension to the span they're said to be linearly independent

**বাংলা ডায়ালগ:** পক্ষান্তরে, যদি প্রতিটি ভেক্টরই স্প্যানে নতুন একটি মাত্রা যোগ করে, তবে তাদেরকে বলা হয় লিনিয়ারলি ইনডিপেনডেন্ট (Linearly Independent)।

---

### [কিউ 59] 546.44s ➔ 556.24s (ব্যাপ্তি: 9.80s)
**মূল ইংরেজি:** so with all of that terminology and hopefully with some good mental images to go with it let me leave you with a puzzle before we go the technical definition of a basis of a space is a

**বাংলা ডায়ালগ:** এবার একটি সুন্দর ধাঁধা রেখে যাই: গণিতে কোনো ভেক্টর স্পেসের বেসিসের আনুষ্ঠানিক সংজ্ঞা হলো—

---

### [কিউ 60] 556.24s ➔ 561.00s (ব্যাপ্তি: 4.76s)
**মূল ইংরেজি:** set of linearly independent vectors that span that

**বাংলা ডায়ালগ:** একগুচ্ছ লিনিয়ারলি ইনডিপেনডেন্ট ভেক্টর যারা পুরো স্পেসটিকে স্প্যান করে।

---

### [কিউ 61] 561.00s ➔ 569.92s (ব্যাপ্তি: 8.92s)
**মূল ইংরেজি:** space now given how I described a basis earlier and given your current understanding of the words span and linearly independent think about why

**বাংলা ডায়ালগ:** আমরা যেভাবে বেসিস, স্প্যান ও ইনডিপেনডেন্স ব্যাখ্যা করলাম, তার আলোকে ভাবুন তো: কেন এই সংজ্ঞাটি এত নিখুঁত?

---

### [কিউ 62] 569.92s ➔ 577.88s (ব্যাপ্তি: 7.96s)
**মূল ইংরেজি:** this definition would make sense in the next video I'll get into matrices and transforming space see you

**বাংলা ডায়ালগ:** পরবর্তী ভিডিওতে আমরা ম্যাট্রিক্স এবং স্থানের রূপান্তর নিয়ে বিস্তারিত জানবো।

---

### [কিউ 63] 577.88s ➔ 593.81s (ব্যাপ্তি: 15.93s)
**মূল ইংরেজি:** then

**বাংলা ডায়ালগ:** দেখা হবে পরবর্তী পর্বে। সাথে থাকার জন্য ধন্যবাদ।

---

