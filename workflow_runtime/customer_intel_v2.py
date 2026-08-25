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
TRUSTED_STRONG_SECONDARY_DOMAINS = {
    "bloomberg.com",
    "crunchbase.com",
    "dnb.com",
    "linkedin.com",
    "reuters.com",
    "thecompanycheck.com",
    "tofler.in",
}
BARE_PUBLIC_SUFFIX_LABELS = {"ac", "co", "com", "edu", "gob", "gov", "int", "mil", "net", "org"}
TRUSTED_GOVERNMENT_SUFFIXES = {
    "gc.ca",
    "go.jp",
    "go.kr",
    "gob.cl",
    "gob.es",
    "gob.mx",
    "gob.pe",
    "gouv.fr",
    "gov.ae",
    "gov.au",
    "gov.bd",
    "gov.br",
    "gov.cn",
    "gov.hk",
    "gov.id",
    "gov.in",
    "gov.ke",
    "gov.lk",
    "gov.my",
    "gov.ng",
    "gov.nz",
    "gov.ph",
    "gov.pk",
    "gov.qa",
    "gov.sa",
    "gov.sg",
    "gov.tw",
    "gov.uk",
    "gov.vn",
    "gov.za",
}
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
        "industrial": (
            "industrial",
            "industrial automation",
            "factory automation",
            "warehouse automation",
            "material handling",
            "automation",
            "machinery",
            "machine",
            "manufacturing",
            "robotics",
            "robot",
            "plc",
            "servo",
            "cnc",
            "pneumatic",
            "conveyor",
            "asrs",
            "工业",
            "工厂自动化",
            "工业自动化",
            "机械",
            "制造",
            "机器人",
            "仓储自动化",
            "物料搬运",
        ),
        "food": (
            "food",
            "food processing",
            "frozen",
            "beverage",
            "private label",
            "cold chain",
            "bakery",
            "dairy",
            "seafood",
            "食品",
            "食品加工",
            "冷冻",
            "饮料",
            "冷链",
            "烘焙",
            "乳制品",
            "海鲜",
        ),
        "consumer": (
            "retail",
            "consumer",
            "consumer electronics",
            "home appliance",
            "apparel",
            "furniture",
            "home textile",
            "cosmetics",
            "toys",
            "零售",
            "消费电子",
            "消费品",
            "家电",
            "服装",
            "家具",
            "家纺",
            "化妆品",
            "玩具",
        ),
    }
    scores = {
        lens: sum(1 for keyword in keywords if keyword in corpus)
        for lens, keywords in keyword_sets.items()
    }
    best_score = max(scores.values(), default=0)
    winners = [lens for lens, score in scores.items() if score == best_score and score > 0]
    return winners[0] if len(winners) == 1 else "general"


