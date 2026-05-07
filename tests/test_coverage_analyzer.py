"""Tests for the coverage analyzer — categories, strict mode, denominator integrity."""

from __future__ import annotations

from docpistemic.assessment.coverage import CoverageAnalyzer
from docpistemic.discovery.module_discovery import DiscoveredModule


def _make_module(name: str, type_: str = "class", docstring: str = "") -> DiscoveredModule:
    return DiscoveredModule(
        name=name, type=type_, file="mypkg/mod.py", line=1,
        docstring=docstring, is_public=True,
    )


def test_analyze_module_coverage_uses_provided_category(tmp_path):
    analyzer = CoverageAnalyzer(tmp_path)
    analyzer.docs_content = "x"
    modules = [_make_module("Foo", "class", "doc")]

    classes_result = analyzer.analyze_module_coverage(modules, category="Classes")
    funcs_result = analyzer.analyze_module_coverage(modules, category="Public Functions")

    assert classes_result.category == "Classes"
    assert funcs_result.category == "Public Functions"


def test_analyze_module_coverage_default_category(tmp_path):
    """Default category is 'Core Modules' for backward compat."""
    analyzer = CoverageAnalyzer(tmp_path)
    analyzer.docs_content = "x"
    modules = [_make_module("Foo", "class", "doc")]

    result = analyzer.analyze_module_coverage(modules)
    assert result.category == "Core Modules"


def test_analyze_module_coverage_counts_docstring_as_documented(tmp_path):
    analyzer = CoverageAnalyzer(tmp_path)
    analyzer.docs_content = ""  # nothing in docs
    documented_mod = _make_module("DocumentedFunc", "function", docstring="I am documented")
    bare_mod = _make_module("BareFunc", "function", docstring="")

    result = analyzer.analyze_module_coverage([documented_mod, bare_mod])
    assert result.documented == 1
    assert "DocumentedFunc" not in result.undocumented
    assert "BareFunc" in result.undocumented


def test_strict_mode_ignores_docs_substring_match(tmp_path):
    """In strict mode, having the name in docs_content is NOT enough — only AST docstring counts."""
    docs = "MyClass is mentioned here in the docs."
    strict = CoverageAnalyzer(tmp_path, strict=True)
    strict.docs_content = docs.lower()
    permissive = CoverageAnalyzer(tmp_path, strict=False)
    permissive.docs_content = docs.lower()

    mod_no_docstring = _make_module("MyClass", "class", docstring="")
    mod_with_docstring = _make_module("OtherClass", "class", docstring="docstring")

    strict_result = strict.analyze_module_coverage([mod_no_docstring, mod_with_docstring])
    permissive_result = permissive.analyze_module_coverage([mod_no_docstring, mod_with_docstring])

    # Strict: only OtherClass (docstring) counts; MyClass undocumented despite mention
    assert strict_result.documented == 1
    assert "MyClass" in strict_result.undocumented

    # Permissive: both count — MyClass via substring match, OtherClass via docstring
    assert permissive_result.documented == 2


def test_coverage_denominator_includes_all_provided_modules(tmp_path):
    """Regression: 0.1.0 was capping denominator at 20 via get_key_classes(limit=20).
    The analyzer must count every module passed in."""
    analyzer = CoverageAnalyzer(tmp_path)
    analyzer.docs_content = ""

    # 50 modules, none documented
    modules = [_make_module(f"Mod{i}", "class", docstring="") for i in range(50)]
    result = analyzer.analyze_module_coverage(modules)

    assert result.total == 50
    assert result.documented == 0
    assert result.coverage == 0.0


def test_strict_mode_passes_when_all_have_docstrings(tmp_path):
    analyzer = CoverageAnalyzer(tmp_path, strict=True)
    analyzer.docs_content = ""
    modules = [_make_module(f"Mod{i}", "function", docstring="doc") for i in range(10)]

    result = analyzer.analyze_module_coverage(modules)
    assert result.coverage == 1.0
    assert result.documented == 10
