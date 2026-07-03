# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 100:51
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 4:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 49:9
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: query
#   module_name: query
#   module_kind: service
#   summary: Query enhancement, entity extraction, and cache duration helpers.
#   owner: hmmm
#   public_surface: enhance_query, build_enhanced_query
#   internal_surface: _detect_question_type, _extract_entities, _split_multi_part, _extract_site_filter, _boost_entities_in_query, _is_news_query, _cache_duration_for_query
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   tests: hmmm
#   rollout: hmmm
#   rollback: hmmm
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: query_boundaries
#   summary: Query enhancement, entity extraction, and cache duration helpers.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: query
#   summary: Query enhancement, entity extraction, and cache duration helpers.
#   exposes: enhance_query, build_enhanced_query
# === END CAPABILITIES ===
"""Query enhancement, entity extraction, and cache duration helpers."""

import re
import logging
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Query processing helpers
# ----------------------------------------------------------------------
def _detect_question_type(query: str) -> Optional[str]:
    """Return the leading question word if present (who, what, when, where, why, how)."""
    if not isinstance(query, str):
        return None
    q = query.strip().lower()
    for word in ("who", "what", "when", "where", "why", "how"):
        # Require a whole-word match: a bare prefix mis-flags ordinary queries
        # like "whatsapp pricing" (-> what) or "however ..." (-> how), which
        # then get spurious boost terms OR-appended in enhance_query.
        if q == word or q.startswith(word + " "):
            return word
    return None


def _extract_entities(query: str) -> Dict[str, List[str]]:
    """Lightweight entity extraction: capitalized words and date patterns."""
    if not isinstance(query, str):
        return {"names": [], "dates": []}
    entities: Dict[str, List[str]] = {"names": [], "dates": []}
    qtype = _detect_question_type(query)
    cleaned = query
    if qtype:
        cleaned = re.sub(rf"^{qtype}\b", "", cleaned, flags=re.I).strip()
    for token in re.findall(r"\b[A-Z][a-zA-Z]+\b", cleaned):
        entities["names"].append(token)
    for year in re.findall(r"\b(?:19|20)\d{2}\b", cleaned):
        entities["dates"].append(year)
    month_day_year = re.findall(
        r"\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{1,2},?\s*\d{4}\b",
        cleaned,
        flags=re.I,
    )
    entities["dates"].extend(month_day_year)
    return entities


def _split_multi_part(query: str) -> List[str]:
    """Split a query into sub-queries on common conjunctions."""
    if not isinstance(query, str):
        return []
    parts = re.split(r"\s+and\s+|\s+or\s+|;", query, flags=re.I)
    return [p.strip() for p in parts if p.strip()]


def _extract_site_filter(query: str) -> Tuple[str, Optional[str]]:
    """Detect a 'site:example.com' token. Returns (query_without_token, site_or_None)."""
    if not isinstance(query, str):
        return "", None
    match = re.search(r"\bsite:([^\s]+)", query, flags=re.I)
    if match:
        site = match.group(1)
        new_query = re.sub(r"\bsite:[^\s]+", "", query, flags=re.I).strip()
        return new_query, site
    return query, None


def _boost_entities_in_query(base_query: str, entities: Dict[str, List[str]]) -> str:
    """Append extracted entities to the query using OR to increase relevance."""
    parts = [base_query]
    if entities.get("names"):
        parts.append(" OR ".join(f'"{n}"' for n in entities["names"]))
    if entities.get("dates"):
        parts.append(" OR ".join(f'"{d}"' for d in entities["dates"]))
    return " ".join(parts)


def enhance_query(original_query: str) -> Tuple[str, Optional[str]]:
    """Process the original query: site filter, question type boosts, entity extraction."""
    if not isinstance(original_query, str):
        original_query = ""
    query_without_site, site = _extract_site_filter(original_query)
    sub_queries = _split_multi_part(query_without_site)

    enhanced_subs: List[str] = []
    for sub in sub_queries:
        qtype = _detect_question_type(sub)
        boost_keywords = []
        if qtype == "who":
            boost_keywords.append("person")
        elif qtype == "when":
            boost_keywords.append("date")
        elif qtype == "where":
            boost_keywords.append("location")
        elif qtype == "why":
            boost_keywords.append("reason")
        elif qtype == "how":
            boost_keywords.append("method")
        entities = _extract_entities(sub)
        boosted = _boost_entities_in_query(sub, entities)
        if boost_keywords:
            boosted = f'({boosted}) OR ({" OR ".join(boost_keywords)})'
        enhanced_subs.append(boosted)

    final_query = " AND ".join(f"({s})" for s in enhanced_subs)
    if site:
        final_query = f"{final_query} site:{site}"
    return final_query, site


def build_enhanced_query(query: str, time_filter: str = None) -> str:
    """Build an enhanced search query with optional time filtering."""
    enhanced_query, _ = enhance_query(query)

    if time_filter:
        time_map = {"day": "d", "week": "w", "month": "m", "year": "y"}
        if time_filter in time_map:
            enhanced_query = f"{enhanced_query} after:{time_map[time_filter]}"
            logger.info(f"Added time filter '{time_filter}' to query")

    logger.info(f"Enhanced query: '{query}' -> '{enhanced_query}'")
    return enhanced_query


# ----------------------------------------------------------------------
# Cache duration helpers
# ----------------------------------------------------------------------
def _is_news_query(query: str) -> bool:
    """Lightweight heuristic to decide if a query is news-oriented."""
    news_terms = {"news", "latest", "breaking", "today", "today's", "current", "updates", "happening"}
    if not isinstance(query, str):
        return False
    tokens = set(re.findall(r"\b\w+\b", query.lower()))
    return bool(tokens & news_terms)


def _cache_duration_for_query(query: str) -> timedelta:
    """News queries -> 30 minutes, reference queries -> 24 hours."""
    if _is_news_query(query):
        return timedelta(minutes=30)
    return timedelta(hours=24)
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 100:51
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 4:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 49:9
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
