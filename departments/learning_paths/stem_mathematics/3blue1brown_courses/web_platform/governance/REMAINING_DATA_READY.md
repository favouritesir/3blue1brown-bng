# Remaining lessons — data/manifest readiness (checked 2026-11-20)

All 11 remaining lessons (DiffEq L04–L06, Lockdown L03–L10) have:
- data JSON ✅
- audio manifest ✅ (forbidden label count 0)
- no component page yet (`page=False`) — content phase pending

## Quick-reference (id / sections count)
| Course | Lesson | youtube_id | #sections | Note |
|---|---|---|---|---|
| diffeq | 04 | ToIXSwZ1pJU | 5 | heat/boundary/Fourier; official DE3 |
| diffeq | 05 | r6sGWTCMz2k | 5 | heat eq + Fourier transform; official DE4 |
| diffeq | 06 | ToIXSwZ1pJU | 5 | wave equation; NO official 3B1B video → content+audio only, disclose (id duplicate) |
| lockdown | 03 | bT1p5tJwn_0 | 5 | binomial/coin flips |
| lockdown | 04 | 5PcpBw5HbWo | 8 | complex numbers geometric |
| lockdown | 05 | mvmuCPvRoWQ | 8 | Euler's formula & trig |
| lockdown | 06 | d_bZk5f2Z8Y | 8 | continuous probability |
| lockdown | 07 | b3NxrZOup_U | 4 | area & derivative of circle |
| lockdown | 08 | d-o3eB9sfls | 4 | Basel problem proof |
| lockdown | 09 | fNk_zzaMoSs | 4 | linear combinations & dual vectors |
| lockdown | 10 | LqbZpur38nw | 4 | higher-degree polynomials |

Before launching each VIDEO agent, oEmbed spot-check the id (webfetch `https://www.youtube.com/oembed?url=...`). For diffeq L06 the id is a known duplicate → SKIP video agent (content+audio only).

Launch pattern (per lesson): content agent → audio agent (backup first) + video agent (fill policy + quality gate) → ffprobe verify → video-src swap → tracker.
