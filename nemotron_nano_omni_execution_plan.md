**1️⃣  TASK RECAP & CONSTRAINTS**  

| Item | Requirement |
|------|--------------|
| **Source** | `original_audio.wav` – 44.1 kHz, 2‑channel (stereo) WAV, 3 min 33 s, cartoon “Steve & Maggie – Learn the Senses”. |
| **Target stems** | `sfx_bells_isolated.wav`  – *only* cartoon SFX (bells, chimes, boings, sniff, sizzle, cheers, transitions). **No hiss, buzz, robotic musical noise, flanging or any distortion**. |
| | `speech_isolated.wav` – *only* Steve & Maggie dialogue. **Zero‑hiss, clean, no background cartoon artefacts**. |
| **Dialogue timestamps** | 48 cues supplied in `master_bangla_screenplay_script.json`. Each cue = `[start_sec, end_sec]` (float). |
| **Zero‑hiss requirement** | Must eliminate any residual centre‑channel hiss that appears when naïve L‑R side‑channel extraction is used. |
| **No distortion** | No clipping, no flanging/robotic musical artefacts, no audible “musical noise” from aggressive spectral subtraction. |
| **Output directory** | `departments/media_production/youtube_channels/wow_english/kids_education/steve_and_maggie_school_stories_senses/isolated_stems/nemotron_3_nano_omni/` |

---

## 2️⃣  ARCHITECTURAL BLUEPRINT  

```
+---------------------------------------------------------------+
|                     HIGH‑LEVEL PIPELINE                        |
+-------------------+----------------+--------------------------+
| 1. Load & Pre‑process                                            |
|    - Read original WAV (44.1 kHz, 24‑bit PCM)                  |
|    - Convert to 32‑bit float for all DSP steps                |
+-------------------+----------------+--------------------------+
| 2. Speech‑segment extraction (using JSON timestamps)          |
|    - For each cue [s, e] → cut out a temporary wav file      |
|    - Apply a *high‑precision VAD* (pyannote‑vader) to tighten   |
|      the boundaries (±5 ms) → final speech mask               |
+-------------------+----------------+--------------------------+
| 3. Speech separation (neural)                                   |
|    - Run Demucs‑v4 (speech‑only model) on each speech segment   |
|    - Output: *speech‑only* signal (center‑channel dominant)    |
|    - Optional: fine‑tune Demucs on a small “cartoon‑dialogue”   |
|      dataset (10 s) to improve cartoon‑voice separation        |
+-------------------+----------------+--------------------------+
| 4. Noise‑profile estimation (speech‑only segments)            |
|    - Compute short‑time energy (STE) in 0.5 s windows        |
|    - Identify “quiet” windows (STE < 0.01 × max) → noise PSD   |
|    - Store noise profile (mean spectrum) for later use        |
+-------------------+----------------+--------------------------+
| 5. SFX‑only extraction (non‑speech remainder)                  |
|    - Subtract the *speech‑only* signal from the full mix →     |
|      residual = full – speech (this contains all SFX +      |
|      any residual hiss).                                     |
|    - Apply a *band‑pass cascade* tuned to cartoon SFX:        |
|        • 2 kHz–8 kHz  → bells, chimes, boings                |
|        • 300 Hz–2 kHz → sniff, cheering, low‑boing           |
|        • 4 kHz–12 kHz → sizzle, magical twinkle              |
|    - Use a *soft‑spectral gate* (noisereduce) with the noise   |
|      profile from step 4 → removes hiss while preserving      |
|      transients.                                              |
|    - Detect true SFX onsets with an onset‑detector (e.g.    |
|      librosa `onset_detect` with `backtrack=True`) → keep    |
|      only the segments that actually contain a sound event.   |
+-------------------+----------------+--------------------------+
| 6. Final clean‑up & export                                        |
|    - Apply a *very mild* high‑pass (30 Hz) to remove any      |
|      sub‑bass rumble that survived the band‑pass.             |
|    - Apply a *hard‑clip* protection (max 0.99 × FS) to avoid   |
|      digital clipping after gain adjustments.                |
|    - Convert back to 24‑bit PCM WAV (44.1 kHz, stereo)        |
|    - Write `sfx_bells_isolated.wav` and `speech_isolated.wav`|
+---------------------------------------------------------------+
```

**Why this pipeline satisfies the constraints**

* **Zero‑hiss** – Noise profile is estimated from *silent* portions of the speech‑only signal (which contain only residual hiss). The subsequent soft‑spectral gate removes that noise without the “musical‑noise” artefacts typical of hard threshold gating.  
* **No distortion** – All processing is done in 32‑bit float; gain is limited to ≤ ‑0.1 dBFS before the final 24‑bit conversion, guaranteeing no clipping.  
* **Exact dialogue timestamps** – The VAD + JSON cue alignment guarantees that every spoken phrase is isolated exactly as required.  
* **Pure cartoon SFX** – By subtracting the speech‑only signal we keep everything that is *not* speech, then we further band‑pass filter to the frequency ranges that define the cartoon sound‑effects family, discarding any low‑frequency rumble or high‑frequency static that could be interpreted as hiss.  

---

## 3️⃣  DETAILED DSP ALGORITHM  

Below each step is expressed as a concrete algorithm (pseudo‑code + math).  

### 3.1  Loading & Normalisation  

```python
import soundfile as sf
import numpy as np

# Load 24‑bit PCM, keep stereo
data, sr = sf.read('original_audio.wav', dtype='float32')   # shape (N, 2)
data = data / np.iinfo(np.int32).max   # normalise to [-1, 1]
```

### 3.2  Speech‑segment extraction (JSON timestamps)  

```python
import json, pathlib

with open('master_bangla_screenplay_script.json') as f:
    cues = json.load(f)                     # list of [start, end] in seconds

def cut_segment(wav, start, end):
    """Return a copy of wav[ int(start*sr) : int(end*sr) ]"""
    s = int(start * sr)
    e = int(end   * sr)
    return wav[s:e].copy()
```

For each cue we create a *temporary* file `speech_cue_i.wav`.  

### 3.3  Voice Activity Detection (VAD) – tighten boundaries  

We use **pyannote‑vader** (pre‑trained, 10 ms resolution).  

```python
from pyannote.audio import Pipeline

vad_pipe = Pipeline.from_pretrained('py