#!/usr/bin/env python3
"""Obsidian Vault Integration helper for NotebookLM pipelines.

Extracts summaries, sanitizes titles, writes structured markdown notes with
YAML frontmatter directly to the Obsidian vault filesystem, and invokes the
Obsidian CLI for UI sync.
"""

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

def sanitize_filename(title: str) -> str:
    """Remove invalid filesystem characters from title."""
    s = re.sub(r'[\\/*?:"<>|]', "", title)
    s = " ".join(s.split())
    return s.strip()

def get_obsidian_vault_info():
    """Retrieve Obsidian vault name and path from environment or defaults."""
    vault_name = os.environ.get("OBSIDIAN_VAULT", "Home-ubuntu-files")
    vault_path_env = os.environ.get("OBSIDIAN_VAULT_PATH")
    if vault_path_env:
        vault_path = Path(vault_path_env)
    else:
        vault_path = Path("/home/vreddy1/Documents/Home-ubuntu-files")
    return vault_name, vault_path

def extract_summary_and_key_points(report_path: Path):
    """Extract summary and key points from NotebookLM report.md."""
    if not report_path or not report_path.exists():
        return "No report generated.", []
    
    try:
        content = report_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        return f"Error reading report: {e}", []
    
    summary = ""
    # Try finding Executive Summary or Summary sections
    m_exec = re.search(r"## Executive Summary\s*\n\n(.*?)(?=\n\n##|\n\n---|\Z)", content, re.DOTALL | re.IGNORECASE)
    if m_exec:
        summary = m_exec.group(1).strip()
    else:
        # Fallback: take first paragraph that is not a heading
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        non_headings = [p for p in paragraphs if not p.startswith("#")]
        if non_headings:
            summary = non_headings[0]
            if len(summary) > 400:
                summary = summary[:400] + "..."
        else:
            summary = "Summary not extractable from report."
            
    # Try to find bullet points for key points
    bullets = re.findall(r"^\s*[\*\-]\s+(.*)$", content, re.MULTILINE)
    key_points = []
    if bullets:
        for b in bullets:
            b_clean = b.strip()
            # Filter out lines that look like markdown tasks or internal paths
            if b_clean and not b_clean.startswith("[") and not b_clean.endswith("]"):
                key_points.append(b_clean)
        key_points = key_points[:6]
    
    if not key_points:
        key_points = ["Refer to full report for detailed insights."]
        
    return summary, key_points

