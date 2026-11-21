#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix_phonetics.py
Lead Phonetic & Audio Quality Engineer – Comprehensive fix for all 5 lessons.

Replaces every TTS-hostile Latin/mixed pattern in the "bn" field of each
master script with clean, phonetically crisp Bengali so Edge-TTS
bn-BD-PradeepNeural reads every axis, hat-vector, and dimension word clearly.
"""

import json, re, copy, sys
from pathlib import Path

BASE = Path(r"D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics\3blue1brown_courses\essence_of_linear_algebra")

SCRIPTS = {
    "L01": BASE / "lesson_01_vectors/dubbing_pipeline/3b1b_lesson_01_bangla_master_script.json",
    "L02": BASE / "lesson_02_span/dubbing_pipeline/3b1b_lesson_02_bangla_master_script.json",
    "L03": BASE / "lesson_03_linear_transformations/dubbing_pipeline/3b1b_lesson_03_bangla_master_script.json",
    "L04": BASE / "lesson_04_matrix_multiplication/dubbing_pipeline/3b1b_lesson_04_bangla_master_script.json",
    "L05": BASE / "lesson_05_3d_transformations/dubbing_pipeline/3b1b_lesson_05_bangla_master_script.json",
}

# ─────────────────────────────────────────────────────────────────────────────
# Universal replacement table: applied to ALL scripts
# Order matters – more specific patterns first
# ─────────────────────────────────────────────────────────────────────────────
GLOBAL_REPLACEMENTS = [
    # ── Axis names ────────────────────────────────────────────────────────────
    ("x-অক্ষ",          "এক্স অক্ষ"),
    ("y-অক্ষ",          "ওয়াই অক্ষ"),
    ("z-অক্ষ",          "জেড অক্ষ"),
    # ── Hat vectors (Latin) ───────────────────────────────────────────────────
    ("i-hat",            "আই হ্যাট"),
    ("j-hat",            "জে হ্যাট"),
    ("k-hat",            "কে হ্যাট"),
    ("i_hat",            "আই হ্যাট"),
    ("j_hat",            "জে হ্যাট"),
    ("k_hat",            "কে হ্যাট"),
    # ── Dimensions ────────────────────────────────────────────────────────────
    ("2D",               "টুডি"),
    ("3D",               "থ্রিডি"),
    # ── Coordinate plane label ────────────────────────────────────────────────
    ("xy-প্লেনের",       "এক্সওয়াই প্লেনের"),
    ("xy-প্লেন",         "এক্সওয়াই প্লেন"),
    ("xy-plane",         "এক্সওয়াই প্লেন"),
    # ── Common Latin terms left raw in BN ─────────────────────────────────────
    ("Linear Transformation",     "লিনিয়ার ট্রান্সফর্মেশন"),
    ("linear transformation",     "লিনিয়ার ট্রান্সফর্মেশন"),
    ("Composition",               "কম্পোজিশন"),
    ("Product",                   "গুণফল"),
    ("Order",                     "ক্রম"),
    ("Shear",                     "শিয়ার"),
    # ── Matrix size notation ──────────────────────────────────────────────────
    ("2x2",              "দুই-বাই-দুই"),
    ("3x3",              "তিন-বাই-তিন"),
    # ── Combined "x and y" / "x এবং y" without axis suffix ──────────────────
    # (only replace when not already fixed as "এক্স" / "ওয়াই")
]

# ─────────────────────────────────────────────────────────────────────────────
# Per-lesson overrides: specific bn strings to completely replace.
# Used where the auto-replacement above is insufficient (mixed script in bn).
# ─────────────────────────────────────────────────────────────────────────────
PER_CUE_OVERRIDES = {
    # Lesson 03 cue overrides
    ("L03", 2): (
        None,   # leave `en` untouched
        "এবং যা প্রথমবারের শিক্ষার্থীরা প্রায়ই না বুঝে মুখস্থ করে ফেলে—তা হলো লিনিয়ার ট্রান্সফর্মেশন এবং ম্যাট্রিক্সের সম্পর্ক।"
    ),
    ("L03", 4): (
        None,
        "শুরুতেই এই শব্দটি ভেঙে নেওয়া যাক: 'লিনিয়ার রূপান্তর' বা লিনিয়ার ট্রান্সফর্মেশন। রূপান্তর মূলত একটি ফাংশনেরই অন্য নাম।"
    ),
    ("L03", 26): (
        None,
        "একটি রূপান্তর প্রয়োগ করলে এবং এই তিনটি ভেক্টর কোথায় যায় তা অনুসরণ করলে, গ্রিড লাইন সমান্তরাল ও সমদূরত্বে থাকার ধর্মটি অত্যন্ত গুরুত্বপূর্ণ পরিণতি বহন করে। যেমন শিয়ার রূপান্তর।"
    ),
    ("L03", 30): (
        None,
        "এখানে দেখানো রূপান্তরটিতে আমরা পড়তে পারি যে, আই হ্যাট গিয়ে পৌঁছায় (১, -২) স্থানাঙ্কে, এবং জে হ্যাট গিয়ে পৌঁছায় এক্স অক্ষের উপর (৩, ০) স্থানাঙ্কে।"
    ),
    ("L03", 40): (
        None,
        "আপনাকে যদি একটি দুই-বাই-দুই ম্যাট্রিক্স দেওয়া হয় যা একটি লিনিয়ার ট্রান্সফর্মেশন বর্ণনা করে এবং কোনো একটি নির্দিষ্ট ভেক্টর, তাহলে ভেক্টরের স্থানাঙ্কগুলোকে সংশ্লিষ্ট কলামের সাথে গুণ করে যোগ করলেই রূপান্তর পরবর্তী অবস্থান পাওয়া যায়।"
    ),
    ("L03", 50): (
        None,
        "আসুন কয়েকটি লিনিয়ার ট্রান্সফর্মেশনকে ম্যাট্রিক্স দিয়ে বর্ণনা করি। উদাহরণস্বরূপ শিয়ার রূপান্তর।"
    ),
    ("L03", 57): (
        None,
        "একটু থামুন এবং কল্পনা করার চেষ্টা করুন। মনে করুন দুটি ভেক্টর যখন একে অপরের স্কেলড সংস্করণ, তখন তারা রৈখিকভাবে নির্ভরশীল বা লিনিয়ারলি ডিপেন্ডেন্ট।"
    ),
    ("L03", 62): (
        None,
        "সারসংক্ষেপে বলতে গেলে, লিনিয়ার ট্রান্সফর্মেশনের সাথে ডিটারমিন্যান্ট এবং র‍্যাংকের ধারণাগুলো গভীরভাবে সম্পর্কিত।"
    ),
    ("L03", 63): (
        None,
        "আনন্দের বিষয় হলো, ট্রান্সফর্মেশন T-এর ফলে কী ঘটে তা বর্ণনা করা সম্ভব মাত্র কয়েকটি সংখ্যা দিয়ে।"
    ),
    ("L03", 64): (
        None,
        "উদাহরণস্বরূপ, T(v + w) = T(v) + T(w) — এই সম্পর্কটি দেখায় লিনিয়ার ট্রান্সফর্মেশনে যোগ সংরক্ষিত থাকে।"
    ),
    ("L03", 65): (
        None,
        "একইভাবে, T(গুণক × v) = গুণক × T(v) — এই সম্পর্কটি দেখায় স্কেলিং সংরক্ষিত থাকে।"
    ),
    # Lesson 04 overrides
    ("L04", 14): (
        None,
        "উদাহরণস্বরূপ, আপনি যদি সমতলটিকে ৯০ ডিগ্রি ঘড়ির কাঁটার বিপরীতে ঘুরিয়ে তারপর শিয়ার রূপান্তর প্রয়োগ করতে চান।"
    ),
    ("L04", 16): (
        None,
        "এই নতুন লিনিয়ার ট্রান্সফর্মেশনটিকে সাধারণত দুটি পৃথক ট্রান্সফর্মেশনের কম্পোজিশন বলা হয়।"
    ),
    ("L04", 25): (
        None,
        "এখানে যেভাবে লেখা হয়েছে তার ভিত্তিতে এই নতুন ম্যাট্রিক্সটিকে মূল দুটি ম্যাট্রিক্সের গুণফল বা প্রোডাক্ট বলা যুক্তিসঙ্গত।"
    ),
    ("L04", 53): (
        None,
        "এখন একটি গুরুত্বপূর্ণ প্রশ্ন জিজ্ঞেস করা যাক: গুণের ক্রম বা অর্ডার কি কোনো পার্থক্য তৈরি করে?"
    ),
    # Lesson 02 overrides
    ("L02", 9): (
        None,
        "তাহলে ভেক্টরের এই সেটের ক্ষেত্রে আপনি কি বলতে পারবেন বেসিস কী? একটি বেসিস হলো রৈখিকভাবে স্বাধীন এবং স্প্যান দ্বারা সম্পূর্ণ স্থান নির্মাণকারী ভেক্টর সেট।"
    ),
    ("L02", 19): (
        None,
        "উদাহরণস্বরূপ, দুটি ভেক্টর একটি রৈখিক সমন্বয় বা লিনিয়ার কম্বিনেশন তৈরি করে যদি আমরা তাদের স্কেল করে যোগ করতে পারি।"
    ),
    ("L02", 26): (
        None,
        "তাহলে দুটি ভেক্টরের স্প্যান মানে কী? স্প্যান হলো তাদের সকল সম্ভাব্য রৈখিক সমন্বয়ের সেট।"
    ),
    ("L02", 56): (
        None,
        "তাহলে কখন দুটি ভেক্টর রৈখিকভাবে নির্ভরশীল বা লিনিয়ারলি ডিপেন্ডেন্ট? মনে রাখুন, একটি যদি অপরটির স্কেলড সংস্করণ হয় তবে তারা নির্ভরশীল।"
    ),
    ("L02", 58): (
        None,
        "বিপরীতভাবে, যদি প্রতিটি ভেক্টর নতুন মাত্রা যোগ করে তাহলে তারা রৈখিকভাবে স্বাধীন বা লিনিয়ারলি ইন্ডিপেন্ডেন্ট।"
    ),
}

def apply_global_replacements(text: str) -> str:
    for old, new in GLOBAL_REPLACEMENTS:
        text = text.replace(old, new)
    return text

def fix_script(label: str, path: Path) -> tuple[list, list]:
    """Returns (fixed_data, change_log)."""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    change_log = []
    for cue in data:
        cue_id = cue.get("id")
        original_bn = cue.get("bn", "")

        # Apply per-cue override if defined
        override_key = (label, cue_id)
        if override_key in PER_CUE_OVERRIDES:
            new_en, new_bn = PER_CUE_OVERRIDES[override_key]
            if new_en is not None:
                cue["en"] = new_en
            if new_bn is not None and new_bn != original_bn:
                change_log.append({
                    "cue": cue_id,
                    "type": "OVERRIDE",
                    "old": original_bn,
                    "new": new_bn,
                })
                cue["bn"] = new_bn
        else:
            # Apply global replacements
            fixed_bn = apply_global_replacements(original_bn)
            if fixed_bn != original_bn:
                change_log.append({
                    "cue": cue_id,
                    "type": "GLOBAL",
                    "old": original_bn,
                    "new": fixed_bn,
                })
                cue["bn"] = fixed_bn

    return data, change_log

def main():
    all_changes = {}
    for label, path in SCRIPTS.items():
        print(f"\n{'='*60}")
        print(f"Processing {label}: {path.name}")
        print('='*60)
        fixed_data, changes = fix_script(label, path)
        all_changes[label] = changes

        if changes:
            print(f"  ✅ {len(changes)} cue(s) fixed:")
            for c in changes:
                print(f"     Cue {c['cue']} [{c['type']}]:")
                print(f"       OLD: {c['old'][:100]}")
                print(f"       NEW: {c['new'][:100]}")
        else:
            print("  ✔  No changes needed (already clean).")

        # Write fixed JSON back
        with path.open("w", encoding="utf-8") as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)
        print(f"  💾 Saved: {path}")

    # Write change report
    report_path = Path(r"D:\0PEN CODE\Dub Studio") / "phonetics_fix_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(all_changes, f, ensure_ascii=False, indent=2)
    print(f"\n📋 Full report saved → {report_path}")
    print("\n🎯 All phonetic fixes complete!")

if __name__ == "__main__":
    main()
