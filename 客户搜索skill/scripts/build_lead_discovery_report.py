#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow_runtime.contracts import SEARCH_GRADE_TO_ACTION


USER_AGENT = "trade-lead-discovery/0.1"
DEFAULT_MAX_RESULTS = 6
LINKEDIN_HOSTS = ("linkedin.com/company",)
NOISE_HOSTS = (
    "linkedin.com/jobs",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "twitter.com",
    "x.com",
)
CONTACT_HINT_RE = re.compile(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
CONTACT_NAME_RE = re.compile(r"(?:Contact|contact)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})")


@dataclass
class SearchResult:
    query: str
    title: str
    url: str
    snippet: str
    source: str


@dataclass
class Candidate:
    company_name: str = ""
    company_website: str = ""
    source_url: str = ""
    linkedin_url: str = ""
    country_or_market: str = ""
    visible_contact_clues: list[str] = field(default_factory=list)
    search_snippet: str = ""
    search_query_used: list[str] = field(default_factory=list)
    follow_up_suggestion: str = ""
    source_type: str = ""
    source_name: str = ""
    source_url_or_note: str = ""
    freshness: str = ""
    confidence: str = ""
    match_basis: str = ""


def load_json(path: str | None) -> Any:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def dump_json(data: Any, path: str | None) -> None:
    if path:
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dump_text(text: str, path: str | None) -> None:
    if path:
        Path(path).write_text(text, encoding="utf-8")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize_terms(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_text(item) for item in value if normalize_text(item)]
    text = normalize_text(value)
    return [item.strip() for item in text.split(",") if item.strip()]


def normalize_data_sources(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    sources: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            continue
        source_type = normalize_text(item.get("source_type")) or "manual_import"
        source_name = normalize_text(item.get("source_name")) or f"data_source_{index}"
        authorization_status = normalize_text(item.get("authorization_status")) or "user_provided"
        input_format = normalize_text(item.get("input_format")) or "records"
        records = item.get("records") if isinstance(item.get("records"), list) else []
        sources.append(
            {
                "source_type": source_type,
                "source_name": source_name,
                "authorization_status": authorization_status,
                "input_format": input_format,
                "source_url_or_note": normalize_text(item.get("source_url_or_note") or item.get("notes")),
                "field_mapping": item.get("field_mapping") if isinstance(item.get("field_mapping"), dict) else {},
                "records": [record for record in records if isinstance(record, dict)],
            }
        )
    return sources


def normalize_seller_context(value: Any, product_or_offer: str, customer_type: str) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    return {
        "company_name": normalize_text(raw.get("company_name")),
        "product_or_offer": normalize_text(raw.get("product_or_offer")) or product_or_offer,
        "product_categories": normalize_terms(raw.get("product_categories")),
        "target_customer_types": normalize_terms(raw.get("target_customer_types")) or [customer_type],
        "target_industries": normalize_terms(raw.get("target_industries")),
        "value_propositions": normalize_terms(raw.get("value_propositions")),
        "certifications": normalize_terms(raw.get("certifications")),
        "proof_points": normalize_terms(raw.get("proof_points")),
        "authorized_materials": normalize_terms(raw.get("authorized_materials")),
        "excluded_customer_signals": normalize_terms(raw.get("excluded_customer_signals")),
        "forbidden_claims": normalize_terms(raw.get("forbidden_claims")),
    }


def normalize_input(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object.")
    product_or_offer = normalize_text(data.get("product_or_offer"))
    customer_type = normalize_text(data.get("customer_type"))
    normalized = {
        "product_or_offer": product_or_offer,
        "target_market": normalize_text(data.get("target_market")),
        "customer_type": customer_type,
        "search_keywords": normalize_terms(data.get("search_keywords")),
        "must_include": normalize_terms(data.get("must_include")),
        "exclude_terms": normalize_terms(data.get("exclude_terms")),
        "max_results": data.get("max_results") or DEFAULT_MAX_RESULTS,
        "notes": normalize_text(data.get("notes")),
        "industry_lens": normalize_text(data.get("industry_lens")) or "auto",
        "seller_context": normalize_seller_context(data.get("seller_context"), product_or_offer, customer_type),
        "data_sources": normalize_data_sources(data.get("data_sources")),
    }
    if not all(normalized[key] for key in ("product_or_offer", "target_market", "customer_type")):
        raise ValueError("product_or_offer, target_market, and customer_type are required.")
    if not normalized["search_keywords"]:
        raise ValueError("search_keywords must contain at least one keyword.")
    normalized["max_results"] = max(1, min(int(normalized["max_results"]), 20))
    return normalized


def source_summaries(data_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_type": source["source_type"],
            "source_name": source["source_name"],
            "authorization_status": source["authorization_status"],
            "input_format": source["input_format"],
            "record_count": len(source["records"]),
        }
        for source in data_sources
    ]


def run_command(args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout.strip() or proc.stderr.strip()
    except FileNotFoundError:
        return 127, ""


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
        },
    )
    last_error: Exception | None = None
    for _ in range(2):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, http.client.IncompleteRead) as exc:
            last_error = exc
            continue
    if last_error:
        raise last_error
    return ""


