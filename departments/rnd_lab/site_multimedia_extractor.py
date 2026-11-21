"""
Bangla Resource Factory - Site Multimedia & Media Extractor
Department: R&D Lab & Automation Engineering
Author: Lead R&D Lab & Automation Engineer

Purpose:
Automates extraction of all images, diagrams, video embeds, and audio files from websites/blogs.
Outputs:
1. Downloads images to figures_and_data/ or visual_assets/
2. Extracts original video and audio URLs
3. Generates standardized Bengali markdown with Dual-Media Links (Original + Bangla Dubbed)
"""

import os
import re
import sys
import json
import urllib.parse
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup


class SiteMultimediaExtractor:
    def __init__(self, target_dir):
        self.target_dir = Path(target_dir)
        self.figures_dir = self.target_dir / "figures_and_data"
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.media_meta_file = self.target_dir / "multimedia_meta.json"

    def parse_html_content(self, html_content, base_url=""):
        soup = BeautifulSoup(html_content, "html.parser")
        results = {
            "images": [],
            "videos": [],
            "audios": []
        }

        # 1. Extract Images
        for idx, img in enumerate(soup.find_all("img")):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue
            full_src = urllib.parse.urljoin(base_url, src)
            alt = img.get("alt", "").strip() or f"চিত্র {idx + 1}"
            title = img.get("title", "").strip()
            results["images"].append({
                "index": idx + 1,
                "url": full_src,
                "alt": alt,
                "title": title
            })

        # Check SVG tags
        for idx, svg in enumerate(soup.find_all("svg")):
            results["images"].append({
                "index": len(results["images"]) + 1,
                "url": "inline_svg",
                "alt": f"ভেক্টর ডায়াগ্রাম {idx + 1}",
                "content": str(svg)
            })

        # 2. Extract Videos (iframes, video tags)
        for idx, iframe in enumerate(soup.find_all("iframe")):
            src = iframe.get("src") or ""
            if any(k in src for k in ["youtube.com", "youtu.be", "vimeo.com", "loom.com"]):
                results["videos"].append({
                    "type": "embed",
                    "url": src,
                    "title": iframe.get("title", f"ভিডিও লেকচার {idx + 1}")
                })

        for idx, vid in enumerate(soup.find_all("video")):
            src = vid.get("src")
            sources = [s.get("src") for s in vid.find_all("source") if s.get("src")]
            all_srcs = [src] if src else sources
            for s in all_srcs:
                if s:
                    results["videos"].append({
                        "type": "direct_video",
                        "url": urllib.parse.urljoin(base_url, s),
                        "title": f"ভিডিও {idx + 1}"
                    })

        # 3. Extract Audios
        for idx, aud in enumerate(soup.find_all("audio")):
            src = aud.get("src")
            sources = [s.get("src") for s in aud.find_all("source") if s.get("src")]
            all_srcs = [src] if src else sources
            for s in all_srcs:
                if s:
                    results["audios"].append({
                        "type": "audio",
                        "url": urllib.parse.urljoin(base_url, s),
                        "title": f"অডিও ট্র্যাক {idx + 1}"
                    })

        # Check links pointing to media files (.mp3, .wav, .mp4, youtube)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(href.lower().endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".aac"]):
                results["audios"].append({
                    "type": "audio_link",
                    "url": urllib.parse.urljoin(base_url, href),
                    "title": a.get_text().strip() or "অডিও লিংক"
                })
            elif any(k in href for k in ["youtube.com/watch", "youtu.be/"]):
                if not any(v["url"] == href for v in results["videos"]):
                    results["videos"].append({
                        "type": "youtube_link",
                        "url": href,
                        "title": a.get_text().strip() or "ইউটিউব ভিডিও লিংক"
                    })

        return results

    def download_images(self, image_list):
        downloaded = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        for img in image_list:
            url = img.get("url")
            idx = img.get("index", 1)
            if not url or url == "inline_svg":
                if "content" in img:
                    svg_file = self.figures_dir / f"diagram_{idx}.svg"
                    svg_file.write_text(img["content"], encoding="utf-8")
                    downloaded.append({
                        "local_rel_path": f"figures_and_data/{svg_file.name}",
                        "alt": img.get("alt", f"ডায়াগ্রাম {idx}")
                    })
                continue

            try:
                parsed = urllib.parse.urlparse(url)
                ext = Path(parsed.path).suffix.lower()
                if ext not in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]:
                    ext = ".png"
                local_filename = f"figure_{idx}{ext}"
                target_file = self.figures_dir / local_filename

                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    with open(target_file, "wb") as f:
                        f.write(resp.read())

                downloaded.append({
                    "local_rel_path": f"figures_and_data/{local_filename}",
                    "alt": img.get("alt", f"চিত্র {idx}")
                })
            except Exception as e:
                # If download fails, record original URL
                downloaded.append({
                    "local_rel_path": url,
                    "alt": img.get("alt", f"চিত্র {idx}")
                })

        return downloaded

    def generate_multimedia_markdown_section(self, media_data, downloaded_images, dubbed_audio_rel_path="", dubbed_video_rel_path=""):
        """
        Generates the standard Bengali Dual-Media & Figures Markdown Section
        """
        lines = []
        lines.append("## 🎬 মাল্টিমিডিয়া ও ডাবেড রিসোর্স হাব (Multimedia & Dubbed Hub)\n")
        lines.append("> ℹ️ **বাংলা রিসোর্স ফ্যাক্টরি পলিসি:** মূল ওয়েবসাইটের সকল অডিও-ভিডিওর সাথে বাংলা ডাবেড সংস্করণ সংযুক্ত করা হয়েছে।\n")

        # Video Section
        if media_data.get("videos"):
            lines.append("### 🎥 ভিডিও রিসোর্স ও বাংলা ডাবিং")
            for idx, vid in enumerate(media_data["videos"], 1):
                title = vid.get("title") or f"ভিডিও লেকচার {idx}"
                url = vid.get("url", "")
                lines.append(f"- **{title}**")
                lines.append(f"  - 🔗 **মূল ভিডিও লিংক (English Source):** [{url}]({url})")
                if dubbed_video_rel_path:
                    lines.append(f"  - 🎬 **বাংলা ডাবেড ভিডিও ভার্সন:** [{Path(dubbed_video_rel_path).name}]({dubbed_video_rel_path})")
                else:
                    lines.append(f"  - 🎙️ **বাংলা ডাবিং স্ট্যাটাস:** `[ডাবিং প্রক্রিয়াকরণ কিউতে পাঠানো হয়েছে | Priority Dubbing]`")
            lines.append("")

        # Audio Section
        if media_data.get("audios") or dubbed_audio_rel_path:
            lines.append("### 🎙️ অডিও আলোচনা ও পডকাস্ট")
            if media_data.get("audios"):
                for idx, aud in enumerate(media_data["audios"], 1):
                    title = aud.get("title") or f"অডিও ট্র্যাক {idx}"
                    url = aud.get("url", "")
                    lines.append(f"- **{title}**")
                    lines.append(f"  - 🔗 **মূল অডিও লিংক (English Source):** [{url}]({url})")

            if dubbed_audio_rel_path:
                lines.append(f"- **বাংলা টেকনিক্যাল অডিও ওভারভিউ (Bengali Dubbed Audio):**")
                lines.append(f"  - 🎧 **বাংলা অডিও শুনুন:** [{Path(dubbed_audio_rel_path).name}]({dubbed_audio_rel_path})")
                lines.append(f"  - *প্রোডাকশন নোট:* ১০০% পরিষ্কার নেটিভ বাংলা ভয়েস (পিউর সাউন্ড, নো ব্যাকগ্রাউন্ড মিউজিক)।")
            else:
                lines.append(f"- 🎙️ **বাংলা অডিও ডাবিং:** `[অডিও জেনারেশন কিউতে সংরক্ষিত]`")
            lines.append("")

        # Image Gallery snippet
        if downloaded_images:
            lines.append("### 🖼️ সংরক্ষিত ভিজ্যুয়াল আর্কিটেকচার ও ডায়াগ্রাম")
            for img in downloaded_images:
                rel = img.get("local_rel_path")
                alt = img.get("alt", "ডায়াগ্রাম")
                lines.append(f"![{alt}]({rel})")
                lines.append(f"*চিত্র: {alt} (বাংলা রিসোর্স ফ্যাক্টরি ভিজ্যুয়াল স্ট্যান্ডার্ড অনুযায়ী সংরক্ষিত)*\n")

        lines.append("---\n")
        return "\n".join(lines)


if __name__ == "__main__":
    print("Site Multimedia Extractor module initialized successfully.")
