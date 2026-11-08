"""Load and validate the site content.

Everything shown on the site lives in `content/`. Validation happens here so that a typo
in the YAML fails the build instead of producing a broken card.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

import yaml

GRID_COLUMNS = 12
SPANS = {"large": 7, "medium": 5, "small": 4}
FITS = {"cover", "contain", "native"}
DEMO_PREFIX = "https://huggingface.co/spaces/"


class ContentError(ValueError):
    """The content files are invalid."""


@dataclass(frozen=True)
class Media:
    source: str
    alt: str
    fit: str = "cover"
    position: str = "center"
    frame: float = 0.5  # where in an animation the poster is taken, from 0 to 1


@dataclass(frozen=True)
class Project:
    repo: str
    title: str
    area: str
    size: str
    summary: str
    metric: str
    metric_label: str
    caveat: str
    tags: tuple[str, ...]
    compare: str = ""
    demo: str = ""
    demo_note: str = ""
    media: Media | None = None

    @property
    def url(self) -> str:
        return f"https://github.com/haroonkhan02/{self.repo}"

    @property
    def page_url(self) -> str:
        return f"/projects/{self.repo}/"

    @property
    def span(self) -> int:
        return SPANS[self.size]

    @property
    def claims(self) -> list[str]:
        """The texts whose numbers must be backed by the project's README."""
        texts = [self.summary, self.metric, self.metric_label, self.compare, self.caveat]
        return [text for text in texts + [self.demo_note] if text]


def _build(cls, raw: dict, where: str):
    """Build a dataclass from a mapping, rejecting unknown keys and missing required ones."""
    if not isinstance(raw, dict):
        raise ContentError(f"{where}: expected a mapping")
    known = {f.name for f in fields(cls)}
    unknown = set(raw) - known
    if unknown:
        raise ContentError(f"{where}: unknown keys {sorted(unknown)}")
    try:
        return cls(**raw)
    except TypeError as exc:
        raise ContentError(f"{where}: {exc}") from exc


def parse_project(raw: dict) -> Project:
    where = f"project {raw.get('repo', '?')}" if isinstance(raw, dict) else "project"
    data = dict(raw) if isinstance(raw, dict) else raw
    if isinstance(data, dict):
        if data.get("media") is not None:
            data["media"] = _build(Media, data["media"], f"{where} media")
        data["tags"] = tuple(data.get("tags", ()))
    project = _build(Project, data, where)
    # An unquoted `metric: 0.690` would load as the float 0.69 and lose its trailing zero.
    for name in ("metric", "metric_label", "summary", "compare", "caveat", "demo_note"):
        if not isinstance(getattr(project, name), str):
            raise ContentError(f"{where}: {name} must be a string, quote it in the YAML")
    if project.size not in SPANS:
        raise ContentError(f"{where}: size must be one of {sorted(SPANS)}")
    if project.media and project.media.fit not in FITS:
        raise ContentError(f"{where}: media fit must be one of {sorted(FITS)}")
    if project.media and not 0 <= project.media.frame <= 1:
        raise ContentError(f"{where}: media frame must be between 0 and 1")
    if project.media and not project.media.alt.strip():
        raise ContentError(f"{where}: media needs alt text")
    if project.demo and not project.demo.startswith(DEMO_PREFIX):
        raise ContentError(f"{where}: demo must be a Hugging Face Space URL")
    if bool(project.demo) != bool(project.demo_note):
        raise ContentError(f"{where}: demo and demo_note go together")
    return project


def check_grid(projects: list[Project]) -> None:
    """Every row of the grid must fill all columns exactly, or the layout gets holes."""
    used = 0
    for project in projects:
        used += project.span
        if used > GRID_COLUMNS:
            raise ContentError(f"grid row overflows at {project.repo}")
        if used == GRID_COLUMNS:
            used = 0
    if used:
        raise ContentError("the last grid row is not full")


def load_projects(path: Path) -> list[Project]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ContentError(f"{path}: expected a list of projects")
    projects = [parse_project(item) for item in raw]
    repos = [project.repo for project in projects]
    duplicates = sorted({repo for repo in repos if repos.count(repo) > 1})
    if duplicates:
        raise ContentError(f"duplicate projects: {duplicates}")
    check_grid(projects)
    return projects


@dataclass(frozen=True)
class Results:
    caption: str
    rows: tuple[tuple[str, ...], ...]  # the first row is the header

    @property
    def header(self) -> tuple[str, ...]:
        return self.rows[0]

    @property
    def body(self) -> tuple[tuple[str, ...], ...]:
        return self.rows[1:]


@dataclass(frozen=True)
class Page:
    """The longer write-up shown on a project's own page."""

    problem: str
    approach: tuple[str, ...]
    results: Results
    findings: tuple[str, ...]
    limitations: tuple[str, ...]

    @property
    def claims(self) -> list[str]:
        cells = [cell for row in self.results.rows for cell in row]
        return [
            self.problem,
            *self.approach,
            self.results.caption,
            *cells,
            *self.findings,
            *self.limitations,
        ]


def _strings(value, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ContentError(f"{where}: expected a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ContentError(f"{where}: every item must be a non-empty string, quote numbers")
    return tuple(value)


def parse_page(raw: dict, repo: str) -> Page:
    where = f"page {repo}"
    if not isinstance(raw, dict):
        raise ContentError(f"{where}: expected a mapping")
    data = dict(raw)
    if not isinstance(data.get("problem"), str):
        raise ContentError(f"{where}: problem must be a paragraph of text")
    for name in ("approach", "findings", "limitations"):
        data[name] = _strings(data.get(name), f"{where} {name}")
    table = data.get("results")
    if not isinstance(table, dict) or set(table) != {"caption", "rows"}:
        raise ContentError(f"{where}: results must have a caption and rows, nothing else")
    rows = table.get("rows")
    if not isinstance(rows, list) or len(rows) < 2:
        raise ContentError(f"{where}: results need a header row and at least one data row")
    rows = tuple(_strings(row, f"{where} results row {i}") for i, row in enumerate(rows))
    if len({len(row) for row in rows}) != 1:
        raise ContentError(f"{where}: every results row needs the same number of cells")
    data["results"] = _build(
        Results, {"caption": table.get("caption"), "rows": rows}, f"{where} results"
    )
    if not isinstance(data["results"].caption, str):
        raise ContentError(f"{where}: results caption must be text")
    return _build(Page, data, where)


def load_pages(directory: Path, projects: list[Project]) -> dict[str, Page]:
    """Load one page per project. A missing or orphaned page file is an error."""
    files = {path.stem: path for path in directory.glob("*.yaml")}
    repos = {project.repo for project in projects}
    if missing := sorted(repos - set(files)):
        raise ContentError(f"no page for {missing}")
    if extra := sorted(set(files) - repos):
        raise ContentError(f"pages without a project: {extra}")
    return {
        repo: parse_page(yaml.safe_load(files[repo].read_text(encoding="utf-8")), repo)
        for repo in sorted(repos)
    }


def load_profile(path: Path) -> dict:
    profile = yaml.safe_load(path.read_text(encoding="utf-8"))
    missing = {"name", "role", "headline", "intro", "about", "skills", "links"} - set(profile)
    if missing:
        raise ContentError(f"{path}: missing {sorted(missing)}")
    return profile
