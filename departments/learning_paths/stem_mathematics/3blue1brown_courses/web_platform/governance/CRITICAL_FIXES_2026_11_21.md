# Critical fixes — 2026-11-21 (user-reported)

## 1. Lesson 01 video: 9:19 + music → 9:51, no music
- We had swapped L01 page to `3b1b_lesson_01_bangla_dubbed_video_v2.mp4` (559.9s = 9:19, with music/lead-in audio at −26 dBFS) as a "cheap win". WRONG.
- Restored the gold file `media_vault/lesson_01/experiments/3b1b_lesson_01_full_591s_dubbed.mp4` (591.1s = 9:51, silent lead-in −99 dB, no music) ✅.
- Audited ALL 48 active videos: every lead-in is −99 dB → **no background music anywhere** ✅ (`audit_all_videos_quality.py`).

## 2. Bookmark timestamps not working
- Component was correct (numeric `time` attrs, `jumpToLessonTime()` fine). Root cause: **`python -m http.server` has no Range support** → `video.seekable=[0,0]` → seeking to 160s clamps to 0.
- Fix: `serve_range.py` (Range-capable server, 206 Partial Content) is now the server on port 8085. Bookmark click → currentTime=160 ✅.
- **IMPORTANT: run `python serve_range.py 8085`, NOT `python -m http.server 8085`.**

## 3. Playlist navigation: wrong content / no active mark / video not loading
- `B1bRouter` in `lesson_components.js` intercepted ALL local `.html` links and did partial DOM swaps. On component pages `.article` selector didn't match `<b1b-article>` → stale article/video/playlist with new URL.
- Fix: disabled B1bRouter click interception (full page loads) ✅.
- Playlist was hardcoded to 5 items with `active` always on lesson 1. Fix: dynamic generation from `B1B_COURSES` totals + injected `B1B_LESSON_TITLES` (all 53 from curriculum_index.json), active marked from URL ✅. Verified across all 6 courses.

## 4. Homepage / course index pages were stale
- All 6 index pages listed only 1–5 lessons; homepage said "LA 01-05 dubbed, others coming"; curriculum_index.json had 5 LA lessons.
- Fixed via `regenerate_indexes.py` + `fix_homepage_stale2.py`: all 53 lessons listed (15/12/4/6/6/10), curriculum refreshed, stale texts removed, lockdown card polished ✅.

All audits green after fixes: verify_completed_artifacts 53/0, regression 53 pages/0 issues, expressive audio 53 manifests/0 issues, video quality 0 music.
