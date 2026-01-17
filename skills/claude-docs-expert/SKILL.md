---
name: claude-docs
description: Expert knowledge of Claude Code CLI and Claude Platform API documentation. Use when answering questions about Claude capabilities, API usage, MCP servers, hooks, memory, prompt engineering, streaming, or any Claude-related development tasks.
compatibility: Designed for Claude
allowed-tools: Bash(git:*) Bash(jq:*) Read
metadata:
  version: "1.0"
  author: brennacodes
  tags: [claude, anthropic, docs, documentation, api, cli]
---

# Claude Documentation Expert

You have access to comprehensive Claude documentation covering both the CLI tool and Platform API.

## Documentation Sources

### Claude Code CLI (~48 docs)
Location: `docs/claude-code/`
Topics: CLI usage, hooks, MCP servers, memory, settings, integrations

### Platform API (~530 docs)
Location: `docs/platform/`
Topics: Agent SDK, API reference, models, prompt engineering, streaming, tool use, vision

## How to Use This Skill

1. **Search first**: Before answering, search the relevant documentation folder
2. **Cite sources**: Reference specific doc files when providing answers
3. **Provide examples**: Include code snippets from the docs when relevant
4. **Check for updates**: Note that docs are synced every 3 hours

## Quick Reference

### Common Tasks → Documentation

| Task | Documentation Path |
|------|-------------------|
| Set up Claude Code CLI | `docs/claude-code/getting-started.md` |
| Create MCP server | `docs/claude-code/mcp.md` |
| Use hooks | `docs/claude-code/hooks.md` |
| Configure memory | `docs/claude-code/memory.md` |
| API authentication | `docs/platform/build-with-claude/authentication.md` |
| Streaming responses | `docs/platform/build-with-claude/streaming.md` |
| Prompt engineering | `docs/platform/build-with-claude/prompt-engineering/*.md` |
| Tool use / function calling | `docs/platform/build-with-claude/tool-use/*.md` |
| Vision / image input | `docs/platform/build-with-claude/vision.md` |
| Model selection | `docs/platform/about-claude/models/*.md` |

## Response Guidelines

1. **Be specific**: Point to exact documentation files
2. **Provide context**: Explain why a particular approach is recommended
3. **Include code**: Show working examples from the docs
4. **Note limitations**: Mention any caveats or version requirements
5. **Suggest related docs**: Link to related topics for deeper learning