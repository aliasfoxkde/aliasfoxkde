#!/usr/bin/env python3
"""Validate the canonical portfolio project manifest using only the Python standard library."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "projects.json"
ALLOWED = {
    "maintained", "active-development", "prototype", "experimental",
    "archived", "fork-or-mirror", "internal-support", "needs-review",
}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def valid_url(value: object, field: str, project_id: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        fail(f"{project_id}.{field} must be a URL string or null")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{project_id}.{field} must be an absolute HTTPS URL")


def main() -> None:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {MANIFEST}: {exc}")
    if not isinstance(data, dict):
        fail("top-level manifest must be an object")
    if data.get("schema_version") != 1:
        fail("schema_version must be 1")
    if data.get("owner") != "aliasfoxkde":
        fail("owner must be aliasfoxkde")
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        fail("projects must be a non-empty array")

    seen: set[str] = set()
    for index, project in enumerate(projects):
        if not isinstance(project, dict):
            fail(f"projects[{index}] must be an object")
        project_id = project.get("id")
        if not isinstance(project_id, str) or not ID_RE.fullmatch(project_id):
            fail(f"projects[{index}].id must be lowercase kebab-case")
        if project_id in seen:
            fail(f"duplicate project id: {project_id}")
        seen.add(project_id)
        for field in ("name", "category", "summary"):
            if not isinstance(project.get(field), str) or not project[field].strip():
                fail(f"{project_id}.{field} must be a non-empty string")
        if project.get("status") not in ALLOWED:
            fail(f"{project_id}.status must be one of {sorted(ALLOWED)}")
        if not isinstance(project.get("featured"), bool):
            fail(f"{project_id}.featured must be boolean")
        valid_url(project.get("repository"), "repository", project_id)
        valid_url(project.get("website"), "website", project_id)
        if not project.get("repository") and not project.get("website"):
            fail(f"{project_id} must have a repository or website URL")

    print(f"Validated {len(projects)} projects ({sum(p['featured'] for p in projects)} featured).")


if __name__ == "__main__":
    main()
