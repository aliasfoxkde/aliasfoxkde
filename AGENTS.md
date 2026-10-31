# Agent guidance

This repository contains the public profile README, its screenshots, cloneable examples, and a scheduled updater for public GitHub metrics. Changes are visible to anyone who views the profile.

## Public data and secrets

- Never put private organization names, private repository data, prompts, tokens, or account secrets in the README, charts, logs, or committed assets.
- Generated metrics may use only the public GitHub API and the public Sponsors connection with `includePrivate: false`.
- Store credentials only in GitHub Actions secrets or the workflow token. Never print a token or embed one in a badge URL.
- Public organization membership is managed in GitHub account settings. Keep the README organization links aligned with the public memberships.

## Generated content

- `scripts/update_profile_followers.py` owns the `profile-followers`, `profile-stats`, `profile-sponsors`, and `profile-projects` marker regions plus the contribution-mix and language-chart SVG files in `assets/`.
- Stats count public repository records; the donut shows public contribution types over the rolling 12-month window, while the radar and bars count primary-language labels per repository. None of these charts measure code volume, proficiency, or time spent.
- Preserve explicit sample/live labels and keep chart SVG output escaped, deterministic, and valid XML.
- Keep screenshot alt text descriptive. Do not treat the root MIT license as overriding the separate licenses of project screenshots.
- Keep `examples/` self-contained and runnable from a clone with browser-native HTML, CSS, JavaScript, and SVG. Keep its local assets in the folder, label illustrative data, and preserve the separate `examples/LICENSE` scope, which does not cover project screenshots.
- Keep this root `AGENTS.md` useful to contributors and coding agents. Link it from the README so people discovering the repository know the guidance is included in a clone.

## Validation

Run `python3 -m unittest discover -s scripts -p 'test_*.py'` and `python3 -m py_compile scripts/update_profile_followers.py`. When changing README layout, render it through GitHub Flavored Markdown or review the public profile. The scheduled workflow opens/updates a PR and auto-merges only after repository protections pass.

The repository's active `Safeguards` ruleset requires the `validate` status check on `main`. `validate-profile.yml` runs on branch pushes and explicit dispatches; it deliberately does not use `pull_request`, because PRs created by `GITHUB_TOKEN` make those runs approval-required. The scheduled updater dispatches both validation and CodeQL against the exact generated commit and waits for success before creating or updating its PR. The repository Actions setting allowing `GITHUB_TOKEN` to create/approve pull requests is enabled because this automation uses the built-in token; its default permissions remain read-only, and only the updater job has the scoped write permissions it needs. The workflow does not submit approvals.
