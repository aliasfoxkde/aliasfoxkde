"""Contract tests for self-hosted language charts in the profile README."""

from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import update_profile_followers as profile


class LanguageChartTests(unittest.TestCase):
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

        pie = ET.fromstring(profile.render_language_mix(repositories))
        radar = ET.fromstring(profile.render_language_radar(repositories))

        self.assertEqual(pie.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(radar.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIn("<script>", "".join(pie.itertext()))
        self.assertEqual(pie.findall(".//{http://www.w3.org/2000/svg}script"), [])
        self.assertIn("repositories", "".join(radar.itertext()))

    def test_empty_data_renders_without_division_errors(self) -> None:
        pie = ET.fromstring(profile.render_language_mix([]))
        radar = ET.fromstring(profile.render_language_radar([]))

        self.assertIn("No data", "".join(pie.itertext()))
        self.assertIn("Shared scale: 0–1 repositories", "".join(radar.itertext()))

    def test_chart_writer_updates_only_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            files = (Path(directory) / "mix.svg", Path(directory) / "radar.svg")
            with patch.object(profile, "CHART_FILES", files):
                self.assertTrue(profile.write_language_charts([{"language": "Rust"}]))
                self.assertTrue(all(path.is_file() for path in files))
                self.assertFalse(profile.write_language_charts([{"language": "Rust"}]))


if __name__ == "__main__":
    unittest.main()
