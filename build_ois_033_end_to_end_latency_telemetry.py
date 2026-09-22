from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_033_latency_telemetry.py"
TEST = ROOT / "test_ois_033_end_to_end_latency_telemetry.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_031_low_latency_event_intake import CanonicalMarketEvent\n\nOIS_033_BUILD_ID="OIS-033"\nOIS_033_REVISION="OIS_033_END_TO_END_LATENCY_TELEMETRY_V1"\n\n@dataclass(frozen=True)\nclass EventLatencyTelemetry:\n    venue_to_oracle_ns:int\n    oracle_to_shadow_ns:int\n    shadow_to_evaluation_ns:int\n    evaluation_to_handoff_ns:int\n    end_to_end_ns:int\n\ndef measure_event_latency(event,shadow_commit_ns,evaluation_ns,handoff_ns):\n    if not isinstance(event,CanonicalMarketEvent):\n        raise ValueError("canonical event required")\n    times=(event.venue_event_ns,event.oracle_receive_ns,int(shadow_commit_ns),int(evaluation_ns),int(handoff_ns))\n    if any(b<a for a,b in zip(times,times[1:])):\n        raise ValueError("latency timestamps must be monotonic")\n    return EventLatencyTelemetry(\n        times[1]-times[0],\n        times[2]-times[1],\n        times[3]-times[2],\n        times[4]-times[3],\n        times[4]-times[0],\n    )\n\ndef verify_ois_033_end_to_end_latency_telemetry():\n    from .ois_031_low_latency_event_intake import build_canonical_market_event\n    e=build_canonical_market_event("k","a","m","trade",100,120,1,"a"*64)\n    x=measure_event_latency(e,130,150,170)\n    return x.end_to_end_ns==70 and x.venue_to_oracle_ns==20\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake import build_canonical_market_event\nfrom qseries_v2.oracle_intelligence_state.ois_033_latency_telemetry import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_033_end_to_end_latency_telemetry())\n\n    def test_segments_sum(self):\n        e=build_canonical_market_event("k","a","m","trade",0,10,1,"a"*64)\n        x=measure_event_latency(e,20,30,40)\n        self.assertEqual(x.end_to_end_ns,x.venue_to_oracle_ns+x.oracle_to_shadow_ns+x.shadow_to_evaluation_ns+x.evaluation_to_handoff_ns)\n\n    def test_nonmonotonic(self):\n        e=build_canonical_market_event("k","a","m","trade",0,10,1,"a"*64)\n        with self.assertRaises(ValueError):\n            measure_event_latency(e,9,30,40)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-033 CERTIFICATION TEST");print(" END-TO-END LATENCY TELEMETRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Venue-to-Oracle-to-Q-Series-handoff latency telemetry certified")\n    print("[DONE] OIS-033 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_032_event_classification")
    if getattr(upstream, "verify_ois_032_market_event_classification")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_033_latency_telemetry import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-033 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-033 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
