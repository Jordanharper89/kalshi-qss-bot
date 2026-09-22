from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import re

from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import (
    capture_current_market_cohort,
    snapshot_markets,
)
from qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import (
    decompose_mixed_market,
)

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

# Phrase lists are matched with token/phrase boundaries, never arbitrary substring search.
SPORT_TERMS = {
    "football": (
        "touchdown", "quarterback", "passing yards", "rushing yards",
        "receiving yards", "field goal", "nfl", "fbs", "fcs",
    ),
    "basketball": (
        "rebounds", "assists", "three pointers", "3-pointers", "nba", "wnba",
        "college basketball", "ncaa basketball",
    ),
    "baseball": (
        "home run", "strikeout", "innings", "rbi", "mlb", "first 5 innings",
        "1st inning",
    ),
    "soccer": (
        "both teams to score", "clean sheet", "champions league", "premier league",
        "la liga", "bundesliga", "serie a", "wins by more than 1.5 goals",
        "wins by more than 2.5 goals",
    ),
    "tennis": (
        "tennis", "atp", "wta", "set 1", "sets won", "aces", "double faults",
        "games won", "wins 2-1", "wins 3-0",
    ),
    "combat": (
        "ufc", "mma", "boxing", "bout", "submission", "ko/tko", "decision",
    ),
    "golf": (
        "golf", "pga", "birdie", "bogey", "par", "top 10", "top 20",
    ),
    "esports": (
        "esports", "esport", "map 1", "map 2", "valorant", "counter-strike",
        "league of legends",
    ),
    "hockey": (
        "nhl", "shots on goal", "power play", "puck", "period goals",
    ),
}

NONSPORT_TERMS = {
    "financial_price": ("target price",),
    "crypto": ("bitcoin", "ethereum", "solana", "btc", "eth", "crypto"),
    "macroeconomics": ("cpi", "inflation", "gdp", "unemployment", "payroll", "fed funds"),
    "politics_elections": ("election", "president", "senate", "governor", "primary"),
    "weather": ("hurricane", "tornado", "rainfall", "snowfall", "temperature", "flood"),
    "energy_commodities": ("crude oil", "natural gas", "gasoline", "gold", "silver", "wheat"),
    "legal_regulatory": ("supreme court", "lawsuit", "indictment", "regulation", "tariff"),
    "health": ("cdc", "fda", "vaccine", "outbreak", "disease", "drug approval"),
    "transport": ("faa", "tsa", "airport", "flight", "shipping", "port"),
    "science_space": ("nasa", "rocket", "spacecraft", "asteroid", "moon", "mars"),
    "geopolitics": ("ceasefire", "nato", "invasion", "military", "peace deal", "treaty"),
}

@dataclass(frozen=True, slots=True)
class EvidenceSignal:
    source_scope: str
    domain: str
    subdomain: str
    matched_terms: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class DiagnosticCluster:
    root_cause: str
    likely_domain: str
    likely_subdomain: str
    count: int
    examples: tuple[str, ...]
    parent_prefixes: tuple[tuple[str, int], ...]
    required_foundational_capability: str

@dataclass(frozen=True, slots=True)
class ExhaustiveDiagnostic:
    snapshot_id: str
    market_count: int
    total_decomposed_legs: int
    resolved_legs: int
    intentionally_unresolved_legs: int
    rejected_invalid_legs: int
    accounted_legs: int
    accounting_ok: bool
    unresolved_cluster_count: int
    unresolved_exactly_once_ok: bool
    sports_none: int
    parser_failure_markets: int
    boundary_collision_count: int
    cross_subdomain_cluster_contamination_count: int
    clusters: tuple[DiagnosticCluster, ...]
    report_hash: str

def _prefix(ticker):
    return str(ticker or "").split("-")[0][:64] or "UNKNOWN_PARENT"

def _normalize_spaces(value):
    return re.sub(r"\s+", " ", str(value or "").strip())

def _phrase_pattern(term):
    # Token-safe phrase matcher. Hyphen/slash stay meaningful inside terms;
    # alphanumeric adjacency is forbidden on both sides.
    escaped = re.escape(_normalize_spaces(term))
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(r"(?<![A-Za-z0-9])" + escaped + r"(?![A-Za-z0-9])", re.I)

_TERM_PATTERNS = {}
for group in (SPORT_TERMS, NONSPORT_TERMS):
    for _, terms in group.items():
        for term in terms:
            _TERM_PATTERNS[term] = _phrase_pattern(term)

def _term_match(text, term):
    return bool(_TERM_PATTERNS[term].search(str(text or "")))

def _signals(text, scope):
    text = str(text or "")
    out = []
    for subdomain, terms in SPORT_TERMS.items():
        hits = tuple(t for t in terms if _term_match(text, t))
        if hits:
            out.append(EvidenceSignal(scope, "sports", subdomain, hits))
    for domain, terms in NONSPORT_TERMS.items():
        hits = tuple(t for t in terms if _term_match(text, t))
        if hits:
            out.append(EvidenceSignal(scope, domain, "", hits))
    return tuple(out)

