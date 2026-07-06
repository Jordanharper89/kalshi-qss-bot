import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.play_model import Play


class OracleAPI:
    def get_alpha_plays(self, limit=10):
        plays = []
        try:
            import oracle_cross_market_arbitrage as arb
            d = arb.diagnostics()
            for item in (d.get("top") or [])[:limit]:
                edge_pct = float(item.get("edge_pct") or 0)
                confidence = float(item.get("confidence") or 0)
                kind = str(item.get("kind") or "alpha")

                plays.append(Play(
                    ticker=f"ORACLE-{kind.upper()}",
                    title=kind.replace("_", " ").title(),
                    category="ORACLE",
                    play_type="ALPHA",
                    mission="WATCH",
                    side="WATCH",
                    edge=edge_pct,
                    confidence=confidence,
                    grade=self._grade(edge_pct, confidence),
                    reason=item.get("recommendation") or "",
                ).to_dict())
        except Exception as e:
            plays.append(Play(
                ticker="ORACLE-ERROR",
                title="Oracle Alpha Error",
                mission="IGNORE",
                reason=str(e),
            ).to_dict())
        return plays

    def get_live_plays(self, category="all", limit=10):
        if category in ("oracle", "all"):
            return self.get_alpha_plays(limit=limit)

        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "category_scan.py", category],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=240,
                errors="replace",
            )
            text = (result.stdout or result.stderr or "").strip()
            return [Play(
                ticker=f"{category.upper()}-SCAN",
                title=f"{category.title()} Scan Output",
                category=category.upper(),
                mission="REVIEW",
                reason=text[:2500] if text else "No output.",
            ).to_dict()]
        except Exception as e:
            return [Play(
                ticker=f"{category.upper()}-ERROR",
                title=f"{category.title()} Scan Error",
                category=category.upper(),
                mission="IGNORE",
                reason=str(e),
            ).to_dict()]

    def get_snapshot(self):
        try:
            import oracle_continuous_intelligence as o
            o.run_cycle()
            s = o.status()
            return {
                "status": "ok",
                "market_regime": s.get("market_regime"),
                "final_decision_status": s.get("final_decision_status"),
                "data_quality": s.get("data_quality_planner_status", {}).get("status"),
                "ranked_count": len(s.get("last_ranked") or []),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _grade(self, edge, confidence):
        score = edge + confidence / 10
        if score >= 30:
            return "A+"
        if score >= 20:
            return "A"
        if score >= 12:
            return "B"
        return "WATCH"


oracle_api = OracleAPI()