def _domain(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    return (parsed.hostname or "").lower().removeprefix("www.")


def _plausible_official_domain(domain: str) -> bool:
    labels = [label for label in domain.split(".") if label]
    if len(labels) < 2:
        return False
    if len(labels) == 2 and labels[0] in BARE_PUBLIC_SUFFIX_LABELS:
        return False
    government_labels = {"go", "gob", "gouv", "gov"}.intersection(labels)
    return not government_labels or bool(_government_source_key(domain))


def _government_source_key(domain: str) -> str:
    labels = domain.split(".")
    if domain.endswith(".gov") and len(labels) >= 2:
        return ".".join(labels[-2:])
    for suffix in TRUSTED_GOVERNMENT_SUFFIXES:
        if domain.endswith(f".{suffix}"):
            return ".".join(labels[-(len(suffix.split(".")) + 1):])
    return ""


def _trusted_strong_source_key(domain: str) -> str:
    return next(
        (
            host
            for host in TRUSTED_STRONG_SECONDARY_DOMAINS
            if domain == host or domain.endswith(f".{host}")
        ),
        "",
    )


def _independent_source_key(url: str, source_identity: str = "") -> str:
    domain = _domain(url)
    if domain:
        return _trusted_strong_source_key(domain) or _government_source_key(domain) or domain
    return _text(source_identity).casefold()


def _auditable_http_url(value: str) -> str:
    text = _text(value)
    if not text:
        return ""
    parsed = urllib.parse.urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return text


def classify_source_quality(url: str, source_type: str, official_website: str) -> str:
    domain = _domain(url)
    official_domain = _domain(official_website)
    if _plausible_official_domain(official_domain) and domain == official_domain:
        return "primary"
    if _government_source_key(domain):
        return "primary"
    if _trusted_strong_source_key(domain):
        return "strong_secondary"
    if any(
        domain == host or domain.endswith(f".{host}")
        for host in ("facebook.com", "instagram.com", "youtube.com", "x.com", "twitter.com")
    ):
        return "secondary"
    source = re.sub(r"[^a-z0-9]+", "_", source_type.lower()).strip("_")
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
        url = _auditable_http_url(_text(raw.get("url") or raw.get("source_url")))
        source_identity = _text(
            raw.get("source_id")
            or raw.get("source_name")
            or raw.get("source_title")
            or raw.get("title")
        )
        title = _text(raw.get("title")) or source_identity or url
        note = _text(raw.get("note") or raw.get("snippet") or raw.get("text"))
        if not title or (
            not url
            and title.casefold() in {"untitled evidence", "unknown", "n/a", "na", "web", "source"}
        ):
            continue
        key = (url.rstrip("/"), note[:120])
        if key in seen or (not url and not note):
            continue
        seen.add(key)
        source_type = _text(raw.get("source_type") or raw.get("source") or raw.get("platform")) or "web"
        quality = classify_source_quality(url, source_type, official_website)
        if not url and quality in {"primary", "strong_secondary"}:
            quality = "secondary"
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
                "source_identity": source_identity or title,
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
    official_domain = _domain(official_website)
    official_ids = [
        item["evidence_id"]
        for item in evidence_ledger
        if _plausible_official_domain(official_domain)
        and _domain(item.get("url", "")) == official_domain
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
        summary_tokens = _tokens(company_summary)
        summary_evidence_ids = [
            item["evidence_id"]
            for item in evidence_ledger
            if summary_tokens
            and summary_tokens.intersection(
                _tokens(
                    " ".join(
                        [
                            _text(item.get("title")),
                            _text(item.get("note")),
                            *[
                                _text(claim.get("statement") or claim.get("claim"))
                                for claim in item.get("claims") or []
                                if isinstance(claim, dict)
                            ],
                        ]
                    )
                )
            )
        ]
        claims.append(
            {
                "claim_id": f"CL-{len(claims) + 1:03d}",
                "category": "business_line",
                "statement": company_summary,
                "statement_type": "inference",
                "confidence": "medium" if official_ids else "low",
                "evidence_ids": summary_evidence_ids[:3],
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
    if product_text and not any(item["category"] == "product_fit" for item in claims):
        fit_evidence_ids = list(
            dict.fromkeys(
                evidence_id
                for claim in claims
                if claim.get("category") == "business_line"
                and overlap.intersection(_tokens(_text(claim.get("statement"))))
                for evidence_id in claim.get("evidence_ids") or []
            )
        )
        fit_rating = 4 if len(overlap) >= 2 and fit_evidence_ids else 3 if overlap and fit_evidence_ids else None
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
                "evidence_ids": fit_evidence_ids[:3],
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
    evidence_by_id = {item["evidence_id"]: item for item in evidence_ledger}

    def strong_source_keys(selected_claims: list[dict[str, Any]]) -> set[str]:
        keys: set[str] = set()
        for claim in selected_claims:
            for evidence_id in claim.get("evidence_ids") or []:
                evidence = evidence_by_id.get(evidence_id)
                if not evidence or SOURCE_WEIGHT.get(evidence.get("source_quality"), 0) < 3:
                    continue
                key = _independent_source_key(
                    evidence.get("url", ""), evidence.get("source_identity", "")
                )
                if key:
                    keys.add(key)
        return keys

    identity_claims = [
        item
        for item in claims
        if item["category"] in {"identity", "registration", "address"}
        and item.get("status") == "supported"
        and item.get("evidence_ids")
    ]
    business_claims = [
        item
        for item in claims
        if item["category"] in {"business_line", "business_model"}
        and item.get("status") == "supported"
        and item.get("evidence_ids")
    ]
    identity_strong_keys = strong_source_keys(identity_claims)
    business_strong_keys = strong_source_keys(business_claims)
    core_strong_keys = identity_strong_keys | business_strong_keys
    product_fit_candidates = [
        item
        for item in claims
        if item.get("category") == "product_fit" and item.get("rating")
    ]
    product_fit = max(
        product_fit_candidates,
        key=lambda item: (
            bool(strong_source_keys([item])),
            CONFIDENCE_WEIGHT.get(item["confidence"], 0),
            len(item.get("evidence_ids") or []),
        ),
        default=None,
    )
    product_fit_strong_keys = strong_source_keys([product_fit]) if product_fit else set()
    identity_gate = (
        _gate("pass", "主体置信度高。") if entity_confidence == "high"
        else _gate("review", "主体置信度中等，需要人工确认。") if entity_confidence == "medium"
        else _gate("hold", "主体置信度低。")
    )
    evidence_gate = (
        _gate("pass", "至少两个独立强来源分别绑定主体与业务主张。")
        if identity_strong_keys and business_strong_keys and len(core_strong_keys) >= 2
        else _gate("review", "强来源未绑定到完整的主体与业务主张，或独立来源不足。")
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
        _gate("pass", "产品匹配主张已绑定至少一个强来源。")
        if product_fit and product_fit["rating"] >= 3 and product_fit_strong_keys
        else _gate("hold", "尚未以强来源证明产品匹配。")
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


def _first_claim(claims: list[dict[str, Any]], *categories: str) -> dict[str, Any] | None:
    matches = _claims_for(claims, *categories)
    return matches[0] if matches else None


INDUSTRIAL_CONCEPT_RULES = (
    ("asrs", (r"(?<![A-Za-z0-9_])asrs(?![A-Za-z0-9_])",), "相关系统", "the relevant system"),
    (
        "industrial-automation",
        (r"\bindustrial[\s-]+automation(?:[\s-]+module)?\b", r"工业自动化(?:模块|系统|方案)?", r"自动化模块"),
        "相关业务应用",
        "the relevant business application",
    ),
    (
        "engineering-integration",
        (r"\b(?:engineering|system)[\s-]+integration\b", r"工程集成", r"系统集成"),
        "相关业务协作",
        "the relevant business coordination",
    ),
    (
        "bom",
        (r"(?<![A-Za-z0-9_])bom(?![A-Za-z0-9_])", r"\bbill\s+of\s+materials\b", r"物料清单"),
        "相关配置",
        "the relevant configuration",
    ),
    ("motor", (r"\bmotors?\b", r"电机"), "相关部件", "the relevant part"),
    ("drive", (r"\bdrives?\b", r"驱动"), "相关控制要求", "the relevant control requirements"),
    (
        "warehouse-automation",
        (r"warehouse[\s-]+automation", r"仓储自动化"),
        "相关仓储应用",
        "the relevant warehouse application",
    ),
    ("storage", (r"\bstorage\b",), "相关方案", "the relevant solution"),
    (
        "material-handling",
        (r"\bmaterial[\s-]+handling\b", r"物料搬运"),
        "相关应用",
        "the relevant application",
    ),
)

INDUSTRIAL_CONCEPT_LABELS = {
    "asrs": ("ASRS", "ASRS"),
    "industrial-automation": ("工业自动化", "industrial automation"),
    "engineering-integration": ("工程集成", "engineering integration"),
    "bom": ("BOM", "BOM"),
    "motor": ("电机", "motor"),
    "drive": ("驱动", "drive"),
    "warehouse-automation": ("仓储自动化", "warehouse automation"),
    "storage": ("仓储方案", "storage solution"),
    "material-handling": ("物料搬运", "material handling"),
}


def _seller_offer_text(seller_context: dict[str, Any]) -> str:
    return " ".join(
        [
            _text(seller_context.get("product_or_offer")),
            *_list(seller_context.get("product_categories")),
            *_list(seller_context.get("value_propositions")),
        ]
    ).lower()


def _matches_any_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _supported_industrial_concepts(
    selected_claims: list[dict[str, Any]], seller_context: dict[str, Any]
) -> set[str]:
    claim_text = " ".join(_text(claim.get("statement")) for claim in selected_claims).lower()
    seller_text = _seller_offer_text(seller_context)
    return {
        name
        for name, patterns, _, _ in INDUSTRIAL_CONCEPT_RULES
        if _matches_any_pattern(claim_text, patterns) and _matches_any_pattern(seller_text, patterns)
    }


def _sanitize_angle_text(
    text: str,
    selected_claims: list[dict[str, Any]],
    seller_context: dict[str, Any],
) -> str:
    text = _text(text)
    if not text:
        return ""
    supported = _supported_industrial_concepts(selected_claims, seller_context)
    use_chinese = bool(re.search(r"[\u4e00-\u9fff]", text))
    sanitized = text
    for name, patterns, chinese_replacement, english_replacement in INDUSTRIAL_CONCEPT_RULES:
        if name in supported:
            continue
        if not _matches_any_pattern(sanitized, patterns):
            continue
        replacement = chinese_replacement if use_chinese else english_replacement
        for pattern in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    return _text(sanitized)


def _claim_basis(
    claims: list[dict[str, Any]], seller_context: dict[str, Any]
) -> str:
    return "；".join(
        _sanitize_angle_text(claim.get("statement", ""), claims, seller_context)
        for claim in claims
        if _text(claim.get("statement"))
    )


def build_evidence_sales_angles(
    claims: list[dict[str, Any]], seller_context: dict[str, Any], industry_lens: str
) -> list[dict[str, Any]]:
    offer = seller_context.get("product_or_offer") or "我方产品/方案"
    value_propositions = seller_context.get("value_propositions") or []
    value_text = "、".join(value_propositions[:3]) or "选型、交期和定制支持"
    product_fit = _first_claim(claims, "product_fit")
    procurement_clue = _first_claim(claims, "procurement_clue")
    supplier_entry = _first_claim(claims, "supplier_entry_point")
    replacement = _first_claim(claims, "replacement_point")
    procurement_concern = _first_claim(claims, "procurement_concern")
    technical = _first_claim(claims, "technical_capability")
    business_line = _first_claim(claims, "business_line")

    if industry_lens != "industrial":
        return []
    if not offer or not product_fit or not (procurement_clue or supplier_entry):
        return []

    clue = procurement_clue or supplier_entry
    opening_claims = [clue, product_fit]
    supported_concepts = _supported_industrial_concepts(opening_claims, seller_context)
    topic_cn = "、".join(
        INDUSTRIAL_CONCEPT_LABELS.get(name, (name, name))[0]
        for name in sorted(supported_concepts)
    ) or "公开线索中的具体产品线或项目"
    topic_en = ", ".join(
        INDUSTRIAL_CONCEPT_LABELS.get(name, (name, name))[1]
        for name in sorted(supported_concepts)
    ) or "the specific product line or project in the public clue"
    angles: list[dict[str, Any]] = [
        {
            "cn": (
                f"围绕{topic_cn}先确认公开线索中的规格、接口和采购约束，"
                f"再评估我方 {offer} 是否匹配。"
            ),
            "en": (
                f"Based on the public clue about {topic_en}, could we confirm the relevant specifications, "
                f"interfaces and purchasing constraints before assessing whether our {offer} fits?"
            ),
            "why": _claim_basis(opening_claims, seller_context),
            "avoid": "不要把公开线索中的可能性写成已确认的采购计划、现用品牌或替代意向。",
            "_claim_ids": [clue["claim_id"], product_fit["claim_id"]],
        }
    ]

    if replacement or procurement_concern:
        replacement_basis = replacement or procurement_concern
        claim_ids = [replacement_basis["claim_id"], product_fit["claim_id"]]
        if procurement_concern and procurement_concern["claim_id"] not in claim_ids:
            claim_ids.append(procurement_concern["claim_id"])
        replacement_claims = [replacement_basis, product_fit]
        if procurement_concern and procurement_concern["claim_id"] not in {
            claim["claim_id"] for claim in replacement_claims
        }:
            replacement_claims.append(procurement_concern)
        angles.append(
            {
                "cn": (
                    f"先确认公开线索中的具体需求和约束，再用我方 {offer} 对照 {value_text}，"
                    "以参数或技术资料核对作为下一步。"
                ),
                "en": (
                    "After confirming the specific requirements and constraints in the public clue, we can "
                    f"compare our {offer} against {', '.join(value_propositions[:3]) or 'selection, lead time and customization'} "
                    "and use a parameter or technical-document review as the next step."
                ),
                "why": _claim_basis(replacement_claims, seller_context),
                "avoid": "没有现用型号和工况参数时，不承诺兼容、降本比例、寿命或交期优势。",
                "_claim_ids": claim_ids,
            }
        )

    if technical or business_line:
        engineering_basis = technical or business_line
        engineering_claims = [engineering_basis, product_fit]
        if technical:
            angle_cn = (
                f"把首轮目标设为工程需求确认，而不是立即报价。围绕有证据支持的技术能力，"
                f"提供一页 {offer} 选型清单，邀请相关工程人员确认应用参数和验证条件。"
            )
            angle_en = (
                "A practical first step may be an engineering-fit review rather than a price-first pitch. "
                f"We can share a one-page selection checklist for our {offer} and ask the relevant technical "
                "contact to confirm the application parameters and validation conditions."
            )
        else:
            angle_cn = (
                f"把首轮目标设为应用需求确认，而不是立即报价。围绕公开业务线提供一页 {offer} "
                "适配问题清单，请相关产品或采购人员确认需求与验证条件。"
            )
            angle_en = (
                "A practical first step may be an application-fit review rather than a price-first pitch. "
                f"We can share a one-page fit checklist for our {offer} and ask the relevant product or sourcing "
                "contact to confirm the requirements and validation conditions."
            )
        angles.append(
            {
                "cn": angle_cn,
                "en": angle_en,
                "why": _claim_basis(engineering_claims, seller_context),
                "avoid": (
                    "不要把对方具备研发能力推断成其正在采购，也不要未经确认发送大而全目录。"
                    if technical
                    else "不要把公开业务线写成已确认采购，也不要未经确认发送大而全目录。"
                ),
                "_claim_ids": [engineering_basis["claim_id"], product_fit["claim_id"]],
            }
        )
    return angles[:3]


def enrich_sales_angles(
    sales_angles: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    evidence_ledger: list[dict[str, Any]],
    seller_context: dict[str, Any],
    industry_lens: str,
) -> list[dict[str, Any]]:
    evidence_by_id = {item["evidence_id"]: item for item in evidence_ledger}
    fallback_claims = _claims_for(claims, "product_fit", "recent_signal", "business_line")
    evidence_angles = build_evidence_sales_angles(claims, seller_context, industry_lens)
    source_angles = evidence_angles or sales_angles
    enriched: list[dict[str, Any]] = []
    for index, angle in enumerate(source_angles, start=1):
        item = dict(angle)
        preferred_claim_ids = item.pop("_claim_ids", [])
        if preferred_claim_ids:
            selected_claims = [claim for claim in claims if claim["claim_id"] in preferred_claim_ids]
        else:
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
        for key in ("cn", "en", "why", "avoid"):
            item[key] = _sanitize_angle_text(item.get(key, ""), selected_claims, seller_context)
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
                "buyer_or_component_clue": _sanitize_angle_text(
                    _claim_text(selected_claims, "procurement_clue"), selected_claims, seller_context
                ),
                "replacement_point": _sanitize_angle_text(
                    _claim_text(selected_claims, "replacement_point"), selected_claims, seller_context
                ),
                "authorized_materials": seller_context["authorized_materials"],
                "why_this_angle_fits": item.get("why") or _sanitize_angle_text(
                    _claim_text(selected_claims, "product_fit"), selected_claims, seller_context
                ),
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
    enriched_angles = enrich_sales_angles(
        sales_angles,
        claim_ledger,
        evidence_ledger,
        seller_context,
        industry_lens,
    )
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
