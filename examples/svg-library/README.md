# SVG Profile Library

A small, dependency-free browser generator for profile README artwork. It creates original, downloadable SVG files locally in the browser.

## Included templates

- **Profile header:** choose a visual treatment, display name, subtitle, and accent color.
- **Summary card:** edit three numeric snapshots for repositories, stars, and forks.
- **Pixel snake wordmark:** draw a supported username in a pixel font and animate the moving head.

Open [`index.html`](./index.html) locally or visit the [hosted generator](https://aliasfoxkde.github.io/examples/svg-library/). Edit a template, download the SVG, and copy the Markdown embed. Save the downloaded file in your own repository, for example at `assets/profile-header.svg`, then update the generated image path in your README.

## License and reuse

The library source code uses the [MIT License](../LICENSE). That license does not cover the project screenshots in `../assets/screenshots/`, which depict separate projects and remain subject to their own terms. Generated SVGs contain only the chosen text, values, colors, and vector shapes; there are no external images, fonts, libraries, scripts, API calls, or analytics. Keep the MIT copyright and permission notice when copying substantial portions of the source code. You can use and modify generated artwork freely.

## Data and refresh behavior

The generator has no GitHub credentials and fetches no account data. Summary values are entered by the user and are static snapshots. For auto-updating metrics, connect the template to a scheduled workflow or service that reads only appropriate public fields, documents its refresh interval, and writes a generated SVG. Never expose a token in a browser-side script or public SVG.

GitHub profile READMEs display image files but do not run JavaScript. Therefore the editor itself is interactive, while each exported SVG is a standalone image. SVG animation support can differ between viewers; static shapes and text remain readable if animation is removed.

## Source inspiration

This is an original implementation inspired by public profile patterns in [SuperSupeng](https://github.com/SuperSupeng/SuperSupeng), [mmphego](https://github.com/mmphego/mmphego), and [CyrisXD](https://github.com/CyrisXD/CyrisXD). No source artwork or code is copied from those repositories.
