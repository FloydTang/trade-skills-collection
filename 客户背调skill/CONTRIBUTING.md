# Contributing

Thanks for your interest in improving Trade Customer Intel.

## How to Contribute

- Open an issue for bugs, feature ideas, or workflow questions
- Keep changes focused and easy to review
- Preserve the conservative identity-resolution and risk-scoring principles
- Do not add private-data collection or unverifiable personalization logic

## Development Notes

- `SKILL.md` defines the skill workflow and intended usage
- `scripts/build_customer_intel_report.py` is the main execution entrypoint
- `references/` contains the output contract and sourcing rules

## Pull Request Checklist

- Update documentation when behavior changes
- Keep public-web-only constraints intact
- Add or adjust examples if the input/output shape changes
- Avoid breaking the report structure unless there is a strong reason

## Code Style

- Prefer small, readable changes
- Keep comments brief and high-signal
- Preserve conservative wording around weak evidence
