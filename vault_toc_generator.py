#!/usr/bin/env python3
"""
Obsidian Vault TOC Generator with Mermaid.js

Generates a visual table of contents for your Obsidian vault folders
using Mermaid diagrams, suitable for embedding in Obsidian notes.

Workflow:
  1. Generate template: python vault_toc_generator.py <path> -o toc.md
  2. Edit toc.md to organize files into sections
  3. Regenerate diagram: python vault_toc_generator.py -i toc.md -d mindmap

No admin privileges or third-party packages required — pure Python 3.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def scan_folder(path, exclude=None):
    """Scan folder and return list of all files (case-insensitive)."""
    exclude = exclude or [".git", ".obsidian", ".DS_Store", "node_modules"]

    try:
        entries = sorted([
            e for e in os.listdir(path)
            if os.path.isfile(os.path.join(path, e))
            and e not in exclude
        ])
        return entries
    except PermissionError:
        print(f"Error: Permission denied reading {path}", file=sys.stderr)
        return []


def generate_template_markdown(files, title="Table of Contents"):
    """Generate editable markdown template."""
    lines = [
        f"# {title}",
        "",
        "## How to Use This Template",
        "",
        "1. Edit the sections below to organize your files",
        "2. Use `### Section Name` for main sections",
        "3. Use `#### Subsection Name` for sub-sections (optional)",
        "4. Move file links between sections as needed",
        "5. Delete unused section headers",
        "6. Run the tool again to regenerate the mermaid diagram",
        "",
        "---",
        "",
        "## Files by Section",
        ""
    ]

    lines.append("### Section 1: First Half")
    lines.append("")
    lines.append("<!-- Add your files here -->")
    lines.append("")
    lines.extend([f"- [[{f}]]" for f in files[:len(files)//2]])
    lines.append("")
    lines.append("")

    lines.append("### Section 2: Second Half")
    lines.append("")
    lines.append("<!-- Add your files here -->")
    lines.append("")
    lines.extend([f"- [[{f}]]" for f in files[len(files)//2:]])
    lines.append("")

    return "\n".join(lines)


def parse_markdown_structure(markdown_text, title):
    """Parse organized markdown to extract sections and files."""
    lines = markdown_text.split('\n')
    sections = []
    current_section = None
    current_subsection = None

    for line in lines:
        # Main section (### heading)
        if re.match(r'^### ', line):
            section_name = line.replace('### ', '').strip()
            current_section = {
                'name': section_name,
                'files': [],
                'subsections': []
            }
            current_subsection = None
            sections.append(current_section)

        # Subsection (#### heading)
        elif re.match(r'^#### ', line):
            subsection_name = line.replace('#### ', '').strip()
            if current_section:
                current_subsection = {
                    'name': subsection_name,
                    'files': []
                }
                current_section['subsections'].append(current_subsection)

        # File link
        elif re.match(r'^- \[\[', line):
            file_name = re.search(r'\[\[(.*?)\]\]', line)
            if file_name:
                link = file_name.group(1)
                if current_subsection:
                    current_subsection['files'].append(link)
                elif current_section:
                    current_section['files'].append(link)

    return {'title': title, 'sections': sections}


def generate_mermaid_mindmap(config):
    """Generate a Mermaid mindmap diagram with subsections."""
    lines = ["```mermaid", "mindmap"]
    title = config['title']
    lines.append(f"  root((({title}))))")

    for section in config.get("sections", []):
        section_name = section["name"]
        safe_section = section_name.replace("(", "\\(").replace(")", "\\)")
        lines.append(f"    {safe_section}")

        # Add files from this section (not in subsections)
        for file in section.get("files", []):
            file_name = file.replace(".md", "").replace(".MD", "")
            safe_file = file_name.replace("(", "\\(").replace(")", "\\)")
            lines.append(f"      {safe_file}")

        # Add subsections
        for subsection in section.get("subsections", []):
            sub_name = subsection["name"]
            safe_sub = sub_name.replace("(", "\\(").replace(")", "\\)")
            lines.append(f"      {safe_sub}")

            for file in subsection.get("files", []):
                file_name = file.replace(".md", "").replace(".MD", "")
                safe_file = file_name.replace("(", "\\(").replace(")", "\\)")
                lines.append(f"        {safe_file}")

    lines.append("```")
    return "\n".join(lines)


def generate_mermaid_flowchart(config):
    """Generate a Mermaid flowchart diagram with subsections."""
    lines = ["```mermaid", "flowchart TD"]

    # Root node
    root_id = "root"
    title = config['title']
    safe_title = title.replace("\"", '\\"')
    lines.append(f"    {root_id}[\"{safe_title}\"]")

    # Sections and files
    node_counter = 0
    for section_idx, section in enumerate(config.get("sections", [])):
        section_name = section["name"]
        section_id = f"section_{section_idx}"
        safe_section = section_name.replace("\"", '\\"')
        lines.append(f"    {section_id}[\"{safe_section}\"]")
        lines.append(f"    {root_id} --> {section_id}")

        # Files directly in section
        for file_idx, file in enumerate(section.get("files", [])):
            file_name = file.replace(".md", "").replace(".MD", "")
            file_id = f"file_{section_idx}_{node_counter}"
            safe_file = file_name.replace("\"", '\\"')
            lines.append(f"    {file_id}[\"{safe_file}\"]")
            lines.append(f"    {section_id} --> {file_id}")
            node_counter += 1

        # Subsections
        for sub_idx, subsection in enumerate(section.get("subsections", [])):
            sub_name = subsection["name"]
            sub_id = f"subsection_{section_idx}_{sub_idx}"
            safe_sub = sub_name.replace("\"", '\\"')
            lines.append(f"    {sub_id}[\"{safe_sub}\"]")
            lines.append(f"    {section_id} --> {sub_id}")

            for file_idx, file in enumerate(subsection.get("files", [])):
                file_name = file.replace(".md", "").replace(".MD", "")
                file_id = f"subfile_{section_idx}_{sub_idx}_{file_idx}"
                safe_file = file_name.replace("\"", '\\"')
                lines.append(f"    {file_id}[\"{safe_file}\"]")
                lines.append(f"    {sub_id} --> {file_id}")

    lines.append("```")
    return "\n".join(lines)


def generate_markdown_with_diagram(config, markdown_content, diagram_type="mindmap"):
    """Generate markdown with original content + mermaid diagram."""
    # Generate mermaid diagram
    if diagram_type == "flowchart":
        diagram = generate_mermaid_flowchart(config)
    else:  # default mindmap
        diagram = generate_mermaid_mindmap(config)

    # Extract content before the diagram (if it exists)
    lines = markdown_content.split('\n')
    diagram_start = None
    for i, line in enumerate(lines):
        if line.startswith('```mermaid'):
            diagram_start = i
            break

    if diagram_start is not None:
        # Remove old diagram
        diagram_end = diagram_start
        for i in range(diagram_start, len(lines)):
            if lines[i].startswith('```') and i > diagram_start:
                diagram_end = i
                break

        # Reconstruct without old diagram
        content_before = '\n'.join(lines[:diagram_start]).rstrip()
        content_after = '\n'.join(lines[diagram_end + 1:]).lstrip()

        result = content_before + '\n\n' + diagram
        if content_after:
            result += '\n\n' + content_after
        return result
    else:
        # No existing diagram, add it at the beginning
        return diagram + '\n\n' + markdown_content


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mermaid-based table of contents for Obsidian vault folders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python vault_toc_generator.py "/path/to/SOP" -o toc.md
  python vault_toc_generator.py -i toc.md -d mindmap -o final.md
  python vault_toc_generator.py -i toc.md -d flowchart -o final.md
""",
    )
    parser.add_argument("path", nargs='?', help="Path to vault folder to scan")
    parser.add_argument(
        "-i", "--input",
        help="Input markdown file to parse (for regenerating diagram)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Write markdown output to this file"
    )
    parser.add_argument(
        "-d", "--diagram",
        choices=["mindmap", "flowchart"],
        default="mindmap",
        help="Mermaid diagram type: mindmap (default) or flowchart"
    )
    parser.add_argument(
        "-t", "--title",
        default="Table of Contents",
        help="Title for the TOC (default: Table of Contents)"
    )

    args = parser.parse_args()

    # Mode 1: Generate template from folder scan
    if args.path:
        if not os.path.isdir(args.path):
            print(f"Error: '{args.path}' is not a directory.", file=sys.stderr)
            sys.exit(1)

        print(f"Scanning {args.path}...")
        files = scan_folder(args.path)
        print(f"Found {len(files)} file(s)")

        markdown = generate_template_markdown(files, args.title)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(markdown)
            print(f"✓ Template written to {args.output}")
            print("Edit this file to organize files, then regenerate with: python vault_toc_generator.py -i <file> -d <style>")
        else:
            print("\n" + "=" * 60)
            print("Generated Template:")
            print("=" * 60 + "\n")
            print(markdown)

    # Mode 2: Parse existing markdown and regenerate diagram
    elif args.input:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"Reading {args.input}...")
        with open(args.input, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        config = parse_markdown_structure(markdown_content, args.title)
        result_markdown = generate_markdown_with_diagram(config, markdown_content, args.diagram)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result_markdown)
            print(f"✓ Markdown with {args.diagram} diagram written to {args.output}")
        else:
            print("\n" + "=" * 60)
            print("Generated Markdown:")
            print("=" * 60 + "\n")
            print(result_markdown)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
