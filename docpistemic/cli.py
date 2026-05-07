"""
Docpistemic CLI - Epistemic documentation coverage assessment.

Usage:
    docpistemic assess .                    # Assess current project
    docpistemic assess /path/to/project     # Assess local project
    docpistemic assess https://github.com/user/repo  # Assess remote repo
    docpistemic assess . --output json      # JSON output for CI
    docpistemic assess . --depth 3          # Multi-pass turtle assessment
"""

import json
import shutil
import tempfile
from pathlib import Path

import typer
from rich.console import Console

# Empirica integration - uses signaling for moon phases and finding logging
try:
    from empirica.core.signaling import DriftLevel
    from empirica.data.session_database import SessionDatabase
    EMPIRICA_AVAILABLE = True
except ImportError:
    EMPIRICA_AVAILABLE = False

from .assessment import CoverageAnalyzer, EpistemicAssessor
from .discovery import APIDiscovery, CLIDiscovery, ConfigDiscovery, ModuleDiscovery

app = typer.Typer(
    name="docpistemic",
    help="Epistemic documentation coverage assessment - know what your docs know",
    no_args_is_help=True
)
console = Console()


def clone_repo(url: str) -> Path:
    """Clone a git repository to a temp directory."""
    try:
        import git
    except ImportError:
        console.print("[red]GitPython not installed. Run: pip install gitpython[/red]")
        raise typer.Exit(1)

    temp_dir = Path(tempfile.mkdtemp(prefix="docpistemic_"))
    console.print(f"[dim]Cloning {url}...[/dim]")

    try:
        git.Repo.clone_from(url, temp_dir, depth=1)
    except Exception as e:
        console.print(f"[red]Failed to clone: {e}[/red]")
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise typer.Exit(1)

    return temp_dir


