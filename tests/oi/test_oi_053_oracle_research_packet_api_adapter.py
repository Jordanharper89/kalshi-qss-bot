from qseries_v2.oracle_intelligence.oracle_research_packet_api_adapter import OracleResearchPacketAPIAdapter


class FakeSynthesis:
    def status(self):
        return {"status": "ok"}

    def synthesize(self, *args, **kwargs):
        return {
            "summary": {
                "market_ticker": "API-PACKET-TEST",
                "expected_resolution": "YES",
                "expected_probability": 0.86,
                "adjusted_confidence": 84.0,
                "confidence_delta": -1.5,
                "risk_level": "medium",
                "tail_risk_level": "low",
                "analog_count": 9,
                "research_ready": True,
            }
        }


class FakeComposer:
    def status(self):
        return {"status": "ok"}

    def compose_from_synthesis(self, synthesis, format="terminal"):
        return {
            "status": "ok",
            "read_only": True,
            "format": format,
            "market_ticker": synthesis["summary"]["market_ticker"],
            "report": f"Report format={format} market={synthesis['summary']['market_ticker']}",
            "sections": [
                {"title": "Oracle Research Summary", "lines": ["Expected Resolution: YES"]}
            ],
        }


def test_oi_053_oracle_research_packet_api_adapter():
    adapter = OracleResearchPacketAPIAdapter(FakeSynthesis(), FakeComposer())

    terminal = adapter.build_terminal_packet({"ticker": "API-PACKET-TEST"})
    assert terminal["status"] == "ok"
    assert terminal["read_only"] is True
    assert terminal["packet_type"] == "oracle_research_packet"
    assert terminal["api"]["execution_enabled"] is False
    assert terminal["market_ticker"] == "API-PACKET-TEST"
    assert terminal["report_format"] == "terminal"
    assert "raw" in terminal

    telegram = adapter.build_telegram_packet({"ticker": "API-PACKET-TEST"})
    assert telegram["report_format"] == "telegram"
    assert "raw" not in telegram

    api = adapter.build_api_packet({"ticker": "API-PACKET-TEST"})
    assert api["report_format"] == "api"
    assert api["signals"]["actionable"] is False
    assert api["signals"]["execution_owner"] == "Q Series"
    assert api["signals"]["research_grade"] in {"A+", "A", "A-", "B+", "B", "WATCH", "UNRATED"}

    status = adapter.status()
    assert status["status"] == "ok"

    print("[PASS] OI-053 Oracle Research Packet API Adapter")
    print({
        "market_ticker": api["market_ticker"],
        "research_grade": api["signals"]["research_grade"],
        "execution_enabled": api["api"]["execution_enabled"],
    })


if __name__ == "__main__":
    test_oi_053_oracle_research_packet_api_adapter()
