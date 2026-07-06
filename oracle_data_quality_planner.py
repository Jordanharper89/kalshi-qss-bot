
"""
ORACLE-077 Data Quality Upgrade Planner

Purpose:
- Diagnose why Oracle is in THIN_LIQUIDITY / NO_TRADE mode.
- Identify missing bid/ask, depth, volume, fill probability, price quality, and order book data.
- Produce prioritized upstream data-fix recommendations.
- Does NOT place trades.
"""

from datetime import datetime, UTC


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _txt(v):
    return str(v or "").strip().upper()


class OracleDataQualityPlanner:
    def __init__(self):
        self.version = "ORACLE-077"

    def analyze(self, ranked, market_regime=None):
        ranked = ranked if isinstance(ranked, list) else []

        counts = {
            "total": len(ranked),
            "missing_bid_ask": 0,
            "missing_depth": 0,
            "missing_volume": 0,
            "low_fill_probability": 0,
            "weak_order_book": 0,
            "poor_tradability": 0,
            "synthetic_price": 0,
            "low_price_quality": 0,
            "no_trade": 0,
            "blocked": 0,
        }

        examples = {}
        repair_scores = {
            "bid_ask": 0,
            "depth": 0,
            "volume": 0,
            "fill_probability": 0,
            "price_quality": 0,
            "order_book": 0,
            "tradability": 0,
            "portfolio_concentration": 0,
        }

        for item in ranked:
            if not isinstance(item, dict):
                continue

            ticker = item.get("ticker")
            action = _txt(item.get("oracle_final_action"))
            execution = _txt(item.get("execution_decision"))
            tradability = _txt(item.get("tradability"))
            order_book = _txt(item.get("order_book_rating"))
            fill = _num(item.get("fill_probability"), 0)
            price_quality = _txt(item.get("price_quality"))
            portfolio = _txt(item.get("portfolio_decision"))

            price_metrics = item.get("price_metrics") if isinstance(item.get("price_metrics"), dict) else {}
            price_discovery = item.get("price_discovery") if isinstance(item.get("price_discovery"), dict) else {}

            total_depth = _num(price_metrics.get("total_depth"), 0)
            synthetic_legs = _num(price_metrics.get("synthetic_legs"), 0)
            legs = _num(price_metrics.get("legs"), 0)
            real_depth_legs = _num(price_metrics.get("real_depth_legs"), 0)

            warnings = price_discovery.get("warnings") if isinstance(price_discovery.get("warnings"), list) else []

            if action == "NO_TRADE":
                counts["no_trade"] += 1

            if execution == "BLOCK":
                counts["blocked"] += 1

            if price_quality in ("LOW", "VERY_LOW", ""):
                counts["low_price_quality"] += 1
                repair_scores["price_quality"] += 3
                self._example(examples, "low_price_quality", ticker)

            if synthetic_legs > 0 or any("synthetic" in str(w).lower() for w in warnings):
                counts["synthetic_price"] += 1
                repair_scores["bid_ask"] += 4
                self._example(examples, "synthetic_price", ticker)

            if legs > 0 and synthetic_legs >= legs:
                counts["missing_bid_ask"] += 1
                repair_scores["bid_ask"] += 5
                self._example(examples, "missing_bid_ask", ticker)

            if total_depth <= 0 or real_depth_legs <= 0:
                counts["missing_depth"] += 1
                repair_scores["depth"] += 6
                self._example(examples, "missing_depth", ticker)

            volume = _num(item.get("volume"), 0)
            raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
            if volume <= 0 and _num(raw.get("volume"), 0) <= 0:
                counts["missing_volume"] += 1
                repair_scores["volume"] += 3
                self._example(examples, "missing_volume", ticker)

            if fill < 40:
                counts["low_fill_probability"] += 1
                repair_scores["fill_probability"] += 5
                self._example(examples, "low_fill_probability", ticker)

            if order_book in ("WEAK", "UNUSABLE", ""):
                counts["weak_order_book"] += 1
                repair_scores["order_book"] += 5
                self._example(examples, "weak_order_book", ticker)

            if tradability in ("POOR", "UNTRADABLE", ""):
                counts["poor_tradability"] += 1
                repair_scores["tradability"] += 5
                self._example(examples, "poor_tradability", ticker)

            if portfolio == "BLOCK_EXPOSURE":
                repair_scores["portfolio_concentration"] += 2
                self._example(examples, "portfolio_concentration", ticker)

        recommendations = self._recommendations(repair_scores, counts, market_regime)

        status = "ok"
        if counts["total"] == 0:
            status = "no_data"
        elif counts["no_trade"] == counts["total"]:
            status = "needs_data_upgrade"

        result = {
            "module": "oracle_data_quality_planner",
            "version": self.version,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "market_regime": market_regime,
            "counts": counts,
            "repair_scores": repair_scores,
            "examples": examples,
            "recommendations": recommendations,
            "compact_card": self._card(status, market_regime, counts, recommendations, examples),
        }

        return result

    def _example(self, examples, key, ticker):
        if key not in examples:
            examples[key] = []
        if ticker and ticker not in examples[key] and len(examples[key]) < 5:
            examples[key].append(ticker)

    def _recommendations(self, scores, counts, regime):
        recs = []

        mapping = [
            ("depth", "Add real bid/ask depth collection from Kalshi order book snapshots.", "HIGH"),
            ("bid_ask", "Upgrade market loader/cache to store best bid, best ask, and real midpoint per leg.", "HIGH"),
            ("order_book", "Feed real order-book fields into ORACLE-049 instead of synthetic depth.", "HIGH"),
            ("fill_probability", "Improve fill probability model using real queue depth, spread, and volume.", "HIGH"),
            ("price_quality", "Ensure ORACLE-056 receives leg-level bid/ask/depth/volume fields.", "MEDIUM"),
            ("volume", "Add volume/open interest extraction per market leg.", "MEDIUM"),
            ("tradability", "Re-run microstructure after real depth and bid/ask fields are available.", "MEDIUM"),
            ("portfolio_concentration", "Reduce duplicate arbitrage candidates or keep only best per event family.", "LOW"),
        ]

        for key, text, priority in mapping:
            recs.append({
                "area": key,
                "priority": priority,
                "score": scores.get(key, 0),
                "recommendation": text,
            })

        recs.sort(key=lambda x: x["score"], reverse=True)

        if regime == "THIN_LIQUIDITY":
            recs.insert(0, {
                "area": "market_regime",
                "priority": "CRITICAL",
                "score": 999,
                "recommendation": "THIN_LIQUIDITY is active: do not loosen execution gates until real depth, bid/ask, and fill data improve.",
            })

        return recs

    def _card(self, status, regime, counts, recs, examples):
        lines = [
            "🧰 ORACLE DATA QUALITY PLANNER",
            f"Status: {status}",
            f"Market Regime: {regime}",
            "",
            f"Total: {counts.get('total')}",
            f"NO_TRADE: {counts.get('no_trade')}",
            f"Blocked: {counts.get('blocked')}",
            f"Missing Bid/Ask: {counts.get('missing_bid_ask')}",
            f"Missing Depth: {counts.get('missing_depth')}",
            f"Missing Volume: {counts.get('missing_volume')}",
            f"Low Fill Probability: {counts.get('low_fill_probability')}",
            f"Weak Order Book: {counts.get('weak_order_book')}",
            f"Poor Tradability: {counts.get('poor_tradability')}",
            f"Synthetic Price: {counts.get('synthetic_price')}",
            f"Low Price Quality: {counts.get('low_price_quality')}",
            "",
            "Top Recommendations:",
        ]

        for r in recs[:6]:
            lines.append(f"- [{r.get('priority')}] {r.get('recommendation')}")

        if examples:
            lines.append("")
            lines.append("Examples:")
            for k, v in list(examples.items())[:6]:
                lines.append(f"- {k}: {', '.join(v)}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_data_quality_planner",
            "version": self.version,
            "status": "ok",
            "outputs": ["counts", "repair_scores", "recommendations", "compact_card"],
        }


oracle_data_quality_planner = OracleDataQualityPlanner()


if __name__ == "__main__":
    sample = [{
        "ticker": "TEST",
        "oracle_final_action": "NO_TRADE",
        "execution_decision": "BLOCK",
        "tradability": "POOR",
        "order_book_rating": "UNUSABLE",
        "fill_probability": 30,
        "price_quality": "LOW",
        "price_metrics": {
            "legs": 2,
            "synthetic_legs": 2,
            "total_depth": 0,
            "real_depth_legs": 0,
        },
    }]

    import pprint
    pprint.pp(oracle_data_quality_planner.analyze(sample, "THIN_LIQUIDITY"))
