# -*- coding: utf-8 -*-
"""
Generate one self-contained gold-standard teacher-audio builder per PHYSICS
lesson from the authoritative DOM snapshots + course data JSON.

Outputs: governance/build_expressive_teacher_audio_physicsNN.py (NN=01..13)
Each generated builder embeds clean, phonetic, expressive Bengali scripts for
every DOM cue and uses the gold calc02 synthesis/concat/manifest logic.
"""
import os
import re
import json
import unicodedata

GOV = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(GOV)

ORIGINALS = ["প্রথম", "দ্বিতীয়", "তৃতীয়", "চতুর্থ"]


# --------------------------------------------------------------------------- #
# Phonetic / cleanup pipeline (all spoken scripts must be clean Bengali)
# --------------------------------------------------------------------------- #
# English -> Bengali phonetic safeguards (physics domain + generic).
EN = {
    "hologram": "হলোগ্রাম", "holograms": "হলোগ্রাম", "holographic": "হলোগ্রাফিক",
    "physics": "পদার্থবিজ্ঞান", "cosmic": "মহাজাগতিক", "cosmology": "মহাজগত্তত্ব",
    "prism": "প্রিজম", "quantum": "কোয়ান্টাম", "uncertainty": "অনিশ্চয়তা",
    "turbulence": "অশান্ত প্রবাহ", "turbulent": "অশান্ত", "refraction": "প্রতিসরণ",
    "snell": "স্নেল", "interference": "ব্যতিচার", "polarization": "মেরুকরণ",
    "polarization": "মেরুকরণ", "polarised": "মেরুকৃত", "polarized": "মেরুকৃত",
    "parallax": "প্যারালাক্স", "parsec": "পারসেক", "arcsecond": "আর্কসেকেন্ড",
    "arcsec": "আর্কসেকেন্ড", "cepheid": "সেফিড", "hubble": "হাবল",
    "kepler": "কেপলার", "redshift": "লাল সরণ", "supernova": "সুপারনোভা",
    "chiral": "কাইরাল", "analyzer": "আনালাইজার", "analyser": "আনালাইজার",
    "polarizer": "পোলারাইজার", "polariser": "পোলারাইজার", "retarded": "বিলম্বিত",
    "hodograph": "হোডোগ্রাফ", "brachistochrone": "ব্র্যাকিস্টোক্রন",
    "cycloid": "সাইক্লয়েড", "heisenberg": "হাইজেনবার্গ",
    "kolmogorov": "কলমোগরভ", "feynman": "ফাইনম্যান", "photon": "ফোটন",
    "photons": "ফোটন", "slit": "স্লিট", "frequency": "কম্পাঙ্ক",
    "electromagnetic": "তড়িৎচুম্বকীয়", "wavelength": "তরঙ্গদৈর্ঘ্য",
    "velocity": "বেগ", "gravity": "মাধ্যাকর্ষণ", "veritasium": "ভেরিটাসিয়াম",
    "standard": "স্ট্যান্ডার্ড", "candle": "ক্যান্ডেল", "candles": "ক্যান্ডেল",
    "phase": "দশা", "electron": "ইলেকট্রন", "electrons": "ইলেকট্রন",
    "spectrum": "বর্ণালি", "microscale": "অতিক্ষুদ্র মাত্রা",
    "universality": "সার্বজনীনতা", "cascade": "ক্যাসকেড", "spectrum": "বর্ণালি",
    "springs": "স্প্রিং", "wave": "তরঙ্গ", "waves": "তরঙ্গ",
    "optical": "আলোক", "active": "সক্রিয়", "linear": "রৈখিক",
    "polarisation": "মেরুকরণ", "digital": "ডিজিটাল", "data": "ডাটা",
    # Additional physics / notation terms found in the corpus.
    "sin": "সাইন", "cos": "কোস", "theta": "থিটা", "em": "এম",
    "hbar": "এইচ বার", "hf": "এইচ এফ", "eta": "ইটা",
    "superposition": "সুপারপজিশন", "potential": "বিভব", "spike": "স্পাইক",
    "epsilon": "এপসিলন", "eddy": "ঘূর্ণি", "whorls": "ঘূর্ণি",
    "astronomical": "জ্যোতির্বৈজ্ঞানিক", "unit": "একক", "energy": "শক্তি",
    "differential": "অবকলন", "equation": "সমীকরণ", "projection": "প্রক্ষেপণ",
    "projections": "প্রক্ষেপণ", "total": "মোট", "internal": "আন্তঃ",
    "reflection": "প্রতিফলন", "algo": "অ্যালগরিদম", "unlock": "খুলে দেয়",
    "tautochrone": "টাউটোক্রন", "variational": "পরিবর্তনীয়",
    "calculus": "ক্যালকুলাস", "big": "বড়", "little": "ছোট",
    "have": "আছে", "which": "যা", "feed": "খাওয়ায়", "their": "তাদের",
    "on": "ওপর", "of": "অব", "saman": "সমান", "larger": "বড়",
    "ε": "এপসিলন",
}
# Standalone symbols / roman tokens inside Bengali prose.
TOKEN = {
    "AU": "এ ইউ", "pc": "পারসেক", "T²": "টি বর্গ", "a³": "এ ঘন",
    "1a": "ওয়ান এ", "1A": "ওয়ান এ", "3D": "থ্রিডি", "2D": "টুডি",
    "AI": "এআই", "EGM": "ইজিএম", "API": "এপিআই", "UI": "ইউআই", "ML": "এমএল",
    "x": "এক্স", "y": "ওয়াই", "T": "টি", "M": "এম", "m": "এম",
    "d": "ডি", "v": "ভি", "n": "এন", "E": "ই", "F": "এফ", "k": "কে",
}
# Single-letter / short roman tokens found in the corpus.
TOKEN.update({
    "c": "সি", "a": "এ", "A": "এ", "B": "বি", "p": "পি",
})

