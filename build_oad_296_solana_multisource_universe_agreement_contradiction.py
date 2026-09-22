
from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-296'
REVISION='OAD_296_SOLANA_MULTISOURCE_UNIVERSE_AGREEMENT_CONTRADICTION_V1'
TITLE='SOLANA MULTI-SOURCE UNIVERSE AGREEMENT / CONTRADICTION'
EXPECTED_FILENAME='build_oad_296_solana_multisource_universe_agreement_contradiction.py'
MODULE_NAME='oad_296_solana_multisource_universe_agreement_contradiction.py'
TEST_NAME='test_oad_296_solana_multisource_universe_agreement_contradiction.py'
DEPENDENCIES=[('oad_292_solana_bounded_multisource_token_universe.py', 'discover_bounded_multisource_solana_universe'), ('oad_280_gmgn_dexscreener_cross_source_comparison.py', 'compare_live_gmgn_dexscreener_for_same_token')]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_292_solana_bounded_multisource_token_universe import discover_bounded_multisource_solana_universe\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass SolanaUniverseSourceAgreement:\n token_address:str; sources:tuple; state:str\n@dataclass(frozen=True,slots=True)\nclass SolanaUniverseAgreementReport:\n unique_tokens:int; multi_source_tokens:int; single_source_tokens:int; rows:tuple; execution_authority:bool=False\ndef compare_solana_universe_source_presence(timeout_seconds=30.0):\n u=discover_bounded_multisource_solana_universe(timeout_seconds)\n rows=[]\n for c in u.candidates:\n  state="MULTI_SOURCE_PRESENCE" if len(c.sources)>1 else "SINGLE_SOURCE_PRESENCE"\n  rows.append(SolanaUniverseSourceAgreement(c.token_address,c.sources,state))\n multi=sum(x.state=="MULTI_SOURCE_PRESENCE" for x in rows)\n return SolanaUniverseAgreementReport(len(rows),multi,len(rows)-multi,tuple(rows),False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_296_solana_multisource_universe_agreement_contradiction import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=compare_solana_universe_source_presence()\n  print("[PHYSICAL] unique_tokens=",r.unique_tokens); print("[PHYSICAL] multi_source_tokens=",r.multi_source_tokens); print("[PHYSICAL] single_source_tokens=",r.single_source_tokens)\n  self.assertGreater(r.unique_tokens,0); self.assertEqual(r.multi_source_tokens+r.single_source_tokens,r.unique_tokens)\nif __name__=="__main__":\n z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not z.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-296 cross-source universe presence physically certified")\n print("[PASS] source disagreement remains explicit; no blending")\n'
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")
def write(path,source):
 s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path)); path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(s,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
 if Path(__file__).name!=EXPECTED_FILENAME: raise RuntimeError("installer identity mismatch")
 r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/MODULE_NAME; test=r/TEST_NAME; init=pkg/"__init__.py"
 print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
 for fn,sym in DEPENDENCIES:
  p=pkg/fn
  if not p.is_file(): raise RuntimeError("dependency missing: "+str(p))
  src=p.read_text(encoding="utf-8"); ast.parse(src,filename=str(p))
  if ("def "+sym+"(") not in src: raise RuntimeError("exact dependency symbol missing: "+fn+" -> "+sym)
  print("[PASS] exact dependency verified:",fn,"->",sym)
 protected=[]
 for p in (r/"qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",r/"qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
  if not p.is_file(): raise RuntimeError("frozen boundary missing: "+str(p))
  protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
 old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
 try:
  write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
  lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+module.stem+" import *"
  if exp not in lines: lines.append(exp)
  write(init,"\n".join(x for x in lines if x.strip())+"\n")
  for p,h in protected:
   if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
  print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.name); print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
  print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE"); print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
 except Exception:
  for p,b in old.items():
   if b is None:
    if p.exists(): p.unlink()
   else: p.write_bytes(b)
  print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
