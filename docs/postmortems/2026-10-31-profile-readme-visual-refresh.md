# Profile README visual refresh post-mortem

**Date:** 2026-10-31  
**Scope:** PRs [#22](https://github.com/aliasfoxkde/aliasfoxkde/pull/22), [#23](https://github.com/aliasfoxkde/aliasfoxkde/pull/23), and [#24](https://github.com/aliasfoxkde/aliasfoxkde/pull/24).

## Outcome

The profile now uses a static responsive project gallery, a collapsible table of all 33 public original repositories (forks excluded, archived status shown), and three generated charts. The donut shows public contribution counts over a rolling 12-month window and the current public repository total; the radar and bars show primary-language repository counts. The updater, tests, generated SVG assets, refresh workflow, and validation workflow were updated together. All three PRs merged after required checks passed.

The contribution values were fetched from GitHub's `ContributionsCollection` and verified live: 2,143 commits, 768 pull requests, 31 issues, 3 reviews, and 54 repository creations for the observed rolling window; the center showed 135 public repositories. GitHub documents these fields in its [GraphQL Users reference](https://docs.github.com/en/graphql/reference/users). Private/internal contributions require the optional `read:user` scope; the updater does not request that scope.

## What went well

- Changes were isolated on branches, reviewed through PRs, and merged only after `validate` and CodeQL completed successfully.
- Metrics stayed dynamic: the project list and charts are generated from public GitHub APIs rather than maintained as hand-edited snapshots.
- The contribution query validates response shape and nonnegative counts; SVGs are parsed as XML and contract tests cover empty data, escaped repository labels, and chart output.
- The repository list states its inclusion rules and labels archived repositories instead of implying that every public repository is actively maintained or licensed alike.
- Generated-asset validation used Python's XML parser when `xmllint` was unavailable, so validation continued with an equivalent check.

## What went poorly

- The first flip-card revert focused on README links and did not remove the actual hover/button interaction from `examples/projects.html`. I should have traced the rendered experience to its source page before editing.
- I proposed a third language chart while the donut and radar already covered languages. That added redundancy; the user had to redirect the chart toward contribution and repository stats.
- The initial project-table expansion omitted archived repositories because the updater had already filtered them out. I should have stated and checked the inclusion rule before calling the list complete.
- Renaming the donut asset required coordinated edits in the updater, README, refresh workflow, and validation workflow. Those paths are duplicated and remain vulnerable to future drift.
- The contribution SVG was checked as XML and its live values were verified, but a browser screenshot was not captured. The visual layout therefore had less evidence than the gallery layout.

## Learnings and next steps

1. Trace a visual request from the README link through the actual page/component before deciding what “revert” or “change” means.
2. Define the purpose and meaning of adjacent charts before adding another one. The contribution donut currently presents contribution *types*; commits associated with pull requests can make category totals overlap, so do not describe the slices as unique tasks or unique work. A stat-card or bar layout may communicate raw counts more clearly in a future redesign.
3. Keep generated-asset paths aligned across README references, refresh staging, and validation. This post-mortem adds a contract test that fails if one of those references drifts; a single generated manifest may reduce the remaining duplication later.
4. For generated visuals, record both structural checks (XML, data labels, alt text) and a browser-rendered artifact when the environment permits. Clearly mark a visual check as unverified when no artifact was captured.
5. Keep metric provenance, visibility, and time windows in the chart labels and notes. Public contribution totals and current repository totals are different measures; the chart labels them separately.

## Evidence and status

- PR #22 merged as `3b59ea7`; PR #23 as `92f85db`; PR #24 as `6e4ae8d`.
- PR #24's local contract suite passed 8 tests; required GitHub validation and CodeQL checks passed.
- The public contribution GraphQL query and SVG XML parsing were exercised directly. The contribution chart's browser appearance was not captured during this work.
- Follow-up: capture a browser render for the activity chart when the preview tooling is available.
