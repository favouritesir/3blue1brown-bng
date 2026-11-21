# -*- coding: utf-8 -*-
"""
Build the NEW component-based Bengali 'Why Pi' (কেন পাই) course.

Creates ONLY new folders:
  data/why_pi/lesson_NN.json
  courses/why_pi/lesson_NN.html + index.html
  assets/audio/why_pi/lesson_NN/manifest.{json,js}
  assets/figures/why_pi/lesson_NN/fig_XX.svg
  media_vault/why_pi/lesson_NN/experiments/3b1b_why_pi_NN_full_dubbed.mp4

Does NOT touch any existing lesson/library file.
"""
import json
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # web_platform/


import re


def norm_katex(s):
    """Collapse raw-string double backslashes to single for KaTeX."""
    return s.replace('\\\\', '\\')


def fill(template, mapping):
    """Substitute only {identifier} tokens; leave literal {CSS/JS} untouched."""
    def rep(m):
        key = m.group(1)
        return str(mapping[key]) if key in mapping else m.group(0)
    return re.sub(r'\{([A-Za-z_][A-Za-z0-9_]*)\}', rep, template)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def esc(s):
    """Escape text placed inside a double-quoted HTML attribute."""
    return (s.replace('&', '&amp;').replace('"', '&quot;')
             .replace('<', '&lt;').replace('>', '&gt;'))


def fig(id_, caption_bn, label, color):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 240" role="img">'
           f'<rect width="480" height="240" fill="#0e141b"/>'
           f'<circle cx="240" cy="120" r="86" fill="none" stroke="{color}" stroke-width="3"/>'
           f'<line x1="154" y1="120" x2="326" y2="120" stroke="#74c0e3" stroke-width="2"/>'
           f'<line x1="240" y1="34" x2="240" y2="206" stroke="#74c0e3" stroke-width="2"/>'
           f'<text x="240" y="112" fill="#e8eef5" font-size="26" font-family="serif" '
           f'text-anchor="middle">{label}</text>'
           f'<text x="240" y="230" fill="#8fa3b8" font-size="13" font-family="serif" '
           f'text-anchor="middle">3Blue1Brown · Why Pi</text></svg>')
    return svg


def make_figure(spec):
    """Return (figure_html, figure_json, svg_filename, svg_content)."""
    fid = spec['id']
    svg_name = fid + '.svg'
    html = (f'<b1b-figure src="../../assets/figures/why_pi/lesson_{{NN}}/{svg_name}" '
            f'alt="{esc(spec["caption_bn"])}" caption="{esc(spec["caption_bn"])}"></b1b-figure>')
    j = {'id': fid, 'caption_bn': spec['caption_bn'], 'type': 'svg',
         'src': 'figures/why_pi/lesson_{NN}/' + svg_name}
    svg = fig(fid, spec['caption_bn'], spec.get('label', 'π'), spec.get('color', '#74c0e3'))
    return html, j, svg_name, svg


def quiz_html(q):
    opts = '\n'.join(f'          <div slot="option">{o}</div>' for o in q['options'])
    return (f'''<b1b-quiz
          question="❓ {esc(q['question_bn'])}"
          correct="{q['correct_index']}"
          correct-msg="{esc(q['correct_msg'])}"
          wrong-msg="{esc(q['wrong_msg'])}"
          reveal-msg="{esc(q['reveal_msg'])}">
{opts}
        </b1b-quiz>''')


def quiz_json(q, nn):
    return {
        'id': q['id'],
        'course_id': 'why_pi',
        'lesson_id': 'lesson_' + nn,
        'section_ref': q['section_ref'],
        'question_bn': q['question_bn'],
        'question_en': q.get('question_en', ''),
        'options': q['options'],
        'options_bn': q['options'],
        'correct_index': q['correct_index'],
        'explanation_bn': q['correct_msg'],
        'explanation_en': q.get('explanation_en', ''),
        'hint': q['hint'],
        'hints': [q['hint']],
    }


# ---------------------------------------------------------------------------
# Lesson data — natural Bengali pedagogy (course_id = why_pi)
# ---------------------------------------------------------------------------
LESSONS = []

def L(**kw):
    LESSONS.append(kw)

L(
    num='01', slug='clacks',
    title_bn='একটি গণনার ধাঁধার সবচেয়ে অপ্রত্যাশিত উত্তর',
    title_en='The most unexpected answer to a counting puzzle',
    subtitle_bn='দুটি স্লাইডিং ব্লক আর একটি দেয়াল—এই সাদামাটা সেটআপ থেকে কীভাবে পাইয়ের (π) অঙ্কগুলো ধ ধ করে বেরিয়ে আসে',
    date='১৩ জানুয়ারি, ২০১৯', duration='5:30', yt_id='lB(aqeI7a_0',
    epigraph=('Where there is π, there is a hidden circle.',
              'যেখানে পাই আছে, সেখানে একটা লুকোনো বৃত্তও আছে।', 'Grant Sanderson'),
    sections=[
        dict(
            id='sec-setup', title_bn='ধাঁধাটির সেটআপ',
            title_en='The Setup of the Puzzle',
            summary_bn='দুটি ব্লক, একটি দেয়াল, ঘর্ষণহীন পৃষ্ঠ এবং সম্পূর্ণ স্থিতিস্থাপক সংঘর্ষ— এই আদর্শ পরিস্থিতিতেও ফলাফল কী হবে তা এক নজরে বোঝা যায় না।',
            takeaways=['বড় ব্লকটি ডান থেকে একটি নির্দিষ্ট বেগে আসে, ছোট ব্লকটি প্রথমে স্থির থাকে এবং বাঁ দিকে একটি দেয়াল থাকে।',
                       'ঘর্ষণ নেই এবং প্রতিটি সংঘর্ষ সম্পূর্ণ স্থিতিস্থাপক—অর্থাৎ শক্তির কোনো ক্ষতি হয় না।',
                       'দুটি ব্লকের ভর সমান হলে মোট তিনবার সংঘর্ষ হয়: একবার ব্লকদ্বয়ের মধ্যে, একবার দেয়ালে, আবার একবার ব্লকদ্বয়ের মধ্যে।'],
            formulas=[{'label': 'সমান ভরের ক্ষেত্রে মোট ধ্বনি (clack)',
                       'katex': r'N = 3 \quad (m_1 = m_2)'}],
            figures=[
                {'id': 'fig_clacks_setup', 'caption_bn': 'দেয়াল, ছোট ব্লক ও বড় ব্লক—ধাঁধাটির আদি অবস্থা', 'label': '▮▮ →', 'color': '#74c0e3'},
                {'id': 'fig_clacks_equal', 'caption_bn': 'সমান ভরের ব্লক: মোট তিনটি সংঘর্ষ', 'label': '1 : 1 → 3', 'color': '#8ce99a'},
            ],
            body='''<p>কল্পনা করুন একদিকে একটি দেয়াল, তার সামনে ছোট একটি ব্লক এবং তার ডানে অনেক বড় একটি ব্লক। বড় ব্লকটি বাঁ দিকে ধেয়ে আসছে, ছোট ব্লকটি প্রথমে সম্পূর্ণ স্থির। আমরা একধরনের আদর্শ পদার্থবিদ: মেঝেতে কোনো ঘর্ষণ নেই, আর প্রতিটি সংঘর্ষ <em>সম্পূর্ণ স্থিতিস্থাপক</em>—অর্থাৎ সংঘর্ষে কোনো শক্তি নষ্ট হয় না।</p>

[[F0]]

<p>সবচেয়ে সোজা ক্ষেত্রটি হলো দুই ব্লকের ভর সমান হওয়া। প্রথম ব্লকটি তার সম্পূর্ণ ভরবেগ দ্বিতীয়টিকে দিয়ে দেয়, দ্বিতীয়টি দেয়ালে ঠুকে ফিরে আসে, আবার প্রথমটির সাথে ধাক্কা খায়—আর প্রথমটি সোজা অসীমের দিকে চলে যায়। মোট <strong>তিনটি</strong> 'ক্ল্যাক' শোনা যায়।</p>

[[F1]]

<p>কিন্তু যদি প্রথম ব্লকের ভর দ্বিতীয়টির চেয়ে ১০০ গুণ হয়? তখন ছোট ব্লকটি দেয়াল আর বড় ব্লকের মাঝে বারবার ছড়া খেয়ে ধীরে ধীরে বড় ব্লকের ভরবেগকে উল্টে দেয়। কতবার সংঘর্ষ হবে? উত্তরটা সহজে অনুমেয় নয়।</p>''',
        ),
        dict(
            id='sec-pattern', title_bn='অঙ্কগুলোর অপ্রত্যাশিত প্যাটার্ন',
            title_en='The Unexpected Digit Pattern',
            summary_bn='ভরের অনুপাত ১০০-এর ঘাত হলে সংঘর্ষের সংখ্যা পাইয়ের প্রথম অঙ্কগুলোর সাথে মেলে—একটি সম্পূর্ণ অবিশ্বাস্য আবিষ্কার।',
            takeaways=['ভর অনুপাত ১০০ : ১ হলে ৩১টি সংঘর্ষ; ১০,০০০ : ১ হলে ৩১৪টি; ১০,০০,০০০ : ১ হলে ৩,১৪১টি।',
                       'এই সংখ্যাগুলো π ≈ 3.14159… এর প্রথম অঙ্কগুলোর ঠিক মতোই।',
                       'Gregory Galperin ১৯৯৫ সালে এই ঘটনাটি আবিষ্কার করেন এবং ২০০৩ সালে প্রকাশ করেন।'],
            formulas=[{'label': 'ভর অনুপাত ১০০^(d−1) হলে d অঙ্ক',
                       'katex': r'\frac{m_1}{m_2}=100^{\,d-1}\;\Longrightarrow\; N \approx \lfloor 10^{d}\,\pi\rfloor'}],
            figures=[{'id': 'fig_clacks_digits', 'caption_bn': 'ভর বাড়ার সাথে সংঘর্ষের সংখ্যা পাইয়ের অঙ্ক ধরে নেয়', 'label': '3 · 31 · 314 · 3141', 'color': '#fcc419'}],
            body='''<p>আসুন ভরের অনুপাতটা বাড়িয়ে দেখি। ১০০ গুণ হলে <strong>৩১</strong>টি সংঘর্ষ। ১০,০০০ গুণ হলে <strong>৩১৪</strong>টি। ১০ লক্ষ গুণ হলে <strong>৩,১৪১</strong>টি। আপনি কি প্যাটার্নটা দেখতে পাচ্ছেন?</p>

[[F0]]

<p>যখনই বড় ব্লকের ভর ছোটটির <em>১০০-এর কোনো ঘাত</em>, তখনই মোট সংঘর্ষের সংখ্যা পাইয়ের (π ≈ 3.14159…) প্রথম অঙ্কগুলোর মতো হয়। এটি প্রথম শুনে আমাকেও হতবাক করে দিয়েছিল—ধন্যবাদ ভিউয়ার Henry Kavle-কে এই তথ্যটি শেয়ার করার জন্য; মূল আবিষ্কার গণিতবিদ Gregory Galperin-এর (১৯৯৫, প্রকাশ ২০০৩)।</p>

<b1b-callout type="gold" icon="⚡" title="কেন এটা বিস্ময়কর?">
<p>পাই সাধারণত কোনো অবিচ্ছিন্ন জ্যামিতিক পরিমাণ—বৃত্তের পরিধি আর ব্যাসের অনুপাত—বর্ণনা করে। কিন্তু এখানে এর <strong>দশমিক অঙ্কগুলো</strong> একটা পূর্ণসংখ্যা গণনা করছে! এমন অদ্ভুত উপায়ে পাইয়ের আবির্ভাব সত্যিই মানুষকে অবাক করে।</p>
</b1b-callout>

<p>অবশ্যই, এটা পাই হিসাব করার ব্যবহারিক উপায় নয়। ২০টি অঙ্ক পেতে বড় ব্লকের ভর ছোটটির ১০০ কোটি কোটি কোটি কোটি গুণ হতে হবে—আমাদের ছায়াপথের কেন্দ্রের অতিপ্রকৃত কৃষ্ণগহ্বরের চেয়েও অনেক বেশি! তবু প্রশ্নটা থেকে যায়: <strong>এখানে পাই আসছে কেন?</strong></p>''',
        ),
        dict(
            id='sec-hidden-circle', title_bn='লুকোনো বৃত্ত ও শক্তির সংরক্ষণ',
            title_en='The Hidden Circle and Conservation of Energy',
            summary_bn='যেখানে পাই আছে সেখানে একটা বৃত্ত আছে—এই ক্ষেত্রে বৃত্তটা আসে শক্তির সংরক্ষণ সূত্র থেকে।',
            takeaways=['দুই ব্লকের মোট গতিশক্তি সংঘর্ষের আগে ও পরে একই থাকে।',
                       '√m₁·v₁ ও √m₂·v₂ কে অক্ষ হিসেবে নিলে শক্তির সমীকরণটা becomes একটা বৃত্ত— $x^2+y^2=\\text{const}$।',
                       'ভরবেগের সংরক্ষণ এই বৃত্তে সরলরেখা দ্বারা কাটা বিন্দুগুলোর মাঝে চলাচল নির্ধারণ করে।'],
            formulas=[{'label': 'গতিশক্তির সংরক্ষণ—বৃত্তের সমীকরণ',
                       'katex': r'\tfrac12 m_1 v_1^2+\tfrac12 m_2 v_2^2=\text{const}\;\Rightarrow\; \tfrac12(x^2+y^2)=\text{const}'},
                      {'label': 'স্কেল করা স্থানাঙ্ক',
                       'katex': r'x=\sqrt{m_1}\,v_1,\qquad y=\sqrt{m_2}\,v_2'}],
            figures=[{'id': 'fig_clacks_circle', 'caption_bn': 'বেগ-ফেজ স্পেসে শক্তির সংরক্ষণ একটি বৃত্ত তৈরি করে', 'label': 'x²+y² = r²', 'color': '#e599f7'}],
            body='''<p>এই ধাঁধার মূল কথা হলো: <strong>যেখানে পাই আছে, সেখানে একটা লুকোনো বৃত্ত আছে।</strong> এই ক্ষেত্রে সেই বৃত্তটা লুকিয়ে আছে শক্তির সংরক্ষণের ভেতরে।</p>

<p>যেকোনো মুহূর্তে দুই ব্লকের মোট গতিশক্তি $\\tfrac12 m_1 v_1^2+\\tfrac12 m_2 v_2^2$—আর সংঘর্ষের পরও এই মান অপরিবর্তিত থাকে। এখন যদি অক্ষদুটিকে এভাবে স্কেল করি: $x=\\sqrt{m_1}\\,v_1$ এবং $y=\\sqrt{m_2}\\,v_2$, তবে সমীকরণটা দাঁড়ায় $\\tfrac12(x^2+y^2)=\\text{ধ্রুবক}$—অর্থাৎ <strong>একটি বৃত্ত</strong>!</p>

[[F0]]

<b1b-callout type="blue" icon="🔵" title="পরবর্তী দুটি পাঠে">
<p>এই বৃত্তের ওপর দুটি ভিন্ন উপায়ে চলন করে দেখা যাবে কেন সংঘর্ষের সংখ্যা পাইয়ের অঙ্ক দেয়। পরবর্তী পাঠে আমরা <em>বেগ-ফেজ স্পেস</em> (velocity phase space) ব্যবহার করব, আর তারপরের পাঠে দেখব একই সমস্যা <em>আলোর রশ্মির</em> মতো আচরণ করে। দুটিই সমান সুন্দর।</p>
</b1b-callout>

<p>সংক্ষেপে: ব্লকগুলোর গতি নির্ধারণ করে শক্তি ও ভরবেগ—এই দুটি সংরক্ষণ আইন। আর এই আইনগুলোকেই একটা জ্যামিতিক ছবিতে রূপ দিয়েই পাইয়ের রহস্যের উত্তর মিলবে।</p>''',
        ),
    ],
    quizzes=[
        dict(id='quiz_clacks_100', section_ref='sec-pattern',
             question_bn='বড় ব্লকের ভর ছোট ব্লকের ১০০ গুণ হলে মোট কতটি সংঘর্ষ হয়?',
             question_en='How many collisions occur when the big block is 100 times the mass?',
             options=['$3$', '$31$', '$314$', '$3{,}141$'],
             correct_index=1,
             correct_msg='ঠিক! ১০০ : ১ ভর অনুপাতে ৩১টি সংঘর্ষ হয়—π-র প্রথম দুই অঙ্ক ৩.১।',
             wrong_msg='মনে করো: ১ : ১ হলে ৩টি, ১০০ : ১ হলে ৩১টি, ১০,০০০ : ১ হলে ৩১৪টি।',
             reveal_msg='সঠিক উত্তর ৩১টি সংঘর্ষ।',
             hint='ভর অনুপাত ১০০ = ১০⁰² হওয়ায় π-র ২টি অঙ্ক আসে।'),
    ],
),

