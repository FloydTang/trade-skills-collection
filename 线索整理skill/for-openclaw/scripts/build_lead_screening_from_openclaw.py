#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent.parent
CORE_SCRIPT = SKILL_ROOT / "scripts" / "build_lead_screening_report.py"


def load_json(path: str | None) -> object:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def convert_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object.")
    candidates = payload.get("lead_candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Input must include a non-empty lead_candidates array.")
    return {
        "default_country_or_market": str(payload.get("country_or_market") or ""),
        "operator_notes": str(payload.get("operator_notes") or ""),
        "leads": candidates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    converted = convert_payload(load_json(args.input_json))
    proc = subprocess.run(
        [
          sys.executable,
          str(CORE_SCRIPT),
          "--json-out",
          args.json_out or "",
          "--markdown-out",
          args.markdown_out or "",
        ],
        input=json.dumps(converted, ensure_ascii=False),
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
