"""Render the site into `dist/`."""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from PIL import Image

from portfolio_site.content import Project, load_profile, load_projects

SITE_URL = "https://haroonkhan02.github.io/"


@dataclass(frozen=True)
class Card:
    """A project plus the media files that exist for it."""

    project: Project
    poster: str = ""
    video: str = ""
    width: int = 0
    height: int = 0


def make_card(project: Project, media_dir: Path) -> Card:
    if project.media is None:
        return Card(project)
    poster = media_dir / f"{project.repo}.webp"
    if not poster.exists():
        raise FileNotFoundError(f"{poster} is missing, run site-media")
    with Image.open(poster) as image:
        width, height = image.size
    video = media_dir / f"{project.repo}.mp4"
    return Card(
        project,
        poster=f"media/{poster.name}",
        video=f"media/{video.name}" if video.exists() else "",
        width=width,
        height=height,
    )


def render(root: Path, out: Path) -> list[Path]:
    """Build the whole site from `root` into `out` and return the pages written."""
    projects = load_projects(root / "content" / "projects.yaml")
    profile = load_profile(root / "content" / "profile.yaml")
    cards = [make_card(project, root / "static" / "media") for project in projects]

    env = Environment(
        loader=FileSystemLoader(root / "templates"),
        autoescape=select_autoescape(["html", "j2"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    context = {
        "profile": profile,
        "cards": cards,
        "demos": [card.project for card in cards if card.project.demo],
        "site_url": SITE_URL,
    }

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(root / "static", out)
    (out / ".nojekyll").touch()

    pages = []
    for template, name in (("index.html.j2", "index.html"), ("404.html.j2", "404.html")):
        page = out / name
        page.write_text(env.get_template(template).render(context), encoding="utf-8")
        pages.append(page)
    return pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    for page in render(args.root, args.out):
        print(f"{page}  {page.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
