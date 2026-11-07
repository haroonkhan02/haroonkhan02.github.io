from pathlib import Path

import pytest

from portfolio_site.content import load_projects, parse_project
from portfolio_site.verify import local_reader, main, missing_numbers, numbers_in, verify

ROOT = Path(__file__).resolve().parents[1]


def project(**overrides):
    base = {
        "repo": "demo",
        "title": "Demo",
        "area": "Vision",
        "size": "small",
        "summary": "Trained on 480 demos.",
        "metric": "99.0 %",
        "metric_label": "success",
        "caveat": "Only 3 seeds.",
        "tags": [],
    }
    return parse_project(base | overrides)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("99.0 %", {"99.0"}),
        ("1.4–8.8 cm", {"1.4", "8.8"}),
        ("17/18 frames.", {"17", "18"}),
        ("2,782 images", {"2,782"}),
        ("ends with 0.9.", {"0.9"}),
        ("MRR@10 and YOLO11x and Sentinel-2", {"2"}),
    ],
)
def test_numbers_in(text, expected):
    assert numbers_in(text) == expected


def test_reports_only_the_numbers_missing_from_the_readme():
    assert missing_numbers(project(), "480 demos, 99.0 % success over 3 seeds") == []
    assert missing_numbers(project(), "480 demos, 98.5 % success over 3 seeds") == ["99.0"]


def test_a_longer_number_does_not_back_a_shorter_one():
    assert missing_numbers(project(metric="0.9"), "480 3 0.95") == ["0.9"]


def test_verify_reads_each_repo(tmp_path):
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "README.md").write_text("480 and 3 only", encoding="utf-8")
    assert verify([project()], local_reader(tmp_path)) == {"demo": ["99.0"]}


def test_main_fails_on_unbacked_numbers(tmp_path, capsys):
    content = tmp_path / "projects.yaml"
    content.write_text(
        """
- {repo: demo, title: T, area: A, size: small, summary: S, metric: "7.5",
   metric_label: L, caveat: C, tags: []}
- {repo: demo2, title: T, area: A, size: small, summary: S, metric: "1",
   metric_label: L, caveat: C, tags: []}
- {repo: demo3, title: T, area: A, size: small, summary: S, metric: "1",
   metric_label: L, caveat: C, tags: []}
""",
        encoding="utf-8",
    )
    for repo, text in {"demo": "nothing", "demo2": "1", "demo3": "1"}.items():
        (tmp_path / repo).mkdir()
        (tmp_path / repo / "README.md").write_text(text, encoding="utf-8")
    assert main(["--content", str(content), "--repos-dir", str(tmp_path)]) == 1
    assert "demo: not in README: 7.5" in capsys.readouterr().out


def test_shipped_content_is_valid():
    projects = load_projects(ROOT / "content" / "projects.yaml")
    assert len(projects) == 12
    assert sum(1 for p in projects if p.demo) == 5