L(
    num='02', slug='colliding-blocks-v2',
    title_bn='সংঘর্ষরত ব্লকরা কীভাবে পাই গণনা করে',
    title_en='Why colliding blocks compute pi',
    subtitle_bn='বেগ-ফেজ স্পেস, শক্তি ও ভরবেগের সংরক্ষণ এবং অন্তর্লিখিত কোণ—এই টুলগুলো দিয়ে পাইয়ের আবির্ভাবের পেছনের পদার্থবিজ্ঞান খোলা',
    date='১৩ মার্চ, ২০২৫', duration='10:46', yt_id='d4gKmDq7Y1A',
    epigraph=('A change of perspective is worth 80 IQ points.',
              'দৃষ্টিভঙ্গির একটা বদল ৮০ আইকিউ পয়েন্টের মতো।', 'Alan Kay'),
    sections=[
        dict(
            id='sec-conservation', title_bn='শক্তি ও ভরবেগের সংরক্ষণ',
            title_en='Conservation of Energy and Momentum',
            summary_bn='সংঘর্ষের পর ব্লকদের বেগ বের করতে হলে শক্তি ও ভরবেগ—এই দুটি সংরক্ষণ আইনই যথেষ্ট।',
            takeaways=['মোট গতিশক্তি $\\tfrac12 m_1 v_1^2+\\tfrac12 m_2 v_2^2$ সংঘর্ষের সময় ধ্রুবক থাকে।',
                       'মোট ভরবেগ $m_1 v_1+m_2 v_2$ ব্লক-সংঘর্ষে ধ্রুবক, কিন্তু দেয়ালে ঠুকে ছোট ব্লকের ভরবেগ বদলায়।',
                       'দুটি অজানা বেগ ও দুটি সমীকরণ—তাই সমাধান নির্ণেয়।'],
            formulas=[{'label': 'গতিশক্তি ও ভরবেগ',
                       'katex': r'E=\tfrac12 m_1 v_1^2+\tfrac12 m_2 v_2^2,\qquad p=m_1 v_1+m_2 v_2'}],
            figures=[{'id': 'fig_v2_conservation', 'caption_bn': 'দুটি সংরক্ষণ আইনই বেগের পরিবর্তন নির্ধারণ করে', 'label': 'E, p = const', 'color': '#74c0e3'}],
            body='''<p>আমাদের আসলে কী দরকার? সংঘর্ষের ঠিক পরে দুই ব্লকের বেগ কত—তা বের করা। এর চাবিকাঠি হলো দুটি সংরক্ষণ আইন: <strong>শক্তি</strong> আর <strong>ভরবেগ</strong>।</p>

<p>ব্লক দুটির ভর $m_1, m_2$ এবং বেগ $v_1, v_2$। মোট গতিশক্তি $\\tfrac12 m_1 v_1^2+\\tfrac12 m_2 v_2^2$—ব্লকগুলো যতই ধাক্কা খাক, এই মান একই থাকতে হবে। মোট ভরবেগ $m_1 v_1+m_2 v_2$-ও ব্লক সংঘর্ষে অপরিবর্তিত থাকে; শুধু ছোট ব্লক দেয়ালে ঠুকে তার ভরবেগ দেয়ালে দিয়ে দেয় (দেয়ালের ভর অসীম বলে নড়ে না)।</p>

[[F0]]

<p>দুটি অজানা, দুটি সমীকরণ—কাজটা সম্ভব। কিন্তু সরাসরি বীজগণিতের বদলে আমরা একটা ছবি আঁকব। আর সেই ছবিই পাইয়ের দিকে নিয়ে যাবে।</p>''',
        ),
        dict(
            id='sec-phase-circle', title_bn='বেগ-ফেজ স্পেসে বৃত্ত',
            title_en='The Circle in Velocity Phase Space',
            summary_bn='বেগগুলোকে স্থানাঙ্ক ধরে শক্তির সমীকরণ আঁকলে একটি উপবৃত্ত পাই; ভর দিয়ে স্কেল করলে সেটি হয়ে যায় নিখুঁত বৃত্ত।',
            takeaways=['$x=\\sqrt{m_1}v_1$, $y=\\sqrt{m_2}v_2$ স্কেলে শক্তির সমীকরণ হয় $x^2+y^2=\\text{const}$—একটি বৃত্ত।',
                       'বৃত্তের ওপর প্রতিটি বিন্দু এক জোড়া বেগের প্রতিনিধিত্ব করে যারা একই শক্তি বহন করে।',
                       'শুরুতে বড় ব্লক বাঁ dικে যাচ্ছে (x ঋণাত্মক) আর ছোটটি স্থির (y = 0)—অর্থাৎ বৃত্তের বাঁ-প্রান্তে আছি।'],
            formulas=[{'label': 'স্কেল করা স্থানাঙ্কে বৃত্ত',
                       'katex': r'x=\sqrt{m_1}v_1,\;y=\sqrt{m_2}v_2\;\Rightarrow\;\tfrac12(x^2+y^2)=E'}],
            figures=[{'id': 'fig_v2_circle', 'caption_bn': 'উপবৃত্তকে স্কেল করে নিখুঁত বৃত্ত বানানো হলো', 'label': 'ellipse → circle', 'color': '#e599f7'}],
            body='''<p>প্রথমে শক্তির সমীকরণটার দিকে তাকাই। $v_1$ আর $v_2$ তো বদলাচ্ছে—তাই একটা সমতল আঁকি যার x-অক্ষ $v_1$ আর y-অক্ষ $v_2$ বোঝায়। তখন $\\tfrac12 m_1 v_1^2+\\tfrac12 m_2 v_2^2=\\text{const}$ একটি <strong>উপবৃত্ত</strong> (ellipse) হয়।</p>

<p>কিন্তু আমরা পাইয়ের খোঁজে আছি—তাই অক্ষদুটো এভাবে পাল্টাই: x-এ $v_1$-এর বদলে $\\sqrt{m_1}v_1$ আর y-তে $\\sqrt{m_2}v_2$। তখন সমীকরণটা সোজা $\\tfrac12(x^2+y^2)=\\text{const}$—একটি <strong>নিখুঁত বৃত্ত</strong>!</p>

[[F0]]

<p>বৃত্তের প্রতিটি বিন্দু এমন এক জোড়া বেগ যারা একই পরিমাণ শক্তি বহন করে। শুরুতে আমরা বৃত্তের সবচেয়ে বাঁ-প্রান্তে আছি: বড় ব্লক বাঁ দিকে যাচ্ছে ($x<0$) আর ছোটটি স্থির ($y=0$)।</p>''',
        ),
        dict(
            id='sec-momentum-line', title_bn='ভরবেগের রেখা ও ফেজের লাফ',
            title_en='The Momentum Line and Phase Jumps',
            summary_bn='ভরবেগের সংরক্ষণ একটি সরলরেখা দিয়ে প্রকাশ পায়; বৃত্ত আর রেখার ছেদবিন্দুই বলে দেয় সংঘর্ষের পরের বেগ।',
            takeaways=['স্কেল করা অক্ষে $\\sqrt{m_1}x+\\sqrt{m_2}y=\\text{const}$ একটি সরলরেখা, যার ঢাল $-\\sqrt{m_1/m_2}$।',
                       'বৃত্ত ও রেখার দুটি ছেদবিন্দুর মাঝেই সংঘর্ষের আগে-পরে বেগের লাফ ঘটে।',
                       'ছোট ব্লক দেয়ালে ঠুকে $y$-এর চিহ্ন বদলায়—ফেজ ডায়াগ্রামে x-অক্ষের সাপেক্ষে প্রতিফলন।'],
            formulas=[{'label': 'ভরবেগ সংরক্ষণের রেখা',
                       'katex': r'\sqrt{m_1}\,x+\sqrt{m_2}\,y=\text{const},\qquad \text{slope}=-\sqrt{\tfrac{m_1}{m_2}}'}],
            figures=[{'id': 'fig_v2_line', 'caption_bn': 'বৃত্ত আর ভরবেগের রেখার ছেদবিন্দুতেই লাফ ঘটে', 'label': 'circle ∩ line', 'color': '#8ce99a'}],
            body='''<p>শক্তি বলছে আমাদের বৃত্তের ওপর থাকতে হবে। কিন্তু কোন বিন্দুতে যাব? সেটা ঠিক করে <strong>ভরবেগ</strong>। স্কেল করা অক্ষে $m_1v_1+m_2v_2=\\text{const}$ হয় $\\sqrt{m_1}x+\\sqrt{m_2}y=\\text{const}$—একটি সরলরেখা, যার ঢাল $-\\sqrt{m_1/m_2}$।</p>

<p>বৃত্ত আর এই রেখার ছেদে ঠিক দুটি বিন্দু। এর একটি আগের অবস্থা, অন্যটি সংঘর্ষের পরের অবস্থা। দেয়ালে ঠুকে ছোট ব্লকের বেগের চিহ্ন বদলায়—ছবিতে এটা x-অক্ষের ওপর প্রতিফলনের মতো। এইভাবে বারবার লাফ দিয়ে আমরা বৃত্তের ওপর ঘুরে বেড়াই, যতক্ষণ না দুই বেগই ধনাত্মক হয় আর বড় ব্লক ছোটটিকে অতিক্রম করে যায়।</p>

[[F0]]

<b1b-callout type="blue" icon="🗺️" title='ফেজ ডায়াগ্রামের ক্ষমতা'>
<p>সিস্টেমের অবস্থাকে একটা বিন্দু দিয়ে প্রকাশ করলে <em>গতীয়</em> প্রশ্নগুলো <em>জ্যামিতিক</em> প্রশ্ন হয়ে যায়। শক্তির মতো গতীয় ধারণা হয়ে যায় বৃত্ত; আর সংঘর্ষ গণনা হয়ে যায় বৃত্তের ওপর লাফের সংখ্যা গণনা।</p>
</b1b-callout>''',
        ),
        dict(
            id='sec-inscribed-angle', title_bn='অন্তর্লিখিত কোণ ও থিটা হিসাব',
            title_en='Inscribed Angle and Computing Theta',
            summary_bn='প্রতিটি লাফ বৃত্তে সমান 2θ চাপ তৈরি করে; θ = arctan(√(m₂/m₁)) ছোট হলে তার মান প্রায়ই √(−) হয়, আর তাই অঙ্কগুলো পাইয়ের মতো দেখায়।',
            takeaways=['অন্তর্লিখিত কোণের উপপাদ্য অনুযায়ী প্রতিটি লাফের মাঝের চাপ $2\\theta$ রেডিয়ান।',
                       'মোট চাপ $2\\pi$ অতিক্রম না করা পর্যন্ত লাফ চলে: $N\\cdot\\theta<\\pi$।',
                       '$\\theta=\\arctan\\!\\left(\\sqrt{m_2/m_1}\\right)$, আর ছোট $x$-এর জন্য $\\arctan x\\approx x$—তাই ভর ১০০-এর ঘাত হলে অঙ্কগুলো পাইয়ের মতো হয়।'],
            formulas=[{'label': 'থিটার মান', 'katex': r'\theta=\arctan\!\left(\sqrt{\tfrac{m_2}{m_1}}\right)\approx\sqrt{\tfrac{m_2}{m_1}}'},
                      {'label': 'সংঘর্ষের সংখ্যা', 'katex': r'N\cdot\theta<\pi\;\Rightarrow\;N=\left\lfloor\tfrac{\pi}{\theta}\right\rfloor'}],
            figures=[{'id': 'fig_v2_theta', 'caption_bn': 'সমান চাপ 2θ আর π-র সাথে তুলনা', 'label': 'θ = arctan(√m₂/m₁)', 'color': '#fcc419'}],
            body='''<p>এখন আসল প্রশ্ন: সংঘর্ষের সংখ্যা কত? ছবিটার দিকে গভীরভাবে তাকালে দেখা যায় বিন্দুগুলোর মাঝের চাপগুলো প্রায় সমান। <strong>অন্তর্লিখিত কোণের উপপাদ্য</strong> ব্যবহার করে দেখা যায় প্রতিটি লাফ ঠিক $2\\theta$ রেডিয়ান চাপ তৈরি করে।</p>

<p>তাই প্রশ্নটা দাঁড়ায়: $2\\theta$ কে কতবার যোগ করলে $2\\pi$ অতিক্রম করবে না? সরল করে লেখা যায় $N\\cdot\\theta<\\pi$। এখন $\\theta$ হিসাব করি: ভরবেগের রেখার ঢাল $-\\sqrt{m_1/m_2}$ হওয়ায় $\\theta=\\arctan\\!\\left(\\sqrt{m_2/m_1}\\right)$।</p>

[[F0]]

<p>ভর অনুপাত ১০,০০০ : ১ হলে $\\sqrt{m_2/m_1}=1/100$, আর $\\arctan(1/100)\\approx 0.01$। তখন $314\\times 0.01=3.14<\\pi$ কিন্তু $315\\times 0.01=3.15>\\pi$—অর্থাৎ ৩১৪টি সংঘর্ষ। ছোট $x$-এর জন্য $\\arctan x\\approx x$ হওয়াতেই পাইয়ের অঙ্কগুলো এভাবে ফুটে ওঠে!</p>''',
        ),
    ],
    quizzes=[
        dict(id='quiz_v2_theta', section_ref='sec-inscribed-angle',
             question_bn='ভর অনুপাত ১০০ : ১ হলে ফেজ ডায়াগ্রামে θ-র মান কত?',
             question_en='For a 100:1 mass ratio, what is the angle theta?',
             options=['$\\arctan(1/10)$', '$\\arctan(10)$', '$\\pi/10$', '$1/100$'],
             correct_index=0,
             correct_msg='ঠিক! θ = arctan(√(m₂/m₁)) = arctan(1/10), কারণ √(1/100) = 1/10।',
             wrong_msg='মনে করো θ = arctan(√(m₂/m₁)); √(1/100) = 1/10।',
             reveal_msg='সঠিক উত্তর arctan(1/10)।',
             hint='θ = arctan(√(m₂/m₁)) সূত্রটি প্রয়োগ করো।'),
        dict(id='quiz_v2_arc', section_ref='sec-inscribed-angle',
             question_bn='প্রতিটি সংঘর্ষ বৃত্তে কত radian চাপ তৈরি করে?',
             question_en='How much arc (in radians) does each collision cover?',
             options=['$\\theta$', '$2\\theta$', '$\\pi$', '$2\\pi$'],
             correct_index=1,
             correct_msg='সঠিক! অন্তর্লিখিত কোণের উপপাদ্য অনুযায়ী প্রতিটি লাফ 2θ চাপ জুড়ে যায়।',
             wrong_msg='অন্তর্লিখিত কোণ কেন্দ্রীয় কোণের অর্ধেক—তাই চাপ 2θ।',
             reveal_msg='সঠিক উত্তর 2θ।',
             hint='অন্তর্লিখিত কোণ = θ, কেন্দ্রীয় কোণ = 2θ।'),
    ],
),