def save_to_obsidian(
    source_type: str,          # 'youtube', 'telegram', 'arxiv', 'other'
    title: str,
    source_id: str,
    source_url: str,
    notebook_id: str,
    report_path: Path,
    mindmap_path: Path = None,
    infographic_path: Path = None,
    processed_date: str = None,
    additional_tags: list = None
):
    """Create a structured note in the Obsidian vault and attempt to sync via CLI."""
    if not processed_date:
        processed_date = datetime.now().strftime("%Y-%m-%d")
        
    # 1. Determine Vault directories
    vault_name, vault_path = get_obsidian_vault_info()
    
    source_folder_map = {
        'youtube': 'Youtube',
        'telegram': 'Telegram',
        'arxiv': 'Arxiv'
    }
    folder_name = source_folder_map.get(source_type.lower(), 'Other')
    
    obsidian_dir = vault_path / "NotebookLM Processing" / folder_name
    
    # Check write accessibility on vault directory
    if not vault_path.exists():
        print(f"  [OBSIDIAN WARN] Vault directory does not exist: {vault_path}")
        # Create a local fallback folder to avoid losing data
        local_fallback = Path(__file__).parent / "obsidian_vault_fallback" / "NotebookLM Processing" / folder_name
        local_fallback.mkdir(parents=True, exist_ok=True)
        obsidian_dir = local_fallback
        print(f"  [OBSIDIAN INFO] Using local fallback directory: {obsidian_dir}")
    else:
        obsidian_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Sanitize and construct filename
    safe_title = sanitize_filename(title)
    filename = f"{processed_date} - {safe_title}.md"
    note_file_path = obsidian_dir / filename
    
    # 3. Extract Summary & Key Points
    summary, key_points = extract_summary_and_key_points(report_path)
    
    # 4. Construct tags list
    tags = ["notebooklm", source_type.lower(), processed_date]
    if additional_tags:
        for t in additional_tags:
            t_clean = t.replace("@", "").lower().strip()
            # Clean special chars from tag name to prevent YAML issues
            t_clean = re.sub(r"[^a-z0-9_-]", "-", t_clean)
            t_clean = t_clean.strip("-")
            if t_clean and t_clean not in tags:
                tags.append(t_clean)
                
    # 5. Build Content
    # Safe quotes for YAML
    safe_title_yaml = title.replace('"', '\\"')
    safe_id_yaml = source_id.replace('"', '\\"')
    safe_url_yaml = source_url.replace('"', '\\"')
    
    yaml_lines = [
        "---",
        f'title: "{safe_title_yaml}"',
        f'source_type: "{source_type}"',
        f'source_id: "{safe_id_yaml}"',
        f'source_url: "{safe_url_yaml}"',
        f'processed_date: "{processed_date}"',
        f'notebooklm_notebook_id: "{notebook_id}"',
        "tags:"
    ]
    for tag in tags:
        yaml_lines.append(f"  - {tag}")
    yaml_lines.append("---")
    yaml_frontmatter = "\n".join(yaml_lines)
    
    key_points_str = "\n".join([f"- {kp}" for kp in key_points])
    
    artifacts_section = []
    if report_path and report_path.exists():
        artifacts_section.append(f"- [Report](file://{report_path.resolve()})")
    if mindmap_path and mindmap_path.exists():
        artifacts_section.append(f"- [Mind Map](file://{mindmap_path.resolve()})")
    if infographic_path and infographic_path.exists():
        artifacts_section.append(f"- [Infographic](file://{infographic_path.resolve()})")
    artifacts_str = "\n".join(artifacts_section) if artifacts_section else "- None"
    
    source_label_map = {
        'youtube': 'YouTube Video',
        'telegram': 'Telegram Source',
        'arxiv': 'arXiv Paper'
    }
    source_label = source_label_map.get(source_type.lower(), 'Source Link')
    
    body = f"""
# {title}

## Summary
{summary}

## Key Points
{key_points_str}

## Artifacts
{artifacts_str}

## Source
- [{source_label}]({source_url})

## NotebookLM
- [View in NotebookLM](https://notebooklm.google.com/notebook/{notebook_id})
"""
    
    full_content = f"{yaml_frontmatter}\n{body}"
    
    # 6. Save directly to filesystem (robust backup)
    try:
        note_file_path.write_text(full_content, encoding="utf-8")
        print(f"  [OBSIDIAN] Note saved directly to vault: {note_file_path.name}")
    except Exception as e:
        print(f"  [OBSIDIAN WARN] Failed to write file to vault path {note_file_path}: {e}")
        
    # 7. Attempt Obsidian CLI invocation (for UI sync and active note targeting)
    rel_path = f"NotebookLM Processing/{folder_name}/{filename}"
    cmd = [
        "obsidian",
        f"vault={vault_name}",
        "create",
        f"name={processed_date} - {safe_title}",
        f"content={full_content}",
        f"path={rel_path}",
        "overwrite",
        "silent"
    ]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if res.returncode == 0:
            print(f"  [OBSIDIAN] CLI created/synced note successfully.")
        else:
            # Not a critical failure, could just be that the GUI is not running
            pass
    except Exception:
        # Silently fail, CLI might not be accessible or timed out
        pass
        
    return note_file_path


