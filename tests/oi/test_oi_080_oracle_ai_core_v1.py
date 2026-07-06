from qseries_v2.oracle_intelligence.oracle_ai_core_v1 import OracleAICoreV1


class FakeMeta:
    def status(self):
        return {"status": "ok"}

    def evaluate_engines(self):
        return {
            "status": "ok",
            "read_only": True,
            "overall_health": 88,
            "research_quality": "strong",
            "best_engine": "case_reasoning_engine",
            "weakest_engine": "analog_retrieval_engine",
            "engine_scores": {},
            "recommended_weight_changes": {},
        }


class FakeWeights:
    def status(self):
        return {"status": "ok"}

    def optimize_weights(self, meta_report=None):
        return {
            "status": "ok",
            "read_only": True,
            "optimized_weights": {
                "case_reasoning_engine": 0.28,
                "outcome_distribution_engine": 0.24,
                "analog_retrieval_engine": 0.16,
                "adaptive_confidence_engine": 0.14,
                "market_dna_engine": 0.10,
                "knowledge_graph_engine": 0.08,
            },
        }


class FakeQuality:
    def status(self):
        return {"status": "ok"}

    def score_packet(self, packet, meta_report=None, weight_report=None, runtime_status=None):
        return {
            "status": "ok",
            "read_only": True,
            "research_quality_score": 91.5,
            "grade": "A",
            "institutional_ready": True,
            "execution_enabled": False,
            "execution_owner": "Q Series",
        }


class FakeAttribution:
    def status(self):
        return {"status": "ok"}

    def attribute_packet(self, packet, actual_side=None, market_ticker=None):
        return {
            "status": "ok",
            "read_only": True,
            "attribution": {
                "largest_positive_contributor": "case_reasoning_engine",
                "largest_negative_contributor": "analog_retrieval_engine",
                "alpha_added": 18.5,
            },
        }


class FakeAgreement:
    def status(self):
        return {"status": "ok"}

    def analyze_consensus_packet(self, packet, actual_side=None, record=True):
        return {
            "status": "ok",
            "read_only": True,
            "consensus_diversity": {
                "diversity_level": "high",
                "diversity_score": 86,
            },
        }


class FakeInstitutional:
    def status(self):
        return {"status": "ok"}

    def score(self, **kwargs):
        return {
            "status": "ok",
            "read_only": True,
            "institutional_intelligence_score": 92.7,
            "grade": "A",
            "institutional_ready": True,
        }


def test_oi_080_oracle_ai_core_v1():
    core = OracleAICoreV1(
        meta_engine=FakeMeta(),
        weight_optimizer=FakeWeights(),
        quality_engine=FakeQuality(),
        attribution_engine=FakeAttribution(),
        agreement_matrix=FakeAgreement(),
        institutional_engine=FakeInstitutional(),
    )

    packet = {
        "market_ticker": "AI-CORE-TEST",
        "summary": {
            "market_ticker": "AI-CORE-TEST",
            "expected_resolution": "YES",
            "expected_probability": 0.88,
            "adjusted_confidence": 86,
        },
        "signals": {
            "expected_resolution": "YES",
            "execution_enabled": False,
        },
        "consensus_votes": [
            {"engine": "case_reasoning_engine", "side": "YES", "confidence": 90, "weight": 0.24},
            {"engine": "outcome_distribution_engine", "side": "YES", "confidence": 86, "weight": 0.24},
        ],
    }

    result = core.build_ai_research_envelope(packet, actual_side="YES", runtime_status={"health": "healthy"})

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["market_ticker"] == "AI-CORE-TEST"
    assert result["execution_enabled"] is False
    assert result["execution_owner"] == "Q Series"
    assert result["research_quality"]["research_quality_score"] == 91.5
    assert result["institutional_intelligence"]["institutional_intelligence_score"] == 92.7
    assert result["final_summary"]["institutional_ready"] is True
    assert result["final_summary"]["consensus_diversity"] == "high"

    hist = core.history()
    assert hist["count"] == 1

    status = core.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-080 Oracle AI Core v1")
    print({
        "market_ticker": result["market_ticker"],
        "quality": result["final_summary"]["research_quality_score"],
        "institutional_score": result["final_summary"]["institutional_intelligence_score"],
        "history_count": hist["count"],
    })


if __name__ == "__main__":
    test_oi_080_oracle_ai_core_v1()
