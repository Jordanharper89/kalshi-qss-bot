from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-064"; REVISION="OAD_064_PRODUCTION_INSTALLER_V1"
def find_root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise SystemExit("[ERROR] Q Series repository not found")
ROOT=find_root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"; MODULE=PKG/"oad_064_bounded_market_association_candidate.py"; TEST=ROOT/"test_oad_064_bounded_market_association_candidate.py"; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass AssociationCandidate: observation_id:str; market_id:str; overlap_terms:tuple; overlap_count:int; candidate_only:bool=True\ndef bounded_market_association_candidates(entity_terms,indexed_markets,max_candidates=10):\n if not isinstance(indexed_markets,dict): raise TypeError("pre-bounded indexed mapping required")\n et=set(entity_terms.terms); out=[]\n for mid,terms in indexed_markets.items():\n  ov=tuple(sorted(et & {str(t).lower() for t in terms}))\n  if ov: out.append(AssociationCandidate(entity_terms.observation_id,str(mid),ov,len(ov)))\n return tuple(sorted(out,key=lambda x:(-x.overlap_count,x.market_id))[:max_candidates])\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_064_bounded_market_association_candidate import *\nclass T(unittest.TestCase):\n def test_bounded(self):\n  class E: observation_id="o1"; terms=("federal","reserve","rate")\n  r=bounded_market_association_candidates(E(),{"KX1":("federal","reserve"),"KX2":("weather","rain")})\n  self.assertEqual(r[0].market_id,"KX1"); self.assertTrue(r[0].candidate_only)\n def test_no_scan(self):\n  class E: observation_id="o"; terms=()\n  with self.assertRaises(TypeError): bounded_market_association_candidates(E(),[])\nif __name__=="__main__":\n print("="*80); print(" OAD-064 CERTIFICATION TEST"); print("="*80)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] Association accepts only pre-bounded/indexed market sets"); print("[DONE] OAD-064 CERTIFIED")\n'
def write(p,s):
 s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
 print("="*80); print(" OAD-064 INSTALLER"); print(" BOUNDED INDEXED MARKET ASSOCIATION CANDIDATE CONTRACT"); print("="*80); print("[BOOT] Revision:",REVISION); print("[ROOT]",ROOT)
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
  print("[PASS] OAD-060 dependency verified"); print("[PASS] Frozen Kalshi OAD-055 unchanged"); print("[PASS] Wrote:",MODULE.relative_to(ROOT)); print("[PASS] Wrote:",TEST.name); print("[PASS] execution_authority=FALSE"); print("[DONE] OAD-064 INSTALLATION COMPLETE")
 except Exception:
  for p,v in backup.items():
   if v is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(v)
  print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
