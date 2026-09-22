from pathlib import Path
import ast,importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_026_full_page_coverage_admission.py'
TEST=ROOT/'test_opc_026_full_page_coverage_admission.py'
SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .opc_028_activity_tier_refresh_policy import classify_market_refresh_tier\nOPC_026_BUILD_ID="OPC-026"; OPC_026_REVISION="OPC_026_FRESHNESS_LIFECYCLE_ADMISSION_RECERTIFIED"\n@dataclass(frozen=True)\nclass FullPageCoverageAdmission:\n    page_markets:int; already_covered:int; missing_markets:int; admitted_tickers:tuple; full_page_mode:bool=True; execution_authority:bool=False\ndef _utc(v):\n    if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n    if v:return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    return None\ndef admit_full_page_coverage(markets,recent_tickers=None,*,freshness=None,now=None):\n    now=now or datetime.now(timezone.utc); recent={str(x) for x in (recent_tickers or ())}; freshness=freshness or {}\n    admitted=[]; covered=0; seen=set()\n    for row in markets:\n        if not isinstance(row,dict):continue\n        ticker=str(row.get("ticker") or "")\n        if not ticker or ticker in seen:continue\n        seen.add(ticker); tier=classify_market_refresh_tier(row,now); last=_utc(freshness.get(ticker))\n        fresh=bool(last and (now-last).total_seconds() < tier.refresh_seconds)\n        if freshness:\n            if fresh:covered+=1\n            else:admitted.append((tier.priority,ticker))\n        elif ticker in recent:covered+=1\n        else:admitted.append((tier.priority,ticker))\n    admitted.sort(key=lambda x:(-x[0],x[1]))\n    tickers=tuple(t for _,t in admitted)\n    return FullPageCoverageAdmission(len(seen),covered,len(tickers),tickers,True,False)\ndef verify_opc_026_full_page_coverage_admission():\n    now=datetime(2026,8,27,12,tzinfo=timezone.utc)\n    rows=({"ticker":"KXSOON","close_time":"2026-08-27T12:30:00Z"},{"ticker":"KXLATER","close_time":"2026-08-29T12:00:00Z"})\n    x=admit_full_page_coverage(rows,freshness={"KXSOON":"2026-08-27T11:58:00Z","KXLATER":"2026-08-27T11:58:00Z"},now=now)\n    return x.admitted_tickers==("KXSOON",) and x.already_covered==1 and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_026_full_page_coverage_admission as m\nclass T(unittest.TestCase):\n def test_contract(self):self.assertTrue(m.verify_opc_026_full_page_coverage_admission())\nif __name__=="__main__":unittest.main(verbosity=2)\n'
def write_atomic(p,s):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+f".{os.getpid()}.tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists(): p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88); print(' OPC-026 PAVEMENT REBUILD — FRESHNESS + LIFECYCLE ADMISSION'); print("="*88); print("[ROOT]",ROOT)
 before=TARGET.read_bytes() if TARGET.exists() else None; tb=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE); ast.parse(TEST_SOURCE); print("[PASS] payload syntax verified")
  write_atomic(TARGET,SOURCE); write_atomic(TEST,TEST_SOURCE); importlib.invalidate_caches()
  pass
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=180)
 except Exception:
  restore(TARGET,before); restore(TEST,tb); print("[ROLLBACK] failed; affected files restored"); raise
 print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
