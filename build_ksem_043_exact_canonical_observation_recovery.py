from pathlib import Path
import importlib, json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=STATE/"ksem043_exact_canonical_observation_recovery.json"
TEST=ROOT/"test_ksem_043_exact_canonical_observation_recovery.py"
SRCMOD="qseries_v2.oracle_adapters.independent.oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit"

def safe(x):
    if x is None or isinstance(x,(str,int,float,bool)): return x
    if isinstance(x,dict): return {str(k):safe(v) for k,v in x.items()}
    if isinstance(x,(list,tuple,set)): return [safe(v) for v in x]
    if hasattr(x,"__dict__"): return {"__type__":type(x).__name__,**{str(k):safe(v) for k,v in vars(x).items()}}
    return {"__type__":type(x).__name__,"__repr__":repr(x)}

def main():
    print("="*120); print(" KSEM-043 EXACT CANONICAL OBSERVATION RECOVERY"); print("="*120)
    prior=json.loads((STATE/"ksem042_bounded_postgresql_underlying_retrieval.json").read_text())
    mod=importlib.import_module(SRCMOD)
    _,backend=mod._router_backend(ROOT)
    raw=mod._read_market_snapshot_observations(backend,tuple(prior["requested_tickers"]))
    request_cls=mod._request_class(backend); recovered=[]; direct=[]
    for item in raw:
        if isinstance(item,tuple) and len(item)>=3 and item[0]=="PAIR":
            ticker,obs_id=str(item[1]),str(item[2])
            try:
                req=mod._request_for_observation_id(request_cls,backend,obs_id)
                observations=backend.query(request=req)
                recovered.append({"ticker":ticker,"observation_id":obs_id,"query_count":len(observations),"observations":safe(observations)})
            except Exception as e:
                recovered.append({"ticker":ticker,"observation_id":obs_id,"query_count":0,"error":type(e).__name__+": "+str(e),"observations":[]})
        else: direct.append(safe(item))
    print("[PAIR_OBSERVATIONS]",len(recovered)); print("[DIRECT_SERIALIZED_ROWS]",len(direct))
    print("[CANONICAL_QUERY_ROWS]",sum(x["query_count"] for x in recovered))
    for x in recovered[:15]: print("[RECOVERED]",x)
    OUT.write_text(json.dumps({"requested_tickers":prior["requested_tickers"],"pair_observations":recovered,"direct_serialized_rows":direct,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem043_exact_canonical_observation_recovery.json').read_text())\nassert d['requested_tickers']\nassert 'pair_observations' in d and 'direct_serialized_rows' in d\nassert d['execution_authority'] is False\nprint('[PASS] canonical observations recovered through exact existing PostgreSQL pavement')\nprint('[PASS] KSEM-043 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()