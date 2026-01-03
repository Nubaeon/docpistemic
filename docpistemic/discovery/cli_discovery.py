"""
CLI Discovery - Detect CLI commands from various frameworks.

Supports:
- argparse: ArgumentParser, add_subparsers
- click: @click.command, @click.group
- typer: typer.Typer(), app.command()
- fire: fire.Fire()
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CLICommand:
    """Discovered CLI command."""
    name: str
    framework: str  # argparse, click, typer, fire
    file: str
    line: int
    help_text: str = ""


class CLIDiscovery:
    """Discover CLI commands from Python projects."""

    def __init__(self, root: Path):
        self.root = root
        self.commands: list[CLICommand] = []

    def discover(self) -> list[CLICommand]:
        """Run all CLI discovery methods."""
        for py_file in self.root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                content = py_file.read_text()
                self._discover_argparse(py_file, content)
                self._discover_click(py_file, content)
                self._discover_typer(py_file, content)
                self._discover_fire(py_file, content)
            except Exception:
                pass

        return self.commands

    def _should_skip(self, path: Path) -> bool:
        """Skip test files, venvs, etc."""
        skip_patterns = [
            "__pycache__", ".venv", "venv", "node_modules",
            ".git", ".tox", ".eggs", "build", "dist",
            "test_", "_test.py", "tests/", "conftest.py"
        ]
        path_str = str(path)
        return any(p in path_str for p in skip_patterns)

    def _discover_argparse(self, file: Path, content: str):
        """Discover argparse subcommands."""
        # Find add_parser calls: subparsers.add_parser('command-name', ...)
        pattern = r"add_parser\s*\(\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            self.commands.append(CLICommand(
                name=match.group(1),
                framework="argparse",
                file=str(file.relative_to(self.root)),
                line=line_num
            ))

        # Also find ArgumentParser with prog=
        prog_pattern = r"ArgumentParser\s*\([^)]*prog\s*=\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(prog_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            self.commands.append(CLICommand(
                name=match.group(1),
                framework="argparse",
                file=str(file.relative_to(self.root)),
                line=line_num
            ))

    def _discover_click(self, file: Path, content: str):
        """Discover click commands."""
        # @click.command() or @app.command()
        # Pattern: @something.command(name='cmd') or @something.command()

        # Find @click.command or @app.command decorators
        cmd_pattern = r"@(\w+)\.command\s*\("
        for match in re.finditer(cmd_pattern, content):
            decorator_obj = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Look for explicit name= parameter with quotes
            rest = content[match.end():match.end()+200]
            name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", rest)

            if name_match:
                name = name_match.group(1)
            else:
                # Get the function name from def statement
                func_match = re.search(r"\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\(", rest)
                if func_match:
                    name = func_match.group(1).replace("_", "-")
                else:
                    continue  # Skip if we can't find a valid command name

            # Filter out false positives (parameters, not command names)
            if "=" in name or name.startswith("_"):
                continue

            self.commands.append(CLICommand(
                name=name,
                framework="click",
                file=str(file.relative_to(self.root)),
                line=line_num
            ))

        # @click.group()
        group_pattern = r"@click\.group\s*\("
        for match in re.finditer(group_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            func_match = re.search(r"def\s+(\w+)\s*\(", content[match.end():match.end()+100])
            name = func_match.group(1) if func_match else "cli"
            self.commands.append(CLICommand(
                name=name,
                framework="click",
                file=str(file.relative_to(self.root)),
                line=line_num
            ))

    def _discover_typer(self, file: Path, content: str):
        """Discover typer commands."""
        # @app.command() with typer
        if "typer" not in content.lower():
            return

        # Find app = typer.Typer() pattern
        typer_pattern = r"(\w+)\s*=\s*typer\.Typer\s*\("
        app_names = re.findall(typer_pattern, content)

        for app_name in app_names:
            # Find @app.command() decorators
            cmd_pattern = rf"@{app_name}\.command\s*\(\s*(?:['\"]([^'\"]+)['\"])?\s*\)"
            for match in re.finditer(cmd_pattern, content):
                name = match.group(1) if match.group(1) else "unknown"
                line_num = content[:match.start()].count('\n') + 1

                # Try to get function name
                if name == "unknown":
                    func_match = re.search(r"def\s+(\w+)\s*\(", content[match.end():match.end()+100])
                    if func_match:
                        name = func_match.group(1).replace("_", "-")

                self.commands.append(CLICommand(
                    name=name,
                    framework="typer",
                    file=str(file.relative_to(self.root)),
                    line=line_num
                ))

    def _discover_fire(self, file: Path, content: str):
        """Discover fire CLI commands."""
        if "fire.Fire" not in content:
            return

        # fire.Fire(ClassName) or fire.Fire(function)
        fire_pattern = r"fire\.Fire\s*\(\s*(\w+)\s*\)"
        for match in re.finditer(fire_pattern, content):
            target = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # If it's a class, find its methods
            class_pattern = rf"class\s+{target}\s*.*?:"
            if re.search(class_pattern, content):
                # Find methods in this class
                method_pattern = r"def\s+(\w+)\s*\(self"
                for method_match in re.finditer(method_pattern, content):
                    method_name = method_match.group(1)
                    if not method_name.startswith("_"):
                        self.commands.append(CLICommand(
                            name=method_name.replace("_", "-"),
                            framework="fire",
                            file=str(file.relative_to(self.root)),
                            line=line_num
                        ))
            else:
                # It's a function
                self.commands.append(CLICommand(
                    name=target.replace("_", "-"),
                    framework="fire",
                    file=str(file.relative_to(self.root)),
                    line=line_num
                ))
