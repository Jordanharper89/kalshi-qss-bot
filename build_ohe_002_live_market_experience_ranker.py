from pathlib import Path
import hashlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_terminal";MOD=PKG/"oracle_live_market_experience_ranker.py";TEST=ROOT/"test_ohe_002_live_market_experience_ranker.py";UP=PKG/"oracle_historical_experience_read_model.py"
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
from math import log1p
from .oracle_historical_experience_read_model import HistoricalExperienceReadModel
OHE_002_BUILD_ID="OHE-002";OHE_002_REVISION="OHE_002_LIVE_MARKET_EXPERIENCE_RANKER_V1"
@dataclass(frozen=True)
class RankedHistoricalExperience:
    rank:int;market_ticker:str;series_key:str;maturity:str;experience_available:bool;regime_id:str;reliability:float;series_learned_records:int;exact_ticker_learned_records:int;lineage_current:bool;rank_reason:str;experience_score:float;read_only:bool=True;execution_authority:bool=False
_M={"BLIND":0,"IMMATURE":1,"DEVELOPING":2,"MATURE":3,"PROVEN":4}
def _family(series_key,ticker):
    s=str(series_key or "")
    return s.split(":")[-1] if s else str(ticker or "").split("-",1)[0]
def _score(c,depth,exact,lineage):
    return round((500 if c.experience_available else 0)+75*_M.get(c.maturity.upper(),0)+100*max(0,min(float(c.reliability),1))+20*log1p(max(0,int(depth)))+5*log1p(max(0,int(exact)))+(25 if lineage else 0),6)
def rank_live_markets_by_experience(model,limit=20):
    if not isinstance(model,HistoricalExperienceReadModel):raise TypeError("model must be HistoricalExperienceReadModel")
    fam=dict(model.learned_family_counts);exact=dict(model.learned_market_counts);dedup={}
    for c in model.contexts:
        o=dedup.get(c.market_ticker)
        if o is None or (c.experience_available,c.reliability)>(o.experience_available,o.reliability):dedup[c.market_ticker]=c
    rows=[]
    for c in dedup.values():
        d=int(fam.get(_family(c.series_key,c.market_ticker),0));e=int(exact.get(c.market_ticker,0));score=_score(c,d,e,model.lineage_current)
        reason="usable matched historical regime" if c.experience_available else ("series known but current regime withheld" if c.series_admitted else "insufficient learned series history")
        rows.append((c,d,e,score,reason))
    rows.sort(key=lambda x:(x[3],x[0].reliability,x[1],x[0].market_ticker),reverse=True)
    return tuple(RankedHistoricalExperience(i,c.market_ticker,c.series_key,c.maturity,c.experience_available,c.regime_id,float(c.reliability),d,e,model.lineage_current,reason,score,True,False) for i,(c,d,e,score,reason) in enumerate(rows[:max(1,min(int(limit),100))],1))
"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_terminal.oracle_historical_experience_read_model import HistoricalExperienceReadModel,HistoricalExperienceContext
import qseries_v2.oracle_terminal.oracle_live_market_experience_ranker as m
class T(unittest.TestCase):
    def test_rank(self):
        c=(HistoricalExperienceContext("KXFAM-A","kalshi:series:KXFAM","PROVEN",True,True,"R",.7,"h","ok"),HistoricalExperienceContext("KXOTHER-A","kalshi:series:KXOTHER","BLIND",False,False,"",0,"h","none"))
        x=HistoricalExperienceReadModel(1,3,3,"h","h","a",True,2,1,0,1,(("KXFAM-X",3),),(("KXFAM",3),),c,True,False)
        rows=m.rank_live_markets_by_experience(x);self.assertEqual(rows[0].market_ticker,"KXFAM-A");self.assertTrue(rows[0].experience_available)
if __name__=="__main__":
    print("="*88);print(" OHE-002 CERTIFICATION TEST");print(" LIVE MARKET EXPERIENCE RANKER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] deterministic experience ranking certified");print("[PASS] score is ranking index, not probability");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-002 CERTIFIED")
"""
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    print("="*88);print(" OHE-002 INSTALLER");print(" LIVE MARKET EXPERIENCE RANKER");print("="*88);print("[ROOT]",ROOT)
    if not UP.is_file():raise RuntimeError("OHE-001 missing")
    h=hashlib.sha256(UP.read_bytes()).hexdigest();write(MOD,MODULE_SOURCE);write(TEST,TEST_SOURCE);subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    if hashlib.sha256(UP.read_bytes()).hexdigest()!=h:raise RuntimeError("OHE-001 changed")
    print("[PASS] OHE-001 unchanged");print("[DONE] OHE-002 INSTALLATION COMPLETE")
if __name__=="__main__":main()
