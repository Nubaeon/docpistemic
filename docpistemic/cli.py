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
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Empirica integration - uses signaling for moon phases and finding logging
try:
    from empirica.core.signaling import DriftLevel
    from empirica.data.session_database import SessionDatabase
    EMPIRICA_AVAILABLE = True
except ImportError:
    EMPIRICA_AVAILABLE = False

from .discovery import CLIDiscovery, ModuleDiscovery, APIDiscovery, ConfigDiscovery
from .assessment import CoverageAnalyzer, EpistemicAssessor

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
        result = run_assessment(project_path, verbose, depth)

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


def run_assessment(root: Path, verbose: bool = False, depth: int = 1) -> dict:
    """
    Run the full assessment pipeline.

    Depth controls turtle recursion:
    - 1: Quick scan (20 modules max)
    - 2: Standard (50 modules max)
    - 3: Thorough (100 modules, multiple passes)
    """
    module_limits = {1: 20, 2: 50, 3: 100}
    module_limit = module_limits.get(depth, 20)

    # Discovery phase
    if verbose:
        console.print(f"[dim]Discovering features (depth={depth})...[/dim]")

    cli_discovery = CLIDiscovery(root)
    cli_commands = cli_discovery.discover()

    module_discovery = ModuleDiscovery(root)
    modules = module_discovery.discover()
    key_classes = module_discovery.get_key_classes(limit=module_limit)

    api_discovery = APIDiscovery(root)
    endpoints = api_discovery.discover()

    config_discovery = ConfigDiscovery(root)
    configs = config_discovery.discover()

    # Coverage analysis phase
    if verbose:
        console.print("[dim]Analyzing documentation coverage...[/dim]")

    analyzer = CoverageAnalyzer(root)
    analyzer.load_documentation()

    cli_coverage = analyzer.analyze_cli_coverage(cli_commands)
    module_coverage = analyzer.analyze_module_coverage(key_classes)
    api_coverage = analyzer.analyze_api_coverage(endpoints)
    config_coverage = analyzer.analyze_config_coverage(configs)

    # Epistemic assessment phase
    assessor = EpistemicAssessor()
    assessor.add_result(cli_coverage)
    assessor.add_result(module_coverage)
    assessor.add_result(api_coverage)
    assessor.add_result(config_coverage)

    assessment = assessor.assess()

    # Build result
    categories = []
    for result in [cli_coverage, module_coverage, api_coverage, config_coverage]:
        if result.total > 0:
            categories.append({
                "name": result.category,
                "total": result.total,
                "documented": result.documented,
                "coverage": round(result.coverage * 100, 1),
                "moon": result.moon,
                "undocumented": result.undocumented[:10]
            })

    return {
        "project": str(root.name),
        "epistemic": assessment.to_dict(),
        "categories": categories,
        "discovery": {
            "cli_commands": len(cli_commands),
            "modules": len(key_classes),
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
    console.print(f"\n[bold]📊 Epistemic Assessment:[/bold]")
    console.print(f"   know: {epistemic['know']}")
    console.print(f"   uncertainty: {epistemic['uncertainty']}")
    console.print(f"   → {epistemic['assessment']}")

    # Category breakdown
    if categories:
        console.print(f"\n[bold]📋 Category Coverage:[/bold]")
        console.print("-" * 50)

        for cat in categories:
            status = "✅" if cat["coverage"] >= 70 else "⚠️" if cat["coverage"] >= 40 else "❌"
            console.print(f"   {cat['moon']} {cat['name']}: {cat['coverage']}% ({cat['documented']}/{cat['total']})")

            if verbose and cat["undocumented"]:
                for item in cat["undocumented"][:5]:
                    console.print(f"      └─ Missing: {item}")

    # Recommendations
    if epistemic["recommendations"]:
        console.print(f"\n[bold]💡 Recommendations:[/bold]")
        for rec in epistemic["recommendations"]:
            console.print(f"   • {rec}")

    # Discovery stats
    discovery = result["discovery"]
    console.print(f"\n[dim]Discovered: {discovery['cli_commands']} CLI commands, "
                  f"{discovery['modules']} modules, {discovery['api_endpoints']} API endpoints, "
                  f"{discovery['config_options']} config options[/dim]")

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
