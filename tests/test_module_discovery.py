"""Tests for module discovery — classes AND public functions."""

from __future__ import annotations

from pathlib import Path

from docpistemic.discovery.module_discovery import ModuleDiscovery


def _setup_pkg(root: Path, name: str = "mypkg") -> Path:
    """Create a minimal Python package layout."""
    (root / "pyproject.toml").write_text(f'[project]\nname = "{name}"\n', encoding="utf-8")
    pkg = root / name
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    return pkg


def test_discovery_finds_classes_and_module_level_functions(tmp_path):
    pkg = _setup_pkg(tmp_path)
    (pkg / "mod.py").write_text(
        '"""Module docstring."""\n'
        '\n'
        'class PublicClass:\n'
        '    """Has a docstring."""\n'
        '    pass\n'
        '\n'
        'class _PrivateClass:\n'
        '    pass\n'
        '\n'
        'def public_function():\n'
        '    """A public function."""\n'
        '    pass\n'
        '\n'
        'def _private_function():\n'
        '    pass\n',
        encoding="utf-8",
    )

    disc = ModuleDiscovery(tmp_path)
    disc.discover()
    pub = disc.get_public_modules()

    by_type = {(m.name, m.type) for m in pub}
    assert ("PublicClass", "class") in by_type
    assert ("public_function", "function") in by_type
    # Private (leading underscore) should be excluded
    assert ("_PrivateClass", "class") not in by_type
    assert ("_private_function", "function") not in by_type


def test_discovery_records_docstring_presence(tmp_path):
    pkg = _setup_pkg(tmp_path)
    (pkg / "mod.py").write_text(
        'def documented():\n'
        '    """I have a docstring."""\n'
        '    pass\n'
        '\n'
        'def undocumented():\n'
        '    pass\n',
        encoding="utf-8",
    )

    disc = ModuleDiscovery(tmp_path)
    disc.discover()
    pub = {m.name: m for m in disc.get_public_modules()}

    assert pub["documented"].docstring  # truthy
    assert not pub["undocumented"].docstring


def test_discovery_skips_methods_inside_classes(tmp_path):
    """Methods inside classes are NOT module-level functions and shouldn't be counted."""
    pkg = _setup_pkg(tmp_path)
    (pkg / "mod.py").write_text(
        'class Container:\n'
        '    def method_one(self):\n'
        '        pass\n'
        '    def method_two(self):\n'
        '        pass\n'
        '\n'
        'def actual_module_function():\n'
        '    pass\n',
        encoding="utf-8",
    )

    disc = ModuleDiscovery(tmp_path)
    disc.discover()
    func_names = {m.name for m in disc.get_public_modules() if m.type == "function"}

    assert "actual_module_function" in func_names
    assert "method_one" not in func_names
    assert "method_two" not in func_names


def test_discovery_skips_test_files(tmp_path):
    """test_*.py and tests/ paths should be skipped."""
    pkg = _setup_pkg(tmp_path)
    (pkg / "real_module.py").write_text(
        "def real_func(): pass\n", encoding="utf-8"
    )
    (pkg / "test_real_module.py").write_text(
        "def test_something(): pass\n", encoding="utf-8"
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")

    disc = ModuleDiscovery(tmp_path)
    disc.discover()
    func_names = {m.name for m in disc.get_public_modules() if m.type == "function"}

    assert "real_func" in func_names
    assert "test_something" not in func_names
    assert "test_x" not in func_names


def test_get_public_modules_returns_both_types(tmp_path):
    pkg = _setup_pkg(tmp_path)
    (pkg / "mod.py").write_text(
        "class Foo: pass\n"
        "def bar(): pass\n"
        "def baz(): pass\n",
        encoding="utf-8",
    )

    disc = ModuleDiscovery(tmp_path)
    disc.discover()
    pub = disc.get_public_modules()

    types = {m.type for m in pub}
    assert types == {"class", "function"}
    assert len(pub) == 3


def test_all_filter_marks_non_exports_private(tmp_path):
    """If a module has __all__, items not in __all__ get is_public=False."""
    pkg = _setup_pkg(tmp_path)
    (pkg / "mod.py").write_text(
        '__all__ = ["exported_func"]\n'
        '\n'
        'def exported_func(): pass\n'
        'def hidden_func(): pass\n',
        encoding="utf-8",
    )

    disc = ModuleDiscovery(tmp_path)
    disc.discover()
    by_name = {m.name: m for m in disc.modules}
    assert by_name["exported_func"].is_public is True
    assert by_name["hidden_func"].is_public is False
    # get_public_modules filters
    pub_names = {m.name for m in disc.get_public_modules()}
    assert "exported_func" in pub_names
    assert "hidden_func" not in pub_names
