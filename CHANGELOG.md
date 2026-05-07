# Changelog

## [0.2.0] — 2026-05-07

### Fixed — coverage assessment was systematically narrow

Pre-0.2.0, `assess` reported coverage against a curated heuristic top-N
classes (default top 20) and **did not count module-level functions at all**.
Discovery was finding functions but the assessor only consumed
`get_key_classes(limit=20)`. Result: denominators were 4–6× smaller than
the real public surface, coverage % was inflated, and adding undocumented
functions to a project did not move the metric.

Verified against the empirica repo: 0.1.0 reported 401 features at 98% →
0.2.0 reports 1,844 features at 97.5% (`--strict` 94.6%). 1,058 public
functions were previously invisible.

### Added

- **`Classes` and `Public Functions` are separate categories** in the
  output. The old single "Core Modules" category split so users can see
  where their gaps are by surface type. JSON shape and console output
  reflect the split.
- **`--strict` flag** — requires AST docstring presence as the primary
  signal instead of substring-matching the name against any markdown.
  Substring match has false positives (a class named `Commit` matches
  every changelog entry); strict mode eliminates them at the cost of a
  more conservative coverage %.
- **`module_limit` is now a display cap on the undocumented preview**,
  not a coverage-denominator cap. `--depth 1/2/3` controls how many
  undocumented items appear in the report (20/50/100), but the
  denominator counts every public class and every public module-level
  function the discoverer found.
- **`CoverageAnalyzer.analyze_module_coverage(modules, category="...")`** —
  the analyzer accepts a `category` parameter so the same code can bucket
  the same analyzer into multiple categories without inventing a new
  method per category.

### Fixed

- **`_should_skip` false-positive on pytest tmp paths** —
  `module_discovery._should_skip` matched `"test_"` and `"tests/"`
  against the full path string, causing pytest's
  `/tmp/pytest-of-USER/test_X0/` parent directories to trigger a skip on
  every real package file inside. Now matches against directory-name
  parts and file basename, not full path.

### Wire compat

- The JSON output's `categories` array gained two distinct entries
  (`Classes` and `Public Functions`) instead of one (`Core Modules`).
  Consumers that look up by category name need to update.
- `discovery.modules` (the count) is replaced by `discovery.classes` +
  `discovery.public_functions` (separate counts). Empirica's compliance
  pipeline (`_parse_docpistemic_result`) uses the top-level
  `epistemic.total_features` and `epistemic.documented_features` fields
  which are unchanged in shape.

## [0.1.0]

Initial release.
