# Repository settings

Applied 2026-10-30 to the public `aliasfoxkde/aliasfoxkde` profile repository.

- Issues, Discussions, Wiki, Sponsorships, and auto-merge are enabled.
- Pull request branch updates are allowed; merged head branches are deleted.
- Release immutability is enabled for future releases.
- The active `Safeguards` branch ruleset protects the default, `stable/*`, and
  `release/*` branches against deletion and force-push, requires pull requests
  and linear history, requests Copilot review, requires the `validate` status,
  and applies CodeQL scanning at all alert thresholds.
- GitHub's auto-close setting for linked issues defaults to enabled. The
  repository REST and GraphQL settings APIs do not expose a way to read or set
  the override. GitHub documents that linked issues close by default, but the
  setting itself could not be verified through the available API.
- Code Quality and coverage rules from the Safeguards template are omitted.
  This repository has a small metrics updater and contract tests, but its
  workflow does not publish a coverage report or a Code Quality signal for
  GitHub to enforce. Add those gates when the necessary reports and a suitable
  baseline are in place; do not claim these two rules are active today.

GitHub's Sponsorships repository feature is enabled. The account does not
currently expose a Sponsors listing, so there is no active sponsorship page
linked from this repository.
