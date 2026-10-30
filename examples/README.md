# Profile examples

This folder contains small, original examples for a GitHub profile README and hosted portfolio. Clone this repository to get the complete source and local assets. The pages are plain HTML, CSS, JavaScript, and SVG; there is no package manager or build step. Repository-level contributor and agent instructions are in [`../AGENTS.md`](../AGENTS.md).

## Pages

- [`index.html`](./index.html) — sample profile stats, donut/radar/bar charts, and a pixel snake wordmark. Its numbers are fictional and stay in the browser.
- [`creative.html`](./creative.html) — tags, a project table, original inline SVG icons, text art, a banner concept, a browser-only tic-tac-toe game, and a native collapsible disclosure.
- [`projects.html`](./projects.html) — responsive screenshot cards. Mouse hover flips a card; buttons provide the same interaction to touch and keyboard users. Descriptions and links live on each card's back.
- [`svg-library/`](./svg-library/) — customize a profile header, repository-summary card, or pixel wordmark and download the result as SVG.
- [`about.html`](./about.html) — design references, data definitions, privacy, licensing, and operational caveats.
- [`assets/screenshots/`](./assets/screenshots/) — optimized WebP copies used by the flip-card gallery. These illustrate separate projects and are not automatically covered by this repository's MIT license.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000/examples/`. All preview images load from this cloned repository. Live project links on the cards leave the local site and open their respective public demos or source repositories. The [hosted gallery](https://aliasfoxkde.github.io/examples/) is the same set of examples published from the companion Pages repository.

## Data and reuse

The gallery uses original implementation and illustrative data; it does not call GitHub APIs, require a token, or include analytics. The SVG generator builds output locally in the browser. Exported metrics remain snapshots unless a user supplies a separate refresh workflow. The repository is MIT-licensed; retain the license notice when copying substantial source. Linked profile repositories are references, not permission to reuse their individual graphics or code.
