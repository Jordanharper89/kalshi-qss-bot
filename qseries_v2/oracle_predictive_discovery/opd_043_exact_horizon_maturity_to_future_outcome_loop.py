from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_039_durable_horizon_maturity_queue import rebuild,mature
from qseries_v2.oracle_predictive_data.opd_033_prospective_future_outcome_resolver import resolve

execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _items(value):
    if value is None: return []
    if isinstance(value,(list,tuple)): return list(value)
    if isinstance(value,dict):
        lists=[v for v in value.values() if isinstance(v,list)]
        if len(lists)==1: return list(lists[0])
        if len(value)==0: return []
        raise TypeError("OPD-039 mature(root) dict must expose exactly one list-valued mature collection")
    raise TypeError("unsupported OPD-039 mature(root) result type: "+type(value).__name__)

def rebuild_queue(root=None):
    root=Path(root or Path.cwd()).resolve()
    return rebuild(root)

def resolve_mature_once(root=None,now=None):
    root=Path(root or Path.cwd()).resolve()
    due=_items(mature(root,now))
    results=[]
    for outcome in due:
        results.append(resolve(outcome,root))
    return {"mature_count":len(due),"resolved_count":len(results),"results":results}
