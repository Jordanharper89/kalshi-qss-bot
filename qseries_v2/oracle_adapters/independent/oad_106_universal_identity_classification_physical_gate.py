from __future__ import annotations
from collections import Counter
from dataclasses import dataclass

from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import (
    capture_current_market_cohort,
    snapshot_markets,
)
from qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import (
    decompose_mixed_market,
)
from qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import (
    build_identity_envelopes,
)
from qseries_v2.oracle_adapters.independent.oad_103_guarded_contextual_identity_resolver import (
    resolve_guarded_identity,
)
from qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation import (
    disambiguate_semantic_domain,
)
from qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import (
    assign_source_requirement,
)

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

CANONICAL_SPORTS = {
    "baseball",
    "soccer",
    "tennis",
    "combat",
    "golf",
    "esports",
    "hockey",
    "basketball",
    "football",
    "UNKNOWN",
}

@dataclass(frozen=True, slots=True)
class PhysicalGate:
    snapshot_id: str
    markets: int
    decomposed_legs: int
    direct_resolved: int
    parent_resolved: int
    sibling_advisory_only: int
    conflicting: int
    unresolved: int
    admitted_demands: int
    demand_without_source: int
    sports_none: int
    noncanonical_sport_subdomains: tuple[tuple[str, int], ...]
    financial_price_preserved: int
    source_demand: tuple[tuple[str, int], ...]

def run_physical_gate(limit: int = 1000) -> PhysicalGate:
    snap = capture_current_market_cohort(limit)

    counts = Counter()
    source_demand = Counter()
    noncanonical = Counter()
    total = 0

    for market in snapshot_markets(snap):
        legs = decompose_mixed_market(market)
        envelopes = build_identity_envelopes(market, legs)

        for leg, envelope in zip(legs, envelopes):
            total += 1

            guarded = resolve_guarded_identity(envelope)
            counts[guarded.state] += 1

            leg_domain = str(getattr(leg, "domain", "") or "")
            leg_subdomain = str(getattr(leg, "subdomain", "") or "")
            lexical_domain = leg_domain if leg_domain != "other" else "unknown"

            semantic = disambiguate_semantic_domain(
                getattr(leg, "text", ""),
                lexical_domain,
                guarded.sport,
                leg_subdomain,
            )

            if semantic.semantic_domain == "sports":
                if semantic.semantic_subdomain in ("", "NONE"):
                    counts["SPORTS_NONE"] += 1
                if semantic.semantic_subdomain not in CANONICAL_SPORTS:
                    noncanonical[semantic.semantic_subdomain] += 1

            if (
                semantic.semantic_domain == "financial_markets"
                and semantic.semantic_subdomain == "financial_price"
            ):
                counts["FINANCIAL_PRICE_PRESERVED"] += 1

            admitted = semantic.semantic_domain != "unknown"
            requirement = assign_source_requirement(
                semantic.semantic_domain,
                semantic.semantic_subdomain,
                semantic.state,
            )

            if admitted:
                counts["ADMITTED"] += 1
                if not requirement.authoritative_source_families:
                    counts["NO_SOURCE"] += 1
                else:
                    for family in requirement.authoritative_source_families:
                        source_demand[
                            f"{requirement.domain}:"
                            f"{requirement.subdomain or 'UNKNOWN'}:"
                            f"{family}"
                        ] += 1

    return PhysicalGate(
        snapshot_id=snap.snapshot_id,
        markets=snap.market_count,
        decomposed_legs=total,
        direct_resolved=counts["RESOLVED_DIRECT"],
        parent_resolved=counts["RESOLVED_PARENT"],
        sibling_advisory_only=counts["SIBLING_ADVISORY_ONLY"],
        conflicting=counts["CONFLICTING"],
        unresolved=counts["UNRESOLVED"],
        admitted_demands=counts["ADMITTED"],
        demand_without_source=counts["NO_SOURCE"],
        sports_none=counts["SPORTS_NONE"],
        noncanonical_sport_subdomains=tuple(noncanonical.most_common()),
        financial_price_preserved=counts["FINANCIAL_PRICE_PRESERVED"],
        source_demand=tuple(source_demand.most_common()),
    )
