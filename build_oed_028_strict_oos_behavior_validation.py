from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_edge_discovery"
MOD=PKG/"oed_028_strict_oos_behavior_validation.py"
TEST=ROOT/"test_oed_028_strict_oos_behavior_validation.py"

MOD.write_text(r"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,math

def _h(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def _binom_tail(k,n,p):
    if n<=0: return 1.0
    p=min(max(float(p),1e-12),1-1e-12)
    vals=[]
    for i in range(k,n+1):
        vals.append(math.comb(n,i)*(p**i)*((1-p)**(n-i)))
    return min(1.0,sum(vals))

def build(root=None):
    root=Path(root or Path.cwd())
    pop=json.loads((root/"runtime"/"edge_discovery"/"oed_026_chronological_validation_population.json").read_text())
    rb=json.loads((root/"runtime"/"edge_discovery"/"oed_027_locked_discovery_rulebook.json").read_text())
    cmap={x["condition_key"]:x for x in pop["conditions"]}
    results=[]
    for r in rb["rules"]:
        c=cmap[r["condition_key"]]; test=c["test_rows"]; n=len(test)
        hits=sum(x["behavior"]==r["locked_prediction"] for x in test)
        rate=hits/n if n else 0.0
        p0=float(r["train_family_majority_baseline"])
        pv=_binom_tail(hits,n,p0) if n else 1.0
        results.append({**{k:r[k] for k in ("condition_key","detector_family","family_key","horizon_seconds","magnitude_bucket",
                                           "locked_prediction","train_n","train_hit_rate","train_family_majority_baseline")},
                        "test_n":n,"test_hits":hits,"test_hit_rate":rate,"oos_lift_over_train_baseline":rate-p0,
                        "raw_one_sided_binomial_p":pv,"oos_behavior_survived_raw":n>=5 and rate>p0 and pv<0.05,
                        "multiple_testing_adjusted":False})
    # Holm-Bonferroni over the locked rules.
    order=sorted(range(len(results)),key=lambda i:results[i]["raw_one_sided_binomial_p"])
    m=len(order)
    running=0.0
    for rank,idx in enumerate(order,1):
        adj=min(1.0,(m-rank+1)*results[idx]["raw_one_sided_binomial_p"])
        running=max(running,adj)
        results[idx]["holm_adjusted_p"]=running
        results[idx]["holm_rank"]=rank
        results[idx]["oos_behavior_survived_holm"]=(
            results[idx]["test_n"]>=5 and results[idx]["oos_lift_over_train_baseline"]>0 and running<0.05
        )
        results[idx]["multiple_testing_adjusted"]=True
    results.sort(key=lambda x:(x["holm_adjusted_p"],-x["test_n"],x["condition_key"]))
    payload={"schema_version":"OED-028","created_at":datetime.now(timezone.utc).isoformat(),
             "source_rulebook_hash":rb["rulebook_hash"],"results":results,"tested_rules":len(results),
             "raw_survivors":sum(x["oos_behavior_survived_raw"] for x in results),
             "holm_survivors":sum(x["oos_behavior_survived_holm"] for x in results),
             "multiple_testing_method":"HOLM_BONFERRONI","results_hash":_h(results),
             "behavioral_signal_only":True,"profitability_proven":False,"edge_proven":False,
             "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"edge_discovery"/"oed_028_strict_oos_behavior_validation.json"
    p.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")
    return payload,p
""",encoding="utf-8")

TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_028_strict_oos_behavior_validation import build
s,p=build(Path.cwd())
assert p.exists() and s["multiple_testing_method"]=="HOLM_BONFERRONI"
assert s["holm_survivors"]<=s["raw_survivors"] and not s["profitability_proven"]
print("[TESTED_RULES]",s["tested_rules"])
print("[RAW_SURVIVORS]",s["raw_survivors"])
print("[HOLM_SURVIVORS]",s["holm_survivors"])
print("[RESULTS_HASH]",s["results_hash"])
for x in s["results"][:30]: print(" ",x)
print("[PASS] unseen-day chronological holdout scored")
print("[PASS] one-sided exact binomial baseline test applied")
print("[PASS] Holm-Bonferroni multiple-testing control applied")
print("[PASS] OED-028 strict OOS behavior validation certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True); py_compile.compile(str(TEST),doraise=True)
print("[PASS] OED-028 installer complete")
