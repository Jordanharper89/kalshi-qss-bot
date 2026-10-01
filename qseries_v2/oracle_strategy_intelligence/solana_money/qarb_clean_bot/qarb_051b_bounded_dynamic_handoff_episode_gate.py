from __future__ import annotations
import asyncio,hashlib,json,subprocess,sys,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_049c_cpmm_connected_live_route_graph as q

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
RECENT=Path("runtime_state/qseries/qarb_clean_bot/mriya_recent_transactions.json")
CAPTURE=Path("runtime_state/qseries/qarb_clean_bot/mriya_dex_instruction_accounts.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_051b_bounded_dynamic_handoff_episode_gate.json")
EPISODE_COOLDOWN_S=2.0
REPRICE_BPS=5.0

def _rows(obj):
    if isinstance(obj,list): return obj
    if isinstance(obj,dict):
        for k in ("rows","records","transactions","instructions"):
            if isinstance(obj.get(k),list): return obj[k]
    return []

def _state(path):
    p=Path(path)
    if not p.is_file(): return {"exists":False,"rows":0,"max_slot":None,"sha":None}
    raw=p.read_bytes()
    try: obj=json.loads(raw.decode("utf-8"))
    except Exception: obj={}
    rows=_rows(obj)
    slots=[]
    for r in rows:
        if isinstance(r,dict) and r.get("slot") is not None:
            try: slots.append(int(r["slot"]))
            except Exception: pass
    return {"exists":True,"rows":len(rows),"max_slot":max(slots) if slots else None,
            "sha":hashlib.sha256(raw).hexdigest()}

def _one(root,pattern):
    xs=sorted(Path(root).glob(pattern))
    if len(xs)!=1: raise RuntimeError("EXPECTED_ONE:%s found=%s"%(pattern,[x.name for x in xs]))
    return xs[0]

def bounded_043b(root,seconds):
    runner=_one(root,"run_qarb_043b*.py")
    print("[DYNAMIC_SOURCE] %s bounded_seconds=%.1f"%(runner.name,seconds),flush=True)
    proc=subprocess.Popen([sys.executable,str(runner)])
    deadline=time.monotonic()+float(seconds)
    while time.monotonic()<deadline and proc.poll() is None:
        time.sleep(.25)
    if proc.poll() is None:
        print("[DYNAMIC_BOUNDARY] acquisition window complete; terminating child",flush=True)
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill();proc.wait(timeout=5)
    print("[DYNAMIC_EXIT] rc=%s"%proc.returncode,flush=True)
    return proc.returncode

def refresh_handoff(root,dynamic_seconds):
    root=Path(root)
    recent_before=_state(root/RECENT)
    capture_before=_state(root/CAPTURE)

    bounded_043b(root,dynamic_seconds)

    r027=root/"run_qarb_027_mriya_native_wallet_observer.py"
    r030=root/"run_qarb_030_mriya_dex_instruction_account_capture.py"
    if not r027.is_file(): raise RuntimeError("MISSING:"+str(r027))
    if not r030.is_file(): raise RuntimeError("MISSING:"+str(r030))

    print("[HANDOFF] refreshing QARB-027 native wallet observer",flush=True)
    rc27=subprocess.call([sys.executable,str(r027),"--limit","40"])
    if rc27!=0: raise RuntimeError("QARB_027_FAILED:%d"%rc27)
    recent_after=_state(root/RECENT)

    print("[HANDOFF] decoding fresh QARB-027 transactions through QARB-030",flush=True)
    rc30=subprocess.call([sys.executable,str(r030)])
    if rc30!=0: raise RuntimeError("QARB_030_FAILED:%d"%rc30)
    capture_after=_state(root/CAPTURE)

    recent_progress=bool(
      recent_before["sha"]!=recent_after["sha"] or
      (recent_before["max_slot"] is not None and recent_after["max_slot"] is not None
       and recent_after["max_slot"]>recent_before["max_slot"]))
    capture_progress=bool(
      capture_before["sha"]!=capture_after["sha"] or
      (capture_before["max_slot"] is not None and capture_after["max_slot"] is not None
       and capture_after["max_slot"]>capture_before["max_slot"]))

    print("[QARB027_PROGRESS] before_slot=%s after_slot=%s changed=%s"%(
      recent_before["max_slot"],recent_after["max_slot"],recent_progress),flush=True)
    print("[QARB030_PROGRESS] before_slot=%s after_slot=%s changed=%s"%(
      capture_before["max_slot"],capture_after["max_slot"],capture_progress),flush=True)

    return {
      "recent_before":recent_before,"recent_after":recent_after,
      "capture_before":capture_before,"capture_after":capture_after,
      "qarb027_progress":recent_progress,"qarb030_progress":capture_progress}

