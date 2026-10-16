"""Read-only coverage of research records and their draft usage.

This is a bookkeeping report, not an assessment of evidence quality.
"""

import re

from .audit import prose_only

CITATION_KEY = re.compile(r"(?<![\w@])@([A-Za-z][A-Za-z0-9_.:-]*)")
BRACKET_GROUP = re.compile(r"\[([^\]\n]+)\]")
CLAIM_MARKER = re.compile(r"\{\{claim:([A-Za-z][A-Za-z0-9_.:-]*)\}\}")
RUN_MARKER = re.compile(r"\{\{run:([A-Za-z][A-Za-z0-9_.:-]*)\}\}")


def coverage(audit_result):
    """Summarize registered links; do not mutate workspace files.

    Use the same prose filter and citation grammar as the main audit.
    Return no inferred coverage when the audit could not read its inputs.
    """
    errors = audit_result["errors"]
    if not audit_result.get("counts"):
        return {
            "title": audit_result["title"],
            "counts": {},
            "gaps": [],
            "errors": errors,
            "disclaimer": "Input failed validation; no coverage was calculated.",
        }

    refs = audit_result["references"]
    cards = audit_result["evidence"]
    runs = audit_result["runs"]
    prose = prose_only(audit_result["manuscript"])
    cited = {
        match
        for group in BRACKET_GROUP.findall(prose)
        for match in CITATION_KEY.findall(group)
    }
    draft_claims = set(CLAIM_MARKER.findall(prose))
    draft_runs = set(RUN_MARKER.findall(prose))
    ref_keys = {ref["key"] for ref in refs if isinstance(ref.get("key"), str)}
    card_ref_keys = {card["reference_key"] for card in cards}
    card_ids = {card["claim_id"] for card in cards}
    run_ids = {run["run_id"] for run in runs}
    counts = {
        "references": len(refs),
        "references_cited": len(cited & ref_keys),
        "references_with_evidence_cards": len(ref_keys & card_ref_keys),
        "evidence_cards": len(cards),
        "cards_marked_reviewed": sum(card["reviewed"] == "yes" for card in cards),
        "cards_with_locator_and_note": sum(bool(card["locator"].strip() and card["note"].strip()) for card in cards),
        "cards_used_in_draft": len(card_ids & draft_claims),
        "results": len(runs),
        "results_used_in_draft": len(run_ids & draft_runs),
    }
    gaps = []

    def gap(kind, item, action, priority):
        gaps.append({"kind": kind, "item": item, "action": action, "priority": priority})

    for card in cards:
        ident = card["claim_id"]
        if card["reviewed"] != "yes":
            gap("review_pending", ident, "Read the actual source and record your own verification; reviewed=yes is a manual declaration.", "review")
        if not card["locator"].strip() or not card["note"].strip():
            gap("locator_or_note_missing", ident, "Record a section/page locator and your own reading note.", "review")
        if ident not in draft_claims:
            gap("card_not_in_draft", ident, "If this claim belongs in the draft, insert its {{claim:ID}} marker.", "optional")

    for run in runs:
        if run["run_id"] not in draft_runs:
            gap("result_not_in_draft", run["run_id"], "If needed, insert its {{run:ID}} marker in the draft.", "optional")

    for key in sorted(ref_keys - cited - card_ref_keys):
        gap("reference_unlinked", key, "Cite this reference or link it to an evidence card if relevant.", "optional")

    if "TODO" in prose or "待补" in prose:
        gap("unfinished_draft", "manuscript.md", "Resolve the remaining TODO / 待补 notes before sharing the draft.", "review")

    return {
        "title": audit_result["title"],
        "counts": counts,
        "gaps": gaps,
        "errors": errors,
        "disclaimer": "Coverage measures recorded links only. It does not verify whether sources support claims or experiments are valid.",
    }
