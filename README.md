# Claude Code Documentation Mirror

[![Last Update](https://img.shields.io/github/last-commit/brennacodes/claude-code-docs/main.svg?label=docs%20updated)](https://github.com/brennacodes/claude-code-docs/commits/main)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-blue)]()
[![Docs](https://img.shields.io/badge/docs-580+_pages-green)]()

Comprehensive local mirror of **Claude Code** and **Claude Platform API** documentation, automatically updated every 3 hours.

## What's Included

This tool provides local access to:

- ** Claude Code Documentation** (~48 docs) - CLI tool, hooks, MCP, integrations
  - Source: `code.claude.com/docs/en/*`
  - Stored in: `docs/claude-code/*.md`

- ** Claude Platform API Documentation** (~532 docs) - API reference, models, prompt engineering
  - Source: `platform.claude.com/docs/en/*`
  - Stored in: `docs/platform/*/*.md` (hierarchical structure)

**Total: 580+ documentation pages** with automatic updates and intelligent search across both sources.

## 🆕 Version 0.4.0 - Multi-Source Support

**New in this version:**
- **Dual Documentation Sources**: Now includes both Claude Code CLI docs AND Platform API docs
- **Smart Organization**: Hierarchical structure for platform docs, flat structure for code docs
- **Intelligent Search**: Automatically searches across both documentation sources
- **580+ Pages**: Comprehensive coverage of the entire Claude ecosystem
- **Enhanced Performance**: Optimized fetching and caching for large documentation sets

To update:
```bash
curl -fsSL https://raw.githubusercontent.com/brennacodes/claude-code-docs/main/install.sh | bash
```

## Why This Exists

- ** Faster access** - Reads from local files instead of fetching from web
- ** Automatic updates** - Stays current with the latest documentation (updated every 3 hours)
- ** Comprehensive coverage** - Both CLI tool AND API documentation in one place
- ** Better search** - Claude can explore and reference documentation more effectively
- ** Track changes** - See what changed in docs over time via git history
- ** Changelog access** - Quick access to official Claude Code release notes

## Platform Compatibility

- ✅ **macOS**: Fully supported (tested on macOS 12+)
- ✅ **Linux**: Fully supported (Ubuntu, Debian, Fedora, etc.)
- ⏳ **Windows**: Not yet supported - [contributions welcome](#contributing)!

### Prerequisites

This tool requires the following to be installed:
- **git** - For cloning and updating the repository (usually pre-installed)
- **jq** - For JSON processing in the auto-update hook (pre-installed on macOS; Linux users may need `apt install jq` or `yum install jq`)
- **curl** - For downloading the installation script (usually pre-installed)
- **Claude Code** - Obviously :)

## Installation

Run this single command:

```bash
curl -fsSL https://raw.githubusercontent.com/brennacodes/claude-code-docs/main/install.sh | bash
```

This will:
1. Install to `~/.claude-code-docs` (or migrate existing installation)
2. Create the `/docs` slash command to pass arguments to the tool and tell it where to find the docs
3. Set up a 'PreToolUse' 'Read' hook to enable automatic git pull when reading docs from the ~/.claude-code-docs`

**Note**: The command is `/docs (user)` - it will show in your command list with "(user)" after it to indicate it's a user-created command.

## Usage

The `/docs` command provides instant access to documentation with intelligent multi-source search.

### Basic Usage - Auto-Search Both Sources
```bash
# Searches both Claude Code and Platform docs automatically
/docs hooks              # Finds claude-code/hooks.md
/docs intro              # Finds platform/intro.md
/docs streaming          # Finds platform/build-with-claude/streaming.md
/docs memory             # Finds claude-code/memory.md
```

### Explicit Source Selection
```bash
# Claude Code (CLI tool) documentation
/docs claude-code/hooks
/docs claude-code/mcp
/docs claude-code/settings

# Platform API documentation
/docs platform/intro
/docs platform/about-claude/models/overview
/docs platform/build-with-claude/streaming
/docs platform/build-with-claude/prompt-engineering/overview
```

### Advanced Features
```bash
# Check sync status with GitHub
/docs -t                 # Show sync status
/docs -t hooks           # Check sync, then read hooks docs

# See what's new
/docs what's new         # Show recent documentation changes

# Access changelog
/docs changelog          # Official Claude Code release notes

# List all available docs
/docs                    # Shows both sources with counts

# Uninstall
/docs uninstall          # Get uninstall command
```

### Natural Language Queries
```bash
# Claude understands natural queries across both sources
/docs what environment variables exist?
/docs explain the differences between hooks and MCP
/docs how do I use prompt engineering with Claude?
/docs what models are available and how do I choose?
/docs find all mentions of authentication
```

### Customize Command Name

Prefer a different command name?

```bash
# Rename the command file
mv ~/.claude/commands/docs.md ~/.claude/commands/claude-docs.md

# Now use your custom name
/claude-docs hooks
/claude-docs intro
```

You can use any name: `/cdocs`, `/anthropic-docs`, etc.

## How Updates Work

The documentation stays current through multiple mechanisms:

### 1. **GitHub Actions (Automated)**
- Runs every 3 hours automatically
- Fetches from both `code.claude.com` and `platform.claude.com`
- Updates the repository when changes are detected
- View status: [GitHub Actions](https://github.com/brennacodes/claude-code-docs/actions)

### 2. **Local Auto-Update (When You Use `/docs`)**
- Checks for updates when you read documentation
- Pulls latest changes from GitHub if available
- You may see "🔄 Updating documentation..." when this happens

### 3. **Manual Update**
```bash
# Re-run installer
curl -fsSL https://raw.githubusercontent.com/brennacodes/claude-code-docs/main/install.sh | bash

# Or manually pull in the installation directory
cd ~/.claude-code-docs && git pull
```

### 4. **Custom Cron Job (Optional)**

If you want to customize the update schedule on your local machine:

```bash
# Edit your crontab
crontab -e

# Add this line to update every hour (adjust schedule as needed)
0 * * * * cd ~/.claude-code-docs && git pull --quiet origin main 2>&1 | logger -t claude-docs

# Or every 6 hours at minute 0
0 */6 * * * cd ~/.claude-code-docs && git pull --quiet origin main 2>&1 | logger -t claude-docs

# Or daily at 9 AM
0 9 * * * cd ~/.claude-code-docs && git pull --quiet origin main 2>&1 | logger -t claude-docs
```

**Note**: The GitHub Actions workflow already handles updates every 3 hours, so a local cron job is typically unnecessary unless you want more frequent checks or are working offline.

## Updating from Previous Versions

Regardless of which version you have installed, simply run:

```bash
curl -fsSL https://raw.githubusercontent.com/brennacodes/claude-code-docs/main/install.sh | bash
```

The installer will handle migration and updates automatically.

## Troubleshooting

### Command not found
If `/docs` returns "command not found":
1. Check if the command file exists: `ls ~/.claude/commands/docs.md`
2. Restart Claude Code to reload commands
3. Re-run the installation script

### Documentation not updating
If documentation seems outdated:
1. Run `/docs -t` to check sync status and force an update
2. Manually update: `cd ~/.claude-code-docs && git pull`
3. Check if GitHub Actions are running: [View Actions](https://github.com/brennacodes/claude-code-docs/actions)

### Installation errors
- **"git/jq/curl not found"**: Install the missing tool first
- **"Failed to clone repository"**: Check your internet connection
- **"Failed to update settings.json"**: Check file permissions on `~/.claude/settings.json`

## Uninstalling

To completely remove the docs integration:

```bash
/docs uninstall
```

Or run:
```bash
~/.claude-code-docs/uninstall.sh
```

See [UNINSTALL.md](UNINSTALL.md) for manual uninstall instructions.

## Security Notes

- The installer modifies `~/.claude/settings.json` to add an auto-update hook
- The hook only runs `git pull` when reading documentation files
- All operations are limited to the documentation directory
- No data is sent externally - everything is local
- **Repository Trust**: The installer clones from GitHub over HTTPS. For additional security, you can:
  - Fork the repository and install from your own fork
  - Clone manually and run the installer from the local directory
  - Review all code before installation

## Development & Testing

### Running Tests

Test the multi-source documentation fetching system:

#### Run the test suite (bash script)
```bash
bin/test
```

#### Or run directly with Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python3 test/test_fetch.py
```

The test script validates:
- ✅ Both documentation sources (Claude Code & Platform API)
- ✅ Sitemap discovery and parsing
- ✅ File naming and organization
- ✅ Content fetching and validation
- ✅ Hierarchical structure for platform docs

### Manual Testing

Fetch documentation manually:

#### Set up Python environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

#### Run the fetcher (downloads all 580+ docs)
```bash
python3 scripts/fetch_claude_docs.py
```

#### Check the results
```bash
ls -la docs/claude-code/
ls -la docs/platform/
```

> !NOTE: Full fetch takes ~5 minutes and downloads 580+ documentation pages.

## What's New

### v0.4.0 (Latest) - Multi-Source Documentation

**Major Changes:**
1. **Multi-Source Documentation Fetching**
   - Claude Code CLI docs: `code.claude.com` → `docs/claude-code/*.md` (49 pages)
   - Platform API docs: `platform.claude.com` → `docs/platform/*/*.md` (529 pages)
   - Total: **578+ documentation pages**

2. **Intelligent File Organization**
   - Claude Code: Flat structure (`claude-code/hooks.md`)
   - Platform: Hierarchical structure (`platform/about-claude/models/overview.md`)

3. **Smart Search**
   - Auto-searches both sources
   - Explicit source selection with prefixes (`claude-code/` or `platform/`)
   - Natural language queries work across both documentation sets

4. **Enhanced Testing**
   - Test suite in `test/` directory
   - Simple test runner: `bin/test`
   - Validates both documentation sources

**Technical Updates:**
- `scripts/fetch_claude_docs.py`: v3.0 → v4.0 (multi-source configuration)
- `scripts/claude-docs-helper.sh.template`: v0.3.3 → v0.4.0 (intelligent doc finding)
- `install.sh`: v0.3.3 → v0.4.0 (multi-source support)
- New: `bin/test` runner and `test/test_fetch.py` test suite

**File Structure:**
```
claude-code-docs/
├── bin/test                           # Test runner script
├── docs/
│   ├── claude-code/                   # Claude Code CLI docs (49 files)
│   │   ├── hooks.md
│   │   ├── mcp.md
│   │   └── ...
│   └── platform/                      # Platform API docs (529 files)
│       ├── intro.md
│       ├── about-claude/models/overview.md
│       └── build-with-claude/streaming.md
├── scripts/
│   ├── fetch_claude_docs.py          # v4.0 (multi-source)
│   └── claude-docs-helper.sh.template # v0.4.0
└── test/test_fetch.py                 # Test suite
```

### v0.3.3
- Added Claude Code changelog integration (`/docs changelog`)
- Fixed shell compatibility for macOS users (zsh/bash)
- Improved documentation and error messages
- Added platform compatibility badges

### v0.3.2
- Fixed automatic update functionality
- Improved handling of local repository changes
- Better error recovery during updates

## Contributing

**Contributions are welcome!** This is a community project and we'd love your help:

- 🪟 **Windows Support**: Want to help add Windows compatibility? [Fork the repository](https://github.com/brennacodes/claude-code-docs/fork) and submit a PR!
- 🐛 **Bug Reports**: Found something not working? [Open an issue](https://github.com/brennacodes/claude-code-docs/issues)
- 💡 **Feature Requests**: Have an idea? [Start a discussion](https://github.com/brennacodes/claude-code-docs/issues)
- 📝 **Documentation**: Help improve docs or add examples

You can also use Claude Code itself to help build features - just fork the repo and let Claude assist you!

## Known Issues

As this is an early beta, you might encounter some issues:
- Auto-updates may occasionally fail on some network configurations
- Some documentation links might not resolve correctly

If you find any issues not listed here, please [report them](https://github.com/brennacodes/claude-code-docs/issues)!

## License

Documentation content belongs to Anthropic.
This mirror tool is open source - contributions welcome!
