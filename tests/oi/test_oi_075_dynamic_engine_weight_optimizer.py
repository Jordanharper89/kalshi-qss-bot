from qseries_v2.oracle_intelligence.dynamic_engine_weight_optimizer import DynamicEngineWeightOptimizer


class FakeMetaEngine:
    def evaluate_engines(self):
        return {
            "overall_health": 78.5,
            "research_quality": "good",
            "best_engine": "case_reasoning_engine",
            "weakest_engine": "analog_retrieval_engine",
            "highest_drift_engine": "analog_retrieval_engine",
            "recommended_weight_changes": {
                "case_reasoning_engine": 3.0,
                "outcome_distribution_engine": 1.5,
                "analog_retrieval_engine": -3.0,
                "adaptive_confidence_engine": 0.0,
                "market_dna_engine": 1.5,
                "knowledge_graph_engine": 0.0,
            },
            "engine_scores": {
                "case_reasoning_engine": {
                    "meta_score": 90,
                    "avg_drift": 2,
                    "calibration_gap": 1,
                },
                "outcome_distribution_engine": {
                    "meta_score": 82,
                    "avg_drift": 4,
                    "calibration_gap": -3,
                },
                "analog_retrieval_engine": {
                    "meta_score": 48,
                    "avg_drift": 22,
                    "calibration_gap": -20,
                },
                "adaptive_confidence_engine": {
                    "meta_score": 72,
                    "avg_drift": 6,
                    "calibration_gap": -5,
                },
                "market_dna_engine": {
                    "meta_score": 80,
                    "avg_drift": 3,
                    "calibration_gap": 0,
                },
                "knowledge_graph_engine": {
                    "meta_score": 70,
                    "avg_drift": 5,
                    "calibration_gap": -4,
                },
            },
        }


def test_oi_075_dynamic_engine_weight_optimizer():
    optimizer = DynamicEngineWeightOptimizer(FakeMetaEngine())

    result = optimizer.optimize_weights()

    assert result["status"] == "ok"
    assert result["read_only"] is True

    weights = result["optimized_weights"]
    assert round(sum(weights.values()), 6) == 1.0

    assert weights["case_reasoning_engine"] > result["base_weights"]["case_reasoning_engine"]
    assert weights["analog_retrieval_engine"] < result["base_weights"]["analog_retrieval_engine"]

    assert optimizer.get_weight("case_reasoning_engine") == weights["case_reasoning_engine"]
    assert optimizer.last_weights()["status"] == "ok"

    status = optimizer.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-075 Dynamic Engine Weight Optimizer")
    print({
        "optimized_weights": weights,
        "weight_deltas": result["weight_deltas"],
        "meta_summary": result["meta_summary"],
    })


if __name__ == "__main__":
    test_oi_075_dynamic_engine_weight_optimizer()
