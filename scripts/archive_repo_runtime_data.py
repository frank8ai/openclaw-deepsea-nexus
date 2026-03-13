#!/usr/bin/env python3
"""
Archive repo-local runtime artifacts out of the working tree.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE_BASE = Path.home() / ".openclaw-runtime" / "archive" / "deepsea-nexus"
CACHE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".benchmarks"}
EXCLUDED_PARTS = {".git"}


@dataclass(frozen=True)
class RuntimeArtifact:
    relative_path: str
    kind: str
    size_bytes: int
    reason: str


def _dir_size(path: Path) -> int:
    total = 0
    if path.is_file():
        return path.stat().st_size
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def _is_under_venv(path: Path) -> bool:
    return ".venv" in path.parts


def discover_runtime_artifacts(
    repo_root: Path | None = None,
    *,
    include_stale_venv: bool = False,
) -> list[RuntimeArtifact]:
    root = Path(repo_root or REPO_ROOT).expanduser().resolve()
    found: dict[str, RuntimeArtifact] = {}

    logs_dir = root / "logs"
    if logs_dir.exists():
        rel = logs_dir.relative_to(root).as_posix()
        found[rel] = RuntimeArtifact(
            relative_path=rel,
            kind="runtime_logs",
            size_bytes=_dir_size(logs_dir),
            reason="repo-local logs are runtime artifacts, not source of truth",
        )

    for name in CACHE_DIR_NAMES:
        for path in root.rglob(name):
            if not path.exists() or _is_excluded(path) or _is_under_venv(path):
                continue
            rel = path.relative_to(root).as_posix()
            found[rel] = RuntimeArtifact(
                relative_path=rel,
                kind="bytecode_cache",
                size_bytes=_dir_size(path),
                reason="Python cache directory can be regenerated and should not live in the repo tree",
            )

    selected_dirs = {root / item.relative_path for item in found.values() if (root / item.relative_path).is_dir()}
    for path in root.rglob("*.pyc"):
        if _is_excluded(path) or _is_under_venv(path):
            continue
        if any(parent in selected_dirs for parent in path.parents):
            continue
        rel = path.relative_to(root).as_posix()
        found[rel] = RuntimeArtifact(
            relative_path=rel,
            kind="bytecode_file",
            size_bytes=path.stat().st_size,
            reason="orphaned bytecode file outside cache directory",
        )

    if include_stale_venv:
        venv_dir = root / ".venv"
        if venv_dir.exists():
            rel = venv_dir.relative_to(root).as_posix()
            found[rel] = RuntimeArtifact(
                relative_path=rel,
                kind="stale_virtualenv",
                size_bytes=_dir_size(venv_dir),
                reason="repo-local .venv is ignored, reproducible, and not used by the current release gate",
            )

    return [found[key] for key in sorted(found)]


def archive_runtime_artifacts(
    repo_root: Path | None = None,
    *,
    archive_base: Path | None = None,
    include_stale_venv: bool = False,
    apply: bool = False,
) -> dict:
    root = Path(repo_root or REPO_ROOT).expanduser().resolve()
    base = Path(archive_base or DEFAULT_ARCHIVE_BASE).expanduser().resolve()
    artifacts = discover_runtime_artifacts(root, include_stale_venv=include_stale_venv)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    archive_root = base / f"repo-runtime-cleanup-{timestamp}"

    result = {
        "repo_root": str(root),
        "archive_root": str(archive_root),
        "apply": apply,
        "artifact_count": len(artifacts),
        "total_bytes": sum(item.size_bytes for item in artifacts),
        "artifacts": [asdict(item) for item in artifacts],
    }

    if not apply:
        return result

    payload_root = archive_root / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    for artifact in artifacts:
        src = root / artifact.relative_path
        if not src.exists():
            continue
        dest = payload_root / artifact.relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        moved.append(artifact.relative_path)

    manifest = {**result, "moved": moved, "moved_count": len(moved)}
    (archive_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive repo-local runtime artifacts")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repo root to clean")
    parser.add_argument(
        "--archive-base",
        default=str(DEFAULT_ARCHIVE_BASE),
        help="Base directory for archives",
    )
    parser.add_argument(
        "--include-stale-venv",
        action="store_true",
        help="Also move the ignored repo-local .venv directory out of the repo",
    )
    parser.add_argument("--apply", action="store_true", help="Move artifacts into the archive location")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    args = parser.parse_args()

    result = archive_runtime_artifacts(
        repo_root=Path(args.repo_root),
        archive_base=Path(args.archive_base),
        include_stale_venv=args.include_stale_venv,
        apply=args.apply,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"Repo root: {result['repo_root']}")
    print(f"Archive root: {result['archive_root']}")
    print(f"Artifacts: {result['artifact_count']}")
    print(f"Total bytes: {result['total_bytes']}")
    for item in result["artifacts"]:
        print(f"- {item['relative_path']} [{item['kind']}]")
    if args.apply:
        print(f"Moved: {result.get('moved_count', 0)}")
    else:
        print("Dry run only. Re-run with --apply to move artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
