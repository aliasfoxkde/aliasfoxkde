#!/usr/bin/env python3
"""Refresh public profile followers, repository metrics, and sponsors."""

from __future__ import annotations

import html
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

OWNER = "aliasfoxkde"
README = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- profile-followers:start -->"
END = "<!-- profile-followers:end -->"
SPONSORS_START = "<!-- profile-sponsors:start -->"
SPONSORS_END = "<!-- profile-sponsors:end -->"
STATS_START = "<!-- profile-stats:start -->"
STATS_END = "<!-- profile-stats:end -->"
PROJECTS_START = "<!-- profile-projects:start -->"
PROJECTS_END = "<!-- profile-projects:end -->"
PER_PAGE = 100
LOGIN_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")
REPOSITORY_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
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
    Path(__file__).resolve().parents[1] / "assets" / "profile-activity-mix.svg",
    Path(__file__).resolve().parents[1] / "assets" / "profile-language-radar.svg",
    Path(__file__).resolve().parents[1] / "assets" / "profile-language-bars.svg",
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
            if (
                not isinstance(record, dict)
                or not isinstance(record.get("fork"), bool)
                or not isinstance(record.get("archived"), bool)
            ):
                raise RuntimeError(f"GitHub returned an invalid repository record on page {page}")
            if record.get("private") is True:
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


