"""Check the published claims against the projects themselves.

Every number on a card must appear in that project's README, so a retrained model or an
edited README can't silently leave the site out of date. It catches a number that is no
longer there, not a number attached to the wrong label, so it backs up a read-through
rather than replacing it.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from portfolio_site.content import Project, load_projects

RAW_README = "https://raw.githubusercontent.com/haroonkhan02/{repo}/main/README.md"
USER_AGENT = "portfolio-site-verify"
NUMBER = re.compile(r"(?<![\w.@])\d+(?:[.,]\d+)*")


def numbers_in(text: str) -> set[str]:
    """Numeric tokens in a text, skipping digits inside names such as `MRR@10` or `YOLO11`."""
    return set(NUMBER.findall(text))


def missing_numbers(project: Project, readme: str) -> list[str]:
    """Numbers claimed for a project that its README does not contain."""
    found = numbers_in(readme)
    claimed = set().union(*(numbers_in(text) for text in project.claims))
    return sorted(claimed - found)


def local_reader(repos_dir: Path) -> Callable[[str], str]:
    def read(repo: str) -> str:
        return (repos_dir / repo / "README.md").read_text(encoding="utf-8")

    return read


def remote_reader(repo: str) -> str:
    request = urllib.request.Request(
        RAW_README.format(repo=repo), headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def url_status(url: str) -> int:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def verify(projects: list[Project], read: Callable[[str], str]) -> dict[str, list[str]]:
    """Map each project with unbacked numbers to those numbers."""
    problems = {project.repo: missing_numbers(project, read(project.repo)) for project in projects}
    return {repo: numbers for repo, numbers in problems.items() if numbers}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--content", type=Path, default=Path("content/projects.yaml"))
    parser.add_argument(
        "--repos-dir", type=Path, help="folder with local clones (default: read from GitHub)"
    )
    parser.add_argument("--links", action="store_true", help="also request every project link")
    args = parser.parse_args(argv)

    projects = load_projects(args.content)
    read = local_reader(args.repos_dir) if args.repos_dir else remote_reader
    problems = verify(projects, read)
    for repo, numbers in problems.items():
        print(f"{repo}: not in README: {', '.join(numbers)}")

    broken = []
    if args.links:
        urls = [url for p in projects for url in (p.url, p.demo) if url]
        broken = [(url, status) for url in urls if (status := url_status(url)) != 200]
        for url, status in broken:
            print(f"{url}: HTTP {status}")

    print(f"{len(projects)} projects checked, {len(problems)} with unbacked numbers")
    return 1 if problems or broken else 0


if __name__ == "__main__":
    sys.exit(main())
