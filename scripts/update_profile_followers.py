#!/usr/bin/env python3
"""Refresh public profile followers, repository metrics, and sponsors."""

from __future__ import annotations

import html
import json
import math
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
LANGUAGE_COLORS = {
    "Rust": "#d97645",
    "TypeScript": "#377cc8",
    "JavaScript": "#d3a81e",
    "Python": "#568b54",
    "HTML": "#d65c42",
    "CSS": "#8059c5",
    "Go": "#35a4b8",
    "Java": "#b65e36",
    "C#": "#68217a",
    "C++": "#f34b7d",
    "Shell": "#4eaa25",
    "Other / none": "#8b849c",
}
CHART_COLORS = ("#6748c7", "#287b68", "#d97645", "#377cc8", "#d3a81e", "#8b849c")
CHART_FILES = (
    Path(__file__).resolve().parents[1] / "assets" / "profile-language-mix.svg",
    Path(__file__).resolve().parents[1] / "assets" / "profile-language-radar.svg",
)


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
            language = record.get("language")
            if language is not None and not isinstance(language, str):
                raise RuntimeError(f"GitHub returned an invalid primary language on page {page}")
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


def language_distribution(repositories: list[dict[str, object]]) -> list[tuple[str, int, str]]:
    counts: dict[str, int] = {}
    no_language = 0
    for repository in repositories:
        language = repository.get("language")
        if language is None:
            no_language += 1
        elif isinstance(language, str) and language.strip():
            counts[language.strip()] = counts.get(language.strip(), 0) + 1
        else:
            no_language += 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
    selected = ranked[:5]
    remaining = sum(count for _, count in ranked[5:]) + no_language
    items = [
        (name, count, LANGUAGE_COLORS.get(name, CHART_COLORS[index % len(CHART_COLORS)]))
        for index, (name, count) in enumerate(selected)
    ]
    if remaining or not items:
        items.append(("Other / none", remaining, LANGUAGE_COLORS["Other / none"]))
    return items


def render_language_mix(repositories: list[dict[str, object]]) -> str:
    """Render repository primary-language counts as a self-contained SVG donut."""
    items = language_distribution(repositories)
    total = sum(count for _, count, _ in items)
    circumference = 2 * math.pi * 69
    segments: list[str] = []
    legend: list[str] = []
    offset = 0.0
    for index, (name, count, color) in enumerate(items):
        fraction = count / total if total else 0
        length = circumference * fraction
        if length:
            segments.append(
                f'<circle cx="112" cy="126" r="69" fill="none" stroke="{color}" '
                f'stroke-width="27" stroke-dasharray="{length:.2f} {circumference:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 112 126)"/>'
            )
        offset += length
        legend.append(
            f'<circle cx="250" cy="{69 + index * 27}" r="5" fill="{color}"/>'
            f'<text x="263" y="{73 + index * 27}" font-size="12" fill="#433d51">'
            f'{html.escape(name)} · {count}</text>'
        )
    center = f'<text x="112" y="122" text-anchor="middle" font-size="25" font-weight="750" fill="#211b37">{total}</text><text x="112" y="143" text-anchor="middle" font-size="11" fill="#625c75">repositories</text>'
    if not total:
        center = '<text x="112" y="130" text-anchor="middle" font-size="12" fill="#625c75">No data</text>'
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 260" role="img" aria-labelledby="title desc">'
        '<title id="title">Primary languages across public repositories</title>'
        '<desc id="desc">Donut chart showing each repository counted once by its primary language label. This is not a code-volume or skill measure.</desc>'
        '<rect width="440" height="260" rx="16" fill="#f7f6ff" stroke="#ded9ef"/>'
        '<text x="22" y="31" font-size="15" font-weight="700" fill="#211b37">Primary language mix</text>'
        '<circle cx="112" cy="126" r="69" fill="none" stroke="#e5e1ed" stroke-width="27"/>'
        f'{"".join(segments)}{center}{"".join(legend)}'
        '<text x="22" y="241" font-size="10" fill="#625c75">One count per public repository · top five plus remainder</text>'
        '</svg>'
    )


