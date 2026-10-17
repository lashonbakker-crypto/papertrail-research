# Roadmap

## Implemented in 0.1.0

- Local workspaces and self-contained reports.
- CSL-JSON import; explicit Crossref metadata lookup.
- Citation-key, evidence-card and structured result checks.
- Original toy retrieval data and computed ranking results.
- Chinese workflow, student learning steps and contribution templates.

## Implemented in 0.3.0

- Read-only evidence coverage report and optional action list (`coverage`), with machine-readable JSON output and tests.
- The same connections and next steps in self-contained HTML reports, with untrusted IDs escaped.
- Shared case-insensitive draft reminder detection across audit and coverage.

## Next small contributions

1. Evidence cards with multiple sources and per-source locators.
2. A larger public, permissively licensed evaluation example with separate development/evaluation splits.
3. A result adapter for one openly documented research tool, with permission to redistribute its example data.

## Implemented in 0.1.1

- Portable commands propagate successful and failing exit codes.
- Repeatable published-asset verification workflow for Linux, Windows and Intel macOS; actual results are kept in docs/validation.md.

## Implemented in 0.2.0

- External measurement CSV import with exact source snapshots, typed checks, collision refusal, optional data/code hashes and per-group audit caching.
- Cross-check imported values, labels, dataset/command provenance and group membership against the preserved CSV; explicitly warn that external commands were not rerun.
- Computed classification course workflow with train-only model selection, test predictions, report and draft. Tiny self-authored toy data, not a research benchmark.
- Public CSL-JSON metadata example and bilingual import walkthrough ([Issue #1](https://github.com/lashonbakker-crypto/papertrail-research/issues/1)).
- Controlled malformed-CSV errors; fresh workspace guidance no longer creates a false missing citation.

## Later, requiring design and separate validation

- BibTeX/RIS import, more complete Pandoc Markdown citation parsing.
- Versioned dataset paths and concurrent-writer protection.
- School/journal formatting via existing Pandoc or LaTeX templates.
- Optional PDF extraction with clear page provenance and copyright controls.
- Optional tool API / task queue adapter; no LLM provider or autonomous writing exists today.

Prioritize a workflow step someone cannot complete over adding another score or another prompt.
