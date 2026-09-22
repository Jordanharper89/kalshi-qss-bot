from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-062"; REVISION="OAD_062_PRODUCTION_INSTALLER_V1"
def find_root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise SystemExit("[ERROR] Q Series repository not found")
ROOT=find_root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"; MODULE=PKG/"oad_062_independent_canonical_provenance_validation.py"; TEST=ROOT/"test_oad_062_independent_canonical_provenance_validation.py"; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass ProvenanceValidation: observation_id:str; valid:bool; reason:str\ndef validate_independent_canonical(x):\n p=dict(x.payload); q=dict(x.provenance)\n ok=(p.get("independent_evidence") is True and p.get("source_class") in ("authoritative_real_world","independent_information")\n     and str(p.get("source_url","")).startswith("http") and len(str(p.get("provenance_hash","")))==64\n     and q.get("execution_authority") is False and "kalshi" not in str(x.source_id).lower())\n return ProvenanceValidation(x.observation_id,ok,"VALID_INDEPENDENT_PROVENANCE" if ok else "INVALID_OR_MARKET_DERIVED")\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_062_independent_canonical_provenance_validation import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  c=canonicalize_independent_bundle(acquire_independent_production_bundle(2),"oad062.physical"); v=[validate_independent_canonical(x) for x in c]\n  print("[PHYSICAL] provenance_validated=",sum(x.valid for x in v),"total=",len(v))\n  self.assertGreater(len(v),0); self.assertTrue(all(x.valid for x in v))\nif __name__=="__main__":\n print("="*80); print(" OAD-062 PHYSICAL CERTIFICATION TEST"); print("="*80)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] Independent provenance survives canonicalization"); print("[DONE] OAD-062 CERTIFIED")\n'
def write(p,s):
 s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
 print("="*80); print(" OAD-062 INSTALLER"); print(" INDEPENDENT CANONICAL PROVENANCE VALIDATION"); print("="*80); print("[BOOT] Revision:",REVISION); print("[ROOT]",ROOT)
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
  print("[PASS] OAD-060 dependency verified"); print("[PASS] Frozen Kalshi OAD-055 unchanged"); print("[PASS] Wrote:",MODULE.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] execution_authority=FALSE"); print("[DONE] OAD-062 INSTALLATION COMPLETE")
 except Exception:
  for p,v in backup.items():
   if v is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(v)
  print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