# Whole-phrase substitutions applied before word-level replacements.
PHRASES = {
    "astronomical unit বা": "জ্যোতির্বৈজ্ঞানিক একক বা",
    "unlock করে দেয়": "খুলে দেয়",
}

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def strip_html(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = (text.replace("&nbsp;", " ").replace("&amp;", " ও ")
                .replace("&lt;", " ").replace("&gt;", " ")
                .replace("&quot;", "").replace("&#39;", ""))
    return text


def strip_emoji(text):
    out = []
    for ch in text:
        cp = ord(ch)
        if (0x1F000 <= cp <= 0x1FAFF) or (0x2600 <= cp <= 0x27BF) or cp in (0xFE0F, 0x200D):
            continue
        out.append(ch)
    return "".join(out)


def clean(text):
    """Turn any source block text into clean, phonetic, spoken Bengali."""
    t = strip_html(text)
    t = strip_emoji(t)

    # Whole-phrase fixes and quoted English spans (e.g. the Richardson poem).
    for phrase, repl in PHRASES.items():
        t = t.replace(phrase, repl)
    t = re.sub(r"'[^']*[A-Za-z][^']*'", "", t)
    # Source-markup artifacts: repeated "_algo" placeholders and raw subscripts.
    t = re.sub(r"(?:_?algo)+", "", t, flags=re.I)
    t = t.replace("₁", "১").replace("₂", "২").replace("₃", "৩")
    # Exponents and fractions written with ASCII notation in the source.
    t = re.sub(r"\^\(([^)]*)\)", r" ঘাত \1", t)
    t = re.sub(r"(\d)/(\d)", r"\1 ভাগ \2", t)
    t = t.replace("/", ", ")
    t = t.replace("=", " সমান ")

    # Unicode sign -> spoken word (do before generic symbol stripping).
    t = t.replace("→", ", ").replace("⇒", ", ")
    t = t.replace("∝", " সমানুপাতিক ").replace("≈", " প্রায় সমান ")
    t = t.replace("≥", " কমপক্ষে ").replace("≤", " সর্বোচ্চ ")
    t = t.replace("∞", " অসীম ").replace("×", " গুণ ")
    t = t.replace("²", " বর্গ ").replace("³", " ঘন ")

    # Parentheticals that contain Latin letters carry English glossary terms;
    # the Bengali equivalent always precedes them, so drop the whole group.
    t = re.sub(r"\([^)]*[A-Za-z][^)]*\)", "", t)
    # Standalone roman tokens (longest first).
    for tok in sorted(TOKEN, key=len, reverse=True):
        t = re.sub(r"(?<![A-Za-z])" + re.escape(tok) + r"(?![A-Za-z])", TOKEN[tok], t)
    # English words -> Bengali phonetics (longest first, word-bounded).
    for en in sorted(EN, key=len, reverse=True):
        t = re.sub(r"\b" + re.escape(en) + r"\b", EN[en], t, flags=re.I)

    # Dashes and misc punctuation -> natural pause / space.
    t = t.replace("—", "। ").replace("–", " ").replace("−", " ").replace("-", " ")
    t = t.replace(";", ",").replace(":", ",")
    t = t.replace("[", "").replace("]", "").replace("{", "").replace("}", "")
    t = t.replace("\\", " ").replace("$", " ").replace("|", " ")

    # Stuck-together notation (no word boundary after subscript digits).
    t = t.replace("sin", " সাইন ").replace("cos", " কোস ").replace("θ", " থিটা ")
    # Digits to Bengali; drop stray underscores; collapse whitespace.
    t = t.translate(BN_DIGITS)
    t = t.replace("_", " ")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([।,?])", r"\1", t)
    t = re.sub(r",\s*,", ",", t)
    t = t.replace("? ।", "?").replace("। ।", "।").replace(", ।", "।")
    return t


def sentences(text):
    return [s.strip() for s in text.split("।") if s.strip()]


def end_sentence(text):
    """Append a full stop only when the clause does not already end in one."""
    s = text.strip()
    if not s:
        return s
    return s if s[-1] in "।?!." else s + "।"


def ensure_min(text, n=2):
    """Ensure at least n sentences by borrowing a neutral pedagogical closer."""
    s = sentences(text)
    if len(s) >= n:
        return text
    closers = [
        "এই ধারণাটি মনে রাখলে পরের ধাপগুলো বোঝা অনেক সহজ হবে।",
        "এই পর্যবেক্ষণই আমাদের পরবর্তী প্রশ্নের উত্তর খুঁজতে সাহায্য করবে।",
    ]
    k = 0
    while len(s) < n:
        base = text.rstrip()
        sep = " " if base and base[-1] not in "।,.?" else " "
        text = base + sep + closers[k % len(closers)]
        k += 1
        s = sentences(text)
    return text


# Explicit, natural Bengali readings for every unique formula in the course.
FORMULA_READ = {
    r"d\sin\theta = m\lambda":
        "পথ পার্থক্য ডি সাইন থিটা সমান em ল্যাম্বডা। অর্থাৎ দুই রশ্মির পথের পার্থক্য "
        "সাইন থিটার সাথে সমানুপাতিক, আর em হলো ব্যতিচারের ক্রম, ল্যাম্বডা হলো তরঙ্গদৈর্ঘ্য।",
    r"I = |E_o + E_r|^2 = |E_o|^2 + |E_r|^2 + 2|E_o||E_r|\cos\phi":
        "রেকর্ডকৃত তীব্রতা আই সমান অবজেক্ট ক্ষেত্র ই ও এবং রেফারেন্স ক্ষেত্র ই আরের যোগফলের বর্গ। "
        "এটি আবার ই ও-র বর্গ প্লাস ই আর-র বর্গ প্লাস দুই ই ও ই আর কোস ফাই। শেষ পদটিই দশার তথ্য বহন করে।",
    r"d\,(\mathrm{pc}) = \frac{1}{p\,(\mathrm{arcsec})}":
        "দূরত্ব ডি, পারসেক এককে, সমান এক ভাগে প্যারালাক্স পি, আর্কসেকেন্ড এককে। "
        "অর্থাৎ প্যারালাক্স যত ছোট, তারা তত দূরে।",
    r"m - M = 5\log_{10}\!\left(\frac{d}{10\,\mathrm{pc}}\right)":
        "দূরত্ব মডুলাস এম বিয়োগ বড় এম সমান পাঁচ গুণ লগ, যার ভিত্তি দশ আর বিষয় ডি ভাগ দশ পারসেক। "
        "দেখা উজ্জ্বলতা ও প্রকৃত উজ্জ্বলতার পার্থক্য থেকেই দূরত্ব বের করা যায়।",
    r"v = H_0\, d":
        "হাবলের সূত্র, বেগ ভি সমান হাবল ধ্রুবক এইচ শূন্য গুণ দূরত্ব ডি। "
        "অর্থাৎ ছায়াপথ যত দূরে, প্রসারণের কারণে সেটি তত দ্রুত সরে যায়।",
    r"T^2 \propto a^3":
        "কেপলারের তৃতীয় সূত্র, টির বর্গ সমানুপাতিক এ ঘন। "
        "অর্থাৎ কক্ষপথের আকার জানলে সময়কালও বের করা যায়।",
    r"d = 10^{(m-M+5)/5}\ \mathrm{pc}":
        "দূরত্ব ডি সমান দশের ঘাত, এম বিয়োগ বড় এম প্লাস পাঁচ ভাগ পাঁচ, একক পারসেক। "
        "সুপারনোভার দেখা ও প্রকৃত উজ্জ্বলতা থেকে এই দূরত্ব পাওয়া যায়।",
    r"I = I_0\cos^2\theta":
        "ম্যালাসের সূত্র, আউটপুট তীব্রতা আই সমান আই শূন্য গুণ কোস থিটার বর্গ। "
        "অর্থাৎ পোলারাইজারের দিকের সাথে কোণ বাড়লে আলো কমে যায়।",
    r"\theta = [\alpha]\, l\, c":
        "ঘূর্ণন কোণ থিটা সমান আলফা ব্র্যাকেট গুণ পথদৈর্ঘ্য এল গুণ ঘনত্ব সি। "
        "দ্রবণের দিক যত বেশি chiral, পথ যত লম্বা, ঘোরানো তত বেশি।",
    r"\mathbf{E}_{\mathrm{rad}} \propto \frac{\mathbf{a}(t_r)}{c^2 r}":
        "বিকিরণ ক্ষেত্র ই রেডিয়েশন সমানুপাতিক ত্বরণ এ, বিলম্বিত সময় টি আর, "
        "ভাগে আলোর বেগের বর্গ সি স্কয়ার গুণ দূরত্ব আর। ত্বরণই তরঙ্গ তৈরি করে।",
    r"\theta = \tfrac12(\phi_L - \phi_R)":
        "ঘূর্ণন থিটা সমান আধা গুণ, বাঁ দশা ফাই এল বিয়োগ ডান দশা ফাই আর। "
        "দুই বৃত্তাকার উপাদানের দশার পার্থক্যের অর্ধেকই দিকের ঘূর্ণন।",
    r"n = \frac{c}{v_p}":
        "প্রতিসরাংক এন সমান শূন্য মাধ্যমে আলোর বেগ সি ভাগে মাধ্যমের ভেতরের বেগ ভি পি। "
        "মাধ্যমে আলো যত ধীর, প্রতিসরাংক তত বেশি।",
    r"n_{\text{violet}} > n_{\text{blue}} > n_{\text{red}}":
        "প্রতিসরাংকের ক্রম, বেগুনির এন বেশি, নীলের তার চেয়ে কম, লালের সবচেয়ে কম। "
        "এজন্যই প্রিজমে বেগুনি সবচেয়ে বেশি বেঁকে যায়।",
    r"n_1\sin\theta_1 = n_2\sin\theta_2":
        "স্নেলের সূত্র, এন ওয়ান সাইন থিটা ওয়ান সমান এন টু সাইন থিটা টু। "
        "দুই মাধ্যমের প্রতিসরাংক আর আপতন কোণ মিলেই প্রতিসৃত কোণ ঠিক হয়।",
    r"v_g = v_p - \lambda\,\frac{dv_p}{d\lambda}":
        "গ্রুপ বেগ ভি জি সমান ফেজ বেগ ভি পি বিয়োগ ল্যাম্বডা গুণ, ভি পির পরিবর্তন ভাগ ল্যাম্বডার পরিবর্তন। "
        "তথা বহন করে গ্রুপ বেগ, ফেজ বেগ নয়।",
    r"t = \int \frac{n(s)\,ds}{c} \;\longrightarrow\; \delta t = 0":
        "ফার্মাটের নীতি, সময় টি হলো প্রতিসরাংক এন ভাগে আলোর বেগ সি এর পথজুড়ে যোগফল, "
        "এবং এর ছোট পরিবর্তন ডেল্টা টি শূন্য। অর্থাৎ আলো সবচেয়ে কম সময়ের পথ বেছে নেয়।",
    r"\sin\theta_c = \frac{n_2}{n_1},\quad n_1>n_2":
        "ক্রিটিক্যাল কোণের ক্ষেত্রে সাইন থিটা সি সমান এন টু ভাগে এন ওয়ান, যেখানে এন ওয়ান এন টুর চেয়ে বড়। "
        "এই কোণের বেশি হলে আলো বের না গিয়ে সম্পূর্ণ প্রতিফলিত হয়।",
    r"E = h f = \hbar\omega":
        "ফোটনের শক্তি ই সমান প্ল্যাঙ্ক ধ্রুবক এইচ গুণ কম্পাঙ্ক এফ, "
        "আবার এটি সমান এইচ বার গুণ কৌণিক কম্পাঙ্ক ওমেগা। কম্পাঙ্ক বাড়লে শক্তিও বাড়ে।",
    r"\sigma_t\,\sigma_f \ge \frac{1}{4\pi}":
        "সময় ও কম্পাঙ্কের অনিশ্চয়তা, সিগমা টি গুণ সিগমা এফ এক ভাগে চার পাই এর চেয়ে বড় বা সমান। "
        "সময় যত নিখুঁত, কম্পাঙ্ক তত অস্পষ্ট।",
    r"\sigma_x\,\sigma_k \ge \tfrac12":
        "অবস্থান ও তরঙ্গসংখ্যার অনিশ্চয়তা, সিগমা এক্স গুণ সিগমা কে আধার চেয়ে বড় বা সমান। "
        "একটিকে কমালে অন্যটি বাড়তেই থাকে।",
    r"\Delta x\,\Delta p \ge \frac{\hbar}{2}":
        "হাইজেনবার্গের অনিশ্চয়তা নীতি, ডেল্টা এক্স গুণ ডেল্টা পি এইচ বার ভাগ দুই এর চেয়ে বড় বা সমান। "
        "অবস্থান ও ভরবেগ একসাথে নিখুঁতভাবে মাপা যায় না।",
    r"\mathbf{F} = -\frac{GMm}{r^2}\,\hat{\mathbf{r}}":
        "নিউটনের মহাকর্ষ বল এফ সমান ঋণাত্মক জি এম এম ভাগে আর বর্গ, "
        "গুণ রেডিয়াল ভেক্টর আর হ্যাট। কাছে গেলে বল বেড়ে যায়।",
    r"v\,\Delta\theta = \frac{GM}{h}":
        "বেগ-চিত্রের ব্যাসার্ধ, ভি গুণ ডেল্টা থিটা সমান জি এম ভাগে এইচ। "
        "ভেক্টরের আগার বক্রতা মাপে মহাকর্ষের শক্তি।",
    r"\frac{1}{r}=\frac{GM}{h^2}\left(1+e\cos\theta\right)":
        "উপবৃত্তের সমীকরণ, এক ভাগে আর সমান জি এম ভাগে এইচ বর্গ, "
        "গুণ এক প্লাস ই কোস থিটা। উৎকেন্দ্রিকতা ই আকার ঠিক করে।",
    r"\varepsilon \sim \frac{u_\ell^3}{\ell}":
        "শক্তি স্থানান্তর হার এপসিলন প্রায় সমান ইউ সুবৃত্তির ঘন ভাগ সুবৃত্তি এল। "
        "বড় ঘূর্ণি ভেঙে ছোট ঘূর্ণিতে শক্তি নামে।",
    r"E(k) = C\,\varepsilon^{2/3} k^{-5/3}":
        "কলমোগরভের বর্ণালি, ই কে সমান সি গুণ এপসিলনের দুই তৃতীয়াংশ ঘাত "
        "গুণ কে-র ঋণাত্মক পাঁচ তৃতীয়াংশ ঘাত। এই সূচকটি সার্বজনীন।",
    r"\eta = \left(\frac{\nu^3}{\varepsilon}\right)^{1/4}":
        "কলমোগরভের অতিক্ষুদ্র মাত্রা eta সমান, নিউর ঘন ভাগে এপসিলন, "
        "এর চতুর্থাংশ ঘাত। এই মাত্রায় শক্তি তাপে রূপ নেয়।",
    r"\frac{\sin\theta}{v} = \text{const}":
        "স্নেলের সূত্রের সাদৃশ্য, সাইন থিটা ভাগে বেগ ভি সমান ধ্রুবক। "
        "সবচেয়ে কম সময়ের পথেই আলো চলে।",
    r"x = a(\theta - \sin\theta),\quad y = a(1-\cos\theta)":
        "সাইক্লয়েডের সমীকরণ, এক্স সমান এ গুণ থিটা বিয়োগ সাইন থিটা, "
        "ওয়াই সমান এ গুণ এক বিয়োগ কোস থিটা। ঘূর্ণায়মান চাকার এক বিন্দুর পথ এটি।",
    r"F = -k\,x":
        "স্প্রিং বল এফ সমান ঋণাত্মক কে গুণ এক্স। স্প্রিং যত টানা হয়, পুনরুদ্ধার বল তত বাড়ে।",
    r"k_1\sin\theta_1 = k_2\sin\theta_2 \;\Longleftrightarrow\; n_1\sin\theta_1 = n_2\sin\theta_2":
        "স্প্রিং মডেল থেকে স্নেল, কে ওয়ান সাইন থিটা ওয়ান সমান কে টু সাইন থিটা টু, "
        "যা আবার এন ওয়ান সাইন থিটা ওয়ান সমান এন টু সাইন থিটা টু এর সমান।",
}


def formula_script(tex_list, label, takeaways):
    key = tex_list[0].strip() if tex_list else ""
    body = FORMULA_READ.get(key)
    if not body:
        # Safe generic fallback (should not be needed — all 31 mapped).
        body = "গাণিতিক সূত্রটি আমাদের পরিবর্তনের নিখুঁত হিসাব দেয়।"
    body = clean(body)
    head = f"গাণিতিক সূত্র, {clean(label)}। " if label else "গাণিতিক সূত্র। "
    return ensure_min(head + body, 2)


FIGURE_OPENERS = [
    "এই চিত্রে দেখা যাচ্ছে, ",
    "চিত্রটি আমাদের দেখায়, ",
    "লক্ষ্য করুন এই চিত্রে, ",
]


def figure_script(text, takeaways, seed):
    cap = clean(text).rstrip("। ")
    opener = FIGURE_OPENERS[seed % len(FIGURE_OPENERS)]
    s1 = end_sentence(opener + cap)
    extras = [end_sentence(clean(t).rstrip("। ")) for t in takeaways[:2]]
    return ensure_min(" ".join([s1] + extras), 2)


def callout_script(text):
    t = clean(text).rstrip("। ")
    return ensure_min(end_sentence("বিশেষ নোট, " + t), 2)


def p_script(text):
    t = clean(text).rstrip("। ")
    return ensure_min(end_sentence(t), 1)


def h2_script(title, idx):
    base = clean(title).rstrip("। ")
    return f"{ORIGINALS[idx % 4]} পরিচ্ছেদ, {end_sentence(base)}"


# --------------------------------------------------------------------------- #
# Builder template (gold calc02 logic, adapted: canonical DOM section keys)
# --------------------------------------------------------------------------- #
TEMPLATE = r'''# -*- coding: utf-8 -*-
"""
AUTO-GENERATED by governance/_generate_physics_builders.py — DO NOT EDIT BY HAND.
Gold-standard TEACHER NARRATION AUDIO for PHYSICS __LESSUP__.

Deterministic, re-runnable, self-contained. Embedded SECTIONS_DATA carries a
clean, phonetic, expressive Bengali script for EVERY cue of the live DOM
(narration_engine selector, KaTeX annotated). Scripts are genuine 2-4 sentence
natural explanations (never the artificial "চিত্র প্রদর্শনী" label).

Usage:  python governance/build_expressive_teacher_audio_physicsNN.py
"""
import os
import re
import json
import copy
import hashlib
import asyncio
import subprocess

import edge_tts

VOICE = "bn-BD-PradeepNeural"
GAP_MS = 350.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(SCRIPT_DIR)
AUDIO_DIR = os.path.join(WORKSPACE, "assets", "audio", "physics", "__LESS__")
MANIFEST_TITLE = "__TITLE__"

PROSODY_DEFAULT = {
    "h2":            ("-5%", "+2Hz", "+0%"),
    "h3":            ("-3%", "+0Hz", "+0%"),
    "chapter-quote": ("-3%", "+0Hz", "+0%"),
    "p":             ("+2%", "+0Hz", "+0%"),
    "figure":        ("-4%", "+0Hz", "+0%"),
    "callout":       ("+0%", "+0Hz", "+0%"),
    "formula-box":   ("-8%", "+0Hz", "+0%"),
}
CONCLUSION_PROSODY = ("-3%", "+0Hz", "+0%")

# DOM-derived parity guards (exact section ids, audio files, cue type order).
EXPECTED_TYPES = __EXPECTED_TYPES__
EXPECTED_AUDIO_FILES = __EXPECTED_AUDIO__

SECTIONS_DATA = __SECTIONS_DATA__

BAD_CHARS = re.compile(r"[A-Za-z\\$⟦⟧{}\[\]—–\-]")
FORBIDDEN_PREFIX = "চিত্র প্রদর্শনী"


def assert_clean_scripts():
    for sec_id, sec in SECTIONS_DATA.items():
        for cue in sec["cues"]:
            bad = BAD_CHARS.findall(cue["tts"])
            if bad:
                raise ValueError(f"{sec_id} cue {cue['index']}: forbidden chars {bad!r} in {cue['tts']!r}")
            if FORBIDDEN_PREFIX in cue["tts"]:
                raise ValueError(f"{sec_id} cue {cue['index']}: artificial figure label present")
    if len(SECTIONS_DATA) != 4:
        raise ValueError("Expected exactly 4 narrated sections")
    total = 0
    for sec_id, sec in SECTIONS_DATA.items():
        types = [c["type"] for c in sec["cues"]]
        if types != EXPECTED_TYPES[sec_id]:
            raise ValueError(f"{sec_id}: cue type/order mismatch -> {types}")
        if sec["audio_file"] != EXPECTED_AUDIO_FILES[sec_id]:
            raise ValueError(f"{sec_id}: audio_file mismatch")
        indices = [c["index"] for c in sec["cues"]]
        if indices != list(range(len(indices))):
            raise ValueError(f"{sec_id}: cue indices are not 0..n-1")
        total += len(indices)
        for cue in sec["cues"]:
            if cue["type"] == "figure":
                s = [x for x in cue["tts"].split("।") if x.strip()]
                if not (2 <= len(s) <= 4):
                    raise ValueError(f"{sec_id} cue {cue['index']}: figure has {len(s)} sentences")
    if total != __TOTAL__:
        raise ValueError(f"Expected __TOTAL__ cues, found {total}")


def get_duration_ms(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    ms = float(out) * 1000.0
    if ms <= 0:
        raise RuntimeError(f"Non-positive duration for {path}: {ms}")
    return ms


def probe_stream(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels", "-of", "json", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout
    st = json.loads(out)["streams"][0]
    return int(st["sample_rate"]), int(st["channels"])


def prosody_for(cue):
    rate, pitch, volume = PROSODY_DEFAULT[cue["type"]]
    if cue.get("role") == "conclusion" and cue["type"] not in ("h2", "formula-box"):
        rate, pitch, volume = CONCLUSION_PROSODY
    return rate, pitch, volume


def valid_audio(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        return get_duration_ms(path) > 0
    except Exception:  # noqa: BLE001
        return False


async def synth_cue(text, path, rate, pitch, volume):
    for attempt in range(10):
        try:
            comm = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, volume=volume)
            await comm.save(path)
            if valid_audio(path):
                return
        except Exception as exc:  # noqa: BLE001
            print(f"    attempt {attempt + 1} failed: {exc}", flush=True)
        await asyncio.sleep(min(0.5 * (2 ** attempt), 8.0))
    raise RuntimeError(f"Failed to synthesise cue: {text[:40]}...")


def make_silence(path, sample_rate, channels, seconds=GAP_MS / 1000.0):
    layout = "mono" if channels == 1 else "stereo"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"anullsrc=r={sample_rate}:cl={layout}",
         "-t", f"{seconds:.3f}", "-c:a", "libmp3lame", "-b:a", "64k", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
    )
    if os.path.getsize(path) == 0:
        raise RuntimeError("Failed to create silence chunk")


def concat_to(final_path, chunk_paths):
    list_path = os.path.splitext(final_path)[0] + "_expressive_concat.txt"
    with open(list_path, "w", encoding="utf-8") as fh:
        for p in chunk_paths:
            fh.write("file '" + p.replace(os.sep, "/") + "'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", list_path, "-c", "copy", final_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
    )
    os.remove(list_path)


async def build_section(sec_id, sec):
    temp = os.path.join(AUDIO_DIR, f"_expressive_tmp_{sec_id}")
    os.makedirs(temp, exist_ok=True)

    sig = hashlib.sha256(
        json.dumps(sec, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    sig_path = os.path.join(temp, "scripts.sha256")
    old = ""
    if os.path.exists(sig_path):
        with open(sig_path, encoding="utf-8") as fh:
            old = fh.read().strip()
    if old != sig:
        for name in os.listdir(temp):
            if name.endswith(".mp3"):
                os.remove(os.path.join(temp, name))
        with open(sig_path, "w", encoding="utf-8") as fh:
            fh.write(sig)

    cues = sec["cues"]
    chunk_paths, durations = [], []
    print(f"\n[{sec_id}] {len(cues)} cues -> {sec['audio_file']}", flush=True)
    for cue in cues:
        idx = cue["index"]
        chunk = os.path.join(temp, f"cue_{idx:02d}.mp3")
        rate, pitch, volume = prosody_for(cue)
        if not valid_audio(chunk):
            print(f"  cue {idx:02d} [{cue['type']:<13}] {rate:>4} {pitch:>5}  {cue['tts'][:30]}...", flush=True)
            await synth_cue(cue["tts"], chunk, rate, pitch, volume)
        else:
            print(f"  cue {idx:02d} [{cue['type']:<13}] cached", flush=True)
        chunk_paths.append(chunk)
        durations.append(get_duration_ms(chunk))

    sample_rate, channels = probe_stream(chunk_paths[0])
    silence = os.path.join(temp, "silence_350ms.mp3")
    make_silence(silence, sample_rate, channels)

    concat_paths = []
    for i, chunk in enumerate(chunk_paths):
        concat_paths.append(chunk)
        if i < len(chunk_paths) - 1:
            concat_paths.append(silence)

    final_path = os.path.join(AUDIO_DIR, sec["audio_file"])
    concat_to(final_path, concat_paths)

    manifest_cues, cursor = [], 0.0
    for i, (cue, dur) in enumerate(zip(cues, durations)):
        start = cursor
        end = start + dur
        manifest_cues.append({
            "index": cue["index"],
            "type": cue["type"],
            "text": cue["tts"],
            "start_ms": round(start, 1),
            "end_ms": round(end, 1),
            "duration_ms": round(dur, 1),
        })
        cursor = end + (GAP_MS if i < len(cues) - 1 else 0.0)

    for i, mc in enumerate(manifest_cues):
        if mc["duration_ms"] <= 0 or mc["end_ms"] <= mc["start_ms"]:
            raise RuntimeError(f"{sec_id} cue {i}: non-positive span")
        if i > 0:
            prev = manifest_cues[i - 1]
            if mc["start_ms"] < prev["end_ms"]:
                raise RuntimeError(f"{sec_id} cue {i}: overlap")
            if abs((mc["start_ms"] - prev["end_ms"]) - GAP_MS) > 1.0:
                raise RuntimeError(f"{sec_id} cue {i}: gap is not {GAP_MS} ms")

    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError(f"{sec_id}: missing/empty output {final_path}")

    print(f"  => {sec['audio_file']}: {len(manifest_cues)} cues, "
          f"{cursor / 1000.0:.2f}s, {os.path.getsize(final_path)} bytes", flush=True)
    return {
        "section_id": sec_id,
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": round(cursor, 1),
        "cues": manifest_cues,
    }


async def build_all():
    assert_clean_scripts()
    print(f"Validated {sum(len(s['cues']) for s in SECTIONS_DATA.values())} clean cues "
          f"in {len(SECTIONS_DATA)} sections.", flush=True)

    manifest_sections = {}
    for sec_id, sec in SECTIONS_DATA.items():
        manifest_sections[sec_id] = await build_section(sec_id, sec)

    manifest_data = {
        "course": "physics",
        "lesson": "__LESS__",
        "title": MANIFEST_TITLE,
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections,
    }
    json_text = json.dumps(manifest_data, ensure_ascii=False, indent=2)
    with open(os.path.join(AUDIO_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(json_text)
    with open(os.path.join(AUDIO_DIR, "manifest.js"), "w", encoding="utf-8") as fh:
        fh.write("window.TEACHER_AUDIO_MANIFEST = " + json_text + ";\n")

    with open(os.path.join(AUDIO_DIR, "manifest.json"), encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert set(loaded["sections"]) == set(SECTIONS_DATA)
    total_cues = 0
    total_ms = 0.0
    figures = 0
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        assert len(msec["cues"]) == len(EXPECTED_TYPES[sec_id])
        path = os.path.join(AUDIO_DIR, msec["audio_file"])
        assert os.path.exists(path) and os.path.getsize(path) > 0
        total_cues += len(msec["cues"])
        total_ms += msec["total_duration_ms"]
        figures += sum(1 for c in msec["cues"] if c["type"] == "figure")
    assert total_cues == __TOTAL__

    print("\n" + "=" * 64)
    print(f"BUILD COMPLETE — expressive teacher audio, Physics __LESSUP__")
    for sec_id in SECTIONS_DATA:
        msec = loaded["sections"][sec_id]
        print(f"  {sec_id:<26} {len(msec['cues']):>2} cues  "
              f"{msec['total_duration_ms'] / 1000.0:>7.2f}s  {msec['audio_file']}")
    print(f"  TOTAL: {total_cues} cues across 4 sections, "
          f"{total_ms / 1000.0:.2f}s, {figures} figure explanations.")
    print("=" * 64)


if __name__ == "__main__":
    asyncio.run(build_all())
'''


def build_sections(n):
    dom = json.load(open(os.path.join(GOV, f"physics{n:02d}_dom_blocks.json"), encoding="utf-8"))
    data = json.load(open(os.path.join(BASE, "data", "physics", f"lesson_{n:02d}.json"), encoding="utf-8"))
    ph = json.load(open(os.path.join(BASE, "assets", "audio", "physics",
                                    f"lesson_{n:02d}", "manifest.json"), encoding="utf-8"))
    dsec = {s["id"]: s for s in data["sections"]}

    sections = {}
    expected_types = {}
    expected_audio = {}
    total = 0
    for si, sec in enumerate(dom["sections"]):
        sid = sec["id"]
        src = dsec.get(sid, {})
        takeaways = src.get("key_takeaways", [])
        label = (src.get("formulas") or [{}])[0].get("label", "")
        psec = ph["sections"][sid]
        audio_file = psec["audio_file"]
        cues = []
        for ci, b in enumerate(sec["blocks"]):
            t = b["type"]
            text = b["text"]
            if t == "h2":
                tts = h2_script(text, si)
            elif t == "p":
                tts = p_script(text)
            elif t == "figure":
                tts = figure_script(text, takeaways, si * 7 + ci)
            elif t == "formula-box":
                tts = formula_script(b.get("tex", []), label, takeaways)
            elif t == "callout":
                tts = callout_script(text)
            elif t == "chapter-quote":
                tts = end_sentence("উদ্ধৃতি, " + clean(text).rstrip("। "))
            else:
                tts = p_script(text)
            cue = {"index": ci, "type": t, "tts": tts}
            # Calm concluding prose on the final non-heading/non-formula cue.
            if ci == len(sec["blocks"]) - 1 and t in ("p", "callout"):
                cue["role"] = "conclusion"
            cues.append(cue)
        sections[sid] = {
            "title": clean(sec["title"]),
            "audio_file": audio_file,
            "cues": cues,
        }
        expected_types[sid] = [c["type"] for c in cues]
        expected_audio[sid] = audio_file
        total += len(cues)
    return sections, expected_types, expected_audio, total, data.get("title_bn", f"পদার্থবিজ্ঞান অধ্যায় {n:02d}")


def dump_literal(obj):
    return json.dumps(obj, ensure_ascii=False, indent=4)


def main():
    for n in range(1, 14):
        sections, etypes, eaudio, total, title = build_sections(n)
        txt = (TEMPLATE
               .replace("__LESSUP__", f"{n:02d}")
               .replace("__LESS__", f"lesson_{n:02d}")
               .replace("__TITLE__", title.replace('"', ""))
               .replace("__EXPECTED_TYPES__", dump_literal(etypes))
               .replace("__EXPECTED_AUDIO__", dump_literal(eaudio))
               .replace("__SECTIONS_DATA__", dump_literal(sections))
               .replace("__TOTAL__", str(total)))
        out = os.path.join(GOV, f"build_expressive_teacher_audio_physics{n:02d}.py")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(txt)
        print(f"physics{n:02d}: {total} cues, {len(sections)} sections -> {os.path.basename(out)}")


if __name__ == "__main__":
    main()
