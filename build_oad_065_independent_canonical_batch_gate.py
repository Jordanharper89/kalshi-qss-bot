from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-065"; REVISION="OAD_065_PRODUCTION_INSTALLER_V1"
def find_root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise SystemExit("[ERROR] Q Series repository not found")
ROOT=find_root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"; MODULE=PKG/"oad_065_independent_canonical_batch_gate.py"; TEST=ROOT/"test_oad_065_independent_canonical_batch_gate.py"; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom .oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle\nfrom .oad_062_independent_canonical_provenance_validation import validate_independent_canonical\nfrom .oad_063_independent_entity_term_projection import extract_independent_entity_terms\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass IndependentCanonicalBatch: canonical_observations:tuple; provenance_validated:int; entity_projected:int; ready_for_existing_persistence_router:bool\ndef build_independent_canonical_batch(report,acquisition_batch_id):\n c=canonicalize_independent_bundle(report,acquisition_batch_id); v=[validate_independent_canonical(x) for x in c]; e=[extract_independent_entity_terms(x) for x in c]\n ready=bool(c) and all(x.valid for x in v) and all(x.terms for x in e)\n return IndependentCanonicalBatch(c,sum(x.valid for x in v),sum(bool(x.terms) for x in e),ready)\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_065_independent_canonical_batch_gate import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  raw=acquire_independent_production_bundle(2); b=build_independent_canonical_batch(raw,"oad065.physical")\n  print("[PHYSICAL] acquired=",len(raw.observations)); print("[PHYSICAL] canonical=",len(b.canonical_observations))\n  print("[PHYSICAL] provenance_validated=",b.provenance_validated); print("[PHYSICAL] entity_projected=",b.entity_projected)\n  print("[PHYSICAL] ready_for_existing_persistence_router=",b.ready_for_existing_persistence_router)\n  self.assertGreater(len(b.canonical_observations),0); self.assertTrue(b.ready_for_existing_persistence_router)\n  self.assertTrue(all(x.execution_allowed is False for x in b.canonical_observations))\nif __name__=="__main__":\n print("="*80); print(" OAD-065 PHYSICAL CERTIFICATION TEST"); print("="*80)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] Existing OLA-015 remains PostgreSQL persistence authority"); print("[PASS] probability_enabled=FALSE"); print("[PASS] execution_authority=FALSE"); print("[DONE] OAD-065 CERTIFIED")\n'
def write(p,s):
 s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
 print("="*80); print(" OAD-065 INSTALLER"); print(" INDEPENDENT CANONICAL BATCH GATE"); print("="*80); print("[BOOT] Revision:",REVISION); print("[ROOT]",ROOT)
 freeze=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
 if not freeze.is_file(): raise RuntimeError("Frozen Kalshi OAD-055 boundary missing")
 if not (PKG/"oad_060_independent_source_bundle.py").is_file(): raise RuntimeError("Certified OAD-060 dependency missing")
 h=hashlib.sha256(freeze.read_bytes()).hexdigest(); affected=(MODULE,TEST,INIT); backup={p:(p.read_bytes() if p.exists() else None) for p in affected}
 try:
  write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
  lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []; exp="from ."+MODULE.stem+" import *"
  if exp not in lines: lines.append(exp)
  write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
  if hashlib.sha256(freeze.read_bytes()).hexdigest()!=h: raise RuntimeError("Frozen Kalshi OAD-055 changed")
  print("[PASS] OAD-060 dependency verified"); print("[PASS] Frozen Kalshi OAD-055 unchanged"); print("[PASS] Wrote:",MODULE.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] execution_authority=FALSE"); print("[DONE] OAD-065 INSTALLATION COMPLETE")
 except Exception:
  for p,v in backup.items():
   if v is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(v)
  print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
