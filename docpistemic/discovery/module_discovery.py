"""
Module Discovery - Detect classes, functions, and key exports.

Focuses on user-facing modules that should be documented.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DiscoveredModule:
    """A discovered class or function."""
    name: str
    type: str  # class, function, constant
    file: str
    line: int
    docstring: str = ""
    is_public: bool = True


class ModuleDiscovery:
    """Discover public modules, classes, and functions."""

    def __init__(self, root: Path):
        self.root = root
        self.modules: list[DiscoveredModule] = []

    def discover(self) -> list[DiscoveredModule]:
        """Run module discovery."""
        # Find the main package directory
        package_dir = self._find_package_dir()
        if not package_dir:
            return self.modules

        for py_file in package_dir.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                self._parse_file(py_file)
            except Exception:
                pass

        return self.modules

    def _find_package_dir(self) -> Path | None:
        """Find the main Python package directory."""
        # Look for src/ pattern
        src_dir = self.root / "src"
        if src_dir.exists():
            for item in src_dir.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    return item

        # Look for package with same name as project
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                pkg_name = match.group(1).replace("-", "_")
                pkg_dir = self.root / pkg_name
                if pkg_dir.exists() and (pkg_dir / "__init__.py").exists():
                    return pkg_dir

        # Look for any directory with __init__.py
        for item in self.root.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                if item.name not in ["tests", "test", "docs", "examples"]:
                    return item

        return None

    def _should_skip(self, path: Path) -> bool:
        """Skip test files, internal modules, etc.

        Match patterns against directory-name parts and the file basename
        rather than the full path string. Prevents false positives like
        pytest's `/tmp/pytest-of-USER/test_X/` parent directories triggering
        a skip on real package files inside.
        """
        # Directory-name skips (anywhere in the path)
        skip_dirs = {"__pycache__", ".venv", "venv", "tests", "migrations"}
        if any(part in skip_dirs for part in path.parts):
            return True
        # Filename skips (basename only)
        name = path.name
        if name.startswith("test_") or name.endswith("_test.py") or name.startswith("conftest"):
            return True
        return False

    def _parse_file(self, file: Path):
        """Parse a Python file for classes and functions."""
        content = file.read_text()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    self.modules.append(DiscoveredModule(
                        name=node.name,
                        type="class",
                        file=str(file.relative_to(self.root)),
                        line=node.lineno,
                        docstring=ast.get_docstring(node) or "",
                        is_public=True
                    ))

            elif isinstance(node, ast.FunctionDef):
                # Only top-level functions (not methods)
                if not node.name.startswith("_"):
                    # Check if it's a module-level function
                    if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                        self.modules.append(DiscoveredModule(
                            name=node.name,
                            type="function",
                            file=str(file.relative_to(self.root)),
                            line=node.lineno,
                            docstring=ast.get_docstring(node) or "",
                            is_public=True
                        ))

        # Find __all__ exports
        all_pattern = r"__all__\s*=\s*\[([^\]]+)\]"
        match = re.search(all_pattern, content)
        if match:
            exports = re.findall(r"['\"](\w+)['\"]", match.group(1))
            # Mark non-exported items as not public
            for module in self.modules:
                if module.file == str(file.relative_to(self.root)):
                    if exports and module.name not in exports:
                        module.is_public = False

    def get_public_modules(self) -> list[DiscoveredModule]:
        """Return only public modules."""
        return [m for m in self.modules if m.is_public]

    def get_key_classes(self, limit: int = 20) -> list[DiscoveredModule]:
        """Return key classes that should be documented."""
        classes = [m for m in self.modules if m.type == "class" and m.is_public]
        # Prioritize by name (longer names often more important)
        # and by having docstrings (indicates importance)
        classes.sort(key=lambda x: (bool(x.docstring), len(x.name)), reverse=True)
        return classes[:limit]
