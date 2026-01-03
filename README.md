# 📚 Docpistemic

> **Know what your docs know — and what they don't**

[![PyPI](https://img.shields.io/pypi/v/docpistemic)](https://pypi.org/project/docpistemic/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## What is Docpistemic?

Docpistemic applies **epistemic principles** to documentation assessment. Instead of just checking "does this function have a docstring?", it asks the harder question:

> **"Does the user know this feature exists?"**

It measures the gap between what your code *does* and what your docs *explain*.

## Installation

### PyPI (Recommended)
```bash
pip install docpistemic
```

### Docker
```bash
# Pull from DockerHub
docker pull nubaeon/docpistemic:latest

# Assess any GitHub repo
docker run --rm nubaeon/docpistemic assess https://github.com/user/repo

# Assess local project
docker run --rm -v $(pwd):/project nubaeon/docpistemic assess /project
```

### Homebrew (macOS/Linux)
```bash
brew tap nubaeon/tap
brew install docpistemic
```

### From Source
```bash
pip install git+https://github.com/Nubaeon/docpistemic.git
```

## Quick Start

```bash
# If installed via pip/homebrew
docpistemic assess .

# Assess current project
docpistemic assess .

# Assess a GitHub repo
docpistemic assess https://github.com/user/repo

# JSON output for CI
docpistemic assess . --output json

# Thorough multi-pass analysis (turtle depth)
docpistemic assess . --depth 3 --verbose

# Log findings to Empirica (if you have an active session)
docpistemic assess . --log
```

### Turtle Depth Levels

| Depth | Mode | Modules | Use Case |
|-------|------|---------|----------|
| 1 | Quick | 20 | Fast CI checks |
| 2 | Standard | 50 | Regular assessment |
| 3 | Thorough | 100 | Pre-release audit |

## Example Output

```
============================================================
📚 DOCPISTEMIC ASSESSMENT
============================================================

🌔 Overall Coverage: 72.5%
   Features: 58/80 documented

📊 Epistemic Assessment:
   know: 0.72
   uncertainty: 0.28
   → Documentation has notable gaps

📋 Category Coverage:
--------------------------------------------------
   🌕 CLI Commands: 85% (17/20)
   🌓 Core Modules: 60% (12/20)
   🌒 API Endpoints: 35% (7/20)
   🌑 Configuration: 10% (2/20)

💡 Recommendations:
   • Document API Endpoints: /api/users, /api/auth, /api/settings
   • Document Configuration: DATABASE_URL, API_KEY, DEBUG
============================================================
```

## How It Works

1. **Discovery** - Auto-detects CLI framework (argparse, click, typer), modules, classes, API routes
2. **Documentation Scan** - Reads README, docs/, docstrings
3. **Coverage Mapping** - Maps features → documentation
4. **Epistemic Assessment** - Calculates know/uncertainty vectors
5. **Recommendations** - Prioritizes what to document next

## Features

- 🔍 **Auto-discovery** - No config needed, works on any Python project
- 📊 **Epistemic vectors** - know/uncertainty scoring (powered by [Empirica](https://github.com/Nubaeon/empirica))
- 🌙 **Moon phases** - Visual coverage indicators
- 🎯 **Actionable recommendations** - Prioritized list of what to document
- 🔧 **CI-ready** - JSON output, exit codes for quality gates
- 🌐 **Remote repos** - Assess any public GitHub repo

## Supported Frameworks

| Category | Frameworks |
|----------|------------|
| CLI | argparse, click, typer, fire |
| Web | FastAPI, Flask, Django |
| Docs | README.md, docs/, docstrings |

## Philosophy

Traditional tools ask: *"Is there a docstring?"* (binary)

Docpistemic asks: *"Would a user discover this feature?"* (epistemic)

This shifts focus from **code coverage** to **user coverage**.

## Powered by Empirica

Docpistemic uses [Empirica](https://github.com/Nubaeon/empirica) for epistemic assessment — the same framework used by AI agents for genuine self-awareness.

### Why Empirica?

Empirica provides:
- **Epistemic vectors** (know/uncertainty) - calibrated self-assessment
- **Moon phase indicators** - visual coverage signals
- **Finding logging** - track documentation gaps over time
- **Session continuity** - maintain assessment history across sessions

### Empirica Integration

When you install docpistemic, Empirica is installed as a dependency. You can optionally:

```bash
# Initialize Empirica in your project
empirica project-init

# Create a session
empirica session-create --ai-id your-name

# Run docpistemic with logging to track findings
docpistemic assess . --log

# View your documentation debt over time
empirica finding-log --list
```

This lets you track documentation coverage improvements across releases.

## License

MIT License
