import re
from pathlib import Path

import pytest
from test_build import Page

from portfolio_site.build import SITE_URL, render
from portfolio_site.content import load_pages, load_projects

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = load_projects(ROOT / "content" / "projects.yaml")


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    out = tmp_path_factory.mktemp("site") / "dist"
    render(ROOT, out)
    return out


def parsed(path):
    page = Page()
    html = path.read_text(encoding="utf-8")
    page.feed(html)
    return html, page


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.repo)
def test_project_page_is_complete(out, project):
    html, page = parsed(out / project.page_url.strip("/") / "index.html")
    content = load_pages(ROOT / "content" / "pages", PROJECTS)[project.repo]
    assert page.h1 == 1
    assert project.url in html
    assert project.metric in html
    assert html.count("<tr>") == len(content.results.rows)
    assert page.canonical == SITE_URL.rstrip("/") + project.page_url
    for asset in page.assets:
        assert (out / asset.lstrip("/")).is_file(), asset


def test_internal_links_resolve(out):
    for path in [out / "index.html", *out.glob("projects/*/index.html")]:
        _, page = parsed(path)
        for link in page.links:
            if link.startswith("/"):
                target = out / link.split("#")[0].lstrip("/")
                assert (target / "index.html" if target.is_dir() else target).is_file(), link


def test_pager_visits_every_project_once(out):
    seen, url = [], PROJECTS[0].page_url
    for _ in PROJECTS:
        seen.append(url)
        html, _ = parsed(out / url.strip("/") / "index.html")
        url = re.search(r'<a href="([^"]+)"><span>Next</span>', html).group(1)
    assert url == PROJECTS[0].page_url
    assert sorted(seen) == sorted(p.page_url for p in PROJECTS)


def test_sitemap_lists_home_and_every_project(out):
    xml = (out / "sitemap.xml").read_text(encoding="utf-8")
    assert xml.count("<loc>") == len(PROJECTS) + 1
    assert f"<loc>{SITE_URL}</loc>" in xml


def test_cards_link_to_their_pages(out):
    html, _ = parsed(out / "index.html")
    for project in PROJECTS:
        assert f'href="{project.page_url}"' in html
