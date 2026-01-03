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

### Why "Turtle Depth"?

The phrase **"turtles all the way down"** comes from a famous anecdote about infinite regress:

> A scientist finishes a lecture on cosmology. An elderly woman in the audience objects: "What you have told us is rubbish. The world is really a flat plate supported on the back of a giant tortoise."
>
> The scientist asks, "And what is the tortoise standing on?"
>
> The woman replies: "You're very clever, young man, but it's turtles all the way down!"

The story illustrates a fundamental problem: *any explanation requires a further explanation*. In documentation, this manifests as a recursive question:

- Does feature X have docs? → Do the docs explain the context needed to understand X? → Do *those* docs explain their prerequisites? → ...

Traditional tools stop at the first turtle. Docpistemic goes deeper.

### Epistemic vs Binary Coverage

| Approach | Question | Answer |
|----------|----------|--------|
| Traditional | "Is there a docstring?" | Yes/No |
| Docpistemic | "Would a user discover this feature?" | know/uncertainty vectors |

This shifts focus from **code coverage** to **user coverage** — from what the code *says* to what the user *knows*.

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
