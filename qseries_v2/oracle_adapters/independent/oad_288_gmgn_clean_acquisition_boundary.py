from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
import json
from .oad_287_gmgn_clean_provider_foundation import require_gmgn_provider,run_gmgn_cli,GMGNRateLimitError
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class GMGNAcquisition:
 token_address:str; observed_at:datetime; payload:dict; execution_authority:bool=False
def _json(v):
 t=(v.decode("utf-8","replace") if isinstance(v,(bytes,bytearray)) else str(v or "")).strip()
 try:return json.loads(t)
 except Exception:
  a=t.find("{");b=t.rfind("}")
  if a>=0 and b>a:return json.loads(t[a:b+1])
 raise RuntimeError("GMGN output not valid JSON")
def _call(args,timeout=30.0):
 a=require_gmgn_provider();p=run_gmgn_cli(a.cli_path,args,timeout,False);out=(p.stdout or b"").decode("utf-8","replace");err=(p.stderr or b"").decode("utf-8","replace");d=(err or out).strip()
 if p.returncode!=0:
  if "429" in d.upper() or "RATE_LIMIT" in d.upper():raise GMGNRateLimitError("GMGN_RATE_LIMITED",300)
  raise RuntimeError("GMGN command failed rc="+str(p.returncode)+": "+d[:800])
 x=_json(p.stdout)
 if isinstance(x,dict) and str(x.get("code"))=="429":raise GMGNRateLimitError("GMGN_RATE_LIMITED",300)
 return x
def acquire_gmgn_token(token,timeout_seconds=30.0):
 token=str(token).strip()
 if not token:raise ValueError("token required")
 return GMGNAcquisition(token,datetime.now(timezone.utc),{"chain":"sol","info":_call(["token","info","--chain","sol","--address",token,"--raw"],timeout_seconds),"security":_call(["token","security","--chain","sol","--address",token,"--raw"],timeout_seconds),"pool":_call(["token","pool","--chain","sol","--address",token,"--raw"],timeout_seconds)},False)
def acquire_current_gmgn_token(timeout_seconds=30.0,candidate_limit=5):
 x=_call(["market","trending","--chain","sol","--interval","1h","--order-by","volume","--limit",str(max(1,int(candidate_limit))),"--raw"],timeout_seconds);rank=((x.get("data") or {}).get("rank") or []) if isinstance(x,dict) else [];errs=[]
 for row in rank:
  token=str((row or {}).get("address") or "").strip()
  if token:
   try:return acquire_gmgn_token(token,timeout_seconds)
   except GMGNRateLimitError:raise
   except Exception as e:errs.append(token+": "+str(e))
 raise RuntimeError("No GMGN candidate completed: "+" | ".join(errs[:5]))
