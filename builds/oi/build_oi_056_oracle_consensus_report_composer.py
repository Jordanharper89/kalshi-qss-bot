from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "oracle_consensus_report_composer.py"
TEST = ROOT / "test_oi_056_oracle_consensus_report_composer.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-056 Oracle Consensus Report Composer

Purpose:
- Convert OI-055 consensus research packets into human-readable reports.
- Include consensus score, agreement, stability, certainty index, votes, and outliers.
- Support terminal, Telegram, and API/plain formats.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .consensus_research_packet_bridge import (
    consensus_research_packet_bridge,
    ConsensusResearchPacketBridge,
)


class OracleConsensusReportComposer:
    module_name = "oi_056_oracle_consensus_report_composer"

    def __init__(self, consensus_packet_bridge: Optional[ConsensusResearchPacketBridge] = None) -> None:
        self.consensus_packet_bridge = consensus_packet_bridge or consensus_research_packet_bridge

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "consensus_packet_bridge": self._safe_status(self.consensus_packet_bridge),
        }

    def compose_consensus_report(
        self,
        current_setup: Dict[str, Any],
        limit: int = 25,
        format: str = "terminal",
    ) -> Dict[str, Any]:
        packet = self.consensus_packet_bridge.build_consensus_packet(
            current_setup=current_setup,
            limit=limit,
            report_format=format,
            include_raw=True,
        )

        return self.compose_from_packet(packet, format=format)

    def compose_from_packet(self, packet: Dict[str, Any], format: str = "terminal") -> Dict[str, Any]:
        sections = self._sections(packet)
        report = self._render(sections, format=format)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "format": format,
            "market_ticker": packet.get("market_ticker"),
            "report": report,
            "sections": sections,
            "packet": packet,
        }

    def _sections(self, packet: Dict[str, Any]) -> List[Dict[str, Any]]:
        summary = packet.get("summary", {}) or {}
        signals = packet.get("signals", {}) or {}
        consensus = packet.get("consensus", {}) or {}
        votes = packet.get("consensus_votes", []) or []
        explanation = packet.get("consensus_explanation", []) or []

        outliers = consensus.get("outlier_engines", []) or []

        return [
            {
                "title": "Oracle Consensus Summary",
                "lines": [
                    f"Market: {summary.get('market_ticker') or packet.get('market_ticker') or 'UNKNOWN'}",
                    f"Expected Resolution: {summary.get('expected_resolution') or signals.get('expected_resolution') or 'UNKNOWN'}",
                    f"Consensus Side: {consensus.get('consensus_side') or 'UNKNOWN'}",
                    f"Consensus Score: {self._num(consensus.get('consensus_score_pct'))}%",
                    f"Agreement: {self._num(consensus.get('agreement_pct'))}%",
                    f"Disagreement: {self._num(consensus.get('disagreement_pct'))}%",
                    f"Research Stability: {consensus.get('research_stability') or 'unknown'}",
                    f"Research Certainty Index: {self._num(consensus.get('research_certainty_index'))}/100",
                    f"Final Research Grade: {signals.get('final_research_grade') or signals.get('research_grade') or 'UNRATED'}",
                ],
            },
            {
                "title": "Forecast Evidence",
                "lines": [
                    f"Expected Probability: {self._pct(summary.get('expected_probability') or signals.get('expected_probability'))}",
                    f"Adjusted Confidence: {self._num(summary.get('adjusted_confidence') or signals.get('adjusted_confidence'))}%",
                    f"Confidence Delta: {self._num(summary.get('confidence_delta') or signals.get('confidence_delta'))}%",
                    f"Risk Level: {summary.get('risk_level') or signals.get('risk_level') or 'unknown'}",
                    f"Tail Risk: {summary.get('tail_risk_level') or signals.get('tail_risk_level') or 'unknown'}",
                    f"Analog Count: {summary.get('analog_count', 0)}",
                ],
            },
            {
                "title": "Subsystem Votes",
                "lines": self._vote_lines(votes),
            },
            {
                "title": "Consensus Explanation",
                "lines": explanation or ["No consensus explanation available."],
            },
            {
                "title": "Outlier Engines",
                "lines": self._outlier_lines(outliers),
            },
            {
                "title": "Execution Boundary",
                "lines": [
                    "Oracle output is read-only research.",
                    "Execution remains Q Series only.",
                    f"Execution Enabled: {packet.get('api', {}).get('execution_enabled', False)}",
                ],
            },
        ]

    def _vote_lines(self, votes: List[Dict[str, Any]]) -> List[str]:
        if not votes:
            return ["No subsystem votes available."]

        lines = []

        for vote in votes:
            usable = "usable" if vote.get("usable", True) else "not usable"
            lines.append(
                f"{vote.get('engine')}: {vote.get('side')} "
                f"{self._num(vote.get('confidence'))}% "
                f"(weight {self._num(vote.get('weight'))}, {usable})"
            )

        return lines

    def _outlier_lines(self, outliers: List[Dict[str, Any]]) -> List[str]:
        if not outliers:
            return ["No major outlier engines detected."]

        return [
            f"{o.get('engine')}: {o.get('side')} {self._num(o.get('confidence'))}% — {o.get('reason')}"
            for o in outliers
        ]

    def _render(self, sections: List[Dict[str, Any]], format: str = "terminal") -> str:
        if format == "telegram":
            return self._telegram(sections)

        if format == "api":
            return self._plain(sections)

        return self._terminal(sections)

    def _terminal(self, sections: List[Dict[str, Any]]) -> str:
        lines = [
            "=" * 58,
            " ORACLE CONSENSUS RESEARCH REPORT",
            "=" * 58,
        ]

        for section in sections:
            lines.append("")
            lines.append(f"[{section['title']}]")
            for line in section.get("lines", []):
                lines.append(f"- {line}")

        return "\n".join(lines)

    def _telegram(self, sections: List[Dict[str, Any]]) -> str:
        lines = ["🧠 Oracle Consensus Research Report"]

        for section in sections:
            lines.append("")
            lines.append(f"*{section['title']}*")
            for line in section.get("lines", []):
                lines.append(f"• {line}")

        return "\n".join(lines)

    def _plain(self, sections: List[Dict[str, Any]]) -> str:
        lines = []

        for section in sections:
            lines.append(section["title"])
            for line in section.get("lines", []):
                lines.append(line)
            lines.append("")

        return "\n".join(lines).strip()

    def _pct(self, value: Any) -> str:
        if value is None:
            return "unknown"

        try:
            v = float(value)
            if v <= 1:
                v *= 100
            return f"{round(v, 2)}%"
        except Exception:
            return "unknown"

    def _num(self, value: Any) -> str:
        if value is None:
            return "unknown"

        try:
            return str(round(float(value), 2))
        except Exception:
            return "unknown"

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


