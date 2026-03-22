#!/usr/bin/env python3
"""Install an hourly Windows Scheduled Task for Codex periodic ingest."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASK_NAME = "Deepsea-Nexus-Codex-Memory"


def build_task_runner_command(
    python_executable: str,
    runner_script: Path,
    config_path: Optional[Path] = None,
) -> str:
    parts = [f'"{python_executable}"', f'"{str(runner_script)}"']
    if config_path is not None:
        parts.extend(["--config", f'"{str(config_path)}"'])
    parts.append("--json")
    return " ".join(parts)


def build_schtasks_command(
    *,
    task_name: str,
    python_executable: str,
    runner_script: Path,
    config_path: Optional[Path] = None,
    interval_hours: int = 1,
) -> List[str]:
    interval = max(1, int(interval_hours))
    runner = build_task_runner_command(
        python_executable=python_executable,
        runner_script=runner_script,
        config_path=config_path,
    )
    return [
        "schtasks",
        "/Create",
        "/F",
        "/SC",
        "HOURLY",
        "/MO",
        str(interval),
        "/TN",
        task_name,
        "/TR",
        runner,
    ]


def install_task(
    *,
    task_name: str,
    python_executable: str,
    runner_script: Path,
    config_path: Optional[Path] = None,
    interval_hours: int = 1,
) -> subprocess.CompletedProcess[str]:
    command = build_schtasks_command(
        task_name=task_name,
        python_executable=python_executable,
        runner_script=runner_script,
        config_path=config_path,
        interval_hours=interval_hours,
    )
    return subprocess.run(command, capture_output=True, text=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Deepsea Codex periodic ingest task")
    parser.add_argument("--task-name", default=DEFAULT_TASK_NAME, help="Windows Scheduled Task name")
    parser.add_argument("--config", default=str(REPO_ROOT / "config.json"), help="Deepsea config path")
    parser.add_argument("--python", default=sys.executable, help="Python executable for the task")
    parser.add_argument("--interval-hours", type=int, default=1, help="Hourly interval")
    parser.add_argument("--dry-run", action="store_true", help="Print schtasks command only")
    args = parser.parse_args()

    runner_script = REPO_ROOT / "scripts" / "codex_periodic_ingest.py"
    config_path = Path(args.config).resolve() if args.config else None
    command = build_schtasks_command(
        task_name=args.task_name,
        python_executable=args.python,
        runner_script=runner_script,
        config_path=config_path,
        interval_hours=args.interval_hours,
    )
    if args.dry_run:
        print(" ".join(command))
        return 0

    result = install_task(
        task_name=args.task_name,
        python_executable=args.python,
        runner_script=runner_script,
        config_path=config_path,
        interval_hours=args.interval_hours,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
