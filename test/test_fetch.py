#!/usr/bin/env python3
"""
Quick test to verify multi-source fetching works without downloading everything.
Tests the updated structure with claude-code/ and platform/ directories.
"""
import sys
sys.path.insert(0, 'scripts')

from fetch_claude_docs import (
    DOC_SOURCES,
    discover_sitemap_and_base_url,
    discover_documentation_pages,
    fetch_markdown_content,
    url_to_safe_filename
)
import requests

def test_sources():
    """Test each source configuration."""
    print("Testing multi-source documentation fetching (v4.0)...")
    print("=" * 70)
    print("\nExpected structure:")
    print("  docs/claude-code/hooks.md           (flat)")
    print("  docs/platform/about-claude/models/overview.md  (hierarchical)")
    print("=" * 70)

    with requests.Session() as session:
        for source_key, source_config in DOC_SOURCES.items():
            print(f"\n🔍 Testing {source_config['name']} ({source_key})")
            print("-" * 70)

            try:
                # Test sitemap discovery
                print(f"  Discovering sitemap from {len(source_config['sitemap_urls'])} URL(s)...")
                sitemap_url, base_url = discover_sitemap_and_base_url(
                    session,
                    source_config['sitemap_urls']
                )
                print(f"  ✓ Found sitemap: {sitemap_url}")
                print(f"  ✓ Base URL: {base_url}")

                # Test page discovery
                print(f"  Discovering documentation pages...")
                doc_pages = discover_documentation_pages(
                    session,
                    sitemap_url,
                    source_config['url_patterns'],
                    source_config['skip_patterns'],
                    source_config['name']
                )
                print(f"  ✓ Discovered {len(doc_pages)} pages")

                if doc_pages:
                    # Test fetching one document
                    test_page = doc_pages[0]
                    print(f"  Testing fetch of: {test_page}")

                    filename = url_to_safe_filename(
                        test_page,
                        source_key,
                        source_config['preserve_hierarchy']
                    )
                    print(f"  Will save as: {filename}")

                    # Actually fetch it
                    filename, content = fetch_markdown_content(
                        test_page,
                        session,
                        base_url,
                        source_key,
                        source_config['preserve_hierarchy']
                    )
                    print(f"  ✓ Fetched {len(content)} bytes")
                    print(f"  ✓ First 100 chars: {content[:100]}...")

                print(f"\n  ✅ {source_key}: All tests passed!")

            except Exception as e:
                print(f"  ❌ Error testing {source_key}: {e}")
                import traceback
                traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test complete!")

if __name__ == "__main__":
    test_sources()
