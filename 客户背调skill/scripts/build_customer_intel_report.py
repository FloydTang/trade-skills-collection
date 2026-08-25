#!/usr/bin/env python3
"""Build a bilingual customer intelligence report from public web evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = next(
    (root for root in SCRIPT_DIR.parents if (root / "workflow_runtime" / "customer_intel_v2.py").is_file()),
    None,
)
if REPO_ROOT is None:
    raise RuntimeError("Could not locate workflow_runtime/customer_intel_v2.py.")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow_runtime.customer_intel_v2 import upgrade_customer_intel_report

USER_AGENT = "trade-customer-intel/0.1"
SEARCH_LIMIT = 5
PHASE2_PLATFORMS = {"linkedin", "instagram", "x", "web"}
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "their",
    "about", "have", "more", "than", "they", "them", "http", "https", "www", "com",
    "company", "official", "首页", "我们", "关于", "联系", "产品", "服务", "客户", "业务",
    "solutions", "service", "services", "products", "contact", "about", "group",
}
PLATFORMS = {
    "linkedin": ("linkedin.com/company", "linkedin.com/in"),
    "facebook": ("facebook.com",),
    "instagram": ("instagram.com",),
    "x": ("x.com", "twitter.com"),
    "youtube": ("youtube.com",),
}
RECENT_SIGNAL_KEYWORDS = {
    "expansion": ("expansion", "expand", "new warehouse", "new facility", "capacity", "扩产", "新仓", "新工厂"),
    "hiring": ("hiring", "recruit", "career", "job opening", "招聘"),
    "funding": ("funding", "investment", "raised", "融资", "投资"),
    "product_launch": ("launch", "new product", "collection", "发布", "新品"),
    "channel_change": ("distributor", "retail", "market entry", "partnership", "渠道", "合作"),
}
MARKET_SIGNAL_KEYWORDS = {
    "compliance": ("regulation", "directive", "compliance", "standard", "certification", "合规", "指令", "认证"),
    "tariff": ("tariff", "duty", "anti-dumping", "customs duty", "关税", "反倾销"),
    "trade_policy": ("trade agreement", "free trade", "import rule", "export rule", "贸易协定", "进口规则"),
}


@dataclass
class SearchResult:
    query: str
    title: str
    url: str
    snippet: str
    source: str


def load_input(path: str | None) -> dict[str, Any]:
    if path:
        return json.loads(Path(path).read_text())
    raw = sys.stdin.read().strip()
    if raw:
        return json.loads(raw)
    return {}


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "company_name": str(data.get("company_name", "")).strip(),
        "person_name": str(data.get("person_name", "")).strip(),
        "email": str(data.get("email", "")).strip(),
        "company_website": str(data.get("company_website", "")).strip(),
        "country_or_market": str(data.get("country_or_market", "")).strip(),
        "product_or_offer": str(data.get("product_or_offer", "")).strip(),
        "industry_lens": str(data.get("industry_lens", "auto")).strip() or "auto",
        "seller_context": data.get("seller_context") if isinstance(data.get("seller_context"), dict) else {},
        "screening_context": data.get("screening_context") if isinstance(data.get("screening_context"), dict) else {},
        "notes": str(data.get("notes", "")).strip(),
    }
    if not any(normalized[key] for key in ("company_name", "person_name", "email")):
        raise SystemExit("At least one of company_name, person_name, or email is required.")
    return normalized


def extract_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.split("@", 1)[1].lower().strip()


def website_to_domain(website: str) -> str:
    if not website:
        return ""
    parsed = urllib.parse.urlparse(website if "://" in website else f"https://{website}")
    return parsed.netloc.lower().removeprefix("www.")


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
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def strip_tags(text: str) -> str:
    cleaned = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    cleaned = re.sub(r"<style.*?</style>", " ", cleaned, flags=re.S | re.I)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def ddg_search(query: str, limit: int = SEARCH_LIMIT) -> list[SearchResult]:
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


def tavily_search(query: str, limit: int = SEARCH_LIMIT) -> list[SearchResult]:
    code, output = run_command(["tvly", "search", query, "--max-results", str(limit), "--json"])
    if code != 0 or not output:
        return []
    payload = json.loads(output)
    results: list[SearchResult] = []
    for item in payload.get("results", [])[:limit]:
        results.append(
            SearchResult(
                query=query,
                title=item.get("title", "").strip(),
                url=item.get("url", "").strip(),
                snippet=item.get("content", "").strip(),
                source="tavily",
            )
        )
    return results


def search(query: str, limit: int = SEARCH_LIMIT) -> list[SearchResult]:
    results = tavily_search(query, limit=limit)
    if results:
        return results
    return ddg_search(query, limit=limit)


def fetch_snapshot(url: str) -> str:
    reader_url = "https://r.jina.ai/http://" + url.removeprefix("https://").removeprefix("http://")
    try:
        return fetch_url(reader_url)
    except Exception:
        return ""


def build_queries(data: dict[str, str], domain: str) -> list[str]:
    company = data["company_name"]
    person = data["person_name"]
    queries: list[str] = []
    if data["company_website"]:
        queries.append(data["company_website"])
    if domain:
        queries.append(f'"{domain}" company')
    if company:
        queries.extend(
            [
                f'"{company}" official website',
                f'site:linkedin.com/company "{company}"',
                f'site:facebook.com "{company}"',
                f'site:instagram.com "{company}"',
                f'site:youtube.com "{company}"',
                f'site:x.com "{company}" OR site:twitter.com "{company}"',
            ]
        )
    if company and person:
        queries.append(f'site:linkedin.com/in "{person}" "{company}"')
    elif person:
        queries.append(f'"{person}" linkedin')
    if data["country_or_market"] and company:
        queries.append(f'"{company}" "{data["country_or_market"]}"')
        queries.append(f'"{company}" "{data["country_or_market"]}" news expansion hiring')
    if data["country_or_market"] and (data.get("product_or_offer") or data.get("notes")):
        product_hint = data.get("product_or_offer") or data.get("notes", "")[:80]
        queries.append(f'"{data["country_or_market"]}" {product_hint} regulation tariff trade agreement')
    return list(dict.fromkeys(query for query in queries if query.strip()))


def dedupe_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for item in results:
        url = item.url.rstrip("/")
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(item)
    return deduped


def choose_website(data: dict[str, str], results: list[SearchResult], domain: str) -> str:
    if data["company_website"]:
        return data["company_website"]
    if domain:
        return f"https://{domain}"
    company_tokens = set(re.findall(r"[a-z0-9]+", data["company_name"].lower()))
    for item in results:
        netloc = website_to_domain(item.url)
        if not netloc or any(host in netloc for hosts in PLATFORMS.values() for host in hosts):
            continue
        title_tokens = set(re.findall(r"[a-z0-9]+", item.title.lower()))
        if company_tokens and company_tokens.intersection(title_tokens):
            return item.url
    return ""


def classify_platform(url: str) -> str:
    lower = url.lower()
    for platform, hosts in PLATFORMS.items():
        if any(host in lower for host in hosts):
            return platform
    return "web"


def summarize_text_blocks(blocks: list[str], limit: int = 2) -> list[str]:
    sentences: list[str] = []
    for block in blocks:
        pieces = re.split(r"(?<=[.!?。！？])\s+", block)
        for piece in pieces:
            piece = piece.strip()
            if len(piece) > 30 and piece not in sentences:
                sentences.append(piece)
            if len(sentences) >= limit:
                return sentences
    return sentences[:limit]


def extract_topic_signals(results: list[SearchResult], snapshots: dict[str, str]) -> list[dict[str, str]]:
    corpus = " ".join([r.title + " " + r.snippet for r in results] + list(snapshots.values()))
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+-]{3,}", corpus.lower())
    counts = Counter(token for token in tokens if token not in STOPWORDS)
    signals: list[dict[str, str]] = []
    for token, count in counts.most_common(6):
        if count < 2:
            continue
        signals.append(
            {
                "title": token,
                "why_it_matters": f"该主题在公开内容中重复出现 {count} 次，可作为业务沟通切入角度。",
                "confidence": "medium" if count < 4 else "high",
            }
        )
    return signals[:5]


def detect_signal_type(text: str, keyword_map: dict[str, tuple[str, ...]]) -> str:
    lower = text.lower()
    for signal_type, keywords in keyword_map.items():
        if any(keyword.lower() in lower for keyword in keywords):
            return signal_type
    return ""


def extract_observed_period(text: str) -> str:
    patterns = [
        r"\b20\d{2}\s*Q[1-4]\b",
        r"\b20\d{2}[-/](?:0?[1-9]|1[0-2])(?:[-/]\d{1,2})?\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+20\d{2}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(0)
    return "unknown"


def signal_confidence(platform: str, text: str) -> str:
    if platform in {"linkedin", "web"} and len(text) > 80:
        return "medium"
    if len(text) > 180:
        return "medium"
    return "low"


def extract_recent_signals(
    results: list[SearchResult],
    snapshots: dict[str, str],
    product_or_offer: str,
) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in results:
        platform = classify_platform(item.url)
        snapshot = snapshots.get(item.url, "")
        text = " ".join(part for part in [item.title, item.snippet, snapshot[:500]] if part)
        signal_type = detect_signal_type(text, RECENT_SIGNAL_KEYWORDS)
        if not signal_type:
            continue
        key = f"{signal_type}:{item.url}"
        if key in seen:
            continue
        seen.add(key)
        title = item.title or f"{signal_type} signal"
        signals.append(
            {
                "signal_type": signal_type,
                "title": title,
                "source_title": item.title,
                "source_url": item.url,
                "source_type": platform,
                "observed_at_or_period": extract_observed_period(text),
                "freshness": "recent_or_needs_date_check" if extract_observed_period(text) != "unknown" else "unknown",
                "confidence": signal_confidence(platform, text),
                "why_it_matters": "这是客户近期动态，可作为开发信切入点，但需要人工确认是否仍然有效。",
                "product_relevance": (
                    f"需要结合 {product_or_offer} 判断是否能承接对方近期变化。"
                    if product_or_offer
                    else "需要结合我方产品判断是否能承接对方近期变化。"
                ),
            }
        )
    return signals[:5]


def extract_market_signals(
    results: list[SearchResult],
    snapshots: dict[str, str],
    country_or_market: str,
    product_or_offer: str,
) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in results:
        text = " ".join(part for part in [item.title, item.snippet, snapshots.get(item.url, "")[:500]] if part)
        signal_type = detect_signal_type(text, MARKET_SIGNAL_KEYWORDS)
        if not signal_type:
            continue
        if country_or_market and country_or_market.lower() not in text.lower() and signal_type != "tariff":
            continue
        key = f"{signal_type}:{item.url}"
        if key in seen:
            continue
        seen.add(key)
        signals.append(
            {
                "signal_type": signal_type,
                "title": item.title or f"{signal_type} market signal",
                "source_title": item.title,
                "source_url": item.url,
                "source_type": classify_platform(item.url),
                "observed_at_or_period": extract_observed_period(text),
                "freshness": "recent_or_needs_date_check" if extract_observed_period(text) != "unknown" else "unknown",
                "confidence": signal_confidence(classify_platform(item.url), text),
                "why_it_matters": "这是目标市场或行业环境信号，可能影响采购关注点、合规要求或供应商选择。",
                "product_relevance": (
                    f"需要判断该变化是否影响 {product_or_offer} 的采购、认证、报价或交付。"
                    if product_or_offer
                    else "需要判断该变化是否影响客户采购、认证、报价或交付。"
                ),
            }
        )
    return signals[:5]


def collect_platform_evidence(results: list[SearchResult], snapshots: dict[str, str]) -> dict[str, list[dict[str, str]]]:
    platform_map: dict[str, list[dict[str, str]]] = {}
    for item in results:
        platform = classify_platform(item.url)
        if platform not in PHASE2_PLATFORMS:
            continue
        summary = item.snippet.strip()
        snapshot = snapshots.get(item.url, "").strip()
        evidence = {
            "title": item.title,
            "url": item.url,
            "snippet": summary[:240],
            "snapshot": snapshot[:500],
            "platform": platform,
        }
        platform_map.setdefault(platform, []).append(evidence)
    return platform_map


def extract_communication_style(platform_map: dict[str, list[dict[str, str]]]) -> list[str]:
    styles: list[str] = []
    if platform_map.get("linkedin"):
        styles.append("更偏商务表达，适合从行业、职位职责或增长目标切入。")
    if platform_map.get("instagram"):
        styles.append("公开内容带有视觉/展示属性，适合引用产品展示、现场图片或成果感表达。")
    if platform_map.get("x"):
        styles.append("若 X 上有内容，说明其更可能接受简短、直接、观点先行的沟通方式。")
    if platform_map.get("web"):
        styles.append("官网或网页信息较关键，建议先引用其公开业务描述建立可信度。")
    return styles[:3]


def build_outreach_persona_card(
    rating: str,
    signals: list[dict[str, str]],
    platform_map: dict[str, list[dict[str, str]]],
    company_summary: str,
) -> tuple[str, dict[str, Any] | None]:
    if rating == "High":
        return "skipped", None

    themes: list[dict[str, Any]] = []
    recommended_angles: list[str] = []
    available_platforms = [platform for platform, items in platform_map.items() if items]
    evidence_budget = sum(len(items) for items in platform_map.values())

    if company_summary:
        themes.append(
            {
                "title": "公开业务方向",
                "evidence": [company_summary[:160]],
                "confidence": "medium" if evidence_budget < 4 else "high",
            }
        )
        recommended_angles.append("优先围绕其已公开表达的业务方向切入，降低陌生开发感。")

    for signal in signals[:4]:
        themes.append(
            {
                "title": signal["title"],
                "evidence": [signal["why_it_matters"]],
                "confidence": signal["confidence"],
            }
        )
        recommended_angles.append(f"可围绕“{signal['title']}”切入，但要明确这是基于公开内容的保守判断。")

    if platform_map.get("instagram"):
        recommended_angles.append("若 Instagram 有持续内容，可从产品展示、应用场景或品牌感知切入。")
    if platform_map.get("linkedin"):
        recommended_angles.append("若 LinkedIn 内容较强，可从岗位职责、行业趋势或合作价值切入。")

    persona = {
        "themes": themes[:5],
        "communication_style": extract_communication_style(platform_map),
        "recommended_angles": list(dict.fromkeys(recommended_angles))[:4],
    }

    if not persona["themes"]:
        return "limited_evidence", {
            "themes": [],
            "communication_style": extract_communication_style(platform_map),
            "recommended_angles": ["公开内容不足，建议先以公司基础信息核验和需求确认作为首轮沟通目标。"],
        }
    if evidence_budget < 3:
        return "limited_evidence", persona
    return "generated", persona


def build_personalized_outreach_pack(
    phase_2_status: str,
    persona: dict[str, Any] | None,
    platform_map: dict[str, list[dict[str, str]]],
    company_name: str,
    person_name: str,
) -> dict[str, Any] | None:
    if phase_2_status == "skipped" or not persona:
        return None

    opening_angles: list[dict[str, Any]] = []
    for theme in persona["themes"][:4]:
        evidence_platforms = [
            item["platform"]
            for platform, items in platform_map.items()
            for item in items
            if platform in PHASE2_PLATFORMS and item["platform"] == platform
        ]
        opening_angles.append(
            {
                "cn": f"从“{theme['title']}”这个公开主题切入，先引用对方已表达或展示过的方向，再承接你的产品/服务价值。",
                "en": f"I noticed your public content touches on {theme['title']}. That seems closely aligned with the kind of operational or growth priorities we support for similar teams.",
                "evidence": (theme.get("evidence") or [])[:2] + evidence_platforms[:1],
            }
        )

    first_message_en = []
    follow_up_en = []
    business_anchor = persona["themes"][0]["title"] if persona["themes"] else "your current business priorities"
    recipient = person_name or "your team"
    company_ref = company_name or "your company"
    first_message_en.append(
        textwrap.dedent(
            f"""
            Hi {recipient},

            I came across {company_ref} while reviewing your public presence and noticed a visible focus on {business_anchor}. We work with teams that need a more targeted way to support that kind of priority, and I thought it may be worth exploring whether there is a fit.
            """
        ).strip()
    )
    first_message_en.append(
        textwrap.dedent(
            f"""
            Hello {recipient},

            I reviewed some of {company_ref}'s public updates and saw signals around {business_anchor}. If that is still a current focus for your team, I can share a few concrete ideas that may be relevant to your market and buying context.
            """
        ).strip()
    )
    follow_up_en.append(
        textwrap.dedent(
            f"""
            Just following up in case {business_anchor} is still a priority on your side. If useful, I can send a short, tailored suggestion based on what {company_ref} appears to be focusing on publicly.
            """
        ).strip()
    )
    follow_up_en.append(
        textwrap.dedent(
            """
            I did not want to overload you with a generic pitch. If timing is right, I can keep it brief and only share ideas that match the themes your team is already discussing publicly.
            """
        ).strip()
    )

    avoid_points = [
        "不要把弱推断说成确定事实，尤其是人物兴趣和私人偏好。",
        "不要引用看起来像隐私或非公开获取的数据点。",
        "不要一上来就直接报价，先围绕公开主题建立相关性。",
    ]
    if phase_2_status == "limited_evidence":
        avoid_points.append("当前证据有限，建议先确认职位、公司关系或当前需求，再使用个性化话术。")

    return {
        "opening_angles": opening_angles[:4],
        "first_message_en": first_message_en[:2],
        "follow_up_en": follow_up_en[:2],
        "avoid_points": avoid_points,
    }


def build_sales_angles(
    signals: list[dict[str, str]],
    company_summary: str,
    recent_signals: list[dict[str, str]] | None = None,
    market_signals: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    angles: list[dict[str, str]] = []
    for signal in (recent_signals or [])[:2]:
        angles.append(
            {
                "cn": f"优先围绕近期信号“{signal['title']}”切入，先引用来源和时间，再承接我方产品/服务能解决的问题。",
                "en": f"Open with the recent signal '{signal['title']}' and connect it cautiously to a specific operational or sourcing need.",
                "why": signal["why_it_matters"],
                "avoid": "不要把近期信号写成确定需求，发送前确认来源、时间和语境。",
            }
        )
    for signal in (market_signals or [])[:1]:
        angles.append(
            {
                "cn": f"可从目标市场变化“{signal['title']}”切入，讨论合规、关税、交付或供应稳定性。",
                "en": f"Use the market signal '{signal['title']}' as context, then ask whether it affects their sourcing or compliance priorities.",
                "why": signal["why_it_matters"],
                "avoid": "不要给法律、关税或合规结论，只能作为业务沟通背景。",
            }
        )
    if company_summary:
        angles.append(
            {
                "cn": f"先围绕对方公开业务描述切入，引用其官网/社媒提到的方向，例如：{company_summary[:80]}。",
                "en": "Open with the business direction already visible on their website or social footprint, then connect your offer to that stated priority.",
                "why": "先用对方公开表达过的主题建立相关性，降低陌生开发感。",
                "avoid": "避免一开始就泛泛介绍产品，先证明你做过功课。",
            }
        )
    for signal in signals[:2]:
        angles.append(
            {
                "cn": f"可围绕“{signal['title']}”设计第一轮沟通，说明你们如何支持相关需求或项目节奏。",
                "en": f"Use '{signal['title']}' as an opening angle and show how your offer supports that theme or buying priority.",
                "why": signal["why_it_matters"],
                "avoid": "若该信号仅来自单一弱来源，请不要表述得过于确定。",
            }
        )
    return angles[:3]


def risk_rating(data: dict[str, str], website: str, results: list[SearchResult], snapshots: dict[str, str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    score = 0
    if not website:
        score += 2
        reasons.append("未能确认官网，企业身份识别较弱。")
    if len(results) < 4:
        score += 1
        reasons.append("公开检索结果较少，信息完整度有限。")
    if data["email"] and extract_domain(data["email"]) and website:
        email_domain = extract_domain(data["email"])
        site_domain = website_to_domain(website)
        if site_domain and email_domain != site_domain:
            score += 2
            reasons.append("邮箱域名与识别出的官网域名不一致。")
    if website and website in snapshots and len(snapshots[website]) < 80:
        score += 1
        reasons.append("官网内容抓取较少，可能是站点信息有限或访问受限。")

    if score >= 4:
        return "High", reasons or ["存在较强身份或可信度疑点。"]
    if score >= 2:
        return "Medium", reasons or ["公开信息不完整，需要人工复核。"]
    return "Low", reasons or ["公开身份线索基本一致，暂未发现明显红旗。"]


def entity_confidence(data: dict[str, str], website: str, results: list[SearchResult]) -> str:
    if data["company_website"] or extract_domain(data["email"]):
        return "high"
    if website and len(results) >= 4:
        return "medium"
    return "low"


SIEGER_NO_COVERAGE = "公开来源未覆盖"


def build_report(data: dict[str, str], results: list[SearchResult], snapshots: dict[str, str]) -> dict[str, Any]:
    domain = extract_domain(data["email"]) or website_to_domain(data["company_website"])
    website = choose_website(data, results, domain)
    website_summary = " ".join(summarize_text_blocks([snapshots.get(website, "")])) if website else ""
    company_summary = website_summary or (results[0].snippet if results else "")
    footprints: list[dict[str, str]] = []
    evidence: list[dict[str, str]] = []
    ambiguity_notes: list[str] = []

    for item in results:
        platform = classify_platform(item.url)
        if platform != "web":
            footprints.append(
                {
                    "platform": platform,
                    "url": item.url,
                    "confidence": "high" if data["company_name"] and data["company_name"].lower() in item.title.lower() else "medium",
                    "activity": item.snippet[:160] or item.title,
                    "notes": item.title,
                }
            )
        evidence.append(
            {
                "title": item.title or item.query,
                "url": item.url,
                "note": item.snippet[:180],
                "source_type": platform,
            }
        )
    if data["person_name"] and not any("linkedin.com/in" in item.url for item in results):
        ambiguity_notes.append("未找到与联系人高度匹配的个人资料，人物画像仅作弱推断。")
    if not website:
        ambiguity_notes.append("未能稳定识别官网，企业主体可能需要人工二次确认。")

    signals = extract_topic_signals(results, snapshots)
    recent_signals = extract_recent_signals(results, snapshots, data.get("product_or_offer", ""))
    market_signals = extract_market_signals(
        results,
        snapshots,
        data["country_or_market"],
        data.get("product_or_offer", ""),
    )
    rating, risk_reasons = risk_rating(data, website, results, snapshots)
    entity_level = entity_confidence(data, website, results)
    sales_angles = build_sales_angles(signals, company_summary, recent_signals, market_signals)
    platform_map = collect_platform_evidence(results, snapshots)
    phase_2_status, outreach_persona_card = build_outreach_persona_card(
        rating,
        signals,
        platform_map,
        company_summary,
    )
    personalized_outreach_pack = build_personalized_outreach_pack(
        phase_2_status,
        outreach_persona_card,
        platform_map,
        data["company_name"],
        data["person_name"],
    )
    missing_fields = [key for key in ("company_name", "person_name", "email") if not data[key]]
    generated_at = datetime.now(timezone.utc).isoformat()
    v2_sections = upgrade_customer_intel_report(
        lead=data,
        raw_evidence=evidence,
        company_summary=company_summary,
        official_website=website,
        recent_signals=recent_signals,
        market_signals=market_signals,
        sales_angles=sales_angles,
        risk_rating=rating,
        risk_reasons=risk_reasons,
        entity_confidence=entity_level,
        ambiguity_notes=ambiguity_notes,
        generated_at=generated_at,
    )
    intel_decision = v2_sections["intel_decision"]
    sales_angles = v2_sections["sales_angles"]
    unconfirmed_fact_list = list(ambiguity_notes)
    if intel_decision.get("evidence_sufficiency") != "sufficient":
        unconfirmed_fact_list.append("公开证据仍不足以支持强个性化判断，进入开发信前需人工确认。")
    if rating == "High":
        unconfirmed_fact_list.append("当前风险评级为 High，不建议直接进入开发信。")

    summary_cn_parts = [
        f"当前线索更像是{data['company_name'] or '一个待确认的公司主体'}",
        f"公开网络足迹主要集中在{', '.join(sorted({f['platform'] for f in footprints})) or '官网/通用网页'}。",
        (
            "建议优先围绕其公开业务方向和近期内容主题切入，再决定是否进入深度报价或样品沟通。"
            if intel_decision["recommended_next_action"] == "ready_for_email_draft"
            else "当前应先做人工复核或补证据，再决定是否进入开发信。"
        ),
    ]
    summary_en_parts = [
        f"The lead most likely maps to {data['company_name'] or 'a still-unconfirmed company entity'}.",
        f"The strongest public footprint appears on {', '.join(sorted({f['platform'] for f in footprints})) or 'the website and general web results'}.",
        (
            "Lead with a relevant business angle grounded in public evidence before moving to pricing or sample discussions."
            if intel_decision["recommended_next_action"] == "ready_for_email_draft"
            else "Pause before outreach and manually verify the entity match and evidence gaps."
        ),
    ]

    return {
        "summary_cn": " ".join(summary_cn_parts),
        "summary_en": " ".join(summary_en_parts),
        "missing_input_fields": missing_fields,
        "identity_snapshot": {
            "company_name": data["company_name"] or None,
            "person_name": data["person_name"] or None,
            "email": data["email"] or None,
            "email_domain": domain or None,
            "website": website or None,
            "country_or_market": data["country_or_market"] or None,
            "entity_confidence": entity_level,
            "ambiguity_notes": ambiguity_notes,
        },
        "company_profile": {
            "apparent_business": company_summary or "证据不足，暂未能稳定归纳主营方向。",
            "website_quality": "basic" if website else "missing",
            "social_presence_overview": f"识别到 {len(footprints)} 个主要社媒/公开平台线索。",
            "team_or_scale_clues": "可从官网文案、LinkedIn 页面和视频频道进一步补充。",
        },
        "digital_footprint": footprints,
        "interest_signals": signals,
        "recent_signals": recent_signals,
        "market_signals": market_signals,
        "sales_angles": sales_angles,
        "risk_rating": rating,
        "risk_reasons": risk_reasons,
        "intel_decision": intel_decision,
        "unconfirmed_fact_list": unconfirmed_fact_list,
        "phase_2_status": phase_2_status,
        "outreach_persona_card": outreach_persona_card,
        "personalized_outreach_pack": personalized_outreach_pack,
        "evidence": evidence[:15],
        "notes": data["notes"] or None,
        "generated_at": generated_at,
        **v2_sections,
    }


def render_sieger_sections(report: dict[str, Any]) -> list[str]:
    verdict = report.get("verdict_card") or {}
    business = report.get("company_business_breakdown") or {}
    tech = report.get("tech_capability_procurement_concerns") or {}
    scale = report.get("scale_financial_signals") or {}
    sales_model = report.get("sales_model_procurement_logic") or {}
    competition = report.get("competition_map") or {}
    growth = report.get("growth_opportunities") or []
    score_display = verdict.get("score") if verdict.get("score") is not None else "未评分"
    lines = [
        "",
        "## Verdict Card（结论先看）",
        "",
        f"- 综合开发价值：{score_display}/10（{verdict.get('score_basis', SIEGER_NO_COVERAGE)}）",
        f"- 客户分级：{verdict.get('customer_grade', '未覆盖')}；{verdict.get('grade_reason', SIEGER_NO_COVERAGE)}",
        f"- Intel Decision：{verdict.get('intel_decision', 'needs_manual_review')}",
        f"- 一句话总评：{verdict.get('one_line_verdict', SIEGER_NO_COVERAGE)}",
    ]
    for dimension in verdict.get("dimensions") or []:
        lines.append(f"- {dimension.get('name', '维度')}：{dimension.get('display', dimension.get('rating', SIEGER_NO_COVERAGE))}；依据：{dimension.get('basis', SIEGER_NO_COVERAGE)}")
    for item in verdict.get("review_focus") or []:
        lines.append(f"- 人工复核：{item}")

    lines.extend(["", "## Company Profile & Business Breakdown（业务拆解）", ""])
    for business_line in business.get("business_lines") or []:
        lines.append(f"- 业务线：{business_line.get('name', SIEGER_NO_COVERAGE)}")
        lines.append(f"  代表产品/描述：{'；'.join(business_line.get('representative_products') or [SIEGER_NO_COVERAGE])}")
        lines.append(f"  客户类型：{business_line.get('customer_types', SIEGER_NO_COVERAGE)}")
        if business_line.get("evidence_refs"):
            lines.append(f"  来源：{'；'.join(business_line['evidence_refs'])}")
    facts = business.get("entity_facts") or {}
    for label, key in (("注册与实体", "registration_and_entity"), ("地址差异", "address_notes"), ("厂房/研发设施", "facilities"), ("管理层背景", "management_background")):
        lines.append(f"- {label}：{facts.get(key, SIEGER_NO_COVERAGE)}")
    judgment = business.get("business_model_judgment") or {}
    lines.append(f"- 商业模式判断：{judgment.get('value', SIEGER_NO_COVERAGE)}（{judgment.get('basis', SIEGER_NO_COVERAGE)}）")

    lines.extend(["", "## Tech Capability & Procurement Concerns（技术能力与采购关注点）", ""])
    lines.append(f"- 技术栈：{tech.get('technical_stack', SIEGER_NO_COVERAGE)}；依据：{tech.get('technical_stack_basis', SIEGER_NO_COVERAGE)}")
    for concern in tech.get("procurement_concerns") or []:
        lines.append(f"- 采购关注点：{concern.get('item', SIEGER_NO_COVERAGE)} — {concern.get('assessment', SIEGER_NO_COVERAGE)}（优先级：{concern.get('priority', '待确认')}）")
    lines.append(f"- 对我方最关键：{tech.get('most_important_for_us', SIEGER_NO_COVERAGE)}")

    lines.extend(["", "## Scale & Financial Signals（规模与财务信号）", ""])
    lines.append(f"- 营收：{scale.get('revenue', '公开免费来源未覆盖')}")
    lines.append(f"- 员工数：{scale.get('employee_count', '公开免费来源未覆盖')}")
    lines.append(f"- 经营趋势：{scale.get('operating_trend', SIEGER_NO_COVERAGE)}")
    lines.append(f"- 采购行为解读：{scale.get('procurement_behavior_interpretation', SIEGER_NO_COVERAGE)}")
    lines.append(f"- 人工补查入口：{scale.get('manual_check_entry', SIEGER_NO_COVERAGE)}")

    lines.extend(["", "## Sales Model & Procurement Logic（销售模式与采购逻辑）", ""])
    lines.append(f"- 销售模式：{sales_model.get('sales_model', SIEGER_NO_COVERAGE)}")
    lines.append(f"- 典型销售周期：{sales_model.get('sales_cycle', SIEGER_NO_COVERAGE)}")
    lines.append(f"- 供应商进入点：{sales_model.get('supplier_entry_point', SIEGER_NO_COVERAGE)}")
    lines.append(f"- 依据：{sales_model.get('basis', SIEGER_NO_COVERAGE)}")

    lines.extend(["", "## Competition Map（竞争对手图谱）", ""])
    competitors = competition.get("potential_competitors") or []
    lines.append(f"- 潜在竞争集合：{'；'.join(str(item) for item in competitors) if competitors else SIEGER_NO_COVERAGE}")
    lines.append(f"- 注记：{competition.get('note', '公开来源未覆盖；不做一一对应宣称。')}")

    lines.extend(["", "## Growth Opportunities（增长机会）", ""])
    if growth:
        for opportunity in growth:
            lines.append(f"- {opportunity.get('opportunity', SIEGER_NO_COVERAGE)}")
            lines.append(f"  逻辑：{opportunity.get('logic', SIEGER_NO_COVERAGE)}；状态：{opportunity.get('status', '需人工验证')}")
    else:
        lines.append(f"- {SIEGER_NO_COVERAGE}")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    identity = report["identity_snapshot"]
    company = report["company_profile"]
    lines = [
        "# Customer Intel Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Missing input fields: {', '.join(report['missing_input_fields']) or 'none'}",
        f"- Phase 2 status: {report.get('phase_2_status', 'skipped')}",
        f"- Evidence sufficiency: {(report.get('intel_decision') or {}).get('evidence_sufficiency', 'unknown')}",
        f"- Recommended next action: {(report.get('intel_decision') or {}).get('recommended_next_action', 'unknown')}",
    ]
    if len(report["evidence"]) < 4:
        lines.append("- Confidence note: 证据较少，建议人工补充验证。")
    lines.extend(
        [
            "",
            "## Executive Summary",
            "",
            f"中文总结：{report['summary_cn']}",
            "",
            f"English summary: {report['summary_en']}",
            "",
            "## Identity Snapshot",
            "",
            f"- Company name: {identity['company_name'] or 'N/A'}",
            f"- Contact name: {identity['person_name'] or 'N/A'}",
            f"- Email: {identity['email'] or 'N/A'}",
            f"- Email domain: {identity['email_domain'] or 'N/A'}",
            f"- Website: {identity['website'] or 'N/A'}",
            f"- Country / market: {identity['country_or_market'] or 'N/A'}",
            f"- Entity confidence: {identity['entity_confidence']}",
        ]
    )
    for note in identity["ambiguity_notes"]:
        lines.append(f"- Ambiguity note: {note}")

    decision_brief = report.get("decision_brief") or {}
    lines.extend(["", "## Decision Brief", ""])
    lines.append(f"- Decision: {decision_brief.get('decision', 'hold_for_manual_review')}")
    lines.append(f"- Next action: {decision_brief.get('next_action', '补证据后再判断。')}")
    for gate_name, gate in (decision_brief.get("decision_gates") or {}).items():
        lines.append(f"- Gate {gate_name}: {gate.get('status', 'unknown')} - {gate.get('reason', '')}")

    lines.extend(render_sieger_sections(report))

    lines.extend(
        [
            "",
            "## Intel Decision",
            "",
            f"- Evidence sufficiency: {report['intel_decision']['evidence_sufficiency']}",
            f"- Recommended next action: {report['intel_decision']['recommended_next_action']}",
            f"- Manual review required: {report['intel_decision']['manual_review_required']}",
            "",
            "## Company Profile（兼容字段视图）",
            "",
            f"- Apparent business: {company['apparent_business']}",
            f"- Website quality: {company['website_quality']}",
            f"- Social presence overview: {company['social_presence_overview']}",
            f"- Team / scale clues: {company['team_or_scale_clues']}",
            "",
            "## Digital Footprint",
            "",
        ]
    )
    if report["digital_footprint"]:
        for item in report["digital_footprint"]:
            lines.extend(
                [
                    f"- {item['platform']}: {item['url']}",
                    f"  Confidence: {item['confidence']}; Activity: {item['activity']}; Notes: {item['notes']}",
                ]
            )
    else:
        lines.append("- No strong social profiles identified in this pass.")

    lines.extend(["", "## Interest & Topic Signals", ""])
    if report["interest_signals"]:
        for signal in report["interest_signals"]:
            lines.append(
                f"- {signal['title']}: {signal['why_it_matters']} (confidence: {signal['confidence']})"
            )
    else:
        lines.append("- No durable topic signal identified yet.")

    lines.extend(["", "## Recent Customer Signals", ""])
    if report.get("recent_signals"):
        for signal in report["recent_signals"]:
            lines.append(
                f"- {signal['title']} ({signal['signal_type']}, freshness: {signal['freshness']}, confidence: {signal['confidence']})"
            )
            lines.append(f"  Source: {signal['source_title']} - {signal['source_url']}")
            lines.append(f"  Why it matters: {signal['why_it_matters']}")
            lines.append(f"  Product relevance: {signal['product_relevance']}")
    else:
        lines.append("- No recent customer signal confirmed in this pass.")

    lines.extend(["", "## Market & Compliance Signals", ""])
    if report.get("market_signals"):
        for signal in report["market_signals"]:
            lines.append(
                f"- {signal['title']} ({signal['signal_type']}, freshness: {signal['freshness']}, confidence: {signal['confidence']})"
            )
            lines.append(f"  Source: {signal['source_title']} - {signal['source_url']}")
            lines.append(f"  Why it matters: {signal['why_it_matters']}")
            lines.append(f"  Product relevance: {signal['product_relevance']}")
    else:
        lines.append("- No market or compliance signal confirmed in this pass.")

    lines.extend(["", "## Sales Angles（切入策略）", ""])
    for angle in report["sales_angles"]:
        lines.extend(
            [
                f"- 中文建议：{angle.get('cn', SIEGER_NO_COVERAGE)}",
                f"  English angle: {angle.get('en', SIEGER_NO_COVERAGE)}",
                f"  Why: {angle.get('why', SIEGER_NO_COVERAGE)}",
                f"  Why this angle fits: {angle.get('why_this_angle_fits', angle.get('why', SIEGER_NO_COVERAGE))}",
                f"  Buyer/component clue: {angle.get('buyer_or_component_clue', SIEGER_NO_COVERAGE)}",
                f"  Replacement point: {angle.get('replacement_point', SIEGER_NO_COVERAGE)}",
                f"  Authorized materials: {'; '.join(angle.get('authorized_materials') or []) or SIEGER_NO_COVERAGE}",
                f"  Evidence refs: {'; '.join(angle.get('evidence_refs') or []) or SIEGER_NO_COVERAGE}",
                f"  Avoid: {angle.get('avoid', SIEGER_NO_COVERAGE)}",
            ]
        )

    lines.extend(["", "## Unconfirmed Facts", ""])
    for item in report.get("unconfirmed_fact_list") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Outreach Persona Card", ""])
    persona = report.get("outreach_persona_card")
    if persona:
        if persona.get("themes"):
            for theme in persona["themes"]:
                lines.append(
                    f"- Theme: {theme['title']} (confidence: {theme['confidence']})"
                )
                for evidence in theme.get("evidence", []):
                    lines.append(f"  Evidence: {evidence}")
        else:
            lines.append("- No strong persona theme confirmed from public content.")
        for style in persona.get("communication_style", []):
            lines.append(f"- Communication style: {style}")
        for angle in persona.get("recommended_angles", []):
            lines.append(f"- Recommended angle: {angle}")
    else:
        lines.append("- Phase 2 persona analysis skipped for this lead.")

    lines.extend(["", "## Personalized Outreach Pack", ""])
    pack = report.get("personalized_outreach_pack")
    if pack:
        for angle in pack.get("opening_angles", []):
            lines.append(f"- 中文切入：{angle['cn']}")
            lines.append(f"  English angle: {angle['en']}")
            for evidence in angle.get("evidence", []):
                lines.append(f"  Evidence: {evidence}")
        for message in pack.get("first_message_en", []):
            lines.append(f"- First message EN: {message}")
        for message in pack.get("follow_up_en", []):
            lines.append(f"- Follow-up EN: {message}")
        for point in pack.get("avoid_points", []):
            lines.append(f"- Avoid: {point}")
    else:
        lines.append("- Personalized outreach content not generated for this lead.")

    lines.extend(
        [
            "",
            "## Risk Rating",
            "",
            f"- Rating: {report['risk_rating']}",
        ]
    )
    for reason in report["risk_reasons"]:
        lines.append(f"- Reason: {reason}")

    image_summary = report.get("image_summary") or {}
    image_score = image_summary.get("score") if image_summary.get("score") is not None else "未评分"
    lines.extend(
        [
            "",
            "## 画像总结（收尾）",
            "",
            f"- 顾问式总结：{image_summary.get('summary_cn', SIEGER_NO_COVERAGE)}",
            f"- 综合开发价值：{image_score}/10；客户分级：{image_summary.get('customer_grade', '未覆盖')}",
            f"- 最大机会：{image_summary.get('maximum_opportunity', SIEGER_NO_COVERAGE)}",
            f"- 最大风险：{image_summary.get('maximum_risk', SIEGER_NO_COVERAGE)}",
            f"- 策略：{image_summary.get('strategy', SIEGER_NO_COVERAGE)}",
        ]
    )

    lines.extend(["", "## Claim Ledger", ""])
    for item in report.get("claim_ledger") or []:
        lines.append(
            f"- {item['claim_id']} [{item['statement_type']}/{item['confidence']}] "
            f"{item['statement']} -> {', '.join(item['evidence_ids']) or 'no evidence'}"
        )
    lines.extend(["", "## Evidence Ledger", ""])
    for item in report.get("evidence_ledger") or []:
        lines.append(
            f"- {item['evidence_id']} [{item['source_quality']}/{item['confidence']}] "
            f"{item['title']}: {item['url'] or '(no url)'}"
        )
    lines.extend(["", "## Evidence（兼容字段视图）", ""])
    for item in report["evidence"]:
        lines.append(f"- {item['title']}: {item['url']} ({item['source_type']})")
        if item["note"]:
            lines.append(f"  Note: {item['note']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a bilingual public-web customer intelligence report."
    )
    parser.add_argument("--input-json", help="Path to a JSON file matching CustomerIntelInput.")
    parser.add_argument("--json-out", help="Optional path to save the JSON report.")
    parser.add_argument("--markdown-out", help="Optional path to save the Markdown report.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the search plan.")
    args = parser.parse_args()

    data = normalize_input(load_input(args.input_json))
    domain = extract_domain(data["email"]) or website_to_domain(data["company_website"])
    queries = build_queries(data, domain)

    if args.dry_run:
        print(json.dumps({"input": data, "queries": queries}, ensure_ascii=False, indent=2))
        return

    gathered: list[SearchResult] = []
    for query in queries:
        if query.startswith("http://") or query.startswith("https://"):
            gathered.append(SearchResult(query=query, title=query, url=query, snippet="", source="direct"))
            continue
        gathered.extend(search(query, limit=SEARCH_LIMIT))

    results = dedupe_results(gathered)
    snapshots: dict[str, str] = {}
    for item in results[:8]:
        snapshots[item.url] = fetch_snapshot(item.url)

    report = build_report(data, results, snapshots)
    markdown = render_markdown(report)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    if args.markdown_out:
        Path(args.markdown_out).write_text(markdown)
    if not args.json_out and not args.markdown_out:
        print(markdown)


if __name__ == "__main__":
    main()
