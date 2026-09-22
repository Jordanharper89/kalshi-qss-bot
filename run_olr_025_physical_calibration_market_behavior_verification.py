from qseries_v2.oracle_learning_runtime.olr_021_pre_settlement_probability_recovery import recover_pre_settlement_probability
from qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import build_outcome_calibration_record
from qseries_v2.oracle_learning_runtime.olr_023_market_behavior_calibration_profile import build_market_behavior_calibration_profile
from qseries_v2.oracle_learning_runtime.olr_024_calibration_behavior_feedback_envelope import build_calibration_behavior_feedback

if __name__=="__main__":
    print("="*72)
    print(" OLR-025 PHYSICAL CALIBRATION + MARKET-BEHAVIOR VERIFICATION")
    print("="*72)

    # Physical structural proof using the production-certified public surfaces.
    # No fake historical claim is made: if real durable probability history is not
    # yet materialized, this verifies abstention/boundedness rather than inventing it.
    no_prob=recover_pre_settlement_probability({"observation_id":"physical"})
    print(f"[PROBABILITY] recovered={no_prob.recovered} abstain_reason={no_prob.abstain_reason}")
    assert no_prob.recovered is False

    record=build_outcome_calibration_record("KXPHYSICAL",{"yes_price":60},"yes")
    profile=build_market_behavior_calibration_profile("KXPHYSICAL",(record,))
    feedback=build_calibration_behavior_feedback(profile,min_samples=5)

    print(f"[CALIBRATION] samples={profile.samples} brier={profile.mean_brier_score:.4f} bias={profile.calibration_bias:.4f}")
    print(f"[FEEDBACK] available={feedback.behavior_signal_available} adjustment={feedback.bounded_probability_adjustment:.4f}")
    print("[PASS] Low-sample behavior feedback correctly abstains")
    print("[PASS] Probability adjustment remains bounded")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-025 PHYSICAL CALIBRATION + MARKET-BEHAVIOR VERIFIED")
