
"""
ORACLE-056 Live Price Discovery Engine

Purpose:
- Extract best available live price facts from Oracle opportunities.
- Normalize bid/ask/mid/spread/depth/trade proxies.
- Grade data quality so downstream engines know whether prices are real or synthetic.
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
    return str(v or "").strip()


class OracleLivePriceDiscovery:
    def __init__(self):
        self.version = "ORACLE-056"

    def analyze(self, opportunity):
        if not isinstance(opportunity, dict):
            return self._result("error", {}, "Invalid opportunity object")

        raw = opportunity.get("raw") if isinstance(opportunity.get("raw"), dict) else {}
        raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}
        markets = raw_raw.get("markets") or raw.get("markets") or []

        if not isinstance(markets, list):
            markets = []

        legs = []
        quality_score = 100.0
        warnings = []
        strengths = []

        for m in markets:
            if not isinstance(m, dict):
                continue

            yes_bid = _num(m.get("yes_bid") or m.get("bid") or m.get("best_bid"), None)
            yes_ask = _num(m.get("yes_ask") or m.get("ask") or m.get("best_ask"), None)
            yes_mid = _num(m.get("yes_mid") or m.get("mid"), None)
            spread = _num(m.get("spread"), None)

            synthetic = False

            if yes_bid is None or yes_ask is None:
                synthetic = True
                if yes_mid is not None and spread is not None:
                    yes_bid = max(0.0, yes_mid - spread / 2)
                    yes_ask = min(1.0, yes_mid + spread / 2)
                elif yes_mid is not None:
                    spread = 0.08
                    yes_bid = max(0.0, yes_mid - 0.04)
                    yes_ask = min(1.0, yes_mid + 0.04)
                else:
                    yes_bid = 0.0
                    yes_ask = 0.0

            if yes_mid is None:
                yes_mid = (yes_bid + yes_ask) / 2 if yes_ask or yes_bid else 0.0
                synthetic = True

            if spread is None:
                spread = abs(yes_ask - yes_bid)
                synthetic = True

            bid_depth = _num(
                m.get("bid_depth")
                or m.get("yes_bid_depth")
                or m.get("bid_size")
                or m.get("yes_bid_size"),
                0,
            )

            ask_depth = _num(
                m.get("ask_depth")
                or m.get("yes_ask_depth")
                or m.get("ask_size")
                or m.get("yes_ask_size"),
                0,
            )

            last_price = _num(m.get("last_price") or m.get("last_trade_price"), 0)
            volume = _num(m.get("volume") or m.get("volume_24h") or m.get("open_interest"), 0)

            if synthetic:
                quality_score -= 8
                warnings.append(f"Synthetic bid/ask estimate used for {m.get('ticker')}")

            if bid_depth <= 0 and ask_depth <= 0:
                quality_score -= 6
                warnings.append(f"No depth data for {m.get('ticker')}")

            if spread >= 0.15:
                quality_score -= 12
                warnings.append(f"Very wide spread on {m.get('ticker')}: {spread:.4f}")
            elif spread <= 0.02:
                strengths.append(f"Tight spread on {m.get('ticker')}: {spread:.4f}")

            legs.append({
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "yes_bid": round(yes_bid, 6),
                "yes_ask": round(yes_ask, 6),
                "yes_mid": round(yes_mid, 6),
                "spread": round(spread, 6),
                "bid_depth": round(bid_depth, 4),
                "ask_depth": round(ask_depth, 4),
                "total_depth": round(bid_depth + ask_depth, 4),
                "last_price": round(last_price, 6),
                "volume": round(volume, 4),
                "synthetic": synthetic,
            })

        if not legs:
            quality_score -= 35
            warnings.append("No leg-level market price data available")

        avg_spread = sum(x["spread"] for x in legs) / len(legs) if legs else 0
        avg_mid = sum(x["yes_mid"] for x in legs) / len(legs) if legs else 0
        total_depth = sum(x["total_depth"] for x in legs)
        synthetic_count = sum(1 for x in legs if x["synthetic"])

        if total_depth <= 0:
            quality_score -= 15
            warnings.append("No usable aggregate depth")

        if synthetic_count == len(legs) and legs:
            quality_score -= 10
            warnings.append("All price legs rely on synthetic estimates")

        quality_score = max(0.0, min(100.0, quality_score))

        if quality_score >= 80:
            quality = "HIGH"
        elif quality_score >= 60:
            quality = "MEDIUM"
        elif quality_score >= 40:
            quality = "LOW"
        else:
            quality = "VERY_LOW"

        metrics = {
            "legs": len(legs),
            "avg_spread": round(avg_spread, 6),
            "avg_mid": round(avg_mid, 6),
            "total_depth": round(total_depth, 4),
            "synthetic_legs": synthetic_count,
            "real_depth_legs": sum(1 for x in legs if x["total_depth"] > 0),
            "quality": quality,
            "quality_score": round(quality_score, 2),
        }

        return self._result("ok", {
            "quality": quality,
            "quality_score": round(quality_score, 2),
            "metrics": metrics,
            "legs": legs,
            "warnings": warnings[:20],
            "strengths": strengths[:20],
        }, "Price discovery completed")

    def _result(self, status, payload, reason):
        return {
            "module": "oracle_live_price_discovery",
            "version": self.version,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "reason": reason,
            **payload,
            "compact_card": self._card(payload),
        }

    def _card(self, payload):
        metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
        warnings = payload.get("warnings", []) if isinstance(payload, dict) else []
        strengths = payload.get("strengths", []) if isinstance(payload, dict) else []

        lines = [
            "🔎 ORACLE PRICE DISCOVERY",
            f"Quality: {metrics.get('quality')}",
            f"Quality Score: {metrics.get('quality_score')}",
            f"Legs: {metrics.get('legs')}",
            f"Avg Spread: {metrics.get('avg_spread')}",
            f"Avg Mid: {metrics.get('avg_mid')}",
            f"Total Depth: {metrics.get('total_depth')}",
            f"Synthetic Legs: {metrics.get('synthetic_legs')}",
        ]

        if warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in warnings[:6]:
                lines.append(f"- {w}")

        if strengths:
            lines.append("")
            lines.append("Strengths:")
            for s in strengths[:6]:
                lines.append(f"- {s}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_live_price_discovery",
            "version": self.version,
            "status": "ok",
            "outputs": ["price_quality", "price_quality_score", "price_discovery_card"],
        }


oracle_live_price_discovery = OracleLivePriceDiscovery()




# ============================================================
# ORACLE-081 Price Discovery Auto Mapper
# ============================================================

def _oracle081_pick_field(d, names):
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


ORACLE081_FIELD_MAP = {
    "yes_bid": ["yes_bid", "bid", "best_bid", "yes_bid_price", "bid_price"],
    "yes_ask": ["yes_ask", "ask", "best_ask", "yes_ask_price", "ask_price"],
    "yes_mid": ["yes_mid", "mid", "mid_price", "mark_price"],
    "spread": ["spread", "bid_ask_spread"],
    "bid_depth": ["bid_depth", "yes_bid_depth", "bid_size", "yes_bid_size", "bids_depth"],
    "ask_depth": ["ask_depth", "yes_ask_depth", "ask_size", "yes_ask_size", "asks_depth"],
    "last_price": ["last_price", "last_trade_price", "last"],
    "volume": ["volume", "volume_24h", "open_interest", "liquidity"],
}


if "OracleLivePriceDiscovery" in globals():
    if "_oracle081_original_analyze" not in globals():
        _oracle081_original_analyze = OracleLivePriceDiscovery.analyze

        def _oracle081_analyze(self, opportunity):
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
                        mapper_notes = []

                        for target, names in ORACLE081_FIELD_MAP.items():
                            if target not in mm or mm.get(target) in (None, ""):
                                val = _oracle081_pick_field(mm, names)
                                if val not in (None, ""):
                                    mm[target] = val
                                    mapper_notes.append(f"{target}<-mapped")

                        if mapper_notes:
                            mm["oracle081_mapper_notes"] = mapper_notes

                        mapped_markets.append(mm)

                    if "raw" in raw and isinstance(raw.get("raw"), dict):
                        opportunity = dict(opportunity)
                        opportunity["raw"] = dict(raw)
                        opportunity["raw"]["raw"] = dict(raw_raw)
                        opportunity["raw"]["raw"]["markets"] = mapped_markets
                    else:
                        opportunity = dict(opportunity)
                        opportunity["raw"] = dict(raw)
                        opportunity["raw"]["markets"] = mapped_markets

            result = _oracle081_original_analyze(self, opportunity)

            if isinstance(result, dict):
                result["auto_mapper"] = {
                    "version": "ORACLE-081",
                    "status": "applied",
                    "field_map": ORACLE081_FIELD_MAP,
                }
                result["version"] = "ORACLE-056+081"

            return result

        OracleLivePriceDiscovery.analyze = _oracle081_analyze

# ============================================================
# END ORACLE-081
# ============================================================


if __name__ == "__main__":
    sample = {
        "ticker": "TEST",
        "title": "Sample price discovery",
        "raw": {
            "raw": {
                "markets": [
                    {"ticker": "A", "yes_mid": 0.42, "spread": 0.04},
                    {"ticker": "B", "yes_bid": 0.20, "yes_ask": 0.24, "bid_depth": 30, "ask_depth": 20},
                ]
            }
        }
    }

    import pprint
    pprint.pp(oracle_live_price_discovery.analyze(sample))
