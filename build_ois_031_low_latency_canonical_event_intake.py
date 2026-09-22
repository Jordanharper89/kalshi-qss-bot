from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_031_low_latency_event_intake.py"
TEST = ROOT / "test_ois_031_low_latency_canonical_event_intake.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nOIS_031_BUILD_ID="OIS-031"\nOIS_031_REVISION="OIS_031_LOW_LATENCY_CANONICAL_EVENT_INTAKE_V1"\n\n@dataclass(frozen=True)\nclass CanonicalMarketEvent:\n    venue_id:str\n    adapter_id:str\n    market_id:str\n    event_type:str\n    venue_event_ns:int\n    oracle_receive_ns:int\n    sequence:int\n    payload_hash:str\n    event_hash:str\n\ndef build_canonical_market_event(venue_id,adapter_id,market_id,event_type,venue_event_ns,oracle_receive_ns,sequence,payload_hash):\n    if not all((venue_id,adapter_id,market_id,event_type)):\n        raise ValueError("complete event identity required")\n    if venue_event_ns<0 or oracle_receive_ns<0 or sequence<0 or len(payload_hash)!=64:\n        raise ValueError("valid timestamps, sequence, and payload hash required")\n    if oracle_receive_ns < venue_event_ns:\n        raise ValueError("receive time cannot precede venue event time")\n    raw={"venue_id":venue_id,"adapter_id":adapter_id,"market_id":market_id,"event_type":event_type,\n         "venue_event_ns":int(venue_event_ns),"oracle_receive_ns":int(oracle_receive_ns),\n         "sequence":int(sequence),"payload_hash":payload_hash}\n    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return CanonicalMarketEvent(venue_id,adapter_id,market_id,event_type,int(venue_event_ns),int(oracle_receive_ns),int(sequence),payload_hash,h)\n\ndef verify_ois_031_low_latency_canonical_event_intake():\n    e=build_canonical_market_event("kalshi","kalshi_ws","m1","trade",100,120,1,"a"*64)\n    return e.oracle_receive_ns-e.venue_event_ns==20 and len(e.event_hash)==64\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_031_low_latency_canonical_event_intake())\n\n    def test_receive_after_event(self):\n        with self.assertRaises(ValueError):\n            build_canonical_market_event("k","a","m","trade",10,9,1,"a"*64)\n\n    def test_deterministic(self):\n        a=build_canonical_market_event("k","a","m","trade",10,12,1,"a"*64)\n        b=build_canonical_market_event("k","a","m","trade",10,12,1,"a"*64)\n        self.assertEqual(a.event_hash,b.event_hash)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-031 CERTIFICATION TEST");print(" LOW-LATENCY CANONICAL EVENT INTAKE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Low-latency canonical market-event intake certified")\n    print("[DONE] OIS-031 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_030_surveillance_gate")
    if getattr(upstream, "verify_ois_030_universal_venue_surveillance_capability_gate")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_031_low_latency_event_intake import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-031 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-031 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
