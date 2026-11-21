import os
import re
import json

base_dir = r"departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/courses/linear_algebra"

# Common Header & Nav & Mode Switcher component
def inject_dual_mode_and_playlist(file_path, chapter_num, title_bn, title_en, yt_id, quotes_text, quotes_author):
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    # If already has dual-mode-toggle, skip
    if "mode-toggle-pill" in html:
        return

    # Modern 3B1B Header & Navigation with Watch/Read Dual-Mode Bar & Playlist Drawer
    drawer_html = f"""
  <!-- ══════════════ 3B1B DUAL MODE & PLAYLIST BAR ══════════════ -->
  <div class="view-mode-bar" style="background:var(--surface); border-bottom:1px solid rgba(255,255,255,0.08); padding:10px 24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; position:sticky; top:65px; z-index:90;">
    <div style="display:flex; align-items:center; gap:8px;">
      <span style="font-size:0.85rem; color:var(--muted); font-weight:600;">ভিউ মোড:</span>
      <div class="mode-toggle-pill" style="display:inline-flex; background:rgba(0,0,0,0.3); border-radius:30px; padding:3px; border:1px solid rgba(255,255,255,0.1);">
        <button id="btnWatchMode" onclick="setLessonMode('watch')" style="background:var(--accent); color:#fff; border:none; padding:6px 18px; border-radius:20px; font-size:0.85rem; font-weight:bold; cursor:pointer; display:flex; align-items:center; gap:6px; transition:all 0.2s;">
          📺 ভিডিও থিয়েটার (Watch)
        </button>
        <button id="btnReadMode" onclick="setLessonMode('read')" style="background:transparent; color:var(--text); border:none; padding:6px 18px; border-radius:20px; font-size:0.85rem; font-weight:bold; cursor:pointer; display:flex; align-items:center; gap:6px; transition:all 0.2s;">
          📖 রিড মোড / টেক্সটবুক (Read)
        </button>
      </div>
    </div>
    
    <div style="display:flex; align-items:center; gap:12px;">
      <button onclick="togglePlaylistDrawer()" style="background:var(--card); color:var(--blue); border:1px solid var(--blue); padding:6px 14px; border-radius:6px; cursor:pointer; font-size:0.85rem; font-weight:bold; display:flex; align-items:center; gap:6px;">
        📑 অধ্যায় প্লে-লিস্ট (৫টি পাঠ)
      </button>
    </div>
  </div>

  <!-- ══════════════ PLAYLIST DRAWER (MODAL/OFFCANVAS) ══════════════ -->
  <div id="playlistDrawer" style="display:none; position:fixed; top:115px; right:20px; width:340px; background:var(--surface); border:1px solid var(--accent); border-radius:12px; box-shadow:0 12px 36px rgba(0,0,0,0.6); z-index:999; padding:16px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">
      <span style="font-weight:bold; color:var(--yellow); font-size:0.95rem;">🎬 এসেন্স অব লিনিয়ার অ্যালজেব্রা</span>
      <button onclick="togglePlaylistDrawer()" style="background:transparent; border:none; color:var(--muted); font-size:1.2rem; cursor:pointer;">&times;</button>
    </div>
    <div style="display:flex; flex-direction:column; gap:8px; max-height:420px; overflow-y:auto;">
      <a href="lesson_01.html" style="display:flex; align-items:center; gap:10px; padding:8px; border-radius:6px; text-decoration:none; color:var(--text); background:{'rgba(233,69,96,0.15)' if chapter_num=='01' else 'rgba(0,0,0,0.2)'}; border-left:3px solid {'var(--accent)' if chapter_num=='01' else 'transparent'};">
        <span style="font-size:0.8rem; font-weight:bold; color:var(--blue);">০১</span>
        <span style="font-size:0.85rem;">ভেক্টর আসলে কী?</span>
      </a>
      <a href="lesson_02.html" style="display:flex; align-items:center; gap:10px; padding:8px; border-radius:6px; text-decoration:none; color:var(--text); background:{'rgba(233,69,96,0.15)' if chapter_num=='02' else 'rgba(0,0,0,0.2)'}; border-left:3px solid {'var(--accent)' if chapter_num=='02' else 'transparent'};">
        <span style="font-size:0.8rem; font-weight:bold; color:var(--blue);">০২</span>
        <span style="font-size:0.85rem;">রৈখিক সমন্বয়, স্প্যান ও ভিত্তি ভেক্টর</span>
      </a>
      <a href="lesson_03.html" style="display:flex; align-items:center; gap:10px; padding:8px; border-radius:6px; text-decoration:none; color:var(--text); background:{'rgba(233,69,96,0.15)' if chapter_num=='03' else 'rgba(0,0,0,0.2)'}; border-left:3px solid {'var(--accent)' if chapter_num=='03' else 'transparent'};">
        <span style="font-size:0.8rem; font-weight:bold; color:var(--blue);">০৩</span>
        <span style="font-size:0.85rem;">রৈখিক রূপান্তর এবং ম্যাট্রিক্স</span>
      </a>
      <a href="lesson_04.html" style="display:flex; align-items:center; gap:10px; padding:8px; border-radius:6px; text-decoration:none; color:var(--text); background:{'rgba(233,69,96,0.15)' if chapter_num=='04' else 'rgba(0,0,0,0.2)'}; border-left:3px solid {'var(--accent)' if chapter_num=='04' else 'transparent'};">
        <span style="font-size:0.8rem; font-weight:bold; color:var(--blue);">০৪</span>
        <span style="font-size:0.85rem;">ম্যাট্রিক্স গুণন — রূপান্তরের রচনা</span>
      </a>
      <a href="lesson_05.html" style="display:flex; align-items:center; gap:10px; padding:8px; border-radius:6px; text-decoration:none; color:var(--text); background:{'rgba(233,69,96,0.15)' if chapter_num=='05' else 'rgba(0,0,0,0.2)'}; border-left:3px solid {'var(--accent)' if chapter_num=='05' else 'transparent'};">
        <span style="font-size:0.8rem; font-weight:bold; color:var(--blue);">০৫</span>
        <span style="font-size:0.85rem;">ত্রিমাত্রিক স্থানে রৈখিক রূপান্তর</span>
      </a>
    </div>
  </div>

  <script>
    function togglePlaylistDrawer() {{
      const d = document.getElementById('playlistDrawer');
      d.style.display = (d.style.display === 'none' || !d.style.display) ? 'block' : 'none';
    }}

    function setLessonMode(mode) {{
      const bW = document.getElementById('btnWatchMode');
      const bR = document.getElementById('btnReadMode');
      const wSec = document.querySelector('.player-card');
      const rSec = document.querySelector('article') || document.querySelector('.content-col');

      if (mode === 'watch') {{
        bW.style.background = 'var(--accent)';
        bW.style.color = '#fff';
        bR.style.background = 'transparent';
        bR.style.color = 'var(--text)';
        if (wSec) {{
          wSec.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
          wSec.style.border = '2px solid var(--accent)';
          setTimeout(() => {{ wSec.style.border = '1px solid rgba(255,255,255,0.08)'; }}, 1200);
        }}
      }} else {{
        bR.style.background = 'var(--accent)';
        bR.style.color = '#fff';
        bW.style.background = 'transparent';
        bW.style.color = 'var(--text)';
        if (rSec) {{
          rSec.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
      }}
    }}
  </script>
"""

    # Inject right after </header> or <section class="hero">
    if '</header>' in html:
        html = html.replace('</header>', '</header>\n' + drawer_html)
    elif '<header' in html:
        # append after header
        html = re.sub(r'(</header>)', r'\1\n' + drawer_html, html)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Injected modern dual mode & playlist into {file_path}")

