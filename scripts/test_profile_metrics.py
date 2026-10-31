"""Contract tests for self-hosted profile metrics and charts."""

from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import update_profile_followers as profile


class LanguageChartTests(unittest.TestCase):
    def test_public_projects_are_complete_sorted_and_escaped(self) -> None:
        repositories = [
            {"name": "zeta", "fork": False, "archived": False, "language": "Rust", "description": "<script>"},
            {"name": "forked", "fork": True, "archived": False, "language": "Python", "description": "Fork"},
            {"name": "archived", "fork": False, "archived": True, "language": "Go", "description": "Old"},
            {"name": "alpha", "fork": False, "archived": False, "language": None, "description": None},
        ]

        rendered = profile.render_public_projects(repositories)

        self.assertIn("Show all 3 public project repositories", rendered)
        self.assertLess(rendered.index("/alpha\""), rendered.index("/zeta\""))
        self.assertIn("No description provided.", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("/forked\"", rendered)
        self.assertIn("/archived\"", rendered)
        self.assertIn("<td>Archived</td>", rendered)
        self.assertIn("Ask Copilot", rendered)

    def test_distribution_counts_repositories_and_groups_remainder(self) -> None:
        repositories = [
            {"language": "Rust"},
            {"language": "Rust"},
            {"language": "Python"},
            {"language": "TypeScript"},
            {"language": "Go"},
            {"language": "JavaScript"},
            {"language": "C#"},
            {"language": None},
        ]

        distribution = profile.language_distribution(repositories)

        self.assertEqual(distribution[0][0:2], ("Rust", 2))
        self.assertEqual(distribution[-1][0:2], ("Other / none", 2))
        self.assertEqual(sum(count for _, count, _ in distribution), len(repositories))

    def test_chart_svg_is_well_formed_and_escapes_api_text(self) -> None:
        repositories = [{"language": "<script>"}, {"language": "Rust"}]

        pie = ET.fromstring(
            profile.render_activity_mix(
                {"Commits": 4, "Pull requests": 2, "Issues": 1, "PR reviews": 1, "Repositories created": 1},
                135,
            )
        )
        radar = ET.fromstring(profile.render_language_radar(repositories))
        bars = ET.fromstring(profile.render_language_bars(repositories))

        self.assertEqual(pie.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(radar.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(bars.tag, "{http://www.w3.org/2000/svg}svg")
        pie_text = "".join(pie.itertext())
        self.assertIn("135", pie_text)
        self.assertIn("Pull requests · 2", pie_text)
        self.assertIn("Issues · 1", pie_text)
        self.assertIn("Repositories created · 1", pie_text)
        self.assertIn("last 12 months", pie_text)
        self.assertIn("repositories", "".join(radar.itertext()))
        self.assertIn("<script>", "".join(bars.itertext()))

    def test_bar_chart_ranks_named_languages_and_excludes_remainder(self) -> None:
        repositories = (
            [{"language": "Rust"}] * 4
            + [{"language": "Python"}] * 2
            + [{"language": None}] * 20
        )

        bars = ET.fromstring(profile.render_language_bars(repositories))
        text = "".join(bars.itertext())

        self.assertIn("Rust", text)
        self.assertIn("Python", text)
        self.assertNotIn("Other / none", text)
        self.assertIn("Top languages by repository count", text)

    def test_radar_normalizes_named_languages_and_excludes_remainder(self) -> None:
        repositories = (
            [{"language": "TypeScript"}] * 4
            + [{"language": "Python"}] * 2
            + [{"language": None}] * 20
        )

        radar = ET.fromstring(profile.render_language_radar(repositories))
        text = "".join(radar.itertext())

        self.assertIn("TypeScript · 4 (100%)", text)
        self.assertIn("Python · 2 (50%)", text)
        self.assertNotIn("Other / none", text)
        self.assertIn("100% = max", text)

    def test_public_contribution_fetch_validates_graphql_counts(self) -> None:
        collection = {
            "totalCommitContributions": 12,
            "totalPullRequestContributions": 4,
            "totalIssueContributions": 3,
            "totalPullRequestReviewContributions": 2,
            "totalRepositoryContributions": 1,
        }
        response = BytesIO(json.dumps({"data": {"user": {"contributionsCollection": collection}}}).encode())

        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}),
            patch.object(profile, "urlopen", return_value=response) as open_request,
        ):
            contributions = profile.fetch_public_contributions()

        request = open_request.call_args.args[0]
        payload = json.loads(request.data.decode())
        self.assertEqual(contributions["Commits"], 12)
        self.assertEqual(contributions["Pull requests"], 4)
        self.assertIn("totalPullRequestReviewContributions", payload["query"])
        self.assertEqual(request.full_url, "https://api.github.com/graphql")

    def test_empty_data_renders_without_division_errors(self) -> None:
        pie = ET.fromstring(profile.render_activity_mix({}, 0))
        radar = ET.fromstring(profile.render_language_radar([]))
        bars = ET.fromstring(profile.render_language_bars([]))

        self.assertIn("0 public contributions", "".join(pie.itertext()))
        self.assertIn("Relative to largest named language", "".join(radar.itertext()))
        self.assertIn("No data", "".join(bars.itertext()))

    def test_chart_writer_updates_only_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            files = (
                Path(directory) / "mix.svg",
                Path(directory) / "radar.svg",
                Path(directory) / "bars.svg",
            )
            with patch.object(profile, "CHART_FILES", files):
                contributions = {"Commits": 1}
                self.assertTrue(profile.write_profile_charts([{"language": "Rust"}], contributions))
                self.assertTrue(all(path.is_file() for path in files))
                self.assertFalse(profile.write_profile_charts([{"language": "Rust"}], contributions))


if __name__ == "__main__":
    unittest.main()