def append_youtube_summary_to_wiki(
    video: dict,
    notebook_id: str,
    report_path: Path,
    mindmap_path: Path = None,
    processed_date: str = None
) -> Path:
    """Append a YouTube summary entry to the centralized wiki note."""
    if not processed_date:
        processed_date = datetime.now().strftime("%Y-%m-%d")

    vault_name, vault_path = get_obsidian_vault_info()
    wiki_dir = vault_path / "wiki" / "projects"
    
    # Ensure directory exists or use local fallback
    if not vault_path.exists():
        print(f"  [OBSIDIAN WARN] Vault directory does not exist: {vault_path}")
        wiki_dir = Path(__file__).parent / "obsidian_vault_fallback" / "wiki" / "projects"
    
    wiki_dir.mkdir(parents=True, exist_ok=True)
    
    # We prefer the existing case-sensitive file if it matches
    note_file_path = wiki_dir / "Youtube_notebooklm.md"
    if not note_file_path.exists():
        alternative = wiki_dir / "youtube_notebooklm.md"
        if alternative.exists():
            note_file_path = alternative
            
    # Initialize note if empty or non-existent
    if not note_file_path.exists() or note_file_path.stat().st_size == 0:
        init_content = f"""---
title: "YouTube to NotebookLM Logs"
tags:
  - "project"
  - "youtube"
  - "notebooklm"
date: "{processed_date}"
---

# YouTube to NotebookLM Logs

This note tracks the historical feed of YouTube videos processed by the NotebookLM pipeline.

---
"""
        note_file_path.write_text(init_content, encoding="utf-8")
        print(f"  [OBSIDIAN] Initialized centralized note: {note_file_path.name}")

    # Read briefing report content
    report_content = "No report content found."
    if report_path and report_path.exists():
        try:
            report_content = report_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            report_content = f"Error reading report: {e}"

    # Generate mindmap tree text if path exists
    mindmap_section = ""
    if mindmap_path and mindmap_path.exists():
        try:
            import json
            mm_data = json.loads(mindmap_path.read_text(encoding="utf-8"))
            
            # Simple local recursive helper to avoid dependency on caller
            def local_mm_to_text(data, indent=0) -> list[str]:
                prefix = "  " * indent
                lines = []
                if isinstance(data, dict):
                    title = data.get("title") or data.get("label") or data.get("name", "")
                    if title:
                        marker = "•" if indent == 0 else "─"
                        lines.append(f"{prefix}{marker} {title}")
                    children = data.get("children") or data.get("items") or data.get("nodes") or []
                    for child in children:
                        lines.extend(local_mm_to_text(child, indent + 1))
                elif isinstance(data, list):
                    for item in data:
                        lines.extend(local_mm_to_text(item, indent))
                elif isinstance(data, str):
                    lines.append(f"{prefix}  {data}")
                return lines

            tree_lines = local_mm_to_text(mm_data)
            if tree_lines:
                mindmap_section = "\n### Mind Map\n```\n" + "\n".join(tree_lines) + "\n```\n"
        except Exception as e:
            mindmap_section = f"\n### Mind Map\n*Error reading mind map: {e}*\n"

    title = video.get("title", "Untitled Video")
    channel = video.get("channel_handle", "Unknown Channel")
    url = video.get("url", "")
    nb_link = f"https://notebooklm.google.com/notebook/{notebook_id}"

    # Build entry string
    entry = f"""
## [[{processed_date}]] - {title}
- **Channel**: {channel}
- **Video Link**: [Watch on YouTube]({url})
- **NotebookLM**: [Open Notebook]({nb_link})

### Summary & Briefing Report
{report_content}
{mindmap_section}
---
"""

    # Append entry to the file
    try:
        with open(note_file_path, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"  [OBSIDIAN] Appended summary entry to: {note_file_path.name}")
    except Exception as e:
        print(f"  [OBSIDIAN ERROR] Failed to append to vault note {note_file_path}: {e}")

    # Sync with CLI if applicable
    try:
        # For wiki/projects, relative path inside vault is:
        rel_path = f"wiki/projects/{note_file_path.name}"
        # Read full content to sync
        full_content = note_file_path.read_text(encoding="utf-8")
        cmd = [
            "obsidian",
            f"vault={vault_name}",
            "create",
            f"name=wiki/projects/{note_file_path.stem}",
            f"content={full_content}",
            f"path={rel_path}",
            "overwrite",
            "silent"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if res.returncode == 0:
            print(f"  [OBSIDIAN] Centralized note synced via CLI.")
    except Exception:
        pass

    return note_file_path
