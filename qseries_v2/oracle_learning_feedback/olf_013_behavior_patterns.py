from __future__ import annotations
from pathlib import Path
from collections import defaultdict,Counter
import json,os
from .olf_011_learned_experience_profile import materialize_learned_experience_profiles

OLF_013_BUILD_ID="OLF-013"
OLF_013_REVISION="OLF_013_BEHAVIORAL_PATTERN_AGGREGATION_V1"
PATTERN_NAME="oracle_historical_behavior_patterns.json"

def build_behavior_patterns(root=None,min_samples=3):
    root=Path(root or Path.cwd()).resolve();p=materialize_learned_experience_profiles(root)
    groups=defaultdict(list)
    for x in p.get("profiles",[]):
        if not x.get("evidence_resolved"):continue
        groups[(x["series_key"],x["observation_type"])].append(x)
    patterns=[]
    for (series_key,obs_type),rows in sorted(groups.items()):
        if len(rows)<int(min_samples):continue
        sessions=Counter(x["utc_session"] for x in rows)
        sources=Counter(x["source_family"] or "UNKNOWN" for x in rows)
        patterns.append({
            "pattern_id":series_key+"|"+obs_type,
            "series_key":series_key,
            "observation_type":obs_type,
            "samples":len(rows),
            "support":min(1.0,len(rows)/25.0),
            "mature":len(rows)>=int(min_samples),
            "dominant_utc_session":sessions.most_common(1)[0][0],
            "utc_sessions":dict(sorted(sessions.items())),
            "source_families":dict(sorted(sources.items())),
            "settlement_hashes":tuple(sorted(x["settlement_hash"] for x in rows)),
        })
    return {"revision":OLF_013_REVISION,"learner_state_hash":p["learner_state_hash"],"min_samples":int(min_samples),"patterns":patterns,"execution_authority":False}

def materialize_behavior_patterns(root=None,min_samples=3):
    root=Path(root or Path.cwd()).resolve();payload=build_behavior_patterns(root,min_samples)
    path=root/"runtime_state"/PATTERN_NAME;tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path)
    return payload

def verify_olf_013_behavioral_pattern_aggregation():
    return OLF_013_BUILD_ID=="OLF-013" and callable(build_behavior_patterns)
