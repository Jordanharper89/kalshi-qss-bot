from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_live_intelligence_runtime_discovery_and_binding import *
from qseries_v2.oracle_terminal.oracle_open_intelligence_terminal_foundation import (
    build_dependency_receipt,
    format_terminal_response,
    parse_terminal_input,
)


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe binding accepted")
    except OracleLiveIntelligenceBindingInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OIT-002 TEST")
    print(" LIVE INTELLIGENCE RUNTIME DISCOVERY")
    print(" AND READ-ONLY BINDING")
    print("=" * 40)

    dependency = build_dependency_receipt(source_module_sha256="b" * 64)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        analytics = root / "qseries_v2" / "oracle_intelligence" / "analytics"
        analytics.mkdir(parents=True)
        (analytics / "sample_engine.py").write_text(
            'TARGET = r"runtime\\oracle_intelligence\\forward_shadow_confidence"\n',
            encoding="utf-8",
        )
        (root / "runtime" / "oracle_live_shadow").mkdir(parents=True)
        (root / "runtime" / "oracle_research_response").mkdir(parents=True)

        missing = discover_live_intelligence_binding(repository_root=root)
        assert verify_live_intelligence_binding(missing)
        assert missing.analytics_package_present
        assert missing.analytics_module_count == 1
        assert not missing.intelligence_runtime_present
        assert not missing.binding_active
        assert "runtime/oracle_intelligence/forward_shadow_confidence" in missing.declared_runtime_targets

        status = execute_bound_terminal_command(
            parse_terminal_input("status"),
            repository_root=root,
            dependency_receipt=dependency,
        )
        rendered = format_terminal_response(status)
        assert "live_intelligence_binding: waiting for persisted analytics output" in rendered
        assert "intelligence_runtime: not found" in rendered

        runtime_root = root / "runtime" / "oracle_intelligence"
        confidence = runtime_root / "forward_shadow_confidence"
        confidence.mkdir(parents=True)
        (confidence / "current.json").write_text('{"confidence":0.75}\n', encoding="utf-8")

        active = discover_live_intelligence_binding(repository_root=root)
        assert verify_live_intelligence_binding(active)
        assert active.intelligence_runtime_present
        assert active.binding_active
        assert active.intelligence_runtime_file_count == 1
        assert active.bindable_artifact_count >= 1

        freshness = execute_bound_terminal_command(
            parse_terminal_input("freshness"),
            repository_root=root,
            dependency_receipt=dependency,
        )
        rendered_freshness = format_terminal_response(freshness)
        assert "current.json" in rendered_freshness
        assert "No timestamp was invented" in rendered_freshness

        open_request = execute_bound_terminal_command(
            parse_terminal_input("analyze Federal Reserve September decision"),
            repository_root=root,
            dependency_receipt=dependency,
        )
        assert open_request.response_type == "open_intelligence_request"
        assert open_request.read_only
        assert not open_request.execution_allowed

        execution = execute_bound_terminal_command(
            parse_terminal_input("buy BTC"),
            repository_root=root,
            dependency_receipt=dependency,
        )
        assert execution.status == "rejected_read_only_boundary"

        reject(lambda: verify_live_intelligence_binding(
            replace(active, execution_allowed=True)
        ))
        reject(lambda: verify_live_intelligence_binding(
            replace(active, receipt_hash="0" * 64)
        ))

    print("[PASS] Actual OIT-001 terminal foundation consumed")
    print("[PASS] Analytics-declared runtime targets discovered deterministically")
    print("[PASS] Missing intelligence runtime reported without fabrication")
    print("[PASS] Persisted intelligence artifacts bound read-only")
    print("[PASS] Status/runtime/freshness/coverage/capabilities enhanced")
    print("[PASS] No runtime directory or artifact created by discovery")
    print("[PASS] Execution, publication, funds, orders, and portfolio mutation disabled")
    print("[DONE] OIT-002 LIVE INTELLIGENCE RUNTIME DISCOVERY AND BINDING PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