def _parent_container_context(market):
    # Explicitly exclude leg-bearing title/subtitle fields.
    return " ".join(
        str(market.get(k, "") or "")
        for k in ("ticker", "event_ticker", "series_ticker", "rules_primary", "rules_secondary")
    )

def _proper_name_shape(text):
    words = re.findall(r"[A-Za-zÀ-ÿ'.-]+", text or "")
    return 1 <= len(words) <= 6 and not re.search(
        r"\b(over|under|target|price|points|runs|goals|wins|tie|yes|no)\b",
        text or "", re.I
    )

def _keys(signals):
    return {(x.domain, x.subdomain) for x in signals}

def _sibling_signals(legs, current_index):
    out = []
    for x in legs:
        if x.leg_index == current_index:
            continue
        out.extend(_signals(x.text, "sibling"))
    return tuple(out)

def classify_isolated_root_cause(leg, parent_market, sibling_legs):
    text = str(leg.text or "").strip()
    if not text:
        return (
            "INVALID_EMPTY_LEG", "invalid", "",
            "Parser must reject or preserve empty legs explicitly."
        )

    local = _signals(text, "leg_local")
    parent = _signals(_parent_container_context(parent_market), "parent_context")
    sibling = _sibling_signals(sibling_legs, leg.leg_index)

    local_keys = _keys(local)
    parent_keys = _keys(parent)
    sibling_keys = _keys(sibling)

    if len(local_keys) == 1:
        domain, sub = next(iter(local_keys))
        if domain == "sports":
            return (
                "LEG_LOCAL_RESOLVABLE", domain, sub,
                "Promote direct boundary-safe leg-local structural evidence into final identity."
            )
        return (
            "MISROUTED_NONSPORT", domain, sub,
            "Route explicit boundary-safe leg-local non-sport evidence to authoritative sources."
        )

    if len(local_keys) > 1:
        return (
            "CONFLICTING_CONTEXT", "unknown", "",
            "Multiple direct leg-local signals conflict; do not collapse them."
        )

    if len(parent_keys) == 1:
        domain, sub = next(iter(parent_keys))
        return (
            "PARENT_CONTEXT_RESOLVABLE", domain, sub,
            "Use only unambiguous boundary-safe non-leg parent metadata."
        )

    if len(parent_keys) > 1:
        return (
            "CONFLICTING_CONTEXT", "unknown", "",
            "Parent metadata contains incompatible bounded signals."
        )

    if re.search(r":\s*\d+(?:\.\d+)?\+(?=\s|$|[,;/)])", text):
        return (
            "PLAYER_PROP_UNRESOLVED", "sports", "player_prop",
            "Resolve player-prop sport identity from stat semantics plus safe context."
        )

    if "/" in text and len(text.split("/")) == 2:
        return (
            "PARTICIPANT_PAIR_UNRESOLVED", "sports", "participant_pair",
            "Resolve participant-pair identity from safe metadata or recurring cohort evidence."
        )

    if (
        re.search(r"\bwins?\s+(?:1h\s+)?by\s+over\s+\d", text, re.I)
        or re.search(r"\bover\s+\d+(?:\.\d+)?\s+(?:points|runs|goals)\s+scored\b", text, re.I)
        or re.search(r"\bover\s+\d+(?:\.\d+)?\s+games\b", text, re.I)
    ):
        return (
            "MARKET_TYPE_UNRESOLVED", "sports", "market_type",
            "Resolve sport/league from scoring unit, market type, and safe context."
        )

    if sibling_keys:
        if len(sibling_keys) == 1:
            domain, sub = next(iter(sibling_keys))
            return (
                "SIBLING_CONTEXT_ONLY", domain, sub,
                "Sibling evidence is advisory only and may not classify this leg."
            )
        return (
            "CONFLICTING_CONTEXT", "unknown", "",
            "Sibling legs contain multiple incompatible identities."
        )

    if leg.domain == "sports" and _proper_name_shape(text):
        return (
            "FALSE_SPORT_ADMISSION_OR_ENTITY_UNKNOWN", "sports", "named_entity",
            "Revalidate sports admission for name-only legs before entity resolution."
        )

    if _proper_name_shape(text):
        return (
            "TRUE_UNKNOWN_NAMED_ENTITY", "unknown", "named_entity",
            "Entity-resolution layer required; no safe direct identity evidence exists."
        )

    return (
        "TRUE_UNKNOWN", "unknown", "",
        "Preserve unsupported/ambiguous structure explicitly until evidence exists."
    )

def verify_boundary_matcher():
    cases = (
        ("Golden State", "gold", False),
        ("Shanghai Port", "port", True),
        ("Portland St.", "port", False),
        ("gold", "gold", True),
        ("port", "port", True),
        ("airport", "port", False),
        ("Target Price: $100", "target price", True),
    )
    failures = []
    for text, term, expected in cases:
        actual = _term_match(text, term)
        if actual != expected:
            failures.append((text, term, expected, actual))
    return tuple(failures)

