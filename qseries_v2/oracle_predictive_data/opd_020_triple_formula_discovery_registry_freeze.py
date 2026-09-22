
from pathlib import Path
from collections import defaultdict,Counter
from itertools import combinations
import hashlib,json,math
MIN_SUPPORT=60;MAX_TOKENS_PER_ROW=10;SELECT_TOP_TOKENS=60

def _target_map(y):
    return {"UP_5C":bool(y.get("hit_plus_05")),"DOWN_5C":bool(y.get("hit_minus_05")),"UP_10C":bool(y.get("hit_plus_10")),"DOWN_10C":bool(y.get("hit_minus_10")),"RETURN_POS":float(y.get("future_return",0))>0,"RETURN_NEG":float(y.get("future_return",0))<0}
def _pvalue(k,n,k0,n0):
    if n<=0 or n0<=0:return 1.0
    p1=k/n;p0=k0/n0;p=(k+k0)/(n+n0);se=math.sqrt(max(1e-18,p*(1-p)*(1/n+1/n0)));z=(p1-p0)/se
    return math.erfc(abs(z)/math.sqrt(2))
def _bh(rows):
    m=len(rows);order=sorted(range(m),key=lambda i:rows[i]["p_value"]);qprev=1.0
    for rr,i in enumerate(reversed(order),1):
        rank=m-rr+1;q=min(qprev,rows[i]["p_value"]*m/rank);rows[i]["q_value"]=min(1.0,q);qprev=q
    return rows

def _load(p): return json.loads(p.read_text(encoding="utf-8"))
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";pairs=_load(rt/"opd_019_pairwise_formula_tests.json")
    score=Counter()
    for x in pairs:
        if x["q_value"]<=0.25 and x["n"]>=75:
            for t in x["formula"]:score[t]+=max(0.0,abs(x["lift"]))*math.log1p(x["n"])
    selected={t for t,_ in score.most_common(SELECT_TOP_TOKENS)}
    if len(selected)<3:
        for x in pairs[:100]:
            selected.update(x["formula"])
            if len(selected)>=3:break
    bases=defaultdict(lambda:defaultdict(lambda:[0,0]));agg=defaultdict(lambda:{"n":0,"targets":defaultdict(int),"sum_return":0.0,"sum_mfe":0.0,"sum_mae":0.0,"sum_tmax":0.0,"sum_tmin":0.0})
    with (rt/"opd_017_discovery_feature_primitives.jsonl").open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line);h=int(x["horizon_seconds"]);y=x["future_target"];tm=_target_map(y);toks=[t for t in x["tokens"] if t in selected][:MAX_TOKENS_PER_ROW]
            for name,val in tm.items():bases[h][name][0]+=int(val);bases[h][name][1]+=1
            for tri in combinations(sorted(set(toks)),3):
                a=agg[(h,tri)];a["n"]+=1;a["sum_return"]+=float(y.get("future_return",0));a["sum_mfe"]+=float(y.get("mfe",0));a["sum_mae"]+=float(y.get("mae",0));a["sum_tmax"]+=float(y.get("time_to_max_seconds",0));a["sum_tmin"]+=float(y.get("time_to_min_seconds",0))
                for name,val in tm.items():a["targets"][name]+=int(val)
    tests=[]
    for (h,tri),a in agg.items():
        n=a["n"]
        if n<MIN_SUPPORT:continue
        for target,k in a["targets"].items():
            bk,bn=bases[h][target];rn=bn-n;rk=bk-k
            if rn<=0:continue
            base=bk/bn;rate=k/n
            tests.append({"degree":3,"horizon_seconds":h,"formula":list(tri),"target":target,"n":n,"base_rate":base,"conditional_rate":rate,"lift":rate-base,"relative_lift":(rate/base-1) if base>0 else None,"mean_future_return":a["sum_return"]/n,"mean_mfe":a["sum_mfe"]/n,"mean_mae":a["sum_mae"]/n,"mean_time_to_max_seconds":a["sum_tmax"]/n,"mean_time_to_min_seconds":a["sum_tmin"]/n,"p_value":_pvalue(k,n,rk,rn)})
    _bh(tests);tests.sort(key=lambda x:(x["q_value"],-abs(x["lift"]),-x["n"]));tf=rt/"opd_020_triple_formula_tests.json";tf.write_text(json.dumps(tests,indent=2,sort_keys=True))
    allc=[]
    for degree,fn,cut in [(1,"opd_018_univariate_formula_tests.json",0.02),(2,"opd_019_pairwise_formula_tests.json",0.03),(3,"opd_020_triple_formula_tests.json",0.04)]:
        for x in _load(rt/fn):
            if x.get("q_value",1)<=0.10 and abs(x.get("lift",0))>=cut:
                z=dict(x);z["status"]="DISCOVERED";z["holdout_tested"]=False;z["edge_certified"]=False;z["formula_id"]=hashlib.sha256(json.dumps([degree,z["horizon_seconds"],z["formula"],z["target"]],sort_keys=True).encode()).hexdigest()[:24];allc.append(z)
    allc.sort(key=lambda x:(x["q_value"],-abs(x["lift"]),-x["n"],x["degree"]))
    reg={"schema_version":"OPD-020","status":"DISCOVERY_REGISTRY_FROZEN","candidate_count":len(allc),"degree_counts":dict(Counter(str(x["degree"]) for x in allc)),"candidates":allc,"holdout_contracts_used":False,"edge_certified_count":0,"validation_next":"OPD-021_PLUS_CONTRACT_ISOLATED_HOLDOUT_VALIDATION","multiple_testing_method":"BENJAMINI_HOCHBERG_FDR_WITHIN_DEGREE_DISCOVERY_FAMILIES","model_fit_allowed":False,"formula_mining_allowed":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    rf=rt/"opd_020_formula_discovery_registry.json";rf.write_text(json.dumps(reg,indent=2,sort_keys=True))
    tri=[x for x in tests if x["q_value"]<=0.10 and abs(x["lift"])>=0.04]
    s={"schema_version":"OPD-020","selected_token_count":len(selected),"triple_tests":len(tests),"triple_candidates":len(tri),"registry_candidates":len(allc),"degree_counts":reg["degree_counts"],"edge_certified_count":0,"holdout_contracts_used":False,"registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"next_required":reg["validation_next"],"model_fit_allowed":False,"formula_mining_allowed":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_020_triple_formula_discovery_registry_freeze.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
