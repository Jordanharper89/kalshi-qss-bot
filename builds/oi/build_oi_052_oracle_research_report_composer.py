from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "oracle_research_report_composer.py"
TEST = ROOT / "test_oi_052_oracle_research_report_composer.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-052 Oracle Research Report Composer

Purpose:
- Convert synthesized Oracle intelligence into clean human-readable reports.
- Support terminal, Telegram, API, and future Oracle Terminal UI.
- Preserve Oracle as read-only research intelligence.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .oracle_intelligence_synthesis_engine import (
    oracle_intelligence_synthesis_engine,
    OracleIntelligenceSynthesisEngine,
)


class OracleResearchReportComposer:
    module_name = "oi_052_oracle_research_report_composer"

    def __init__(self, synthesis_engine: Optional[OracleIntelligenceSynthesisEngine] = None) -> None:
        self.synthesis_engine = synthesis_engine or oracle_intelligence_synthesis_engine

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "synthesis_engine": self.synthesis_engine.status()["status"],
        }

    def compose_report(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 25,
        format: str = "terminal",
    ) -> Dict[str, Any]:
        synthesis = self.synthesis_engine.synthesize(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
            include_graph=True,
        )

        summary = synthesis.get("summary", {})
        report = self._render(summary, synthesis, format=format)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "format": format,
            "market_ticker": summary.get("market_ticker"),
            "report": report,
            "sections": self._sections(summary, synthesis),
            "synthesis": synthesis,
        }

    def compose_from_synthesis(
        self,
        synthesis: Dict[str, Any],
        format: str = "terminal",
    ) -> Dict[str, Any]:
        summary = synthesis.get("summary", {})
        report = self._render(summary, synthesis, format=format)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "format": format,
            "market_ticker": summary.get("market_ticker"),
            "report": report,
            "sections": self._sections(summary, synthesis),
        }

    def _render(self, summary: Dict[str, Any], synthesis: Dict[str, Any], format: str = "terminal") -> str:
        sections = self._sections(summary, synthesis)

        if format == "telegram":
            return self._telegram(sections)

        if format == "api":
            return self._plain(sections)

        return self._terminal(sections)

    def _sections(self, summary: Dict[str, Any], synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        reasoning = synthesis.get("case_reasoning", {})
        distribution = synthesis.get("outcome_distribution", {})
        retrieval = synthesis.get("analog_retrieval", {})
        confidence = synthesis.get("adjusted_confidence", {})
        dna = synthesis.get("market_dna", {})
        graph = synthesis.get("knowledge_graph_context", {})

        resolution = distribution.get("resolution_distribution", {})
        movement = distribution.get("movement_distribution", {})
        timing = distribution.get("timing_distribution_minutes", {})
        tail = distribution.get("tail_risk", {})

        sections = [
            {
                "title": "Oracle Research Summary",
                "lines": [
                    f"Market: {summary.get('market_ticker') or 'UNKNOWN'}",
                    f"Expected Resolution: {summary.get('expected_resolution') or 'UNKNOWN'}",
                    f"Expected Probability: {self._pct(summary.get('expected_probability'))}",
                    f"Adjusted Confidence: {self._num(summary.get('adjusted_confidence'))}%",
                    f"Risk Level: {summary.get('risk_level') or 'unknown'}",
                    f"Tail Risk: {summary.get('tail_risk_level') or tail.get('tail_risk_level') or 'unknown'}",
                ],
            },
            {
                "title": "Historical Analog Evidence",
                "lines": [
                    f"Analog Count: {summary.get('analog_count', 0)}",
                    f"Top Analog: {self._top_analog_text(summary.get('top_analog'))}",
                    f"Avg Retrieval Score: {self._num(retrieval.get('summary', {}).get('avg_retrieval_score_pct'))}%",
                    f"Avg Similarity: {self._num(retrieval.get('summary', {}).get('avg_similarity_pct'))}%",
                    f"Avg DNA Similarity: {self._num(retrieval.get('summary', {}).get('avg_dna_similarity_pct'))}%",
                ],
            },
            {
                "title": "Outcome Distribution",
                "lines": [
                    f"YES Probability: {self._pct(resolution.get('yes_probability'))}",
                    f"NO Probability: {self._pct(resolution.get('no_probability'))}",
                    f"Known Outcomes: {resolution.get('known_outcome_count', 0)}",
                    f"Average Move: {self._num(movement.get('mean'))}%",
                    f"Median Move: {self._num(movement.get('median'))}%",
                    f"Average Resolution Time: {self._num(timing.get('mean'))} min",
                ],
            },
            {
                "title": "Confidence Learning",
                "lines": [
                    f"Raw Confidence: {self._num(confidence.get('raw_confidence'))}%",
                    f"Adjusted Confidence: {self._num(confidence.get('adjusted_confidence'))}%",
                    f"Confidence Delta: {self._num(confidence.get('delta'))}%",
                    f"Confidence Bucket: {confidence.get('bucket') or 'unknown'}",
                    f"Reason: {confidence.get('reason') or 'No confidence reason available.'}",
                ],
            },
            {
                "title": "Market DNA",
                "lines": [
                    f"DNA ID: {dna.get('dna_id') or 'unknown'}",
                    f"DNA Family: {dna.get('dna_family') or 'unknown'}",
                    f"Traits: {len(dna.get('traits', []))}",
                ],
            },
            {
                "title": "Knowledge Graph Context",
                "lines": [
                    f"Graph Nodes: {summary.get('graph_nodes') or graph.get('graph_summary', {}).get('total_nodes') or 0}",
                    f"Graph Edges: {summary.get('graph_edges') or graph.get('graph_summary', {}).get('total_edges') or 0}",
                    f"Market Node: {graph.get('market_node') or 'unknown'}",
                ],
            },
            {
                "title": "Oracle Reasoning",
                "lines": reasoning.get("reasoning", ["No reasoning lines available."]),
            },
        ]

        return sections

    def _terminal(self, sections: List[Dict[str, Any]]) -> str:
        lines = []
        lines.append("=" * 54)
        lines.append(" ORACLE RESEARCH REPORT")
        lines.append("=" * 54)

        for section in sections:
            lines.append("")
            lines.append(f"[{section['title']}]")
            for line in section.get("lines", []):
                lines.append(f"- {line}")

        lines.append("")
        lines.append("Read-only research report. Execution remains Q Series only.")
        return "\n".join(lines)

    def _telegram(self, sections: List[Dict[str, Any]]) -> str:
        lines = []
        lines.append("🧠 Oracle Research Report")

        for section in sections:
            lines.append("")
            lines.append(f"*{section['title']}*")
            for line in section.get("lines", []):
                lines.append(f"• {line}")

        lines.append("")
        lines.append("_Read-only research. Q Series handles execution._")
        return "\n".join(lines)

    def _plain(self, sections: List[Dict[str, Any]]) -> str:
        lines = []

        for section in sections:
            lines.append(section["title"])
            for line in section.get("lines", []):
                lines.append(line)
            lines.append("")

        lines.append("Read-only research report. Execution remains Q Series only.")
        return "\n".join(lines).strip()

    def _top_analog_text(self, analog: Optional[Dict[str, Any]]) -> str:
        if not analog:
            return "none"

        return (
            f"{analog.get('market_ticker')} "
            f"(retrieval {self._num(analog.get('retrieval_score_pct'))}%, "
            f"similarity {self._num(analog.get('similarity_pct'))}%)"
        )

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


oracle_research_report_composer = OracleResearchReportComposer()
'''

test_code = r'''from qseries_v2.oracle_intelligence.oracle_research_report_composer import OracleResearchReportComposer


class FakeSynthesisEngine:
    def status(self):
        return {"status": "ok"}

    def synthesize(self, *args, **kwargs):
        return {
            "summary": {
                "market_ticker": "REPORT-TEST",
                "expected_resolution": "YES",
                "expected_probability": 0.82,
                "adjusted_confidence": 79.5,
                "confidence_delta": -2.5,
                "avg_expected_move": 5.2,
                "median_expected_move": 4.8,
                "avg_resolution_minutes": 36,
                "tail_risk_level": "medium",
                "risk_level": "medium",
                "analog_count": 12,
                "graph_nodes": 20,
                "graph_edges": 30,
                "top_analog": {
                    "market_ticker": "ANALOG-1",
                    "retrieval_score_pct": 91.2,
                    "similarity_pct": 88.4,
                    "dna_similarity_pct": 86.0,
                },
            },
            "case_reasoning": {
                "reasoning": [
                    "Oracle found 12 similar historical cases.",
                    "Weighted evidence favors YES.",
                ],
            },
            "outcome_distribution": {
                "resolution_distribution": {
                    "yes_probability": 0.82,
                    "no_probability": 0.18,
                    "known_outcome_count": 12,
                },
                "movement_distribution": {
                    "mean": 5.2,
                    "median": 4.8,
                },
                "timing_distribution_minutes": {
                    "mean": 36,
                },
                "tail_risk": {
                    "tail_risk_level": "medium",
                },
            },
            "analog_retrieval": {
                "summary": {
                    "avg_retrieval_score_pct": 80.1,
                    "avg_similarity_pct": 76.2,
                    "avg_dna_similarity_pct": 70.3,
                },
            },
            "adjusted_confidence": {
                "raw_confidence": 82,
                "adjusted_confidence": 79.5,
                "delta": -2.5,
                "bucket": "80-90",
                "reason": "Oracle confidence is reasonably calibrated.",
            },
            "market_dna": {
                "dna_id": "dna_test",
                "dna_family": "family_test",
                "traits": ["momentum:strong_positive", "regime:trend"],
            },
            "knowledge_graph_context": {
                "market_node": "market:REPORT-TEST",
                "graph_summary": {
                    "total_nodes": 20,
                    "total_edges": 30,
                },
            },
        }


def test_oi_052_oracle_research_report_composer():
    composer = OracleResearchReportComposer(FakeSynthesisEngine())

    terminal = composer.compose_report({"ticker": "REPORT-TEST"}, format="terminal")
    assert terminal["status"] == "ok"
    assert terminal["read_only"] is True
    assert "ORACLE RESEARCH REPORT" in terminal["report"]
    assert "REPORT-TEST" in terminal["report"]
    assert "Expected Resolution: YES" in terminal["report"]

    telegram = composer.compose_report({"ticker": "REPORT-TEST"}, format="telegram")
    assert "🧠 Oracle Research Report" in telegram["report"]
    assert "*Oracle Research Summary*" in telegram["report"]

    api = composer.compose_report({"ticker": "REPORT-TEST"}, format="api")
    assert "Oracle Research Summary" in api["report"]

    status = composer.status()
    assert status["status"] == "ok"

    print("[PASS] OI-052 Oracle Research Report Composer")
    print({
        "market_ticker": terminal["market_ticker"],
        "format": terminal["format"],
        "sections": len(terminal["sections"]),
    })


if __name__ == "__main__":
    test_oi_052_oracle_research_report_composer()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .oracle_research_report_composer import oracle_research_report_composer, OracleResearchReportComposer\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-052 INSTALLER")
print(" Oracle Research Report Composer")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-052 installed")
print()
print("Run:")
print("python test_oi_052_oracle_research_report_composer.py")