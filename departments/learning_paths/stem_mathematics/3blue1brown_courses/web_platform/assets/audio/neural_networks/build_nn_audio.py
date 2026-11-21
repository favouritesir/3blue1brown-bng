import os
import re
import json
import asyncio
import subprocess
import edge_tts

VOICE = "bn-BD-PradeepNeural"
NN_AUDIO_DIR = os.path.dirname(os.path.abspath(__file__))

def get_duration_ms(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(res.stdout.strip()) * 1000.0

def sanitize(text: str) -> str:
    t = text.replace("—", ", ").replace("–", ", ").replace("-", " ")
    t = t.replace("1D", "ওয়ান ডি").replace("2D", "টুডি").replace("3D", "থ্রিডি")
    t = t.replace("AI", "এআই").replace("SGD", "এসজিডি").replace("MSE", "এমএসই")
    t = re.sub(r'[\$#\*`\[\]]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

async def build_lesson_audio(lesson_num: str, data_path: str):
    target_dir = os.path.join(NN_AUDIO_DIR, f"lesson_{lesson_num}")
    temp_dir = os.path.join(target_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sections = data.get("sections", [])
    manifest_sections = {}
    gap_ms = 350.0
    
    print(f"\nBuilding Neural Networks Lesson {lesson_num} ({len(sections)} sections)...")
    
    for s_idx, sec in enumerate(sections):
        sec_id = sec.get("id", f"sec_{s_idx+1:02d}")
        title = sec.get("title_bn", f"Section {s_idx+1}")
        audio_name = f"{sec_id}.mp3"
        final_mp3 = os.path.join(target_dir, audio_name)
        
        # Build text cues from elements
        cues_raw = []
        elements = sec.get("elements", [])
        if elements:
            for el in elements:
                el_type = el.get("type", "p")
                el_text = el.get("content", el.get("text", ""))
                if el_type == "figure":
                    cap = el.get("caption", "চিত্র প্রদর্শনী")
                    el_text = f"চিত্র প্রদর্শনী: {cap}"
                elif el_type == "callout":
                    ttl = el.get("title", "বিশেষ দ্রষ্টব্য")
                    el_text = f"{ttl}: {el_text}"
                if el_text:
                    cues_raw.append({"type": el_type, "text": el_text})
        else:
            cues_raw.append({"type": "h2", "text": title})
            if sec.get("summary_bn"):
                cues_raw.append({"type": "p", "text": sec["summary_bn"]})
            for takeaway in sec.get("key_takeaways", []):
                cues_raw.append({"type": "p", "text": takeaway})
            
        cues_manifest = []
        chunk_paths = []
        cur_ms = 0.0
        
        for c_idx, c in enumerate(cues_raw):
            clean_text = sanitize(c["text"])
            if not clean_text:
                continue
            chunk_file = os.path.join(temp_dir, f"{sec_id}_cue_{c_idx:02d}.mp3")
            if not os.path.exists(chunk_file) or os.path.getsize(chunk_file) == 0:
                for attempt in range(3):
                    try:
                        comm = edge_tts.Communicate(clean_text, VOICE)
                        await comm.save(chunk_file)
                        break
                    except Exception as e:
                        await asyncio.sleep(0.5)
            dur = get_duration_ms(chunk_file)
            cues_manifest.append({
                "index": c_idx,
                "type": c["type"],
                "text": clean_text,
                "start_ms": round(cur_ms, 1),
                "end_ms": round(cur_ms + dur, 1),
                "duration_ms": round(dur, 1)
            })
            chunk_paths.append(chunk_file)
            cur_ms += dur + gap_ms
            
        concat_list = os.path.join(temp_dir, f"{sec_id}_list.txt")
        with open(concat_list, "w", encoding="utf-8") as f:
            for p in chunk_paths:
                f.write(f"file '{p.replace(os.sep, '/')}'\n")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list, "-c", "copy", final_mp3
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # Save cues json
        with open(os.path.join(target_dir, f"{sec_id}_cues.json"), "w", encoding="utf-8") as f:
            json.dump(cues_manifest, f, ensure_ascii=False, indent=2)
            
        manifest_sections[sec_id] = {
            "title": title,
            "audio_file": audio_name,
            "total_duration_ms": round(cur_ms, 1),
            "cues": cues_manifest
        }
        print(f"  ✓ {sec_id}: {len(cues_manifest)} cues, {round(cur_ms/1000, 1)}s")
        
        # cleanup
        for p in chunk_paths:
            try: os.remove(p)
            except: pass
        try: os.remove(concat_list)
        except: pass
        
    try: os.rmdir(temp_dir)
    except: pass
    
    manifest_data = {
        "course": "neural_networks",
        "lesson": f"lesson_{lesson_num}",
        "voice": VOICE,
        "mode": "authentic_teacher",
        "sections": manifest_sections
    }
    with open(os.path.join(target_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    with open(os.path.join(target_dir, "manifest.js"), "w", encoding="utf-8") as f:
        f.write("window.TEACHER_AUDIO_MANIFEST = " + json.dumps(manifest_data, ensure_ascii=False, indent=2) + ";\n")
    print(f"✅ Lesson {lesson_num} manifests & audios complete!")

async def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(NN_AUDIO_DIR)))
    await build_lesson_audio("02", os.path.join(root, "data", "neural_networks", "lesson_02.json"))
    await build_lesson_audio("03", os.path.join(root, "data", "neural_networks", "lesson_03.json"))

if __name__ == "__main__":
    asyncio.run(main())
