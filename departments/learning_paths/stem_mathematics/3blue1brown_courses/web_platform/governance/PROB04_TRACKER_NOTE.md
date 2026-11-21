# Probability L04 tracker note (2026-11-20)

Prob L04 was briefly marked `completed` in `completed_lessons.json` after its audio
build, but the dubbed video had NOT been built. `verify_completed_artifacts.py`
caught `video-src MISSING`. Action taken:
- `probability_l04` REMOVED from `completed_lessons.json` (board regenerated: 34).
- Video agent launched → output `media_vault/probability/lesson_04/experiments/3b1b_prob_04_full_dubbed.mp4`.

WHEN the video agent reports ffprobe success:
1. Verify `verify_completed_artifacts.py` shows no MISSING for probability_l04.
2. Re-add `probability_l04` to `completed_lessons.json` (after probability_l03).
3. Regenerate `board_data.json` → expect 36+ completed.

LESSON LEARNED: never mark a lesson `completed` until page + video + audio ALL
exist. `verify_completed_artifacts.py` is the gate — run it before every board regen.
