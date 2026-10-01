from __future__ import annotations
import asyncio,hashlib,json,subprocess,sys,time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_049c_cpmm_connected_live_route_graph as q

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
CAPTURE=Path("runtime_state/qseries/qarb_clean_bot/mriya_dex_instruction_accounts.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/dynamic_progression_independent_episode_gate.json")
EPISODE_COOLDOWN_S=2.0
REPRICE_BPS=5.0

def _rows(x):
    if isinstance(x,list): return x
    if isinstance(x,dict):
        for k in ("rows","records","instructions"):
            if isinstance(x.get(k),list): return x[k]
    return []

def capture_state(root):
    p=Path(root)/CAPTURE
    if not p.is_file(): return {"exists":False,"max_slot":None,"rows":0,"sha":None}
    raw=p.read_bytes()
    try: obj=json.loads(raw.decode("utf-8"))
    except Exception: obj={}
    rows=_rows(obj)
    slots=[int(r.get("slot")) for r in rows if isinstance(r,dict) and r.get("slot") is not None]
    return {"exists":True,"max_slot":max(slots) if slots else None,
            "rows":len(rows),"sha":hashlib.sha256(raw).hexdigest()}

def _find_one(root,pattern):
    xs=sorted(Path(root).glob(pattern))
    if len(xs)!=1:
        raise RuntimeError("EXPECTED_ONE:%s found=%s"%(pattern,[x.name for x in xs]))
    return xs[0]

def refresh_dynamic(root):
    root=Path(root)
    runner=_find_one(root,"run_qarb_043b*.py")
    before=capture_state(root)
    print("[DYNAMIC_SOURCE] "+runner.name,flush=True)
    rc1=subprocess.call([sys.executable,str(runner)])
    if rc1!=0: raise RuntimeError("QARB_043B_FAILED:%d"%rc1)

    cap=root/"run_qarb_030_mriya_dex_instruction_account_capture.py"
    if not cap.is_file(): raise RuntimeError("MISSING_QARB_030_RUNNER")
    rc2=subprocess.call([sys.executable,str(cap)])
    if rc2!=0: raise RuntimeError("QARB_030_FAILED:%d"%rc2)
    after=capture_state(root)

    progressed=bool(
        before["sha"]!=after["sha"] or
        (before["max_slot"] is not None and after["max_slot"] is not None and after["max_slot"]>before["max_slot"])
    )
    print("[PROGRESSION] before_slot=%s after_slot=%s changed=%s"%(
        before["max_slot"],after["max_slot"],progressed),flush=True)
    return before,after,progressed

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
        k=self.key(row)
        old=self.open.get(k)
        if old:
            age=now-old["seen_at"]
            old_bps=float(old["row"].get("net_bps") or 0.0)
            new_bps=float(row.get("net_bps") or 0.0)
            materially_repriced=abs(new_bps-old_bps)>=REPRICE_BPS
            if age<EPISODE_COOLDOWN_S and not materially_repriced:
                self.duplicates+=1
                old["seen_at"]=now
                old["row"]=row
                print("[EPISODE_DUPLICATE] route=%s size=%.6f bps=%+.2f"%(
                    row.get("route"),row.get("size_sol"),row.get("net_bps")),flush=True)
                return None
        eid="E%06d"%(len(self.admitted)+1)
        x=dict(row);x["episode_id"]=eid;x["execution_authority"]=False
        self.open[k]={"seen_at":now,"row":x}
        self.admitted.append(x)
        print("[EPISODE_ADMIT] id=%s size=%.6f net=%+.9f bps=%+.2f route=%s"%(
            eid,x["size_sol"],x["net_sol"],x["net_bps"],x["route"]),flush=True)
        return x

def install_gate(gate):
    original=q.evaluate
    def wrapped(state,routes,received_ns):
        row=original(state,routes,received_ns)
        return gate.admit(row)
    q.evaluate=wrapped
    return original

async def run_generation(root,seconds):
    gate=EpisodeGate()
    original=install_gate(gate)
    try:
        result=await q.serve(Path(root),seconds)
    finally:
        q.evaluate=original
    return result,gate

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=120.0)
    a=ap.parse_args(argv)
    root=Path.cwd()

    print("[QARB-051] DYNAMIC PROGRESSION + INDEPENDENT EPISODE GATE",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

    before,after,progressed=refresh_dynamic(root)
    result,gate=asyncio.run(run_generation(root,a.seconds))

    payload={
      "revision":"QARB_051",
      "source_progressed":progressed,
      "capture_before":before,"capture_after":after,
      "raw_positive_emissions":gate.raw_positive,
      "duplicate_emissions":gate.duplicates,
      "independent_episodes":gate.admitted,
      "independent_episode_count":len(gate.admitted),
      "graph_result":result,
      "paper_only":True,"execution_authority":False}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

    print("[EPISODE_RESULT] raw=%d duplicates=%d independent=%d"%(
        gate.raw_positive,gate.duplicates,len(gate.admitted)),flush=True)
    print("[SOURCE_PROGRESS] "+("PASS" if progressed else "HOLD_NO_NEW_MRIYA_CAPTURE"),flush=True)
    print("[REPORT]",OUT,flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

if __name__=="__main__":main()
