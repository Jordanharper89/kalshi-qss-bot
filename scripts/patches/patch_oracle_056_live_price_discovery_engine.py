from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_live_price_discovery.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
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
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-056 Live Price Discovery Integration
# ============================================================

try:
    from oracle_live_price_discovery import oracle_live_price_discovery
except Exception:
    oracle_live_price_discovery = None


def _oracle056_apply_price_discovery(ranked):
    if oracle_live_price_discovery is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            pd = oracle_live_price_discovery.analyze(item)
            item["price_discovery"] = pd
            item["price_quality"] = pd.get("quality")
            item["price_quality_score"] = pd.get("quality_score")
            item["price_metrics"] = pd.get("metrics", {})
            item["price_discovery_card"] = pd.get("compact_card")
        except Exception as exc:
            item["price_discovery"] = {
                "status": "error",
                "quality": "VERY_LOW",
                "reason": str(exc),
            }
            item["price_quality"] = "VERY_LOW"
            item["price_quality_score"] = 0

        enriched.append(item)

    quality_rank = {
        "HIGH": 4,
        "MEDIUM": 3,
        "LOW": 2,
        "VERY_LOW": 1,
    }

    enriched.sort(
        key=lambda x: (
            quality_rank.get(x.get("price_quality"), 0),
            x.get("price_quality_score", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle056_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle056_apply_price_discovery(ranked)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        q = item.get("price_quality", "UNKNOWN")
                        counts[q] = counts.get(q, 0) + 1

                _state["price_discovery_status"] = {
                    "status": "ok" if oracle_live_price_discovery is not None else "missing",
                    "quality_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
            else:
                _state["price_discovery_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["price_discovery_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle056_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle056_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle056_original_run_cycle(*args, **kwargs)
        _oracle056_enrich_state()
        return result


if "_oracle056_original_status" not in globals() and "status" in globals():
    _oracle056_original_status = status

    def status(*args, **kwargs):
        result = _oracle056_original_status(*args, **kwargs)
        _oracle056_enrich_state()

        if isinstance(result, dict):
            result["price_discovery_status"] = (
                globals().get("_state", {}).get("price_discovery_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-056
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle056_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-056 INSTALLER")
    print(" Live Price Discovery Engine")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_live_price_discovery.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-056 Live Price Discovery Integration" in text:
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
    print(" python oracle_live_price_discovery.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('price_discovery_status')); print(s.get('last_ranked',[{}])[0].get('price_discovery_card'))\"")
    print("")
    print("[DONE] ORACLE-056 Live Price Discovery Engine installed")


if __name__ == "__main__":
    main()