oracle_consensus_report_composer = OracleConsensusReportComposer()
'''

test_code = r'''from qseries_v2.oracle_intelligence.oracle_consensus_report_composer import OracleConsensusReportComposer


class FakeConsensusPacketBridge:
    def status(self):
        return {"status": "ok"}

    def build_consensus_packet(self, *args, **kwargs):
        return {
            "status": "ok",
            "read_only": True,
            "packet_type": "oracle_consensus_research_packet",
            "market_ticker": "CONSENSUS-REPORT-TEST",
            "summary": {
                "market_ticker": "CONSENSUS-REPORT-TEST",
                "expected_resolution": "YES",
                "expected_probability": 0.84,
                "adjusted_confidence": 82,
                "confidence_delta": -2,
                "risk_level": "medium",
                "tail_risk_level": "low",
                "analog_count": 12,
            },
            "signals": {
                "final_research_grade": "A",
                "execution_owner": "Q Series",
                "actionable": False,
            },
            "consensus": {
                "consensus_side": "YES",
                "consensus_score_pct": 87.5,
                "agreement_pct": 92.0,
                "disagreement_pct": 8.0,
                "research_stability": "high",
                "research_certainty_index": 91.0,
                "outlier_engines": [],
            },
            "consensus_votes": [
                {"engine": "case_reasoning", "side": "YES", "confidence": 86, "weight": 0.24, "usable": True},
                {"engine": "outcome_distribution", "side": "YES", "confidence": 82, "weight": 0.24, "usable": True},
            ],
            "consensus_explanation": [
                "Oracle consensus favors YES.",
                "Research stability is high.",
            ],
            "api": {
                "execution_enabled": False,
            },
        }


def test_oi_056_oracle_consensus_report_composer():
    composer = OracleConsensusReportComposer(FakeConsensusPacketBridge())

    terminal = composer.compose_consensus_report({"ticker": "CONSENSUS-REPORT-TEST"}, format="terminal")
    assert terminal["status"] == "ok"
    assert terminal["read_only"] is True
    assert "ORACLE CONSENSUS RESEARCH REPORT" in terminal["report"]
    assert "Consensus Score: 87.5%" in terminal["report"]
    assert "case_reasoning: YES" in terminal["report"]
    assert "Execution remains Q Series only." in terminal["report"]

    telegram = composer.compose_consensus_report({"ticker": "CONSENSUS-REPORT-TEST"}, format="telegram")
    assert "🧠 Oracle Consensus Research Report" in telegram["report"]
    assert "*Oracle Consensus Summary*" in telegram["report"]

    api = composer.compose_consensus_report({"ticker": "CONSENSUS-REPORT-TEST"}, format="api")
    assert "Oracle Consensus Summary" in api["report"]

    status = composer.status()
    assert status["status"] == "ok"

    print("[PASS] OI-056 Oracle Consensus Report Composer")
    print({
        "market_ticker": terminal["market_ticker"],
        "format": terminal["format"],
        "sections": len(terminal["sections"]),
    })


if __name__ == "__main__":
    test_oi_056_oracle_consensus_report_composer()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .oracle_consensus_report_composer import oracle_consensus_report_composer, OracleConsensusReportComposer\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-056 INSTALLER")
print(" Oracle Consensus Report Composer")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-056 installed")
print()
print("Run:")
print("python test_oi_056_oracle_consensus_report_composer.py")