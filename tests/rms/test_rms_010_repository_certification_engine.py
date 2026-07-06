from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_integration_gate_engine import run_repository_integration_gate
from qseries_v2.repository_management.repository_certification_engine import certify_repository_management


def test_repository_certification_from_live_gate():
    gate = run_repository_integration_gate(ROOT)
    result = certify_repository_management(gate)

    assert result.engine_id == "RMS-010"
    assert result.decision_count == 1
    assert result.telemetry["does_not_move_files"] is True
    assert result.telemetry["certification_is_advisory"] is True


def test_passed_gate_certifies():
    result = certify_repository_management(
        {
            "passed": True,
            "check_count": 27,
            "pass_count": 27,
            "fail_count": 0,
        }
    )

    assert result.certified is True
    assert result.status == "certified"
    assert result.certification_level == "certified"


def test_failed_gate_blocks_certification():
    result = certify_repository_management(
        {
            "passed": False,
            "check_count": 27,
            "pass_count": 26,
            "fail_count": 1,
        }
    )

    assert result.certified is False
    assert result.status == "blocked"
    assert result.certification_level == "not_certified"


if __name__ == "__main__":
    test_repository_certification_from_live_gate()
    test_passed_gate_certifies()
    test_failed_gate_blocks_certification()

    gate = run_repository_integration_gate(ROOT)
    result = certify_repository_management(gate)

    print("[PASS] RMS-010 Repository Certification Engine")
    print(result.to_dict())
