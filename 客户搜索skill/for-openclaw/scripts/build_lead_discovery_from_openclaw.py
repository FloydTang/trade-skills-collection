#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent.parent
CORE_SCRIPT = SKILL_ROOT / "scripts" / "build_lead_discovery_report.py"


def load_json(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_json(args.input_json)
    fixtures_json = payload.pop("fixtures_json", "")
    command = [
        sys.executable,
        str(CORE_SCRIPT),
        "--json-out",
        args.json_out or "",
        "--markdown-out",
        args.markdown_out or "",
    ]
    if fixtures_json:
        command.extend(["--fixtures-json", fixtures_json])
    proc = subprocess.run(
        command,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout)
        raise SystemExit(proc.returncode)
    sys.stdout.write(proc.stdout)


if __name__ == "__main__":
    main()