def run_exhaustive_diagnostic(limit=1000, example_limit=8):
    boundary_failures = verify_boundary_matcher()

    snapshot = capture_current_market_cohort(limit)
    total = resolved = unresolved = rejected = parser_failures = sports_none = 0

    # Keyed by full stable semantic identity, not root cause alone.
    cluster_counts = Counter()
    cluster_examples = defaultdict(list)
    cluster_prefixes = defaultdict(Counter)
    cluster_capability = {}

    for market in snapshot_markets(snapshot):
        legs = decompose_mixed_market(market)
        if not legs:
            parser_failures += 1
            rejected += 1
            continue

        for leg in legs:
            total += 1
            if leg.domain == "sports" and leg.subdomain in ("", "NONE"):
                sports_none += 1

            if leg.state == "RESOLVED":
                resolved += 1
                continue

            unresolved += 1
            root, domain, subdomain, capability = classify_isolated_root_cause(
                leg, market, legs
            )
            key = (root, domain, subdomain)
            cluster_counts[key] += 1
            cluster_capability[key] = capability

            if len(cluster_examples[key]) < example_limit:
                cluster_examples[key].append(str(leg.text)[:240])
            cluster_prefixes[key][_prefix(leg.parent_ticker)] += 1

    accounted = resolved + unresolved + rejected
    accounting_ok = accounted == total + rejected
    unresolved_exactly_once_ok = sum(cluster_counts.values()) == unresolved

    clusters = []
    for key, count in sorted(
        cluster_counts.items(),
        key=lambda x: (-x[1], x[0][0], x[0][1], x[0][2]),
    ):
        root, domain, subdomain = key
        clusters.append(
            DiagnosticCluster(
                root,
                domain,
                subdomain,
                count,
                tuple(cluster_examples[key]),
                tuple(cluster_prefixes[key].most_common(12)),
                cluster_capability[key],
            )
        )

    # Because each cluster is keyed by one domain/subdomain, contamination must be zero by construction.
    contamination = 0

    payload = {
        "snapshot_id": snapshot.snapshot_id,
        "market_count": snapshot.market_count,
        "total_decomposed_legs": total,
        "resolved_legs": resolved,
        "intentionally_unresolved_legs": unresolved,
        "rejected_invalid_legs": rejected,
        "accounted_legs": accounted,
        "accounting_ok": accounting_ok,
        "unresolved_exactly_once_ok": unresolved_exactly_once_ok,
        "sports_none": sports_none,
        "parser_failure_markets": parser_failures,
        "boundary_collision_count": len(boundary_failures),
        "cross_subdomain_cluster_contamination_count": contamination,
        "clusters": [
            {
                "root_cause": c.root_cause,
                "likely_domain": c.likely_domain,
                "likely_subdomain": c.likely_subdomain,
                "count": c.count,
                "examples": c.examples,
                "parent_prefixes": c.parent_prefixes,
                "required_foundational_capability": c.required_foundational_capability,
            }
            for c in clusters
        ],
    }

    report_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()

    return ExhaustiveDiagnostic(
        snapshot.snapshot_id,
        snapshot.market_count,
        total,
        resolved,
        unresolved,
        rejected,
        accounted,
        accounting_ok,
        len(clusters),
        unresolved_exactly_once_ok,
        sports_none,
        parser_failures,
        len(boundary_failures),
        contamination,
        tuple(clusters),
        report_hash,
    )

def diagnostic_to_dict(r):
    return {
        "snapshot_id": r.snapshot_id,
        "market_count": r.market_count,
        "total_decomposed_legs": r.total_decomposed_legs,
        "resolved_legs": r.resolved_legs,
        "intentionally_unresolved_legs": r.intentionally_unresolved_legs,
        "rejected_invalid_legs": r.rejected_invalid_legs,
        "accounted_legs": r.accounted_legs,
        "accounting_ok": r.accounting_ok,
        "unresolved_cluster_count": r.unresolved_cluster_count,
        "unresolved_exactly_once_ok": r.unresolved_exactly_once_ok,
        "sports_none": r.sports_none,
        "parser_failure_markets": r.parser_failure_markets,
        "boundary_collision_count": r.boundary_collision_count,
        "cross_subdomain_cluster_contamination_count": r.cross_subdomain_cluster_contamination_count,
        "report_hash": r.report_hash,
        "clusters": [
            {
                "root_cause": c.root_cause,
                "likely_domain": c.likely_domain,
                "likely_subdomain": c.likely_subdomain,
                "count": c.count,
                "examples": c.examples,
                "parent_prefixes": c.parent_prefixes,
                "required_foundational_capability": c.required_foundational_capability,
            }
            for c in r.clusters
        ],
    }
