import re
import shutil
from html.parser import HTMLParser
from pathlib import Path

import pytest
from PIL import Image

from portfolio_site.build import make_card, render
from portfolio_site.content import load_projects

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    """Collects the tags that the checks below care about."""

    def __init__(self):
        super().__init__()
        self.images, self.links, self.ids, self.assets, self.h1 = [], [], set(), [], 0
        self.canonical = ""

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if "id" in attr:
            self.ids.add(attr["id"])
        if tag == "img":
            self.images.append(attr)
            self.assets.append(attr["src"])
        if tag == "a":
            self.links.append(attr["href"])
        if tag == "link" and attr.get("rel") == "canonical":
            self.canonical = attr["href"]
        elif tag in ("link", "script") and (attr.get("href") or attr.get("src")):
            self.assets.append(attr.get("href") or attr.get("src"))
        if tag == "h1":
            self.h1 += 1
        if "data-video" in attr:
            self.assets.append(attr["data-video"])


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site") / "dist"
    render(ROOT, out)
    page = Page()
    html = (out / "index.html").read_text(encoding="utf-8")
    page.feed(html)
    return out, html, page


def test_every_project_is_rendered_with_its_limitation(site):
    _, html, _ = site
    projects = load_projects(ROOT / "content" / "projects.yaml")
    for project in projects:
        assert project.url in html
        assert project.metric in html
    assert html.count('class="caveat"') == len(projects)


def test_all_local_assets_exist(site):
    out, _, page = site
    assert page.assets
    for asset in page.assets:
        assert (out / asset.lstrip("/")).is_file(), asset


def test_images_have_alt_text_and_reserved_size(site):
    _, _, page = site
    assert page.images
    for image in page.images:
        assert image["alt"].strip()
        assert int(image["width"]) > 0 and int(image["height"]) > 0


def test_anchors_point_at_real_sections(site):
    _, _, page = site
    for link in page.links:
        if link.startswith("#"):
            assert link[1:] in page.ids


def test_single_h1_and_no_external_requests(site):
    _, html, page = site
    assert page.h1 == 1
    assert not [a for a in page.assets if a.startswith("http")]
    assert not re.search(r"""(src|href)=["']//""", html)


def test_page_does_not_contain_an_email_address(site):
    _, html, _ = site
    assert not re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", html)


def test_rebuild_replaces_stale_files(tmp_path):
    out = tmp_path / "dist"
    out.mkdir()
    (out / "stale.html").write_text("old", encoding="utf-8")
    render(ROOT, out)
    assert not (out / "stale.html").exists()
    assert (out / "404.html").is_file()
    assert (out / ".nojekyll").is_file()


def test_missing_poster_fails_the_build(tmp_path):
    project = next(p for p in load_projects(ROOT / "content/projects.yaml") if p.media)
    with pytest.raises(FileNotFoundError, match="site-media"):
        make_card(project, tmp_path)


def test_card_records_poster_size_and_optional_video(tmp_path):
    project = next(p for p in load_projects(ROOT / "content/projects.yaml") if p.media)
    Image.new("RGB", (64, 36)).save(tmp_path / f"{project.repo}.webp")
    card = make_card(project, tmp_path)
    assert (card.width, card.height, card.video) == (64, 36, "")
    shutil.copy(tmp_path / f"{project.repo}.webp", tmp_path / f"{project.repo}.mp4")
    assert make_card(project, tmp_path).video.endswith(".mp4")
