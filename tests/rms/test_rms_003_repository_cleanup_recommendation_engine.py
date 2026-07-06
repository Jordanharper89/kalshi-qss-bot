from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qseries_v2.repository_management.repository_inventory_engine import scan_repository
from qseries_v2.repository_management.repository_classification_engine import classify_repository_inventory
from qseries_v2.repository_management.repository_cleanup_recommendation_engine import recommend_repository_cleanup


def test_cleanup_recommendations_from_live_repo():
    inventory = scan_repository(ROOT)
    classification = classify_repository_inventory(inventory)
    result = recommend_repository_cleanup(classification)

    assert result.engine_id == "RMS-003"
    assert result.input_count > 0
    assert result.recommendation_count > 0
    assert result.telemetry["does_not_delete_files"] is True
    assert result.telemetry["does_not_move_files"] is True
    assert result.action_counts


def test_secret_gets_never_commit_recommendation():
    result = recommend_repository_cleanup(
        {"records": [{"path": ".env", "name": ".env", "classification": "SECRET", "action": "ignore"}]}
    )

    assert result.recommendations[0].recommendation == "ignore_never_commit"
    assert result.recommendations[0].risk_level == "critical"


def test_junk_gets_delete_candidate_recommendation():
    result = recommend_repository_cleanup(
        {"records": [{"path": "10", "name": "10", "classification": "ACCIDENTAL_JUNK", "action": "delete_candidate"}]}
    )

    assert result.recommendations[0].recommendation == "delete_after_confirming_zero_byte"
    assert result.recommendations[0].safe_to_automate is True


if __name__ == "__main__":
    test_cleanup_recommendations_from_live_repo()
    test_secret_gets_never_commit_recommendation()
    test_junk_gets_delete_candidate_recommendation()

    inventory = scan_repository(ROOT)
    classification = classify_repository_inventory(inventory)
    result = recommend_repository_cleanup(classification)

    print("[PASS] RMS-003 Repository Cleanup Recommendation Engine")
    print(result.to_dict())
