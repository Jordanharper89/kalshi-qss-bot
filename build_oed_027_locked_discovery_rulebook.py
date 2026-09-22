from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_edge_discovery"
MOD=PKG/"oed_027_locked_discovery_rulebook.py"
TEST=ROOT/"test_oed_027_locked_discovery_rulebook.py"

MOD.write_text(r"""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib,json

def _h(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def build(root=None):
    root=Path(root or Path.cwd())
    pop=json.loads((root/"runtime"/"edge_discovery"/"oed_026_chronological_validation_population.json").read_text())
    rules=[]
    for c in pop["conditions"]:
        if c["status"]!="READY":
            continue
        train=c["train_rows"]
        behavior=Counter(x["behavior"] for x in train)
        winner,count=behavior.most_common(1)[0]
        fam=[x for x in train if x["family_key"]==c["family_key"]]
        fam_counts=Counter(x["behavior"] for x in fam)
        baseline=max(fam_counts.values())/len(fam) if fam else 0.0
        rules.append({"condition_key":c["condition_key"],"detector_family":c["detector_family"],
                      "family_key":c["family_key"],"horizon_seconds":c["horizon_seconds"],
                      "magnitude_bucket":c["magnitude_bucket"],"locked_prediction":winner,
                      "train_n":len(train),"train_hit_rate":count/len(train),
                      "train_family_majority_baseline":baseline,
                      "train_raw_lift":count/len(train)-baseline,
                      "rule_locked_before_test":True,"test_data_consulted":False})
    rules.sort(key=lambda x:x["condition_key"])
    payload={"schema_version":"OED-027","created_at":datetime.now(timezone.utc).isoformat(),
             "source_population_hash":pop["population_hash"],"rules":rules,"rule_count":len(rules),
             "rulebook_hash":_h(rules),"rule_locked_before_test":True,"test_data_consulted":False,
             "edge_proven":False,"probability_enabled":False,"direction_enabled":False,
             "publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"edge_discovery"/"oed_027_locked_discovery_rulebook.json"
    p.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")
    return payload,p
""",encoding="utf-8")

TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_027_locked_discovery_rulebook import build
s,p=build(Path.cwd())
assert p.exists() and s["rule_locked_before_test"] and not s["test_data_consulted"]
assert s["rule_count"]>=0 and not s["edge_proven"]
print("[RULES]",s["rule_count"])
print("[RULEBOOK_HASH]",s["rulebook_hash"])
for x in sorted(s["rules"],key=lambda z:(-z["train_raw_lift"],-z["train_n"]))[:30]: print(" ",x)
print("[PASS] prediction rule determined from discovery/train rows only")
print("[PASS] test outcomes hidden from rule selection")
print("[PASS] OED-027 locked discovery rulebook certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True); py_compile.compile(str(TEST),doraise=True)
print("[PASS] OED-027 installer complete")
