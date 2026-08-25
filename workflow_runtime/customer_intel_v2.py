from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any


ALLOWED_INDUSTRY_LENSES = {"auto", "industrial", "food", "consumer", "general"}
ALLOWED_STATEMENT_TYPES = {"fact", "inference", "hypothesis"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
CONFIDENCE_WEIGHT = {"high": 3, "medium": 2, "low": 1}
SOURCE_WEIGHT = {"primary": 4, "strong_secondary": 3, "secondary": 2, "weak": 1}
DIMENSION_LABELS = {
    "customer_maturity": "客户成熟度",
    "buying_capacity": "潜在采购能力",
    "technical_customization": "技术定制能力",
    "cooperation_value": "合作价值",
    "price_sensitivity": "价格敏感度",
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def _list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def normalize_seller_context(value: Any, fallback_product: str = "") -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    return {
        "company_name": _text(raw.get("company_name")),
        "product_or_offer": _text(raw.get("product_or_offer")) or _text(fallback_product),
        "product_categories": _list(raw.get("product_categories")),
        "target_customer_types": _list(raw.get("target_customer_types")),
        "target_industries": _list(raw.get("target_industries")),
        "value_propositions": _list(raw.get("value_propositions")),
        "certifications": _list(raw.get("certifications")),
        "proof_points": _list(raw.get("proof_points")),
        "authorized_materials": _list(raw.get("authorized_materials")),
        "excluded_customer_signals": _list(raw.get("excluded_customer_signals")),
        "forbidden_claims": _list(raw.get("forbidden_claims")),
    }


def resolve_industry_lens(requested: str, seller_context: dict[str, Any], company_summary: str) -> str:
    requested = _text(requested).lower() or "auto"
    if requested in ALLOWED_INDUSTRY_LENSES and requested != "auto":
        return requested
    corpus = " ".join(
        [
            company_summary,
            seller_context.get("product_or_offer", ""),
            *seller_context.get("product_categories", []),
            *seller_context.get("target_industries", []),
        ]
    ).lower()
    keyword_sets = {
        "industrial": ("automation", "machinery", "machine", "equipment", "component", "asrs", "plc", "servo", "制造", "机械", "自动化", "零部件", "仓储"),
        "food": ("food", "frozen", "beverage", "private label", "cold chain", "食品", "冷冻", "饮料", "冷链"),
        "consumer": ("retail", "consumer", "apparel", "furniture", "home textile", "零售", "消费品", "服装", "家具", "家纺"),
    }
    scores = {
        lens: sum(1 for keyword in keywords if keyword in corpus)
        for lens, keywords in keyword_sets.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "general"


def _domain(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.lower().removeprefix("www.")


def classify_source_quality(url: str, source_type: str, official_website: str) -> str:
    source = source_type.lower()
    domain = _domain(url)
    official_domain = _domain(official_website)
    if official_domain and domain == official_domain:
        return "primary"
    if domain.endswith("linkedin.com"):
        return "strong_secondary"
    if any(domain.endswith(host) for host in ("facebook.com", "instagram.com", "youtube.com", "x.com", "twitter.com")):
        return "secondary"
    if any(token in source for token in ("government", "registry", "filing", "official")):
        return "primary"
    if any(token in source for token in ("financial", "database", "news", "linkedin", "association")):
        return "strong_secondary"
    if any(token in source for token in ("facebook", "instagram", "youtube", "x", "twitter", "snapshot")):
        return "secondary"
    if source in {"web", "duckduckgo", "tavily", "search"}:
        return "weak"
    return "secondary"


def build_evidence_ledger(
    evidence: list[dict[str, Any]], official_website: str, generated_at: str
) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in evidence:
        if not isinstance(raw, dict):
            continue
        url = _text(raw.get("url"))
        title = _text(raw.get("title")) or url or "Untitled evidence"
        note = _text(raw.get("note") or raw.get("snippet") or raw.get("text"))
        key = (url.rstrip("/"), note[:120])
        if key in seen or (not url and not note):
            continue
        seen.add(key)
        source_type = _text(raw.get("source_type") or raw.get("source") or raw.get("platform")) or "web"
        quality = _text(raw.get("source_quality")) or classify_source_quality(url, source_type, official_website)
        observed_at = _text(raw.get("observed_at_or_period") or raw.get("observed_at")) or "unknown"
        confidence = _text(raw.get("confidence")).lower()
        if confidence not in ALLOWED_CONFIDENCE:
            confidence = "high" if quality == "primary" else "medium" if quality == "strong_secondary" else "low"
        claims = raw.get("claims") if isinstance(raw.get("claims"), list) else []
        ledger.append(
            {
                "evidence_id": f"EV-{len(ledger) + 1:03d}",
                "title": title,
                "url": url,
                "source_type": source_type,
                "source_quality": quality,
                "observed_at_or_period": observed_at,
                "retrieved_at": _text(raw.get("retrieved_at")) or generated_at,
                "freshness": _text(raw.get("freshness")) or ("unknown" if observed_at == "unknown" else "dated"),
                "confidence": confidence,
                "note": note,
                "claims": [item for item in claims if isinstance(item, dict)],
            }
        )
    return ledger


def _tokens(text: str) -> set[str]:
    stopwords = {"the", "and", "for", "with", "from", "into", "your", "their", "company", "business", "products", "solutions", "supply"}
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9+-]{2,}", text.lower())
        if token not in stopwords
    }


def _claim_from_raw(raw: dict[str, Any], evidence_id: str, index: int) -> dict[str, Any] | None:
    statement = _text(raw.get("statement") or raw.get("claim"))
    if not statement:
        return None
    statement_type = _text(raw.get("statement_type") or raw.get("type")).lower()
    if statement_type not in ALLOWED_STATEMENT_TYPES:
        statement_type = "inference"
    confidence = _text(raw.get("confidence")).lower()
    if confidence not in ALLOWED_CONFIDENCE:
        confidence = "low"
    rating = raw.get("rating")
    if isinstance(rating, (int, float)):
        rating = max(1, min(int(round(rating)), 5))
    else:
        rating = None
    return {
        "claim_id": f"CL-{index:03d}",
        "category": _text(raw.get("category")) or "other",
        "statement": statement,
        "statement_type": statement_type,
        "confidence": confidence,
        "evidence_ids": [evidence_id],
        "observed_at_or_period": _text(raw.get("observed_at_or_period")) or "unknown",
        "dimension": _text(raw.get("dimension")),
        "rating": rating,
        "status": "supported" if statement_type == "fact" else "needs_review",
    }


def build_claim_ledger(
    *,
    company_name: str,
    company_summary: str,
    official_website: str,
    evidence_ledger: list[dict[str, Any]],
    recent_signals: list[dict[str, Any]],
    market_signals: list[dict[str, Any]],
    seller_context: dict[str, Any],
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for evidence in evidence_ledger:
        for raw_claim in evidence.get("claims", []):
            claim = _claim_from_raw(raw_claim, evidence["evidence_id"], len(claims) + 1)
            if claim:
                claims.append(claim)

    evidence_by_url = {item["url"].rstrip("/"): item["evidence_id"] for item in evidence_ledger if item["url"]}
    official_ids = [
        item["evidence_id"]
        for item in evidence_ledger
        if item["source_quality"] == "primary"
    ]
    if official_website and not any(item["category"] == "identity" for item in claims):
        claims.append(
            {
                "claim_id": f"CL-{len(claims) + 1:03d}",
                "category": "identity",
                "statement": f"{company_name or '该主体'} 的公开官网指向 {official_website}。",
                "statement_type": "fact",
                "confidence": "high" if official_ids else "medium",
                "evidence_ids": official_ids[:2],
                "observed_at_or_period": "current_snapshot",
                "dimension": "",
                "rating": None,
                "status": "supported" if official_ids else "needs_review",
            }
        )
    if company_summary and not any(item["category"] == "business_line" for item in claims):
        claims.append(
            {
                "claim_id": f"CL-{len(claims) + 1:03d}",
                "category": "business_line",
                "statement": company_summary,
                "statement_type": "inference",
                "confidence": "medium" if official_ids else "low",
                "evidence_ids": official_ids[:3] or [item["evidence_id"] for item in evidence_ledger[:2]],
                "observed_at_or_period": "current_snapshot",
                "dimension": "",
                "rating": None,
                "status": "needs_review",
            }
        )
    for category, signals in (("recent_signal", recent_signals), ("market_signal", market_signals)):
        for signal in signals:
            source_url = _text(signal.get("source_url")).rstrip("/")
            evidence_ids = [evidence_by_url[source_url]] if source_url in evidence_by_url else []
            claims.append(
                {
                    "claim_id": f"CL-{len(claims) + 1:03d}",
                    "category": category,
                    "statement": _text(signal.get("title")) or category,
                    "statement_type": "fact" if signal.get("confidence") == "high" else "inference",
                    "confidence": _text(signal.get("confidence")) or "low",
                    "evidence_ids": evidence_ids,
                    "observed_at_or_period": _text(signal.get("observed_at_or_period")) or "unknown",
                    "dimension": "trigger_timing" if category == "recent_signal" else "",
                    "rating": 4 if category == "recent_signal" and signal.get("confidence") == "high" else 3 if category == "recent_signal" else None,
                    "status": "supported" if evidence_ids else "needs_review",
                }
            )

    product_text = " ".join(
        [
            seller_context.get("product_or_offer", ""),
            *seller_context.get("product_categories", []),
            *seller_context.get("target_industries", []),
        ]
    )
    overlap = _tokens(product_text) & _tokens(company_summary)
    if product_text:
        fit_rating = 4 if len(overlap) >= 2 else 3 if overlap else None
        claims.append(
            {
                "claim_id": f"CL-{len(claims) + 1:03d}",
                "category": "product_fit",
                "statement": (
                    f"客户公开业务与我方产品存在可复核交集：{', '.join(sorted(overlap)[:6])}。"
                    if overlap
                    else "现有公开证据尚未证明客户业务与我方产品的直接匹配关系。"
                ),
                "statement_type": "hypothesis",
                "confidence": "medium" if overlap else "low",
                "evidence_ids": official_ids[:3] or [item["evidence_id"] for item in evidence_ledger[:2]],
                "observed_at_or_period": "current_snapshot",
                "dimension": "product_fit",
                "rating": fit_rating,
                "status": "needs_review",
            }
        )
    return claims


def _dimension_claims(claims: list[dict[str, Any]], dimension: str) -> list[dict[str, Any]]:
    return [item for item in claims if item.get("dimension") == dimension and item.get("rating")]


def _best_dimension(claims: list[dict[str, Any]], dimension: str) -> dict[str, Any] | None:
    matches = _dimension_claims(claims, dimension)
    if not matches:
        return None
    return max(matches, key=lambda item: (CONFIDENCE_WEIGHT.get(item["confidence"], 0), len(item["evidence_ids"])))


def build_verdict_card(
    claims: list[dict[str, Any]], intel_action: str, review_focus: list[str]
) -> dict[str, Any]:
    dimensions: list[dict[str, Any]] = []
    ratings: list[int] = []
    for key, label in DIMENSION_LABELS.items():
        claim = _best_dimension(claims, key)
        if claim:
            ratings.append(claim["rating"])
            dimensions.append(
                {
                    "name": label,
                    "rating": claim["rating"],
                    "display": "★" * claim["rating"] + "☆" * (5 - claim["rating"]),
                    "confidence": claim["confidence"],
                    "basis": claim["statement"],
                    "claim_ids": [claim["claim_id"]],
                    "evidence_ids": claim["evidence_ids"],
                }
            )
        else:
            dimensions.append(
                {
                    "name": label,
                    "rating": None,
                    "display": "公开来源未覆盖",
                    "confidence": "low",
                    "basis": "没有足够证据支持评分。",
                    "claim_ids": [],
                    "evidence_ids": [],
                }
            )
    score = round(sum(ratings) / len(ratings) * 2, 1) if len(ratings) >= 3 else None
    if score is None:
        grade = "未分级"
    elif score >= 8:
        grade = "A"
    elif score >= 6:
        grade = "B"
    else:
        grade = "C"
    return {
        "dimensions": dimensions,
        "score": score,
        "score_status": "scored" if score is not None else "insufficient_evidence",
        "score_basis": "至少三个维度具有带证据评分后才计算综合分。",
        "customer_grade": grade,
        "grade_reason": "按已覆盖维度计算，未覆盖维度不补猜。" if score is not None else "可评分维度少于三个。",
        "intel_decision": "ready_for_email_draft" if intel_action == "ready_for_email_draft" else "needs_manual_review",
        "review_focus": review_focus,
        "one_line_verdict": (
            "证据和产品匹配已达到开发信草稿门槛。"
            if intel_action == "ready_for_email_draft"
            else "当前仍需补主体、产品匹配或采购证据，暂不进入开发信。"
        ),
    }


def _gate(status: str, reason: str) -> dict[str, str]:
    return {"status": status, "reason": reason}


def build_decision(
    *,
    entity_confidence: str,
    risk_rating: str,
    evidence_ledger: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    seller_context: dict[str, Any],
    ambiguity_notes: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    strong_evidence_keys = {
        item["url"].rstrip("/") or item["evidence_id"]
        for item in evidence_ledger
        if SOURCE_WEIGHT.get(item["source_quality"], 0) >= 3
    }
    core_claims = [item for item in claims if item["category"] in {"identity", "business_line"} and item["evidence_ids"]]
    product_fit = _best_dimension(claims, "product_fit")
    identity_gate = (
        _gate("pass", "主体置信度高。") if entity_confidence == "high"
        else _gate("review", "主体置信度中等，需要人工确认。") if entity_confidence == "medium"
        else _gate("hold", "主体置信度低。")
    )
    evidence_gate = (
        _gate("pass", "至少两条强证据支持主体或业务判断。")
        if len(strong_evidence_keys) >= 2 and len(core_claims) >= 2
        else _gate("review", "证据可用但强来源或核心主张不足。")
        if evidence_ledger
        else _gate("hold", "没有可审计证据。")
    )
    has_product = bool(seller_context["product_or_offer"])
    has_offer_proof = bool(
        seller_context["product_categories"]
        or seller_context["value_propositions"]
        or seller_context["proof_points"]
    )
    offer_gate = (
        _gate("pass", "已提供我方产品及至少一类能力依据。") if has_product and has_offer_proof
        else _gate("review", "只有产品名称，缺少价值主张或证明材料。") if has_product
        else _gate("hold", "缺少我方产品上下文。")
    )
    fit_gate = (
        _gate("pass", "公开业务与我方产品存在证据化交集。")
        if product_fit and product_fit["rating"] >= 3
        else _gate("hold", "尚未证明产品匹配。")
    )
    risk_gate = _gate("hold", "风险评级为 High。") if risk_rating == "High" else _gate("pass", "未触发高风险拦截。")
    gates = {
        "identity": identity_gate,
        "evidence": evidence_gate,
        "seller_offer": offer_gate,
        "product_fit": fit_gate,
        "risk": risk_gate,
    }
    ready = all(item["status"] == "pass" for item in gates.values())
    action = "ready_for_email_draft" if ready else "hold_for_manual_review"
    review_focus = list(ambiguity_notes)
    review_focus.extend(item["reason"] for item in gates.values() if item["status"] != "pass")
    review_focus = list(dict.fromkeys(review_focus))[:6]
    decision = {
        "entity_confidence": entity_confidence,
        "evidence_sufficiency": "sufficient" if evidence_gate["status"] == "pass" else "limited" if evidence_ledger else "thin",
        "risk_rating": risk_rating,
        "recommended_next_action": action,
        "manual_review_required": not ready,
        "review_focus": review_focus,
        "decision_gates": gates,
    }
    brief = {
        "decision": action,
        "decision_gates": gates,
        "top_supported_claims": [
            {key: item[key] for key in ("claim_id", "category", "statement", "confidence", "evidence_ids")}
            for item in claims
            if item["status"] == "supported"
        ][:5],
        "research_gaps": review_focus,
        "next_action": (
            "选择并人工批准一个证据化销售角度，再交给开发信 Skill。"
            if ready
            else "先补齐未通过的决策门槛，不生成可发送开发信。"
        ),
    }
    return decision, brief


def _claims_for(claims: list[dict[str, Any]], *categories: str) -> list[dict[str, Any]]:
    allowed = set(categories)
    return [item for item in claims if item["category"] in allowed]


def _claim_text(claims: list[dict[str, Any]], category: str, fallback: str = "公开来源未覆盖") -> str:
    matches = _claims_for(claims, category)
    return matches[0]["statement"] if matches else fallback


def enrich_sales_angles(
    sales_angles: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    evidence_ledger: list[dict[str, Any]],
    seller_context: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence_by_id = {item["evidence_id"]: item for item in evidence_ledger}
    fallback_claims = _claims_for(claims, "product_fit", "recent_signal", "business_line")
    enriched: list[dict[str, Any]] = []
    for index, angle in enumerate(sales_angles, start=1):
        item = dict(angle)
        angle_tokens = _tokens(" ".join(_text(item.get(key)) for key in ("cn", "en", "why")))
        ranked = sorted(
            claims,
            key=lambda claim: (
                len(angle_tokens & _tokens(claim["statement"])),
                CONFIDENCE_WEIGHT.get(claim["confidence"], 0),
            ),
            reverse=True,
        )
        selected_claims = [claim for claim in ranked if angle_tokens & _tokens(claim["statement"])][:2]
        if not selected_claims:
            selected_claims = fallback_claims[:2]
        evidence_ids = list(
            dict.fromkeys(
                evidence_id
                for claim in selected_claims
                for evidence_id in claim.get("evidence_ids", [])
            )
        )[:3]
        item.update(
            {
                "angle_id": f"ANGLE-{index:02d}",
                "approval_status": "proposed",
                "claim_type": "hypothesis",
                "claim_ids": [claim["claim_id"] for claim in selected_claims],
                "evidence_ids": evidence_ids,
                "evidence_refs": list(
                    dict.fromkeys(
                        evidence_by_id[eid]["url"]
                        for eid in evidence_ids
                        if eid in evidence_by_id and evidence_by_id[eid]["url"]
                    )
                ),
                "buyer_or_component_clue": _claim_text(claims, "procurement_clue"),
                "replacement_point": _claim_text(claims, "replacement_point"),
                "authorized_materials": seller_context["authorized_materials"],
                "why_this_angle_fits": item.get("why") or _claim_text(claims, "product_fit"),
            }
        )
        enriched.append(item)
    return enriched


def build_analysis_sections(
    *,
    claims: list[dict[str, Any]],
    verdict: dict[str, Any],
    industry_lens: str,
) -> dict[str, Any]:
    business_claims = _claims_for(claims, "business_line")
    business_lines = [
        {
            "name": f"业务线 {index}",
            "representative_products": [claim["statement"]],
            "customer_types": "公开来源未覆盖",
            "claim_ids": [claim["claim_id"]],
            "evidence_ids": claim["evidence_ids"],
        }
        for index, claim in enumerate(business_claims, start=1)
    ]
    technical_claims = _claims_for(claims, "technical_capability")
    procurement_claims = _claims_for(claims, "procurement_concern", "procurement_clue")
    growth_claims = _claims_for(claims, "growth_opportunity")
    competition_claims = _claims_for(claims, "competition")
    financial_claims = _claims_for(claims, "revenue", "employee_count", "operating_trend", "procurement_behavior")
    score_text = verdict["score"] if verdict["score"] is not None else "未评分"
    return {
        "company_business_breakdown": {
            "business_lines": business_lines,
            "entity_facts": {
                "registration_and_entity": _claim_text(claims, "registration"),
                "address_notes": _claim_text(claims, "address"),
                "facilities": _claim_text(claims, "facility"),
                "management_background": _claim_text(claims, "management"),
            },
            "business_model_judgment": {
                "value": _claim_text(claims, "business_model"),
                "basis": "只采用带 claim_id 与 evidence_id 的主张。",
                "confidence": "medium" if _claims_for(claims, "business_model") else "low",
            },
        },
        "tech_capability_procurement_concerns": {
            "industry_lens": industry_lens,
            "technical_stack": "；".join(item["statement"] for item in technical_claims) or "公开来源未覆盖",
            "technical_stack_basis": [item["claim_id"] for item in technical_claims],
            "procurement_concerns": [
                {
                    "item": item["statement"],
                    "assessment": item["statement_type"],
                    "priority": "待确认" if item["statement_type"] != "fact" else "已观察",
                    "claim_id": item["claim_id"],
                    "evidence_ids": item["evidence_ids"],
                }
                for item in procurement_claims
            ],
            "most_important_for_us": procurement_claims[0]["statement"] if procurement_claims else "公开来源未覆盖",
        },
        "scale_financial_signals": {
            "revenue": _claim_text(claims, "revenue", "公开免费来源未覆盖"),
            "employee_count": _claim_text(claims, "employee_count", "公开免费来源未覆盖"),
            "operating_trend": _claim_text(claims, "operating_trend"),
            "procurement_behavior_interpretation": _claim_text(claims, "procurement_behavior"),
            "claim_ids": [item["claim_id"] for item in financial_claims],
            "manual_check_entry": "优先补工商/注册局、可信财务数据库和公司官方材料。",
        },
        "sales_model_procurement_logic": {
            "sales_model": _claim_text(claims, "sales_model"),
            "sales_cycle": _claim_text(claims, "sales_cycle"),
            "supplier_entry_point": _claim_text(claims, "supplier_entry_point"),
            "basis": "事实与推断均保留 claim_id，不把行业常识写成客户事实。",
        },
        "competition_map": {
            "potential_competitors": [
                {
                    "name_or_set": item["statement"],
                    "claim_id": item["claim_id"],
                    "evidence_ids": item["evidence_ids"],
                }
                for item in competition_claims
            ],
            "note": "这是潜在竞争集合，不代表逐项直接竞争。" if competition_claims else "公开来源未覆盖。",
        },
        "growth_opportunities": [
            {
                "opportunity": item["statement"],
                "logic": item["statement_type"],
                "status": "已观察" if item["statement_type"] == "fact" else "推断，需人工验证",
                "claim_ids": [item["claim_id"]],
                "evidence_ids": item["evidence_ids"],
            }
            for item in growth_claims
        ],
        "image_summary": {
            "summary_cn": verdict["one_line_verdict"],
            "score": verdict["score"],
            "customer_grade": verdict["customer_grade"],
            "maximum_opportunity": growth_claims[0]["statement"] if growth_claims else _claim_text(claims, "product_fit"),
            "maximum_risk": "；".join(verdict["review_focus"][:2]) or "当前未发现额外高风险信号。",
            "strategy": _claim_text(claims, "supplier_entry_point", "先补产品匹配与采购场景证据，再决定触达策略。"),
        },
    }


def upgrade_customer_intel_report(
    *,
    lead: dict[str, Any],
    raw_evidence: list[dict[str, Any]],
    company_summary: str,
    official_website: str,
    recent_signals: list[dict[str, Any]],
    market_signals: list[dict[str, Any]],
    sales_angles: list[dict[str, Any]],
    risk_rating: str,
    risk_reasons: list[str],
    entity_confidence: str,
    ambiguity_notes: list[str],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    seller_context = normalize_seller_context(lead.get("seller_context"), _text(lead.get("product_or_offer")))
    industry_lens = resolve_industry_lens(_text(lead.get("industry_lens")), seller_context, company_summary)
    evidence_ledger = build_evidence_ledger(raw_evidence, official_website, generated_at)
    claim_ledger = build_claim_ledger(
        company_name=_text(lead.get("company_name")),
        company_summary=company_summary,
        official_website=official_website,
        evidence_ledger=evidence_ledger,
        recent_signals=recent_signals,
        market_signals=market_signals,
        seller_context=seller_context,
    )
    intel_decision, decision_brief = build_decision(
        entity_confidence=entity_confidence,
        risk_rating=risk_rating,
        evidence_ledger=evidence_ledger,
        claims=claim_ledger,
        seller_context=seller_context,
        ambiguity_notes=ambiguity_notes,
    )
    verdict = build_verdict_card(claim_ledger, intel_decision["recommended_next_action"], intel_decision["review_focus"])
    intel_decision["sieger_status"] = verdict["intel_decision"]
    intel_decision["sieger_review_focus"] = verdict["review_focus"]
    enriched_angles = enrich_sales_angles(sales_angles, claim_ledger, evidence_ledger, seller_context)
    return {
        "contract_version": "2.0",
        "seller_context": seller_context,
        "industry_lens": industry_lens,
        "decision_brief": decision_brief,
        "intel_decision": intel_decision,
        "verdict_card": verdict,
        "sales_angles": enriched_angles,
        "evidence_ledger": evidence_ledger,
        "claim_ledger": claim_ledger,
        "risk_rating": risk_rating,
        "risk_reasons": risk_reasons,
        **build_analysis_sections(claims=claim_ledger, verdict=verdict, industry_lens=industry_lens),
        "sieger_standard": {
            "name": "SIEGER",
            "version": "2.0-2026-08-25",
            "iron_rules": [
                "每个结论通过 claim_id 关联 evidence_id。",
                "事实、推断和假设分开表达。",
                "少于三个有证据评分维度时不计算综合分。",
                "未通过决策门槛或销售角度未获批准时，不进入开发信。",
            ],
        },
    }
