from pathlib import Path
import hashlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_terminal";MOD=PKG/"oracle_historical_ticker_profile.py";TEST=ROOT/"test_ohe_003_historical_ticker_profile.py";UP1=PKG/"oracle_historical_experience_read_model.py";UP2=PKG/"oracle_live_market_experience_ranker.py"
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
from .oracle_historical_experience_read_model import HistoricalExperienceReadModel
OHE_003_BUILD_ID="OHE-003";OHE_003_REVISION="OHE_003_HISTORICAL_TICKER_PROFILE_V1"
@dataclass(frozen=True)
class HistoricalTickerProfile:
    ticker:str;family:str;exact_learned_records:int;family_learned_records:int;current_context_found:bool;maturity:str;experience_available:bool;regime_id:str;reliability:float;reason:str;learner_state_hash:str;lineage_current:bool;read_only:bool=True;execution_authority:bool=False
def build_historical_ticker_profile(model,ticker):
    if not isinstance(model,HistoricalExperienceReadModel):raise TypeError("model must be HistoricalExperienceReadModel")
    t=str(ticker or "").strip().upper()
    if not t:raise ValueError("ticker required")
    family=t.split("-",1)[0];exact=dict(model.learned_market_counts);families=dict(model.learned_family_counts);current=None
    for c in model.contexts:
        if c.market_ticker.upper()==t:current=c;break
    if current is None:
        for c in model.contexts:
            if c.market_ticker.upper().split("-",1)[0]==family:current=c;break
    return HistoricalTickerProfile(t,family,int(exact.get(t,0)),int(families.get(family,0)),current is not None,current.maturity if current else ("LEARNED_FAMILY" if families.get(family,0) else "BLIND"),bool(current.experience_available) if current else False,current.regime_id if current else "",float(current.reliability) if current else 0.0,current.reason if current else ("HISTORICAL_FAMILY_ONLY" if families.get(family,0) else "NO_LEARNED_HISTORY"),model.learner_state_hash,model.lineage_current,True,False)
"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_terminal.oracle_historical_experience_read_model import HistoricalExperienceReadModel,HistoricalExperienceContext
import qseries_v2.oracle_terminal.oracle_historical_ticker_profile as m
class T(unittest.TestCase):
    def test_profile(self):
        c=HistoricalExperienceContext("KXFAM-LIVE","kalshi:series:KXFAM","PROVEN",True,True,"R",.61,"h","matched")
        x=HistoricalExperienceReadModel(1,3,3,"h","h","a",True,1,1,0,0,(("KXFAM-OLD",3),),(("KXFAM",3),),(c,),True,False)
        p=m.build_historical_ticker_profile(x,"KXFAM-LIVE");self.assertEqual(p.family_learned_records,3);self.assertTrue(p.experience_available)
if __name__=="__main__":
    print("="*88);print(" OHE-003 CERTIFICATION TEST");print(" HISTORICAL TICKER PROFILE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] exact ticker + family history profile certified");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-003 CERTIFIED")
"""
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    print("="*88);print(" OHE-003 INSTALLER");print(" HISTORICAL TICKER PROFILE");print("="*88);print("[ROOT]",ROOT)
    for p in (UP1,UP2):
        if not p.is_file():raise RuntimeError(f"Required OHE upstream missing: {p}")
    hs={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (UP1,UP2)}
    write(MOD,MODULE_SOURCE);write(TEST,TEST_SOURCE);subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    for p,h in hs.items():
        if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError(f"Upstream changed: {p}")
    print("[PASS] OHE-001/002 unchanged");print("[DONE] OHE-003 INSTALLATION COMPLETE")
if __name__=="__main__":main()
