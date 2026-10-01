from __future__ import annotations
import inspect,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
OUT=Path("runtime_state/qseries/qarb_clean_bot/cpmm_discovery_boundary_capture.json")
def run(root):
    rc=m.rc
    print("[RC_MODULE]",rc.__name__)
    print("[RC_FILE]",getattr(rc,"__file__",None))
    for n in ("discover","hydrate","registry","update","quote"):
        o=getattr(rc,n,None)
        print("[RC_CALLABLE]",n,callable(o),None if not callable(o) else str(inspect.signature(o)))
        if callable(o):
            print("[SOURCE]",n)
            try: print(inspect.getsource(o))
            except Exception as e: print("[SOURCE_FAIL]",repr(e))
    rows=[]
    try:
        rows=list(rc.discover(Path(root)))
        print("[DISCOVER_COUNT]",len(rows))
        for x in rows[:20]: print("[DISCOVER_ROW]",repr(x))
    except Exception as e:
        print("[DISCOVER_ERROR]",type(e).__name__,str(e))
    d={"module":rc.__name__,"file":getattr(rc,"__file__",None),"discover_count":len(rows),
       "execution_authority":False,"read_only":True}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
    print("[REPORT]",OUT)
    print("[MODE] SOURCE_CAPTURE_ONLY execution_authority=FALSE")
    return d
if __name__=="__main__":
    run(Path.cwd())
