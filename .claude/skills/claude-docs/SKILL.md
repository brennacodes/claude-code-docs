---
name: claude-docs-navigator
description: Navigate Claude docs. Automatically follows cross-references to gain a complete understanding of the documentation. Use when creating code maps (or codemaps), answering questions about Claude, Claude Code, Claude API, MCP, any other Claude feature, or when the user needs to understand or map out how different Claude features connect.
compatibility: Designed for Claude
allowed-tools: Bash(jq:*), ReadFile(*), WriteFile(*)
metadata:
  version: "1.0"
  author: brennacodes
  repository: https://github.com/brennacodes/claude-code-docs
  tags: [docs, documentation, reference, codemap, Claude, Claude Code, Claude API, MCP]
---

# Claude Documentation Navigator

You have access to the [Claude documentation](~/.claude-code-docs/docs/).
As well as a manifest for the documentation (`~/.claude-code-docs/docs_manifest.json`).

The docs are organized based on their source:
- **Claude Platform API** (`~/.claude-code-docs/docs/platform/`): ~530 docs covering the entire Claude ecosystem
- **Claude Code CLI** (`~/.claude-code-docs/docs/claude-code/`): ~48 docs covering the CLI tool

## Documentation Manifest

The file `docs_manifest.json` contains metadata about all documentation files:
- File paths
- Source URLs
- Content hashes (for change detection)
- Last updated timestamps

## Core Principle: Follow the References

When searching for information, **trace conceptual relationships** by following cross-references in the documentation. Don't just read one file — follow the links to build complete understanding.

### Reference Patterns to Recognize

The docs use these link formats:

```markdown
# Internal links (same source)
[Hooks reference](/en/hooks)
[slash command](/en/slash-commands)
See [Get started with Claude Code hooks](/en/hooks-guide)

# Cross-source links (Platform API from Code docs)
[Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)
[What are Skills?](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

# Card links (in <Card> components)
href="/en/cli-reference"
href="/en/github-actions"
```

**When you see these patterns, read the linked document** to understand the full relationship.

### Step 1: Find the Primary Doc

Start with the most relevant doc based on the current context.

### Step 2: Identify Cross-References

#### Reference Patterns to Recognize:
```markdown
# Internal links (same source)
[Hooks reference](/en/hooks)
[slash command](/en/slash-commands)
See [Get started with Claude Code hooks](/en/hooks-guide)

# Cross-source links (Platform API from Code docs)
[Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)
[What are Skills?](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

# Card links (in <Card> components)
href="/en/cli-reference"
href="/en/github-actions"
```

### Step 3: Resolve Links to Local Paths

**Do NOT fetch URLs from the web.** Use the resolver script:

```bash
python scripts/resolve_link.py "/en/hooks"
# → docs/claude-code/hooks.md

python scripts/resolve_link.py "https://platform.claude.com/docs/en/agent-sdk/overview"
# → docs/platform/agent-sdk/overview.md

# Extract all links from a doc
python scripts/resolve_link.py --extract docs/claude-code/skills.md
```

**Quick manual translation:**

| Link Pattern | Local Path |
|--------------|------------|
| `/en/<slug>` | `docs/claude-code/<slug>.md` |
| `https://platform.claude.com/docs/en/<path>` | `docs/platform/<path>.md` |
| `https://code.claude.com/docs/en/<slug>` | `docs/claude-code/<slug>.md` |

### Step 4: Read Referenced Docs

Follow the references that are relevant to the question. Look for:
- How features interact
- What triggers or calls what
- Differences between similar features
- What restrictions apply
- Prerequisites or dependencies

### Step 5: Synthesize

Combine information from multiple docs to complete your objective. Don't just list features - understand and explain how they work together (where applicable).

## What to Look For

When tracing relationships, notice:

- **"works with"** / **"integrates with"** → feature connections
- **"unlike"** / **"differs from"** / **"vs"** → comparisons
- **"requires"** / **"depends on"** → prerequisites
- **"triggers"** / **"fires"** / **"runs when"** → event relationships
- **"can block"** / **"can allow"** → control flow
- **"defined in"** / **"configured in"** → where settings live

## Examples

### 1. "Create a hook that auto-approves file reads."

1. Start with `docs/claude-code/hooks.md`
2. Notice the references to settings files (`/en/settings`), and other relevant docs
3. Use the resolver script to find the settings documentation (`docs/claude-code/settings.md`), and any other relevant docs
4. Read the relevant docs to synthesize the relevant structure and patterns
5. Ensure you have any additional necessary context or requirements from the user based on your understanding of the documentation (e.g., specific MCP tools, file paths, etc.)
6. Create the hook following the patterns and structure you've synthesized

### 2. "What's the difference between Skills and Slash Commands?"

1. Read `docs/claude-code/skills.md`
2. Find references to slash commands, follow them
3. Read `docs/claude-code/slash-commands.md`
4. Find the "Skills vs slash commands" comparison section
5. Synthesize: invocation model, file structure, use cases