class EpisodeGate:
    def __init__(self):
        self.open={}
        self.admitted=[]
        self.raw_positive=0
        self.duplicates=0

    @staticmethod
    def key(row):
        return (row.get("route"),float(row.get("size_sol") or 0.0))

    def admit(self,row,now=None):
        if not row or not row.get("qualified"): return row
        self.raw_positive+=1
        now=time.monotonic() if now is None else float(now)
        k=self.key(row);old=self.open.get(k)
        if old:
            age=now-old["seen_at"]
            old_bps=float(old["row"].get("net_bps") or 0.0)
            new_bps=float(row.get("net_bps") or 0.0)
            if age<EPISODE_COOLDOWN_S and abs(new_bps-old_bps)<REPRICE_BPS:
                self.duplicates+=1
                old["seen_at"]=now;old["row"]=row
                print("[EPISODE_DUPLICATE] route=%s size=%.6f bps=%+.2f"%(
                    row.get("route"),row.get("size_sol"),row.get("net_bps")),flush=True)
                return None
        x=dict(row);x["episode_id"]="E%06d"%(len(self.admitted)+1);x["execution_authority"]=False
        self.open[k]={"seen_at":now,"row":x};self.admitted.append(x)
        print("[EPISODE_ADMIT] id=%s size=%.6f net=%+.9f bps=%+.2f route=%s"%(
            x["episode_id"],x["size_sol"],x["net_sol"],x["net_bps"],x["route"]),flush=True)
        return x

async def run_graph(root,seconds,gate):
    original=q.evaluate
    def wrapped(state,routes,received_ns):
        return gate.admit(original(state,routes,received_ns))
    q.evaluate=wrapped
    try: return await q.serve(Path(root),seconds)
    finally: q.evaluate=original

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--dynamic-seconds",type=float,default=35.0)
    ap.add_argument("--seconds",type=float,default=120.0)
    a=ap.parse_args(argv)

    root=Path.cwd()
    print("[QARB-051B] BOUNDED DYNAMIC HANDOFF + INDEPENDENT EPISODE GATE",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

    handoff=refresh_handoff(root,a.dynamic_seconds)
    gate=EpisodeGate()
    graph=asyncio.run(run_graph(root,a.seconds,gate))

    payload={"revision":"QARB_051B","handoff":handoff,
             "raw_positive_emissions":gate.raw_positive,
             "duplicate_emissions":gate.duplicates,
             "independent_episode_count":len(gate.admitted),
             "independent_episodes":gate.admitted,
             "graph_result":graph,"paper_only":True,"execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

    print("[EPISODE_RESULT] raw=%d duplicates=%d independent=%d"%(
      gate.raw_positive,gate.duplicates,len(gate.admitted)),flush=True)
    print("[HANDOFF_RESULT] qarb027_progress=%s qarb030_progress=%s"%(
      handoff["qarb027_progress"],handoff["qarb030_progress"]),flush=True)
    print("[REPORT]",OUT,flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

if __name__=="__main__":main()
