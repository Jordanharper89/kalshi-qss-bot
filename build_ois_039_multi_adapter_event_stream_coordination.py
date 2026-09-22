from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_039_multi_adapter_event_coordination.py"
TEST = ROOT / "test_ois_039_multi_adapter_event_stream_coordination.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_031_low_latency_event_intake import CanonicalMarketEvent\n\nOIS_039_BUILD_ID="OIS-039"\nOIS_039_REVISION="OIS_039_MULTI_ADAPTER_EVENT_STREAM_COORDINATION_V1"\n\n@dataclass(frozen=True)\nclass CoordinatedAdapterEvent:\n    adapter_id:str\n    venue_id:str\n    market_id:str\n    sequence:int\n    oracle_receive_ns:int\n    event_hash:str\n\ndef coordinate_adapter_events(events):\n    rows=tuple(sorted(events,key=lambda x:(x.oracle_receive_ns,x.adapter_id,x.market_id,x.sequence,x.event_hash)))\n    seen=set()\n    out=[]\n    for x in rows:\n        if not isinstance(x,CanonicalMarketEvent):\n            raise ValueError("canonical market events required")\n        key=(x.adapter_id,x.market_id,x.sequence)\n        if key in seen:\n            raise ValueError("duplicate adapter event sequence")\n        seen.add(key)\n        out.append(CoordinatedAdapterEvent(x.adapter_id,x.venue_id,x.market_id,x.sequence,x.oracle_receive_ns,x.event_hash))\n    return tuple(out)\n\ndef verify_ois_039_multi_adapter_event_stream_coordination():\n    from .ois_031_low_latency_event_intake import build_canonical_market_event\n    a=build_canonical_market_event("kalshi","kalshi_ws","A","trade",1,3,1,"a"*64)\n    b=build_canonical_market_event("coinbase","coinbase_ws","BTC-USD","trade",1,2,1,"b"*64)\n    c=coordinate_adapter_events((a,b))\n    return c[0].adapter_id=="coinbase_ws" and c[1].adapter_id=="kalshi_ws"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake import build_canonical_market_event\nfrom qseries_v2.oracle_intelligence_state.ois_039_multi_adapter_event_coordination import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_039_multi_adapter_event_stream_coordination())\n\n    def test_order(self):\n        a=build_canonical_market_event("v1","a1","m1","trade",1,5,1,"a"*64)\n        b=build_canonical_market_event("v2","a2","m2","trade",1,4,1,"b"*64)\n        self.assertEqual(coordinate_adapter_events((a,b))[0].adapter_id,"a2")\n\n    def test_duplicate(self):\n        a=build_canonical_market_event("v","a","m","trade",1,2,1,"a"*64)\n        with self.assertRaises(ValueError):\n            coordinate_adapter_events((a,a))\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-039 CERTIFICATION TEST");print(" MULTI-ADAPTER EVENT-STREAM COORDINATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Deterministic multi-adapter event-stream coordination certified")\n    print("[DONE] OIS-039 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_038_universe_reconciliation")
    if getattr(upstream, "verify_ois_038_full_universe_reconciliation")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_039_multi_adapter_event_coordination import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-039 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-039 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
