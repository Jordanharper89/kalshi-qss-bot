from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_032_event_classification.py"
TEST = ROOT / "test_ois_032_market_event_classification.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_031_low_latency_event_intake import CanonicalMarketEvent\n\nOIS_032_BUILD_ID="OIS-032"\nOIS_032_REVISION="OIS_032_MARKET_EVENT_CLASSIFICATION_V1"\n\nEVENT_CLASSES=(\n    "TRADE","BOOK_ADD","BOOK_REMOVE","BOOK_SIZE_CHANGE","BEST_PRICE_CHANGE",\n    "SPREAD_CHANGE","LIQUIDITY_ARRIVAL","LIQUIDITY_WITHDRAWAL","ABNORMAL_SIZE",\n    "TRADE_BURST","PRICE_JUMP","MARKET_STATUS_CHANGE","NEW_LISTING",\n    "SETTLEMENT","CROSS_MARKET_DIVERGENCE","OPPORTUNITY_TRIGGER","OTHER"\n)\n\n@dataclass(frozen=True)\nclass ClassifiedMarketEvent:\n    event_hash:str\n    event_class:str\n    urgency:str\n\ndef classify_market_event(event):\n    if not isinstance(event,CanonicalMarketEvent):\n        raise ValueError("canonical market event required")\n    x=event.event_type.strip().lower()\n    mapping={\n        "trade":"TRADE","book_add":"BOOK_ADD","book_remove":"BOOK_REMOVE",\n        "book_size_change":"BOOK_SIZE_CHANGE","best_price_change":"BEST_PRICE_CHANGE",\n        "spread_change":"SPREAD_CHANGE","liquidity_arrival":"LIQUIDITY_ARRIVAL",\n        "liquidity_withdrawal":"LIQUIDITY_WITHDRAWAL","abnormal_size":"ABNORMAL_SIZE",\n        "trade_burst":"TRADE_BURST","price_jump":"PRICE_JUMP","market_status":"MARKET_STATUS_CHANGE",\n        "new_listing":"NEW_LISTING","settlement":"SETTLEMENT",\n        "cross_market_divergence":"CROSS_MARKET_DIVERGENCE","opportunity_trigger":"OPPORTUNITY_TRIGGER",\n    }\n    cls=mapping.get(x,"OTHER")\n    urgency="INTERRUPT" if cls in ("PRICE_JUMP","TRADE_BURST","LIQUIDITY_WITHDRAWAL","CROSS_MARKET_DIVERGENCE","OPPORTUNITY_TRIGGER","NEW_LISTING") else "NORMAL"\n    return ClassifiedMarketEvent(event.event_hash,cls,urgency)\n\ndef verify_ois_032_market_event_classification():\n    from .ois_031_low_latency_event_intake import build_canonical_market_event\n    e=build_canonical_market_event("k","a","m","price_jump",1,2,1,"a"*64)\n    c=classify_market_event(e)\n    return c.event_class=="PRICE_JUMP" and c.urgency=="INTERRUPT"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake import build_canonical_market_event\nfrom qseries_v2.oracle_intelligence_state.ois_032_event_classification import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_032_market_event_classification())\n\n    def test_trade_normal(self):\n        e=build_canonical_market_event("k","a","m","trade",1,2,1,"a"*64)\n        self.assertEqual(classify_market_event(e).urgency,"NORMAL")\n\n    def test_unknown_other(self):\n        e=build_canonical_market_event("k","a","m","mystery",1,2,1,"a"*64)\n        self.assertEqual(classify_market_event(e).event_class,"OTHER")\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-032 CERTIFICATION TEST");print(" MARKET EVENT CLASSIFICATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Canonical transaction/market-event classification certified")\n    print("[DONE] OIS-032 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake")
    if getattr(upstream, "verify_ois_031_low_latency_canonical_event_intake")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_032_event_classification import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-032 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-032 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
