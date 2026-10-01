from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
QARB030=Path("run_qarb_030_mriya_dex_instruction_account_capture.py")
QARB049C=Path("run_qarb_049c_cpmm_connected_live_route_graph.py")
GEN_REPORT=Path("runtime_state/qseries/qarb_clean_bot/cpmm_connected_live_route_graph.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/continuous_fresh_mriya_multibase_hunter.json")

def _run(cmd):
    return subprocess.call(cmd)

def _load():
    if not GEN_REPORT.is_file(): return {}
    try:return json.loads(GEN_REPORT.read_text(encoding="utf-8"))
    except Exception:return {}

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--generation-seconds",type=float,default=90.0)
    ap.add_argument("--generations",type=int,default=4)
    ap.add_argument("--between-seconds",type=float,default=5.0)
    a=ap.parse_args(argv)

    root=Path.cwd()
    for p in (root/QARB030,root/QARB049C):
        if not p.is_file():raise SystemExit("[FAIL] dependency missing: "+str(p))

    history=[];best=None;total_signals=0
    print("[QARB-050] CONTINUOUS FRESH MRIYA MULTIBASE HUNTER",flush=True)
    print("[REFRESH] exact recent Mriya instruction capture before every generation",flush=True)
    print("[WINDOW] generation_seconds=%.1f generations=%d"%(a.generation_seconds,a.generations),flush=True)
    print("[MODE] PAPER_OBSERVATION=True execution_authority=FALSE",flush=True)

    for g in range(1,a.generations+1):
        print("\n[GENERATION_START] %d/%d"%(g,a.generations),flush=True)

        rc=_run([sys.executable,str(root/QARB030)])
        if rc!=0:
            print("[GENERATION_HOLD] QARB-030 refresh failed rc=%d; retaining prior exact capture"%rc,flush=True)

        try:GEN_REPORT.unlink(missing_ok=True)
        except Exception:pass

        rc=_run([sys.executable,str(root/QARB049C),"--seconds",str(a.generation_seconds)])
        row=_load()
        row["generation"]=g
        row["runner_rc"]=rc
        history.append(row)

        signals=int(row.get("signals") or 0);total_signals+=signals
        b=row.get("best")
        if isinstance(b,dict) and (best is None or float(b.get("net_sol") or -1e99)>float(best.get("net_sol") or -1e99)):
            best=dict(b);best["generation"]=g

        print("[GENERATION_RESULT] gen=%d rc=%d cpmm_pools=%s dlmm_bridges=%s cycles=%s signals=%s"%(
            g,rc,row.get("cpmm_pools"),row.get("dlmm_wsol_bridges"),row.get("cpmm_cycles"),row.get("signals")),flush=True)

        if g<a.generations and a.between_seconds>0:
            time.sleep(a.between_seconds)

    payload={"revision":"QARB_050","generations":history,"generation_count":len(history),
             "total_signals":total_signals,"best":best,
             "paper_only":True,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

    print("\n[SUPERVISOR_RESULT] generations=%d total_signals=%d"%(len(history),total_signals),flush=True)
    print("[BEST] "+("NONE" if best is None else json.dumps(best,sort_keys=True)),flush=True)
    print("[REPORT]",OUT,flush=True)
    print("[MODE] PAPER_OBSERVATION=True execution_authority=FALSE",flush=True)

if __name__=="__main__":main()
