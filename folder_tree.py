#!/usr/bin/env python3
"""
Folder Tree Generator

Generates a text-based tree of a directory's sub-folders and files,
suitable for pasting into Obsidian, Markdown documents, or anywhere else.

Usage:
    python folder_tree.py <path>                          # print to console
    python folder_tree.py <path> -o tree.md               # write to file
    python folder_tree.py <path> --dirs-only              # folders only
    python folder_tree.py <path> --depth 2                # limit depth
    python folder_tree.py <path> --exclude .git node_modules
    python folder_tree.py <path> --include "*.md" "*.txt" # only these files

No admin privileges or third-party packages required — pure Python 3.
"""

import argparse
import fnmatch
import os
import sys


def build_tree(
    root,
    prefix="",
    dirs_only=False,
    max_depth=None,
    current_depth=0,
    exclude=None,
    include=None,
):
    """Recursively build a list of lines representing the folder tree."""
    if max_depth is not None and current_depth >= max_depth:
        return []

    exclude = exclude or []

    try:
        entries = sorted(os.listdir(root), key=lambda s: (not os.path.isdir(os.path.join(root, s)), s.lower()))
    except PermissionError:
        return [f"{prefix}[access denied]"]

    # Separate dirs and files
    dirs = [e for e in entries if os.path.isdir(os.path.join(root, e)) and e not in exclude]
    files = [e for e in entries if not os.path.isdir(os.path.join(root, e))]

    # Apply include filter to files (if specified)
    if include:
        files = [f for f in files if any(fnmatch.fnmatch(f, pat) for pat in include)]

    if dirs_only:
        files = []

    items = dirs + files
    lines = []

    for i, name in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        full_path = os.path.join(root, name)

        if os.path.isdir(full_path):
            lines.append(f"{prefix}{connector}{name}/")
            extension = "    " if is_last else "│   "
            lines.extend(
                build_tree(
                    full_path,
                    prefix=prefix + extension,
                    dirs_only=dirs_only,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    exclude=exclude,
                    include=include,
                )
            )
        else:
            lines.append(f"{prefix}{connector}{name}")

    return lines


def generate_tree(
    path,
    dirs_only=False,
    max_depth=None,
    exclude=None,
    include=None,
):
    """Return the full tree as a string."""
    root_name = os.path.basename(os.path.abspath(path)) or path
    lines = [f"{root_name}/"]
    lines.extend(
        build_tree(
            path,
            dirs_only=dirs_only,
            max_depth=max_depth,
            exclude=exclude,
            include=include,
        )
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a text tree of a folder's contents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python folder_tree.py "C:/Users/me/ObsidianVault"
  python folder_tree.py . -o tree.md
  python folder_tree.py . --dirs-only --depth 2
  python folder_tree.py . --exclude .git .obsidian --include "*.md"
""",
    )
    parser.add_argument("path", help="Root directory to scan")
    parser.add_argument("-o", "--output", help="Write output to this file instead of the console")
    parser.add_argument("--dirs-only", action="store_true", help="Only show directories, skip files")
    parser.add_argument("--depth", type=int, default=None, help="Maximum depth to recurse (e.g. 2)")
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="Directory names to skip (e.g. .git node_modules .obsidian)",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        default=None,
        help='Only show files matching these patterns (e.g. "*.md" "*.txt")',
    )

    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(f"Error: '{args.path}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    tree = generate_tree(
        args.path,
        dirs_only=args.dirs_only,
        max_depth=args.depth,
        exclude=args.exclude,
        include=args.include,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(tree + "\n")
        print(f"Tree written to {args.output}")
    else:
        print(tree)


if __name__ == "__main__":
    main()