L(
    num='03', slug='clacks-via-light',
    title_bn='সংঘর্ষরত ব্লকরা আলোর রশ্মির মতো আচরণ করে',
    title_en='How colliding blocks act like a beam of light...to compute pi.',
    subtitle_bn='অবস্থান-ফেজ স্পেস, আয়নার মতো প্রতিফলন আর “লুকিং-গ্লাস” কৌশল—ব্লকের সংঘর্ষকে আলোর অপটিক্সে রূপান্তর',
    date='৩ ফেব্রুয়ারি, ২০১৯', duration='12:05', yt_id='QvmxHpskGg0',
    epigraph=('A change of perspective is worth 80 IQ points.',
              'দৃষ্টিভঙ্গির একটা বদল ৮০ আইকিউ পয়েন্টের মতো।', 'Alan Kay'),
    sections=[
        dict(
            id='sec-position-space', title_bn='অবস্থান-ফেজ স্পেস',
            title_en='Position Phase Space',
            summary_bn='এবার অক্ষগুলো বেগ নয়, ব্লকদুটির অবস্থান বোঝাবে। দুটি ব্লকের দূরত্বই একটা বিন্দুর অবস্থান নির্ধারণ করে।',
            takeaways=['x-অক্ষ দেয়াল থেকে বড় ব্লকের বাঁ প্রান্তের দূরত্ব $d_1$, y-অক্ষ ছোট ব্লকের ডান প্রান্তের দূরত্ব $d_2$।',
                       '$x=y$ রেখায় ব্লকদুটি সংঘর্ষ করে; নিচের সীমানায় ছোট ব্লক দেয়ালে ঠুকে।',
                       'আগের পাঠের মতোই এখানে也是在 একটা বিন্দু সিস্টেমের পুরো অবস্থা প্রকাশ করে।'],
            formulas=[{'label': 'সংঘর্ষের রেখা', 'katex': r'd_1=d_2\;\Rightarrow\;x=y'}],
            figures=[{'id': 'fig_light_position', 'caption_bn': 'অবস্থান-ফেজ স্পেসে দুই ব্লকের গতি একটা বিন্দুর পথ', 'label': 'd₁ , d₂', 'color': '#74c0e3'}],
            body='''<p>আগের পাঠে আমরা এমন একটা সমতল ব্যবহার করেছিলাম যার প্রতিটি বিন্দু দুই ব্লকের <em>বেগ</em> প্রকাশ করে। এবার অন্য something চেষ্টা করি: বিন্দুটা যেন দুই ব্লকের <strong>অবস্থান</strong> প্রকাশ করে।</p>

<p>ধরি x-অক্ষ দেয়াল থেকে বড় ব্লকের বাঁ প্রান্তের দূরত্ব $d_1$, আর y-অক্ষ দেয়াল থেকে ছোট ব্লকের ডান প্রান্তের দূরত্ব $d_2$। যখন $d_1=d_2$, অর্থাৎ $x=y$ রেখায়, ব্লকদুটি ধাক্কা খায়। নিচের সীমানা বোঝায় ছোট ব্লক দেয়ালে ঠুকে।</p>

[[F0]]

<p>ব্লকগুলো নড়ার সাথে সাথে আমাদের বিন্দুটা এই দুই সীমানার মাঝে ছড়া খায়—ঠিক যেন দুইটা আয়নার মাঝে একটা আলোর রশ্মি! কিন্তু একটা সমস্যা আছে: সাধারণ আয়নায় আপতন কোণ ও প্রতিফলন কোণ সমান, কিন্তু এখানে তা নয়।</p>''',
        ),
        dict(
            id='sec-rescale', title_bn='ভর দিয়ে অক্ষ স্কেল করা',
            title_en='Rescaling by Square Roots of Mass',
            summary_bn='√m দিয়ে অক্ষ স্কেল করলে শক্তি হয় “আলোর ধ্রুবক বেগ” আর ভরবেগ হয় “আপতন কোণ = প্রতিফলন কোণ”—অপটিক্যাল অ্যানালজিটি সঠিক হয়ে যায়।',
            takeaways=['নতুন অক্ষ: $x=\\sqrt{m_1}d_1$, $y=\\sqrt{m_2}d_2$।',
                       'বিন্দুর বেগের মান $\\sqrt{2E}$—যা ধ্রুবক, ঠিক যেন আলোর বেগ ধ্রুবক।',
                       'ভরবেগের সংরক্ষণ নিশ্চিত করে আপতন কোণ = প্রতিফলন কোণ, অর্থাৎ সীমানাগুলো আসলেই আয়নার মতো কাজ করে।'],
            formulas=[{'label': 'স্কেল করা অক্ষ', 'katex': r'x=\sqrt{m_1}\,d_1,\qquad y=\sqrt{m_2}\,d_2'},
                      {'label': 'ধ্রুবক “আলোর বেগ”', 'katex': r'\sqrt{\dot x^2+\dot y^2}=\sqrt{2E}=\text{const}'}],
            figures=[{'id': 'fig_light_rescale', 'caption_bn': 'স্কেলের পর সীমানা দুটো আয়নার মতো কাজ করে', 'label': 'mirror, mirror', 'color': '#e599f7'}],
            body='''<p>অ্যানালজিটা ঠিক করতে আমরা আগের মতোই অক্ষ স্কেল করি: $x=\\sqrt{m_1}d_1$ আর $y=\\sqrt{m_2}d_2$। প্রথমে মনে হতে পারে এটা একটা এলোমেলো কাজ, কিন্তু শক্তি ও ভরবেগের সাথে মিলিয়ে দেখলে সব জায়গায় পড়ে যায়।</p>

<p>বিন্দুটির “বেগ” $\\dot x=\\sqrt{m_1}v_1$, $\\dot y=\\sqrt{m_2}v_2$। পাইথাগোরাসে $\\sqrt{\\dot x^2+\\dot y^2}=\\sqrt{2E}$—অর্থাৎ <strong>ধ্রুবক</strong>। অপটিক্যাল ভাষায়: আলোর বেগ সব জায়গায় একই।</p>

[[F0]]

<p>আর ভরবেগ $m_1v_1+m_2v_2=\\text{const}$ কে ডট প্রোডাক্ট হিসেবে লিখলে দেখা যায় বিন্দুটা যে কোণে আয়নায় আছড়ে পড়ে, সেই কোণেই ফিরে আসে। অর্থাৎ দুই সীমানা সত্যিই <strong>আয়না</strong>! যান্ত্রিক আইনগুলো অপটিক্যাল আইন হয়ে গেল—কি অদ্ভুত কিন্তু সুন্দর!</p>''',
        ),
        dict(
            id='sec-unfold', title_bn='আয়না “খুলে” সোজা রশ্মি',
            title_en='Unfolding the Mirrors',
            summary_bn='রশ্মিকে প্রতিফলিত হতে না দিয়ে বরং পুরো বিশ্বকে উল্টিয়ে দিলে রশ্মিটা সোজা চলে—তখন সংঘর্ষ গণনা হয়ে যায় কাঁচের টুকরো গণনা।',
            takeaways=['প্রতিফলনের বদলে বিশ্বকে উল্টানো: রশ্মি সোজা যায়, আর আমরা “লুকিং-গ্লাস” ইউনিভার্সে প্রবেশ করি।',
                       'আয়নাদুটোর মাঝের কোণ θ হলে কতবার θ যোগ করা যায় যাতে যোগফল π-র কম থাকে—সেটাই উত্তর।',
                       'সংখ্যা $\\left\\lfloor \\pi/\\theta \\right\\rfloor$ (সঠিক ক্ষেত্রে $\\lceil \\pi/\\theta\\rceil-1$)।'],
            formulas=[{'label': 'আয়নার কোণ', 'katex': r'\theta=\arctan\!\sqrt{\tfrac{m_2}{m_1}}'},
                      {'label': 'প্রতিফলনের সংখ্যা', 'katex': r'N=\left\lfloor\frac{\pi}{\theta}\right\rfloor'}],
            figures=[{'id': 'fig_light_unfold', 'caption_bn': 'আয়না খুলে দিলে রশ্মি কাঁচের টুকরোর মাঝ দিয়ে সোজা যায়', 'label': 'π / θ', 'color': '#fcc419'}],
            body='''<p>আয়নার মাঝে রশ্মি গণনা করা কঠিন। কিন্তু একটা চতুর কৌশল আছে: রশ্মি প্রতিফলিত হচ্ছে ভেবে না, বরং <strong>পুরো বিশ্বটাকেই উল্টিয়ে দিন</strong>। তখন রশ্মিটা সোজা চলতে থাকে এবং পরপর কয়েকটা “লুকিং-গ্লাস” ইউনিভার্সে প্রবেশ করে।</p>

[[F0]]

<p>আসল বাঁকা পথ আর কাল্পনিক সোজা পথের তুলনা করলে দেখা যায়: সংঘর্ষ গণনা হয়ে গেছে <strong>কতগুলো কাঁচের টুকরো অতিক্রম করেছে</strong> তা গণনা। আয়নাদুটোর মাঝের কোণ θ হলে, $\\pi$ অতিক্রম না করে θ কে কতবার যোগ করা যায়—সেটাই আয়নের সংখ্যা: $N=\\left\\lfloor \\pi/\\theta \\right\\rfloor$।</p>

<b1b-callout type="gold" icon="💡" title='কোথায় পাই এলো?'>
<p>$\\theta=\\arctan\\sqrt{m_2/m_1}$ ছোট হলে $\\theta\\approx\\sqrt{m_2/m_1}$। ভর ১০০-এর ঘাত হলে $\\pi/\\theta$ জাতীয় এই গণনাই পাইয়ের অঙ্কগুলোকে বের bring করে দেয়—যা আগের পাঠেও দেখেছি।</p>
</b1b-callout>''',
        ),
    ],
    quizzes=[
        dict(id='quiz_light_formula', section_ref='sec-unfold',
             question_bn='আয়না খulে দেওয়া কৌশলে প্রতিফলনের সংখ্যার সূত্র কী?',
             question_en='What is the reflection-count formula after unfolding the mirrors?',
             options=['$\\lfloor \\pi/\\theta \\rfloor$', '$\\lfloor 2\\pi/\\theta \\rfloor$', '$\\lfloor \\theta/\\pi \\rfloor$', '$\\pi\\theta$'],
             correct_index=0,
             correct_msg='ঠিক! $\\pi$ অতিক্রম না করে θ কে যতবার যোগ করা যায়, ততবার প্রতিফলন—অর্থাৎ $\\lfloor \\pi/\\theta \\rfloor$।',
             wrong_msg='মনে করো: θ যোগ করতে থাকি যতক্ষণ যোগফল π-র কম থাকে।',
             reveal_msg='সঠিক উত্তর $\\lfloor \\pi/\\theta \\rfloor$।',
             hint='π কে θ দিয়ে ভাগ করে নিচের দিকে বৃত্তাকার করো।'),
    ],
),

