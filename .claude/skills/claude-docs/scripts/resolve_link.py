#!/usr/bin/env python3
"""
Claude Docs Link Resolver

Translates documentation URLs and paths to local file paths.

Usage:
    # Single link
    python resolve_link.py "/en/hooks"
    python resolve_link.py "https://platform.claude.com/docs/en/agent-sdk/overview"
    
    # From stdin (for batch processing)
    echo "/en/hooks" | python resolve_link.py --stdin
    
    # Extract and resolve all links from a markdown file
    python resolve_link.py --extract docs/claude-code/skills.md

Output:
    Returns the local file path, or "NOT_FOUND: <original>" if no match.
"""

import sys
import re
import os
import json
from pathlib import Path

# Base path to docs directory (relative to this script's location)
SCRIPT_DIR = Path(__file__).parent.parent.parent  # skills/claude-docs-navigator/scripts -> repo root
DOCS_DIR = SCRIPT_DIR / "docs"
MANIFEST_PATH = SCRIPT_DIR / "docs_manifest.json"


def load_manifest():
    """Load the docs manifest for validation."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    return None


def resolve_link(link: str, source_file: str = None) -> str:
    """
    Resolve a documentation link to a local file path.
    
    Args:
        link: The URL or path to resolve
        source_file: Optional source file for relative path resolution
        
    Returns:
        Local file path or "NOT_FOUND: <original>"
    """
    original = link
    
    # Strip any markdown link syntax
    link = link.strip()
    if link.startswith('['):
        # Extract URL from [text](url)
        match = re.search(r'\]\(([^)]+)\)', link)
        if match:
            link = match.group(1)
    
    # Remove any anchor fragments
    link = link.split('#')[0]
    
    # Skip external non-Anthropic links
    if link.startswith('http') and 'claude.com' not in link and 'anthropic.com' not in link:
        return f"EXTERNAL: {original}"
    
    local_path = None
    
    # Pattern 1: Internal Claude Code links like /en/hooks
    if link.startswith('/en/'):
        slug = link[4:]  # Remove /en/
        local_path = DOCS_DIR / "claude-code" / f"{slug}.md"
    
    # Pattern 2: Full platform.claude.com URLs
    elif 'platform.claude.com/docs/en/' in link:
        match = re.search(r'platform\.claude\.com/docs/en/(.+?)(?:\.md)?$', link)
        if match:
            slug = match.group(1)
            local_path = DOCS_DIR / "platform" / f"{slug}.md"
    
    # Pattern 3: Full code.claude.com URLs
    elif 'code.claude.com/docs/en/' in link:
        match = re.search(r'code\.claude\.com/docs/en/(.+?)(?:\.md)?$', link)
        if match:
            slug = match.group(1)
            local_path = DOCS_DIR / "claude-code" / f"{slug}.md"
    
    # Pattern 4: Relative paths like ./hooks.md or ../platform/x.md
    elif link.startswith('./') or link.startswith('../'):
        if source_file:
            source_dir = Path(source_file).parent
            local_path = (source_dir / link).resolve()
        else:
            # Can't resolve relative without source context
            return f"RELATIVE_NO_CONTEXT: {original}"
    
    # Pattern 5: Just a filename like hooks.md
    elif link.endswith('.md') and '/' not in link:
        # Search both directories
        for subdir in ['claude-code', 'platform']:
            candidate = DOCS_DIR / subdir / link
            if candidate.exists():
                local_path = candidate
                break
        if not local_path:
            # Try recursive search in platform
            for candidate in DOCS_DIR.rglob(link):
                local_path = candidate
                break
    
    # Pattern 6: href="/en/something" (from Card components)
    elif 'href="' in link:
        match = re.search(r'href="(/en/[^"]+)"', link)
        if match:
            return resolve_link(match.group(1), source_file)
    
    # Validate the path exists
    if local_path:
        if local_path.exists():
            return str(local_path)
        else:
            # Try without .md extension being doubled
            if str(local_path).endswith('.md.md'):
                fixed = Path(str(local_path)[:-3])
                if fixed.exists():
                    return str(fixed)
            # Try adding .md if missing
            if not str(local_path).endswith('.md'):
                with_md = Path(str(local_path) + '.md')
                if with_md.exists():
                    return str(with_md)
            return f"NOT_FOUND: {original} -> {local_path}"
    
    return f"UNRECOGNIZED: {original}"


def extract_links(markdown_content: str) -> list[str]:
    """Extract all links from markdown content."""
    links = []
    
    # Standard markdown links [text](url)
    links.extend(re.findall(r'\]\(([^)]+)\)', markdown_content))
    
    # href attributes
    links.extend(re.findall(r'href="([^"]+)"', markdown_content))
    
    # Filter to only doc-like links
    doc_links = []
    for link in links:
        if any([
            link.startswith('/en/'),
            'claude.com/docs' in link,
            link.endswith('.md'),
            link.startswith('./'),
            link.startswith('../'),
        ]):
            doc_links.append(link)
    
    return list(set(doc_links))  # Deduplicate


def resolve_all_in_file(filepath: str) -> dict:
    """Extract and resolve all links in a markdown file."""
    with open(filepath) as f:
        content = f.read()
    
    links = extract_links(content)
    results = {}
    
    for link in links:
        results[link] = resolve_link(link, filepath)
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Resolve Claude doc links to local paths')
    parser.add_argument('link', nargs='?', help='Link to resolve')
    parser.add_argument('--stdin', action='store_true', help='Read links from stdin')
    parser.add_argument('--extract', metavar='FILE', help='Extract and resolve all links from a file')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--source', metavar='FILE', help='Source file for relative path resolution')
    
    args = parser.parse_args()
    
    if args.extract:
        results = resolve_all_in_file(args.extract)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for link, resolved in sorted(results.items()):
                print(f"{link}")
                print(f"  -> {resolved}")
                print()
    
    elif args.stdin:
        for line in sys.stdin:
            link = line.strip()
            if link:
                result = resolve_link(link, args.source)
                if args.json:
                    print(json.dumps({"input": link, "resolved": result}))
                else:
                    print(result)
    
    elif args.link:
        result = resolve_link(args.link, args.source)
        if args.json:
            print(json.dumps({"input": args.link, "resolved": result}))
        else:
            print(result)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
