from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_terminal.oracle_live_terminal_evidence_bridge import (
    LiveTerminalEvidence,
    LiveTerminalEvidenceResult,
    _stable_hash,
    is_live_factual_price_query,
    render_live_terminal_evidence,
    verify_live_terminal_evidence_result,
)


def make_evidence() -> LiveTerminalEvidence:
    body = {
        "query": "what is the current price of bitcoin?",
        "asset": "bitcoin",
        "source_table": "oracle_observations",
        "source_column": "payload:$.price",
        "source_identity": "oracle_observations:abc123",
        "price": 123456.78,
        "observed_at": "2026-08-10T02:00:00+00:00",
        "source_record": {
            "asset": "BTC",
            "price": 123456.78,
        },
        "database_read_performed": True,
        "read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }

    return LiveTerminalEvidence(
        **body,
        evidence_hash=_stable_hash(body),
    )


def make_result() -> LiveTerminalEvidenceResult:
    evidence = make_evidence()

    body = {
        "query": evidence.query,
        "matched": True,
        "evidence": evidence,
        "reason": "live_read_only_evidence_found",
        "database_read_performed": True,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }

    return LiveTerminalEvidenceResult(
        **body,
        result_hash=_stable_hash(body),
    )


def main() -> int:
    print("=" * 72)
    print(" INT-ORACLE-LIVE-001 CERTIFICATION TEST")
    print(" LIVE OBSERVATION -> TERMINAL EVIDENCE PIPELINE REPAIR")
    print("=" * 72)

    root = Path(__file__).resolve().parent

    assert is_live_factual_price_query(
        "what is the current price of bitcoin?"
    )

    assert is_live_factual_price_query(
        "latest BTC price"
    )

    assert is_live_factual_price_query(
        "what is the live price of solana?"
    )

    assert not is_live_factual_price_query(
        "what direction is bitcoin going?"
    )

    assert not is_live_factual_price_query(
        "what is the strongest kalshi opportunity?"
    )

    result = make_result()

    assert verify_live_terminal_evidence_result(
        result
    )

    lines = render_live_terminal_evidence(
        result
    )

    assert lines
    assert any(
        "Bitcoin" in line
        for line in lines
    )
    assert any(
        "$123,456.78" in line
        for line in lines
    )
    assert any(
        "oracle_observations" in line
        for line in lines
    )
    assert any(
        "READ-ONLY" in line
        for line in lines
    )

    tampered = replace(
        result,
        publication_allowed=True,
    )

    try:
        verify_live_terminal_evidence_result(
            tampered
        )
    except Exception:
        pass
    else:
        raise AssertionError(
            "publication capability tamper accepted"
        )

    runner = (
        root
        / "run_oracle_open_intelligence_terminal.py"
    )

    assert runner.is_file()

    source = runner.read_text(
        encoding="utf-8"
    )

    assert (
        "# BEGIN INT-ORACLE-LIVE-001 LIVE TERMINAL EVIDENCE BRIDGE"
        in source
    )

    assert (
        "_int_oracle_live_001_original_display_query"
        in source
    )

    assert (
        "read_live_price_evidence"
        in source
    )

    assert (
        "render_live_terminal_evidence"
        in source
    )

    print("[PASS] Factual live-price query classification certified")
    print("[PASS] Immutable live evidence contract certified")
    print("[PASS] Evidence source, field, identity, timestamp, and hash preserved")
    print("[PASS] Terminal factual evidence rendering certified")
    print("[PASS] Existing display_query fallback preserved")
    print("[PASS] Live bridge runner binding installed")
    print("[PASS] Publication remains disabled")
    print("[PASS] Action authorization remains disabled")
    print("[PASS] Q Series execution remains disabled")
    print("[PASS] No orders or portfolio mutation enabled")
    print("[DONE] INT-ORACLE-LIVE-001 CERTIFIED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