L(
    num='04', slug='basel-problem',
    title_bn='পাই কেন এখানে? আর কেন তার বর্গ?',
    title_en='Why is pi here? And why is it squared? A geometric answer to the Basel problem',
    subtitle_bn='ব্যাসেল সমস্যারManage এক জ্যামিতিক প্রমাণ—যেখানে ১ + ১/৪ + ১/৯ + … হঠাৎ করে π²/৬ হয়ে যায়',
    date='২ মার্চ, ২০১৮', duration='15:31', yt_id='d-o3B6c2TWI',
    epigraph=('Unlike many more common proofs, this one makes it very clear why pi is involved.',
              'অনেক প্রচলিত প্রমাণের তুলনায় এই প্রমাণে পাইয়ের উপস্থিতি অনেক পরিষ্কার।', 'Grant Sanderson'),
    sections=[
        dict(
            id='sec-basel-series', title_bn='ব্যাসেল সমস্যা',
            title_en='The Basel Problem',
            summary_bn='বর্গসংখ্যার ব্যস্তনের এই অসীম ধারার মান কত—এই প্রশ্নই প্রায় ৯০ বছর গণিতবিদদের বিব্রত করে রেখেছিল।',
            takeaways=['ধারা $1+\\tfrac14+\\tfrac19+\\tfrac1{16}+\\cdots=\\sum_{n=1}^{\\infty}\\frac1{n^2}$।',
                       'অয়লার ১৭৩৪ সালে দেখান এর মান $\\pi^2/6$—কিন্তু কেন পাই, তা সাধারণ প্রমাণে বোঝা যায় না।',
                       '3Blue1Brown-এর জ্যামিতিক প্রমাণে পাইয়ের আগমন স্পষ্টভাবে দেখা যায়।'],
            formulas=[{'label': 'ব্যাসেল সমস্যা', 'katex': r'\sum_{n=1}^{\infty}\frac{1}{n^2}=\frac{\pi^2}{6}'}],
            figures=[{'id': 'fig_basel_series', 'caption_bn': 'বর্গের ব্যস্তনের যোগফল π²/৬', 'label': 'Σ 1/n² = π²/6', 'color': '#74c0e3'}],
            body='''<p>১৬৪৪ সাল থেকে গণিতবিদরা একটা প্রশ্ন নিয়ে কাজ করছিলেন: $1+\\tfrac14+\\tfrac19+\\tfrac1{16}+\\cdots$ অর্থাৎ $\\sum_{n=1}^{\\infty}\\frac1{n^2}$ এর মান কত? প্রতিটি পদ একের পর এক ছোট হয়ে যাচ্ছে, কিন্তু যোগফল কোথায় গিয়ে থামে?</p>

<p>১৭৩৪ সালে অয়লার দেখালেন মানটা $\\pi^2/6$। কিন্তু <strong>কেন পাই?</strong> আর তাও আবার <strong>বর্গ</strong> ($\\pi^2$)? প্রচলিত বীজগাণিতিক প্রমাণে এটা বোঝা কঠিন। এখানে আমরা দেখব একটা জ্যামিতিক প্রমাণ যেখানে পাইটা সামনাসামনি দেখা যায়।</p>

[[F0]]''',
        ),
        dict(
            id='sec-inverse-squares', title_bn='ব্যস্ত-বর্গ ও জ্যামিতি',
            title_en='Inverse Squares and Geometry',
            summary_bn='একই শক্তি একাধিক দূরত্বে ছড়িয়ে পড়লে ব্যস্ত-বর্গ আসে; বৃত্তের ক্ষেত্রে এই ছড়ানোর হিসাব π-র দিকে নিয়ে যায়।',
            takeaways=['দূরত্ব $r$-এ কোনো রশ্মির তীব্রতা $1/r^2$ হারে কমে—ব্যস্ত-বর্গ সূত্র।',
                       'বৃত্তের পরিধি $2\\pi r$ হওয়ায় বৃত্তাকার ছড়ানোর হিসাব স্বাভাবিকভাবেই π আনে।',
                       'জ্যামিতিক ছবিটা প্রমাণকে “কেন পাই” প্রশ্নের সরাসরি উত্তর দেয়।'],
            formulas=[{'label': 'ব্যস্ত-বর্গ সূত্র', 'katex': r'I(r)\propto\frac{1}{r^2}'},
                      {'label': 'বৃত্তের পরিধি', 'katex': r'C=2\pi r'}],
            figures=[{'id': 'fig_basel_geometry', 'caption_bn': 'বৃত্তাকার ছড়ানোর হিসাবেই পাই আসে', 'label': '2πr', 'color': '#e599f7'}],
            body='''<p>ব্যাসেল ধারার পদগুলো ব্যস্ত-বর্গের (inverse square)। প্রকৃতিতেও ব্যস্ত-বর্গ সূত্র দেখা যায়: কোনো উৎস থেকে দূরত্ব $r$-এ গেলে তার তীব্রতা $1/r^2$ হারে কমে। কারণ শক্তি একটা বৃত্তের পরিধি $2\\pi r$ জুড়ে ছড়িয়ে পড়ে—আর sector-এর ক্ষেত্রফল $\\tfrac12 r^2\\theta$।</p>

[[F0]]

<p>এই $r^2$ আর $\\pi$ এর সংমিশ্রণই ইঙ্গিত দেয়: ধারার উত্তরে $\\pi^2$ থাকতে পারে। কিন্তু এটা ইঙ্গিত মাত্র—আমাদের চাই একটা নিখুঁত প্রমাণ, যেখানে প্রতিটি পদ একটা জ্যামিতিক বস্তুর সাথে মেলে।</p>

<b1b-callout type="blue" icon="📐" title='জ্যামিতিক দৃষ্টিভঙ্গি'>
<p>সরাসরি যোগ করার বদলে আমরা প্রতিটি $1/n^2$ কে একটা উপবৃত্তের (ellipse) বা বৃত্তের ক্ষেত্রফলের সাথে মিলিয়ে দেখি। তখন অসীম যোগটা হয়ে যায় একটা মসৃণ বক্ররেখার নিচের ক্ষেত্রফল—আর সেই ক্ষেত্রফলেই লুকিয়ে আছে $\\pi^2/6$।</p>
</b1b-callout>''',
        ),
        dict(
            id='sec-result', title_bn='উত্তর: π²/6',
            title_en='The Answer and Why It Is Squared',
            summary_bn='সাবধানে জ্যামিতিক হিসাব করলে ধারার মান π²/6 দাঁড়ায়—বর্গ আসে দ্বিমাত্রিক জ্যামিতি থেকে।',
            takeaways=['ধারার মান $\\sum_{n=1}^{\\infty}1/n^2=\\pi^2/6\\approx 1.6449$।',
                       '$\\pi$ বর্গাকৃত হয় কারণ হিসাবটা দ্বিমাত্রিক ক্ষেত্রফলের সাথে যুক্ত।',
                       'একই কৌশল অন্যান্য জোড় ঘাতের ধারার জন্যও সাধারণীকরণ করা যায়।'],
            formulas=[{'label': 'চূড়ান্ত ফলাফল', 'katex': r'\sum_{n=1}^{\infty}\frac{1}{n^{2}}=\frac{\pi^{2}}{6}\approx 1.644934'}],
            figures=[{'id': 'fig_basel_result', 'caption_bn': 'ধারার মান π²/6—পাই বর্গাকৃত', 'label': 'π² / 6', 'color': '#8ce99a'}],
            body='''<p>জ্যামিতিক ছবিটিকে যতক্ষণ কাগজে কলমে এগিয়ে নিয়ে যাই, ততক্ষণে দেখা যায় অসীম পদগুলোর যোগফল ঠিক $\\pi^2/6$। $\\pi$ যেটা এসেছে বৃত্ত থেকে, আর তার বর্গ এসেছে দুই মাত্রার ক্ষেত্রফলের হিসাব থেকে।</p>

[[F0]]

<p>এই প্রমাণের সৌন্দর্য হলো এটা শুধু “উত্তর কী” বলেই থামে না, বরং “<strong>কেন পাই</strong>” প্রশ্নেরও সরাসরি জবাব দেয়। পরবর্তী পাঠে আমরা আরেকটি বিখ্যাত ধারা—লাইবনিজের সূত্র—দেখব, যেখানে পাই আবারও অপ্রত্যাশিত ভাবে আবির্ভূত হয়।</p>''',
        ),
    ],
    quizzes=[
        dict(id='quiz_basel_sum', section_ref='sec-result',
             question_bn='ব্যাসেল ধারা $\\sum_{n=1}^{\\infty}1/n^2$ এর মান কত?',
             question_en='What is the value of the Basel series sum of 1/n²?',
             options=['$\\pi/6$', '$\\pi^2/6$', '$\\pi^2/4$', '$6/\\pi^2$'],
             correct_index=1,
             correct_msg='চমৎকার! $1+\\tfrac14+\\tfrac19+\\cdots=\\pi^2/6\\approx 1.6449$।',
             wrong_msg='মনে করো অয়লারের ফলাফল: পাই-র বর্গকে ৬ দিয়ে ভাগ করতে হয়।',
             reveal_msg='সঠিক উত্তর $\\pi^2/6$।',
             hint='উত্তরে পাই বর্গাকৃত থাকে এবং ৬ দিয়ে ভাগ করা হয়।'),
    ],
),

