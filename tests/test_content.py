import pytest

from portfolio_site.content import ContentError, check_grid, load_projects, parse_project


def raw(**overrides):
    base = {
        "repo": "demo-repo",
        "title": "Demo",
        "area": "Vision",
        "size": "small",
        "summary": "Does a thing.",
        "metric": "0.9",
        "metric_label": "accuracy",
        "caveat": "Small test set.",
        "tags": ["PyTorch"],
    }
    return base | overrides


def test_parses_a_project():
    project = parse_project(raw(media={"source": "a.gif", "alt": "A clip"}))
    assert project.url == "https://github.com/haroonkhan02/demo-repo"
    assert project.span == 4
    assert project.tags == ("PyTorch",)
    assert project.media.fit == "cover"


@pytest.mark.parametrize(
    "overrides",
    [
        {"size": "huge"},
        {"unexpected": 1},
        {"media": {"source": "a.gif", "alt": ""}},
        {"media": {"source": "a.gif", "alt": "x", "fit": "stretch"}},
        {"demo": "https://example.com/x", "demo_note": "note"},
        {"demo": "https://huggingface.co/spaces/a/b"},
    ],
)
def test_rejects_bad_projects(overrides):
    with pytest.raises(ContentError):
        parse_project(raw(**overrides))


def test_missing_field_is_a_content_error():
    data = raw()
    del data["metric"]
    with pytest.raises(ContentError):
        parse_project(data)


def test_claims_skip_empty_fields():
    project = parse_project(raw())
    assert "" not in project.claims
    assert "0.9" in project.claims


def test_grid_rows_must_fill_exactly():
    large, medium, small = (parse_project(raw(size=s)) for s in ("large", "medium", "small"))
    check_grid([large, medium, small, small, small])
    with pytest.raises(ContentError):
        check_grid([large, small])
    with pytest.raises(ContentError):
        check_grid([large])


def test_duplicate_repos_are_rejected(tmp_path):
    path = tmp_path / "projects.yaml"
    entry = """
- repo: same
  title: T
  area: A
  size: small
  summary: S
  metric: "1"
  metric_label: L
  caveat: C
  tags: [x]
"""
    path.write_text(entry * 3, encoding="utf-8")
    with pytest.raises(ContentError, match="duplicate"):
        load_projects(path)
