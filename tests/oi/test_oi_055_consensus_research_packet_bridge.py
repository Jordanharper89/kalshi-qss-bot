from qseries_v2.oracle_intelligence.consensus_research_packet_bridge import ConsensusResearchPacketBridge


class FakePacketAdapter:
    def status(self):
        return {"status": "ok"}

    def build_packet(self, *args, **kwargs):
        include_raw = kwargs.get("include_raw", True)

        packet = {
            "status": "ok",
            "read_only": True,
            "packet_type": "oracle_research_packet",
            "market_ticker": "CONSENSUS-PACKET-TEST",
            "summary": {
                "market_ticker": "CONSENSUS-PACKET-TEST",
                "expected_resolution": "YES",
                "expected_probability": 0.84,
                "adjusted_confidence": 82,
            },
            "signals": {
                "expected_resolution": "YES",
                "expected_probability": 0.84,
                "adjusted_confidence": 82,
                "research_grade": "A-",
                "actionable": False,
                "execution_owner": "Q Series",
            },
            "api": {
                "version": "oi-053",
                "stable": True,
                "execution_enabled": False,
            },
            "report": "fake report",
            "sections": [],
        }

        if include_raw:
            packet["raw"] = {
                "synthesis": {
                    "summary": {
                        "market_ticker": "CONSENSUS-PACKET-TEST",
                        "expected_resolution": "YES",
                    }
                }
            }

        return packet


class FakeConsensusEngine:
    def status(self):
        return {"status": "ok"}

    def build_consensus_from_synthesis(self, synthesis):
        return self._result()

    def build_consensus(self, *args, **kwargs):
        return self._result()

    def _result(self):
        return {
            "status": "ok",
            "read_only": True,
            "market_ticker": "CONSENSUS-PACKET-TEST",
            "consensus": {
                "consensus_side": "YES",
                "consensus_score_pct": 87.5,
                "agreement_pct": 92.0,
                "disagreement_pct": 8.0,
                "research_stability": "high",
                "research_certainty_index": 91.0,
                "outlier_engines": [],
            },
            "votes": [
                {"engine": "case_reasoning", "side": "YES", "confidence": 86},
                {"engine": "outcome_distribution", "side": "YES", "confidence": 82},
            ],
            "explanation": [
                "Oracle consensus favors YES.",
                "Research stability is high.",
            ],
        }


def test_oi_055_consensus_research_packet_bridge():
    bridge = ConsensusResearchPacketBridge(FakePacketAdapter(), FakeConsensusEngine())

    packet = bridge.build_api_packet({"ticker": "CONSENSUS-PACKET-TEST"})

    assert packet["status"] == "ok"
    assert packet["read_only"] is True
    assert packet["packet_type"] == "oracle_consensus_research_packet"
    assert packet["api"]["version"] == "oi-055"
    assert packet["api"]["consensus_enabled"] is True
    assert packet["api"]["execution_enabled"] is False
    assert packet["summary"]["consensus_side"] == "YES"
    assert packet["summary"]["consensus_validated"] is True
    assert packet["signals"]["final_research_grade"] in {"A+", "A", "A-", "B+", "B", "WATCH"}
    assert len(packet["consensus_votes"]) == 2
    assert "raw" in packet
    assert "consensus" in packet["raw"]

    telegram = bridge.build_telegram_packet({"ticker": "CONSENSUS-PACKET-TEST"})
    assert "raw" not in telegram
    assert telegram["signals"]["execution_owner"] == "Q Series"

    status = bridge.status()
    assert status["status"] == "ok"

    print("[PASS] OI-055 Consensus Research Packet Bridge")
    print({
        "packet_type": packet["packet_type"],
        "consensus_side": packet["summary"]["consensus_side"],
        "final_grade": packet["signals"]["final_research_grade"],
        "execution_enabled": packet["api"]["execution_enabled"],
    })


if __name__ == "__main__":
    test_oi_055_consensus_research_packet_bridge()