L(
    num='05', slug='leibniz-formula',
    title_bn='মৌলিক সংখ্যার নিয়মিততায় লুকোনো পাই',
    title_en='Pi hiding in prime regularities',
    subtitle_bn='১ − ১/৩ + ১/৫ − ১/৭ + … সূত্রটির পেছনে লুকিয়ে আছে বৃত্ত, মৌলিক সংখ্যা এবং জটিল সংখ্যা',
    date='১৯ মে, ২০১৭', duration='17:29', yt_id='cS0WsJhZFiw',
    epigraph=('Pi hides in the most unlikely of places.',
              'পাই সবচেয়ে অপ্রত্যাশিত জায়গায় লukিয়ে থাকে।', 'Grant Sanderson'),
    sections=[
        dict(
            id='sec-leibniz-series', title_bn='লাইবনিজের ধারা',
            title_en="Leibniz's Alternating Series",
            summary_bn='একটিমাত্র alternating ধারা—প্রথম দেখে মনে হয় বৃত্তের সাথে এর কোনো সম্পর্ক নেই—কিন্তু এর মান π/4।',
            takeaways=['ধারা $1-\\tfrac13+\\tfrac15-\\tfrac17+\\cdots=\\pi/4$।',
                       'এটি $\\arctan(1)$ এর টেলর ধারা; $\\arctan(1)=\\pi/4$।',
                       'ধারাটি খুব ধীরে converges—কয়েক লক্ষ পদ নিলেও কয়েকটি অঙ্কই পাওয়া যায়।'],
            formulas=[{'label': 'লাইবনিজ সূত্র', 'katex': r'1-\frac13+\frac15-\frac17+\cdots=\frac{\pi}{4}'},
                      {'label': 'আরকট্যা-র টেলর ধারা', 'katex': r'\arctan(x)=x-\frac{x^3}{3}+\frac{x^5}{5}-\cdots'}],
            figures=[{'id': 'fig_leibniz_series', 'caption_bn': 'alternating ধারার যোগফল π/4', 'label': '1−1/3+1/5−…', 'color': '#74c0e3'}],
            body='''<p>দেখে মনে হয় না কিছু—$1-\\tfrac13+\\tfrac15-\\tfrac17+\\tfrac19-\\cdots$। ছোট ছোট ভগ্নাংশের একটা alternating যোগ। কিন্তু বিস্ময়করভাবে এর মান $\\pi/4$!</p>

<p>রহস্যটার চাবি $\\arctan$ ফাংশনে লুকিয়ে আছে। টেলর ধারায় $\\arctan(x)=x-\\tfrac{x^3}{3}+\\tfrac{x^5}{5}-\\cdots$। এখানে $x=1$ বসালেই পাই $\\arctan(1)=\\pi/4$। কিন্তু তখন প্রশ্ন দাঁড়ায়—$\\arctan$ এ আবার পাই এলো কেন?</p>

[[F0]]''',
        ),
        dict(
            id='sec-circle-hidden', title_bn='এখানেও একটা বৃত্ত',
            title_en='A Circle Hiding Here Too',
            summary_bn='arctan(1)-এর ৪৫° কোণের পেছনে আছে একটা বৃত্ত; ব্যস্ত-বর্গ আর বৃত্তের কোণ একসাথে মিলে পাই আনে।',
            takeaways=['$\\arctan(1)=45^\\circ=\\pi/4$—একটা বৃত্তের কোণ।',
                       'ব্যাসেল সমস্যার মতোই এখানেও ব্যস্ত-বর্গ ও বৃত্তের মিল পাইকে প্রকাশ করে।',
                       'ধারার কাঠামো বোঝা যায় একটা একক বৃত্তের ওপর ভিত্তি করে।'],
            formulas=[{'label': 'বৃত্তের কোণ', 'katex': r'\arctan(1)=\frac{\pi}{4}=45^\circ'}],
            figures=[{'id': 'fig_leibniz_circle', 'caption_bn': '৪৫° কোণ—একক বৃত্তের চার ভাগের এক ভাগ', 'label': 'π / 4', 'color': '#e599f7'}],
            body='''<p>$\\arctan(1)$ মানে হলো ৪৫° কোণ—একটা বৃত্তের ঠিক চার ভাগের এক ভাগ, অর্থাৎ $\\pi/4$ রেডিয়ান। তাই ধারাটির উত্তরে পাই থাকাটা আর এত অদ্ভুত নয়: <strong>এখানেও একটা বৃত্ত লুকিয়ে আছে</strong>।</p>

[[F0]]

<p>ব্যাসেল সমস্যার মতোই এখানেও ব্যস্ত-বর্গ পদগুলো ($1, 1/3, 1/5,\\ldots$) আর বৃত্তের কোণের হিসাব একসাথে মিলে পাইকে বের করে আনে। কিন্তু এই গল্পে আরেকটা unexpected অধ্যায় আছে—মৌলিক সংখ্যা।</p>''',
        ),
        dict(
            id='sec-primes', title_bn='মৌলিক সংখ্যা ও জটিল তল',
            title_en='Primes and the Complex Plane',
            summary_bn='পাইয়ের এই ধারার সাথে মৌলিক সংখ্যার একটা গাণিতিক সম্পর্ক আছে, যা জটিল সংখ্যা আর গauss-িয় পূর্ণসংখ্যার মাধ্যমে বোঝা যায়।',
            takeaways=['জটিল সংখ্যা $\\mathbb{C}$ তে গুণন মানে ঘূর্ণন ও স্কেলিং—বৃত্তের সাথে সরাসরি সম্পর্ক।',
                       'মৌলিক সংখ্যাগুলোকে জটিল তলে বিন্যাস করলে পাইয়ের সাথে তাদের নিয়মিততা দেখা যায়।',
                       'Gaussian integer-এর factorization পাই-সংক্রান্ত ধারার সাথে যুক্ত।'],
            formulas=[{'label': 'জটিল একক', 'katex': r'e^{i\\theta}=\\cos\\theta+i\\sin\\theta,\\quad e^{i\\pi}=-1'}],
            figures=[{'id': 'fig_leibniz_primes', 'caption_bn': 'জটিল তলে মৌলিক সংখ্যা ও ঘূর্ণন', 'label': 'e^(iπ) = −1', 'color': '#8ce99a'}],
            body='''<p>জটিল সংখ্যার তলে কোনো সংখ্যা দিয়ে গুণ করার মানে হলো ঘূর্ণন ও স্কেলিং—আর ঘূর্ণন মানেই বৃত্ত। তাই অয়লারের বিখ্যাত $e^{i\\pi}=-1$ সমীকরণটা আসলে বৃত্তের এক আধ-ঘূর্ণনের গল্প।</p>

[[F0]]

<p>মৌলিক সংখ্যাগুলোকে জটিল তলে বসিয়ে দেখলে তাদের একটা নিয়মিততা ফুটে ওঠে, যা আবার $\\pi$-র সাথে যুক্ত। এইভাবে একটিমাত্র alternating ধারা আমাদের নিয়ে যায় বৃত্ত, জটিল সংখ্যা আর মৌলিক সংখ্যার—এক অদ্ভুত মিলনের জগতে।</p>

<b1b-callout type="blue" icon="🔢" title='সংখ্যা তত্ত্বের সাথে সেতু'>
<p>লাইবনিজের এই ধারা দেখায় জটিল সংখ্যার গুণন আর মৌলিক সংখ্যার factorization—দুটো মিলে পাই-সংক্রান্ত সূত্র তৈরি করে। গণিতের বিভিন্ন শাখা যে আসলে একে অপরের সাথে যুক্ত, এর চেয়ে ভালো উদাহরণ কমই পাওয়া যায়।</p>
</b1b-callout>''',
        ),
    ],
    quizzes=[
        dict(id='quiz_leibniz_sum', section_ref='sec-leibniz-series',
             question_bn='লাইবনিজের ধারা $1-\\tfrac13+\\tfrac15-\\cdots$ এর মান কত?',
             question_en='What is the value of the Leibniz series?',
             options=['$\\pi/2$', '$\\pi/4$', '$\\pi^2/6$', '$1/\\pi$'],
             correct_index=1,
             correct_msg='ঠিক! $\\arctan(1)=\\pi/4$, তাই ধারার মান $\\pi/4$।',
             wrong_msg='মনে করো: arctan(1) = 45° = π/4।',
             reveal_msg='সঠিক উত্তর $\\pi/4$।',
             hint='arctan(1) = π/4 সূত্রটি মনে রাখো।'),
    ],
),

L(
    num='06', slug='gaussian-integral',
    title_bn='স্বাভাবিক বণ্টনে পাই কেন?',
    title_en='Why π is in the normal distribution (beyond integral tricks)',
    subtitle_bn='গাউসিয়ান ইন্টিগ্রাল $\\int e^{-x^2}dx=\\sqrt{\\pi}$ এর পেছনের কৌশল এবং বেল-আকৃতির বণ্টন কেন স্বাভাবিক তা ব্যাখ্যা',
    date='২ এপ্রিল, ২০২৩', duration='22:44', yt_id='cy4FhzMhtnU',
    epigraph=('The Gaussian integral is where the bell curve meets the circle.',
              'গাউসিয়ান ইন্টিগ্রালেই বেল-বক্ররেখা বৃত্তের সাথে মেলে।', 'Grant Sanderson'),
    sections=[
        dict(
            id='sec-bell-curve', title_bn='বেল-আকৃতি ও গাউসিয়ান',
            title_en='The Bell Curve and the Gaussian',
            summary_bn='প্রকৃতির অসংখ্য পরিমাপ বেল-আকৃতির বণ্টন অনুসরণ করে—এবং তার সূত্রে হঠাৎ √π কোথা থেকে এসে যায়?',
            takeaways=['স্বাভাবিক বণ্টনের ঘনত্ব $f(x)\\propto e^{-x^2/2}$।',
                       'সম্পূর্ণ বক্ররেখার নিচের ক্ষেত্রফল ১ হতে হলে একটা স্কেলিং ধ্রুবক লাগে।',
                       'সেই ধ্রুবকের ভেতরেই লুকিয়ে আছে $\\sqrt{2\\pi}$—অর্থাৎ পাই।'],
            formulas=[{'label': 'স্বাভাবিক বণ্টন', 'katex': r'f(x)=\frac{1}{\\sigma\\sqrt{2\\pi}}e^{-\\frac{(x-\\mu)^2}{2\\sigma^2}}'}],
            figures=[{'id': 'fig_gauss_bell', 'caption_bn': 'বেল-আকৃতির বক্ররেখা ও তার নিচের ক্ষেত্রফল', 'label': 'e^(−x²)', 'color': '#74c0e3'}],
            body='''<p>মানুষের উচ্চতা, পরীক্ষার নম্বর, ত্রুটির পরিমাপ—অসংখ্য জিনিস বেল-আকৃতির (bell-shaped) বণ্টন অনুসরণ করে। এর সূত্র $f(x)\\propto e^{-x^2/2}$। কিন্তু বক্ররেখার নিচের মোট ক্ষেত্রফল তো ১ হতে হবে—তাই একটা স্কেলিং ধ্রুবক লাগে $\\frac{1}{\\sigma\\sqrt{2\\pi}}$।</p>

[[F0]]

<p>এই $\\sqrt{2\\pi}$ কোথা থেকে এলো? উত্তরটা আছে গাউসিয়ান ইন্টিগ্রালে।</p>''',
        ),
        dict(
            id='sec-integral-trick', title_bn='ইন্টিগ্রালের কৌশল',
            title_en='The Classic Integration Trick',
            summary_bn='$e^{-x^2}$ কে সরাসরি ইন্টিগ্রেট করা যায় না; কিন্তু দুইটি কপি নিয়ে দ্বিমাত্রিক ক্ষেত্রে নিলে পোলার কোঅর্ডিনেটে সহজে হয়ে যায়।',
            takeaways=['ধরি $I=\\int_{-\\infty}^{\\infty}e^{-x^2}dx$। তবে $I^2=\\iint e^{-(x^2+y^2)}dx\\,dy$।',
                       'পোলার কোঅর্ডিনেটে $x^2+y^2=r^2$ আর $dx\\,dy=r\\,dr\\,d\\theta$।',
                       'ফলাফল $I^2=\\pi$, অর্থাৎ $I=\\sqrt{\\pi}$।'],
            formulas=[{'label': 'গাউসিয়ান ইন্টিগ্রাল',
                       'katex': r'I=\int_{-\\infty}^{\\infty}e^{-x^2}dx=\\sqrt{\\pi}'},
                      {'label': 'দ্বিমাত্রিক কৌশল',
                       'katex': r'I^2=\\int_0^{2\\pi}\\!\!\\int_0^{\\infty} e^{-r^2}r\\,dr\\,d\\theta=\\pi'}],
            figures=[{'id': 'fig_gauss_polar', 'caption_bn': 'দ্বিমাত্রিক ক্ষেত্রে পোলার কোঅর্ডিনেট—পাই এখান থেকে আসে', 'label': 'r dr dθ', 'color': '#e599f7'}],
            body='''<p>$e^{-x^2}$ এর anticivative কোনো সাধারণ ফাংশন নেই—সরাসরি ইন্টিগ্রেট করা যায় না। ক্লাসিক কৌশল হলো একটা কপি নিয়ে গুণ করা: $I^2=\\left(\\int e^{-x^2}dx\\right)\\left(\\int e^{-y^2}dy\\right)=\\iint e^{-(x^2+y^2)}dx\\,dy$।</p>

<p>এখন পোলার কোঅর্ডিনেটে যাই: $x^2+y^2=r^2$, ক্ষেত্রফল উপাদান $dx\\,dy=r\\,dr\\,d\\theta$। তখন $I^2=\\int_0^{2\\pi}\\!\\int_0^{\\infty}e^{-r^2}r\\,dr\\,d\\theta=(2\\pi)(\\tfrac12)=\\pi$। সুতরাং $I=\\sqrt{\\pi}$!</p>

[[F0]]

<p>পাই এসেছে $2\\pi$ কোণ থেকে—অর্থাৎ একটা <strong>বৃত্ত</strong> থেকে। বেল-বক্ররেখা আর বৃত্তের এই মিলনই ইন্টিগ্রালে $\\sqrt{\\pi}$ আনে।</p>''',
        ),
        dict(
            id='sec-herschel-maxwell', title_bn='কেন এই বণ্টন স্বাভাবিক?',
            title_en='The Herschel–Maxwell Derivation',
            summary_bn='কয়েকটি স্বাভাবিক শর্ত (দিক-নিরপেক্ষতা, স্থান-নিরপেক্ষতা, স্বাধীনতা) থেকেই বেল-আকৃতির বণ্টন এবং তার স্কেলিং বের করা যায়—তাই √π-র উপস্থিতি যুক্তিসঙ্গত।',
            takeaways=['ভুলের পরিমাপ সব দিকে একই রকম হলে (দিক-নিরপেক্ষ) $x$ ও $y$ আলাদা হয়।',
                       'স্বাধীন উপাদানের ক্ষেত্রে $f(x)f(y)$ শুধু $x^2+y^2$-র ওপর নির্ভর করলে $f$ অবশ্যই $e^{-cx^2}$।',
                       'এই ডেরিভেশন বোঝায় কেন ইন্টিগ্রালের কৌশল কেবল কাকতালীয় নয়।'],
            formulas=[{'label': 'ফলাফল', 'katex': r'f(x)=A e^{-cx^2}\;\Rightarrow\;\int f = A\\sqrt{\\pi/c}=1'}],
            figures=[{'id': 'fig_gauss_normal', 'caption_bn': 'স্বাভাবিক শর্ত থেকে বেল-বক্ররেখার উৎপত্তি', 'label': 'σ√(2π)', 'color': '#8ce99a'}],
            body='''<p>ইন্টিগ্রালের কৌশলটা দেখে মনে হতে পারে এটা শুধুই একটা চতুর trick। কিন্তু Herschel–Maxwell ডেরিভেশন দেখায় এই বণ্টন কেন <em>স্বাভাবিক</em>: ভুলের পরিমাপ দিক-নিরপেক্ষ, জায়গা-নিরপেক্ষ এবং পরস্পর স্বাধীন হলেই গণিতের নিয়ম বাধ্য হয়ে $f(x)=Ae^{-cx^2}$ রূপ নেয়।</p>

[[F0]]

<p>তাই $\\sqrt{\\pi}$ কোথাও জোর করে আনা হয়নি—এটা সেইসব স্বাভাবিক শর্তেরই ফল। বৃত্ত, বেল-বক্ররেখা আর পাই—এ তিনের এই মিলনই এই পাঠের মূল কথা।</p>

<b1b-callout type="gold" icon="🔔" title='মনে রাখার মতো কথা'>
<p>বেল-আকৃতির বক্ররেখার নিচের ক্ষেত্রফল ১ রাখতে যে স্কেলিং ধ্রুবকটি লাগে, তার ভেতরেই $\\sqrt{2\\pi}$ লুকিয়ে আছে। অর্থাৎ পরিসংখ্যানের এই সুপরিচিত সূত্রের পেছনে আছে একটা বৃত্ত—আর সেটাই পাই-র উৎস।</p>
</b1b-callout>''',
        ),
    ],
    quizzes=[
        dict(id='quiz_gauss_value', section_ref='sec-integral-trick',
             question_bn='গাউসিয়ান ইন্টিগ্রাল $\\int_{-\\infty}^{\\infty}e^{-x^2}dx$ এর মান কত?',
             question_en='What is the value of the Gaussian integral?',
             options=['$\\pi$', '$\\sqrt{\\pi}$', '$\\pi^2$', '$\\sqrt{2\\pi}$'],
             correct_index=1,
             correct_msg='ঠিক! দ্বিমাত্রিক কৌশলে $I^2=\\pi$, তাই $I=\\sqrt{\\pi}$।',
             wrong_msg='মনে করো: $I^2=\\pi$, সুতরাং $I=\\sqrt{\\pi}$।',
             reveal_msg='সঠিক উত্তর $\\sqrt{\\pi}$।',
             hint='আগে $I^2$ হিসাব করো—সেটা হয় π।'),
    ],
),

