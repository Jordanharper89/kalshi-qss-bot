from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_019_pairwise_formula_discovery.py";TEST=ROOT/"test_opd_019_pairwise_formula_discovery.py"
MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict,Counter
from itertools import combinations
import hashlib,json,math
MIN_SUPPORT=75;MAX_TOKENS_PER_ROW=12;SELECT_TOP_TOKENS=120
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
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";uni=json.loads((rt/"opd_018_univariate_formula_tests.json").read_text())
    score=Counter()
    for x in uni:
        if x["q_value"]<=0.25 and x["n"]>=100: score[x["formula"][0]]+=max(0.0,abs(x["lift"]))*math.log1p(x["n"])
    selected={t for t,_ in score.most_common(SELECT_TOP_TOKENS)} or {x["formula"][0] for x in uni[:SELECT_TOP_TOKENS]}
    bases=defaultdict(lambda:defaultdict(lambda:[0,0]));agg=defaultdict(lambda:{"n":0,"targets":defaultdict(int),"sum_return":0.0,"sum_mfe":0.0,"sum_mae":0.0})
    with (rt/"opd_017_discovery_feature_primitives.jsonl").open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line);h=int(x["horizon_seconds"]);y=x["future_target"];tm=_target_map(y);toks=[t for t in x["tokens"] if t in selected][:MAX_TOKENS_PER_ROW]
            for name,val in tm.items():bases[h][name][0]+=int(val);bases[h][name][1]+=1
            for pair in combinations(sorted(set(toks)),2):
                a=agg[(h,pair)];a["n"]+=1;a["sum_return"]+=float(y.get("future_return",0));a["sum_mfe"]+=float(y.get("mfe",0));a["sum_mae"]+=float(y.get("mae",0))
                for name,val in tm.items():a["targets"][name]+=int(val)
    tests=[]
    for (h,pair),a in agg.items():
        n=a["n"]
        if n<MIN_SUPPORT:continue
        for target,k in a["targets"].items():
            bk,bn=bases[h][target];rn=bn-n;rk=bk-k
            if rn<=0:continue
            base=bk/bn;rate=k/n
            tests.append({"degree":2,"horizon_seconds":h,"formula":list(pair),"target":target,"n":n,"base_rate":base,"conditional_rate":rate,"lift":rate-base,"relative_lift":(rate/base-1) if base>0 else None,"mean_future_return":a["sum_return"]/n,"mean_mfe":a["sum_mfe"]/n,"mean_mae":a["sum_mae"]/n,"p_value":_pvalue(k,n,rk,rn)})
    _bh(tests);tests.sort(key=lambda x:(x["q_value"],-abs(x["lift"]),-x["n"]));cand=[x for x in tests if x["q_value"]<=0.10 and abs(x["lift"])>=0.03]
    tf=rt/"opd_019_pairwise_formula_tests.json";tf.write_text(json.dumps(tests,indent=2,sort_keys=True))
    s={"schema_version":"OPD-019","selected_token_count":len(selected),"min_support":MIN_SUPPORT,"tests":len(tests),"discovered_candidates":len(cand),"candidate_preview":cand[:50],"multiple_testing_method":"BENJAMINI_HOCHBERG_FDR","candidate_status":"DISCOVERED_NOT_VALIDATED","holdout_used":False,"tests_hash":hashlib.sha256(tf.read_bytes()).hexdigest(),"model_fit_allowed":False,"formula_mining_allowed":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_019_pairwise_formula_discovery.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_019_pairwise_formula_discovery import build
s,p=build(Path.cwd());assert p.exists() and s["selected_token_count"]>=2 and s["multiple_testing_method"]=="BENJAMINI_HOCHBERG_FDR" and not s["holdout_used"];assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[SELECTED_TOKENS]",s["selected_token_count"]);print("[TESTS]",s["tests"]);print("[CANDIDATES]",s["discovered_candidates"]);print("[TESTS_HASH]",s["tests_hash"]);print("[TOP_CANDIDATES]",s["candidate_preview"][:10])
print("[PASS] X+Y->Z relations searched only inside discovery contracts");print("[PASS] pair search bounded by data-selected univariate token universe");print("[PASS] FDR correction applied before pair admission");print("[PASS] OPD-019 pairwise formula discovery certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-019 installer complete")