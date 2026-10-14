# Changelog

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
