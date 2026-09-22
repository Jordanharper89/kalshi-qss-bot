
"""OSN-010 multi-league coverage accounting."""
from collections import Counter
from typing import Iterable, Any
from ..coverage.kalshi_sports_demand import detect_league

def build_coverage(records: Iterable[Any], covered_leagues):
    covered = {str(x).upper() for x in covered_leagues}
    total = 0
    with_source = 0
    counts = Counter()
    unresolved = Counter()

    for rec in records:
        total += 1
        league = detect_league(rec)
        counts[league] += 1
        if league in covered:
            with_source += 1
        else:
            unresolved[league] += 1

    return {
        "live_sports_markets_evaluated": total,
        "markets_with_official_source_candidate": with_source,
        "markets_without_official_source_candidate": total - with_source,
        "coverage_percentage": round((with_source / total * 100.0), 2) if total else None,
        "coverage_by_league": dict(sorted(counts.items())),
        "remaining_unresolved_leagues": dict(sorted(unresolved.items())),
        "execution_authority": False,
    }