lessons_meta = [
    ("lesson_01.html", "01", "ভেক্টর আসলে কী?", "Vectors, what even are they?", "fNk_zzaMoSs", "The introduction of numbers as coordinates is an act of violence.", "Hermann Weyl"),
    ("lesson_02.html", "02", "রৈখিক সমন্বয়, স্প্যান ও ভিত্তি ভেক্টর", "Linear combinations, span, and basis vectors", "k7RM-ot2NWY", "Mathematics requires a small dose, not of genius, but of an imaginative freedom...", "Angus K. Rodgers"),
    ("lesson_03.html", "03", "রৈখিক রূপান্তর এবং ম্যাট্রিক্স", "Linear transformations and matrices", "kYB8IZa5AuE", "Unfortunately, no one can be told what the Matrix is. You have to see it for yourself.", "Morpheus"),
    ("lesson_04.html", "04", "ম্যাট্রিক্স গুণন আসলে রূপান্তরের রচনা", "Matrix multiplication as composition", "XkY2DOUCWMU", "It is my experience that proofs involving matrices can be shortened by 50% if one throws the matrices out.", "Emil Artin"),
    ("lesson_05.html", "05", "ত্রিমাত্রিক স্থানে রৈখিক রূপান্তর", "Three-dimensional linear transformations", "rHLEWRxRGiM", "Homer Simpson has stumbled into... the third dimension.", "Frink"),
]

for fname, num, tbn, ten, ytid, qtxt, qauth in lessons_meta:
    p = os.path.join(base_dir, fname)
    if os.path.exists(p):
        inject_dual_mode_and_playlist(p, num, tbn, ten, ytid, qtxt, qauth)
