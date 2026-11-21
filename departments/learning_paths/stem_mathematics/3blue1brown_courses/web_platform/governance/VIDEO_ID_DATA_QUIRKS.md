# Video-ID data quirks — verify before launching video agents

Fixed so far (2026-11-20):
- probability L02: HZGCoVF3YvM (wrong, = Bayes theorem) → lG4VkPoG3ko (medical test paradox)
- calculus L11: 9vKqVkMQHKk (wrong dup, = paradox of derivative) → CfW845LNObM (Ch12 "other way to visualize derivatives")
- differential_equations L2: p_di4Zn4wDg → ly4S0oi3Yz8 (DE2 partial DE)
- differential_equations L5: ToIXSwZ1pJU → r6sGWTCMz2k (DE4 Fourier series)

## KNOWN UNRESOLVED (handle before launching those video agents)
- **calculus L12** "What is a differential?" — data id `1tGQvW48p64` returns 404 (oEmbed). 3B1B Essence of Calculus ends at Ch12; no official Ch13 video on YouTube. → Content page is authoritative (data JSON); NO official dubbed video possible. Either skip video phase for L12 or reuse a closely-related official clip with disclosure.
- **differential_equations L1 & L3** both `p_di4Zn4wz4` (DE1 tourist's guide); L4 & L6 both `ToIXSwZ1pJU` (DE3 heat eq). We only have FOUR official 3B1B DE videos:
  - DE1 `p_di4Zn4wz4` — tourist's guide
  - DE2 `ly4S0oi3Yz8` — partial differential equation
  - DE3 `ToIXSwZ1pJU` — solving the heat equation
  - DE4 `r6sGWTCMz2k` — Fourier series
  The data has 6 lessons (extra: Oscillations/Damping, Wave Equation) with no official 3B1B video. For L3/L6 either find best-fit official clip or disclose no-official-video and build content page only.
- **probability L05** `i3AkTO9HLXo` = "Markov Chains Clearly Explained" by Normalized Nerd (NOT 3B1B). No 3B1B Markov-chain video exists. Content page from data JSON is authoritative; video phase should either skip or disclose third-party source (parity with "official 3B1B content" cannot hold).

## Verification method
`python governance/audit_video_ids.py` shows duplicates; confirm each via
`webfetch https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=<ID>&format=json`.


## Lockdown L03 — FIXED 2026-11-20
- data id `bT1p5tJwn_0` was NOT 3B1B (jbstatistics "Intro to Bernoulli Distribution", 301s). Agent built a 301s dub before flagging.
- FIXED to `8idr1WZ1A7Q` (official 3B1B "Binomial distributions | Probabilities of probabilities, part 1") — closest official source for the lesson topic. Old jbstatistics video renamed to `..._jbstatistics_replaced.mp4`; new official dub to be built at the same video-src path.


## Lockdown Math ID sweep — 2026-11-20 (verify_lockdown_authors.py + yt-dlp)
- L04 `5PcpBw5HbWo` (404, case typo) -> `5PcpBw5Hbwo` (3B1B "Complex number fundamentals | Ep.3") FIXED
- L06 `d_bZk5f2Z8Y` (404) -> `ZA4JkHKZM50` (3B1B continuous-probability clip) FIXED
- L07 `b3NxrZOup_U` (404) -> `GNcFjFmqEc8` (3B1B area/geometry related clip) FIXED
- L09 `fNk_zzaMoSs` (topic mismatch) -> `LyGKycYT2v0` (3B1B "Dot products and duality | Ch9") FIXED
- L10 `LqbZpur38nw` ("Beyond Mandelbrot", topic mismatch) -> NO dedicated 3B1B higher-degree-polynomial video; treat as content+audio ONLY + disclose (like probability L05, diffeq L06). SKIP video agent.
- L03 `bT1p5tJwn_0` (jbstatistics) -> `8idr1WZ1A7Q` (3B1B binomial) — fixed earlier; video rebuilt from official source.
- L08 `d-o3eB9sfls` verified 3B1B "Why is pi here? Basel problem" ✅
- L05 `mvmuCPvRoWQ` verified 3B1B "Euler's formula ... group theory" ✅
- Prob L05 `i3AkTO9HLXo` is Normalized Nerd (NOT 3B1B) -> content+audio only (already done).
IMPORTANT: oEmbed-verify each id right before launching its video agent (IDs can be stale/mistyped).
