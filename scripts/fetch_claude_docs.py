#!/usr/bin/env python3
"""
Improved Claude Code documentation fetcher with better robustness.
"""

import requests
import time
from pathlib import Path
from typing import List, Tuple, Set, Optional
import logging
from datetime import datetime
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import json
import hashlib
import os
import re
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Documentation sources configuration
DOC_SOURCES = {
    "claude-code": {
        "name": "Claude Code",
        "sitemap_urls": [
            "https://code.claude.com/docs/sitemap.xml",
            "https://docs.anthropic.com/sitemap.xml",  # Legacy fallback
        ],
        "url_patterns": [
            '/docs/en/',  # New structure (code.claude.com)
            '/en/docs/claude-code/',  # Legacy structure (docs.anthropic.com)
        ],
        "skip_patterns": [],  # Don't skip anything for code docs
        "preserve_hierarchy": False,  # Flat structure for code docs
        "fallback_pages": [
            "/docs/en/overview",
            "/docs/en/setup",
            "/docs/en/quickstart",
            "/docs/en/memory",
            "/docs/en/common-workflows",
            "/docs/en/mcp",
            "/docs/en/hooks",
        ]
    },
    "platform": {
        "name": "Claude Platform API",
        "sitemap_urls": [
            "https://platform.claude.com/sitemap.xml",
        ],
        "url_patterns": [
            '/docs/en/',  # platform.claude.com/docs/en/...
        ],
        "skip_patterns": [
            '/legacy/',    # Legacy documentation
        ],
        "preserve_hierarchy": True,  # Preserve directory structure
        "fallback_pages": [
            "/docs/en/intro",
            "/docs/en/get-started",
            "/docs/en/about-claude/models/overview",
            "/docs/en/build-with-claude/overview",
            "/docs/en/api/overview",
        ]
    }
}

MANIFEST_FILE = "docs_manifest.json"

# Base URL will be discovered from sitemap
# No longer using global variable