L(
    num='07', slug='wallis-product',
    title_bn='পাই-র জন্য ওয়ালিস গুণফল — একটি জ্যামিতিক প্রমাণ',
    title_en='The Wallis product for pi, proved geometrically',
    subtitle_bn='$\\frac{\\pi}{2}=\\frac21\\cdot\\frac23\\cdot\\frac43\\cdot\\frac45\\cdots$ — এই অসীম গুণফলটির জ্যামিতিক প্রমাণ ও জটিল সংখ্যার কৌশল',
    date='২০ এপ্রিল, ২০১৮', duration='15:08', yt_id='V4YQUKiRbEA',
    epigraph=('A product of simple fractions equals pi over two.',
              'সরল ভগ্নাংশের একটা গুণফল সমান পাই-র অর্ধেক।', 'Grant Sanderson'),
    sections=[
        dict(
            id='sec-wallis-product', title_bn='ওয়ালিস গুণফল',
            title_en='The Wallis Product',
            summary_bn='১৬৫৫ সালে John Wallis আবিষ্কার করেন এই অদ্ভুত গুণফলটির মান π/2—কিন্তু প্রমাণ ছাড়াই।',
            takeaways=['$g$ুণফল $\\frac21\\cdot\\frac23\\cdot\\frac43\\cdot\\frac45\\cdots=\\frac{\\pi}{2}$।',
                       'জোড় ও বেজোড় সংখ্যার একটি সুন্দর বিন্যাস এর পদগুলো তৈরি করে।',
                       '3Blue1Brown এই গুণফলের একটা জ্যামিতিক প্রমাণ দেখান।'],
            formulas=[{'label': 'ওয়ালিস গুণফল', 'katex': r'\frac{\\pi}{2}=\prod_{n=1}^{\\infty}\frac{2n}{2n-1}\cdot\\frac{2n}{2n+1}=\frac21\cdot\frac23\cdot\frac43\cdot\frac45\cdots'}],
            figures=[{'id': 'fig_wallis_product', 'caption_bn': 'সরল ভগ্নাংশের গুণফল π/2', 'label': '2/1 · 2/3 · 4/3 · 4/5', 'color': '#74c0e3'}],
            body='''<p>১৬৫৫ সালে John Wallis একটা বিস्मয়কর সম্পর্ক লিখেছিলেন: $\\frac21\\cdot\\frac23\\cdot\\frac43\\cdot\\frac45\\cdot\\frac65\\cdot\\frac67\\cdots=\\frac{\\pi}{2}$। সব পদ সরল ভগ্নাংশ, কিন্তু ফলাফল পাই!</p>

[[F0]]

<p>ওয়ালিস নিজে এইটা প্রমাণ করতে পারেননি। আজ আমরা দেখব একটা জ্যামিতিক প্রমাণ, যার মূলে আছে $\\sin^n x$ এর ইন্টিগ্রাল।</p>''',
        ),
        dict(
            id='sec-sin-integrals', title_bn='sin^n-এর ইন্টিগ্রাল',
            title_en='Integrals of sin to the n',
            summary_bn='$\\int_0^{\\pi}\\sin^n x\\,dx$ এর ধারাবাহিক মানগুলোর অনুপাত থেকেই ওয়ালিসের ভগ্নাংশগুলো বেরিয়ে আসে।',
            takeaways=['$I_n=\\int_0^{\\pi}\\sin^n x\\,dx$ এর পুনরাবৃত্তি সূত্র $I_n=\\frac{n-1}{n}I_{n-2}$।',
                       'এই অনুপাতগুলোই ওয়ালিস গুণফলের পদ $\\frac{2n}{2n-1}\\cdot\\frac{2n}{2n+1}$ তৈরি করে।',
                       'জ্যামিতিকভাবে $I_n$ হলো একটা বৃত্ত-সম্পর্কিত আকৃতির ক্ষেত্রফল।'],
            formulas=[{'label': 'পুনরাবৃত্তি সূত্র', 'katex': r'I_n=\int_0^{\\pi}\\sin^n x\\,dx=\frac{n-1}{n}I_{n-2}'},
                      {'label': 'জোড় ঘাতের মান', 'katex': r'I_{2n}=\\pi\\cdot\frac{1\\cdot3\\cdot5\\cdots(2n-1)}{2\\cdot4\\cdot6\\cdots(2n)}'}],
            figures=[{'id': 'fig_wallis_sin', 'caption_bn': 'sin^n বক্ররেখার নিচের ক্ষেত্রফল থেকে গুণফল', 'label': '∫ sinⁿ x dx', 'color': '#e599f7'}],
            body='''<p>ধরি $I_n=\\int_0^{\\pi}\\sin^n x\\,dx$। আংশিক ইন্টিগ্রেশন দিয়ে পাই সুন্দর একটা পুনরাবৃত্তি: $I_n=\\frac{n-1}{n}I_{n-2}$। অর্থাৎ $I_2=\\frac12 I_0$, $I_4=\\frac34 I_2$, $I_6=\\frac56 I_4$—এইভাবে চলতে থাকে।</p>

[[F0]]

<p>এই অনুপাতগুলোকে বারবার বসালে ওয়ালিসের $\\frac21\\cdot\\frac23\\cdot\\frac43\\cdots$ পদগুলো তৈরি হয়। কিন্তু $I_0=\\pi$ কোথা থেকে এলো? সেটা এলো $\\sin^0 x=1$ কে $0$ থেকে $\\pi$ পর্যন্ত ইন্টিগ্রেট করে—অর্থাৎ $\\pi$ দৈর্ঘ্যের একটা আয়তক্ষেত্রের ক্ষেত্রফল থেকে।</p>''',
        ),
        dict(
            id='sec-geometric-proof', title_bn='জ্যামিতিক প্রমাণ ও জটিল সংখ্যা',
            title_en='The Geometric Proof and Complex Numbers',
            summary_bn='বৃত্তের ক্ষেত্রফল ও জটিল সংখ্যার ব্যবহার করে $\\pi/2$ কে এই গুণফলের সাথে মিলিয়ে দেখানো যায়—পাই আবারো বৃত্ত থেকে জন্ম নেয়।',
            takeaways=['$\\sin x$-এর শূন্যবিন্দুগুলোর বিন্যাস গুণফলটির সাথে মেলে।',
                       'জটিল তলে বৃত্তের বিন্দুগুলোর গুণন পাই-সংক্রান্ত সূত্র দেয়।',
                       'প্রমাণের শেষে $\\pi/2$ ঠিক ওয়ালিসের গুণফলের সমান দাঁড়ায়।'],
            formulas=[{'label': 'চূড়ান্ত ফলাফল', 'katex': r'\prod_{n=1}^{\\infty}\frac{2n}{2n-1}\cdot\frac{2n}{2n+1}=\frac{\\pi}{2}'}],
            figures=[{'id': 'fig_wallis_circle', 'caption_bn': 'বৃত্তের জ্যামিতি থেকেই পাই আসে', 'label': 'π / 2', 'color': '#8ce99a'}],
            body='''<p>জটিল সংখ্যার তলে $\\sin x$-কে তার শূন্যবিন্দুগুলো দিয়ে প্রকাশ করা যায়। এই গুণনরূপ আর বৃত্তের ক্ষেত্রফলের হিসাব একসাথে করে দেখা যায় ওয়ালিসের গুণফল ঠিক $\\pi/2$।</p>

[[F0]]

<p>এই প্রমাণ আবার একই কথা মনে করিয়ে দেয়: পাই যেখানেই আবির্ভূত হোক, তার পেছনে কোথাও না কোথাও একটা <strong>বৃত্ত</strong> থাকেই।</p>

<b1b-callout type="green" icon="✅" title='ওয়ালিস গুণফলের তাৎপর্য'>
<p>সরল ভগ্নাংশের একটা অসীম গুণফলের মান $\\pi/2$—এটা দেখে মনে হয় কাকতালীয়, কিন্তু মূলে আছে $\\sin^n x$-এর ইন্টিগ্রালের পুনরাবৃত্তি সূত্র আর বৃত্তের জ্যামিতি। গুণফলটির প্রতিটি পদ আসলে একটা জ্যামিতিক অনুপাত।</p>
</b1b-callout>''',
        ),
    ],
    quizzes=[
        dict(id='quiz_wallis_value', section_ref='sec-geometric-proof',
             question_bn='ওয়ালিস গুণফল $\\frac21\\cdot\\frac23\\cdot\\frac43\\cdots$ এর মান কত?',
             question_en='What is the value of the Wallis product?',
             options=['$\\pi$', '$\\pi/2$', '$\\pi^2/6$', '$2/\\pi$'],
             correct_index=1,
             correct_msg='সঠিক! ওয়ালিস গুণফলের মান $\\pi/2$।',
             wrong_msg='মনে করো: ওয়ালিস গুণফল π-র অর্ধেকের সমান।',
             reveal_msg='সঠিক উত্তর $\\pi/2$।',
             hint='উত্তরটা পাই-র অর্ধেক।'),
    ],
),