@app.command()
def assess(
    target: str = typer.Argument(..., help="Path to project or GitHub URL"),
    output: str = typer.Option("human", "--output", "-o", help="Output format: human or json"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    depth: int = typer.Option(1, "--depth", "-d", help="Turtle depth: 1=quick, 2=standard, 3=thorough"),
    log_findings: bool = typer.Option(False, "--log", help="Log findings to Empirica (requires active session)"),
    strict: bool = typer.Option(False, "--strict",
                                  help="Require AST docstring presence (no substring-match fallback). More honest, more conservative."),
):
    """
    Assess documentation coverage for a project.

    The --depth flag controls how thoroughly we turtle through the codebase:
    - depth=1: Quick scan (default) - main package only
    - depth=2: Standard - includes nested modules
    - depth=3: Thorough - full recursive analysis with multiple passes

    Examples:
        docpistemic assess .
        docpistemic assess /path/to/project
        docpistemic assess https://github.com/user/repo
        docpistemic assess . --depth 3 --verbose
    """
    # Determine if target is URL or path
    is_remote = target.startswith("http://") or target.startswith("https://")
    cleanup_needed = False

    if is_remote:
        project_path = clone_repo(target)
        cleanup_needed = True
    else:
        project_path = Path(target).resolve()
        if not project_path.exists():
            console.print(f"[red]Path not found: {target}[/red]")
            raise typer.Exit(1)

    try:
        result = run_assessment(project_path, verbose, depth, strict=strict)

        if output == "json":
            print(json.dumps(result, indent=2))
        else:
            print_human_output(result, verbose, depth)

        # Log findings to Empirica if requested
        if log_findings and EMPIRICA_AVAILABLE:
            log_to_empirica(result)

    finally:
        if cleanup_needed:
            shutil.rmtree(project_path, ignore_errors=True)


def log_to_empirica(result: dict):
    """Log assessment findings to Empirica."""
    try:
        import subprocess
        epistemic = result["epistemic"]

        # Log the overall finding
        finding = (
            f"Docpistemic assessment: {epistemic['overall_coverage']}% coverage, "
            f"know={epistemic['know']}, uncertainty={epistemic['uncertainty']}"
        )

        # Calculate impact based on coverage gaps
        impact = 0.5 if epistemic["overall_coverage"] >= 70 else 0.7

        subprocess.run(
            ["empirica", "finding-log", "--finding", finding, "--impact", str(impact)],
            capture_output=True,
            timeout=5
        )

        # Log undocumented items as unknowns
        for rec in epistemic.get("recommendations", [])[:3]:
            subprocess.run(
                ["empirica", "unknown-log", "--unknown", rec],
                capture_output=True,
                timeout=5
            )

        console.print("[dim]Findings logged to Empirica[/dim]")
    except Exception as e:
        console.print(f"[dim]Could not log to Empirica: {e}[/dim]")


def run_assessment(
    root: Path,
    verbose: bool = False,
    depth: int = 1,
    strict: bool = False,
) -> dict:
    """
    Run the full assessment pipeline.

    Depth controls how many undocumented items are surfaced in the report
    (display cap, NOT a coverage-denominator cap):
    - 1: Quick (top 20 undocumented per category)
    - 2: Standard (top 50)
    - 3: Thorough (top 100)

    The denominator counts EVERY public class and EVERY public module-level
    function the discoverer found, not a heuristic-curated subset. (v0.2.0
    fix: prior versions capped at top-20 classes only — see CHANGELOG.)

    `strict=True` requires AST docstring presence as the primary signal
    instead of substring-match on docs. More honest, more conservative.
    """
    undoc_display_limits = {1: 20, 2: 50, 3: 100}
    undoc_display_limit = undoc_display_limits.get(depth, 20)

    # Discovery phase
    if verbose:
        console.print(f"[dim]Discovering features (depth={depth})...[/dim]")

    cli_discovery = CLIDiscovery(root)
    cli_commands = cli_discovery.discover()

    module_discovery = ModuleDiscovery(root)
    module_discovery.discover()
    public_modules = module_discovery.get_public_modules()
    classes = [m for m in public_modules if m.type == "class"]
    functions = [m for m in public_modules if m.type == "function"]

    api_discovery = APIDiscovery(root)
    endpoints = api_discovery.discover()

    config_discovery = ConfigDiscovery(root)
    configs = config_discovery.discover()

    # Coverage analysis phase
    if verbose:
        console.print("[dim]Analyzing documentation coverage...[/dim]")
        if strict:
            console.print("[dim]Strict mode: requires AST docstring presence[/dim]")

    analyzer = CoverageAnalyzer(root, strict=strict)
    analyzer.load_documentation()

    cli_coverage = analyzer.analyze_cli_coverage(cli_commands)
    class_coverage = analyzer.analyze_module_coverage(classes, category="Classes")
    function_coverage = analyzer.analyze_module_coverage(functions, category="Public Functions")
    api_coverage = analyzer.analyze_api_coverage(endpoints)
    config_coverage = analyzer.analyze_config_coverage(configs)

    # Epistemic assessment phase
    assessor = EpistemicAssessor()
    assessor.add_result(cli_coverage)
    assessor.add_result(class_coverage)
    assessor.add_result(function_coverage)
    assessor.add_result(api_coverage)
    assessor.add_result(config_coverage)

    assessment = assessor.assess()

    # Build result
    categories = []
    for result in [cli_coverage, class_coverage, function_coverage, api_coverage, config_coverage]:
        if result.total > 0:
            categories.append({
                "name": result.category,
                "total": result.total,
                "documented": result.documented,
                "coverage": round(result.coverage * 100, 1),
                "moon": result.moon,
                "undocumented": result.undocumented[:undoc_display_limit]
            })

    return {
        "project": str(root.name),
        "epistemic": assessment.to_dict(),
        "categories": categories,
        "strict": strict,
        "discovery": {
            "cli_commands": len(cli_commands),
            "classes": len(classes),
            "public_functions": len(functions),
            "api_endpoints": len(endpoints),
            "config_options": len(configs)
        }
    }


def print_human_output(result: dict, verbose: bool, depth: int = 1):
    """Print human-readable output."""
    epistemic = result["epistemic"]
    categories = result["categories"]

    depth_labels = {1: "Quick", 2: "Standard", 3: "Thorough"}
    depth_label = depth_labels.get(depth, "Quick")

    console.print()
    console.print("=" * 60)
    console.print(f"[bold]📚 DOCPISTEMIC ASSESSMENT[/bold] [dim]({depth_label})[/dim]")
    console.print("=" * 60)

    # Overall score
    console.print(f"\n{epistemic['moon']} [bold]Overall Coverage: {epistemic['overall_coverage']}%[/bold]")
    console.print(f"   Features: {epistemic['documented_features']}/{epistemic['total_features']} documented")

    # Epistemic assessment
    console.print("\n[bold]📊 Epistemic Assessment:[/bold]")
    console.print(f"   know: {epistemic['know']}")
    console.print(f"   uncertainty: {epistemic['uncertainty']}")
    console.print(f"   → {epistemic['assessment']}")

    # Category breakdown
    if categories:
        console.print("\n[bold]📋 Category Coverage:[/bold]")
        console.print("-" * 50)

        for cat in categories:
            status = "✅" if cat["coverage"] >= 70 else "⚠️" if cat["coverage"] >= 40 else "❌"
            console.print(f"   {cat['moon']} {cat['name']}: {cat['coverage']}% ({cat['documented']}/{cat['total']})")

            if verbose and cat["undocumented"]:
                for item in cat["undocumented"][:5]:
                    console.print(f"      └─ Missing: {item}")

    # Recommendations
    if epistemic["recommendations"]:
        console.print("\n[bold]💡 Recommendations:[/bold]")
        for rec in epistemic["recommendations"]:
            console.print(f"   • {rec}")

    # Discovery stats
    discovery = result["discovery"]
    console.print(
        f"\n[dim]Discovered: {discovery['cli_commands']} CLI commands, "
        f"{discovery['classes']} classes, {discovery['public_functions']} public functions, "
        f"{discovery['api_endpoints']} API endpoints, {discovery['config_options']} config options"
        f"{' (strict)' if result.get('strict') else ''}[/dim]"
    )

    console.print()
    console.print("=" * 60)


@app.command()
def explain(
    target: str = typer.Argument(".", help="Path to project (default: current directory)"),
    topic: str | None = typer.Option(None, "--topic", "-t", help="Topic to explain"),
    question: str | None = typer.Option(None, "--question", "-q", help="Question to answer"),
    output: str = typer.Option("human", "--output", "-o", help="Output format: human or json"),
):
    """
    Get focused explanation of project documentation topics.

    Searches project docs for relevant information about a topic or question.
    Returns relevant sections with sources and suggests further learning.

    Examples:
        docpistemic explain . --topic "authentication"
        docpistemic explain . --question "How do I configure logging?"
        docpistemic explain /path/to/project --topic "api" --output json
    """
    if not topic and not question:
        console.print("[red]Please provide --topic or --question[/red]")
        raise typer.Exit(1)

    project_path = Path(target).resolve()
    if not project_path.exists():
        console.print(f"[red]Path not found: {target}[/red]")
        raise typer.Exit(1)

    agent = DocsExplainAgent(project_path)
    result = agent.explain(topic=topic, question=question)

    if output == "json":
        print(json.dumps(result, indent=2))
    else:
        print_explain_output(result)


class DocsExplainAgent:
    """
    Generic documentation explain agent.

    Retrieves focused information from any project's docs.
    """

    # Common topic aliases
    TOPIC_ALIASES = {
        "auth": ["authentication", "auth", "login", "oauth", "jwt", "token"],
        "api": ["api", "endpoint", "route", "rest", "graphql"],
        "config": ["config", "configuration", "settings", "environment", "env"],
        "install": ["install", "installation", "setup", "getting started", "quickstart"],
        "test": ["test", "testing", "pytest", "unittest", "coverage"],
        "deploy": ["deploy", "deployment", "docker", "kubernetes", "ci/cd"],
        "database": ["database", "db", "sql", "postgres", "mysql", "migration"],
        "logging": ["logging", "log", "debug", "error", "trace"],
    }

    def __init__(self, project_root: Path):
        self.root = project_root
        self.docs_dir = project_root / "docs"
        self._docs_cache: dict = {}

    def _load_docs(self) -> dict:
        """Load all docs into memory."""
        if self._docs_cache:
            return self._docs_cache

        # Look for docs in common locations
        doc_locations = [
            self.root / "docs",
            self.root / "doc",
            self.root / "documentation",
        ]

        # Also check README
        readme = self.root / "README.md"
        if readme.exists():
            try:
                self._docs_cache["README.md"] = readme.read_text()
            except Exception:
                pass

        # Load from doc directories
        for docs_dir in doc_locations:
            if docs_dir.exists():
                for md_file in docs_dir.rglob("*.md"):
                    if "_archive" not in str(md_file) and "node_modules" not in str(md_file):
                        try:
                            rel_path = str(md_file.relative_to(self.root))
                            self._docs_cache[rel_path] = md_file.read_text()
                        except Exception:
                            pass

        return self._docs_cache

    def _expand_topic(self, topic: str) -> list:
        """Expand topic to related keywords."""
        topic_lower = topic.lower()

        # Extract meaningful words from questions/phrases
        # Remove common question words and stop words
        stop_words = {
            "how", "do", "i", "can", "what", "is", "the", "a", "an", "to",
            "where", "when", "why", "should", "could", "would", "does",
            "are", "in", "for", "of", "my", "your", "this", "that", "it"
        }

        # Split into words and filter
        words = [w.strip("?.,!") for w in topic_lower.split()]
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]

        # Start with meaningful words as keywords
        keywords = meaningful_words if meaningful_words else [topic_lower]

        # Expand via aliases
        for alias_key, alias_keywords in self.TOPIC_ALIASES.items():
            for word in meaningful_words:
                if word in alias_key or alias_key in word or any(kw.startswith(word) or word.startswith(kw) for kw in alias_keywords):
                    keywords.extend(alias_keywords)
                    break

        return list(set(keywords))

    def _score_doc(self, content: str, keywords: list) -> float:
        """Score document by keyword relevance."""
        content_lower = content.lower()
        score = 0.0

        for kw in keywords:
            count = content_lower.count(kw)
            if count > 0:
                score += min(count, 10) * 0.1
            if f"# {kw}" in content_lower or f"## {kw}" in content_lower:
                score += 0.5

        return score

    def _extract_sections(self, content: str, keywords: list, max_sections: int = 3) -> list:
        """Extract relevant sections from document."""
        sections = []
        lines = content.split('\n')
        current_section = []
        current_header = ""

        for line in lines:
            if line.startswith('#'):
                if current_section and current_header:
                    sections.append((current_header, '\n'.join(current_section)))
                current_header = line
                current_section = []
            else:
                current_section.append(line)

        if current_section and current_header:
            sections.append((current_header, '\n'.join(current_section)))

        scored = []
        for header, body in sections:
            combined = f"{header}\n{body}"
            score = self._score_doc(combined, keywords)
            if score > 0:
                scored.append((score, header, body[:500]))

        scored.sort(reverse=True)
        return [(h, b) for _, h, b in scored[:max_sections]]

    def explain(self, topic: str = None, question: str = None) -> dict:
        """Get focused explanation."""
        docs = self._load_docs()

        if not docs:
            return {
                "ok": False,
                "error": "No documentation found in project",
                "hint": "Ensure project has docs/, README.md, or similar"
            }

        search_text = topic or question or ""
        keywords = self._expand_topic(search_text)

        scored_docs = []
        for path, content in docs.items():
            score = self._score_doc(content, keywords)
            if score > 0.1:
                scored_docs.append((score, path, content))

        scored_docs.sort(reverse=True)

        if not scored_docs:
            return {
                "ok": True,
                "query": search_text,
                "explanation": f"No documentation found for '{search_text}'",
                "sources": [],
                "suggestions": list(self.TOPIC_ALIASES.keys())
            }

        top_docs = scored_docs[:5]
        all_sections = []
        sources = []

        for score, path, content in top_docs:
            sections = self._extract_sections(content, keywords)
            for header, body in sections:
                all_sections.append(f"**{path}** {header}\n{body.strip()}")
            sources.append({"path": path, "relevance": round(score, 2)})

        if question:
            explanation_header = f"**Answering:** {question}\n\n"
        else:
            explanation_header = f"**Topic:** {topic}\n\n"

        explanation = explanation_header + "\n\n---\n\n".join(all_sections[:5])

        return {
            "ok": True,
            "query": search_text,
            "explanation": explanation,
            "sources": sources,
            "related_topics": [k for k in self.TOPIC_ALIASES.keys() if k not in search_text.lower()][:5]
        }


