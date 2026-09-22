from __future__ import annotations
import ast, hashlib, os, subprocess, sys
from pathlib import Path

BUILD_ID = "OAD-056"
TITLE = "INDEPENDENT SOURCE PROVENANCE FOUNDATION"
REVISION = "OAD_056_PRODUCTION_INSTALLER_V1"

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
MODULE = ROOT / r"qseries_v2/oracle_adapters/independent/oad_056_independent_source_provenance.py"
TEST = ROOT / r"test_oad_056_independent_source_provenance_foundation.py"
INIT = ROOT / r"qseries_v2/oracle_adapters/independent/__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport json\n\nOAD_056_BUILD_ID="OAD-056"\nOAD_056_REVISION="OAD_056_INDEPENDENT_SOURCE_PROVENANCE_FOUNDATION_V1"\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\n\nALLOWED_SOURCE_CLASSES=("authoritative_real_world","independent_information")\nFORBIDDEN_SOURCE_CLASSES=("prediction_market","kalshi_market_state","kalshi_price_derivative")\n\n@dataclass(frozen=True, slots=True)\nclass IndependentObservation:\n    source_id:str\n    source_class:str\n    observation_type:str\n    subject:str\n    observed_at:str\n    source_url:str\n    payload:dict\n    provenance_hash:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef build_independent_observation(*,source_id,source_class,observation_type,subject,observed_at,source_url,payload):\n    if source_class not in ALLOWED_SOURCE_CLASSES:\n        raise ValueError("source_class is not independently admissible")\n    if not source_id or not observation_type or not subject or not source_url:\n        raise ValueError("independent observation identity fields required")\n    body={"source_id":source_id,"source_class":source_class,"observation_type":observation_type,\n          "subject":subject,"observed_at":observed_at,"source_url":source_url,"payload":payload}\n    h=sha256(json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()\n    return IndependentObservation(source_id,source_class,observation_type,subject,observed_at,source_url,dict(payload),h)\n\ndef verify_oad_056_independent_source_provenance_foundation():\n    x=build_independent_observation(source_id="test.authority",source_class="authoritative_real_world",\n        observation_type="event",subject="test",observed_at="2026-08-27T00:00:00Z",\n        source_url="https://example.gov/test",payload={"x":1})\n    return x.read_only and not x.execution_authority and len(x.provenance_hash)==64\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_056_independent_source_provenance import *\nclass T(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_oad_056_independent_source_provenance_foundation())\n    def test_kalshi_rejected(self):\n        with self.assertRaises(ValueError):\n            build_independent_observation(source_id="kalshi",source_class="prediction_market",observation_type="price",\n                subject="x",observed_at="x",source_url="https://kalshi.com",payload={})\n    def test_execution_false(self):\n        x=build_independent_observation(source_id="gov",source_class="authoritative_real_world",observation_type="event",\n            subject="x",observed_at="x",source_url="https://example.gov",payload={})\n        self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    print("="*72); print(" OAD-056 CERTIFICATION TEST"); print(" INDEPENDENT SOURCE PROVENANCE FOUNDATION"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Kalshi-derived evidence rejected as independent")\n    print("[PASS] Independent provenance contract certified")\n    print("[DONE] OAD-056 CERTIFIED")\n'

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
    print(" OAD-056 INSTALLER")
    print(" INDEPENDENT SOURCE PROVENANCE FOUNDATION")
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
        print("[DONE] OAD-056 INSTALLATION COMPLETE")
    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(old)
        print("[ROLLBACK] OAD-056 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
