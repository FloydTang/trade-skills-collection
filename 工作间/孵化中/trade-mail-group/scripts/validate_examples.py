#!/usr/bin/env python3
import json
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
EXAMPLES = BASE / "examples"
REQUIRED_INPUT = {"our_product", "target_market", "tone", "customers"}
REQUIRED_CUSTOMER = {
    "company_name",
    "country",
    "industry",
    "source",
    "intel_summary",
    "known_signal",
}
REQUIRED_OUTPUT = {"one_line_conclusion", "input_quality", "handoff"}
REQUIRED_GROUP = {
    "group_id",
    "group_name",
    "companies",
    "facts",
    "inferences",
    "outreach_angle",
    "subject_candidates",
    "first_email_draft",
    "follow_up_cadence",
    "human_review_points",
}
REQUIRED_HANDOFF = {
    "to_customer_intel_skill",
    "to_outreach_email_skill",
    "non_goals",
}
REQUIRED_BLOCKING = {
    "reason",
    "missing_fields",
    "recommended_next_action",
    "safe_use_of_current_data",
    "do_not_do",
}
BANNED_OUTPUT_PHRASES = [
    "smtp setup",
    "tracking pixel",
    "guaranteed reply",
    "guarantee reply",
    "reply rate guarantee",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def assert_fields(obj, required, label):
    missing = sorted(required - set(obj))
    if missing:
        raise AssertionError(f"{label} missing fields: {missing}")


def validate_pair(input_path: Path):
    output_path = input_path.with_name(input_path.name.replace("-input.json", "-output.json"))
    if not output_path.exists():
        raise AssertionError(f"missing paired output: {output_path.name}")

    payload = load_json(input_path)
    output = load_json(output_path)
    assert_fields(payload, REQUIRED_INPUT, input_path.name)
    assert_fields(output, REQUIRED_OUTPUT, output_path.name)
    assert_fields(output["handoff"], REQUIRED_HANDOFF, f"{output_path.name}.handoff")

    customers = payload["customers"]
    if not isinstance(customers, list) or not customers:
        raise AssertionError(f"{input_path.name} customers must be a non-empty list")
    customer_names = []
    for idx, customer in enumerate(customers):
        assert_fields(customer, REQUIRED_CUSTOMER, f"{input_path.name}.customers[{idx}]")
        customer_names.append(customer["company_name"])

    if "blocking_recommendation" in output:
        assert_fields(
            output["blocking_recommendation"],
            REQUIRED_BLOCKING,
            f"{output_path.name}.blocking_recommendation",
        )
        if output.get("groups"):
            raise AssertionError(f"{output_path.name} must not force groups when blocking_recommendation is present")
    else:
        if "groups" not in output:
            raise AssertionError(f"{output_path.name} missing groups or blocking_recommendation")
        assigned = []
        for idx, group in enumerate(output["groups"]):
            assert_fields(group, REQUIRED_GROUP, f"{output_path.name}.groups[{idx}]")
            if len(group["subject_candidates"]) < 2:
                raise AssertionError(f"{output_path.name}.groups[{idx}] needs at least 2 subject candidates")
            assigned.extend(group["companies"])

        missing = sorted(set(customer_names) - set(assigned))
        extra = sorted(set(assigned) - set(customer_names))
        duplicates = sorted({name for name in assigned if assigned.count(name) > 1})
        if missing or extra or duplicates:
            raise AssertionError(
                f"{output_path.name} customer assignment mismatch: "
                f"missing={missing}, extra={extra}, duplicates={duplicates}"
            )

    lower_output = json.dumps(output, ensure_ascii=False).lower()
    for phrase in BANNED_OUTPUT_PHRASES:
        if phrase in lower_output:
            raise AssertionError(f"{output_path.name} contains banned phrase: {phrase}")


def main():
    inputs = sorted(EXAMPLES.glob("*-input.json"))
    if not inputs:
        raise AssertionError("no example inputs found")
    for input_path in inputs:
        validate_pair(input_path)
    print(f"validated {len(inputs)} example pairs")


if __name__ == "__main__":
    main()
