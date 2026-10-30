#!/usr/bin/env python3
"""Refresh the public follower list in the profile README."""

from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OWNER = "aliasfoxkde"
README = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- profile-followers:start -->"
END = "<!-- profile-followers:end -->"
STATS_START = "<!-- profile-stats:start -->"
STATS_END = "<!-- profile-stats:end -->"
PER_PAGE = 100
LOGIN_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")


def fetch_followers() -> list[str]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "aliasfoxkde-profile-follower-refresh",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    followers: dict[str, str] = {}
    page = 1
    while True:
        request = Request(
            f"https://api.github.com/users/{OWNER}/followers?per_page={PER_PAGE}&page={page}",
            headers=headers,
        )
        try:
            with urlopen(request, timeout=30) as response:
                records = json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError(f"GitHub follower API request failed on page {page}: {error}") from error
        if not isinstance(records, list):
            raise RuntimeError(f"GitHub returned an unexpected response on page {page}")
        for record in records:
            login = record.get("login") if isinstance(record, dict) else None
            if not isinstance(login, str) or not LOGIN_RE.fullmatch(login):
                raise RuntimeError(f"GitHub returned an invalid follower record on page {page}")
            followers.setdefault(login.casefold(), login)
        if len(records) < PER_PAGE:
            break
        page += 1
    return sorted(followers.values(), key=str.casefold)


def fetch_public_repositories() -> list[dict[str, object]]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "aliasfoxkde-profile-stats-refresh",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repositories: list[dict[str, object]] = []
    page = 1
    while True:
        request = Request(
            f"https://api.github.com/users/{OWNER}/repos?type=owner&per_page={PER_PAGE}&page={page}",
            headers=headers,
        )
        try:
            with urlopen(request, timeout=30) as response:
                records = json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError(f"GitHub repository API request failed on page {page}: {error}") from error
        if not isinstance(records, list):
            raise RuntimeError(f"GitHub returned an unexpected repository response on page {page}")
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("fork"), bool):
                raise RuntimeError(f"GitHub returned an invalid repository record on page {page}")
            if record.get("private") is True or record.get("archived") is True:
                continue
            for key in ("stargazers_count", "forks_count"):
                if not isinstance(record.get(key), int) or record[key] < 0:
                    raise RuntimeError(f"GitHub returned an invalid {key} value on page {page}")
            repositories.append(record)
        if len(records) < PER_PAGE:
            break
        page += 1
    return repositories


def render_followers(followers: list[str]) -> str:
    if not followers:
        return "No public followers yet."
    tags = [
        f'<a href="https://github.com/{html.escape(login, quote=True)}"><code>@{html.escape(login)}</code></a>'
        for login in followers
    ]
    return ",\n".join(", ".join(tags[start : start + 8]) for start in range(0, len(tags), 8))


def render_stats(followers: list[str], repositories: list[dict[str, object]]) -> str:
    originals = [repository for repository in repositories if repository["fork"] is False]
    stats = [
        ("Followers", len(followers), "blue"),
        ("Public%20repos", len(repositories), "informational"),
        ("Original%20repos", len(originals), "success"),
        ("Project%20stars", sum(int(repository["stargazers_count"]) for repository in originals), "yellow"),
        ("Project%20forks", sum(int(repository["forks_count"]) for repository in originals), "lightgrey"),
    ]
    return "\n  ".join(
        f'<a href="https://github.com/{OWNER}?tab={"followers" if label == "Followers" else "repositories"}">'
        f'<img alt="{html.escape(label.replace("%20", " "))}" '
        f'src="https://img.shields.io/badge/{label}-{value}-{color}?style=flat-square" /></a>'
        for label, value, color in stats
    )


def update_readme() -> bool:
    content = README.read_text(encoding="utf-8")
    if content.count(START) != 1 or content.count(END) != 1:
        raise RuntimeError("README must contain exactly one start and end marker")
    start = content.index(START) + len(START)
    end = content.index(END)
    if start > end:
        raise RuntimeError("README follower markers are in the wrong order")

    followers = fetch_followers()
    repositories = fetch_public_repositories()
    generated = f"\n{render_followers(followers)}\n"
    updated = content[:start] + generated + content[end:]
    if updated.count(STATS_START) != 1 or updated.count(STATS_END) != 1:
        raise RuntimeError("README must contain exactly one start and end stats marker")
    stats_start = updated.index(STATS_START) + len(STATS_START)
    stats_end = updated.index(STATS_END)
    if stats_start > stats_end:
        raise RuntimeError("README stats markers are in the wrong order")
    stats = f"\n  {render_stats(followers, repositories)}\n  "
    updated = updated[:stats_start] + stats + updated[stats_end:]
    if updated == content:
        print(
            f"Profile data already current ({len(followers)} public followers, "
            f"{len(repositories)} public repositories)."
        )
        return False
    README.write_text(updated, encoding="utf-8")
    print(
        f"Updated README with {len(followers)} public followers and "
        f"{len(repositories)} public repositories."
    )
    return True


if __name__ == "__main__":
    try:
        update_readme()
    except (OSError, RuntimeError) as error:
        print(f"update_profile_followers: {error}", file=sys.stderr)
        sys.exit(1)
