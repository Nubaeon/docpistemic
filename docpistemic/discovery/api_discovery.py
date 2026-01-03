"""
API Discovery - Detect web API endpoints.

Supports:
- FastAPI: @app.get, @router.post, etc.
- Flask: @app.route, @blueprint.route
- Django: urlpatterns, path(), re_path()
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIEndpoint:
    """Discovered API endpoint."""
    path: str
    method: str  # GET, POST, PUT, DELETE, etc.
    framework: str  # fastapi, flask, django
    file: str
    line: int
    name: str = ""  # Function/view name


class APIDiscovery:
    """Discover API endpoints from web frameworks."""

    def __init__(self, root: Path):
        self.root = root
        self.endpoints: list[APIEndpoint] = []

    def discover(self) -> list[APIEndpoint]:
        """Run all API discovery methods."""
        for py_file in self.root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            try:
                content = py_file.read_text()
                self._discover_fastapi(py_file, content)
                self._discover_flask(py_file, content)
                self._discover_django(py_file, content)
            except Exception:
                pass

        return self.endpoints

    def _should_skip(self, path: Path) -> bool:
        """Skip test files, migrations, etc."""
        skip_patterns = [
            "__pycache__", ".venv", "venv", "test_", "_test.py",
            "tests/", "migrations/", "node_modules"
        ]
        path_str = str(path)
        return any(p in path_str for p in skip_patterns)

    def _discover_fastapi(self, file: Path, content: str):
        """Discover FastAPI endpoints."""
        if "fastapi" not in content.lower() and "@app." not in content and "@router." not in content:
            return

        # Pattern: @app.get("/path") or @router.post("/path")
        methods = ["get", "post", "put", "delete", "patch", "options", "head"]
        for method in methods:
            pattern = rf"@\w+\.{method}\s*\(\s*['\"]([^'\"]+)['\"]"
            for match in re.finditer(pattern, content, re.IGNORECASE):
                path = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # Try to get function name
                func_match = re.search(r"(?:async\s+)?def\s+(\w+)\s*\(", content[match.end():match.end()+200])
                name = func_match.group(1) if func_match else ""

                self.endpoints.append(APIEndpoint(
                    path=path,
                    method=method.upper(),
                    framework="fastapi",
                    file=str(file.relative_to(self.root)),
                    line=line_num,
                    name=name
                ))

    def _discover_flask(self, file: Path, content: str):
        """Discover Flask endpoints."""
        if "flask" not in content.lower() and "@app.route" not in content:
            return

        # Pattern: @app.route("/path", methods=["GET", "POST"])
        pattern = r"@\w+\.route\s*\(\s*['\"]([^'\"]+)['\"](?:[^)]*methods\s*=\s*\[([^\]]+)\])?"
        for match in re.finditer(pattern, content):
            path = match.group(1)
            methods_str = match.group(2) if match.group(2) else '"GET"'
            methods = re.findall(r"['\"](\w+)['\"]", methods_str)
            line_num = content[:match.start()].count('\n') + 1

            # Get function name
            func_match = re.search(r"def\s+(\w+)\s*\(", content[match.end():match.end()+200])
            name = func_match.group(1) if func_match else ""

            for method in methods or ["GET"]:
                self.endpoints.append(APIEndpoint(
                    path=path,
                    method=method.upper(),
                    framework="flask",
                    file=str(file.relative_to(self.root)),
                    line=line_num,
                    name=name
                ))

    def _discover_django(self, file: Path, content: str):
        """Discover Django URL patterns."""
        if "urlpatterns" not in content:
            return

        # Pattern: path('api/users/', views.user_list)
        path_pattern = r"path\s*\(\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(path_pattern, content):
            path = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Try to get view name
            view_match = re.search(r",\s*(\w+\.?\w*)", content[match.end():match.end()+100])
            name = view_match.group(1) if view_match else ""

            self.endpoints.append(APIEndpoint(
                path="/" + path if not path.startswith("/") else path,
                method="*",  # Django doesn't specify method in urls.py
                framework="django",
                file=str(file.relative_to(self.root)),
                line=line_num,
                name=name
            ))
