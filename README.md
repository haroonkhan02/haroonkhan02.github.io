<div align="center">

# haroonkhan02.github.io

Source of my portfolio site: **[haroonkhan02.github.io](https://haroonkhan02.github.io/)**

[![CI](https://github.com/haroonkhan02/haroonkhan02.github.io/actions/workflows/ci.yml/badge.svg)](https://github.com/haroonkhan02/haroonkhan02.github.io/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

A small static site generated with Python and Jinja2 from YAML files in `content/`, deployed
to GitHub Pages by CI. The projects themselves live in their own repos, linked from the site.

## Run locally

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
.venv/bin/site-build
.venv/bin/python -m http.server 8000 --directory dist
```

## License

Code is [MIT](LICENSE) © 2026 Muhammad Haroon Khan. Geist fonts are under the
[SIL Open Font License](static/fonts/OFL.txt).
