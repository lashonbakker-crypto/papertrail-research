# Changelog

## 0.2.0 — 2026-10-16

- Add `import-results` for measured CSV outputs: exact byte snapshots, finite metric/sample-size validation, explicit toy/real labels, collision refusal, and optional input/code hashes. Stored commands are never executed.
- Audit CSV snapshots, JSON mappings, table values and source descriptions; cache each group's parsed snapshot. Detect missing group members and changed inputs. Unknown artifact schemas explicitly warn that numeric values were not verified.
- Add an actually computed classification teaching workflow, saved per-test predictions/code, and accuracy/precision/recall report charts. Ten original toy rows and four test cases establish workflow behavior, not method superiority.
- Supply public CSL-JSON metadata and bilingual beginner steps. Fix the blank workspace's example citation being treated as a real missing reference; turn malformed CSV quoting/field errors into controlled exit code 2.
- Extend installed, portable and published-download checks to cover external imports and changed snapshots. Include examples in source downloads.

## 0.1.1 — 2026-10-14

- Fix portable archive exit codes: the generated entry point now exits with the CLI result. Invalid projects and missing citations return 2 instead of 0.
- Extend the portable regression check to exercise successful and failing commands away from the source tree.
- Use the current version in report footers and the explicit DOI lookup User-Agent.
- Add a repeatable release-download check for Linux, Windows and Intel macOS; actual outcomes are recorded in docs/validation.md.

## 0.1.0 — 2026-10-14

- New local research workspaces, reference import, evidence cards and structured experiment records.
- Bracketed Markdown citation checks, evidence/result ID checks, artifact SHA-256 checks, and built-in metric/input verification.
- Explicit single DOI metadata lookup via Crossref with bounded reads and controlled errors.
- Reproducible toy retrieval demo: overlap and TF-IDF, per-query rankings, MRR and Recall@1/3.
- Self-contained HTML audit, JSON, Markdown handoff, and draft expansion.
- Chinese first-week guide, research portfolio templates, manual assistant prompts, English entry and share copy.
- Portable Python archive, reproducible release packaging and cross-platform CI.

Validation scope and actual outcomes are recorded in docs/validation.md; a structural pass does not certify research quality.
