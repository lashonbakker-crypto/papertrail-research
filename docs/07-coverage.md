# Evidence coverage / 证据覆盖率

PaperTrail's read-only coverage command answers an operational question: **what has been recorded, and what still needs connecting before writing?** It is not a paper-grading or automatic fact-checking system.

## Run / 运行

After initializing a workspace (or running the included demo):

~~~bash
python -m papertrail demo demo-study
python -m papertrail coverage demo-study
python -m papertrail coverage demo-study --json
~~~

The CLI reads project files, performs the existing structural audit, then prints counts and action items. It never writes to the workspace or calls a web service. Exit code **0** means no structural errors, even if research reminders remain; **2** means a structural or input error.

## Understanding the counts / 如何理解指标

- `references_cited`: registered bibliography keys appearing in supported `[@key]` manuscript citations.
- `references_with_evidence_cards`: registered sources linked from at least one evidence card.
- `cards_marked_reviewed`: rows whose **human-declared** `reviewed` cell equals `yes`. It is not independent verification.
- `cards_with_locator_and_note`: rows with both a location and a personal note.
- `cards_used_in_draft`: unique evidence-card IDs referenced by `{{claim:ID}}`.
- `results_used_in_draft`: unique measured result IDs referenced by `{{run:ID}}`.

Suggested actions distinguish **review** work (unread sources, missing locators, TODOs) from **optional** links (cards or results kept for background work but not yet mentioned). It is normal for an experiment notebook to have unused measurements. These are not errors.

The command honors the same limited Markdown citation grammar as `check`: bracket groups, and ignores fenced/inline code and HTML comments. It does not parse all Pandoc citation syntax. For structural errors, run `python -m papertrail check PROJECT`. Invalid workspace inputs produce no inferred coverage.

**Do not call this a plagiarism, source-validity, research-novelty, or admissions-readiness score.** To share results responsibly, read the cited source, inspect the experiment artifacts and limitations, and rerun relevant computations.
