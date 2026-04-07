#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_FETCH_BACKEND = "html_requests"
DEFAULT_PROCESSOR = "text_json_diff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a minimal changedetection.io watch seed file from the monitoring input."
    )
    parser.add_argument("--input-json", required=True, help="Monitoring input JSON path.")
    parser.add_argument("--json-out", required=True, help="Output JSON path.")
    parser.add_argument(
        "--tag",
        default="竞品监控-skill-demo",
        help="Logical tag name to group the three seed watches.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_seed_watch(target: dict, tag: str) -> dict:
    focus_fields = target.get("focus_fields") or []
    field_names = [field.get("field") if isinstance(field, dict) else field for field in focus_fields]
    field_notes = [
        {
            "field": field.get("field"),
            "why_it_matters": field.get("why_it_matters"),
        }
        for field in focus_fields
        if isinstance(field, dict)
    ]

    page_type = str(target.get("page_type", "")).strip()
    validation_notes = []
    if page_type == "product_detail_page":
        validation_notes = [
            "优先确认产品标题、价格、尺码区上方 CTA 是否都在同一内容块内。",
            "如果页面有推荐商品干扰，优先通过上半屏主要商品区域缩小监控范围。",
        ]
    elif page_type == "new_arrivals_collection_page":
        validation_notes = [
            "优先确认集合页主标题、首屏产品卡片和 NEW 标识是否被稳定抓到。",
            "若集合页顺序噪音过大，先缩到首屏主文案与前 4 个产品卡片。",
        ]
    elif page_type == "homepage_promo_page":
        validation_notes = [
            "优先确认首页促销横幅或首屏活动区，不要把整个首页导航一起纳入。",
            "如果首页轮播频繁变化，先只截促销标题、折扣文案和主 CTA。",
        ]

    return {
        "title": f"{target.get('company_name')} / {target.get('page_name')}",
        "url": target.get("watch_url"),
        "tag": tag,
        "fetch_backend": DEFAULT_FETCH_BACKEND,
        "processor": DEFAULT_PROCESSOR,
        "check_frequency": target.get("check_frequency"),
        "page_type": page_type,
        "watch_goal": target.get("watch_goal"),
        "focus_fields": field_names,
        "field_notes": field_notes,
        "changedetection_setup_notes": {
            "preferred_method": "先在 changedetection.io GUI 中手动建 watch，再按页面主内容区补 include filters。",
            "selector_status": "未在真实 watch 中确认，当前只提供字段级校验口径，不伪造稳定 CSS 选择器。",
            "validation_notes": validation_notes,
            "filter_failure_action": "如果过滤失败，先放宽到页面主内容块；仍不稳定时保留整页监控并用摘要层降噪。",
        },
    }


def main() -> None:
    args = parse_args()
    payload = load_json(Path(args.input_json).resolve())
    watch_targets = payload.get("watch_targets") or []
    seed_payload = {
        "company_scope": payload.get("company_scope"),
        "market": payload.get("market"),
        "product_line": payload.get("product_line"),
        "tag": args.tag,
        "watches": [build_seed_watch(target, args.tag) for target in watch_targets],
    }
    dump_json(Path(args.json_out).resolve(), seed_payload)


if __name__ == "__main__":
    main()
