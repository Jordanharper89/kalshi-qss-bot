from pathlib import Path
import hashlib, os, subprocess, sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_terminal"
MOD=PKG/"oracle_historical_experience_read_model.py";TEST=ROOT/"test_ohe_001_historical_experience_read_model.py"
OLR=ROOT/"qseries_v2"/"oracle_learning_runtime"/"olr_016_production_learned_state_adapter.py"
OLF=ROOT/"qseries_v2"/"oracle_learning_feedback"/"olf_030_breadth_aware_reasoning_runtime.py"
RUNNER=ROOT/"run_oracle_open_intelligence_terminal.py"
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import hashlib,json
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state
OHE_001_BUILD_ID="OHE-001";OHE_001_REVISION="OHE_001_HISTORICAL_EXPERIENCE_READ_MODEL_V1"
ATTESTATION_NAME="oracle_learning_breadth_reasoning_attestation.json"
@dataclass(frozen=True)
class HistoricalExperienceContext:
    market_ticker:str;series_key:str;maturity:str;series_admitted:bool;experience_available:bool;regime_id:str;reliability:float;learner_state_hash:str;reason:str
@dataclass(frozen=True)
class HistoricalExperienceReadModel:
    cycles:int;outcomes_learned:int;learned_records:int;learner_state_hash:str;attestation_state_hash:str;attestation_hash:str;lineage_current:bool;markets_reasoned:int;experience_contexts:int;withheld_contexts:int;blind_contexts:int;learned_market_counts:tuple;learned_family_counts:tuple;contexts:tuple;read_only:bool=True;execution_authority:bool=False
def _load_json(path):
    p=Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
def _family(t):return str(t or "").split("-",1)[0] or "UNKNOWN"
def _ctx(r):
    return HistoricalExperienceContext(str(r.get("market_ticker") or ""),str(r.get("series_key") or ""),str(r.get("maturity") or "BLIND"),bool(r.get("series_admitted",False)),bool(r.get("experience_available",False)),str(r.get("regime_id") or ""),float(r.get("reliability") or 0.0),str(r.get("learner_state_hash") or ""),str(r.get("reason") or ""))
def load_historical_experience_read_model(root=None):
    root=Path(root or Path.cwd()).resolve();learned=load_production_learned_state(root)
    ap=root/"runtime_state"/ATTESTATION_NAME;att=_load_json(ap);raw=att.get("contexts",[]) if isinstance(att,dict) else []
    if not isinstance(raw,list):raw=[]
    contexts=tuple(_ctx(x) for x in raw if isinstance(x,dict));families=Counter()
    for ticker,count in learned.learned_market_counts:families[_family(ticker)]+=int(count)
    ah=str(att.get("learner_state_hash") or "") if isinstance(att,dict) else ""
    return HistoricalExperienceReadModel(int(learned.cycles),int(learned.outcomes_learned),int(learned.learned_records),str(learned.learner_state_hash),ah,hashlib.sha256(ap.read_bytes()).hexdigest() if ap.is_file() else "",bool(ah and ah==str(learned.learner_state_hash)),int(att.get("markets_reasoned",0)) if isinstance(att,dict) else 0,int(att.get("experience_contexts",0)) if isinstance(att,dict) else 0,int(att.get("withheld_contexts",0)) if isinstance(att,dict) else 0,int(att.get("blind_contexts",0)) if isinstance(att,dict) else 0,tuple(learned.learned_market_counts),tuple(sorted(families.items())),contexts,True,False)
def verify_historical_experience_read_model(x):
    if not x.read_only or x.execution_authority:raise RuntimeError("OHE read-only boundary violation")
    if x.learned_records<0 or x.outcomes_learned<0:raise RuntimeError("invalid learner counts")
    return True
"""
TEST_SOURCE=r"""import json,tempfile,unittest
from pathlib import Path
import qseries_v2.oracle_terminal.oracle_historical_experience_read_model as m
class T(unittest.TestCase):
    def test_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);s=r/"runtime_state";s.mkdir()
            (s/"oracle_learning_runtime_state.json").write_text(json.dumps({"cycles":3,"outcomes_learned":4,"ocl_state":{"applied_through_sequence":4,"state_hash":"abc"}}),encoding="utf-8")
            (s/"oracle_learning_event_ledger.json").write_text(json.dumps({"1":{"status":"learned","ticker":"KXFAM-A"},"2":{"status":"learned","ticker":"KXFAM-B"}}),encoding="utf-8")
            (s/m.ATTESTATION_NAME).write_text(json.dumps({"learner_state_hash":"abc","markets_reasoned":1,"experience_contexts":1,"withheld_contexts":0,"blind_contexts":0,"contexts":[{"market_ticker":"KXFAM-LIVE","series_key":"kalshi:series:KXFAM","maturity":"PROVEN","series_admitted":True,"experience_available":True,"regime_id":"R1","reliability":0.7,"learner_state_hash":"abc","reason":"MATURE_SERIES_AND_MATCHED_REGIME"}]}),encoding="utf-8")
            x=m.load_historical_experience_read_model(r);self.assertTrue(m.verify_historical_experience_read_model(x));self.assertTrue(x.lineage_current);self.assertEqual(dict(x.learned_family_counts)["KXFAM"],2)
if __name__=="__main__":
    print("="*88);print(" OHE-001 CERTIFICATION TEST");print(" HISTORICAL EXPERIENCE READ MODEL");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OLR-016 + OLF-030 read-only consumption certified");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-001 CERTIFIED")
"""
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    print("="*88);print(" OHE-001 INSTALLER");print(" HISTORICAL EXPERIENCE READ MODEL");print("="*88);print("[ROOT]",ROOT)
    for p in (OLR,OLF,RUNNER):
        if not p.is_file():raise RuntimeError(f"Required proven upstream missing: {p}")
    protected={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (OLR,OLF,RUNNER)}
    write(MOD,MODULE_SOURCE);write(TEST,TEST_SOURCE);subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    for p,h in protected.items():
        if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError(f"Protected upstream changed: {p}")
    sys.path.insert(0,str(ROOT));from qseries_v2.oracle_terminal.oracle_historical_experience_read_model import load_historical_experience_read_model
    x=load_historical_experience_read_model(ROOT);print(f"[PHYSICAL] cycles={x.cycles} outcomes={x.outcomes_learned} learned_records={x.learned_records} contexts={len(x.contexts)} lineage_current={x.lineage_current}")
    print("[PASS] frozen OLR/OLF/OIT unchanged");print("[DONE] OHE-001 INSTALLATION COMPLETE")
if __name__=="__main__":main()
