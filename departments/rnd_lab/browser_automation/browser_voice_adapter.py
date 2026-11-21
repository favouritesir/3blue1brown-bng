"""
Bangla Resource Factory - R&D Lab: Browser Automation & Multi-Character Voice Adapter
Automates browser-based voice synthesis, web scraping of educational resources,
and ultra-realistic dialogue generation for multi-character scripts.
"""
import os
import sys
import asyncio
from pathlib import Path
import edge_tts

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Character Voice Registry
VOICE_REGISTRY = {
    "narrator_male": {
        "voice": "bn-BD-PradeepNeural",
        "description": "গম্ভীর ও আকর্ষণীয় পুরুষ কণ্ঠ (প্রধান বর্ণনাকারী বা টেক-টিউটোরিয়াল হোস্ট)",
        "rate": "+0%",
        "pitch": "+0Hz"
    },
    "agent_female": {
        "voice": "bn-BD-NabanitaNeural",
        "description": "স্পষ্ট ও প্রমিত নারী কণ্ঠ (এজেন্ট, উদ্ধৃতি ও দ্বিতীয় চরিত্র)",
        "rate": "+0%",
        "pitch": "+0Hz"
    },
    "academic_speaker": {
        "voice": "bn-IN-BashkarNeural",
        "description": "বিশ্লেষণধর্মী প্রমিত বাংলা কণ্ঠ (গবেষণা ও একাডেমিক লেকচার)",
        "rate": "-3%",
        "pitch": "-2Hz"
    },
    "young_learner": {
        "voice": "bn-IN-TanishaaNeural",
        "description": "প্রাণবন্ত আধুনিক কণ্ঠ (লার্নিং গাইড ও শিক্ষানবিস চরিত্র)",
        "rate": "+4%",
        "pitch": "+2Hz"
    }
}


async def synthesize_speech(text, role="narrator_male", output_path=None):
    """Synthesize Bengali dialogue using character preset"""
    if role not in VOICE_REGISTRY:
        role = "narrator_male"
        
    cfg = VOICE_REGISTRY[role]
    if output_path is None:
        output_path = BASE_DIR / "departments" / "rnd_lab" / "browser_automation" / f"sample_{role}.mp3"
        
    output_p = Path(output_path)
    output_p.parent.mkdir(parents=True, exist_ok=True)
    
    communicator = edge_tts.Communicate(
        text=text,
        voice=cfg["voice"],
        rate=cfg["rate"],
        pitch=cfg["pitch"]
    )
    await communicator.save(str(output_p))
    print(f"[Voice Adapter] Rendered '{role}' -> {output_p} ({output_p.stat().st_size} bytes)")
    return str(output_p)


if __name__ == "__main__":
    sample_text = "বাংলা রিসোর্স ফ্যাক্টরিতে আপনাদের স্বাগতম। আমরা বাংলা ভাষায় মানসম্মত গবেষণা ও শিক্ষামূলক উপকরণ তৈরিতে প্রতিশ্রুতিবদ্ধ।"
    asyncio.run(synthesize_speech(sample_text, role="narrator_male"))
