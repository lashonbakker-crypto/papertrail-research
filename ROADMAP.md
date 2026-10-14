# Roadmap

## Implemented in 0.1.0

- Local workspaces and self-contained reports.
- CSL-JSON import; explicit Crossref metadata lookup.
- Citation-key, evidence-card and structured result checks.
- Original toy retrieval data and computed ranking results.
- Chinese workflow, student learning steps and contribution templates.

## Next small contributions

1. A validated external experiment adapter: map a real CSV result to the record schema without inventing measurements.
2. Evidence cards with multiple sources and per-source locators.
3. A larger public, permissively licensed evaluation example with separate development/evaluation splits.
4. Release-asset download verification on Linux, Windows and macOS.

## Later, requiring design and separate validation

- BibTeX/RIS import, more complete Pandoc Markdown citation parsing.
- Versioned dataset paths and concurrent-writer protection.
- School/journal formatting via existing Pandoc or LaTeX templates.
- Optional PDF extraction with clear page provenance and copyright controls.
- Optional tool API / task queue adapter; no LLM provider or autonomous writing exists today.

Prioritize a workflow step someone cannot complete over adding another score or another prompt.
