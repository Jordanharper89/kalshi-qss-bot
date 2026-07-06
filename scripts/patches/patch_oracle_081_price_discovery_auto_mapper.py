from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_live_price_discovery.py")

PATCH = r'''

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
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle081_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-081 INSTALLER")
    print(" Price Discovery Auto Mapper")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_live_price_discovery.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "ORACLE-081 Price Discovery Auto Mapper" in text:
        print("[SKIP] ORACLE-081 already installed")
        return

    b = backup(TARGET)

    marker = 'if __name__ == "__main__":'
    if marker in text:
        text = text.replace(marker, PATCH + "\n\n" + marker, 1)
    else:
        text += "\n\n" + PATCH + "\n"

    TARGET.write_text(text, encoding="utf-8")

    print("[OK] Patched oracle_live_price_discovery.py")
    print(f"[OK] Backup created: {b}")
    print("")
    print("Tests:")
    print(" python oracle_live_price_discovery.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('last_ranked',[{}])[0].get('price_discovery',{}).get('auto_mapper')); print(s.get('last_ranked',[{}])[0].get('price_discovery_card'))\"")
    print("")
    print("[DONE] ORACLE-081 Price Discovery Auto Mapper installed")


if __name__ == "__main__":
    main()