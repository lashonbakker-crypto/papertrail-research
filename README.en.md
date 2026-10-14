# PaperTrail — Research with a record

![PaperTrail](assets/banner.svg)

**Your paper is not written yet, but your references, notes, and experiment outputs are already scattered? Connect the process first.**

A local research starter for students: references → evidence cards → experiments → draft → advisor update. Python 3.10+, no runtime dependencies. [中文](README.md)

[![Tests](https://github.com/lashonbakker-crypto/papertrail-research/actions/workflows/ci.yml/badge.svg)](https://github.com/lashonbakker-crypto/papertrail-research/actions/workflows/ci.yml)
[![MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Try it in five minutes

For the complete offline bundle, unzip it, enter `papertrail-research`, and run `python -m papertrail demo my-first-study`. For a Release source ZIP, unzip it and run the same command inside `papertrail-research`. See [offline start](docs/00-offline-start.md).

```bash
git clone https://github.com/lashonbakker-crypto/papertrail-research.git
cd papertrail-research
python -m papertrail demo my-first-study
```

Open `my-first-study/report/index.html`: two real background references, two evidence cards, six measured result rows, and actionable reminders. The expected summary is `STRUCTURE CHECK OK: 0 error(s), 7 reminder(s)`.

![Real CLI demo](assets/demo.gif)

![Generated report](assets/report-preview.png)

The graphic above is a data overview generated from a real demo audit, not a browser screenshot. Open the local HTML report for the full output.

## What works today

| Feature | Behavior |
|---|---|
| Citation checks | Detect unknown bracketed Markdown citation keys such as `[@missing2026]`; skip fenced/inline code and HTML comments |
| Evidence cards | Record claim, reference key, section/page locator, your own note, and an explicit human review state |
| Provenance checks | Check artifact SHA-256; built-in experiment also checks table values against the original JSON and input hashes |
| Zotero handoff | Import CSL-JSON, refuse key/DOI collisions without partial imports |
| Explicit DOI lookup | Fetch one Crossref metadata record only when `add-doi` is requested |
| Reproducible experiment | Compare term-overlap and smoothed TF-IDF cosine ranking on a handwritten English toy corpus |
| Reports | Self-contained HTML, JSON audit, expanded Markdown draft, and research handoff notes |

```bash
python -m papertrail init my-research
python -m papertrail import-csl my-research zotero-export.json
python -m papertrail add-doi my-research 10.1038/nature14539 --key lecun2015
python -m papertrail check my-research --json
python -m papertrail report my-research --out my-research/report-v1
```

Only `add-doi` performs networking. Other commands run locally. Existing project/report destinations and experiment IDs are not overwritten. CSL keys use `citation-key`, a valid `id`, or sequential `refN` fallback. An import does not mark papers reviewed.

Download `papertrail.pyz` and `SHA256SUMS.txt` from [Releases](https://github.com/lashonbakker-crypto/papertrail-research/releases/latest), verify the checksum, and run `python papertrail.pyz demo my-first-study`. A Python interpreter is still required. See [commands and integrity checks](docs/03-cli.md).

## Honest scope

The demo has 8 documents and 12 manually authored queries, one relevant document per query. Both methods score 1.0 for MRR and Recall@1/3 on this easy corpus. This establishes a runnable workflow, not method superiority or research novelty. It does not run an LLM, RAG, or BEIR.

A passing audit confirms selected structural and file consistency checks. It does not prove scientific validity, support for a claim, plagiarism status, retraction status, or publisher compliance. `reviewed=yes` is a human declaration. DOI metadata is not evidence that a paper supports a claim; a Crossref 404 can also mean another registration agency.

The toy experiment tokenizes ASCII English alphanumerics. The workflow accepts Unicode notes. Input files are limited to 8 MiB each; symlinks in project paths are refused. There is no concurrent-writer lock or snapshot. Artifact creation plus CSV update is not a multi-file transaction; an interrupted write may leave an orphan artifact for manual inspection.

Generated reports have no external scripts, fonts or telemetry. The project supplies prompts for manual use with your preferred assistant, without API integration. Personal research projects belong outside this public repository.

## Learn and contribute

- [First week](docs/01-first-week.md) / [Workflow](docs/02-workflow.md) / [CLI](docs/03-cli.md)
- [Research portfolio](docs/04-research-portfolio.md) / [manual assistant prompts](prompts/README.md)
- [Validation](docs/validation.md) / [Contributing](CONTRIBUTING.md) / [Roadmap](ROADMAP.md)

```bash
python -m unittest discover -s tests -v
python scripts/build_zipapp.py
```

**Star to keep it handy, run the demo, and open an issue with the step you could not complete.** Public reproductions and well-scoped improvements are welcome.

Original code, templates, diagrams, and toy data are MIT licensed. Background sources: [Lewis et al.](https://arxiv.org/abs/2005.11401), [Thakur et al.](https://arxiv.org/abs/2104.08663), [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), [Zotero](https://www.zotero.org/support/kb/exporting), and [CSL specification](https://docs.citationstyles.org/en/stable/specification.html). No paper full text is redistributed.