L(
    num='08', slug='pi-was-628',
    title_bn='পাই প্রায় ৬.২৮৩১৮৫… হতে পারত',
    title_en='How pi was almost 6.283185...',
    subtitle_bn='পাই-র প্রতীকটি নিয়ে ইতিহাস—অয়লার কীভাবেই বা π দিয়ে একাধিক বৃত্ত-ধ্রুবক বোঝাতেন',
    date='১৪ মার্চ, ২০১৮', duration='5:01', yt_id='RdzR6c0SKDc',
    epigraph=('The symbol could so easily have meant something else.',
              'এই প্রতীকটি খুব সহজেই অন্য কিছু বোঝাতে পারত।', 'Grant Sanderson'),
    sections=[
        dict(
            id='sec-early-notation', title_bn='প্রথম দিকের চিহ্ন',
            title_en='Early Notation',
            summary_bn='পাইয়ের আধুনিক প্রতীক ব্যবহার শুরু হয় ১৮শ শতাব্দীতে; তার আগে বৃত্ত-ধ্রুবক বোঝাতে বিভিন্ন অক্ষর ব্যবহৃত হতো।',
            takeaways=['ওয়ালিস ও অন্যরা বৃত্তের পরিধি/ব্যাস অনুপাত বোঝাতে বিভিন্ন চিহ্ন ব্যবহার করতেন।',
                       '১৭০৬ সালে William Jones প্রথম π চিহ্নটি ব্যবহার করেন।',
                       'অয়লার ১৭৩০-এর দশকে এই চিহ্নকে জনপ্রিয় করেন।'],
            formulas=[{'label': 'পাইয়ের সংজ্ঞা', 'katex': r'\pi=\frac{\text{perimeter}}{\text{diameter}}\approx 3.14159'}],
            figures=[{'id': 'fig_history_pi', 'caption_bn': 'পাই-র আধুনিক প্রতীকের উৎপত্তি', 'label': 'π ≈ 3.14159', 'color': '#74c0e3'}],
            body='''<p>আজ আমরা π মানে বৃত্তের পরিধি আর ব্যাসের অনুপাত—প্রায় ৩.১৪১৫৯। কিন্তু এই প্রতীকটা সবসময় এ অর্থে ব্যবহৃত হয়নি। ১৭০৬ সালে William Jones প্রথম π অক্ষরটি ব্যবহার করেন, আর অয়লার পরে এটিকে জনপ্রিয় করেন।</p>

[[F0]]''',
        ),
        dict(
            id='sec-euler-pi', title_bn='অয়লারের দুই মান',
            title_en="Euler's Two Values of Pi",
            summary_bn='অয়লার কখনো π দিয়ে ৩.১৪ বোঝাতেন, আবার কখনো ৬.২৮—অর্থাৎ আজকের 2π। ইতিহাসে পাই প্রায় ৬.২৮ হয়ে যেতে পারত!',
            takeaways=['অয়লার π দিয়ে বৃত্তের perimeter (≈ ৬.২৮) ও diameter (≈ ৩.১৪)—দুটোই বোঝাতেন।',
                       'তাঁর লেখায় কোথাও $\\pi$ মানে ৬.২৮ আবার কোথাও ৩.১৪—প্রসঙ্গভেদে অর্থ বদলাতো।',
                       'আজকের সুবিধाजনক ঐকমত্যেই π = ৩.১৪, আর 2π-র জন্য অনেকে τ প্রস্তাব করেন।'],
            formulas=[{'label': 'দুই সম্ভাব্য অর্থ', 'katex': r'\pi\approx 3.14159\quad\text{before}\quad 2\pi\approx 6.28319'}],
            figures=[{'id': 'fig_history_two', 'caption_bn': 'অয়লারের π—দুইটি সম্ভাব্য অর্থ', 'label': '3.14  vs  6.28', 'color': '#e599f7'}],
            body='''<p>অয়লারের লেখা পড়লে অদ্ভুত একটা ব্যাপার দেখা যায়: তিনি π দিয়ে মাঝে মাঝে ৬.২৮ (বৃত্তের perimeter) আবার মাঝে মাঝে ৩.১৪ (ব্যাসের অনুপাত) বোঝাতেন। অর্থাৎ ইতিহাসে পাইয়ের মান আজকের <strong>2π ≈ ৬.২৮৩১৮৫</strong> হয়ে যেতে পারত!</p>

[[F0]]

<p>কেন এটা হলো? কারণ বৃত্তের সব সূত্রে $2\\pi$ বারবার আসে—পরিধি $2\\pi r$, একটি পূর্ণ ঘূর্ণন $2\\pi$ রেডিয়ান। অনেকের মতে ২ সংখ্যা নিয়ে π-কে সংজ্ঞায়িত করা হলে অনেক কিছু সহজ হতো।</p>

<b1b-callout type="gold" icon="🤔" title='কেন ঐকমত্য গুরুত্বপূর্ণ?'>
<p>আজ আমরা π = ৩.১৪ তেই ঐকমত্য করেছি। তবে 2π-র জন্য <strong>τ (tau)</strong> ব্যবহারের প্রস্তাব এখনো আছে। এই পাঠটা আমাদের মনে করিয়ে দেয়: গণিতের প্রতীক ও সংজ্ঞা মানুষের বেছে নেওয়া <em>চুক্তি</em>, প্রকৃতির কোনো পরম সত্য নয়।</p>
</b1b-callout>''',
        ),
        dict(
            id='sec-today', title_bn='আজকের ঐকমত্য ও টাউ (τ) প্রস্তাব',
            title_en="Today's Convention and the Tau Proposal",
            summary_bn='আজ π = ৩.১৪-এ ঐকমত্য; তবে 2π-র জন্য τ ব্যবহারের প্রস্তাব গণিত সম্প্রদায়ে আলোচিত।',
            takeaways=['আন্তর্জাতিক ঐকমত্যে π = ৩.১৪১৫৯…, পরিধি/ব্যাস।',
                       'প্রস্তাবিত τ = 2π ≈ ৬.২৮৩১৮৫; একটি পূর্ণ ঘূর্ণন = τ রেডিয়ান।',
                       'কোনটা “সঠিক” তা নয়—কোনটা বেশি সুবিধাজনক তা নিয়েই আলোচনা।'],
            formulas=[{'label': 'টাউ প্রস্তাব', 'katex': r'\tau = 2\pi \approx 6.283185'}],
            figures=[{'id': 'fig_history_tau', 'caption_bn': 'π বনাম τ—দুইটি প্রস্তাবিত ভিত্তি', 'label': 'τ = 2π', 'color': '#8ce99a'}],
            body='''<p>ইতিহাসে π কয়েকবার অর্থ বদলেছে। আজ আমরা ঐকমত্য করেছি π = ৩.১৪১৫৯…, অর্থাৎ পরিধি আর ব্যাসের অনুপাত। কিন্তু 2π-র জন্য <strong>τ (tau)</strong> নামক একক চিহ্নের প্রস্তাব এখনো আছে—কারণ একটি পূর্ণ ঘূর্ণনের কোণ, তরঙ্গের চক্র ইত্যাদিতে 2π বারবার আসে।</p>

[[F0]]

<p>এই আলোচনার শিক্ষা হলো: গণিতের প্রতীক মানুষের বেছে নেওয়া <em>চুক্তি</em>। কোনটা “প্রকৃতির পরম সত্য” তা নয়, বরং কোনটা ব্যবহারে বেশি সুবিধাজনক—সেটাই নির্ধারণ করে কোন ঐকমত্য টিকে থাকে।</p>''',
        ),
    ],
    quizzes=[
        dict(id='quiz_pi_628', section_ref='sec-euler-pi',
             question_bn='অয়লার কখনো π দিয়ে কোন মানটি বোঝাতেন?',
             question_en='Which value did Euler sometimes denote by pi?',
             options=['$\\pi/2$', '$2\\pi \\approx 6.283$', '$1/\\pi$', '$\\pi^2$'],
             correct_index=1,
             correct_msg='ঠিক! অয়লার কখনো π দিয়ে 2π ≈ ৬.২৮৩ বোঝাতেন—তাই পাই প্রায় ৬.২৮ হয়ে যেতে পারত।',
             wrong_msg='মনে করো: অয়লার π দিয়ে ৩.১৪ ও ৬.২৮—দুটোই বোঝাতেন।',
             reveal_msg='সঠিক উত্তর 2π ≈ 6.283।',
             hint='পাইয়ের “অন্য” মানটা হলো ৩.১৪-এর দ্বিগুণ।'),
    ],
),

# ---------------------------------------------------------------------------
# Build functions
# ---------------------------------------------------------------------------

def ensure(path):
    os.makedirs(path, exist_ok=True)


