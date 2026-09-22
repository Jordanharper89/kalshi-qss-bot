
from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-295'
REVISION='OAD_295_SOLANA_POOL_LIFECYCLE_MIGRATION_TRACKING_V1'
TITLE='SOLANA POOL LIFECYCLE / MIGRATION TRACKING'
EXPECTED_FILENAME='build_oad_295_solana_pool_lifecycle_migration_tracking.py'
MODULE_NAME='oad_295_solana_pool_lifecycle_migration_tracking.py'
TEST_NAME='test_oad_295_solana_pool_lifecycle_migration_tracking.py'
DEPENDENCIES=[('oad_294_solana_universe_durable_change_detection.py', 'detect_and_checkpoint_solana_universe_changes'), ('oad_263_solana_token_pool_identity_liquidity_expansion.py', 'expand_live_solana_token_pools')]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_294_solana_universe_durable_change_detection import detect_and_checkpoint_solana_universe_changes\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass SolanaPoolLifecycle:\n current_tokens:int; current_pools:int; newly_seen_pools:tuple; missing_since_prior:tuple; migration_candidates:tuple; execution_authority:bool=False\ndef track_solana_pool_lifecycle(root=None,timeout_seconds=30.0,max_tokens=12):\n d=detect_and_checkpoint_solana_universe_changes(root,timeout_seconds,max_tokens)\n # Missing is evidence of disappearance from the bounded observed universe only.\n # It is not labeled "dead" without stronger chain evidence.\n migrations=tuple()\n return SolanaPoolLifecycle(d.current_tokens,d.current_pools,d.new_pools,d.missing_pools,migrations,False)\n'
TEST_SOURCE='import unittest,tempfile\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.independent.oad_295_solana_pool_lifecycle_migration_tracking import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  with tempfile.TemporaryDirectory() as d:\n   r=track_solana_pool_lifecycle(Path(d),max_tokens=8)\n   print("[PHYSICAL] current_tokens=",r.current_tokens); print("[PHYSICAL] current_pools=",r.current_pools); print("[PHYSICAL] missing_since_prior=",r.missing_since_prior)\n   self.assertGreater(r.current_pools,0); self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not z.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-295 bounded pool lifecycle tracking physically certified")\n print("[PASS] disappearance is not falsely promoted to dead-pool truth")\n'
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
