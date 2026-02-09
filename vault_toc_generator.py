#!/usr/bin/env python3
"""
Obsidian Vault TOC Generator with Mermaid.js

Generates a visual table of contents for your Obsidian vault folders
using Mermaid diagrams, suitable for embedding in Obsidian notes.

Usage:
    python vault_toc_generator.py <path>              # scan and generate config
    python vault_toc_generator.py <path> -c config.json  # use existing config
    python vault_toc_generator.py <path> -o output.md    # write markdown to file

No admin privileges or third-party packages required — pure Python 3.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def scan_folder(path, exclude=None):
    """Scan folder and return list of markdown files."""
    exclude = exclude or [".git", ".obsidian", ".DS_Store", "node_modules"]

    try:
        entries = sorted([
            e for e in os.listdir(path)
            if os.path.isfile(os.path.join(path, e))
            and e.endswith(".md")
            and e not in exclude
        ])
        return entries
    except PermissionError:
        print(f"Error: Permission denied reading {path}", file=sys.stderr)
        return []


def create_default_config(files):
    """Create a default config structure."""
    return {
        "title": "Table of Contents",
        "sections": [
            {
                "name": "Uncategorized",
                "files": files
            }
        ]
    }


def generate_mermaid_mindmap(config):
    """Generate a Mermaid mindmap diagram."""
    lines = ["```mermaid", "mindmap"]
    title = config['title']
    lines.append(f"  root((({title}))))")

    for section in config.get("sections", []):
        section_name = section["name"]
        files = section.get("files", [])

        # Escape special characters in section name
        safe_section = section_name.replace("(", "\\(").replace(")", "\\)")
        lines.append(f"    {safe_section}")

        for file in files:
            # Remove .md extension for display
            file_name = file.replace(".md", "")
            safe_file = file_name.replace("(", "\\(").replace(")", "\\)")
            lines.append(f"      {safe_file}")

    lines.append("```")
    return "\n".join(lines)


def generate_mermaid_flowchart(config):
    """Generate a Mermaid flowchart diagram."""
    lines = ["```mermaid", "flowchart TD"]

    # Root node
    root_id = "root"
    title = config["title"].replace(" ", "_").replace("(", "").replace(")", "")
    lines.append(f"    {root_id}[\"{config['title']}\"]")

    # Sections and files
    for section_idx, section in enumerate(config.get("sections", [])):
        section_name = section["name"]
        section_id = f"section_{section_idx}"
        safe_section = section_name.replace("\"", '\\"')
        lines.append(f"    {section_id}[\"{safe_section}\"]")
        lines.append(f"    {root_id} --> {section_id}")

        for file_idx, file in enumerate(section.get("files", [])):
            file_name = file.replace(".md", "")
            file_id = f"file_{section_idx}_{file_idx}"
            safe_file = file_name.replace("\"", '\\"')
            lines.append(f"    {file_id}[\"{safe_file}\"]")
            lines.append(f"    {section_id} --> {file_id}")

    lines.append("```")
    return "\n".join(lines)


def generate_markdown(config, diagram_type="mindmap"):
    """Generate complete markdown with mermaid diagram."""
    title = config.get("title", "Table of Contents")

    lines = [
        f"# {title}",
        "",
        "## Visual Overview",
        ""
    ]

    if diagram_type == "mindmap":
        lines.append(generate_mermaid_mindmap(config))
    else:
        lines.append(generate_mermaid_flowchart(config))

    lines.extend([
        "",
        "## Files by Section",
        ""
    ])

    for section in config.get("sections", []):
        section_name = section["name"]
        files = section.get("files", [])

        lines.append(f"### {section_name}")
        lines.append("")

        if files:
            for file in files:
                file_link = file.replace(".md", "")
                lines.append(f"- [[{file_link}]]")
        else:
            lines.append("*(No files in this section)*")

        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mermaid-based table of contents for Obsidian vault folders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python vault_toc_generator.py "/path/to/SOP"
  python vault_toc_generator.py "/path/to/SOP" -c sections.json
  python vault_toc_generator.py "/path/to/SOP" -o toc.md
  python vault_toc_generator.py "/path/to/SOP" -d flowchart
""",
    )
    parser.add_argument("path", help="Path to vault folder to scan")
    parser.add_argument(
        "-c", "--config",
        help="Path to config JSON file with section definitions"
    )
    parser.add_argument(
        "-o", "--output",
        help="Write markdown output to this file"
    )
    parser.add_argument(
        "-d", "--diagram",
        choices=["mindmap", "flowchart"],
        default="mindmap",
        help="Mermaid diagram type (default: mindmap)"
    )
    parser.add_argument(
        "-t", "--title",
        default="Table of Contents",
        help="Title for the TOC (default: Table of Contents)"
    )

    args = parser.parse_args()

    # Validate path
    if not os.path.isdir(args.path):
        print(f"Error: '{args.path}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Load config or scan folder
    if args.config and os.path.exists(args.config):
        print(f"Loading config from {args.config}...")
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        print(f"Scanning {args.path}...")
        files = scan_folder(args.path)
        config = create_default_config(files)
        config["title"] = args.title

        # Save default config for editing
        config_path = os.path.join(os.path.dirname(args.path), "toc_config.json")
        print(f"\nFound {len(files)} markdown file(s)")
        print(f"Default config saved to: {config_path}")
        print("Edit this file to organize files into sections, then re-run with -c option")
        print("")

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    # Generate markdown
    markdown = generate_markdown(config, args.diagram)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"✓ Markdown written to {args.output}")
        print("Copy the content into your Obsidian note.")
    else:
        print("\n" + "=" * 60)
        print("Generated Markdown (copy into your Obsidian note):")
        print("=" * 60 + "\n")
        print(markdown)


if __name__ == "__main__":
    main()
