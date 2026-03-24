#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: str | None) -> Any:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def build(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
        raise ValueError("Input must be a discovery output JSON object with candidates.")
    if isinstance(payload.get("lead_screening_input"), dict):
        return payload["lead_screening_input"]
    leads = []
    for item in payload["candidates"]:
        leads.append(
            {
                "company_name": item.get("company_name", ""),
                "company_website": item.get("company_website", ""),
                "person_name": "",
                "email": "",
                "country_or_market": item.get("country_or_market", ""),
                "source_url": item.get("source_url", ""),
                "linkedin_url": item.get("linkedin_url", ""),
                "notes": item.get("search_snippet", ""),
                "product_keywords": "",
                "source_type": item.get("source_type", ""),
            }
        )
    return {"default_country_or_market": "", "operator_notes": "", "leads": leads}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json")
    parser.add_argument("--json-out")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = build(load_json(args.input_json))
    text = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
