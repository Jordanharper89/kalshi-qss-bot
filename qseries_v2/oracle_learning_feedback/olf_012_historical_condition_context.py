from __future__ import annotations
from pathlib import Path
from collections import Counter
import json,os
from .olf_011_learned_experience_profile import materialize_learned_experience_profiles

OLF_012_BUILD_ID="OLF-012"
OLF_012_REVISION="OLF_012_HISTORICAL_CONDITION_CONTEXT_V1"
CONTEXT_NAME="oracle_historical_condition_context.json"

def build_historical_condition_context(root=None):
    root=Path(root or Path.cwd()).resolve()
    p=materialize_learned_experience_profiles(root)
    groups={}
    for x in p.get("profiles",[]):
        if not x.get("evidence_resolved"):continue
        groups.setdefault(x["series_key"],[]).append(x)
    series={}
    for key,rows in sorted(groups.items()):
        types=Counter(str(x.get("observation_type") or "UNKNOWN") for x in rows)
        sessions=Counter(str(x.get("utc_session") or "UNKNOWN") for x in rows)
        sources=Counter(str(x.get("source_family") or "UNKNOWN") for x in rows)
        series[key]={
            "evidence_records":len(rows),
            "observation_types":dict(sorted(types.items())),
            "utc_sessions":dict(sorted(sessions.items())),
            "source_families":dict(sorted(sources.items())),
            "dominant_observation_type":types.most_common(1)[0][0] if types else "UNKNOWN",
            "dominant_utc_session":sessions.most_common(1)[0][0] if sessions else "UNKNOWN",
        }
    return {"revision":OLF_012_REVISION,"learner_state_hash":p["learner_state_hash"],"series":series,"execution_authority":False}

def materialize_historical_condition_context(root=None):
    root=Path(root or Path.cwd()).resolve();payload=build_historical_condition_context(root)
    path=root/"runtime_state"/CONTEXT_NAME;tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\n");os.replace(tmp,path)
    return payload

def verify_olf_012_historical_condition_context():
    return OLF_012_BUILD_ID=="OLF-012" and callable(build_historical_condition_context)
