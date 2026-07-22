import json
import shutil
from pathlib import Path

from tools.memory_wiki import lint, query, status


REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_ROOT = REPO_ROOT / "sergio-memory"


def test_seed_memory_lints_cleanly():
    assert lint(MEMORY_ROOT) == []


def test_query_finds_the_synthetic_pilot():
    results = query(MEMORY_ROOT, "synthetic pilot")
    assert results
    assert results[0]["path"] == "wiki/projects/memory-pilot.md"


def test_status_reports_seed_counts():
    report = status(MEMORY_ROOT)
    assert report["pages"] == 1
    assert report["source_pointers"] == 1
    assert report["by_status"] == {"verified": 1}


def test_lint_detects_broken_link_and_missing_pointer(tmp_path):
    target = tmp_path / "sergio-memory"
    shutil.copytree(MEMORY_ROOT, target)
    page = target / "wiki" / "projects" / "memory-pilot.md"
    text = page.read_text(encoding="utf-8")
    text = text.replace("raw-pointers/memory-pilot.json", "raw-pointers/missing.json")
    text += "\n- [[missing-page]]\n"
    page.write_text(text, encoding="utf-8")

    codes = {finding.code for finding in lint(target)}
    assert "page-source-missing" in codes
    assert "link-broken" in codes


def test_lint_detects_probable_secret(tmp_path):
    target = tmp_path / "sergio-memory"
    shutil.copytree(MEMORY_ROOT, target)
    pointer = target / "raw-pointers" / "leak.json"
    pointer.write_text(
        json.dumps(
            {
                "id": "leak",
                "title": "bad fixture",
                "kind": "synthetic",
                "sensitivity": "internal",
                "locator": "synthetic://leak",
                "sha256": "0" * 64,
                "created": "2026-07-22",
                "immutable": True,
                "secret": "api_key=abcdefghijklmnop123456",
            }
        ),
        encoding="utf-8",
    )

    assert any(finding.code == "possible-secret" for finding in lint(target))
