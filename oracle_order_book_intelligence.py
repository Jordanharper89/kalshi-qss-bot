
"""
ORACLE-049 Live Order Book Intelligence

Purpose:
- Estimate execution quality from order-book style fields.
- Calculate spread cost, slippage estimate, fill probability,
  execution cost, best execution size, and tradable edge.
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


class OracleOrderBookIntelligence:
    def __init__(self):
        self.version = "ORACLE-049"

    def analyze(self, opportunity):
        if not isinstance(opportunity, dict):
            return self._result("error", "UNUSABLE", 0, "Invalid opportunity object", {})

        raw = opportunity.get("raw") if isinstance(opportunity.get("raw"), dict) else {}
        raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}
        markets = raw_raw.get("markets") or raw.get("markets") or []

        if not isinstance(markets, list):
            markets = []

        edge = abs(_num(opportunity.get("edge") or raw.get("edge") or raw_raw.get("edge"), 0))
        confidence = _num(opportunity.get("confidence") or raw.get("confidence") or raw_raw.get("confidence"), 0)
        volume = _num(opportunity.get("volume") or raw.get("volume") or raw_raw.get("volume"), 0)

        leg_reports = []
        total_spread_cost = 0.0
        total_slippage = 0.0
        total_depth = 0.0
        usable_legs = 0

        for m in markets:
            if not isinstance(m, dict):
                continue

            yes_mid = _num(m.get("yes_mid"), 0)
            spread = abs(_num(m.get("spread"), 0))

            bid_depth = _num(
                m.get("bid_depth")
                or m.get("yes_bid_depth")
                or m.get("bids_depth")
                or m.get("bid_size"),
                0,
            )

            ask_depth = _num(
                m.get("ask_depth")
                or m.get("yes_ask_depth")
                or m.get("asks_depth")
                or m.get("ask_size"),
                0,
            )

            # If true depth is missing, use conservative synthetic depth.
            synthetic_depth = False
            if bid_depth <= 0 and ask_depth <= 0:
                synthetic_depth = True
                bid_depth = max(1.0, volume * 0.15) if volume > 0 else 1.0
                ask_depth = max(1.0, volume * 0.15) if volume > 0 else 1.0

            depth = bid_depth + ask_depth
            imbalance = 0.0
            if depth > 0:
                imbalance = (bid_depth - ask_depth) / depth

            spread_cost = spread / 2.0

            if depth <= 2:
                slippage = max(0.02, spread * 0.75)
            elif depth <= 10:
                slippage = max(0.01, spread * 0.45)
            elif depth <= 50:
                slippage = max(0.005, spread * 0.25)
            else:
                slippage = max(0.0025, spread * 0.12)

            fill_probability = self._fill_probability(spread, depth, synthetic_depth)

            leg_reports.append({
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "yes_mid": yes_mid,
                "spread": spread,
                "bid_depth": round(bid_depth, 4),
                "ask_depth": round(ask_depth, 4),
                "total_depth": round(depth, 4),
                "liquidity_imbalance": round(imbalance, 4),
                "spread_cost": round(spread_cost, 4),
                "slippage_estimate": round(slippage, 4),
                "fill_probability": round(fill_probability, 2),
                "synthetic_depth": synthetic_depth,
            })

            total_spread_cost += spread_cost
            total_slippage += slippage
            total_depth += depth
            usable_legs += 1

        if usable_legs == 0:
            # Single-market fallback.
            spread = 0.08
            total_spread_cost = spread / 2
            total_slippage = 0.03
            total_depth = volume
            usable_legs = 1

        avg_spread_cost = total_spread_cost / usable_legs
        avg_slippage = total_slippage / usable_legs
        avg_depth = total_depth / usable_legs

        execution_cost = avg_spread_cost + avg_slippage
        tradable_edge = max(0.0, edge - execution_cost)

        fill_probability = self._portfolio_fill_probability(leg_reports, avg_depth, volume)

        best_size = self._best_execution_size(avg_depth, fill_probability, confidence)

        score = 100.0
        risks = []
        strengths = []
        blockers = []

        if tradable_edge <= 0:
            score -= 35
            blockers.append("Execution cost consumes theoretical edge")
        elif tradable_edge < 0.03:
            score -= 22
            risks.append("Tradable edge is small after execution costs")
        elif tradable_edge >= 0.10:
            strengths.append("Strong tradable edge after execution costs")

        if fill_probability < 35:
            score -= 25
            blockers.append("Low fill probability")
        elif fill_probability < 60:
            score -= 14
            risks.append("Moderate-low fill probability")
        else:
            strengths.append("Acceptable fill probability")

        if avg_depth <= 2:
            score -= 18
            risks.append("Very thin depth estimate")
        elif avg_depth <= 10:
            score -= 8
            risks.append("Thin depth estimate")
        else:
            strengths.append("Depth estimate is usable")

        if any(l.get("synthetic_depth") for l in leg_reports):
            score -= 10
            risks.append("Using synthetic depth because true order-book depth is missing")

        if execution_cost >= edge * 0.75 and edge > 0:
            score -= 18
            risks.append("Execution cost is large relative to edge")

        score = max(0.0, min(100.0, score))

        if blockers:
            rating = "UNUSABLE"
        elif score >= 78:
            rating = "GOOD"
        elif score >= 62:
            rating = "FAIR"
        elif score >= 45:
            rating = "WEAK"
        else:
            rating = "UNUSABLE"

        reason = (
            f"Order book rating {rating}. Raw edge {edge:.4f}, "
            f"estimated execution cost {execution_cost:.4f}, "
            f"tradable edge {tradable_edge:.4f}, fill probability {fill_probability:.2f}%."
        )

        return self._result(
            "ok",
            rating,
            score,
            reason,
            opportunity,
            metrics={
                "raw_edge": round(edge, 6),
                "avg_spread_cost": round(avg_spread_cost, 6),
                "avg_slippage_estimate": round(avg_slippage, 6),
                "execution_cost": round(execution_cost, 6),
                "tradable_edge": round(tradable_edge, 6),
                "fill_probability": round(fill_probability, 2),
                "best_execution_size": round(best_size, 2),
                "avg_depth": round(avg_depth, 4),
                "legs": usable_legs,
                "volume": volume,
            },
            leg_reports=leg_reports,
            risks=risks,
            strengths=strengths,
            blockers=blockers,
        )

    def _fill_probability(self, spread, depth, synthetic_depth):
        prob = 75.0

        if spread >= 0.15:
            prob -= 30
        elif spread >= 0.08:
            prob -= 18
        elif spread >= 0.04:
            prob -= 8
        else:
            prob += 5

        if depth <= 2:
            prob -= 25
        elif depth <= 10:
            prob -= 12
        elif depth >= 50:
            prob += 8

        if synthetic_depth:
            prob -= 12

        return max(5.0, min(95.0, prob))

    def _portfolio_fill_probability(self, leg_reports, avg_depth, volume):
        if leg_reports:
            vals = [float(x.get("fill_probability", 0)) for x in leg_reports]
            if vals:
                return max(5.0, min(95.0, min(vals) * 0.65 + (sum(vals) / len(vals)) * 0.35))

        if volume <= 0:
            return 35.0
        if avg_depth <= 2:
            return 40.0
        return 60.0

    def _best_execution_size(self, avg_depth, fill_probability, confidence):
        base = max(1.0, avg_depth * 0.25)
        conf_mult = max(0.25, min(1.25, confidence / 80.0))
        fill_mult = max(0.20, min(1.0, fill_probability / 80.0))
        return max(1.0, base * conf_mult * fill_mult)

    def _result(self, status, rating, score, reason, opportunity, metrics=None, leg_reports=None, risks=None, strengths=None, blockers=None):
        opportunity = opportunity if isinstance(opportunity, dict) else {}
        metrics = metrics or {}
        risks = risks or []
        strengths = strengths or []
        blockers = blockers or []

        return {
            "module": "oracle_order_book_intelligence",
            "version": self.version,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "ticker": opportunity.get("ticker"),
            "title": opportunity.get("title"),
            "order_book_rating": rating,
            "score": round(float(score or 0), 2),
            "reason": reason,
            "metrics": metrics,
            "leg_reports": leg_reports or [],
            "risks": risks,
            "strengths": strengths,
            "blockers": blockers,
            "compact_card": self._card(opportunity, rating, score, reason, metrics, risks, strengths, blockers),
        }

    def _card(self, opportunity, rating, score, reason, metrics, risks, strengths, blockers):
        lines = [
            "📘 ORACLE ORDER BOOK INTELLIGENCE",
            f"Ticker: {opportunity.get('ticker', 'UNKNOWN')}",
            f"Market: {opportunity.get('title', 'Untitled opportunity')}",
            "",
            f"Rating: {rating}",
            f"Score: {round(float(score or 0), 2)}",
            f"Raw Edge: {metrics.get('raw_edge')}",
            f"Execution Cost: {metrics.get('execution_cost')}",
            f"Tradable Edge: {metrics.get('tradable_edge')}",
            f"Fill Probability: {metrics.get('fill_probability')}%",
            f"Best Size Estimate: {metrics.get('best_execution_size')}",
            "",
            f"Reason: {reason}",
        ]

        if blockers:
            lines.append("")
            lines.append("Blockers:")
            for b in blockers[:5]:
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
            "module": "oracle_order_book_intelligence",
            "version": self.version,
            "status": "ok",
            "outputs": [
                "order_book_rating",
                "execution_cost",
                "tradable_edge",
                "fill_probability",
                "best_execution_size",
            ],
        }


oracle_order_book_intelligence = OracleOrderBookIntelligence()




# ============================================================
# ORACLE-082 Order Book Auto Mapper
# ============================================================

def _oracle082_pick_field(d, names):
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


ORACLE082_FIELD_MAP = {
    "yes_mid": ["yes_mid", "mid", "mid_price", "mark_price"],
    "spread": ["spread", "bid_ask_spread"],
    "bid_depth": ["bid_depth", "yes_bid_depth", "bid_size", "yes_bid_size", "bids_depth"],
    "ask_depth": ["ask_depth", "yes_ask_depth", "ask_size", "yes_ask_size", "asks_depth"],
    "volume": ["volume", "volume_24h", "open_interest", "liquidity"],
}


if "OracleOrderBookIntelligence" in globals():
    if "_oracle082_original_analyze" not in globals():
        _oracle082_original_analyze = OracleOrderBookIntelligence.analyze

        def _oracle082_analyze(self, opportunity):
            if isinstance(opportunity, dict):
                raw = opportunity.get("raw") if isinstance(opportunity.get("raw"), dict) else {}
                raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}
                markets = raw_raw.get("markets") or raw.get("markets") or []

                if isinstance(markets, list):
                    mapped_markets = []
                    for m in markets:
                        if not isinstance(m, dict):
                            mapped_markets.append(m)
                            continue

                        mm = dict(m)
                        notes = []

                        for target, names in ORACLE082_FIELD_MAP.items():
                            if target not in mm or mm.get(target) in (None, ""):
                                val = _oracle082_pick_field(mm, names)
                                if val not in (None, ""):
                                    mm[target] = val
                                    notes.append(f"{target}<-mapped")

                        # If bid/ask are present but spread/mid are missing, derive them.
                        bid = _oracle082_pick_field(mm, ["yes_bid", "bid", "best_bid", "bid_price"])
                        ask = _oracle082_pick_field(mm, ["yes_ask", "ask", "best_ask", "ask_price"])

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

                        if notes:
                            mm["oracle082_mapper_notes"] = notes

                        mapped_markets.append(mm)

                    opportunity = dict(opportunity)
                    opportunity["raw"] = dict(raw)

                    if isinstance(raw_raw, dict) and raw_raw:
                        opportunity["raw"]["raw"] = dict(raw_raw)
                        opportunity["raw"]["raw"]["markets"] = mapped_markets
                    else:
                        opportunity["raw"]["markets"] = mapped_markets

            result = _oracle082_original_analyze(self, opportunity)

            if isinstance(result, dict):
                result["auto_mapper"] = {
                    "version": "ORACLE-082",
                    "status": "applied",
                    "field_map": ORACLE082_FIELD_MAP,
                }
                result["version"] = "ORACLE-049+082"

            return result

        OracleOrderBookIntelligence.analyze = _oracle082_analyze

# ============================================================
# END ORACLE-082
# ============================================================


if __name__ == "__main__":
    sample = {
        "ticker": "TEST",
        "title": "Sample order book opportunity",
        "edge": 0.12,
        "confidence": 90,
        "volume": 0,
        "raw": {
            "raw": {
                "markets": [
                    {"ticker": "A", "spread": 0.04, "yes_mid": 0.33},
                    {"ticker": "B", "spread": 0.05, "yes_mid": 0.12},
                ]
            }
        },
    }

    result = oracle_order_book_intelligence.analyze(sample)
    print(result["compact_card"])
    print(result)
