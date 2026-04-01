#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


FIELD_LABELS = {
    "product_title": "产品标题",
    "price": "价格",
    "spec_keywords": "规格关键词",
    "promotion_copy": "促销文案",
    "discount_copy": "折扣文案",
    "cta_text": "CTA 文案",
    "hero_copy": "首屏主文案",
    "new_badge": "上新标识",
    "featured_products": "主推产品",
}

MANUAL_REVIEW_FIELDS = {
    "price",
    "promotion_copy",
    "discount_copy",
    "new_badge",
    "featured_products",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a minimal competitor-page change summary from normalized watch events."
    )
    parser.add_argument("--input-json", required=True, help="Normalized JSON input with monitoring events.")
    parser.add_argument("--markdown-out", required=True, help="Markdown summary output path.")
    parser.add_argument("--json-out", required=True, help="JSON summary output path.")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def unique_in_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def to_label(field_name: str) -> str:
    return FIELD_LABELS.get(field_name, field_name)


def summarize_field_change(change: dict) -> str:
    field_label = to_label(str(change.get("field", "")).strip())
    before = str(change.get("before", "")).strip() or "未标注"
    after = str(change.get("after", "")).strip() or "未标注"
    return f"{field_label}：`{before}` -> `{after}`"


def infer_change_types(changes: list[dict]) -> list[str]:
    labels: list[str] = []
    for change in changes:
        field_name = str(change.get("field", "")).strip()
        if field_name == "price":
            labels.append("价格变化")
        elif field_name in {"promotion_copy", "discount_copy"}:
            labels.append("促销变化")
        elif field_name in {"new_badge", "featured_products"}:
            labels.append("上新变化")
        elif field_name in {"cta_text"}:
            labels.append("CTA 变化")
        elif field_name in {"spec_keywords", "hero_copy", "product_title"}:
            labels.append("页面表达变化")
        else:
            labels.append("页面字段变化")
    return unique_in_order(labels)


def infer_business_meaning(change_fields: set[str]) -> str:
    signals: list[str] = []
    if "price" in change_fields:
        signals.append("疑似在调整成交门槛或清仓节奏")
    if {"promotion_copy", "discount_copy"} & change_fields:
        signals.append("疑似在强化短期促销或活动转化")
    if {"new_badge", "featured_products"} & change_fields:
        signals.append("疑似在推动新品曝光或调整当前主推款")
    if "cta_text" in change_fields:
        signals.append("页面目标可能更偏向直接转化")
    if {"spec_keywords", "hero_copy", "product_title"} & change_fields:
        signals.append("品牌卖点表达可能在微调")
    if not signals:
        return "当前只确认页面字段有变化，业务含义暂不确定。"
    return "；".join(unique_in_order(signals)) + "。"


def infer_next_action(change_fields: set[str]) -> str:
    if "price" in change_fields:
        return "人工打开页面复核价格、折扣范围和适用 SKU，并判断是否需要调整当前报价口径。"
    if {"promotion_copy", "discount_copy"} & change_fields:
        return "人工打开首页或活动页复核促销入口、活动力度和主推品类，并判断是否需要同步销售或选品侧提醒。"
    if {"new_badge", "featured_products"} & change_fields:
        return "人工复核新增主推款或新品系列，并判断是否要补做竞品对比备注。"
    if "cta_text" in change_fields:
        return "确认 CTA 是否从品牌表达转向促销导向，必要时同步销售话术。"
    if {"spec_keywords", "hero_copy", "product_title"} & change_fields:
        return "复核卖点关键词是否变化，必要时更新竞品对比维度。"
    return "先人工查看页面，再决定是否需要补充新的监控字段。"


def build_item(event: dict) -> dict:
    changes = event.get("changes") or []
    change_fields = {str(change.get("field", "")).strip() for change in changes if change.get("field")}
    change_types = infer_change_types(changes)
    manual_review = bool(change_fields & MANUAL_REVIEW_FIELDS or "price" in change_fields)

    return {
        "competitor_name": event.get("company_name"),
        "page_name": event.get("page_name"),
        "page_type": event.get("page_type"),
        "watch_url": event.get("watch_url"),
        "change_types": change_types,
        "change_summary": "；".join(summarize_field_change(change) for change in changes),
        "possible_business_meaning": infer_business_meaning(change_fields),
        "needs_manual_review": manual_review,
        "manual_review_reason": "涉及价格、促销或上新等高价值字段。" if manual_review else "当前变化以表达层为主，可低优先级复核。",
        "suggested_next_action": infer_next_action(change_fields),
        "observed_at": event.get("observed_at"),
        "focus_fields": event.get("focus_fields") or [],
        "field_changes": [
            {
                "field": change.get("field"),
                "label": to_label(str(change.get("field", "")).strip()),
                "before": change.get("before"),
                "after": change.get("after"),
            }
            for change in changes
        ],
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# 竞品变化摘要",
        "",
        "## 监控概览",
        f"- 监控对象：{summary.get('company_scope', '未标注')}",
        f"- 本次有明显变化的页面：{summary.get('changed_page_count', 0)}",
        f"- 生成时间：{summary.get('generated_at', '未标注')}",
        "",
    ]

    for index, item in enumerate(summary.get("items") or [], start=1):
        lines.extend(
            [
                f"## {index}. {item['competitor_name']}",
                "",
                f"- 页面：`{item['page_name']}`",
                f"- 页面类型：`{item['page_type']}`",
                f"- 监控链接：{item['watch_url']}",
                f"- 变化类型：{' + '.join(item['change_types'])}",
                f"- 变化内容简述：{item['change_summary']}",
                f"- 可能业务含义：{item['possible_business_meaning']}",
                f"- 是否需要人工复核：{'是' if item['needs_manual_review'] else '否'}",
                f"- 人工复核原因：{item['manual_review_reason']}",
                f"- 建议下一步动作：{item['suggested_next_action']}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_json).resolve()
    markdown_out = Path(args.markdown_out).resolve()
    json_out = Path(args.json_out).resolve()

    payload = load_json(input_path)
    events = payload.get("events") or []
    items = [build_item(event) for event in events]
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "company_scope": payload.get("company_scope") or "未标注",
        "changed_page_count": len(items),
        "items": items,
    }

    ensure_parent(markdown_out)
    ensure_parent(json_out)
    markdown_out.write_text(render_markdown(summary), encoding="utf-8")
    dump_json(json_out, summary)


if __name__ == "__main__":
    main()
