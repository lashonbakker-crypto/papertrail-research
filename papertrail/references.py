"""Import CSL-JSON and explicitly fetch bibliographic metadata from Crossref."""

import datetime
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from . import __version__
from .storage import LIMIT, ProjectError, json_text, project_path, read_json, replace_text

KEY_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*\Z")


def normalize_doi(value):
    if not isinstance(value, str):
        raise ProjectError("DOI must be text")
    value = value.strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.I)
    value = re.sub(r"^doi:\s*", "", value, flags=re.I)
    if not re.fullmatch(r"10\.\d{4,9}/[^\s?#]+", value, re.I):
        raise ProjectError(f"Invalid DOI syntax: {value}")
    return value.lower()


def _year(issued):
    if issued is None:
        return None
    if not isinstance(issued, dict):
        raise ProjectError("issued must be an object")
    date = issued.get("date-parts", [[]])
    if not isinstance(date, list) or any(not isinstance(part, list) for part in date):
        raise ProjectError("date-parts must be an array of date arrays")
    year = date[0][0] if date and date[0] else None
    if year is not None and (type(year) is not int or not 1000 <= year <= 2200):
        raise ProjectError("Publication year must be an integer between 1000 and 2200")
    return year


def _authors(names):
    if names is None:
        return []
    if not isinstance(names, list) or any(not isinstance(a, dict) for a in names):
        raise ProjectError("Authors must be an array of name objects")
    for author in names:
        if any(not isinstance(author.get(key, ""), str) for key in ("given", "family", "literal")):
            raise ProjectError("Author names must be strings")
    return [a.get("literal") or " ".join(filter(None, [a.get("given"), a.get("family")])) for a in names]


def import_csl(root, source):
    """All-or-nothing import, preserving existing keys and rejecting collisions."""
    items = read_json(source)
    path = project_path(root, "references.json")
    existing = read_json(path)
    if not isinstance(items, list) or not isinstance(existing, list):
        raise ProjectError("CSL input and references.json must be JSON arrays")
    if any(not isinstance(ref, dict) or not isinstance(ref.get("key"), str) for ref in existing):
        raise ProjectError("Existing references must have string keys")
    keys = {ref["key"] for ref in existing}
    dois = {normalize_doi(ref["doi"]) for ref in existing if ref.get("doi")}
    if len(keys) != len(existing):
        raise ProjectError("Existing reference keys are duplicated")
    added = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict) or not isinstance(item.get("title"), str) or not item["title"].strip():
            raise ProjectError(f"CSL item {index} needs a title")
        key = item.get("citation-key", item.get("id", ""))
        if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
            key = f"ref{len(existing) + index}"
        if key in keys:
            raise ProjectError(f"Reference key collision: {key}; edit the CSL id before importing")
        doi = normalize_doi(item["DOI"]) if item.get("DOI") else ""
        if doi and doi in dois:
            raise ProjectError(f"Duplicate DOI: {doi}")
        year = _year(item.get("issued"))
        authors = _authors(item.get("author"))
        added.append({"key": key, "title": item["title"], "authors": authors, "year": year, "doi": doi, "url": item.get("URL", ""), "metadata_source": "CSL-JSON import; not independently verified"})
        keys.add(key)
        if doi:
            dois.add(doi)
    replace_text(path, json_text(existing + added))
    return added


def fetch_doi(doi, timeout=15):
    doi = normalize_doi(doi)
    endpoint = "https://api.crossref.org/works/" + quote(doi, safe="")
    request = Request(endpoint, headers={"User-Agent": f"PaperTrail/{__version__} (https://github.com/lashonbakker-crypto/papertrail-research)", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read(LIMIT + 1)
    except HTTPError as error:
        if error.code == 404:
            raise ProjectError("DOI not found in Crossref. It may belong to DataCite or another agency; check the publisher manually.") from error
        raise ProjectError(f"Crossref HTTP {error.code}; no reference was saved") from error
    except (URLError, TimeoutError) as error:
        raise ProjectError(f"Crossref unavailable; no reference was saved: {error}") from error
    if len(payload) > LIMIT:
        raise ProjectError("Crossref response exceeds size limit")
    envelope = json.loads(payload)
    message = envelope.get("message") if isinstance(envelope, dict) else None
    if not isinstance(message, dict) or not isinstance(message.get("DOI"), str) or not isinstance(message.get("title"), list) or not message["title"] or not isinstance(message["title"][0], str):
        raise ProjectError("Crossref response is missing bibliographic fields")
    if normalize_doi(message["DOI"]) != doi or not message["title"][0].strip():
        raise ProjectError("Crossref response DOI/title mismatch")
    return {"title": message["title"][0], "authors": _authors(message.get("author")), "year": _year(message.get("issued")), "doi": doi, "url": "https://doi.org/" + doi, "metadata_source": endpoint, "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}


def add_doi(root, doi, key):
    if not KEY_PATTERN.fullmatch(key):
        raise ProjectError("Citation key must start with an ASCII letter")
    path = project_path(root, "references.json")
    refs = read_json(path)
    if not isinstance(refs, list) or any(not isinstance(ref, dict) for ref in refs):
        raise ProjectError("references.json must be an array of objects")
    canonical = normalize_doi(doi)
    if any(ref.get("key") == key or (ref.get("doi") and normalize_doi(ref["doi"]) == canonical) for ref in refs):
        raise ProjectError("Key or DOI already exists; existing references were not changed")
    reference = {"key": key, **fetch_doi(canonical)}
    replace_text(path, json_text(refs + [reference]))
    return reference
