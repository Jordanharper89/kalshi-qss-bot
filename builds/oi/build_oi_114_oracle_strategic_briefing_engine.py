from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_strategic_briefing_engine.py"
TEST = ROOT / "test_oi_114_oracle_strategic_briefing_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-114 Oracle Strategic Briefing Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle executive intelligence into strategic briefing output.
- Produce strategic posture, key themes, focus lanes, executive risk notes,
  and downstream dashboard-ready briefing cards.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleStrategicBriefingEngine:
    module = "oi_114_oracle_strategic_briefing_engine"

    def __init__(self):
        self.last_briefing = {}

    def build_strategic_briefing(self, executive_packet=None, digest_report=None, stability_index=None):
        executive_packet = executive_packet or {}
        digest_report = digest_report or {}
        stability_index = stability_index or {}

        priorities = [x for x in executive_packet.get("top_priorities", []) if isinstance(x, dict)]
        risks = [x for x in executive_packet.get("top_risks", []) if isinstance(x, dict)]
        themes = [str(x) for x in executive_packet.get("themes", [])]
        digest_items = [x for x in digest_report.get("digest_items", []) if isinstance(x, dict)]

        strategic_score = self._strategic_score(executive_packet, digest_report, stability_index)
        posture = self._posture(strategic_score, executive_packet, stability_index)

        lanes = self._build_lanes(priorities, risks, digest_items)
        briefing_cards = self._build_cards(lanes, posture)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_113_oracle_executive_intelligence_engine",
                "oi_112_oracle_digest_engine",
                "oi_094_global_market_stability_engine",
            ],
            "strategic_score": round(strategic_score, 4),
            "strategic_posture": posture,
            "briefing_title": self._title(posture, strategic_score),
            "strategic_themes": themes[:7],
            "priority_count": len(priorities),
            "risk_count": len(risks),
            "lane_count": len(lanes),
            "strategic_lanes": lanes,
            "briefing_cards": briefing_cards,
            "executive_notes": self._executive_notes(posture, themes, priorities, risks),
            "recommended_oracle_focus": self._focus(posture, priorities, risks),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "strategic_context_only",
            },
        }

        self.last_briefing = report
        return report

    def _strategic_score(self, executive_packet, digest_report, stability_index):
        executive_score = self._float(executive_packet.get("executive_score"), 70)
        urgent_count = self._float(
            digest_report.get("executive_summary", {}).get("urgent_count"),
            0,
        )
        stability_score = self._float(stability_index.get("global_stability_score"), 65)

        risk_drag = max(0, 70 - stability_score) * 0.25
        urgency_lift = min(urgent_count * 4, 16)

        score = executive_score + urgency_lift - risk_drag
        return max(0.0, min(100.0, score))

    def _posture(self, score, executive_packet, stability_index):
        executive_posture = str(executive_packet.get("executive_posture") or "")
        global_tier = str(stability_index.get("global_stability_tier") or "")

        if executive_posture == "defensive" or global_tier in {"critical", "fragile"}:
            return "strategic_defense"
        if executive_posture == "cautious" or score < 60:
            return "selective_review"
        if score >= 82:
            return "priority_expansion_review"
        return "balanced_strategy_review"

    def _build_lanes(self, priorities, risks, digest_items):
        lanes = []

        for item in priorities[:5]:
            lanes.append({
                "lane": "priority",
                "label": str(item.get("label") or "unnamed_priority"),
                "score": round(self._float(item.get("priority")), 4),
                "briefing_action": "Review priority intelligence before Q Series execution evaluation.",
                "read_only": True,
                "execution_allowed": False,
            })

        for item in risks[:5]:
            lanes.append({
                "lane": "risk",
                "label": str(item.get("label") or "unnamed_risk"),
                "score": round(self._float(item.get("severity")), 4),
                "briefing_action": "Review risk driver before exposure expansion.",
                "read_only": True,
                "execution_allowed": False,
            })

        for item in digest_items[:5]:
            lanes.append({
                "lane": "digest",
                "label": str(item.get("market") or item.get("label") or "unnamed_digest"),
                "score": round(self._float(item.get("digest_score")), 4),
                "briefing_action": "Compare digest rank against executive posture.",
                "read_only": True,
                "execution_allowed": False,
            })

        lanes.sort(key=lambda x: x["score"], reverse=True)

        for idx, lane in enumerate(lanes, start=1):
            lane["strategic_rank"] = idx

        return lanes

    def _build_cards(self, lanes, posture):
        cards = []
        for lane in lanes[:10]:
            cards.append({
                "title": f"{lane['label']} strategic briefing",
                "lane": lane["lane"],
                "rank": lane["strategic_rank"],
                "score": lane["score"],
                "posture": posture,
                "summary": (
                    f"{lane['label']} is ranked #{lane['strategic_rank']} in the "
                    f"{lane['lane']} lane under {posture} posture."
                ),
                "execution_allowed": False,
                "read_only": True,
            })
        return cards

    def _title(self, posture, score):
        return f"Oracle strategic briefing: {posture} with score {round(score, 2)}"

    def _executive_notes(self, posture, themes, priorities, risks):
        notes = []

        if themes:
            notes.append(f"Dominant theme: {themes[0]}")
        else:
            notes.append("No dominant strategic theme detected.")

        if priorities:
            notes.append(f"Top priority lane: {priorities[0].get('label')}")
        else:
            notes.append("No priority lane requires executive escalation.")

        if risks:
            notes.append(f"Top risk lane: {risks[0].get('label')}")
        else:
            notes.append("No major risk lane is currently elevated.")

        notes.append(f"Strategic posture: {posture}")
        notes.append("Oracle remains read-only; execution remains with Q Series.")
        return notes

    def _focus(self, posture, priorities, risks):
        focus = []

        if posture == "strategic_defense":
            focus.extend([
                "Reduce attention to expansion lanes until risk posture improves",
                "Review fragility, contagion, and anomaly reports first",
            ])
        elif posture == "selective_review":
            focus.extend([
                "Focus only on the highest-confidence intelligence lanes",
                "Require confirmation from decision support packets",
            ])
        elif posture == "priority_expansion_review":
            focus.extend([
                "Review top priority markets for Q Series decision evaluation",
                "Compare strategic lanes against executive digest rankings",
            ])
        else:
            focus.extend([
                "Maintain balanced review across priority and risk lanes",
                "Monitor top digest-ranked markets for posture changes",
            ])

        if priorities:
            focus.append(f"Primary priority focus: {priorities[0].get('label')}")
        if risks:
            focus.append(f"Primary risk focus: {risks[0].get('label')}")

        focus.append("Do not execute from Oracle; route execution context to Q Series only")
        return focus

    def _float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_briefing": bool(self.last_briefing),
            "lane_count": self.last_briefing.get("lane_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_strategic_briefing_engine = OracleStrategicBriefingEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_strategic_briefing_engine import oracle_strategic_briefing_engine


def test_oi_114_oracle_strategic_briefing_engine():
    executive_packet = {
        "executive_score": 81,
        "executive_posture": "balanced_review",
        "themes": ["Cross-market pressure building"],
        "top_priorities": [
            {"label": "Election market volatility", "priority": 91},
            {"label": "Macro rate path", "priority": 76},
        ],
        "top_risks": [
            {"label": "Liquidity fragility", "severity": 68},
            {"label": "Contagion risk", "severity": 61},
        ],
    }

    digest = {
        "digest_items": [
            {"market": "CRYPTO", "digest_score": 88, "digest_tier": "critical"},
            {"market": "NASDAQ", "digest_score": 74, "digest_tier": "high"},
        ],
        "executive_summary": {
            "urgent_count": 2,
            "summary_tone": "urgent_oracle_attention",
        },
    }

    stability = {
        "global_stability_score": 66,
        "global_stability_tier": "mixed",
        "risk_posture": "heightened_monitoring",
    }

    report = oracle_strategic_briefing_engine.build_strategic_briefing(
        executive_packet,
        digest,
        stability,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["strategic_score"] > 0
    assert report["strategic_posture"] in {
        "strategic_defense",
        "selective_review",
        "priority_expansion_review",
        "balanced_strategy_review",
    }
    assert report["priority_count"] == 2
    assert report["risk_count"] == 2
    assert report["lane_count"] >= 4
    assert report["strategic_lanes"][0]["strategic_rank"] == 1
    assert report["briefing_cards"]
    assert report["briefing_cards"][0]["execution_allowed"] is False
    assert "Oracle remains read-only" in report["executive_notes"][-1]

    diag = oracle_strategic_briefing_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["lane_count"] == report["lane_count"]

    print("[PASS] OI-114 Oracle Strategic Briefing Engine")
    print({
        "strategic_score": report["strategic_score"],
        "strategic_posture": report["strategic_posture"],
        "lane_count": report["lane_count"],
        "top_lane": report["strategic_lanes"][0],
    })


if __name__ == "__main__":
    test_oi_114_oracle_strategic_briefing_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_strategic_briefing_engine import oracle_strategic_briefing_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-114 INSTALLER")
print(" Oracle Strategic Briefing Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-114 installed")
print()
print("Run:")
print("py test_oi_114_oracle_strategic_briefing_engine.py")