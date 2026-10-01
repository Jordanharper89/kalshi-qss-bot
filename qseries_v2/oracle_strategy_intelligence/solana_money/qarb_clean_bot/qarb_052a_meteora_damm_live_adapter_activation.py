
from __future__ import annotations
import importlib.util, inspect, json, time
from pathlib import Path

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_AGE_MS=750.0

def _import_file(path:Path):
    name="_qarb052_"+path.stem+"_"+str(abs(hash(str(path))))[:8]
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError("IMPORT_SPEC_FAILED:"+str(path))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _candidate_modules(root:Path, needles):
    sub=root/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
    out=[]
    for p in sub.rglob("*.py"):
        low=p.name.lower()
        if any(n in low for n in needles) and not low.startswith(("build_","test_","run_")):
            out.append(p)
    return sorted(out)

def _sig(fn):
    try:return str(inspect.signature(fn))
    except Exception:return "?"

VENUE="METEORA_DAMM_V2"
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_052a_meteora_damm_activation.json")

def locate(root):
    rows=[]
    for p in _candidate_modules(Path(root),("damm","meteora")):
        try:m=_import_file(p)
        except Exception as e:
            rows.append({"file":str(p),"import_error":type(e).__name__+":"+str(e)});continue
        c={k:getattr(m,k,None) for k in ("discover","hydrate","update","quote")}
        rows.append({"file":str(p),"module":m,
                     "contract":{k:bool(callable(v)) for k,v in c.items()},
                     "signatures":{k:_sig(v) for k,v in c.items() if callable(v)}})
    return rows

def activate(root):
    root=Path(root)
    rows=locate(root)
    exact=[]
    for r in rows:
        m=r.get("module")
        if m and all(r["contract"].get(k) for k in ("discover","hydrate","update","quote")):
            exact.append((r,m))
    payload={"venue":VENUE,"candidate_files":[{k:v for k,v in r.items() if k!="module"} for r in rows],
             "exact_contract_count":len(exact),"activated":False,
             "descriptor_count":0,"hydrated_count":0,"execution_authority":False}
    if not exact:
        _write(root,payload);return payload

    # The adapter is activated only when the existing repo module itself can discover
    # descriptors and hydrate them with the repo-native account reader.
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
    chosen,m=exact[0]
    desc=list(m.discover(root))
    hydrated=[]
    for d in desc:
        try:
            s=m.hydrate(d,c.account)
            hydrated.append((d,s))
        except Exception:
            pass
    payload.update({"activated":bool(hydrated),"descriptor_count":len(desc),
                    "hydrated_count":len(hydrated),"selected_file":chosen["file"]})
    _write(root,payload)
    return payload

def _write(root,payload):
    p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

def main():
    p=activate(Path.cwd())
    print("[QARB-052A] METEORA DAMM V2 LIVE-ADAPTER ACTIVATION")
    print("[CONTRACTS] exact=%d descriptors=%d hydrated=%d"%(p["exact_contract_count"],p["descriptor_count"],p["hydrated_count"]))
    print("[ACTIVATED]",p["activated"])
    if not p["activated"]:
        print("[HOLD] existing DAMM adapter was not physically activatable; no fake quote path installed")
    print("[REPORT]",OUT)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
