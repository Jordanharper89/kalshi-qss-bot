from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_digest_engine.py"
TEST = ROOT / "test_oi_112_oracle_digest_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-112 Oracle Digest Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert Oracle briefing packets into a clean read-only digest.
- Produce top risks, urgent briefings, market watch groups, and executive summary.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class OracleDigestEngine:
    module = "oi_112_oracle_digest_engine"

    def __init__(self):
        self.last_digest = {}

    def build_digest(self, briefing_report=None, stability_index=None, risk_posture_report=None):
        briefing_report = briefing_report or {}
        stability_index = stability_index or {}
        risk_posture_report = risk_posture_report or {}

        briefings = [x for x in briefing_report.get("briefing_packets", []) if isinstance(x, dict)]
        postures = self._index(risk_posture_report.get("postures", []), "market")

        digest_items = []
        for item in briefings:
            market = str(item.get("market") or "UNKNOWN")
            posture = postures.get(market, {})

            briefing_score = self._float(item.get("briefing_score"))
            posture_score = self._float(posture.get("risk_posture_score"), 50)
            health_score = self._float(item.get("health_score"), 50)
            alert_count = int(self._float(item.get("alert_count"), 0))

            digest_score = self._digest_score(
                briefing_score=briefing_score,
                posture_score=posture_score,
                health_score=health_score,
                alert_count=alert_count,
            )

            digest_items.append({
                "market": market,
                "digest_score": round(digest_score, 4),
                "digest_tier": self._tier(digest_score),
                "briefing_tier": item.get("briefing_tier"),
                "briefing_score": round(briefing_score, 4),
                "risk_posture_score": round(posture_score, 4),
                "health_score": round(health_score, 4),
                "alert_count": alert_count,
                "headline": self._headline(market, digest_score, item),
                "digest_summary": self._summary_text(market, item, posture),
                "oracle_observation": item.get("oracle_observation"),
                "execution_allowed": False,
                "read_only": True,
            })

        digest_items.sort(key=lambda x: x["digest_score"], reverse=True)

        for idx, item in enumerate(digest_items, start=1):
            item["digest_rank"] = idx

        digest = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_111_oracle_briefing_packet_engine",
                "oi_094_global_market_stability_engine",
                "oi_102_risk_posture_synthesis_engine",
            ],
            "digest_count": len(digest_items),
            "global_stability_score": stability_index.get("global_stability_score"),
            "global_stability_tier": stability_index.get("global_stability_tier"),
            "risk_posture": stability_index.get("risk_posture"),
            "digest_items": digest_items,
            "urgent_digest": [x for x in digest_items if x["digest_tier"] in {"critical", "high"}],
            "watch_digest": [x for x in digest_items if x["digest_tier"] in {"elevated", "watch"}],
            "executive_summary": self._executive_summary(digest_items, stability_index),
        }

        self.last_digest = digest
        return digest

    def _digest_score(self, briefing_score, posture_score, health_score, alert_count):
        score = (
            briefing_score * 0.45
            + posture_score * 0.25
            + (100 - health_score) * 0.18
            + min(alert_count * 8, 20)
        )
        return max(0.0, min(100.0, score))

    def _tier(self, score):
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "elevated"
        if score >= 30:
            return "watch"
        return "normal"

    def _headline(self, market, score, item):
        return f"{market} Oracle digest: {self._tier(score)} attention, briefing {item.get('briefing_tier')}"

    def _summary_text(self, market, briefing, posture):
        return (
            f"{market} digest combines briefing tier {briefing.get('briefing_tier')}, "
            f"support tier {briefing.get('support_tier')}, posture {posture.get('posture')}, "
            f"and top alert priority {briefing.get('top_alert_priority')}."
        )

    def _executive_summary(self, items, stability_index):
        counts = {}
        for item in items:
            tier = item["digest_tier"]
            counts[tier] = counts.get(tier, 0) + 1

        top = items[0] if items else None
        urgent_count = len([x for x in items if x["digest_tier"] in {"critical", "high"}])

        if urgent_count:
            tone = "urgent_oracle_attention"
        elif counts.get("elevated", 0):
            tone = "heightened_oracle_monitoring"
        else:
            tone = "normal_oracle_digest"

        return {
            "digest_tier_counts": counts,
            "top_market": top["market"] if top else None,
            "top_digest_tier": top["digest_tier"] if top else None,
            "urgent_count": urgent_count,
            "summary_tone": tone,
            "global_stability_score": stability_index.get("global_stability_score"),
            "risk_posture": stability_index.get("risk_posture"),
            "execution_allowed": False,
        }

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = str(row.get(key) or "").strip()
                if value:
                    out[value] = row
        return out

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
            "has_digest": bool(self.last_digest),
            "digest_count": self.last_digest.get("digest_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


oracle_digest_engine = OracleDigestEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_digest_engine import oracle_digest_engine


def test_oi_112_oracle_digest_engine():
    briefing = {
        "briefing_packets": [
            {
                "market": "CRYPTO",
                "briefing_score": 92,
                "briefing_tier": "critical",
                "support_tier": "critical",
                "health_score": 24,
                "alert_count": 1,
                "top_alert_priority": "critical",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
            },
            {
                "market": "NASDAQ",
                "briefing_score": 74,
                "briefing_tier": "high",
                "support_tier": "high",
                "health_score": 32,
                "alert_count": 1,
                "top_alert_priority": "high",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
            },
        ]
    }

    stability = {
        "global_stability_score": 62.6,
        "global_stability_tier": "mixed",
        "risk_posture": "heightened_monitoring",
    }

    posture = {
        "postures": [
            {"market": "CRYPTO", "risk_posture_score": 90, "posture": "systemic_alert"},
            {"market": "NASDAQ", "risk_posture_score": 62.9, "posture": "heightened_monitoring"},
        ]
    }

    report = oracle_digest_engine.build_digest(briefing, stability, posture)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["digest_count"] == 2
    assert report["digest_items"][0]["digest_rank"] == 1
    assert report["digest_items"][0]["digest_score"] >= report["digest_items"][-1]["digest_score"]
    assert report["executive_summary"]["execution_allowed"] is False

    diag = oracle_digest_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-112 Oracle Digest Engine")
    print({
        "digest_count": report["digest_count"],
        "summary": report["executive_summary"],
        "top": report["digest_items"][0],
    })


if __name__ == "__main__":
    test_oi_112_oracle_digest_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_digest_engine import oracle_digest_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-112 INSTALLER")
print(" Oracle Digest Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-112 installed")
print()
print("Run:")
print("py test_oi_112_oracle_digest_engine.py")