"""
Coverage Analyzer - Map discovered features to documentation.
"""

from dataclasses import dataclass, field
from pathlib import Path

from ..discovery.api_discovery import APIEndpoint
from ..discovery.cli_discovery import CLICommand
from ..discovery.config_discovery import ConfigOption
from ..discovery.module_discovery import DiscoveredModule


@dataclass
class CoverageResult:
    """Coverage result for a category."""
    category: str
    total: int
    documented: int
    items: list[str] = field(default_factory=list)
    undocumented: list[str] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return self.documented / self.total if self.total > 0 else 0.0

    @property
    def moon(self) -> str:
        """Moon phase indicator."""
        if self.coverage >= 0.85:
            return "🌕"
        elif self.coverage >= 0.70:
            return "🌔"
        elif self.coverage >= 0.50:
            return "🌓"
        elif self.coverage >= 0.30:
            return "🌒"
        else:
            return "🌑"


class CoverageAnalyzer:
    """Analyze documentation coverage for discovered features.

    Pass `strict=True` at construction to require AST docstring presence as
    the primary signal (instead of substring-match on docs content). Strict
    mode is more honest — substring match has false positives ("commit"
    matching every changelog entry, etc.) — but takes a stricter view of
    "documented" so coverage numbers will drop.
    """

    def __init__(self, root: Path, strict: bool = False):
        self.root = root
        self.docs_content = ""
        self.strict = strict

    def load_documentation(self):
        """Load all documentation content."""
        content_parts = []

        # README files
        for readme in ["README.md", "README.rst", "README.txt", "readme.md"]:
            readme_path = self.root / readme
            if readme_path.exists():
                try:
                    content_parts.append(readme_path.read_text())
                except Exception:
                    pass

        # docs/ directory
        docs_dir = self.root / "docs"
        if docs_dir.exists():
            for doc_file in docs_dir.rglob("*"):
                if doc_file.suffix in [".md", ".rst", ".txt"]:
                    try:
                        content_parts.append(doc_file.read_text())
                    except Exception:
                        pass

        # Docstrings from __init__.py files
        for init_file in self.root.rglob("__init__.py"):
            if ".venv" not in str(init_file) and "test" not in str(init_file).lower():
                try:
                    content_parts.append(init_file.read_text())
                except Exception:
                    pass

        self.docs_content = "\n".join(content_parts).lower()

    def _is_documented(self, term: str) -> bool:
        """Check if a term appears in documentation."""
        term_lower = term.lower()
        term_normalized = term_lower.replace("-", " ").replace("_", " ")

        # Check various forms
        return (
            term_lower in self.docs_content or
            term_normalized in self.docs_content or
            term.replace("-", "_").lower() in self.docs_content or
            term.replace("_", "-").lower() in self.docs_content
        )

    def analyze_cli_coverage(self, commands: list[CLICommand]) -> CoverageResult:
        """Analyze CLI command documentation coverage."""
        documented = []
        undocumented = []

        for cmd in commands:
            if self._is_documented(cmd.name):
                documented.append(cmd.name)
            else:
                undocumented.append(cmd.name)

        return CoverageResult(
            category="CLI Commands",
            total=len(commands),
            documented=len(documented),
            items=[c.name for c in commands],
            undocumented=undocumented
        )

    def analyze_module_coverage(
        self,
        modules: list[DiscoveredModule],
        category: str = "Core Modules",
    ) -> CoverageResult:
        """Analyze module/class/function documentation coverage.

        `category` lets the caller bucket the same analyzer into multiple
        categories (e.g. "Classes" vs "Public Functions") without inventing
        a new method per category.

        In strict mode: requires AST docstring presence (mod.docstring truthy).
        Non-strict (default): docstring OR name appears in docs content.
        """
        documented = []
        undocumented = []

        for mod in modules:
            if self.strict:
                is_doc = bool(mod.docstring)
            else:
                is_doc = self._is_documented(mod.name) or bool(mod.docstring)
            if is_doc:
                documented.append(mod.name)
            else:
                undocumented.append(mod.name)

        return CoverageResult(
            category=category,
            total=len(modules),
            documented=len(documented),
            items=[m.name for m in modules],
            undocumented=undocumented
        )

    def analyze_api_coverage(self, endpoints: list[APIEndpoint]) -> CoverageResult:
        """Analyze API endpoint documentation coverage."""
        documented = []
        undocumented = []

        for endpoint in endpoints:
            # Check path and function name
            path_documented = self._is_documented(endpoint.path)
            name_documented = endpoint.name and self._is_documented(endpoint.name)

            if path_documented or name_documented:
                documented.append(f"{endpoint.method} {endpoint.path}")
            else:
                undocumented.append(f"{endpoint.method} {endpoint.path}")

        return CoverageResult(
            category="API Endpoints",
            total=len(endpoints),
            documented=len(documented),
            items=[f"{e.method} {e.path}" for e in endpoints],
            undocumented=undocumented
        )

    def analyze_config_coverage(self, configs: list[ConfigOption]) -> CoverageResult:
        """Analyze configuration documentation coverage."""
        documented = []
        undocumented = []

        for config in configs:
            if self._is_documented(config.name):
                documented.append(config.name)
            else:
                undocumented.append(config.name)

        return CoverageResult(
            category="Configuration",
            total=len(configs),
            documented=len(documented),
            items=[c.name for c in configs],
            undocumented=undocumented
        )