def print_explain_output(result: dict):
    """Print human-readable explain output."""
    console.print()
    console.print("=" * 60)
    console.print("[bold]📖 DOCPISTEMIC EXPLAIN[/bold]")
    console.print("=" * 60)

    if not result.get("ok"):
        console.print(f"\n[red]❌ {result.get('error', 'Unknown error')}[/red]")
        if result.get("hint"):
            console.print(f"[dim]{result['hint']}[/dim]")
        return

    console.print(f"\n[bold]🔍 Query:[/bold] {result.get('query', 'N/A')}")
    console.print("-" * 60)

    explanation = result.get("explanation", "No explanation available")
    if len(explanation) > 2000:
        explanation = explanation[:2000] + "\n\n... (use --output json for full content)"
    console.print(explanation)

    console.print("-" * 60)

    sources = result.get("sources", [])
    if sources:
        console.print("\n[bold]📚 Sources:[/bold]")
        for src in sources[:5]:
            console.print(f"   • {src['path']} (relevance: {src['relevance']})")

    related = result.get("related_topics", [])
    if related:
        console.print(f"\n[bold]🔗 Related:[/bold] {', '.join(related)}")

    console.print()
    console.print("=" * 60)


@app.command()
def version():
    """Show version information."""
    from . import __version__
    console.print(f"docpistemic v{__version__}")
    console.print("[dim]Powered by Empirica - https://github.com/Nubaeon/empirica[/dim]")


if __name__ == "__main__":
    app()
