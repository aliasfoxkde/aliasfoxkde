# Project catalog

[projects.json](../projects.json) is the canonical structured inventory for the
GitHub profile and portfolio work. It deliberately separates repository links
from live website links: some gallery entries do not yet have a verified
source-repository mapping.

## Status vocabulary

| Status | Meaning |
|---|---|
| `maintained` | Publicly maintained project with a current, supported release or service |
| `active-development` | Under active implementation; not necessarily release-stable |
| `prototype` | Demonstrates a concept or partial implementation |
| `experimental` | Exploratory work without a support commitment |
| `archived` | No longer actively developed |
| `fork-or-mirror` | Primarily upstream code or a derivative mirror |
| `internal-support` | Deployment, operations, or support repository rather than a product |
| `needs-review` | Maturity or current operating state has not yet been verified |

## Editing rules

- Keep IDs stable; use lowercase kebab-case.
- Do not infer a repository from a similar project name. Leave `repository`
  absent until the mapping is confirmed.
- Do not add a website until the URL has been checked for ownership,
  reachability, TLS, and the expected project.
- Use `needs-review` rather than upgrading maturity based on README language
  alone.
- Keep summaries user-facing and concise. Put technical detail in each
  project's own documentation.
- Update this file first; profile, inventory, and website generators should
  consume it rather than maintaining duplicate project lists.
- Run `python3 scripts/validate-projects.py` before submitting changes.

## Current validation boundary

The manifest is an initial curated catalog, not proof that every deployment
is live or every repository is maintained. Entries marked `needs-review`
require owner verification. A missing repository mapping is intentional where
the live gallery does not yet identify a canonical source repository.
