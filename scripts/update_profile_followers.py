#!/usr/bin/env python3
"""Refresh public profile followers, repository metrics, and sponsors."""

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
SPONSORS_START = "<!-- profile-sponsors:start -->"
SPONSORS_END = "<!-- profile-sponsors:end -->"
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


def fetch_public_sponsors() -> list[str]:
    """Return active public sponsors only; private sponsorships are excluded."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required to query the public Sponsors GraphQL connection")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "aliasfoxkde-profile-sponsors-refresh",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    query = """
    query($cursor: String) {
      user(login: "aliasfoxkde") {
        sponsorshipsAsMaintainer(first: 100, after: $cursor, activeOnly: true, includePrivate: false) {
          nodes {
            sponsorEntity {
              __typename
              ... on User { login }
              ... on Organization { login }
            }
          }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    sponsors: dict[str, str] = {}
    cursor: str | None = None
    while True:
        payload = json.dumps({"query": query, "variables": {"cursor": cursor}}).encode()
        request = Request(
            "https://api.github.com/graphql",
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                result = json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError(f"GitHub Sponsors API request failed: {error}") from error
        if not isinstance(result, dict) or result.get("errors"):
            raise RuntimeError("GitHub Sponsors API returned an error response")
        user = result.get("data", {}).get("user") if isinstance(result.get("data"), dict) else None
        connection = user.get("sponsorshipsAsMaintainer") if isinstance(user, dict) else None
        if not isinstance(connection, dict) or not isinstance(connection.get("nodes"), list):
            raise RuntimeError("GitHub returned an unexpected Sponsors response")
        for node in connection["nodes"]:
            entity = node.get("sponsorEntity") if isinstance(node, dict) else None
            login = entity.get("login") if isinstance(entity, dict) else None
            if not isinstance(login, str) or not LOGIN_RE.fullmatch(login):
                raise RuntimeError("GitHub returned an invalid public sponsor record")
            sponsors.setdefault(login.casefold(), login)
        page_info = connection.get("pageInfo")
        if not isinstance(page_info, dict) or not isinstance(page_info.get("hasNextPage"), bool):
            raise RuntimeError("GitHub returned invalid Sponsors pagination data")
        if not page_info["hasNextPage"]:
            break
        cursor = page_info.get("endCursor")
        if not isinstance(cursor, str):
            raise RuntimeError("GitHub returned a missing Sponsors pagination cursor")
    return sorted(sponsors.values(), key=str.casefold)


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


def render_sponsors(sponsors: list[str]) -> str:
    if not sponsors:
        return (
            "**0 public sponsors so far.** If you find my open-source work useful, "
            "[sponsor me on GitHub](https://github.com/sponsors/aliasfoxkde). "
            "Thank you for considering it."
        )
    names = ", ".join(
        f'<a href="https://github.com/{html.escape(login, quote=True)}">'
        f"<code>@{html.escape(login)}</code></a>"
        for login in sponsors
    )
    return f"**{len(sponsors)} public sponsor{'s' if len(sponsors) != 1 else ''}** · {names}"


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
    sponsors = fetch_public_sponsors()
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
    if updated.count(SPONSORS_START) != 1 or updated.count(SPONSORS_END) != 1:
        raise RuntimeError("README must contain exactly one start and end sponsor marker")
    sponsors_start = updated.index(SPONSORS_START) + len(SPONSORS_START)
    sponsors_end = updated.index(SPONSORS_END)
    if sponsors_start > sponsors_end:
        raise RuntimeError("README sponsor markers are in the wrong order")
    generated_sponsors = f"\n{render_sponsors(sponsors)}\n"
    updated = updated[:sponsors_start] + generated_sponsors + updated[sponsors_end:]
    if updated == content:
        print(
            f"Profile data already current ({len(followers)} public followers, "
            f"{len(repositories)} public repositories, {len(sponsors)} public sponsors)."
        )
        return False
    README.write_text(updated, encoding="utf-8")
    print(
        f"Updated README with {len(followers)} public followers and "
        f"{len(repositories)} public repositories."
        f" Listed {len(sponsors)} public sponsors."
    )
    return True


if __name__ == "__main__":
    try:
        update_readme()
    except (OSError, RuntimeError) as error:
        print(f"update_profile_followers: {error}", file=sys.stderr)
        sys.exit(1)
