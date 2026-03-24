#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def load_json(path: str | None) -> object:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def extract_leads(payload: object, include_enrichment: bool) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get("leads"), list):
        raise ValueError("Input must be a screening output JSON object with a leads array.")
    allowed = {"enter_customer_intel"}
    if include_enrichment:
        allowed.add("enrich_then_customer_intel")

    batch = []
    for lead in payload["leads"]:
        if lead.get("recommended_next_action") not in allowed:
            continue
        batch.append(lead.get("customer_intel_input", {}))
    return {
        "total_exported": len(batch),
        "customer_intel_inputs": batch,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json")
    parser.add_argument("--json-out")
    parser.add_argument("--include-enrichment", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = extract_leads(load_json(args.input_json), include_enrichment=args.include_enrichment)
    text = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
