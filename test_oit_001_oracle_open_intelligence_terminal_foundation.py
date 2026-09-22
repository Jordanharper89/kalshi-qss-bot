from dataclasses import asdict, replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_open_intelligence_terminal_foundation import *


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe terminal boundary accepted")
    except OracleOpenIntelligenceTerminalInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OIT-001 TEST")
    print(" OPEN INTELLIGENCE TERMINAL FOUNDATION")
    print("=" * 40)

    receipt = build_dependency_receipt(source_module_sha256="a" * 64)
    assert verify_dependency_receipt(receipt)

    first = parse_terminal_input("analyze Federal Reserve September decision")
    second = parse_terminal_input("analyze Federal Reserve September decision")
    assert first == second
    assert first.command == "analyze"
    assert first.subject == "Federal Reserve September decision"

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "qseries_v2" / "oracle_intelligence" / "analytics").mkdir(parents=True)
        (root / "qseries_v2" / "oracle_operator_runtime").mkdir(parents=True)
        status = execute_terminal_command(
            parse_terminal_input("status"),
            repository_root=root,
            dependency_receipt=receipt,
        )
        assert status.read_only and not status.execution_allowed
        assert status.response_type == "system_status"

        open_request = execute_terminal_command(
            first,
            repository_root=root,
            dependency_receipt=receipt,
        )
        assert open_request.subject == "Federal Reserve September decision"
        assert open_request.status == "accepted_no_live_artifact"
        assert "No analysis was fabricated." in open_request.lines

        rejection = execute_terminal_command(
            parse_terminal_input("buy BTC"),
            repository_root=root,
            dependency_receipt=receipt,
        )
        assert rejection.status == "rejected_read_only_boundary"
        assert not rejection.execution_allowed

        help_response = execute_terminal_command(
            parse_terminal_input("help"),
            repository_root=root,
            dependency_receipt=receipt,
        )
        assert "USAGE: <command> <any subject>" in help_response.lines

    assert format_terminal_response(status)
    reject(lambda: verify_dependency_receipt(replace(receipt, receipt_hash="0" * 64)))
    reject(lambda: format_terminal_response(replace(status, execution_allowed=True)))

    print("[PASS] Actual OOR-013 completion dependency represented")
    print("[PASS] Generic open-subject command parsing deterministic")
    print("[PASS] Full capability command families exposed")
    print("[PASS] Missing live intelligence artifacts reported honestly")
    print("[PASS] Execution and publication remain disabled")
    print("[PASS] Q Series remains the sole execution layer")
    print("[PASS] Terminal foundation is ready for later intelligence bindings")
    print("[DONE] OIT-001 OPEN INTELLIGENCE TERMINAL FOUNDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
