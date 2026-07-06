from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_market_microstructure.py")

PATCH = r'''

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
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle083_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-083 INSTALLER")
    print(" Microstructure Auto Mapper")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_market_microstructure.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "ORACLE-083 Microstructure Auto Mapper" in text:
        print("[SKIP] ORACLE-083 already installed")
        return

    b = backup(TARGET)

    marker = 'if __name__ == "__main__":'
    if marker in text:
        text = text.replace(marker, PATCH + "\n\n" + marker, 1)
    else:
        text += "\n\n" + PATCH + "\n"

    TARGET.write_text(text, encoding="utf-8")

    print("[OK] Patched oracle_market_microstructure.py")
    print(f"[OK] Backup created: {b}")
    print("")
    print("Tests:")
    print(" python oracle_market_microstructure.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); top=s.get('last_ranked',[{}])[0]; print(top.get('microstructure',{}).get('auto_mapper')); print(top.get('microstructure_card'))\"")
    print("")
    print("[DONE] ORACLE-083 Microstructure Auto Mapper installed")


if __name__ == "__main__":
    main()