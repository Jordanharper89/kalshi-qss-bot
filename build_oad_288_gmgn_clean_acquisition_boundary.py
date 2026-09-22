from __future__ import annotations
import ast,os,textwrap,hashlib
from pathlib import Path
EXPECTED='build_oad_288_gmgn_clean_acquisition_boundary.py'
MODULE='oad_288_gmgn_clean_acquisition_boundary.py'
TEST='test_oad_288_gmgn_clean_acquisition_boundary.py'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nimport json\nfrom .oad_287_gmgn_clean_provider_foundation import require_gmgn_provider,run_gmgn_cli,GMGNRateLimitError\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass GMGNAcquisition:\n token_address:str; observed_at:datetime; payload:dict; execution_authority:bool=False\ndef _json(v):\n t=(v.decode("utf-8","replace") if isinstance(v,(bytes,bytearray)) else str(v or "")).strip()\n try:return json.loads(t)\n except Exception:\n  a=t.find("{");b=t.rfind("}")\n  if a>=0 and b>a:return json.loads(t[a:b+1])\n raise RuntimeError("GMGN output not valid JSON")\ndef _call(args,timeout=30.0):\n a=require_gmgn_provider();p=run_gmgn_cli(a.cli_path,args,timeout,False);out=(p.stdout or b"").decode("utf-8","replace");err=(p.stderr or b"").decode("utf-8","replace");d=(err or out).strip()\n if p.returncode!=0:\n  if "429" in d.upper() or "RATE_LIMIT" in d.upper():raise GMGNRateLimitError("GMGN_RATE_LIMITED",300)\n  raise RuntimeError("GMGN command failed rc="+str(p.returncode)+": "+d[:800])\n x=_json(p.stdout)\n if isinstance(x,dict) and str(x.get("code"))=="429":raise GMGNRateLimitError("GMGN_RATE_LIMITED",300)\n return x\ndef acquire_gmgn_token(token,timeout_seconds=30.0):\n token=str(token).strip()\n if not token:raise ValueError("token required")\n return GMGNAcquisition(token,datetime.now(timezone.utc),{"chain":"sol","info":_call(["token","info","--chain","sol","--address",token,"--raw"],timeout_seconds),"security":_call(["token","security","--chain","sol","--address",token,"--raw"],timeout_seconds),"pool":_call(["token","pool","--chain","sol","--address",token,"--raw"],timeout_seconds)},False)\ndef acquire_current_gmgn_token(timeout_seconds=30.0,candidate_limit=5):\n x=_call(["market","trending","--chain","sol","--interval","1h","--order-by","volume","--limit",str(max(1,int(candidate_limit))),"--raw"],timeout_seconds);rank=((x.get("data") or {}).get("rank") or []) if isinstance(x,dict) else [];errs=[]\n for row in rank:\n  token=str((row or {}).get("address") or "").strip()\n  if token:\n   try:return acquire_gmgn_token(token,timeout_seconds)\n   except GMGNRateLimitError:raise\n   except Exception as e:errs.append(token+": "+str(e))\n raise RuntimeError("No GMGN candidate completed: "+" | ".join(errs[:5]))\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_288_gmgn_clean_acquisition_boundary import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=acquire_current_gmgn_token();print("[GMGN] token=",x.token_address);print("[GMGN] sections=",tuple(x.payload));self.assertTrue(x.token_address);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));raise SystemExit(0 if r.wasSuccessful() else 1)\n'
def root():
 for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
  for p in (b,*b.parents):
   if (p/"qseries_v2").is_dir(): return p
 raise RuntimeError("Q Series repository root not found")
def write(p,s):
 s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
 if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
 r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
 for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
  if not (r/rel).is_file(): raise RuntimeError("frozen boundary missing: "+rel)
 write(pkg/MODULE,MODULE_SOURCE); write(r/TEST,TEST_SOURCE)
 
 print("[PASS] installed:",MODULE); print("[PASS] frozen OPH-023/Kalshi OAD-055 preserved"); print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE"); print("[DONE] installation complete")
if __name__=="__main__": main()
