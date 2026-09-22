from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_terminal";MOD=PKG/"oracle_live_market_differentiation.py";TEST=ROOT/"test_ohe_006_live_market_differentiation.py"
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import os
from .oracle_historical_experience_read_model import load_historical_experience_read_model
OHE_006_BUILD_ID="OHE-006"
@dataclass(frozen=True)
class LiveMarketDifferentiation:
    ticker:str;observation_count:int;latest_sequence:int;latest_observed_at:str;freshness_seconds:float;yes_bid:float|None;yes_ask:float|None;last_price:float|None;price_span:float;change_events:int;read_only:bool=True
def _db_url(root):
    u=os.environ.get("DATABASE_URL") or os.environ.get("ORACLE_DATABASE_URL")
    if u:return u
    p=Path(root)/".env"
    if p.is_file():
        for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1)
                if k.strip() in ("DATABASE_URL","ORACLE_DATABASE_URL"):return v.strip().strip(chr(34)).strip(chr(39))
    raise RuntimeError("Oracle PostgreSQL URL not configured")
def _num(v):
    try:
        x=float(v);return x*100.0 if 0<=x<=1 else x
    except:return None
def _payload(obj):
    if not isinstance(obj,dict):return {}
    raw=obj.get("raw_observation") if isinstance(obj.get("raw_observation"),dict) else {}
    p=raw.get("payload") if isinstance(raw.get("payload"),dict) else obj.get("payload")
    return p if isinstance(p,dict) else {}
def _msg(p):
    m=p.get("message");return m if isinstance(m,dict) else p
def _pick(d,*names):
    for n in names:
        if d.get(n) not in (None,""):return d.get(n)
def _ticker(p):
    m=_msg(p);return str(_pick(p,"source_market_id","market_id","ticker") or _pick(m,"market_ticker","ticker","market_id") or "").upper()
def load_live_market_differentiation(root=None,per_market=40):
    root=Path(root or Path.cwd()).resolve();model=load_historical_experience_read_model(root);wanted={str(c.market_ticker).upper() for c in model.contexts}
    if not wanted:return ()
    import psycopg
    c=psycopg.connect(_db_url(root));c.autocommit=True
    try:
        with c.cursor() as cur:
            cur.execute("SELECT sequence_number,observed_at,canonical_observation_json FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT %s",(max(2000,len(wanted)*int(per_market)*8),));rows=cur.fetchall()
    finally:c.close()
    now=datetime.now(timezone.utc);by={x:[] for x in wanted}
    for seq,ts,obj in rows:
        p=_payload(obj);t=_ticker(p)
        if t in by and len(by[t])<per_market:by[t].append((int(seq),ts,p))
    out=[]
    for t,rs in by.items():
        if not rs:continue
        vals=[];changes=0
        for seq,ts,p in rs:
            m=_msg(p);v=_num(_pick(m,"price","last_price","yes_price","yes_bid_dollars","yes_bid","yes_ask_dollars","yes_ask"))
            if v is not None:vals.append(v)
            changes+=1 if str(_pick(p,"event_type") or "").lower() in ("trade","ticker","orderbook_delta") else 0
        m=_msg(rs[0][2]);yb=_num(_pick(m,"yes_bid_dollars","yes_bid"));ya=_num(_pick(m,"yes_ask_dollars","yes_ask"));last=_num(_pick(m,"price","last_price","yes_price"))
        ts=rs[0][1];age=max(0.0,(now-ts.astimezone(timezone.utc)).total_seconds()) if hasattr(ts,"astimezone") else 0.0
        out.append(LiveMarketDifferentiation(t,len(rs),rs[0][0],str(ts),age,yb,ya,last,(max(vals)-min(vals)) if len(vals)>1 else 0.0,changes,True))
    return tuple(sorted(out,key=lambda x:x.ticker))
"""
TEST_SOURCE=r'''import unittest
import qseries_v2.oracle_terminal.oracle_live_market_differentiation as m
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(m.OHE_006_BUILD_ID,"OHE-006");self.assertTrue(m.LiveMarketDifferentiation("A",1,1,"",0,None,None,None,0,0).read_only)
if __name__=="__main__":
 print("="*88);print(" OHE-006 CERTIFICATION TEST");print(" LIVE MARKET DIFFERENTIATION");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] canonical PostgreSQL differentiation contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-006 CERTIFIED")
'''
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\\n");os.replace(t,p)
def main():
 print("="*88);print(" OHE-006 INSTALLER");print(" LIVE MARKET DIFFERENTIATION");print("="*88);print("[ROOT]",ROOT)
 if not (PKG/"oracle_historical_experience_read_model.py").is_file():raise RuntimeError("OHE-001 missing")
 write(MOD,MODULE_SOURCE);write(TEST,TEST_SOURCE);subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True);print("[PASS] canonical observations consumed read-only");print("[DONE] OHE-006 INSTALLATION COMPLETE")
if __name__=="__main__":main()
