import re

path = 'departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/linear_algebra/lesson_01.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update <head> with favicon, narration.css, manifest.js, narration_engine.js
if 'manifest.js' not in text:
    head_search = '<link rel="stylesheet" href="../../assets/css/lesson.css"/>'
    head_replace = '''<link rel="icon" type="image/svg+xml" href="../../assets/images/favicon.svg"/>
<link rel="stylesheet" href="../../assets/css/lesson.css"/>
<link rel="stylesheet" href="../../assets/css/narration.css"/>
<script src="../../assets/audio/linear_algebra/lesson_01/manifest.js"></script>
<script defer src="../../assets/js/narration_engine.js"></script>'''
    text = text.replace(head_search, head_replace)

# 2. Fix chapter-label
text = text.replace('অধ্যায় ১ · লিনিয়ার অ্যালজেব্রার সারমর্ম', 'অধ্যায় ০১ · লিনিয়ার অ্যালজেব্রার সারমর্ম')

# 3. Fix button name
text = text.replace('▶ মূল ইউটিউব', '▶ অরিজিনাল ভিডিও')

# 4. Inject Teacher Narration Top Card and Timestamp Ribbon if missing
if 'bookmark-ribbon' not in text:
    card_marker = '<div class="read-mode">'
    card_html = '''<div class="read-mode">

    <!-- Smart Reading Narration Top Banner -->
    <div class="narration-card fade-up">
      <div class="narration-card-left">
        <div class="narration-icon-box">🎙️</div>
        <div>
          <h4>শিক্ষক অডিও বিবরণ ও লাইভ কারাওকে সহকারী <span class="badge-live">TEACHER VOICE</span></h4>
          <p>দরদী শিক্ষকের কণ্ঠে প্রতিটি অনুচ্ছেদ, গাণিতিক সূত্র ও চিত্র বিবরণ শুনুন — সাথে রিয়েলটাইম হাইলাইটার ও কন্ট্রোল।</p>
        </div>
      </div>
      <div class="narration-card-right">
        <button id="btnListenFullArticle" class="btn-read-full">
          🎙️ শিক্ষকের কণ্ঠে শুনুন
        </button>
      </div>
    </div>

    <!-- Timestamp Bookmarks Ribbon -->
    <div class="bookmark-ribbon fade-up">
      <div class="bookmark-ribbon-title">
        <span>⏱️ অধ্যায়ের টাইমস্ট্যাম্প বুকমার্ক — যেকোনো অংশে সরাসরি জাম্প করুন:</span>
      </div>
      <div class="bookmark-grid">
        <button class="bookmark-chip" onclick="jumpToLessonTime(0, this)">
          <span class="bookmark-time">০০:০০</span>
          <span>ভেক্টরের সূচনা ও মূল দৃষ্টিভঙ্গি</span>
        </button>
        <button class="bookmark-chip" onclick="jumpToLessonTime(65, this)">
          <span class="bookmark-time">০১:০৫</span>
          <span>পদার্থবিদ, সিএস ও গণিতবিদ দৃষ্টিভঙ্গি</span>
        </button>
        <button class="bookmark-chip" onclick="jumpToLessonTime(160, this)">
          <span class="bookmark-time">০২:৪০</span>
          <span>স্থানাঙ্ক ব্যবস্থার পেছনের দর্শন</span>
        </button>
        <button class="bookmark-chip" onclick="jumpToLessonTime(315, this)">
          <span class="bookmark-time">০৫:১৫</span>
          <span>ভেক্টর যোগ — ত্রিভুজ ও সামান্তরিক সূত্র</span>
        </button>
        <button class="bookmark-chip" onclick="jumpToLessonTime(450, this)">
          <span class="bookmark-time">০৭:৩০</span>
          <span>স্কেলার গুণন ও স্ট্রেচিং রহস্য</span>
        </button>
      </div>
    </div>'''
    text = text.replace(card_marker, card_html, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated lesson_01.html successfully!')
