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


def normalize_input(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object.")
    normalized = {
        "product_or_offer": normalize_text(data.get("product_or_offer")),
        "target_market": normalize_text(data.get("target_market")),
        "customer_type": normalize_text(data.get("customer_type")),
        "search_keywords": normalize_terms(data.get("search_keywords")),
        "must_include": normalize_terms(data.get("must_include")),
        "exclude_terms": normalize_terms(data.get("exclude_terms")),
        "max_results": data.get("max_results") or DEFAULT_MAX_RESULTS,
        "notes": normalize_text(data.get("notes")),
    }
    if not all(normalized[key] for key in ("product_or_offer", "target_market", "customer_type")):
        raise ValueError("product_or_offer, target_market, and customer_type are required.")
    if not normalized["search_keywords"]:
        raise ValueError("search_keywords must contain at least one keyword.")
    normalized["max_results"] = max(1, min(int(normalized["max_results"]), 20))
    return normalized


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
    )


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
    if incoming.source_type == "linkedin" and base.source_type != "web":
        base.source_type = "linkedin"
    elif incoming.source_type == "web":
        base.source_type = "web"
    return base


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


def build_candidates(results: list[SearchResult], data: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, Candidate] = {}
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
                "follow_up_suggestion": follow_up_suggestion(candidate),
                "source_type": candidate.source_type,
            }
        )
    return output


def build_lead_screening_input(candidates: list[dict[str, Any]], notes: str) -> dict[str, Any]:
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
                    part for part in [notes, item["search_snippet"], item["follow_up_suggestion"]] if part
                ),
                "product_keywords": "",
                "source_type": item["source_type"],
            }
        )
    return {"default_country_or_market": "", "operator_notes": notes, "leads": leads}


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
        "",
        "## Queries",
    ]
    for query in report["summary"]["queries"]:
        lines.append(f"- {query}")
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
                "- Visible Contact Clues: "
                + (", ".join(candidate["visible_contact_clues"]) if candidate["visible_contact_clues"] else "(none)"),
                f"- Search Snippet: {candidate['search_snippet'] or '(missing)'}",
                "- Search Query Used: " + (", ".join(candidate["search_query_used"]) if candidate["search_query_used"] else "(none)"),
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
    gathered: list[SearchResult] = []
    for query in queries:
        if query in fixture_results:
            gathered.extend(fixture_results[query])
        else:
            gathered.extend(search(query, limit=data["max_results"]))
    filtered = [item for item in dedupe_results(gathered) if filter_result(item, data)]
    candidates = build_candidates(filtered, data)
    report = {
        "summary": {
            "product_or_offer": data["product_or_offer"],
            "target_market": data["target_market"],
            "customer_type": data["customer_type"],
            "queries": queries,
            "raw_result_count": len(filtered),
            "candidate_count": len(candidates),
        },
        "candidates": candidates,
        "lead_screening_input": build_lead_screening_input(candidates, data["notes"]),
    }
    markdown = render_markdown(report)
    dump_json(report, args.json_out)
    dump_text(markdown, args.markdown_out)
    sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
