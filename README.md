# 📚 Docpistemic

> **Know what your docs know — and what they don't**

[![PyPI](https://img.shields.io/pypi/v/docpistemic)](https://pypi.org/project/docpistemic/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

> **0.2.0 (2026-05-07):** Coverage assessment now counts every public class
> AND every module-level function discovered (previously capped at top-20
> classes — most public functions were invisible). New `--strict` flag
> requires AST docstring presence (no substring-match fallback). See
> [CHANGELOG.md](CHANGELOG.md).

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
# Assess current project
docpistemic assess .

# Assess a GitHub repo
docpistemic assess https://github.com/user/repo

# JSON output for CI / compliance pipelines
docpistemic assess . --output json

# Strict mode — requires AST docstring presence, no substring-match fallback
docpistemic assess . --strict

# Show more undocumented items in the report
docpistemic assess . --depth 3 --verbose

# Log findings to Empirica (if you have an active session)
docpistemic assess . --log
```

### `--depth` controls the report, not the denominator

`--depth N` controls how many undocumented items are surfaced in the
report per category. The coverage denominator always counts every public
class and every public module-level function the discoverer found —
adding new functions to your project always moves the metric.

| Depth | Mode | Undocumented preview | Use Case |
|-------|------|----------------------|----------|
| 1 | Quick | top 20 per category | Fast CI checks |
| 2 | Standard | top 50 per category | Regular assessment |
| 3 | Thorough | top 100 per category | Pre-release audit |

### `--strict`: AST docstring as the primary signal

By default, an item is "documented" if its name appears anywhere in
README.md or `docs/*.md` OR if it has an AST docstring. Substring match
has false positives (a class named `Commit` matches every changelog
entry). `--strict` mode requires an AST docstring — more honest, more
conservative coverage %.

```bash
docpistemic assess .            # Permissive: substring or docstring
docpistemic assess . --strict   # Strict: docstring only
```

## Example Output

```
============================================================
📚 DOCPISTEMIC ASSESSMENT
============================================================

🌔 Overall Coverage: 94.6%
   Features: 1745/1844 documented

📊 Epistemic Assessment:
   know: 0.95
   uncertainty: 0.05
   → Documentation is comprehensive

📋 Category Coverage:
--------------------------------------------------
   🌕 CLI Commands: 99.6% (272/273)
   🌕 Classes: 93.8% (380/405)
   🌔 Public Functions: 93.7% (991/1058)
   🌕 API Endpoints: 92.3% (72/78)
   🌕 Configuration: 100% (30/30)

💡 Recommendations:
   • Document Public Functions: _resolve_artifact_by_id, _walk_graph, ...
   • Document Classes: _ReadOnlyDB, ...

Discovered: 273 CLI commands, 405 classes, 1058 public functions,
            78 API endpoints, 30 config options (strict)
============================================================
```

## How It Works

1. **Discovery** - Auto-detects CLI framework (argparse, click, typer), classes, public module-level functions, API routes (FastAPI / Flask / Django), config options
2. **Documentation Scan** - Reads README, docs/, docstrings
3. **Coverage Mapping** - Maps features → documentation (every class + function, no top-N cap)
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
