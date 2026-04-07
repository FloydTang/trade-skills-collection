#!/usr/bin/env python3
"""Initialize the GitHub daily discovery workspace and create a dated report."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
REPORTS = ROOT / "reports"


STATIC_FILES = {
    ROOT / "github-watchlist.md": TEMPLATES / "watchlist-template.md",
    ROOT / "tool-adoption-backlog.md": TEMPLATES / "adoption-backlog-template.md",
    ROOT / "tool-adoption-decisions.md": TEMPLATES / "decision-log-template.md",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize GitHub discovery docs and create a daily report."
    )
    parser.add_argument(
        "--date",
        dest="report_date",
        help="Report date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the dated report if it already exists.",
    )
    return parser.parse_args()


def resolve_report_date(raw: str | None) -> date:
    if not raw:
        return date.today()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"Invalid --date value: {raw}. Expected YYYY-MM-DD.") from exc


def ensure_static_files() -> list[Path]:
    created: list[Path] = []
    for target, template in STATIC_FILES.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        created.append(target)
    return created


def create_report(report_date: date, force: bool) -> tuple[Path, bool]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    target = REPORTS / f"{report_date.isoformat()}.md"
    existed = target.exists()
    if existed and not force:
        return target, False

    template = (TEMPLATES / "daily-report-template.md").read_text(encoding="utf-8")
    target.write_text(template.replace("{{date}}", report_date.isoformat()), encoding="utf-8")
    return target, True


def main() -> None:
    args = parse_args()
    report_date = resolve_report_date(args.report_date)
    created_static = ensure_static_files()
    report_path, wrote_report = create_report(report_date, args.force)

    print(f"workspace: {ROOT}")
    if created_static:
        print("created static files:")
        for path in created_static:
            print(f"- {path.relative_to(ROOT)}")
    else:
        print("static files already existed")

    if wrote_report:
        print(f"created report: {report_path.relative_to(ROOT)}")
    else:
        print(f"report already exists: {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
