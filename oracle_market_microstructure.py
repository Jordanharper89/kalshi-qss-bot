
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




# ============================================================
# ORACLE-083 Microstructure Auto Mapper
# ============================================================

def _oracle083_pick_field(d, names):
    if not isinstance(d, dict):
        return None
    lowered = {str(k).lower(): k for k in d.keys()}
    for n in names:
        if n in d:
            return d.get(n)
        lk = str(n).lower()
        if lk in lowered:
            return d.get(lowered[lk])
    for k, v in d.items():
        kl = str(k).lower()
        if any(str(n).lower() in kl for n in names):
            return v
    return None


ORACLE083_FIELD_MAP = {
    "yes_bid": ["yes_bid", "bid", "best_bid", "bid_price"],
    "yes_ask": ["yes_ask", "ask", "best_ask", "ask_price"],
    "yes_mid": ["yes_mid", "mid", "mid_price", "mark_price"],
    "spread": ["spread", "bid_ask_spread"],
    "bid_depth": ["bid_depth", "yes_bid_depth", "bid_size", "yes_bid_size", "bids_depth"],
    "ask_depth": ["ask_depth", "yes_ask_depth", "ask_size", "yes_ask_size", "asks_depth"],
    "volume": ["volume", "volume_24h", "open_interest", "liquidity"],
}


if "OracleMarketMicrostructureEngine" in globals():
    if "_oracle083_original_analyze" not in globals():
        _oracle083_original_analyze = OracleMarketMicrostructureEngine.analyze

        def _oracle083_analyze(self, opportunity):
            if isinstance(opportunity, dict):
                raw = opportunity.get("raw") if isinstance(opportunity.get("raw"), dict) else {}
                raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}
                markets = raw_raw.get("markets") or raw.get("markets") or []

                if isinstance(markets, list):
                    mapped = []

                    for m in markets:
                        if not isinstance(m, dict):
                            mapped.append(m)
                            continue

                        mm = dict(m)
                        notes = []

                        for target, names in ORACLE083_FIELD_MAP.items():
                            if target not in mm or mm.get(target) in (None, ""):
                                val = _oracle083_pick_field(mm, names)
                                if val not in (None, ""):
                                    mm[target] = val
                                    notes.append(f"{target}<-mapped")

                        bid = _oracle083_pick_field(mm, ["yes_bid", "bid", "best_bid", "bid_price"])
                        ask = _oracle083_pick_field(mm, ["yes_ask", "ask", "best_ask", "ask_price"])

                        try:
                            if bid not in (None, "") and ask not in (None, ""):
                                bid_f = float(bid)
                                ask_f = float(ask)

                                if "spread" not in mm or mm.get("spread") in (None, ""):
                                    mm["spread"] = abs(ask_f - bid_f)
                                    notes.append("spread<-derived_bid_ask")

                                if "yes_mid" not in mm or mm.get("yes_mid") in (None, ""):
                                    mm["yes_mid"] = (ask_f + bid_f) / 2.0
                                    notes.append("yes_mid<-derived_bid_ask")
                        except Exception:
                            pass

                        # Promote total visible depth if available
                        try:
                            bd = _oracle083_pick_field(mm, ORACLE083_FIELD_MAP["bid_depth"])
                            ad = _oracle083_pick_field(mm, ORACLE083_FIELD_MAP["ask_depth"])
                            if bd not in (None, "") and ad not in (None, ""):
                                mm["total_depth"] = float(bd) + float(ad)
                                notes.append("total_depth<-derived")
                        except Exception:
                            pass

                        if notes:
                            mm["oracle083_mapper_notes"] = notes

                        mapped.append(mm)

                    opportunity = dict(opportunity)
                    opportunity["raw"] = dict(raw)

                    if isinstance(raw_raw, dict) and raw_raw:
                        opportunity["raw"]["raw"] = dict(raw_raw)
                        opportunity["raw"]["raw"]["markets"] = mapped
                    else:
                        opportunity["raw"]["markets"] = mapped

            result = _oracle083_original_analyze(self, opportunity)

            if isinstance(result, dict):
                result["auto_mapper"] = {
                    "version": "ORACLE-083",
                    "status": "applied",
                    "field_map": ORACLE083_FIELD_MAP,
                }
                result["version"] = "ORACLE-048+083"

            return result

        OracleMarketMicrostructureEngine.analyze = _oracle083_analyze

# ============================================================
# END ORACLE-083
# ============================================================


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
