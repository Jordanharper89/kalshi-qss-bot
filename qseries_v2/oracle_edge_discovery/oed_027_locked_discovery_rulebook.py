
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
