<div align="center">

# haroonkhan02.github.io

Source of my portfolio site: one static page generated from a content file, with every
published number checked against the project it came from.

[![CI](https://github.com/haroonkhan02/haroonkhan02.github.io/actions/workflows/ci.yml/badge.svg)](https://github.com/haroonkhan02/haroonkhan02.github.io/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

Work in progress. The home page works: twelve project cards with results and limitations,
the five browser demos, and about and contact sections. A page per project is next.

## How it works

- `content/` holds everything shown on the site. `site-build` renders it with Jinja2 into
  `dist/`, and GitHub Actions deploys that folder to Pages.
- `site-verify` reads each project's README and fails if a number on its card is missing,
  so a retrained model can't leave the site out of date. It runs before every deploy.
- `site-media` turns the source GIFs into WebP posters and short H.264 clips, which load only
  when a mouse user hovers a card.

## Getting started

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
.venv/bin/pytest -q
.venv/bin/site-build
.venv/bin/python -m http.server 8000 --directory dist
```

`site-media` also needs ffmpeg and local clones of the project repos next to this folder.

## License

Code is [MIT](LICENSE) © 2026 Muhammad Haroon Khan. Geist and Geist Mono are under the
[SIL Open Font License](static/fonts/OFL.txt).