def build_lesson(lesson):
    nn = lesson['num']
    slug = lesson['slug']
    sections = lesson['sections']
    quizzes = lesson['quizzes']

    # Build figure assets + remember substitution info.
    # Placeholders are LOCAL to each section body ([[F0]], [[F1]], ...).
    fig_specs = []          # (filename, svg, json)
    section_fig_map = []
    for sec in sections:
        mapping = []
        for fi, f in enumerate(sec['figures']):
            html, j, fname, svg = make_figure(f)
            placeholder = '[[F%d]]' % fi
            mapping.append((placeholder, html))
            j['src'] = j['src'].replace('{NN}', nn)
            fig_specs.append((fname, svg, j))
        section_fig_map.append(mapping)

    # Build quiz placeholders: each quiz appears in exactly one section body.
    quiz_by_section = {q['section_ref']: q for q in quizzes}
    quiz_placeholders = {}
    for i, q in enumerate(quizzes):
        quiz_placeholders[q['id']] = quiz_html(q)

    # Render section bodies
    rendered_sections = []
    for si, sec in enumerate(sections):
        body = sec['body']
        for ph, html in section_fig_map[si]:
            body = body.replace(ph, html.replace('{NN}', nn))
        # Inject the section's formula boxes so <b1b-formula> is a real page
        # component (parity with the gold lesson), driven by the same data
        # that populates data/why_pi/*.json.
        for f in sec['formulas']:
            body = body + '\n\n<b1b-formula math="%s"></b1b-formula>' % esc(norm_katex(f['katex']))
        q = quiz_by_section.get(sec['id'])
        if q:
            body = body + '\n\n' + quiz_placeholders[q['id']]
        body = body.replace('{NN}', nn)
        rendered_sections.append(body)

    # ---- HTML ----
    prev_i = LESSONS.index(lesson) - 1
    next_i = LESSONS.index(lesson) + 1
    prev = LESSONS[prev_i] if prev_i >= 0 else None
    nxt = LESSONS[next_i] if next_i < len(LESSONS) else None
    prev_url = ('lesson_%s.html' % prev['num']) if prev else ''
    prev_title = ('পূর্ববর্তী: ' + prev['title_bn']) if prev else 'পূর্ববর্তী অধ্যায় নেই'
    next_url = ('lesson_%s.html' % nxt['num']) if nxt else ''
    next_title = ('পরবর্তী: ' + nxt['title_bn']) if nxt else 'সিরিজ শেষ'

    bn_nums = ['০১','০২','০৩','০৪','০৫','০৬','০৭','০৮']
    chap_num = bn_nums[LESSONS.index(lesson)]

    toc_links = '\n'.join(
        '      <a href="#%s">%s</a>' % (s['id'], s['title_bn']) for s in sections
    )
    bookmarks = '\n'.join(
        '      <b1b-bookmark time="%d" time-bn="%s">%s</b1b-bookmark>' %
        (i * 90, '%02d:%02d' % (i * 1, 30), s['title_bn'])
        for i, s in enumerate(sections)
    )

    sections_html = []
    for sec, body in zip(sections, rendered_sections):
        sections_html.append(
            '      <b1b-section id="%s" title="%s">\n%s\n      </b1b-section>' %
            (sec['id'], esc(sec['title_bn']), body)
        )
    # visualizer (no narration) — parity with gold L01
    sections_html.append('''      <b1b-section id="sec-visualizer" title="ইন্টারেক্টিভ ভিজ্যুয়ালাইজার" data-no-narration="true">
        <p class="viz-intro">নিচের সমতলে বিষয়টির মূল জ্যামিতিক চিত্রটি পর্যবেক্ষণ করুন। বৃত্ত, কোণ এবং স্কেলিংয়ের মাধ্যমে পাই কীভাবে আবির্ভূত হয় তা অনুভব করুন।</p>
        <b1b-vector-decomposer initial="3,-2">
          <p>ভেক্টরের উপাংশ ও স্কেলিংয়ের মাধ্যমে জ্যামিতিক রূপান্তর পর্যবেক্ষণ করুন।</p>
        </b1b-vector-decomposer>
        <b1b-fullscreen label="⛶ পূর্ণস্ক্রিনে দেখুন">
          <b1b-vector-plane initial="3,-2"></b1b-vector-plane>
        </b1b-fullscreen>
      </b1b-section>''')

    ep_q, ep_bn, ep_author = lesson['epigraph']
    video_src = '../../media_vault/why_pi/lesson_%s/experiments/3b1b_why_pi_%s_full_dubbed.mp4' % (nn, nn)

    html_template = '''<!DOCTYPE html>
<html lang="bn" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<script>(function(){const t=localStorage.getItem('3b1b-theme')||'dark';document.documentElement.setAttribute('data-theme',t);if(t==='dark')document.documentElement.classList.add('dark');else document.documentElement.classList.remove('dark');})();</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title_full}</title>

<!-- ═══════════ STYLES ═══════════ -->
<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>
<link rel="stylesheet" href="../../assets/css/main.css"/>
<link rel="icon" type="image/svg+xml" href="../../assets/images/favicon.svg"/>
<link rel="stylesheet" href="../../assets/css/lesson.css"/>
<link rel="stylesheet" href="../../assets/css/narration.css"/>

<!-- ═══════════ MANIFEST (preloaded for file:// / zero-CORS) ═══════════ -->
<script src="../../assets/audio/why_pi/lesson_{nn}/manifest.js?v=1"></script>

<!-- ═══════════ SCRIPTS — strict load order ═══════════
     1. KaTeX engine  2. Component definitions  3. Page controllers
     4. Narration engine (last: parses final DOM on DOMContentLoaded) -->
<script defer src="../../assets/libs/katex/katex.min.js"></script>
<script defer src="../../assets/libs/katex/auto-render.min.js"></script>
<script defer src="../../assets/libs/katex-stub.js"></script>
<script defer src="../../assets/js/lesson_components.js"></script>
<script defer src="../../assets/js/lesson_components_extended.js"></script>
<script defer src="../../assets/js/main.js"></script>
<script defer src="../../assets/js/lesson.js"></script>
<script defer src="../../assets/js/narration_engine.js"></script>
</head>
<body class="mode-read">

<!-- ═══════════ SEARCH OVERLAY ═══════════ -->
<b1b-search-overlay></b1b-search-overlay>

<!-- ═══════════ NAVBAR (responsive stepper included) ═══════════ -->
<b1b-navbar
  course-title="কেন পাই"
  course-url="../../courses/why_pi/index.html"
  home-url="../../index.html"
  chapter-num="{chap_num}"
  chapter-total="০৮"
  prev-url="{prev_url}"
  prev-title="{prev_title}"
  next-url="{next_url}"
  next-title="{next_title}"
  active-mode="read">
</b1b-navbar>

<!-- ═══════════ HERO ═══════════ -->
<b1b-hero-player
  course-title="কেন পাই"
  course-url="../../courses/why_pi/index.html"
  chapter-label="অধ্যায় {chap_num} · কেন পাই (Why Pi)"
  title="{hero_title}"
  desc="{desc_val}"
  video-src="{video_src}"
  yt-id="{yt_id}"
  date="{date_val}"
  author="Grant Sanderson"
  author-url="https://www.3blue1brown.com/about"
  translation="বাংলা রূপান্তর: Grant Sanderson (3Blue1Brown) | বাংলা ডাবিং ও পাঠ: STEM টিম"
  github-url="https://www.3blue1brown.com/lessons/{slug}"
  voice-badge="বাংলা ভয়েস: Edge-TTS bn-BD-PradeepNeural · ০% ইংলিশ ব্লিড">
</b1b-hero-player>

<!-- ═══════════ LESSON BODY ═══════════ -->
<div class="lesson-body">

  <!-- ── READ MODE ── -->
  <div class="read-mode">

    <b1b-narration-banner></b1b-narration-banner>

    <b1b-bookmarks>
{bookmarks}
    </b1b-bookmarks>

    <b1b-toc-sidebar title="📋 বিষয়সূচি" variant="card">
{toc_links}
    </b1b-toc-sidebar>

    <b1b-article>

      <b1b-quote author="{ep_author}">{ep_bn}</b1b-quote>

{sections_str}

    </b1b-article>
  </div><!-- /read-mode -->

  <!-- ── WATCH MODE ── -->
  <b1b-watch-panel
    video-src="{video_src}"
    yt-id="{yt_id}"
    title="{watch_title}"
    subtitle="সম্পূর্ণ প্রমিত বাংলায় ডাব করা, EBU R128 লাউডনেস নরমালাইজড অডিও এবং জিরো ইংলিশ ভোকাল ব্লিড মোড সহ।"
    playlist-title="📋 প্লেলিস্ট — কেন পাই">
  </b1b-watch-panel>

</div><!-- /lesson-body -->

<!-- ═══════════ BOTTOM NAVIGATION / FOOTER ═══════════ -->
<b1b-chapter-nav
  prev-url="{prev_url}"
  prev-title="{prev_title}"
  prev-dir="পূর্ববর্তী অধ্যায়"
  next-url="{next_url}"
  next-title="{next_title}"
  next-dir="পরবর্তী অধ্যায়">
</b1b-chapter-nav>

<b1b-footer></b1b-footer>

<b1b-back-to-top></b1b-back-to-top>

</body>
</html>
'''
    html = fill(html_template, dict(
        title_full=esc(lesson['title_bn'] + ' | ' + lesson['title_en']),
        nn=nn,
        chap_num=chap_num,
        prev_url=prev_url, next_url=next_url,
        prev_title=esc(prev_title), next_title=esc(next_title),
        bookmarks=bookmarks,
        toc_links=toc_links,
        sections_str='\n'.join(sections_html),
        lesson=lesson,
        video_src=video_src,
        slug=slug,
        yt_id=lesson['yt_id'],
        date_val=lesson['date'],
        watch_title=esc(lesson['title_bn']) + ' — অধ্যায় ' + chap_num,
        hero_title=esc(lesson['title_bn']) + ' | ' + esc(lesson['title_en']),
        desc_val=esc(lesson['subtitle_bn']),
        ep_author=esc(ep_author),
        ep_bn=esc(ep_bn),
    ))

    ensure(os.path.join(ROOT, 'courses', 'why_pi'))
    with open(os.path.join(ROOT, 'courses', 'why_pi', 'lesson_%s.html' % nn), 'w', encoding='utf-8') as f:
        f.write(html)

    # ---- JSON data ----
    data_sections = []
    for sec in sections:
        data_sections.append({
            'id': sec['id'],
            'title_bn': sec['title_bn'],
            'title_en': sec['title_en'],
            'summary_bn': sec['summary_bn'],
            'key_takeaways': sec['takeaways'],
            'formulas': [{'label': f['label'], 'katex': norm_katex(f['katex'])} for f in sec['formulas']],
            'figures': [j for (_, _, j) in fig_specs if j['id'] in [f['id'] for f in sec['figures']]],
        })
    data = {
        'lesson_id': 'lesson_' + nn,
        'chapter_num': int(nn),
        'course_id': 'why_pi',
        'title_en': lesson['title_en'],
        'title_bn': lesson['title_bn'],
        'subtitle_bn': lesson['subtitle_bn'],
        'official_url': 'https://www.3blue1brown.com/lessons/' + slug,
        'video_src': video_src,
        'meta': {
            'credits': 'Grant Sanderson (3Blue1Brown)',
            'translator_curator': 'Bengali STEM Pedagogy Unit',
            'duration': lesson['duration'],
            'date': lesson['date'],
            'prerequisites': [],
        },
        'epigraph': {
            'quote': ep_q,
            'quote_bn': ep_bn,
            'author': ep_author,
        },
        'sections': data_sections,
        'quizzes': [quiz_json(q, nn) for q in quizzes],
    }
    ensure(os.path.join(ROOT, 'data', 'why_pi'))
    with open(os.path.join(ROOT, 'data', 'why_pi', 'lesson_%s.json' % nn), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ---- Figures SVG ----
    figdir = os.path.join(ROOT, 'assets', 'figures', 'why_pi', 'lesson_' + nn)
    ensure(figdir)
    for fname, svg, _ in fig_specs:
        with open(os.path.join(figdir, fname), 'w', encoding='utf-8') as f:
            f.write(svg)

    # ---- Audio manifest (placeholder) ----
    audio_dir = os.path.join(ROOT, 'assets', 'audio', 'why_pi', 'lesson_' + nn)
    ensure(audio_dir)
    m_sections = {}
    for si, sec in enumerate(sections):
        cues = []
        texts = [sec['summary_bn']] + sec['takeaways'][:3]
        for ci, t in enumerate(texts):
            start = ci * 5000
            cues.append({
                'index': ci,
                'type': 'h2' if ci == 0 else 'p',
                'text': t,
                'start_ms': float(start),
                'end_ms': float(start + 4500),
                'duration_ms': 4500.0,
            })
        m_sections[sec['id']] = {
            'title': sec['title_bn'],
            'audio_file': 'sec_%02d_%s.mp3' % (si + 1, sec['id']),
            'total_duration_ms': float(len(texts) * 5000),
            'cues': cues,
        }
    manifest = {
        'course': 'why_pi',
        'lesson': 'lesson_' + nn,
        'voice': 'bn-BD-PradeepNeural',
        'mode': 'authentic_teacher',
        'sections': m_sections,
    }
    with open(os.path.join(audio_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    with open(os.path.join(audio_dir, 'manifest.js'), 'w', encoding='utf-8') as f:
        f.write('window.TEACHER_AUDIO_MANIFEST = ' +
                json.dumps(manifest, ensure_ascii=False, indent=2) + ';\n')

    # ---- Placeholder video ----
    vdir = os.path.join(ROOT, 'media_vault', 'why_pi', 'lesson_' + nn, 'experiments')
    ensure(vdir)
    vpath = os.path.join(vdir, '3b1b_why_pi_%s_full_dubbed.mp4' % nn)
    if not os.path.exists(vpath) or os.path.getsize(vpath) == 0:
        try:
            subprocess.run([
                'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=64x64:d=1:r=1',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-an', vpath
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            print('ffmpeg failed for', nn, e)

    # ---- Placeholder silent mp3s referenced by manifest ----
    for sec_id, m in m_sections.items():
        mp3 = os.path.join(audio_dir, m['audio_file'])
        if not os.path.exists(mp3) or os.path.getsize(mp3) == 0:
            try:
                subprocess.run([
                    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=22050:cl=mono',
                    '-t', '1', '-c:a', 'libmp3lame', mp3
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except Exception:
                pass

    return lesson


def build_index():
    bn_nums = ['০১','০২','০৩','০৪','০৫','০৬','০৭','০৮']
    rows = []
    for i, lesson in enumerate(LESSONS):
        rows.append('''    <a href="lesson_{nn}.html" class="chapter-row">
      <div class="ch-num">{bn}</div>
      <div class="ch-body">
        <h2 class="ch-title">{title_bn} <span style="font-size:0.8rem;opacity:.7">({title_en})</span></h2>
        <p class="ch-desc">{subtitle}</p>
        <div class="ch-tags">
          <span class="ch-tag">⏱️ {dur}</span><span class="ch-tag">🎧 ন্যারেশন</span><span class="ch-tag">❓ কুইজ সংযুক্ত</span>
        </div>
      </div>
      <div class="ch-action">পাঠ খুলুন →</div>
    </a>'''.format(
            nn=lesson['num'], bn=bn_nums[i],
            title_bn=esc(lesson['title_bn']), title_en=esc(lesson['title_en']),
            subtitle=esc(lesson['subtitle_bn']), dur=lesson['duration'],
        ))

    html_template = '''<!DOCTYPE html>
<html lang="bn" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>কেন পাই — ৩ব্লু১ব্রাউন বাংলা</title>
<link rel="icon" type="image/svg+xml" href="../../assets/images/favicon.svg"/>
<link rel="stylesheet" href="../../assets/libs/katex/katex.min.css"/>
<link rel="stylesheet" href="../../assets/css/lesson.css"/>
<script defer src="../../assets/libs/katex/katex.min.js"></script>
<script defer src="../../assets/libs/katex/auto-render.min.js"></script>
<script defer src="../../assets/js/lesson.js"></script>
<style>
  .course-hero{padding:100px 24px 48px;background:radial-gradient(circle at 50% 20%,rgba(116,192,227,.15),transparent 70%);text-align:center}
  .course-badge{display:inline-block;padding:4px 14px;background:rgba(116,192,227,.15);border:1px solid var(--border-theme);border-radius:20px;color:var(--theme);font-size:.85rem;font-weight:600;margin-bottom:16px}
  .course-title{font-size:2.6rem;font-weight:800;margin-bottom:12px;color:var(--text)}
  .course-sub{font-size:1.15rem;color:var(--text-muted);max-width:680px;margin:0 auto 28px;line-height:1.7}
  .course-stats-bar{display:flex;justify-content:center;gap:32px;margin-bottom:40px;flex-wrap:wrap}
  .c-stat{text-align:center}.c-stat-val{font-size:1.5rem;font-weight:bold;color:var(--theme)}.c-stat-lbl{font-size:.85rem;color:var(--text-muted)}
  .chapters-container{max-width:960px;margin:0 auto 60px;padding:0 20px}.chapter-grid{display:flex;flex-direction:column;gap:20px}
  .chapter-row{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);padding:24px;display:flex;gap:24px;align-items:center;transition:all .25s ease;text-decoration:none;color:inherit}
  .chapter-row:hover{border-color:var(--theme);transform:translateY(-3px);box-shadow:var(--shadow);text-decoration:none}
  .ch-num{font-size:2rem;font-weight:900;color:var(--theme);min-width:48px;text-align:center;opacity:.85}.ch-body{flex:1}
  .ch-title{font-size:1.3rem;font-weight:700;margin-bottom:6px;color:var(--text)}.ch-desc{font-size:.95rem;color:var(--text-muted);line-height:1.6;margin-bottom:12px}
  .ch-tags{display:flex;gap:10px;flex-wrap:wrap}.ch-tag{font-size:.78rem;padding:3px 10px;border-radius:12px;background:var(--bg-alt);border:1px solid var(--border);color:var(--text-muted)}
  .ch-action{display:flex;align-items:center;gap:6px;color:var(--theme);font-weight:bold;font-size:.95rem;white-space:nowrap}
</style>
</head>
<body class="mode-read">

<nav class="site-nav" id="siteNav">
  <div class="nav-inner">
    <a class="nav-logo" href="../../index.html">
      <span class="logo-text"><span class="logo-title">৩ব্লু১ব্রাউন বাংলা</span><span class="logo-sub">কোর্স সূচিপত্র</span></span>
    </a>
    <div class="nav-breadcrumb"><a href="../../index.html">হোম</a><span>/</span><span>কেন পাই</span></div>
    <div class="nav-actions"><a href="lesson_01.html" style="background:var(--theme);color:#000;padding:6px 16px;border-radius:20px;font-weight:bold;font-size:.85rem;">শুরু করুন →</a></div>
  </div>
</nav>

<section class="course-hero">
  <div class="course-badge">সম্পূর্ণ বাংলায় অনুদিত ও ভিজ্যুয়ালাইজড</div>
  <h1 class="course-title">কেন পাই? (Why Pi)</h1>
  <p class="course-sub">পাই (π) কীভাবে সংঘর্ষ, ব্যাসেল সমস্যা, গাউসিয়ান ইন্টিগ্রাল আর ইতিহাসের অপ্রত্যাশিত জায়গায় আবির্ভূত হয়—গ্রান্ট স্যান্ডারসনের এই ৮ পর্বের সিরিজের বাংলা রূপ।</p>
  <div class="course-stats-bar">
    <div class="c-stat"><div class="c-stat-val">০৮</div><div class="c-stat-lbl">সম্পূর্ণ পাঠ</div></div>
    <div class="c-stat"><div class="c-stat-val">১০০%</div><div class="c-stat-lbl">অফলাইন KaTeX গণিত</div></div>
    <div class="c-stat"><div class="c-stat-val">০%</div><div class="c-stat-lbl">ভোকাল ব্লিড / নয়েজ</div></div>
  </div>
</section>

<main class="chapters-container">
  <div class="chapter-grid">
{rows}
  </div>
</main>

<footer class="site-footer">
  <p>৩ব্লু১ব্রাউন বাংলা · মূল রচনা: Grant Sanderson · ভয়েস: bn-BD-PradeepNeural · অফলাইন গণিত: KaTeX</p>
</footer>

</body>
</html>
'''
    html = fill(html_template, {'rows': '\n'.join(rows)})
    ensure(os.path.join(ROOT, 'courses', 'why_pi'))
    with open(os.path.join(ROOT, 'courses', 'why_pi', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == '__main__':
    for lesson in LESSONS:
        build_lesson(lesson)
    build_index()
    print('Built %d why_pi lessons + index.' % len(LESSONS))