def strip_tags(text: str) -> str:
    cleaned = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    cleaned = re.sub(r"<style.*?</style>", " ", cleaned, flags=re.S | re.I)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def ddg_search(query: str, limit: int) -> list[SearchResult]:
    encoded = urllib.parse.urlencode({"q": query})
    html = fetch_url(f"https://html.duckduckgo.com/html/?{encoded}")
    matches = re.findall(
        r'<a rel="nofollow" class="result__a" href="(?P<href>.*?)">(?P<title>.*?)</a>.*?'
        r'<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
        html,
        flags=re.S,
    )
    results: list[SearchResult] = []
    for href, title, snippet in matches[:limit]:
        url = urllib.parse.unquote(href)
        if "uddg=" in href:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            url = urllib.parse.unquote(parsed.get("uddg", [href])[0])
        results.append(
            SearchResult(
                query=query,
                title=strip_tags(title),
                url=url,
                snippet=strip_tags(snippet),
                source="duckduckgo",
            )
        )
    return results


def tavily_search(query: str, limit: int) -> list[SearchResult]:
    code, output = run_command(["tvly", "search", query, "--max-results", str(limit), "--json"])
    if code != 0 or not output:
        return []
    payload = json.loads(output)
    return [
        SearchResult(
            query=query,
            title=normalize_text(item.get("title")),
            url=normalize_text(item.get("url")),
            snippet=normalize_text(item.get("content")),
            source="tavily",
        )
        for item in payload.get("results", [])[:limit]
    ]


def search(query: str, limit: int) -> list[SearchResult]:
    results = tavily_search(query, limit)
    if results:
        return results
    try:
        return ddg_search(query, limit)
    except Exception:
        return []


def load_fixture_results(path: str | None) -> dict[str, list[SearchResult]]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    mapping: dict[str, list[SearchResult]] = {}
    for query, items in payload.items():
        mapping[query] = [
            SearchResult(
                query=query,
                title=normalize_text(item.get("title")),
                url=normalize_text(item.get("url")),
                snippet=normalize_text(item.get("snippet")),
                source=normalize_text(item.get("source")) or "fixture",
            )
            for item in items
        ]
    return mapping


def build_queries(data: dict[str, Any]) -> list[str]:
    product = data["product_or_offer"]
    market = data["target_market"]
    customer_type = data["customer_type"]
    first_keyword = data["search_keywords"][0]
    role_hint = "importer distributor brand buyer"
    queries = [
        f'{product} {market} {customer_type}',
        f'{first_keyword} {market} {role_hint}',
        f'site:linkedin.com/company {product} {market} {customer_type}',
    ]
    for term in data["must_include"][:2]:
        queries.append(f'{product} {market} {customer_type} "{term}"')
    return list(dict.fromkeys(normalize_text(query) for query in queries if normalize_text(query)))


def build_search_strategy(data: dict[str, Any], queries: list[str]) -> dict[str, Any]:
    return {
        "strategy_summary": (
            "先用产品 + 市场 + 客户类型构造主查询，再补角色词、LinkedIn 公司页线索和 must_include 限定词。"
            "如用户提供海关数据、展会名单、行业协会名单或企业自有表格，则作为授权数据源同步归并。"
        ),
        "query_plan": queries,
        "exclude_terms": data["exclude_terms"],
        "must_include": data["must_include"],
        "data_sources": source_summaries(data["data_sources"]),
        "notes": data["notes"],
    }


