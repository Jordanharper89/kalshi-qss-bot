from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_027_full_universe_state.py"
TEST = ROOT / "test_ois_027_full_universe_market_state.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nOIS_027_BUILD_ID="OIS-027"\nOIS_027_REVISION="OIS_027_FULL_UNIVERSE_MARKET_STATE_V1"\n\n@dataclass(frozen=True)\nclass MarketSurveillanceState:\n    venue_id:str\n    market_id:str\n    category:str\n    tradable:bool\n    last_event_ns:int\n    last_trade_ns:int\n    liquidity_score:float\n    activity_score:float\n    state_hash:str\n\ndef build_market_surveillance_state(venue_id,market_id,category,tradable,last_event_ns,last_trade_ns,liquidity_score,activity_score):\n    if not venue_id or not market_id or not category:\n        raise ValueError("market identity required")\n    if last_event_ns<0 or last_trade_ns<0:\n        raise ValueError("timestamps must be non-negative")\n    if any(not 0<=v<=1 for v in (liquidity_score,activity_score)):\n        raise ValueError("normalized market scores required")\n    raw={\n        "venue_id":venue_id,"market_id":market_id,"category":category,"tradable":bool(tradable),\n        "last_event_ns":int(last_event_ns),"last_trade_ns":int(last_trade_ns),\n        "liquidity_score":float(liquidity_score),"activity_score":float(activity_score)\n    }\n    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return MarketSurveillanceState(\n        venue_id,market_id,category,bool(tradable),int(last_event_ns),int(last_trade_ns),\n        float(liquidity_score),float(activity_score),h\n    )\n\ndef build_full_universe_state(states):\n    rows=tuple(sorted(states,key=lambda x:(x.venue_id,x.market_id)))\n    if not rows:\n        raise ValueError("market universe required")\n    ids=[(x.venue_id,x.market_id) for x in rows]\n    if len(ids)!=len(set(ids)):\n        raise ValueError("duplicate market identity")\n    return rows\n\ndef verify_ois_027_full_universe_market_state():\n    a=build_market_surveillance_state("kalshi","A","econ",True,1,1,.5,.8)\n    b=build_market_surveillance_state("kalshi","B","weather",False,2,0,0,0)\n    u=build_full_universe_state((b,a))\n    return len(u)==2 and u[0].market_id=="A" and len(u[0].state_hash)==64\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_027_full_universe_state import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_027_full_universe_market_state())\n\n    def test_deterministic_order(self):\n        a=build_market_surveillance_state("kalshi","A","x",True,1,1,.5,.5)\n        b=build_market_surveillance_state("kalshi","B","x",True,1,1,.5,.5)\n        self.assertEqual(build_full_universe_state((b,a))[0].market_id,"A")\n\n    def test_duplicate(self):\n        a=build_market_surveillance_state("kalshi","A","x",True,1,1,.5,.5)\n        with self.assertRaises(ValueError):\n            build_full_universe_state((a,a))\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-027 CERTIFICATION TEST");print(" FULL-UNIVERSE MARKET STATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Deterministic full-universe market surveillance state certified")\n    print("[DONE] OIS-027 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_026_universal_surveillance")
    if getattr(upstream, "verify_ois_026_universal_venue_surveillance_foundation")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_027_full_universe_state import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-027 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-027 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
