from __future__ import annotations

from qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import (
    COVERED,
    NOT_COVERED,
    UNMAPPED,
    CoverageGap,
    coverage_state,
)

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def verify_truthful_unmapped_semantics():
    a=coverage_state("other",(),())
    b=coverage_state(
        "sports",
        (object(),),
        ("Official league/team feeds",),
    )
    c=coverage_state(
        "weather",
        (object(),),
        (),
    )
    return a==UNMAPPED and b==NOT_COVERED and c==COVERED
