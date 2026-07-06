from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_022_rhythm_insight_bridge.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE = OI_DIR / "rhythm_insight_bridge.py"

BRIDGE.write_text(textwrap.dedent(r'''
"""
OI-022 Rhythm Insight Bridge

Purpose:
- Bridge OI-021 Market Rhythm Analyzer into Oracle Intelligence.
- Convert raw rhythm profiles into clean Oracle-ready insight packets.
- Remain read-only.
- No execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from .market_rhythm_analyzer import oracle_market_rhythm_analyzer
except Exception:
    oracle_market_rhythm_analyzer = None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


@dataclass
class RhythmInsightPacket:
    module: str
    status: str
    generated_at: str
    rows_analyzed: int
    market_clock: Dict[str, Any]
    liquidity_intelligence: Dict[str, Any]
    spread_intelligence: Dict[str, Any]
    volume_intelligence: Dict[str, Any]
    volatility_intelligence: Dict[str, Any]
    category_intelligence: Dict[str, Any]
    oracle_summary: List[str]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RhythmInsightBridge:
    """
    Read-only Oracle bridge for market rhythm intelligence.
    """

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or oracle_market_rhythm_analyzer
        self.last_packet: Optional[Dict[str, Any]] = None

    def diagnostics(self) -> Dict[str, Any]:
        analyzer_ready = self.analyzer is not None

        analyzer_diag = {}
        if analyzer_ready and hasattr(self.analyzer, "diagnostics"):
            analyzer_diag = self.analyzer.diagnostics()

        return {
            "module": "OI-022 Rhythm Insight Bridge",
            "status": "ok" if analyzer_ready else "missing_analyzer",
            "analyzer_ready": analyzer_ready,
            "analyzer_status": analyzer_diag.get("status"),
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def build_packet(self) -> Dict[str, Any]:
        if self.analyzer is None:
            packet = RhythmInsightPacket(
                module="OI-022 Rhythm Insight Bridge",
                status="missing_analyzer",
                generated_at=self._now(),
                rows_analyzed=0,
                market_clock={},
                liquidity_intelligence={},
                spread_intelligence={},
                volume_intelligence={},
                volatility_intelligence={},
                category_intelligence={},
                oracle_summary=["OI-021 analyzer is not available."],
                read_only=True,
                execution_allowed=False,
            ).to_dict()
            self.last_packet = packet
            return packet

        snapshot = self.analyzer.analyze() if hasattr(self.analyzer, "analyze") else {}
        insights = self.analyzer.oracle_insights() if hasattr(self.analyzer, "oracle_insights") else {}

        packet = RhythmInsightPacket(
            module="OI-022 Rhythm Insight Bridge",
            status=snapshot.get("status", "unknown"),
            generated_at=self._now(),
            rows_analyzed=snapshot.get("rows_analyzed", 0),
            market_clock=self._market_clock(insights),
            liquidity_intelligence=self._metric_intelligence("liquidity", insights),
            spread_intelligence=self._metric_intelligence("spread", insights),
            volume_intelligence=self._metric_intelligence("volume", insights),
            volatility_intelligence=self._metric_intelligence("volatility", insights),
            category_intelligence=self._category_intelligence(insights),
            oracle_summary=self._summary(snapshot, insights),
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def get_packet(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return self.build_packet()
        return self.last_packet

    def oracle_context(self) -> Dict[str, Any]:
        packet = self.get_packet()

        return {
            "context_type": "market_rhythm",
            "module": "oracle_rhythm_context",
            "status": packet.get("status"),
            "rows_analyzed": packet.get("rows_analyzed"),
            "summary": packet.get("oracle_summary", []),
            "market_clock": packet.get("market_clock", {}),
            "category_intelligence": packet.get("category_intelligence", {}),
            "read_only": True,
            "execution_allowed": False,
        }

    def _market_clock(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "best_activity_hours": insights.get("best_activity_hours", []),
            "highest_volume_hours": insights.get("highest_volume_hours", []),
            "strongest_liquidity_hours": insights.get("strongest_liquidity_hours", []),
            "highest_volatility_hours": insights.get("highest_volatility_hours", []),
            "interpretation": "Market clock identifies when activity, liquidity, volume, and volatility historically cluster.",
        }

    def _metric_intelligence(self, metric: str, insights: Dict[str, Any]) -> Dict[str, Any]:
        key_map = {
            "liquidity": "strongest_liquidity_hours",
            "spread": "widest_spread_hours",
            "volume": "highest_volume_hours",
            "volatility": "highest_volatility_hours",
        }

        hours = insights.get(key_map.get(metric, ""), [])

        return {
            "metric": metric,
            "top_hours": hours,
            "signal_use": "context_only",
            "execution_allowed": False,
        }

    def _category_intelligence(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        categories = insights.get("category_patterns", {}) or {}

        ranked = []
        for name, data in categories.items():
            ranked.append({
                "category": name,
                "records": data.get("records", 0),
                "top_hours": data.get("top_hours", []),
                "avg_volume": _safe_float((data.get("volume") or {}).get("avg")),
                "avg_liquidity": _safe_float((data.get("liquidity") or {}).get("avg")),
                "avg_spread": _safe_float((data.get("spread") or {}).get("avg")),
                "price_volatility": _safe_float(data.get("price_volatility")),
            })

        ranked.sort(key=lambda x: x["records"], reverse=True)

        return {
            "categories_ranked": ranked,
            "count": len(ranked),
            "interpretation": "Category patterns help Oracle understand which market types behave differently across time.",
        }

    def _summary(self, snapshot: Dict[str, Any], insights: Dict[str, Any]) -> List[str]:
        rows = snapshot.get("rows_analyzed", 0)

        if snapshot.get("status") != "ok":
            return [
                "Market rhythm intelligence is installed but waiting for usable historical data.",
                "Oracle remains read-only and will not execute trades.",
            ]

        best_hours = insights.get("best_activity_hours", [])
        volume_hours = insights.get("highest_volume_hours", [])
        spread_hours = insights.get("widest_spread_hours", [])

        summary = [f"Oracle analyzed {rows} historical market records."]

        if best_hours:
            summary.append(f"Most active historical hour bucket: {best_hours[0].get('key')}.")

        if volume_hours:
            summary.append(f"Highest volume historical hour bucket: {volume_hours[0].get('key')}.")

        if spread_hours:
            summary.append(f"Widest spread historical hour bucket: {spread_hours[0].get('key')}.")

        summary.append("Rhythm intelligence is context-only and execution remains disabled.")

        return summary

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_rhythm_insight_bridge = RhythmInsightBridge()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
from qseries_v2.oracle_intelligence.rhythm_insight_bridge import RhythmInsightBridge


class FakeAnalyzer:
    def diagnostics(self):
        return {
            "status": "ok",
            "database_exists": True,
        }

    def analyze(self):
        return {
            "status": "ok",
            "rows_analyzed": 100,
            "category_patterns": {
                "crypto": {
                    "records": 60,
                    "top_hours": [{"hour": "14", "activity_score": 900}],
                    "volume": {"avg": 500},
                    "liquidity": {"avg": 2000},
                    "spread": {"avg": 3.5},
                    "price_volatility": 8.2,
                },
                "sports": {
                    "records": 40,
                    "top_hours": [{"hour": "19", "activity_score": 700}],
                    "volume": {"avg": 350},
                    "liquidity": {"avg": 1200},
                    "spread": {"avg": 4.1},
                    "price_volatility": 6.4,
                },
            },
        }

    def oracle_insights(self):
        return {
            "status": "ok",
            "rows_analyzed": 100,
            "best_activity_hours": [{"key": "14", "score": 900}],
            "strongest_liquidity_hours": [{"key": "15", "score": 2000}],
            "widest_spread_hours": [{"key": "3", "score": 7.5}],
            "highest_volume_hours": [{"key": "14", "score": 500}],
            "highest_volatility_hours": [{"key": "20", "score": 9.2}],
            "category_patterns": self.analyze()["category_patterns"],
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_022_rhythm_insight_bridge():
    bridge = RhythmInsightBridge(FakeAnalyzer())

    diagnostics = bridge.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["analyzer_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    packet = bridge.build_packet()
    assert packet["status"] == "ok"
    assert packet["rows_analyzed"] == 100
    assert packet["market_clock"]["best_activity_hours"]
    assert packet["liquidity_intelligence"]["top_hours"]
    assert packet["spread_intelligence"]["top_hours"]
    assert packet["volume_intelligence"]["top_hours"]
    assert packet["volatility_intelligence"]["top_hours"]
    assert packet["category_intelligence"]["count"] == 2
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    context = bridge.oracle_context()
    assert context["context_type"] == "market_rhythm"
    assert context["read_only"] is True
    assert context["execution_allowed"] is False
    assert context["summary"]

    print("[PASS] OI-022 Rhythm Insight Bridge")
    print({
        "rows_analyzed": packet["rows_analyzed"],
        "top_activity_hour": packet["market_clock"]["best_activity_hours"][0],
        "categories": [
            c["category"]
            for c in packet["category_intelligence"]["categories_ranked"]
        ],
    })


if __name__ == "__main__":
    test_oi_022_rhythm_insight_bridge()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .rhythm_insight_bridge import RhythmInsightBridge, oracle_rhythm_insight_bridge\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-022 INSTALLER")
print(" Rhythm Insight Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-022 installed")
print("")
print("Run:")
print("python test_oi_022_rhythm_insight_bridge.py")