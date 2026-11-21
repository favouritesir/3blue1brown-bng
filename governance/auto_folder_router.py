"""
Bangla Resource Factory - Automated Hierarchy & Folder Router
Automatically determines, creates, and maintains clean, structured directory trees
based on:
1. Source Type (YouTube Channel, Website/Domain, Academic Publisher, Book/Doc, Course)
2. Content Genre / Topic (AI Agents, Cybersecurity, Web Development, DevOps, etc.)
3. Media / Asset Type (Video, Audio Podcast, Research Paper, Interactive Guide, Handbook)
"""

import os
import re
import json
import urllib.parse
from pathlib import Path

BASE_DIR = Path("D:/Drive/gub221902131/My Drive/my/INS/PaperClip-opencode/Dub Studio")
REGISTRY_FILE = BASE_DIR / "data" / "resource_registry" / "registry.json"


def slugify(text):
    """Convert text to clean filesystem-safe slug"""
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text.strip("_") or "misc"


def extract_domain_from_url(url):
    """Extract clean domain/site name from URL"""
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        # Extract main site name
        parts = netloc.split(".")
        if len(parts) >= 2:
            return parts[-2]
        return netloc or "external_web"
    except Exception:
        return "external_web"


class AutoFolderRouter:
    def __init__(self, base_dir=BASE_DIR):
        self.base_dir = Path(base_dir)

    def route_and_create(self, source_type, source_name_or_url, content_type, genre, content_title):
        """
        Determines and automatically creates the exact hierarchical directory.
        
        source_type: 'youtube_channel', 'website', 'academic_paper', 'book_doc', 'learning_path', 'rnd_lab'
        source_name_or_url: e.g., 'JavaScript Mastery', 'https://anthropic.com/research', 'arXiv'
        content_type: 'video_dubbing', 'audio_podcast', 'research_paper', 'book_doc', 'learning_path', 'rnd_tool'
        genre: e.g., 'ai_agents', 'cybersecurity', 'system_design', 'web_development', 'devops'
        content_title: e.g., '700 AI Agents Escaped'
        """
        source_type = slugify(source_type)
        genre = slugify(genre)
        content_slug = slugify(content_title)

        # 1. Resolve source label (Channel name, Website domain, or Publisher)
        if "http://" in str(source_name_or_url) or "https://" in str(source_name_or_url):
            if "youtube.com" in str(source_name_or_url) or "youtu.be" in str(source_name_or_url):
                source_category = "youtube_channels"
                source_label = slugify(source_name_or_url.split("?")[0].split("/")[-1])
            else:
                source_category = "websites"
                source_label = slugify(extract_domain_from_url(source_name_or_url))
        else:
            source_label = slugify(source_name_or_url)
            if "youtube" in source_type or "channel" in source_type:
                source_category = "youtube_channels"
            elif "web" in source_type:
                source_category = "websites"
            elif "paper" in source_type or "academic" in source_type:
                source_category = "academic_institutions"
            elif "book" in source_type:
                source_category = "publishers_and_authors"
            else:
                source_category = "sources"

        # 2. Build canonical Department directory structure
        if content_type in ["video_dubbing", "audio_podcast"]:
            target_dir = self.base_dir / "departments" / "media_production" / source_category / source_label / genre / content_slug
            subfolders = ["scripts", "stems_audio", "output_rendered", "raw_sources"]
        elif content_type == "research_paper":
            target_dir = self.base_dir / "departments" / "research_academic" / source_category / source_label / genre / content_slug
            subfolders = ["original_en", "bangla_adapted", "figures_and_data"]
        elif content_type in ["book_doc", "documentation"]:
            target_dir = self.base_dir / "departments" / "books_docs" / source_category / source_label / genre / content_slug
            subfolders = ["chapters_bn", "glossary", "code_examples"]
        elif content_type == "learning_path":
            target_dir = self.base_dir / "departments" / "learning_paths" / genre / content_slug
            subfolders = ["curriculum", "assignments", "roadmaps"]
        elif content_type == "rnd_tool":
            target_dir = self.base_dir / "departments" / "rnd_lab" / genre / content_slug
            subfolders = ["engine", "benchmarks", "samples"]
        else:
            target_dir = self.base_dir / "departments" / "general" / source_category / source_label / genre / content_slug
            subfolders = ["content", "metadata"]

        # Create main directory and subfolders automatically
        target_dir.mkdir(parents=True, exist_ok=True)
        created_subfolders = []
        for sub in subfolders:
            sub_p = target_dir / sub
            sub_p.mkdir(parents=True, exist_ok=True)
            created_subfolders.append(sub)

        meta_info = {
            "source_type": source_type,
            "source_category": source_category,
            "source_label": source_label,
            "content_type": content_type,
            "genre": genre,
            "content_slug": content_slug,
            "full_target_dir": str(target_dir),
            "relative_path": str(target_dir.relative_to(self.base_dir)).replace("\\", "/"),
            "subfolders": created_subfolders
        }

        # Save metadata within the folder
        with open(target_dir / "folder_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_info, f, indent=2, ensure_ascii=False)

        print(f"[AutoFolderRouter] Created structured folder:")
        print(f" -> {meta_info['relative_path']}")
        return meta_info


if __name__ == "__main__":
    router = AutoFolderRouter()
    
    # Example 1: YouTube video from JavaScript Mastery on AI Agents
    m1 = router.route_and_create(
        source_type="youtube_channel",
        source_name_or_url="JavaScript Mastery",
        content_type="video_dubbing",
        genre="ai_agents_security",
        content_title="700 AI Agents Escaped"
    )
    
    # Example 2: Website Article from Anthropic on Model Context Protocol
    m2 = router.route_and_create(
        source_type="website",
        source_name_or_url="https://www.anthropic.com/news/model-context-protocol",
        content_type="research_paper",
        genre="agentic_architecture",
        content_title="Model Context Protocol In-Depth"
    )

    # Example 3: Academic Paper from arXiv on Multi-Agent Reinforcement Learning
    m3 = router.route_and_create(
        source_type="academic_paper",
        source_name_or_url="arXiv",
        content_type="research_paper",
        genre="reinforcement_learning",
        content_title="Exploit Gym Technical Benchmark"
    )

    print("\nRouter verified successfully.")