def website_domain(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc or parsed.path
    host = host.lower().removeprefix("www.")
    return host


def normalize_company_name(text: str) -> str:
    cleaned = re.sub(r"\s*\|\s*LinkedIn.*$", "", text, flags=re.I)
    cleaned = re.sub(r"\s*-\s*LinkedIn.*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*\|\s*.*$", "", cleaned)
    cleaned = re.sub(r"\s*-\s*.*$", "", cleaned)
    return normalize_text(cleaned)


def guess_company_name(result: SearchResult) -> str:
    title = normalize_company_name(result.title)
    if title and "linkedin" not in title.lower():
        return title
    snippet = normalize_text(result.snippet)
    match = re.search(r"([A-Z][A-Za-z0-9&.,' -]{3,})", snippet)
    return normalize_text(match.group(1)) if match else title


def extract_contact_clues(text: str) -> list[str]:
    clues: list[str] = []
    for match in CONTACT_NAME_RE.finditer(text):
        clue = normalize_text(match.group(1))
        if not clue:
            continue
        if clue not in clues:
            clues.append(clue)
    for match in CONTACT_HINT_RE.finditer(text):
        clue = normalize_text(match.group(1))
        if clue and clue not in clues:
            clues.append(clue)
    fallback_titles = re.findall(r"\b(?:Importer|Distributor|Buyer|Retail|Design|Brand)\b", text)
    for clue in fallback_titles:
        clue = normalize_text(clue)
        if clue and clue not in clues:
            clues.append(clue)
    return clues[:3]


def filter_result(result: SearchResult, data: dict[str, Any]) -> bool:
    lower = (result.title + " " + result.snippet + " " + result.url).lower()
    if any(term.lower() in lower for term in data["exclude_terms"]):
        return False
    return True


def dedupe_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for item in results:
        key = item.url.rstrip("/")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def candidate_key(company_name: str, website: str, linkedin_url: str) -> str:
    if website:
        return f"web:{website_domain(website)}"
    if linkedin_url:
        return f"li:{linkedin_url.rstrip('/')}"
    compact = re.sub(r"[^a-z0-9]+", "", company_name.lower())
    return f"name:{compact}"


def follow_up_suggestion(candidate: Candidate) -> str:
    if candidate.company_website and candidate.linkedin_url:
        return "先进入线索整理，再优先核对官网、LinkedIn 与联系人线索的一致性。"
    if candidate.company_website:
        return "先补 LinkedIn 公司页或可见联系人线索，再进入线索整理。"
    if candidate.linkedin_url:
        return "先补官网或公司域名，再进入线索整理。"
    return "当前来源较弱，建议先补官网或 LinkedIn 公司页。"


def result_to_candidate(result: SearchResult, target_market: str) -> Candidate:
    url = normalize_text(result.url)
    is_linkedin = any(host in url.lower() for host in LINKEDIN_HOSTS)
    website = "" if is_linkedin else url
    linkedin_url = url if is_linkedin else ""
    name = guess_company_name(result)
    source_type = "linkedin" if is_linkedin else "web"
    return Candidate(
        company_name=name,
        company_website=website,
        source_url=url,
        linkedin_url=linkedin_url,
        country_or_market=target_market,
        visible_contact_clues=extract_contact_clues(result.title + " " + result.snippet),
        search_snippet=result.snippet[:240],
        search_query_used=[result.query],
        source_type=source_type,
        source_name=result.source,
        source_url_or_note=url,
        freshness="unknown",
        confidence="medium",
        match_basis=f"命中搜索查询：{result.query}",
    )


def first_record_value(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_text(value)
        if value is not None and not isinstance(value, (dict, list)):
            text = normalize_text(value)
            if text:
                return text
    return ""


def mapped_value(record: dict[str, Any], field_mapping: dict[str, Any], standard_key: str, *fallback_keys: str) -> str:
    mapped_key = field_mapping.get(standard_key)
    if isinstance(mapped_key, str) and mapped_key:
        value = first_record_value(record, mapped_key)
        if value:
            return value
    return first_record_value(record, standard_key, *fallback_keys)


def customs_match_basis(record: dict[str, Any]) -> str:
    parts = []
    for label, keys in (
        ("进口商", ("importer_name", "importer", "buyer")),
        ("出口商", ("exporter_name", "exporter", "supplier")),
        ("HS Code", ("hs_code", "hscode")),
        ("产品关键词", ("product_keywords", "product", "goods_description")),
        ("贸易伙伴", ("trade_partner", "partner_country")),
        ("时间区间", ("trade_period", "shipment_date", "date_range")),
    ):
        value = first_record_value(record, *keys)
        if value:
            parts.append(f"{label}: {value}")
    return "；".join(parts)


def build_data_source_candidates(data_sources: list[dict[str, Any]], data: dict[str, Any]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for source in data_sources:
        field_mapping = source["field_mapping"]
        for record in source["records"]:
            company_name = mapped_value(
                record,
                field_mapping,
                "company_name",
                "importer_name",
                "buyer",
                "customer_name",
                "account_name",
            )
            website = mapped_value(record, field_mapping, "company_website", "website", "url", "domain")
            source_url = mapped_value(record, field_mapping, "source_url", "url", "record_url")
            linkedin_url = mapped_value(record, field_mapping, "linkedin_url", "linkedin")
            country_or_market = mapped_value(record, field_mapping, "country_or_market", "country", "market")
            contact = mapped_value(record, field_mapping, "contact", "person_name", "email", "phone")
            note = mapped_value(record, field_mapping, "notes", "note", "summary", "description")
            record_match_basis = mapped_value(record, field_mapping, "match_basis", "reason")
            if source["source_type"] == "customs":
                record_match_basis = record_match_basis or customs_match_basis(record)
            if not record_match_basis:
                record_match_basis = f"来自用户授权数据源：{source['source_name']}"
            candidates.append(
                Candidate(
                    company_name=company_name,
                    company_website=website,
                    source_url=source_url or website or linkedin_url,
                    linkedin_url=linkedin_url,
                    country_or_market=country_or_market or data["target_market"],
                    visible_contact_clues=[contact] if contact else [],
                    search_snippet=note[:240],
                    search_query_used=[],
                    source_type=source["source_type"],
                    source_name=source["source_name"],
                    source_url_or_note=source_url or source["source_url_or_note"] or note,
                    freshness=mapped_value(record, field_mapping, "freshness", "trade_period", "shipment_date", "updated_at") or "unknown",
                    confidence=mapped_value(record, field_mapping, "confidence", "confidence_label") or "medium",
                    match_basis=record_match_basis,
                )
            )
    return candidates


def merge_candidate(base: Candidate, incoming: Candidate) -> Candidate:
    if not base.company_name and incoming.company_name:
        base.company_name = incoming.company_name
    if not base.company_website and incoming.company_website:
        base.company_website = incoming.company_website
    if not base.linkedin_url and incoming.linkedin_url:
        base.linkedin_url = incoming.linkedin_url
    if not base.source_url:
        base.source_url = incoming.source_url
    if incoming.source_url and base.source_url != incoming.source_url and not base.company_website:
        base.source_url = incoming.source_url
    for clue in incoming.visible_contact_clues:
        if clue not in base.visible_contact_clues:
            base.visible_contact_clues.append(clue)
    for query in incoming.search_query_used:
        if query not in base.search_query_used:
            base.search_query_used.append(query)
    if not base.search_snippet and incoming.search_snippet:
        base.search_snippet = incoming.search_snippet
    source_priority = {
        "crm": 5,
        "customs": 5,
        "historical_customer": 5,
        "trade_show": 4,
        "association": 4,
        "referral": 4,
        "manual_import": 3,
        "web": 3,
        "linkedin": 2,
    }
    if source_priority.get(incoming.source_type, 1) > source_priority.get(base.source_type, 0):
        base.source_type = incoming.source_type
    if not base.source_name and incoming.source_name:
        base.source_name = incoming.source_name
    if not base.source_url_or_note and incoming.source_url_or_note:
        base.source_url_or_note = incoming.source_url_or_note
    if not base.freshness and incoming.freshness:
        base.freshness = incoming.freshness
    if not base.confidence and incoming.confidence:
        base.confidence = incoming.confidence
    if not base.match_basis and incoming.match_basis:
        base.match_basis = incoming.match_basis
    return base


def candidate_missing_fields(candidate: Candidate) -> list[str]:
    missing = []
    if not candidate.company_name:
        missing.append("company_name")
    if not candidate.company_website:
        missing.append("company_website")
    if not candidate.linkedin_url:
        missing.append("linkedin_url")
    if not candidate.visible_contact_clues:
        missing.append("visible_contact_clues")
    return missing


def candidate_evidence_grade(candidate: Candidate) -> str:
    has_name = bool(candidate.company_name)
    has_website = bool(candidate.company_website)
    has_linkedin = bool(candidate.linkedin_url)
    has_contacts = bool(candidate.visible_contact_clues)

    if has_name and has_website and has_linkedin:
        return "A"
    if has_name and (has_website or has_linkedin):
        return "B"
    if has_name or has_website or has_linkedin or has_contacts:
        return "C"
    return "D"


def candidate_next_action(candidate: Candidate, grade: str) -> str:
    if grade in {"A", "B", "C"}:
        return SEARCH_GRADE_TO_ACTION[grade]
    if candidate.company_name or candidate.visible_contact_clues:
        return "hold_for_manual_review"
    return "reject_low_evidence"


def candidate_match_reason(candidate: Candidate, grade: str) -> str:
    reasons = []
    if candidate.source_name:
        reasons.append(f"来源：{candidate.source_name}")
    if candidate.match_basis:
        reasons.append(candidate.match_basis)
    if candidate.company_website:
        reasons.append("有官网主体线索")
    if candidate.linkedin_url:
        reasons.append("有 LinkedIn 公司页线索")
    if candidate.visible_contact_clues:
        reasons.append("搜索结果出现可见联系人或角色线索")
    if candidate.search_query_used:
        reasons.append("命中当前搜索策略中的目标关键词组合")
    if not reasons:
        reasons.append("当前只有弱网页片段，尚不能稳定证明主体")
    return f"证据等级 {grade}：{'；'.join(reasons)}。"


def candidate_evidence_summary(candidate: Candidate, grade: str, next_action: str) -> str:
    source_parts = []
    if candidate.company_website:
        source_parts.append("官网")
    if candidate.linkedin_url:
        source_parts.append("LinkedIn")
    if candidate.source_url and candidate.source_url not in {candidate.company_website, candidate.linkedin_url}:
        source_parts.append("公开网页来源")
    if candidate.visible_contact_clues:
        source_parts.append(f"{len(candidate.visible_contact_clues)} 条可见联系人线索")
    if candidate.source_name:
        source_parts.append(f"数据源 {candidate.source_name}")
    if not source_parts:
        source_parts.append("弱网页片段")
    return (
        f"当前候选主要基于{'、'.join(source_parts)}形成。"
        f" 建议动作：{next_action}。"
    )


def normalized_name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def consolidate_candidates(candidates: list[Candidate]) -> list[Candidate]:
    merged_by_name: dict[str, Candidate] = {}
    passthrough: list[Candidate] = []
    for candidate in candidates:
        key = normalized_name_key(candidate.company_name)
        if not key:
            passthrough.append(candidate)
            continue
        if key not in merged_by_name:
            merged_by_name[key] = candidate
        else:
            merged_by_name[key] = merge_candidate(merged_by_name[key], candidate)
    return list(merged_by_name.values()) + passthrough


def build_candidates(
    results: list[SearchResult],
    data: dict[str, Any],
    imported_candidates: list[Candidate] | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, Candidate] = {}
    for candidate in imported_candidates or []:
        key = candidate_key(candidate.company_name, candidate.company_website, candidate.linkedin_url)
        if key in {"name:"}:
            continue
        grouped[key] = merge_candidate(grouped.get(key, Candidate(country_or_market=data["target_market"])), candidate)
    for result in results:
        candidate = result_to_candidate(result, data["target_market"])
        key = candidate_key(candidate.company_name, candidate.company_website, candidate.linkedin_url)
        if key in {"name:"}:
            continue
        grouped[key] = merge_candidate(grouped.get(key, Candidate(country_or_market=data["target_market"])), candidate)
    consolidated = consolidate_candidates(list(grouped.values()))
    ordered = sorted(consolidated, key=lambda item: (not item.company_website, not item.linkedin_url, item.company_name.lower()))
    output = []
    for index, candidate in enumerate(ordered[: data["max_results"]], start=1):
        evidence_grade = candidate_evidence_grade(candidate)
        next_action = candidate_next_action(candidate, evidence_grade)
        output.append(
            {
                "candidate_id": f"candidate-{index:03d}",
                "company_name": candidate.company_name,
                "company_website": candidate.company_website,
                "source_url": candidate.source_url,
                "linkedin_url": candidate.linkedin_url,
                "country_or_market": candidate.country_or_market,
                "visible_contact_clues": candidate.visible_contact_clues,
                "search_snippet": candidate.search_snippet,
                "search_query_used": candidate.search_query_used,
                "evidence_grade": evidence_grade,
                "match_reason": candidate_match_reason(candidate, evidence_grade),
                "missing_fields": candidate_missing_fields(candidate),
                "evidence_summary": candidate_evidence_summary(candidate, evidence_grade, next_action),
                "next_action": next_action,
                "follow_up_suggestion": follow_up_suggestion(candidate),
                "source_type": candidate.source_type,
                "source_name": candidate.source_name,
                "source_url_or_note": candidate.source_url_or_note,
                "freshness": candidate.freshness or "unknown",
                "confidence": candidate.confidence or ("high" if evidence_grade in {"A", "B"} else "medium"),
                "match_basis": candidate.match_basis,
            }
        )
    return output


def build_lead_screening_input(candidates: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    leads = []
    for item in candidates:
        person_name = ""
        email = ""
        normalized_company = normalized_name_key(item["company_name"])
        for clue in item["visible_contact_clues"]:
            if "@" in clue and not email:
                email = clue
            elif (
                not person_name
                and "@" not in clue
                and len(clue.split()) >= 2
                and normalized_name_key(clue) != normalized_company
            ):
                person_name = clue
        leads.append(
            {
                "company_name": item["company_name"],
                "company_website": item["company_website"],
                "person_name": person_name,
                "email": email,
                "country_or_market": item["country_or_market"],
                "source_url": item["source_url"],
                "linkedin_url": item["linkedin_url"],
                "notes": " | ".join(
                    part for part in [data["notes"], item["search_snippet"], item["follow_up_suggestion"]] if part
                ),
                "evidence_grade": item["evidence_grade"],
                "match_reason": item["match_reason"],
                "evidence_summary": item["evidence_summary"],
                "discovery_missing_fields": item["missing_fields"],
                "discovery_next_action": item["next_action"],
                "product_keywords": "",
                "source_type": item["source_type"],
                "source_name": item.get("source_name", ""),
                "source_url_or_note": item.get("source_url_or_note", ""),
                "freshness": item.get("freshness", ""),
                "confidence": item.get("confidence", ""),
                "match_basis": item.get("match_basis", ""),
            }
        )
    return {
        "default_country_or_market": data["target_market"],
        "operator_notes": data["notes"],
        "product_or_offer": data["product_or_offer"],
        "target_customer_type": data["customer_type"],
        "industry_lens": data["industry_lens"],
        "seller_context": data["seller_context"],
        "leads": leads,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Lead Discovery Package",
        "",
        "## Summary",
        f"- Product/Offer: {report['summary']['product_or_offer']}",
        f"- Target Market: {report['summary']['target_market']}",
        f"- Customer Type: {report['summary']['customer_type']}",
        f"- Raw Result Count: {report['summary']['raw_result_count']}",
        f"- Candidate Count: {report['summary']['candidate_count']}",
        f"- Data Sources: {len(report['summary'].get('data_sources', []))}",
        "",
        "## Search Strategy",
        f"- Strategy Summary: {report['search_strategy']['strategy_summary']}",
        "- Query Plan:",
    ]
    for query in report["search_strategy"]["query_plan"]:
        lines.append(f"- {query}")
    if report["search_strategy"]["must_include"]:
        lines.append("- Must Include: " + ", ".join(report["search_strategy"]["must_include"]))
    if report["search_strategy"]["exclude_terms"]:
        lines.append("- Exclude Terms: " + ", ".join(report["search_strategy"]["exclude_terms"]))
    if report["search_strategy"].get("data_sources"):
        lines.append("- Data Sources:")
        for source in report["search_strategy"]["data_sources"]:
            lines.append(
                f"  - {source['source_type']} / {source['source_name']} "
                f"({source['authorization_status']}, {source['record_count']} records)"
            )
    for candidate in report["candidates"]:
        lines.extend(
            [
                "",
                f"## {candidate['candidate_id']}",
                f"- Company: {candidate['company_name'] or '(missing)'}",
                f"- Website: {candidate['company_website'] or '(missing)'}",
                f"- LinkedIn: {candidate['linkedin_url'] or '(missing)'}",
                f"- Source URL: {candidate['source_url'] or '(missing)'}",
                f"- Country/Market: {candidate['country_or_market'] or '(missing)'}",
                f"- Source Type: {candidate['source_type']}",
                f"- Source Name: {candidate.get('source_name') or '(missing)'}",
                f"- Source URL/Note: {candidate.get('source_url_or_note') or '(missing)'}",
                f"- Freshness: {candidate.get('freshness') or 'unknown'}",
                f"- Confidence: {candidate.get('confidence') or 'unknown'}",
                f"- Match Basis: {candidate.get('match_basis') or '(missing)'}",
                f"- Evidence Grade: {candidate['evidence_grade']}",
                f"- Next Action: {candidate['next_action']}",
                "- Visible Contact Clues: "
                + (", ".join(candidate["visible_contact_clues"]) if candidate["visible_contact_clues"] else "(none)"),
                f"- Search Snippet: {candidate['search_snippet'] or '(missing)'}",
                "- Search Query Used: " + (", ".join(candidate["search_query_used"]) if candidate["search_query_used"] else "(none)"),
                f"- Evidence Summary: {candidate['evidence_summary']}",
                f"- Match Reason: {candidate['match_reason']}",
                "- Missing Fields: " + (", ".join(candidate["missing_fields"]) if candidate["missing_fields"] else "(none)"),
                f"- Follow-up Suggestion: {candidate['follow_up_suggestion']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Lead Screening Bridge",
            "```json",
            json.dumps(report["lead_screening_input"], ensure_ascii=False, indent=2),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--fixtures-json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = normalize_input(load_json(args.input_json))
    fixture_results = load_fixture_results(args.fixtures_json)
    queries = build_queries(data)
    search_strategy = build_search_strategy(data, queries)
    imported_candidates = build_data_source_candidates(data["data_sources"], data)
    gathered: list[SearchResult] = []
    for query in queries:
        if query in fixture_results:
            gathered.extend(fixture_results[query])
        else:
            gathered.extend(search(query, limit=data["max_results"]))
    filtered = [item for item in dedupe_results(gathered) if filter_result(item, data)]
    candidates = build_candidates(filtered, data, imported_candidates)
    report = {
        "summary": {
            "product_or_offer": data["product_or_offer"],
            "target_market": data["target_market"],
            "customer_type": data["customer_type"],
            "industry_lens": data["industry_lens"],
            "seller_context_complete": bool(
                data["seller_context"]["product_or_offer"]
                and (
                    data["seller_context"]["value_propositions"]
                    or data["seller_context"]["product_categories"]
                )
            ),
            "queries": queries,
            "raw_result_count": len(filtered),
            "candidate_count": len(candidates),
            "data_sources": source_summaries(data["data_sources"]),
        },
        "search_strategy": search_strategy,
        "candidates": candidates,
        "lead_screening_input": build_lead_screening_input(candidates, data),
    }
    markdown = render_markdown(report)
    dump_json(report, args.json_out)
    dump_text(markdown, args.markdown_out)
    sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
