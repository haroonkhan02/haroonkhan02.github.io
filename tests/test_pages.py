import pytest

from portfolio_site.content import ContentError, load_pages, parse_page, parse_project


def raw(**overrides):
    base = {
        "problem": "Why it matters.",
        "approach": ["Built a thing.", "Measured it."],
        "results": {"caption": "Test split.", "rows": [["Model", "Score"], ["Mine", "0.90"]]},
        "findings": ["It works on easy cases."],
        "limitations": ["Small test set."],
    }
    return base | overrides


def test_parses_a_page():
    page = parse_page(raw(), "demo")
    assert page.results.header == ("Model", "Score")
    assert page.results.body == (("Mine", "0.90"),)
    assert "0.90" in page.claims
    assert "Small test set." in page.claims


@pytest.mark.parametrize(
    "overrides",
    [
        {"problem": None},
        {"approach": []},
        {"findings": ["ok", 0.5]},
        {"limitations": "not a list"},
        {"results": {"caption": "C", "rows": [["Only a header"]]}},
        {"results": {"caption": "C", "rows": [["A", "B"], ["1"]]}},
        {"results": {"caption": "C", "rows": [["A"], [0.69]]}},
        {"results": {"rows": [["A"], ["1"]]}},
        {"results": {"caption": "C", "rows": [["A"], ["1"]], "extra": 1}},
        {"unexpected": "key"},
    ],
)
def test_rejects_bad_pages(overrides):
    with pytest.raises(ContentError):
        parse_page(raw(**overrides), "demo")


def _project(repo):
    return parse_project(
        {
            "repo": repo,
            "title": "T",
            "area": "A",
            "size": "small",
            "summary": "S",
            "metric": "1",
            "metric_label": "L",
            "caveat": "C",
            "tags": [],
        }
    )


def test_every_project_needs_exactly_one_page(tmp_path):
    (tmp_path / "a.yaml").write_text("problem: P", encoding="utf-8")
    with pytest.raises(ContentError, match="no page"):
        load_pages(tmp_path, [_project("a"), _project("b")])
    with pytest.raises(ContentError, match="without a project"):
        load_pages(tmp_path, [])


def test_project_page_url():
    assert _project("demo-repo").page_url == "/projects/demo-repo/"
