"""
Config Discovery - Detect configuration options.

Finds:
- Environment variables: os.getenv, os.environ
- Pydantic Settings
- Django settings
- Config file references
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConfigOption:
    """Discovered configuration option."""
    name: str
    type: str  # env_var, setting, config_file
    file: str
    line: int
    default: str = ""
    required: bool = False


class ConfigDiscovery:
    """Discover configuration options from Python projects."""

    def __init__(self, root: Path):
        self.root = root
        self.configs: list[ConfigOption] = []

    def discover(self) -> list[ConfigOption]:
        """Run config discovery."""
        for py_file in self.root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                content = py_file.read_text()
                self._discover_env_vars(py_file, content)
                self._discover_pydantic_settings(py_file, content)
                self._discover_django_settings(py_file, content)
            except Exception:
                pass

        # Deduplicate by name
        seen = set()
        unique = []
        for config in self.configs:
            if config.name not in seen:
                seen.add(config.name)
                unique.append(config)
        self.configs = unique

        return self.configs

    def _should_skip(self, path: Path) -> bool:
        """Skip test files, etc."""
        skip_patterns = [
            "__pycache__", ".venv", "venv", "test_",
            "tests/", "migrations/", "node_modules"
        ]
        path_str = str(path)
        return any(p in path_str for p in skip_patterns)

    def _discover_env_vars(self, file: Path, content: str):
        """Discover environment variable usage."""
        # os.getenv("VAR_NAME", "default")
        getenv_pattern = r"os\.getenv\s*\(\s*['\"]([A-Z_][A-Z0-9_]*)['\"](?:\s*,\s*([^)]+))?\)"
        for match in re.finditer(getenv_pattern, content):
            name = match.group(1)
            default = match.group(2).strip().strip("'\"") if match.group(2) else ""
            line_num = content[:match.start()].count('\n') + 1

            self.configs.append(ConfigOption(
                name=name,
                type="env_var",
                file=str(file.relative_to(self.root)),
                line=line_num,
                default=default,
                required=not bool(default)
            ))

        # os.environ["VAR_NAME"] or os.environ.get("VAR_NAME")
        environ_pattern = r"os\.environ(?:\.get)?\s*\[\s*['\"]([A-Z_][A-Z0-9_]*)['\"]"
        for match in re.finditer(environ_pattern, content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            self.configs.append(ConfigOption(
                name=name,
                type="env_var",
                file=str(file.relative_to(self.root)),
                line=line_num,
                required=True
            ))

    def _discover_pydantic_settings(self, file: Path, content: str):
        """Discover Pydantic Settings fields."""
        if "BaseSettings" not in content and "pydantic_settings" not in content:
            return

        # Find class that inherits from BaseSettings
        class_pattern = r"class\s+\w+\s*\([^)]*BaseSettings[^)]*\):"
        if not re.search(class_pattern, content):
            return

        # Find Field definitions with env= parameter
        field_pattern = r"(\w+)\s*:\s*\w+\s*=\s*Field\s*\([^)]*env\s*=\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(field_pattern, content):
            field_name = match.group(1)
            env_name = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            self.configs.append(ConfigOption(
                name=env_name,
                type="pydantic_setting",
                file=str(file.relative_to(self.root)),
                line=line_num
            ))

        # Also find simple type annotations after BaseSettings class
        # pattern: field_name: type = "default" or field_name: type
        simple_pattern = r"^\s{4}([A-Z_][A-Z0-9_]*)\s*:\s*(\w+)"
        for match in re.finditer(simple_pattern, content, re.MULTILINE):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            self.configs.append(ConfigOption(
                name=name,
                type="pydantic_setting",
                file=str(file.relative_to(self.root)),
                line=line_num
            ))

    def _discover_django_settings(self, file: Path, content: str):
        """Discover Django settings."""
        if "settings.py" not in str(file) and "DJANGO_SETTINGS" not in content:
            return

        # Find uppercase variable assignments
        setting_pattern = r"^([A-Z][A-Z0-9_]*)\s*=\s*(.+)$"
        for match in re.finditer(setting_pattern, content, re.MULTILINE):
            name = match.group(1)
            value = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1

            # Skip imports and common non-settings
            if name in ["TRUE", "FALSE", "NONE"] or "import" in value:
                continue

            self.configs.append(ConfigOption(
                name=name,
                type="django_setting",
                file=str(file.relative_to(self.root)),
                line=line_num,
                default=value[:50] if len(value) < 50 else value[:47] + "..."
            ))
