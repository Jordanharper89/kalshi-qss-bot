from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
ENGINE = ROOT / "oracle_market_microstructure.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

ENGINE_CODE = r'''
"""
ORACLE-048 Market Microstructure Engine

Purpose:
- Analyze market tradability underneath Oracle score.
- Detect spread quality, liquidity weakness, price stability, and execution risk.
- Does NOT place trades.
"""

from datetime import datetime, UTC


def _num(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _txt(value):
    return str(value or "").strip()


class OracleMarketMicrostructureEngine:
    def __init__(self):
        self.version = "ORACLE-048"

    def analyze(self, opportunity):
        if not isinstance(opportunity, dict):
            return self._result(
                status="error",
                tradability="UNTRADABLE",
                score=0,
                reason="Invalid opportunity object",
                opportunity={},
            )

        raw = opportunity.get("raw") if isinstance(opportunity.get("raw"), dict) else {}
        raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}

        markets = raw_raw.get("markets") or raw.get("markets") or []
        if not isinstance(markets, list):
            markets = []

        warnings = opportunity.get("warnings") or []
        if not isinstance(warnings, list):
            warnings = [str(warnings)]

        volume = _num(opportunity.get("volume") or raw.get("volume") or raw_raw.get("volume"), 0)
        market_price = _num(opportunity.get("market_price") or raw.get("market_price"), 0)
        edge = abs(_num(opportunity.get("edge") or raw.get("edge") or raw_raw.get("edge"), 0))
        confidence = _num(opportunity.get("confidence") or raw.get("confidence") or raw_raw.get("confidence"), 0)

        spread_values = []
        yes_mid_values = []

        for m in markets:
            if not isinstance(m, dict):
                continue
            if "spread" in m:
                spread_values.append(abs(_num(m.get("spread"), 0)))
            if "yes_mid" in m:
                yes_mid_values.append(_num(m.get("yes_mid"), 0))

        avg_spread = sum(spread_values) / len(spread_values) if spread_values else None
        max_spread = max(spread_values) if spread_values else None
        min_spread = min(spread_values) if spread_values else None

        avg_yes_mid = sum(yes_mid_values) / len(yes_mid_values) if yes_mid_values else None

        score = 100.0
        strengths = []
        risks = []
        blockers = []

        if avg_spread is None:
            score -= 18
            risks.append("No order-book spread data available")
        else:
            if avg_spread <= 0.02:
                strengths.append("Tight average spread")
                score += 4
            elif avg_spread <= 0.06:
                strengths.append("Acceptable average spread")
            elif avg_spread <= 0.12:
                score -= 16
                risks.append(f"Wide average spread: {avg_spread:.3f}")
            else:
                score -= 28
                risks.append(f"Very wide average spread: {avg_spread:.3f}")
                blockers.append("Spread too wide for clean execution")

        if max_spread is not None and max_spread >= 0.15:
            score -= 12
            risks.append(f"One or more legs have very wide spread: {max_spread:.3f}")

        if volume <= 0:
            score -= 22
            risks.append("No volume detected")
        elif volume < 100:
            score -= 14
            risks.append(f"Low volume: {volume:.0f}")
        elif volume < 500:
            score -= 6
            risks.append(f"Moderate-low volume: {volume:.0f}")
        else:
            strengths.append(f"Volume present: {volume:.0f}")

        if any("liquidity" in str(w).lower() for w in warnings):
            score -= 18
            risks.append("Existing Oracle warning: liquidity may be weak")

        if any("edge is not strong" in str(w).lower() for w in warnings):
            score -= 8
            risks.append("Existing Oracle warning: edge is not strong enough yet")

        if edge <= 0:
            score -= 20
            blockers.append("No measurable edge")
        elif edge < 0.03:
            score -= 10
            risks.append("Very small edge")
        elif edge >= 0.15:
            strengths.append("Large theoretical edge detected")

        if confidence >= 85:
            strengths.append("High upstream confidence")
            score += 3
        elif confidence < 55:
            score -= 10
            risks.append("Low upstream confidence")

        if len(markets) >= 2:
            strengths.append(f"Multi-leg structure detected: {len(markets)} markets")
            score -= min(12, max(0, len(markets) - 2) * 2)
            if len(markets) > 5:
                risks.append("Many-leg basket increases execution complexity")

        score = max(0.0, min(100.0, score))

        if blockers:
            tradability = "UNTRADABLE"
        elif score >= 78:
            tradability = "GOOD"
        elif score >= 62:
            tradability = "CAUTION"
        elif score >= 45:
            tradability = "POOR"
        else:
            tradability = "UNTRADABLE"

        reason = self._reason(tradability, score, strengths, risks, blockers)

        return self._result(
            status="ok",
            tradability=tradability,
            score=round(score, 2),
            reason=reason,
            opportunity=opportunity,
            strengths=strengths,
            risks=risks,
            blockers=blockers,
            metrics={
                "avg_spread": avg_spread,
                "max_spread": max_spread,
                "min_spread": min_spread,
                "avg_yes_mid": avg_yes_mid,
                "legs": len(markets),
                "volume": volume,
                "market_price": market_price,
                "edge": edge,
                "confidence": confidence,
            },
        )

    def _reason(self, tradability, score, strengths, risks, blockers):
        parts = [f"Tradability {tradability} with microstructure score {score:.2f}."]

        if blockers:
            parts.append("Blockers: " + "; ".join(blockers[:3]))

        if risks:
            parts.append("Risks: " + "; ".join(risks[:4]))

        if strengths:
            parts.append("Strengths: " + "; ".join(strengths[:4]))

        return " ".join(parts)

    def _result(self, status, tradability, score, reason, opportunity, strengths=None, risks=None, blockers=None, metrics=None):
        return {
            "module": "oracle_market_microstructure",
            "version": self.version,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "ticker": opportunity.get("ticker") if isinstance(opportunity, dict) else None,
            "title": opportunity.get("title") if isinstance(opportunity, dict) else None,
            "tradability": tradability,
            "microstructure_score": score,
            "score": score,
            "reason": reason,
            "strengths": strengths or [],
            "risks": risks or [],
            "blockers": blockers or [],
            "metrics": metrics or {},
            "compact_card": self._card(opportunity, tradability, score, reason, strengths or [], risks or [], blockers or []),
        }

    def _card(self, opportunity, tradability, score, reason, strengths, risks, blockers):
        opportunity = opportunity if isinstance(opportunity, dict) else {}
        lines = [
            "📊 ORACLE MICROSTRUCTURE",
            f"Ticker: {opportunity.get('ticker', 'UNKNOWN')}",
            f"Market: {opportunity.get('title', 'Untitled opportunity')}",
            "",
            f"Tradability: {tradability}",
            f"Score: {score}",
            f"Reason: {reason}",
        ]

        if blockers:
            lines.append("")
            lines.append("Blockers:")
            for b in blockers:
                lines.append(f"- {b}")

        if risks:
            lines.append("")
            lines.append("Risks:")
            for r in risks[:5]:
                lines.append(f"- {r}")

        if strengths:
            lines.append("")
            lines.append("Strengths:")
            for s in strengths[:5]:
                lines.append(f"- {s}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_market_microstructure",
            "version": self.version,
            "status": "ok",
            "outputs": ["tradability", "microstructure_score", "risks", "blockers", "compact_card"],
        }


oracle_market_microstructure = OracleMarketMicrostructureEngine()


if __name__ == "__main__":
    sample = {
        "ticker": "TEST",
        "title": "Sample microstructure opportunity",
        "edge": 0.12,
        "confidence": 90,
        "warnings": ["Liquidity may be weak"],
        "raw": {
            "raw": {
                "markets": [
                    {"ticker": "A", "spread": 0.04, "yes_mid": 0.33},
                    {"ticker": "B", "spread": 0.05, "yes_mid": 0.12},
                ]
            }
        },
    }

    result = oracle_market_microstructure.analyze(sample)
    print(result["compact_card"])
    print(result)
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-048 Market Microstructure Integration
# ============================================================

try:
    from oracle_market_microstructure import oracle_market_microstructure
except Exception:
    oracle_market_microstructure = None


def _oracle048_apply_microstructure(ranked):
    if oracle_market_microstructure is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            micro = oracle_market_microstructure.analyze(item)
            item["microstructure"] = micro
            item["tradability"] = micro.get("tradability")
            item["microstructure_score"] = micro.get("microstructure_score")
            item["microstructure_risks"] = micro.get("risks", [])
            item["microstructure_blockers"] = micro.get("blockers", [])
            item["microstructure_card"] = micro.get("compact_card")
        except Exception as exc:
            item["microstructure"] = {
                "status": "error",
                "tradability": "UNTRADABLE",
                "reason": str(exc),
            }
            item["tradability"] = "UNTRADABLE"
            item["microstructure_score"] = 0

        enriched.append(item)

    tradability_rank = {
        "GOOD": 4,
        "CAUTION": 3,
        "POOR": 2,
        "UNTRADABLE": 1,
    }

    enriched.sort(
        key=lambda x: (
            tradability_rank.get(x.get("tradability"), 0),
            x.get("execution_decision") == "EXECUTE",
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, False, 0),
        reverse=True,
    )

    return enriched


def _oracle048_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle048_apply_microstructure(_state["last_ranked"])

            ranked = _state.get("last_ranked") or []
            counts = {}
            for item in ranked:
                if isinstance(item, dict):
                    t = item.get("tradability", "UNKNOWN")
                    counts[t] = counts.get(t, 0) + 1

            _state["microstructure_status"] = {
                "status": "ok" if oracle_market_microstructure is not None else "missing",
                "tradability_counts": counts,
                "top": ranked[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["microstructure_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle048_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle048_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle048_original_run_cycle(*args, **kwargs)
        _oracle048_enrich_state()
        return result


if "_oracle048_original_status" not in globals() and "status" in globals():
    _oracle048_original_status = status

    def status(*args, **kwargs):
        result = _oracle048_original_status(*args, **kwargs)
        _oracle048_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle048_apply_microstructure(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle048_apply_microstructure(ps["last_ranked"])

            result["microstructure_status"] = (
                globals().get("_state", {}).get("microstructure_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )

        return result

# ============================================================
# END ORACLE-048
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle048_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-048 INSTALLER")
    print(" Market Microstructure Engine")
    print("===================================")

    backup(ENGINE)
    ENGINE.write_text(ENGINE_CODE, encoding="utf-8")
    print("[OK] Created oracle_market_microstructure.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-048 Market Microstructure Integration" in text:
            print("[SKIP] Continuous Intelligence already patched")
        else:
            b = backup(CONTINUOUS)
            marker = 'if __name__ == "__main__":'
            if marker in text:
                text = text.replace(marker, PATCH_BLOCK + "\n\n" + marker, 1)
            else:
                text += "\n\n" + PATCH_BLOCK + "\n"
            CONTINUOUS.write_text(text, encoding="utf-8")
            print("[OK] Patched oracle_continuous_intelligence.py")
            print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_market_microstructure.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('microstructure_status')); print(s.get('last_ranked',[{}])[0].get('microstructure_card'))\"")
    print("")
    print("[DONE] ORACLE-048 Market Microstructure Engine installed")


if __name__ == "__main__":
    main()