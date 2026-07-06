
"""
ORACLE-080 Market Data Field Mapper

Purpose:
- Inspect live Oracle opportunities for raw market fields.
- Discover available bid/ask/depth/volume keys.
- Helps decide how to upgrade loader/cache without guessing.
- Does NOT place trades.
"""

from datetime import datetime, UTC
from collections import Counter


KEY_HINTS = {
    "bid": ["bid", "yes_bid", "best_bid", "yes_bid_price", "bid_price"],
    "ask": ["ask", "yes_ask", "best_ask", "yes_ask_price", "ask_price"],
    "mid": ["mid", "yes_mid", "mid_price"],
    "spread": ["spread", "bid_ask_spread"],
    "depth": ["depth", "bid_depth", "ask_depth", "yes_bid_depth", "yes_ask_depth", "bid_size", "ask_size"],
    "volume": ["volume", "volume_24h", "open_interest", "liquidity"],
    "last": ["last_price", "last_trade_price", "last"],
}


class OracleMarketDataFieldMapper:
    def __init__(self):
        self.version = "ORACLE-080"

    def inspect(self, ranked):
        ranked = ranked if isinstance(ranked, list) else []

        key_counts = Counter()
        hint_counts = {k: Counter() for k in KEY_HINTS}
        examples = {}

        market_count = 0

        for item in ranked:
            if not isinstance(item, dict):
                continue

            raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
            raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}
            markets = raw_raw.get("markets") or raw.get("markets") or []

            if not isinstance(markets, list):
                continue

            for m in markets:
                if not isinstance(m, dict):
                    continue

                market_count += 1

                for key, value in m.items():
                    key_counts[key] += 1

                    for group, hints in KEY_HINTS.items():
                        if key.lower() in hints or any(h in key.lower() for h in hints):
                            hint_counts[group][key] += 1
                            examples.setdefault(group, {}).setdefault(key, value)

        recommendations = []

        for group in ["bid", "ask", "depth", "volume"]:
            if not hint_counts[group]:
                recommendations.append({
                    "priority": "HIGH",
                    "group": group,
                    "message": f"No obvious {group} field found in raw market objects.",
                })
            else:
                top = hint_counts[group].most_common(5)
                recommendations.append({
                    "priority": "MEDIUM",
                    "group": group,
                    "message": f"Possible {group} fields found: {top}",
                })

        result = {
            "module": "oracle_market_data_field_mapper",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "opportunities": len(ranked),
            "market_objects": market_count,
            "top_keys": key_counts.most_common(50),
            "hint_counts": {k: v.most_common(20) for k, v in hint_counts.items()},
            "examples": examples,
            "recommendations": recommendations,
            "compact_card": self._card(len(ranked), market_count, key_counts, hint_counts, recommendations),
        }

        return result

    def _card(self, opps, market_count, key_counts, hint_counts, recommendations):
        lines = [
            "🗺️ ORACLE MARKET DATA FIELD MAPPER",
            f"Opportunities inspected: {opps}",
            f"Market objects inspected: {market_count}",
            "",
            "Detected Field Groups:",
        ]

        for group, counts in hint_counts.items():
            if counts:
                lines.append(f"- {group}: {counts.most_common(5)}")
            else:
                lines.append(f"- {group}: NONE")

        lines.append("")
        lines.append("Top Raw Keys:")
        for k, c in key_counts.most_common(15):
            lines.append(f"- {k}: {c}")

        lines.append("")
        lines.append("Recommendations:")
        for r in recommendations[:8]:
            lines.append(f"- [{r.get('priority')}] {r.get('message')}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_market_data_field_mapper",
            "version": self.version,
            "status": "ok",
            "outputs": ["top_keys", "hint_counts", "recommendations"],
        }


oracle_market_data_field_mapper = OracleMarketDataFieldMapper()


if __name__ == "__main__":
    import oracle_continuous_intelligence as o
    o.run_cycle()
    s = o.status()
    result = oracle_market_data_field_mapper.inspect(s.get("last_ranked", []))
    print(result["compact_card"])
