from __future__ import annotations
import ast,json,subprocess,sys
from pathlib import Path
def main():
 r=Path.cwd().resolve();l=r/"run_oracle_live.py";new="run_oad_290_gmgn_clean_continuous_intelligence_child.py";old="run_oad_284_gmgn_continuous_intelligence_production_child.py"
 s=l.read_text(encoding="utf-8")
 if f'"gmgn_intelligence": "{old}"' not in s:raise RuntimeError("expected old GMGN binding missing")
 backup=l.with_suffix(".py.oad291_pre_cutover_backup");backup.write_bytes(l.read_bytes())
 try:
  s=s.replace(f'"gmgn_intelligence": "{old}"',f'"gmgn_intelligence": "{new}"')
  s=s.replace("from qseries_v2.oracle_adapters.independent.oad_283_gmgn_continuous_runtime_checkpoint import load_gmgn_runtime_checkpoint as _load_gmgn_runtime_checkpoint","from qseries_v2.oracle_adapters.independent.oad_290_gmgn_clean_continuous_runtime import load_checkpoint as _load_gmgn_runtime_checkpoint")
  ast.parse(s);l.write_text(s,encoding="utf-8",newline="\n")
  q=subprocess.run([sys.executable,str(l),"--check"],cwd=r,text=True,capture_output=True,timeout=45)
  if q.returncode:raise RuntimeError(q.stdout+"\n"+q.stderr)
  manifest={"replacement":"OAD-287->OAD-291","active_runner":new,"delete_now":False,"retire_after_all_green":["oad_277","oad_278","oad_279","oad_281","oad_282","oad_283","oad_284",old],"preserve":["OAD-280 until migrated","OAD-261","OAD-068","OPH-023","all non-GMGN Oracle children"]}
  (r/"OAD_291_GMGN_REPLACEMENT_RETIREMENT_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
  print("[PASS] gmgn_intelligence cut over to OAD-290");print("[PASS] truthful health reads OAD-290 checkpoint");print("[PASS] old GMGN files retained only for rollback until all-green physical proof");print("[DONE] OAD-291 CUTOVER INSTALLED")
 except Exception:l.write_bytes(backup.read_bytes());print("[ROLLBACK] launcher restored");raise
if __name__=="__main__":main()
