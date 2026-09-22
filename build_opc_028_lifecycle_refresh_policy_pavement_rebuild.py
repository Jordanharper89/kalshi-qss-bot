from pathlib import Path
import ast,importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_028_activity_tier_refresh_policy.py'
TEST=ROOT/'test_opc_028_activity_tier_refresh_policy.py'
SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\n\nOPC_028_BUILD_ID="OPC-028"\nOPC_028_REVISION="OPC_028_LIFECYCLE_AWARE_REFRESH_POLICY_RECERTIFIED"\n@dataclass(frozen=True)\nclass CoverageRefreshTier:\n    tier:str; refresh_seconds:int; priority:int; execution_authority:bool=False\ndef _dt(v):\n    if not v:return None\n    try:\n        d=datetime.fromisoformat(str(v).replace("Z","+00:00")); return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\n    except Exception:return None\ndef classify_market_refresh_tier(market,now=None):\n    if not isinstance(market,dict):return CoverageRefreshTier("QUIET",21600,10,False)\n    now=now or datetime.now(timezone.utc)\n    close=_dt(market.get("close_time") or market.get("expiration_time"))\n    if close:\n        sec=(close-now).total_seconds()\n        if sec<=3600:return CoverageRefreshTier("SETTLEMENT_IMMINENT",60,120,False)\n        if sec<=21600:return CoverageRefreshTier("CLOSING_SOON",300,110,False)\n        if sec<=86400:return CoverageRefreshTier("PRE_SETTLEMENT",900,100,False)\n    volume=float(market.get("volume_fp") or market.get("volume") or 0); v24=float(market.get("volume_24h_fp") or market.get("volume_24h") or 0); oi=float(market.get("open_interest_fp") or market.get("open_interest") or 0)\n    if v24>=10000 or volume>=10000:return CoverageRefreshTier("ULTRA_HOT",60,100,False)\n    if v24>=1000 or volume>=1000:return CoverageRefreshTier("HOT",300,80,False)\n    if v24>0 or volume>0 or oi>0:return CoverageRefreshTier("ACTIVE",1800,50,False)\n    return CoverageRefreshTier("QUIET",21600,10,False)\ndef rank_markets_by_refresh_priority(markets,now=None):\n    rows=[]\n    for row in markets:\n        if not isinstance(row,dict) or not row.get("ticker"):continue\n        tier=classify_market_refresh_tier(row,now); rows.append((tier.priority,str(row["ticker"]),tier))\n    rows.sort(key=lambda x:(-x[0],x[1])); return tuple((t,tier) for _,t,tier in rows)\ndef verify_opc_028_activity_tier_refresh_policy():\n    now=datetime(2026,8,27,12,0,tzinfo=timezone.utc)\n    a=classify_market_refresh_tier({"close_time":"2026-08-27T12:30:00Z"},now)\n    b=classify_market_refresh_tier({"close_time":"2026-08-27T16:00:00Z"},now)\n    c=classify_market_refresh_tier({"volume_24h":20000},now)\n    return a.tier=="SETTLEMENT_IMMINENT" and b.tier=="CLOSING_SOON" and c.tier=="ULTRA_HOT" and not a.execution_authority\n'
TEST_SOURCE='import unittest\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_028_activity_tier_refresh_policy as m\nclass T(unittest.TestCase):\n def test_policy(self):\n  self.assertTrue(m.verify_opc_028_activity_tier_refresh_policy())\n  now=datetime(2026,8,27,12,tzinfo=timezone.utc)\n  self.assertEqual(m.classify_market_refresh_tier({"close_time":"2026-08-27T12:45:00Z"},now).refresh_seconds,60)\nif __name__=="__main__":unittest.main(verbosity=2)\n'
def write_atomic(p,s):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+f".{os.getpid()}.tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists(): p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88); print(' OPC-028 PAVEMENT REBUILD — LIFECYCLE-AWARE REFRESH POLICY'); print("="*88); print("[ROOT]",ROOT)
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
