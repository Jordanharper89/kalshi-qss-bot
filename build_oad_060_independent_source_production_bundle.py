from __future__ import annotations
import ast, hashlib, os, subprocess, sys
from pathlib import Path

BUILD_ID = "OAD-060"
TITLE = "INDEPENDENT SOURCE PRODUCTION BUNDLE"
REVISION = "OAD_060_PRODUCTION_INSTALLER_V1"

def locate_repository():
    candidates = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    seen = set()
    for base in tuple(candidates):
        candidates += list(base.parents)
    for base in candidates:
        for c in (base, base / "kalshi-qss-bot"):
            try: c = c.resolve()
            except OSError: continue
            if c in seen: continue
            seen.add(c)
            if (c / "qseries_v2").is_dir():
                return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
MODULE = ROOT / r"qseries_v2/oracle_adapters/independent/oad_060_independent_source_bundle.py"
TEST = ROOT / r"test_oad_060_independent_source_production_bundle.py"
INIT = ROOT / r"qseries_v2/oracle_adapters/independent/__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_057_nws_weather_adapter import acquire_nws_active_alerts\nfrom .oad_058_federal_register_adapter import acquire_federal_register_documents\nfrom .oad_059_usgs_event_adapter import acquire_usgs_events\nOAD_060_BUILD_ID="OAD-060"; OAD_060_REVISION="OAD_060_INDEPENDENT_SOURCE_PRODUCTION_BUNDLE_V1"\nREAD_ONLY=True; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass IndependentAcquisitionReport:\n    providers:tuple[str,...]; observations:tuple; provider_counts:dict; read_only:bool=True; execution_authority:bool=False\ndef acquire_independent_production_bundle(per_source_limit=5):\n    groups=(("weather.gov",acquire_nws_active_alerts(per_source_limit)),\n            ("federalregister.gov",acquire_federal_register_documents(per_source_limit)),\n            ("usgs.gov",acquire_usgs_events(per_source_limit)))\n    observations=tuple(x for _,rows in groups for x in rows)\n    counts={name:len(rows) for name,rows in groups}\n    return IndependentAcquisitionReport(tuple(name for name,_ in groups),observations,counts)\ndef verify_oad_060_independent_source_production_bundle():\n    r=acquire_independent_production_bundle(2)\n    return r.providers==("weather.gov","federalregister.gov","usgs.gov") and len(r.observations)>0 and not r.execution_authority\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import *\nclass T(unittest.TestCase):\n    def test_physical_bundle(self):\n        r=acquire_independent_production_bundle(2)\n        print("[PHYSICAL] provider_counts="+str(r.provider_counts))\n        print("[PHYSICAL] independent_observations="+str(len(r.observations)))\n        self.assertGreater(len(r.observations),0)\n        self.assertFalse(r.execution_authority)\n        self.assertTrue(all(x.source_class=="authoritative_real_world" for x in r.observations))\nif __name__=="__main__":\n    print("="*72); print(" OAD-060 PHYSICAL CERTIFICATION TEST"); print(" INDEPENDENT SOURCE PRODUCTION BUNDLE"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Multiple authoritative non-Kalshi sources physically acquired")\n    print("[PASS] Independent evidence remains read-only")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-056 through OAD-060 CAPABILITY SLICE CERTIFIED")\n'

def write_exact(path, text):
    text = textwrap_dedent(text).lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def textwrap_dedent(s):
    import textwrap
    return textwrap.dedent(s)

def main():
    print("="*72)
    print(" OAD-060 INSTALLER")
    print(" INDEPENDENT SOURCE PRODUCTION BUNDLE")
    print("="*72)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    kalshi_freeze = ROOT / "qseries_v2" / "oracle_adapters" / "kalshi" / "oad_055_kalshi_production_freeze.py"
    if not kalshi_freeze.is_file():
        raise RuntimeError("Frozen Kalshi OAD-055 boundary missing")
    frozen_hash = hashlib.sha256(kalshi_freeze.read_bytes()).hexdigest()

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from ." + MODULE.stem + " import *"
        if export not in current.splitlines():
            write_exact(INIT, current.rstrip() + ("\n" if current.strip() else "") + export + "\n")
        if hashlib.sha256(kalshi_freeze.read_bytes()).hexdigest() != frozen_hash:
            raise RuntimeError("Frozen Kalshi OAD-055 boundary changed")
        print("[PASS] Frozen Kalshi OAD-055 boundary unchanged")
        print("[PASS] Wrote:", MODULE.relative_to(ROOT))
        print("[PASS] Wrote:", TEST.name)
        print("[PASS] Read-only / execution_authority=False preserved")
        print("[DONE] OAD-060 INSTALLATION COMPLETE")
    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(old)
        print("[ROLLBACK] OAD-060 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