# Headers to bypass caching and identify the script
HEADERS = {
    'User-Agent': 'Claude-Code-Docs-Fetcher/3.0',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # initial delay in seconds
MAX_RETRY_DELAY = 30  # maximum delay in seconds
RATE_LIMIT_DELAY = 0.5  # seconds between requests


def load_manifest(docs_dir: Path) -> dict:
    """Load the manifest of previously fetched files."""
    manifest_path = docs_dir / MANIFEST_FILE
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            # Ensure required keys exist
            if "files" not in manifest:
                manifest["files"] = {}
            return manifest
        except Exception as e:
            logger.warning(f"Failed to load manifest: {e}")
    return {"files": {}, "last_updated": None}


def save_manifest(docs_dir: Path, manifest: dict) -> None:
    """Save the manifest of fetched files."""
    manifest_path = docs_dir / MANIFEST_FILE
    manifest["last_updated"] = datetime.now().isoformat()
    
    # Get GitHub repository from environment or use default
    github_repo = os.environ.get('GITHUB_REPOSITORY', 'ericbuess/claude-code-docs')
    github_ref = os.environ.get('GITHUB_REF_NAME', 'main')
    
    # Validate repository name format (owner/repo)
    if not re.match(r'^[\w.-]+/[\w.-]+$', github_repo):
        logger.warning(f"Invalid repository format: {github_repo}, using default")
        github_repo = 'ericbuess/claude-code-docs'
    
    # Validate branch/ref name
    if not re.match(r'^[\w.-]+$', github_ref):
        logger.warning(f"Invalid ref format: {github_ref}, using default")
        github_ref = 'main'
    
    manifest["base_url"] = f"https://raw.githubusercontent.com/{github_repo}/{github_ref}/docs/"
    manifest["github_repository"] = github_repo
    manifest["github_ref"] = github_ref
    manifest["description"] = "Claude Code documentation manifest. Keys are filenames, append to base_url for full URL."
    manifest_path.write_text(json.dumps(manifest, indent=2))


def url_to_safe_filename(url_path: str, source_key: str, preserve_hierarchy: bool = False) -> str:
    """
    Convert a URL path to a safe filename.

    Args:
        url_path: The URL path (e.g., /docs/en/intro or /docs/en/about-claude/models/overview)
        source_key: The source key (e.g., 'code' or 'platform')
        preserve_hierarchy: If True, preserve directory structure; if False, flatten with __

    Returns:
        Relative path from docs directory (e.g., 'code/intro.md' or 'platform/about-claude/models/overview.md')
    """
    # Remove the /docs/en/ prefix (or legacy prefixes)
    for prefix in ['/docs/en/', '/en/docs/claude-code/', '/docs/claude-code/', '/claude-code/']:
        if prefix in url_path:
            path = url_path.split(prefix)[-1]
            break
    else:
        # If no known prefix, use the path as-is
        path = url_path.lstrip('/')

    # Remove trailing slashes
    path = path.rstrip('/')

    # Ensure .md extension
    if not path.endswith('.md'):
        path += '.md'

    if preserve_hierarchy:
        # Keep directory structure: source/section/subsection/page.md
        return f"{source_key}/{path}"
    else:
        # Flatten with double underscores: source/section__subsection__page.md
        flat_name = path.replace('/', '__')
        return f"{source_key}/{flat_name}"


def discover_sitemap_and_base_url(session: requests.Session, sitemap_urls: List[str]) -> Tuple[str, str]:
    """
    Discover the sitemap URL and extract the base URL from it.

    Args:
        session: requests Session object
        sitemap_urls: List of sitemap URLs to try

    Returns:
        Tuple of (sitemap_url, base_url)
    """
    for sitemap_url in sitemap_urls:
        try:
            logger.info(f"Trying sitemap: {sitemap_url}")
            response = session.get(sitemap_url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                # Extract base URL from the first URL in sitemap
                # Parse XML safely to prevent XXE attacks
                try:
                    # Try with security parameters (Python 3.8+)
                    parser = ET.XMLParser(forbid_dtd=True, forbid_entities=True, forbid_external=True)
                    root = ET.fromstring(response.content, parser=parser)
                except TypeError:
                    # Fallback for older Python versions
                    logger.warning("XMLParser security parameters not available, using default parser")
                    root = ET.fromstring(response.content)

                # Try with namespace first
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                first_url = None
                for url_elem in root.findall('.//ns:url', namespace):
                    loc_elem = url_elem.find('ns:loc', namespace)
                    if loc_elem is not None and loc_elem.text:
                        first_url = loc_elem.text
                        break

                # If no URLs found, try without namespace
                if not first_url:
                    for loc_elem in root.findall('.//loc'):
                        if loc_elem.text:
                            first_url = loc_elem.text
                            break

                if first_url:
                    parsed = urlparse(first_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    logger.info(f"Found sitemap at {sitemap_url}, base URL: {base_url}")
                    return sitemap_url, base_url
        except Exception as e:
            logger.warning(f"Failed to fetch {sitemap_url}: {e}")
            continue

    raise Exception(f"Could not find a valid sitemap from provided URLs")


def discover_documentation_pages(
    session: requests.Session,
    sitemap_url: str,
    url_patterns: List[str],
    skip_patterns: List[str],
    source_name: str
) -> List[str]:
    """
    Dynamically discover documentation pages from a sitemap.

    Args:
        session: requests Session object
        sitemap_url: URL of the sitemap to fetch
        url_patterns: List of URL patterns that identify relevant docs (e.g., ['/docs/en/'])
        skip_patterns: List of URL patterns to skip (e.g., ['/legacy/', '/examples/'])
        source_name: Name of the source for logging (e.g., 'Claude Code', 'Platform API')

    Returns:
        List of URL paths for discovered documentation pages
    """
    logger.info(f"Discovering {source_name} documentation pages from sitemap...")

    try:
        response = session.get(sitemap_url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        # Parse XML sitemap safely
        try:
            # Try with security parameters (Python 3.8+)
            parser = ET.XMLParser(forbid_dtd=True, forbid_entities=True, forbid_external=True)
            root = ET.fromstring(response.content, parser=parser)
        except TypeError:
            # Fallback for older Python versions
            logger.warning("XMLParser security parameters not available, using default parser")
            root = ET.fromstring(response.content)

        # Extract all URLs from sitemap
        urls = []

        # Try with namespace first
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_elem in root.findall('.//ns:url', namespace):
            loc_elem = url_elem.find('ns:loc', namespace)
            if loc_elem is not None and loc_elem.text:
                urls.append(loc_elem.text)

        # If no URLs found, try without namespace
        if not urls:
            for loc_elem in root.findall('.//loc'):
                if loc_elem.text:
                    urls.append(loc_elem.text)

        logger.info(f"Found {len(urls)} total URLs in sitemap")

        # Filter for relevant documentation pages
        doc_pages = []

        for url in urls:
            # Check if URL matches any of the desired patterns
            if any(pattern in url for pattern in url_patterns):
                parsed = urlparse(url)
                path = parsed.path

                # Remove any file extension
                if path.endswith('.html'):
                    path = path[:-5]
                elif path.endswith('/'):
                    path = path[:-1]

                # Skip if matches any skip pattern
                if any(skip in path for skip in skip_patterns):
                    continue

                doc_pages.append(path)

        # Remove duplicates and sort
        doc_pages = sorted(list(set(doc_pages)))

        logger.info(f"Discovered {len(doc_pages)} {source_name} documentation pages")

        return doc_pages

    except Exception as e:
        logger.error(f"Failed to discover pages from sitemap: {e}")
        raise


def validate_markdown_content(content: str, filename: str) -> None:
    """
    Validate that content is proper markdown.
    Raises ValueError if validation fails.
    """
    # Check for HTML content
    if not content or content.startswith('<!DOCTYPE') or '<html' in content[:100]:
        raise ValueError("Received HTML instead of markdown")
    
    # Check minimum length
    if len(content.strip()) < 50:
        raise ValueError(f"Content too short ({len(content)} bytes)")
    
    # Check for common markdown elements
    lines = content.split('\n')
    markdown_indicators = [
        '# ',      # Headers
        '## ',
        '### ',
        '```',     # Code blocks
        '- ',      # Lists
        '* ',
        '1. ',
        '[',       # Links
        '**',      # Bold
        '_',       # Italic
        '> ',      # Quotes
    ]
    
    # Count markdown indicators
    indicator_count = 0
    for line in lines[:50]:  # Check first 50 lines
        for indicator in markdown_indicators:
            if line.strip().startswith(indicator) or indicator in line:
                indicator_count += 1
                break
    
    # Require at least some markdown formatting
    if indicator_count < 3:
        raise ValueError(f"Content doesn't appear to be markdown (only {indicator_count} markdown indicators found)")
    
    # Check for common documentation patterns
    doc_patterns = ['installation', 'usage', 'example', 'api', 'configuration', 'claude', 'code']
    content_lower = content.lower()
    pattern_found = any(pattern in content_lower for pattern in doc_patterns)
    
    if not pattern_found:
        logger.warning(f"Content for {filename} doesn't contain expected documentation patterns")


def fetch_markdown_content(
    path: str,
    session: requests.Session,
    base_url: str,
    source_key: str,
    preserve_hierarchy: bool
) -> Tuple[str, str]:
    """
    Fetch markdown content with better error handling and validation.

    Args:
        path: URL path (e.g., /docs/en/intro)
        session: requests Session object
        base_url: Base URL (e.g., https://platform.claude.com)
        source_key: Source key (e.g., 'code' or 'platform')
        preserve_hierarchy: Whether to preserve directory structure in filename

    Returns:
        Tuple of (filename, content)
    """
    markdown_url = f"{base_url}{path}.md"
    filename = url_to_safe_filename(path, source_key, preserve_hierarchy)

    logger.info(f"Fetching: {markdown_url} -> {filename}")

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(markdown_url, headers=HEADERS, timeout=30, allow_redirects=True)

            # Handle specific HTTP errors
            if response.status_code == 429:  # Rate limited
                wait_time = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()

            # Get content and validate
            content = response.text
            validate_markdown_content(content, filename)

            logger.info(f"Successfully fetched and validated {filename} ({len(content)} bytes)")
            return filename, content

        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {filename}: {e}")
            if attempt < MAX_RETRIES - 1:
                # Exponential backoff with jitter
                delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                # Add jitter to prevent thundering herd
                jittered_delay = delay * random.uniform(0.5, 1.0)
                logger.info(f"Retrying in {jittered_delay:.1f} seconds...")
                time.sleep(jittered_delay)
            else:
                raise Exception(f"Failed to fetch {filename} after {MAX_RETRIES} attempts: {e}")

        except ValueError as e:
            logger.error(f"Content validation failed for {filename}: {e}")
            raise


def content_has_changed(content: str, old_hash: str) -> bool:
    """Check if content has changed based on hash."""
    new_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return new_hash != old_hash


def fetch_changelog(session: requests.Session) -> Tuple[str, str]:
    """
    Fetch Claude Code changelog from GitHub repository.
    Returns tuple of (filename, content).
    """
    changelog_url = "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md"
    filename = "changelog.md"
    
    logger.info(f"Fetching Claude Code changelog: {changelog_url}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(changelog_url, headers=HEADERS, timeout=30, allow_redirects=True)
            
            if response.status_code == 429:  # Rate limited
                wait_time = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            content = response.text
            
            # Add header to indicate this is from Claude Code repo, not docs site
            header = """# Claude Code Changelog

> **Source**: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
> 
> This is the official Claude Code release changelog, automatically fetched from the Claude Code repository. For documentation, see other topics via `/docs`.

---

"""
            content = header + content
            
            # Basic validation
            if len(content.strip()) < 100:
                raise ValueError(f"Changelog content too short ({len(content)} bytes)")
            
            logger.info(f"Successfully fetched changelog ({len(content)} bytes)")
            return filename, content
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for changelog: {e}")
            if attempt < MAX_RETRIES - 1:
                delay = min(RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                jittered_delay = delay * random.uniform(0.5, 1.0)
                logger.info(f"Retrying in {jittered_delay:.1f} seconds...")
                time.sleep(jittered_delay)
            else:
                raise Exception(f"Failed to fetch changelog after {MAX_RETRIES} attempts: {e}")
        
        except ValueError as e:
            logger.error(f"Changelog validation failed: {e}")
            raise


def save_markdown_file(docs_dir: Path, filename: str, content: str) -> str:
    """
    Save markdown content and return its hash.
    Creates subdirectories as needed.

    Args:
        docs_dir: Base docs directory
        filename: Relative filename (may include subdirectories, e.g., 'platform/intro.md')
        content: Markdown content

    Returns:
        SHA256 hash of the content
    """
    file_path = docs_dir / filename

    try:
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding='utf-8')
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        logger.info(f"Saved: {filename}")
        return content_hash
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        raise


def cleanup_old_files(docs_dir: Path, current_files: Set[str], manifest: dict) -> None:
    """
    Remove only files that were previously fetched but no longer exist.
    Preserves manually added files.
    """
    previous_files = set(manifest.get("files", {}).keys())
    files_to_remove = previous_files - current_files
    
    for filename in files_to_remove:
        if filename == MANIFEST_FILE:  # Never delete the manifest
            continue
            
        file_path = docs_dir / filename
        if file_path.exists():
            logger.info(f"Removing obsolete file: {filename}")
            file_path.unlink()


def main():
    """Main function with multi-source support."""
    start_time = datetime.now()
    logger.info("Starting multi-source documentation fetch (v4.0)")

    # Log configuration
    github_repo = os.environ.get('GITHUB_REPOSITORY', 'ericbuess/claude-code-docs')
    logger.info(f"GitHub repository: {github_repo}")
    logger.info(f"Documentation sources: {', '.join(DOC_SOURCES.keys())}")

    # Create docs directory at repository root
    docs_dir = Path(__file__).parent.parent / 'docs'
    docs_dir.mkdir(exist_ok=True)
    logger.info(f"Output directory: {docs_dir}")

    # Create subdirectories for each source
    for source_key in DOC_SOURCES.keys():
        (docs_dir / source_key).mkdir(exist_ok=True)

    # Load manifest
    manifest = load_manifest(docs_dir)

    # Global statistics
    total_successful = 0
    total_failed = 0
    fetched_files = set()
    new_manifest = {"files": {}, "sources": {}}

    # Create a session for connection pooling
    with requests.Session() as session:
        # Process each documentation source
        for source_key, source_config in DOC_SOURCES.items():
            logger.info("\n" + "="*70)
            logger.info(f"Processing {source_config['name']} ({source_key})")
            logger.info("="*70)

            source_successful = 0
            source_failed = 0
            source_failed_pages = []

            try:
                # Discover sitemap and base URL for this source
                sitemap_url, base_url = discover_sitemap_and_base_url(
                    session,
                    source_config['sitemap_urls']
                )

                # Discover documentation pages
                documentation_pages = discover_documentation_pages(
                    session,
                    sitemap_url,
                    source_config['url_patterns'],
                    source_config['skip_patterns'],
                    source_config['name']
                )

                if not documentation_pages:
                    logger.warning(f"No pages discovered for {source_key}, trying fallback...")
                    documentation_pages = source_config['fallback_pages']

                # Fetch each page
                for i, page_path in enumerate(documentation_pages, 1):
                    logger.info(f"[{source_key}] Processing {i}/{len(documentation_pages)}: {page_path}")

                    try:
                        filename, content = fetch_markdown_content(
                            page_path,
                            session,
                            base_url,
                            source_key,
                            source_config['preserve_hierarchy']
                        )

                        # Check if content has changed
                        old_hash = manifest.get("files", {}).get(filename, {}).get("hash", "")
                        old_entry = manifest.get("files", {}).get(filename, {})

                        if content_has_changed(content, old_hash):
                            content_hash = save_markdown_file(docs_dir, filename, content)
                            logger.info(f"  ✓ Updated: {filename}")
                            last_updated = datetime.now().isoformat()
                        else:
                            content_hash = old_hash
                            logger.info(f"  • Unchanged: {filename}")
                            last_updated = old_entry.get("last_updated", datetime.now().isoformat())

                        new_manifest["files"][filename] = {
                            "source": source_key,
                            "source_name": source_config['name'],
                            "original_url": f"{base_url}{page_path}",
                            "original_md_url": f"{base_url}{page_path}.md",
                            "hash": content_hash,
                            "last_updated": last_updated
                        }

                        fetched_files.add(filename)
                        source_successful += 1
                        total_successful += 1

                        # Rate limiting
                        if i < len(documentation_pages):
                            time.sleep(RATE_LIMIT_DELAY)

                    except Exception as e:
                        logger.error(f"  ✗ Failed to process {page_path}: {e}")
                        source_failed += 1
                        total_failed += 1
                        source_failed_pages.append(page_path)

                # Store source metadata
                new_manifest["sources"][source_key] = {
                    "name": source_config['name'],
                    "sitemap_url": sitemap_url,
                    "base_url": base_url,
                    "pages_discovered": len(documentation_pages),
                    "pages_fetched": source_successful,
                    "pages_failed": source_failed,
                    "failed_pages": source_failed_pages
                }

                logger.info(f"\n{source_config['name']} Summary:")
                logger.info(f"  Discovered: {len(documentation_pages)} pages")
                logger.info(f"  Successful: {source_successful}")
                logger.info(f"  Failed: {source_failed}")

            except Exception as e:
                logger.error(f"Failed to process {source_key}: {e}")
                logger.warning(f"Skipping {source_config['name']} due to critical error")
                new_manifest["sources"][source_key] = {
                    "name": source_config['name'],
                    "error": str(e),
                    "pages_fetched": 0
                }

        # Fetch Claude Code changelog (stored in claude-code/ directory)
        logger.info("\n" + "="*70)
        logger.info("Fetching Claude Code changelog...")
        try:
            filename, content = fetch_changelog(session)
            # Save changelog in claude-code directory
            changelog_filename = f"claude-code/{filename}"

            # Check if content has changed
            old_hash = manifest.get("files", {}).get(changelog_filename, {}).get("hash", "")
            old_entry = manifest.get("files", {}).get(changelog_filename, {})

            if content_has_changed(content, old_hash):
                # Create claude-code directory if needed
                (docs_dir / "claude-code").mkdir(exist_ok=True)
                content_hash = save_markdown_file(docs_dir, changelog_filename, content)
                logger.info(f"  ✓ Updated: {changelog_filename}")
                last_updated = datetime.now().isoformat()
            else:
                content_hash = old_hash
                logger.info(f"  • Unchanged: {changelog_filename}")
                last_updated = old_entry.get("last_updated", datetime.now().isoformat())

            new_manifest["files"][changelog_filename] = {
                "source": "claude-code",
                "source_name": "Claude Code Changelog",
                "original_url": "https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md",
                "original_raw_url": "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md",
                "hash": content_hash,
                "last_updated": last_updated,
                "type": "changelog"
            }

            fetched_files.add(changelog_filename)
            total_successful += 1

        except Exception as e:
            logger.error(f"  ✗ Failed to fetch changelog: {e}")
            total_failed += 1

    # Clean up old files (only those we previously fetched)
    cleanup_old_files(docs_dir, fetched_files, manifest)

    # Add global metadata to manifest
    new_manifest["fetch_metadata"] = {
        "last_fetch_completed": datetime.now().isoformat(),
        "fetch_duration_seconds": (datetime.now() - start_time).total_seconds(),
        "total_files": len(fetched_files),
        "total_successful": total_successful,
        "total_failed": total_failed,
        "fetch_tool_version": "4.0",
        "multi_source": True
    }

    # Save new manifest
    save_manifest(docs_dir, new_manifest)

    # Final summary
    duration = datetime.now() - start_time
    logger.info("\n" + "="*70)
    logger.info("FINAL SUMMARY")
    logger.info("="*70)
    logger.info(f"Fetch completed in {duration}")
    logger.info(f"Total files: {len(fetched_files)}")
    logger.info(f"Successful: {total_successful}")
    logger.info(f"Failed: {total_failed}")
    logger.info("")

    for source_key, source_data in new_manifest["sources"].items():
        if "error" in source_data:
            logger.warning(f"  {source_data['name']}: ERROR - {source_data['error']}")
        else:
            logger.info(f"  {source_data['name']}: {source_data['pages_fetched']} pages")

    # Exit with error only if everything failed
    if total_successful == 0:
        logger.error("\nNo pages were fetched successfully!")
        sys.exit(1)
    elif total_failed > 0:
        logger.warning(f"\nCompleted with {total_failed} failures (partial success)")
    else:
        logger.info("\nAll pages fetched successfully!")


if __name__ == "__main__":
    main()