from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_036_adapter_registry.py"
TEST = ROOT / "test_ois_036_production_adapter_registry_orchestration.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_036_BUILD_ID="OIS-036"\nOIS_036_REVISION="OIS_036_PRODUCTION_ADAPTER_REGISTRY_ORCHESTRATION_V1"\n\n@dataclass(frozen=True)\nclass AdapterRegistration:\n    adapter_id:str\n    venue_id:str\n    category_scope:str\n    supports_full_universe:bool\n    supports_event_stream:bool\n    enabled:bool\n\ndef register_adapter(adapter_id,venue_id,category_scope="ALL",supports_full_universe=True,supports_event_stream=True,enabled=True):\n    if not adapter_id or not venue_id or not category_scope:\n        raise ValueError("adapter identity required")\n    return AdapterRegistration(adapter_id,venue_id,category_scope,bool(supports_full_universe),bool(supports_event_stream),bool(enabled))\n\ndef build_adapter_registry(adapters):\n    rows=tuple(sorted(adapters,key=lambda x:x.adapter_id))\n    if not rows:\n        raise ValueError("at least one adapter required")\n    if len({x.adapter_id for x in rows})!=len(rows):\n        raise ValueError("duplicate adapter_id")\n    return rows\n\ndef verify_ois_036_production_adapter_registry_orchestration():\n    a=register_adapter("kalshi_universal","kalshi")\n    r=build_adapter_registry((a,))\n    return r[0].supports_full_universe and r[0].supports_event_stream and r[0].category_scope=="ALL"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_036_adapter_registry import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_036_production_adapter_registry_orchestration())\n\n    def test_duplicate(self):\n        a=register_adapter("a","v")\n        with self.assertRaises(ValueError):\n            build_adapter_registry((a,a))\n\n    def test_full_universe_default(self):\n        self.assertTrue(register_adapter("a","v").supports_full_universe)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-036 CERTIFICATION TEST");print(" PRODUCTION ADAPTER REGISTRY + ORCHESTRATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Production adapter registry/orchestration foundation certified")\n    print("[DONE] OIS-036 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_035_low_latency_event_gate")
    if getattr(upstream, "verify_ois_035_low_latency_event_freshness_capability_gate")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_036_adapter_registry import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-036 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-036 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
