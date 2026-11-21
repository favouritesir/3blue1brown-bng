# Source metadata note — Lockdown Math Lesson 07 dub

- **Verified source:** 3Blue1Brown (official YouTube channel)
- **oEmbed title:** But why is a sphere's surface area four times its shadow?
- **oEmbed author_name:** 3Blue1Brown
- **oEmbed author_url:** https://www.youtube.com/@3blue1brown
- **YouTube id:** GNcFjFmqEc8 (corrected from the 404 id `b3NxrZOup_U`)
- **Downloaded info.json:** {
  "youtube_id": "GNcFjFmqEc8",
  "title": "But why is a sphere's surface area four times its shadow?",
  "uploader": "3Blue1Brown",
  "channel": "3Blue1Brown",
  "duration_sec": 950,
  "webpage_url": "https://www.youtube.com/watch?v=GNcFjFmqEc8"
}
- **Downloaded file:** D:\0PEN CODE\Dub Studio\departments\learning_paths\stem_mathematics\3blue1brown_courses\web_platform\media_vault\lockdown_math\lesson_07\original_source\full_original.mp4 (h264 1920x1080 60fps, video-only;
  the original English narration is discarded — no English vocal bleed).

## Duration discrepancy note
`web_platform/data/lockdown_math/lesson_07.json` advertises a duration of
`1:08:42`, but the corrected source id `GNcFjFmqEc8` resolves to the official
3B1B clip "But why is a sphere's surface area four times its shadow?" whose real duration is ~950 s (15:50), confirmed by
both the oEmbed response and ffprobe. The dub canvas is therefore built to the
**actual** downloaded source duration (measured with ffprobe), exactly as the
proven clean_timesync_v2 pipeline does; it is never stretched to the inaccurate
metadata value.
