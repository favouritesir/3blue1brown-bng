import urllib.request
import json
import os
import re

BASE_DIR = r"D:\Drive\gub221902131\My Drive\my\INS\PaperClip-opencode\Dub Studio"
REGISTRY_DIR = os.path.join(BASE_DIR, "data", "resource_registry")
os.makedirs(REGISTRY_DIR, exist_ok=True)

# 1. Fetch topics
topics_url = "https://raw.githubusercontent.com/3b1b/3Blue1Brown.com/main/app/data/topics.json"
req = urllib.request.Request(topics_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    topics_data = json.loads(resp.read().decode('utf-8'))

print(f"Scanned {len(topics_data)} topics.")

master_manifest = {
    "platform": "3Blue1Brown",
    "official_url": "https://www.3blue1brown.com",
    "source_repo": "https://github.com/3b1b/3Blue1Brown.com",
    "asset_bucket": "https://storage.googleapis.com/3blue1brown-website-bucket",
    "topics_count": len(topics_data),
    "topics": {}
}

total_lessons_indexed = 0
for t_id, t_info in topics_data.items():
    topic_entry = {
        "title": t_info.get("title"),
        "description": t_info.get("description"),
        "total_lessons": len(t_info.get("lessons", [])),
        "lessons": []
    }
    for l_slug in t_info.get("lessons", []):
        total_lessons_indexed += 1
        lesson_data = {
            "slug": l_slug,
            "status": "done" if (t_id == "linear-algebra" and l_slug == "vectors") else "pending",
            "media_assets": {
                "figures_svg": [],
                "figures_mp4": [],
                "has_video": True
            },
            "bangla_deliverables": {
                "interactive_html": True if (t_id == "linear-algebra" and l_slug == "vectors") else False,
                "notes_mathjax": True if (t_id == "linear-algebra" and l_slug == "vectors") else False,
                "halal_dubbing": True if (t_id == "linear-algebra" and l_slug == "vectors") else False,
                "clean_music_free_vocal": True if (t_id == "linear-algebra" and l_slug == "vectors") else False
            }
        }
        topic_entry["lessons"].append(lesson_data)
    master_manifest["topics"][t_id] = topic_entry

manifest_path = os.path.join(REGISTRY_DIR, "3b1b_master_production_tracker.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(master_manifest, f, indent=2, ensure_ascii=False)

print(f"Master Production Tracker created at: {manifest_path}")
print(f"Indexed {total_lessons_indexed} lesson instances across {len(topics_data)} topics.")
