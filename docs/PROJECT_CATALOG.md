# Project catalog

[projects.json](../projects.json) is the curated metadata override catalog for
featured projects and selected live-demo entries. It is not the complete
repository inventory: the profile refresh workflow fetches all public original
repositories directly from GitHub and uses this catalog to override summaries
and maturity labels where an owner-reviewed entry exists.

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
| `needs-review` | Maturity or current operating state has not been verified |

The generated full repository table applies GitHub metadata first:
archived repositories are labeled Archived and zero-size repositories are
labeled Empty / placeholder. Catalog overrides then supply curated maturity
labels and descriptions. Original repositories not yet represented in the
catalog default to Needs review; they are not silently called Active.

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
- Keep the catalog limited to projects whose summary/status should override
  GitHub's generic repository metadata; the full inventory is generated from
  the GitHub API.
- Run `python3 -m unittest discover -s scripts -p 'test_*.py'` before
  submitting changes.

## Current validation boundary

The catalog and generated inventory do not prove that every deployment is
live or every repository is maintained. Website ownership, current behavior,
and maturity remain evidence-based review tasks. A missing repository mapping
is intentional where the canonical source repository has not been confirmed.
