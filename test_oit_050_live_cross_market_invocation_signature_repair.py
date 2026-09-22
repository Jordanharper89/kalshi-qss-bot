from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_terminal import (
    oracle_cross_market_causal_intelligence_analysis as causal_module,
)
from qseries_v2.oracle_terminal.oracle_cross_market_causal_intelligence_analysis import (
    build_causal_intelligence_report,
    verify_causal_intelligence_report,
)
from qseries_v2.oracle_terminal.oracle_cross_market_intelligence_relationship_analysis import (
    build_cross_market_intelligence_report,
)


def main() -> int:
    print("=" * 56)
    print(" OIT-050 DEFECT CORRECTION TEST")
    print(" LIVE CROSS-MARKET INVOCATION SIGNATURE REPAIR")
    print("=" * 56)

    signature = inspect.signature(
        build_cross_market_intelligence_report
    )
    repository_parameter = signature.parameters["repository_root"]
    query_parameter = signature.parameters["query"]

    assert repository_parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert query_parameter.kind is inspect.Parameter.KEYWORD_ONLY

    production_path = Path(causal_module.__file__).resolve()
    production_source = production_path.read_text(encoding="utf-8")

    assert (
        "build_cross_market_intelligence_report(root, query)"
        not in production_source
    )
    assert (
        "build_cross_market_intelligence_report("
        in production_source
    )
    assert "repository_root=root" in production_source
    assert "query=query" in production_source

    calls: list[dict[str, object]] = []

    def keyword_only_cross_market_builder(
        *,
        repository_root: Path,
        query: str,
        result_limit: int = 10,
    ):
        calls.append(
            {
                "repository_root": repository_root,
                "query": query,
                "result_limit": result_limit,
            }
        )
        return SimpleNamespace(
            relationships=(),
            report_hash="cross-market-report-hash-defect-test",
        )

    original_builder = (
        causal_module.build_cross_market_intelligence_report
    )
    original_verifier = (
        causal_module.verify_cross_market_intelligence_report
    )

    try:
        causal_module.build_cross_market_intelligence_report = (
            keyword_only_cross_market_builder
        )
        causal_module.verify_cross_market_intelligence_report = (
            lambda report: True
        )

        repository_root = Path.cwd().resolve()
        query = (
            "what is the current direction of solana, "
            "what evidence supports it"
        )

        report = build_causal_intelligence_report(
            repository_root,
            query,
        )
    finally:
        causal_module.build_cross_market_intelligence_report = (
            original_builder
        )
        causal_module.verify_cross_market_intelligence_report = (
            original_verifier
        )

    assert len(calls) == 1
    assert calls[0]["repository_root"] == repository_root
    assert calls[0]["query"] == query
    assert calls[0]["result_limit"] == 10

    assert report.query == query
    assert report.cross_market_report_hash == (
        "cross-market-report-hash-defect-test"
    )
    assert report.hypothesis_count == 0
    assert report.causal_state == "no_causal_evidence"
    assert report.read_only
    assert not report.analytics_execution_performed
    assert not report.database_access_performed
    assert not report.publication_allowed
    assert not report.qseries_execution_allowed
    assert verify_causal_intelligence_report(report)

    replay_calls: list[dict[str, object]] = []

    def replay_builder(
        *,
        repository_root: Path,
        query: str,
        result_limit: int = 10,
    ):
        replay_calls.append(
            {
                "repository_root": repository_root,
                "query": query,
                "result_limit": result_limit,
            }
        )
        return SimpleNamespace(
            relationships=(),
            report_hash="cross-market-report-hash-defect-test",
        )

    try:
        causal_module.build_cross_market_intelligence_report = (
            replay_builder
        )
        causal_module.verify_cross_market_intelligence_report = (
            lambda report: True
        )
        replay = build_causal_intelligence_report(
            repository_root,
            query,
        )
    finally:
        causal_module.build_cross_market_intelligence_report = (
            original_builder
        )
        causal_module.verify_cross_market_intelligence_report = (
            original_verifier
        )

    assert replay == report
    assert replay_calls == calls

    print("[PASS] Actual OIT-014 callable signature inspected")
    print("[PASS] repository_root is keyword-only")
    print("[PASS] query is keyword-only")
    print("[PASS] Defective positional invocation removed")
    print("[PASS] Correct repository_root keyword binding verified")
    print("[PASS] Correct query keyword binding verified")
    print("[PASS] Exact Solana terminal question accepted")
    print("[PASS] Causal fallback completed without TypeError")
    print("[PASS] Empty bounded cross-market result handled safely")
    print("[PASS] Causal report deterministic across replay")
    print("[PASS] Read-only boundary preserved")
    print("[PASS] Analytics and database execution remained disabled")
    print("[PASS] Publication and Q Series execution remained disabled")
    print("[DONE] OIT-050 CROSS-MARKET SIGNATURE REPAIR PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