def fetch_public_contributions() -> dict[str, int]:
    """Fetch public contribution totals over the rolling 12-month window."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required to query public contribution totals")
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365)
    query = """
    query($from: DateTime!, $to: DateTime!) {
      user(login: "aliasfoxkde") {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
          totalPullRequestReviewContributions
          totalRepositoryContributions
        }
      }
    }
    """
    payload = json.dumps(
        {"query": query, "variables": {"from": start.isoformat(), "to": end.isoformat()}}
    ).encode()
    request = Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "aliasfoxkde-profile-contribution-refresh",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"GitHub contribution API request failed: {error}") from error
    if not isinstance(result, dict) or result.get("errors"):
        raise RuntimeError("GitHub contribution API returned an error response")
    user = result.get("data", {}).get("user") if isinstance(result.get("data"), dict) else None
    collection = user.get("contributionsCollection") if isinstance(user, dict) else None
    if not isinstance(collection, dict):
        raise RuntimeError("GitHub returned an unexpected contribution response")
    fields = {
        "Commits": "totalCommitContributions",
        "Pull requests": "totalPullRequestContributions",
        "Issues": "totalIssueContributions",
        "PR reviews": "totalPullRequestReviewContributions",
        "Repositories created": "totalRepositoryContributions",
    }
    contributions: dict[str, int] = {}
    for label, key in fields.items():
        value = collection.get(key)
        if not isinstance(value, int) or value < 0:
            raise RuntimeError(f"GitHub returned an invalid {key} contribution count")
        contributions[label] = value
    return contributions


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


def render_public_projects(repositories: list[dict[str, object]]) -> str:
    """Render every public original repository, including archived projects."""
    projects = sorted(
        (
            repository
            for repository in repositories
            if repository.get("fork") is False
        ),
        key=lambda repository: str(repository.get("name", "")).casefold(),
    )
    rows: list[str] = []
    prompt = "Give me a concise overview of this repository: its purpose, key components, technologies, and how to get started."
    for repository in projects:
        name = repository.get("name")
        if not isinstance(name, str) or not REPOSITORY_NAME_RE.fullmatch(name):
            raise RuntimeError("GitHub returned an invalid public repository name")
        description = repository.get("description")
        if description is not None and not isinstance(description, str):
            raise RuntimeError(f"GitHub returned an invalid description for {name}")
        language = repository.get("language")
        if language is not None and not isinstance(language, str):
            raise RuntimeError(f"GitHub returned an invalid language for {name}")
        copilot_open = (
            f"ghapp://session/new?repo={quote(f'{OWNER}/{name}', safe='')}"
            f"&mode=interactive&prompt={quote(prompt, safe='')}"
        )
        copilot_url = quote(copilot_open, safe="")
        safe_name = html.escape(name, quote=True)
        safe_language = html.escape(language or "—")
        safe_description = html.escape(description or "No description provided.")
        status = "Archived" if repository.get("archived") is True else "Active"
        rows.append(
            "    <tr>"
            f'<td><a href="https://github.com/{OWNER}/{safe_name}">{safe_name}</a> · '
            f'<a href="https://github.com/copilot/app/launch?open={copilot_url}">Ask Copilot</a></td>'
            f"<td>{safe_language}</td><td>{status}</td><td>{safe_description}</td></tr>"
        )
    if not rows:
        rows.append('    <tr><td colspan="4">No public project repositories found.</td></tr>')
    summary = f"Show all {len(projects)} public project repositories"
    return (
        "<details>\n"
        f"  <summary>{summary}</summary>\n\n"
        "<p>Refreshed daily from public GitHub data. Lists original repositories (not forks), including archived projects; licensing and maintenance status are defined per repository.</p>\n\n"
        "<table>\n"
        "  <thead><tr><th>Project</th><th>Primary language</th><th>Status</th><th>About</th></tr></thead>\n"
        "  <tbody>\n"
        + "\n".join(rows)
        + "\n  </tbody>\n</table>\n</details>"
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


def render_activity_mix(contributions: dict[str, int], public_repository_total: int) -> str:
    """Render public contribution activity by type, with the public repo total at center."""
    colors = {
        "Commits": "#6748c7",
        "Pull requests": "#287b68",
        "Issues": "#d97645",
        "PR reviews": "#377cc8",
        "Repositories created": "#d3a81e",
    }
    items = [(name, contributions.get(name, 0), color) for name, color in colors.items()]
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
            f'<text x="263" y="{69 + index * 27}" font-size="11" fill="#433d51">'
            f'{html.escape(name)} · {count}</text>'
        )
    center = f'<text x="112" y="122" text-anchor="middle" font-size="24" font-weight="750" fill="#211b37">{public_repository_total}</text><text x="112" y="143" text-anchor="middle" font-size="10" fill="#625c75">public repos</text>'
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 260" role="img" aria-labelledby="title desc">'
        '<title id="title">Public GitHub contributions by type over the last 12 months</title>'
        '<desc id="desc">Donut chart showing public commits, pull requests, issues, pull request reviews, and repositories created over a rolling 12-month period. The center shows the current total public repository count.</desc>'
        '<rect width="440" height="260" rx="16" fill="#f7f6ff" stroke="#ded9ef"/>'
        '<text x="22" y="31" font-size="15" font-weight="700" fill="#211b37">Public GitHub activity · 12 months</text>'
        '<circle cx="112" cy="126" r="69" fill="none" stroke="#e5e1ed" stroke-width="27"/>'
        f'{"".join(segments)}{center}{"".join(legend)}'
        f'<text x="22" y="241" font-size="10" fill="#625c75">{total} public contributions · rolling 12-month window</text>'
        '</svg>'
    )


def render_language_radar(repositories: list[dict[str, object]]) -> str:
    """Render named language counts normalized to the largest named category."""
    # "Other / none" combines unrelated data and can dwarf named languages, so
    # omit it from comparisons that imply each spoke is one named language.
    items = [item for item in language_distribution(repositories) if item[0] != "Other / none"]
    if len(items) < 3:
        items = items + [(f"Category {i + 1}", 0, CHART_COLORS[i % len(CHART_COLORS)]) for i in range(3 - len(items))]
    cx, cy, radius = 220.0, 143.0, 67.0
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
        x = cx + math.cos(angle) * (radius + 22)
        y = cy + math.sin(angle) * (radius + 22) + 4
        anchor = "start" if math.cos(angle) > 0.35 else "end" if math.cos(angle) < -0.35 else "middle"
        short_name = name if len(name) <= 14 else f"{name[:12]}…"
        relative = round(count * 100 / maximum) if count else 0
        labels.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="9" fill="#433d51">'
            f'{html.escape(short_name)} · {count} ({relative}%)</text>'
        )
    dots = "".join(
        f'<circle cx="{cx + math.cos(angle) * radius * count / maximum:.1f}" '
        f'cy="{cy + math.sin(angle) * radius * count / maximum:.1f}" r="3.5" fill="#6748c7"/>'
        for angle, (_, count, _) in zip(angles, items)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 260" role="img" aria-labelledby="title desc">'
        '<title id="title">Repository primary-language breadth</title>'
        '<desc id="desc">Named language repository counts normalized from zero to 100 percent of the largest named language count. Other and unlabeled repositories are excluded. This does not represent skill or code volume.</desc>'
        '<rect width="440" height="260" rx="16" fill="#f7f6ff" stroke="#ded9ef"/>'
        '<text x="22" y="31" font-size="15" font-weight="700" fill="#211b37">Named language counts · normalized</text>'
        f'{grid}{axes}<polygon points="{values}" fill="#6748c7" fill-opacity=".17" stroke="#6748c7" stroke-width="2"/>{dots}{"".join(labels)}'
        '<text x="220" y="250" text-anchor="middle" font-size="10" fill="#625c75">Relative to largest named language · 100% = max</text>'
        '</svg>'
    )


def render_language_bars(repositories: list[dict[str, object]]) -> str:
    """Render the five most common named repository languages as ranked bars."""
    items = [item for item in language_distribution(repositories) if item[0] != "Other / none"]
    maximum = max((count for _, count, _ in items), default=0)
    left, top, bar_width, row_height = 112.0, 67.0, 272.0, 32.0
    rows: list[str] = []
    for index, (name, count, color) in enumerate(items):
        y = top + index * row_height
        width = bar_width * count / maximum if maximum else 0
        rows.append(
            f'<text x="100" y="{y + 15:.1f}" text-anchor="end" font-size="11" fill="#433d51">'
            f'{html.escape(name)}</text>'
            f'<rect x="{left:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="19" rx="5" fill="#e5e1ed"/>'
            f'<rect x="{left:.1f}" y="{y:.1f}" width="{width:.1f}" height="19" rx="5" fill="{color}"/>'
            f'<text x="{left + bar_width + 8:.1f}" y="{y + 15:.1f}" font-size="11" font-weight="700" fill="#433d51">{count}</text>'
        )
    if not items:
        rows.append('<text x="220" y="145" text-anchor="middle" font-size="12" fill="#625c75">No data</text>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 260" role="img" aria-labelledby="title desc">'
        '<title id="title">Most common named primary languages</title>'
        '<desc id="desc">Ranked horizontal bars show the repository count for each of up to five most common named primary languages. Other and unlabeled repositories are excluded.</desc>'
        '<rect width="440" height="260" rx="16" fill="#f7f6ff" stroke="#ded9ef"/>'
        '<text x="22" y="31" font-size="15" font-weight="700" fill="#211b37">Top languages by repository count</text>'
        f'{"".join(rows)}'
        '<text x="22" y="242" font-size="10" fill="#625c75">One count per public repository · top five named languages</text>'
        '</svg>'
    )


def write_profile_charts(
    repositories: list[dict[str, object]], contributions: dict[str, int]
) -> bool:
    charts = (
        render_activity_mix(contributions, len(repositories)),
        render_language_radar(repositories),
        render_language_bars(repositories),
    )
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
    contributions = fetch_public_contributions()
    charts_changed = write_profile_charts(repositories, contributions)
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
    if updated.count(PROJECTS_START) != 1 or updated.count(PROJECTS_END) != 1:
        raise RuntimeError("README must contain exactly one start and end project marker")
    projects_start = updated.index(PROJECTS_START) + len(PROJECTS_START)
    projects_end = updated.index(PROJECTS_END)
    if projects_start > projects_end:
        raise RuntimeError("README project markers are in the wrong order")
    projects = f"\n{render_public_projects(repositories)}\n"
    updated = updated[:projects_start] + projects + updated[projects_end:]
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
        f" Listed {sum(repository.get('fork') is False for repository in repositories)} public project repositories."
        f" Listed {len(sponsors)} public sponsors."
        f" Profile charts {'updated' if charts_changed else 'already current'}."
    )
    return readme_changed or charts_changed


if __name__ == "__main__":
    try:
        update_readme()
    except (OSError, RuntimeError) as error:
        print(f"update_profile_followers: {error}", file=sys.stderr)
        sys.exit(1)