def render_language_radar(repositories: list[dict[str, object]]) -> str:
    """Render the same repository-count categories on a shared-scale radar chart."""
    items = language_distribution(repositories)
    if len(items) < 3:
        items = items + [(f"Category {i + 1}", 0, CHART_COLORS[i % len(CHART_COLORS)]) for i in range(3 - len(items))]
    cx, cy, radius = 220.0, 151.0, 82.0
    maximum = max((count for _, count, _ in items), default=0) or 1
    angles = [(-math.pi / 2) + 2 * math.pi * index / len(items) for index in range(len(items))]

    def points(scale: float) -> str:
        return " ".join(
            f"{cx + math.cos(angle) * radius * scale:.1f},{cy + math.sin(angle) * radius * scale:.1f}"
            for angle in angles
        )

    grid = "".join(
        f'<polygon points="{points(level / 4)}" fill="none" stroke="#d8d3e4" stroke-width="1"/>'
        for level in range(1, 5)
    )
    axes = "".join(
        f'<line x1="{cx}" y1="{cy}" x2="{cx + math.cos(angle) * radius:.1f}" '
        f'y2="{cy + math.sin(angle) * radius:.1f}" stroke="#d8d3e4"/>'
        for angle in angles
    )
    values = " ".join(
        f"{cx + math.cos(angle) * radius * count / maximum:.1f},{cy + math.sin(angle) * radius * count / maximum:.1f}"
        for angle, (_, count, _) in zip(angles, items)
    )
    labels: list[str] = []
    for angle, (name, count, _) in zip(angles, items):
        x = cx + math.cos(angle) * (radius + 25)
        y = cy + math.sin(angle) * (radius + 25) + 4
        anchor = "start" if math.cos(angle) > 0.35 else "end" if math.cos(angle) < -0.35 else "middle"
        short_name = name if len(name) <= 14 else f"{name[:12]}…"
        labels.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="10" fill="#433d51">'
            f'{html.escape(short_name)} · {count}</text>'
        )
    dots = "".join(
        f'<circle cx="{cx + math.cos(angle) * radius * count / maximum:.1f}" '
        f'cy="{cy + math.sin(angle) * radius * count / maximum:.1f}" r="3.5" fill="#6748c7"/>'
        for angle, (_, count, _) in zip(angles, items)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 260" role="img" aria-labelledby="title desc">'
        '<title id="title">Repository primary-language breadth</title>'
        '<desc id="desc">Radar chart of repository counts by primary language category on one shared scale. It does not represent skill or code volume.</desc>'
        '<rect width="440" height="260" rx="16" fill="#f7f6ff" stroke="#ded9ef"/>'
        '<text x="22" y="31" font-size="15" font-weight="700" fill="#211b37">Language breadth by repositories</text>'
        f'{grid}{axes}<polygon points="{values}" fill="#6748c7" fill-opacity=".17" stroke="#6748c7" stroke-width="2"/>{dots}{"".join(labels)}'
        f'<text x="220" y="247" text-anchor="middle" font-size="10" fill="#625c75">Shared scale: 0–{maximum} repositories</text>'
        '</svg>'
    )


def write_language_charts(repositories: list[dict[str, object]]) -> bool:
    charts = (render_language_mix(repositories), render_language_radar(repositories))
    changed = False
    for path, content in zip(CHART_FILES, charts):
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            changed = True
    return changed


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
    charts_changed = write_language_charts(repositories)
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
    readme_changed = updated != content
    if not readme_changed and not charts_changed:
        print(
            f"Profile data already current ({len(followers)} public followers, "
            f"{len(repositories)} public repositories, {len(sponsors)} public sponsors)."
        )
        return False
    if readme_changed:
        README.write_text(updated, encoding="utf-8")
    print(
        f"Updated README with {len(followers)} public followers and "
        f"{len(repositories)} public repositories."
        f" Listed {len(sponsors)} public sponsors."
        f" Language charts {'updated' if charts_changed else 'already current'}."
    )
    return readme_changed or charts_changed


if __name__ == "__main__":
    try:
        update_readme()
    except (OSError, RuntimeError) as error:
        print(f"update_profile_followers: {error}", file=sys.stderr)
        sys.exit(1)
