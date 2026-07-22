"""Deterministic search, status, and linting for the maintained memory wiki."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import yaml


PAGE_TYPES = {
    "person",
    "company",
    "project",
    "decision",
    "legal",
    "medical",
    "financial",
    "research",
    "skill",
    "source",
}
STATUSES = {"verified", "disputed", "superseded", "draft"}
SENSITIVITIES = {"public", "internal", "confidential", "restricted"}
REQUIRED_PAGE_FIELDS = {
    "title",
    "type",
    "status",
    "created",
    "updated",
    "sensitivity",
    "sources",
    "supersedes",
}
REQUIRED_POINTER_FIELDS = {
    "id",
    "title",
    "kind",
    "sensitivity",
    "locator",
    "sha256",
    "created",
    "immutable",
}
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
LOG_ENTRY_RE = re.compile(r"^## \[\d{4}-\d{2}-\d{2}\] [a-z-]+ \| .+$", re.MULTILINE)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "aws-access-key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "assigned-secret": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|password|secret)\b\s*[:=]\s*"
        r"['\"]?[A-Za-z0-9_./+\-=]{16,}"
    ),
}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _normalise(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _parse_frontmatter(path: Path, root: Path) -> tuple[dict[str, Any], str, list[Finding]]:
    text = path.read_text(encoding="utf-8")
    rel = _relative(path, root)
    if not text.startswith("---\n"):
        return {}, text, [Finding("error", "frontmatter-missing", rel, "Missing YAML frontmatter")]
    marker = text.find("\n---\n", 4)
    if marker < 0:
        return (
            {},
            text,
            [Finding("error", "frontmatter-unclosed", rel, "Unclosed YAML frontmatter")],
        )
    raw = text[4:marker]
    body = text[marker + 5 :]
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        return {}, body, [Finding("error", "frontmatter-invalid", rel, str(exc).splitlines()[0])]
    if not isinstance(data, dict):
        return {}, body, [Finding("error", "frontmatter-type", rel, "Frontmatter must be a map")]
    return data, body, []


def _content_pages(memory_root: Path) -> list[Path]:
    wiki = memory_root / "wiki"
    excluded = {wiki / "index.md", wiki / "log.md", wiki / "open-questions.md"}
    return sorted(path for path in wiki.rglob("*.md") if path not in excluded)


def _resolve_wikilink(source: Path, target: str, wiki_root: Path) -> Path:
    clean = target.split("|", 1)[0].split("#", 1)[0].strip()
    candidate = Path(clean)
    if candidate.is_absolute():
        candidate = wiki_root / str(candidate).lstrip("/")
    else:
        candidate = source.parent / candidate
    if candidate.suffix != ".md":
        candidate = candidate.with_suffix(".md")
    return candidate.resolve()


def _valid_date(value: Any) -> bool:
    if isinstance(value, date):
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _lint_page(path: Path, memory_root: Path) -> list[Finding]:
    data, _body, findings = _parse_frontmatter(path, memory_root)
    if findings:
        return findings
    rel = _relative(path, memory_root)
    missing = sorted(REQUIRED_PAGE_FIELDS - data.keys())
    for field in missing:
        findings.append(Finding("error", "page-field-missing", rel, f"Missing field: {field}"))

    if data.get("type") not in PAGE_TYPES:
        findings.append(
            Finding("error", "page-type-invalid", rel, f"Invalid type: {data.get('type')}")
        )
    if data.get("status") not in STATUSES:
        findings.append(
            Finding("error", "page-status-invalid", rel, f"Invalid status: {data.get('status')}")
        )
    if data.get("sensitivity") not in SENSITIVITIES:
        findings.append(
            Finding(
                "error",
                "page-sensitivity-invalid",
                rel,
                f"Invalid sensitivity: {data.get('sensitivity')}",
            )
        )
    for field in ("created", "updated"):
        if field in data and not _valid_date(data[field]):
            findings.append(Finding("error", "page-date-invalid", rel, f"Invalid {field} date"))

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        findings.append(
            Finding("error", "page-sources-invalid", rel, "sources must be a non-empty list")
        )
    else:
        for source in sources:
            if not isinstance(source, str):
                findings.append(
                    Finding("error", "page-source-invalid", rel, "Source path must be text")
                )
                continue
            pointer = memory_root / source
            if not pointer.is_file():
                findings.append(
                    Finding(
                        "error", "page-source-missing", rel, f"Missing source pointer: {source}"
                    )
                )
    if not isinstance(data.get("supersedes"), list):
        findings.append(
            Finding("error", "page-supersedes-invalid", rel, "supersedes must be a list")
        )
    return findings


def _lint_pointer(path: Path, memory_root: Path) -> list[Finding]:
    rel = _relative(path, memory_root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [Finding("error", "pointer-json-invalid", rel, str(exc))]
    findings: list[Finding] = []
    missing = sorted(REQUIRED_POINTER_FIELDS - data.keys())
    for field in missing:
        findings.append(Finding("error", "pointer-field-missing", rel, f"Missing field: {field}"))
    if data.get("sensitivity") not in SENSITIVITIES:
        findings.append(
            Finding("error", "pointer-sensitivity-invalid", rel, "Invalid source sensitivity")
        )
    if not SHA256_RE.fullmatch(str(data.get("sha256", ""))):
        findings.append(
            Finding("error", "pointer-sha-invalid", rel, "sha256 must be 64 lowercase hex")
        )
    if data.get("immutable") is not True:
        findings.append(Finding("error", "pointer-mutable", rel, "immutable must be true"))
    if not _valid_date(data.get("created")):
        findings.append(Finding("error", "pointer-date-invalid", rel, "created must be ISO date"))
    locator = str(data.get("locator", ""))
    if data.get("sensitivity") == "restricted" and not locator.startswith("vault://"):
        findings.append(
            Finding("error", "restricted-locator", rel, "Restricted pointers must use vault://")
        )
    return findings


def _lint_links(memory_root: Path) -> list[Finding]:
    wiki_root = (memory_root / "wiki").resolve()
    findings: list[Finding] = []
    for path in sorted((memory_root / "wiki").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for target in WIKILINK_RE.findall(text):
            resolved = _resolve_wikilink(path, target, wiki_root)
            try:
                resolved.relative_to(wiki_root)
            except ValueError:
                findings.append(
                    Finding(
                        "error",
                        "link-outside-wiki",
                        _relative(path, memory_root),
                        f"Link escapes wiki: [[{target}]]",
                    )
                )
                continue
            if not resolved.is_file():
                findings.append(
                    Finding(
                        "error",
                        "link-broken",
                        _relative(path, memory_root),
                        f"Broken link: [[{target}]]",
                    )
                )
    return findings


def _lint_index(memory_root: Path) -> list[Finding]:
    index = memory_root / "wiki" / "index.md"
    if not index.is_file():
        return [Finding("error", "index-missing", "wiki/index.md", "Global index is missing")]
    indexed = {
        _resolve_wikilink(index, target, (memory_root / "wiki").resolve())
        for target in WIKILINK_RE.findall(index.read_text(encoding="utf-8"))
    }
    return [
        Finding(
            "warning",
            "page-orphan",
            _relative(path, memory_root),
            "Content page is not linked from wiki/index.md",
        )
        for path in _content_pages(memory_root)
        if path.resolve() not in indexed
    ]


def _lint_log(memory_root: Path) -> list[Finding]:
    path = memory_root / "wiki" / "log.md"
    if not path.is_file():
        return [Finding("error", "log-missing", "wiki/log.md", "Append-only log is missing")]
    text = path.read_text(encoding="utf-8")
    if not LOG_ENTRY_RE.search(text):
        return [
            Finding(
                "error",
                "log-entry-missing",
                "wiki/log.md",
                "No parseable log entry found",
            )
        ]
    return []


def _iter_text_files(memory_root: Path) -> Iterable[Path]:
    for path in memory_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".txt"}:
            yield path


def _lint_secrets(memory_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_text_files(memory_root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(
                    Finding(
                        "error",
                        "possible-secret",
                        _relative(path, memory_root),
                        f"Possible {name} detected",
                    )
                )
    return findings


def lint(memory_root: Path) -> list[Finding]:
    memory_root = memory_root.resolve()
    findings: list[Finding] = []
    required = [
        memory_root / "AGENTS.md",
        memory_root / "config.yaml",
        memory_root / "engine.lock.json",
        memory_root / "wiki" / "open-questions.md",
    ]
    for path in required:
        if not path.is_file():
            findings.append(
                Finding(
                    "error",
                    "required-file-missing",
                    _relative(path, memory_root),
                    "Required file is missing",
                )
            )
    for page in _content_pages(memory_root):
        findings.extend(_lint_page(page, memory_root))
    for pointer in sorted((memory_root / "raw-pointers").glob("*.json")):
        findings.extend(_lint_pointer(pointer, memory_root))
    findings.extend(_lint_links(memory_root))
    findings.extend(_lint_index(memory_root))
    findings.extend(_lint_log(memory_root))
    findings.extend(_lint_secrets(memory_root))
    return sorted(findings, key=lambda item: (item.level, item.path, item.code))


def query(memory_root: Path, terms: str, limit: int = 10) -> list[dict[str, Any]]:
    tokens = [token for token in re.findall(r"[\w-]+", _normalise(terms)) if len(token) > 1]
    if not tokens:
        return []
    results: list[dict[str, Any]] = []
    for path in _content_pages(memory_root):
        text = path.read_text(encoding="utf-8")
        normalised = _normalise(text)
        title = ""
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        counts = Counter({token: normalised.count(token) for token in tokens})
        if not all(counts[token] for token in tokens):
            continue
        score = sum(counts.values())
        score += sum(4 for token in tokens if token in _normalise(title))
        excerpt = next(
            (
                line.strip("- ")
                for line in text.splitlines()
                if line.strip() and any(token in _normalise(line) for token in tokens)
            ),
            title,
        )
        results.append(
            {
                "path": _relative(path, memory_root),
                "title": title or path.stem,
                "score": score,
                "excerpt": excerpt[:240],
            }
        )
    return sorted(results, key=lambda item: (-item["score"], item["path"]))[:limit]


def status(memory_root: Path) -> dict[str, Any]:
    statuses: Counter[str] = Counter()
    sensitivities: Counter[str] = Counter()
    types: Counter[str] = Counter()
    for path in _content_pages(memory_root):
        data, _body, _findings = _parse_frontmatter(path, memory_root)
        statuses[str(data.get("status", "invalid"))] += 1
        sensitivities[str(data.get("sensitivity", "invalid"))] += 1
        types[str(data.get("type", "invalid"))] += 1
    return {
        "pages": sum(types.values()),
        "source_pointers": len(list((memory_root / "raw-pointers").glob("*.json"))),
        "by_type": dict(sorted(types.items())),
        "by_status": dict(sorted(statuses.items())),
        "by_sensitivity": dict(sorted(sensitivities.items())),
    }


def _default_root() -> Path:
    return Path(__file__).resolve().parents[1] / "sergio-memory"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_default_root(), help="Path to sergio-memory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    lint_parser = subparsers.add_parser(
        "lint", help="Validate structure, provenance, links, and secrets"
    )
    lint_parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    query_parser = subparsers.add_parser("query", help="Search maintained wiki pages")
    query_parser.add_argument("terms")
    query_parser.add_argument("--limit", type=int, default=10)
    subparsers.add_parser("status", help="Show page and provenance counts")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.root.resolve()
    if args.command == "lint":
        findings = lint(root)
        for finding in findings:
            print(f"{finding.level.upper()} {finding.code} {finding.path}: {finding.message}")
        errors = sum(item.level == "error" for item in findings)
        warnings = sum(item.level == "warning" for item in findings)
        print(f"lint: {errors} error(s), {warnings} warning(s)")
        return 1 if errors or (args.strict and warnings) else 0
    if args.command == "query":
        print(json.dumps(query(root, args.terms, args.limit), ensure_ascii=False, indent=2))
        return 0
    if args.command == "status":
        print(json.dumps(status(root), ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
