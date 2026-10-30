# Repository settings

Applied 2026-10-30 to the public `aliasfoxkde/aliasfoxkde` profile repository.

- Issues, Discussions, Wiki, Sponsorships, and auto-merge are enabled.
- Pull request branch updates are allowed; merged head branches are deleted.
- Release immutability is enabled for future releases.
- The active `Safeguards` branch ruleset protects the default, `stable/*`, and
  `release/*` branches against deletion and force-push, requires pull requests
  and linear history, and requests Copilot review where the account has access.
- GitHub's auto-close setting for linked issues defaults to enabled. The
  repository REST and GraphQL settings APIs do not expose a control for this
  setting; GitHub documents that merged linked pull requests close issues by
  default.
- CodeQL scanning, code quality, and coverage rules from the Safeguards
  template are deferred because this repository currently contains only
  Markdown and screenshots, with no source code or analysis workflow. Add
  these protections when executable source is introduced.

GitHub's Sponsorships repository feature is enabled. The account does not
currently expose a Sponsors listing, so there is no active sponsorship page
linked from this repository.
