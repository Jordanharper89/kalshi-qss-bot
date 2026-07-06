from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "market_stability_alert_engine.py"
TEST = ROOT / "test_oi_095_market_stability_alert_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r"""
\"\"\"
OI-095 Market Stability Alert Engine

Read-only Oracle Intelligence module.

Purpose:
- Convert OI-094 global market stability output into clean Oracle alert cards.
- Detect unstable markets, improving markets, systemic alert posture, and watchlist priority.
- Produce alert-ready summaries without execution instructions.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
\"\"\"

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import math
import time


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(value)))


@dataclass
class StabilityAlert:
    alert_id: str
    alert_type: str
    market: str
    priority: str
    severity_score: float
    title: str
    summary: str
    evidence: Dict[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketStabilityAlertEngine:
    module = "oi_095_market_stability_alert_engine"

    def __init__(self) -> None:
        self.last_alerts: Dict[str, Any] = {}

    def build_alerts(
        self,
        stability_index: Optional[Dict[str, Any]] = None,
        previous_stability_index: Optional[Dict[str, Any]] = None,
        min_priority: str = "watch",
    ) -> Dict[str, Any]:
        stability_index = stability_index or {}
        previous_stability_index = previous_stability_index or {}

        current_scores = [x for x in stability_index.get("scores", []) if isinstance(x, dict)]
        previous_lookup = self._previous_lookup(previous_stability_index.get("scores", []))

        alerts: List[StabilityAlert] = []

        global_alert = self._global_alert(stability_index)
        if global_alert is not None:
            alerts.append(global_alert)

        for row in current_scores:
            market_alerts = self._market_alerts(row, previous_lookup.get(_safe_str(row.get("market"))))
            alerts.extend(market_alerts)

        priority_rank = {"critical": 5, "high": 4, "elevated": 3, "watch": 2, "info": 1}
        min_rank = priority_rank.get(min_priority, 2)

        filtered = [a for a in alerts if priority_rank.get(a.priority, 0) >= min_rank]
        filtered.sort(key=lambda a: (priority_rank.get(a.priority, 0), a.severity_score), reverse=True)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_module": "oi_094_global_market_stability_engine",
            "alert_count": len(filtered),
            "alerts": [a.to_dict() for a in filtered],
            "critical_alerts": [a.to_dict() for a in filtered if a.priority == "critical"],
            "high_alerts": [a.to_dict() for a in filtered if a.priority == "high"],
            "watch_alerts": [a.to_dict() for a in filtered if a.priority == "watch"],
            "summary": self._summary(stability_index, filtered),
        }

        self.last_alerts = report
        return report

    def _previous_lookup(self, rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out = {}
        for row in rows:
            if isinstance(row, dict):
                market = _safe_str(row.get("market")).strip()
                if market:
                    out[market] = row
        return out

    def _global_alert(self, index: Dict[str, Any]) -> Optional[StabilityAlert]:
        score = _safe_float(index.get("global_stability_score"))
        tier = _safe_str(index.get("global_stability_tier"))
        posture = _safe_str(index.get("risk_posture"))

        if score <= 25 or tier == "critical" or posture == "systemic_alert":
            priority = "critical"
            alert_type = "global_systemic_alert"
            title = "Global stability is critical"
        elif score <= 45 or tier == "unstable" or posture == "defensive_monitoring":
            priority = "high"
            alert_type = "global_instability_alert"
            title = "Global stability is unstable"
        elif score <= 65 or tier == "mixed" or posture == "heightened_monitoring":
            priority = "elevated"
            alert_type = "global_heightened_monitoring"
            title = "Global stability requires heightened monitoring"
        else:
            return None

        severity = _clamp(100 - score)

        return StabilityAlert(
            alert_id=f"global_{alert_type}",
            alert_type=alert_type,
            market="GLOBAL",
            priority=priority,
            severity_score=round(severity, 4),
            title=title,
            summary=f"Global market stability score is {round(score, 2)} with posture {posture}.",
            evidence={
                "global_stability_score": score,
                "global_stability_tier": tier,
                "risk_posture": posture,
            },
        )

    def _market_alerts(self, row: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> List[StabilityAlert]:
        market = _safe_str(row.get("market"), "UNKNOWN")
        stability = _safe_float(row.get("stability_score"))
        tier = _safe_str(row.get("stability_tier"))
        risk_pressure = _safe_float(row.get("risk_pressure_score"))
        recovery = _safe_float(row.get("recovery_support_score"))
        persistence = _safe_float(row.get("persistence_penalty"))

        alerts: List[StabilityAlert] = []

        if stability < 25 or tier == "critical":
            alerts.append(self._make_market_alert(
                alert_type="market_critical_stability",
                market=market,
                priority="critical",
                severity=_clamp(100 - stability + risk_pressure * 0.15),
                title=f"{market} stability is critical",
                summary=f"{market} has critical stability conditions with score {round(stability, 2)}.",
                evidence=row,
            ))
        elif stability < 45 or tier == "unstable":
            alerts.append(self._make_market_alert(
                alert_type="market_unstable",
                market=market,
                priority="high",
                severity=_clamp(100 - stability + risk_pressure * 0.10),
                title=f"{market} is unstable",
                summary=f"{market} is unstable with risk pressure {round(risk_pressure, 2)}.",
                evidence=row,
            ))
        elif stability < 65 or tier == "mixed":
            alerts.append(self._make_market_alert(
                alert_type="market_mixed_stability",
                market=market,
                priority="watch",
                severity=_clamp(100 - stability),
                title=f"{market} stability is mixed",
                summary=f"{market} has mixed stability and should remain on watch.",
                evidence=row,
            ))

        if risk_pressure >= 75 and persistence >= 65:
            alerts.append(self._make_market_alert(
                alert_type="persistent_risk_pressure",
                market=market,
                priority="high",
                severity=_clamp((risk_pressure + persistence) / 2.0),
                title=f"{market} has persistent risk pressure",
                summary=f"{market} has elevated risk pressure and persistent influence effects.",
                evidence=row,
            ))

        if recovery >= 70 and stability >= 55:
            alerts.append(self._make_market_alert(
                alert_type="recovery_support_improving",
                market=market,
                priority="info",
                severity=_clamp(recovery),
                title=f"{market} has recovery support",
                summary=f"{market} shows recovery support with resilience component {round(recovery, 2)}.",
                evidence=row,
            ))

        if previous is not None:
            previous_stability = _safe_float(previous.get("stability_score"))
            delta = stability - previous_stability
            if delta <= -12:
                alerts.append(self._make_market_alert(
                    alert_type="stability_deterioration",
                    market=market,
                    priority="high",
                    severity=_clamp(abs(delta) * 4.5),
                    title=f"{market} stability deteriorated",
                    summary=f"{market} stability fell by {round(abs(delta), 2)} points versus prior snapshot.",
                    evidence={**row, "previous_stability_score": previous_stability, "stability_delta": round(delta, 4)},
                ))
            elif delta >= 12:
                alerts.append(self._make_market_alert(
                    alert_type="stability_improvement",
                    market=market,
                    priority="info",
                    severity=_clamp(delta * 3.0),
                    title=f"{market} stability improved",
                    summary=f"{market} stability improved by {round(delta, 2)} points versus prior snapshot.",
                    evidence={**row, "previous_stability_score": previous_stability, "stability_delta": round(delta, 4)},
                ))

        return alerts

    def _make_market_alert(
        self,
        alert_type: str,
        market: str,
        priority: str,
        severity: float,
        title: str,
        summary: str,
        evidence: Dict[str, Any],
    ) -> StabilityAlert:
        return StabilityAlert(
            alert_id=f"{alert_type}_{market}".replace(" ", "_").lower(),
            alert_type=alert_type,
            market=market,
            priority=priority,
            severity_score=round(_clamp(severity), 4),
            title=title,
            summary=summary,
            evidence=dict(evidence),
        )

    def _summary(self, index: Dict[str, Any], alerts: List[StabilityAlert]) -> Dict[str, Any]:
        priority_counts: Dict[str, int] = {}
        for alert in alerts:
            priority_counts[alert.priority] = priority_counts.get(alert.priority, 0) + 1

        return {
            "global_stability_score": index.get("global_stability_score"),
            "global_stability_tier": index.get("global_stability_tier"),
            "risk_posture": index.get("risk_posture"),
            "priority_counts": priority_counts,
            "top_priority": alerts[0].priority if alerts else "none",
            "top_alert": alerts[0].title if alerts else None,
        }

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_alerts": bool(self.last_alerts),
            "alert_count": self.last_alerts.get("alert_count", 0),
            "read_only": True,
        }


market_stability_alert_engine = MarketStabilityAlertEngine()
""", encoding="utf-8")

# Cleanup defensive escaping if the text renderer preserved escaped docstring characters.
_engine_text = ENGINE.read_text(encoding="utf-8")
_engine_text = _engine_text.replace('\\"""', '"""')
_engine_text = _engine_text.replace('"""', '"""')
ENGINE.write_text(_engine_text, encoding="utf-8")

TEST.write_text(r"""
from qseries_v2.oracle_intelligence.market_stability_alert_engine import market_stability_alert_engine


def test_oi_095_market_stability_alert_engine():
    stability_index = {
        "global_stability_score": 42.5,
        "global_stability_tier": "unstable",
        "risk_posture": "defensive_monitoring",
        "scores": [
            {
                "market": "NASDAQ",
                "stability_score": 30.0,
                "stability_tier": "unstable",
                "risk_pressure_score": 82.0,
                "recovery_support_score": 35.0,
                "persistence_penalty": 75.0,
                "reasons": ["Risk pressure is elevated."],
            },
            {
                "market": "FED-RATE",
                "stability_score": 72.0,
                "stability_tier": "constructive",
                "risk_pressure_score": 35.0,
                "recovery_support_score": 78.0,
                "persistence_penalty": 30.0,
                "reasons": ["Recovery support is strong."],
            },
        ],
    }

    previous = {
        "scores": [
            {"market": "NASDAQ", "stability_score": 48.0},
            {"market": "FED-RATE", "stability_score": 60.0},
        ]
    }

    report = market_stability_alert_engine.build_alerts(stability_index, previous)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["alert_count"] >= 3
    assert report["alerts"][0]["priority"] in {"critical", "high", "elevated", "watch"}
    assert any(a["market"] == "GLOBAL" for a in report["alerts"])
    assert any(a["alert_type"] == "stability_deterioration" for a in report["alerts"])
    assert report["summary"]["top_priority"] in {"critical", "high", "elevated", "watch"}

    diag = market_stability_alert_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-095 Market Stability Alert Engine")
    print({
        "alerts": report["alert_count"],
        "summary": report["summary"],
        "top_alert": report["alerts"][0],
    })


if __name__ == "__main__":
    test_oi_095_market_stability_alert_engine()
""", encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .market_stability_alert_engine import market_stability_alert_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-095 INSTALLER")
print(" Market Stability Alert Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-095 installed")
print()
print("Run:")
print("python test_oi_095_market_stability_alert_engine.py")
