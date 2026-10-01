from __future__ import annotations
import asyncio,json,os,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026h_fresh_crossvenue_paper_gate as qh
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
EPISODE_GAP_SECONDS=float(os.getenv("QARB_EPISODE_GAP_SECONDS","2.0"))
STATE=Path("runtime_state/qseries/qarb_clean_bot/mriya_exact_episode_lineage_state.json")
HORIZONS=(2.0,5.0,15.0,30.0,60.0,90.0)

def key(token,direction,size): return (token,direction,round(float(size),9))

class ExactEpisodeLane(qh.FreshOnlyPaperLane):
    def __init__(self,root,state):
        super().__init__(root,state)
        self.episodes={};self.active={};self.busy={};self.seq=0;self.last_score=0.0

    def persist_exact(self):
        STATE.parent.mkdir(parents=True,exist_ok=True)
        payload={"exact_position_lineage":True,"episode_gap_seconds":EPISODE_GAP_SECONDS,
                 "episodes":list(self.episodes.values()),"execution_authority":False,"paper_only":True}
        tmp=STATE.with_name(STATE.name+".%d.%d.tmp"%(os.getpid(),time.time_ns()))
        txt=json.dumps(payload,indent=2,sort_keys=True)
        try:
            tmp.write_text(txt,encoding="utf-8")
            for i in range(5):
                try: os.replace(tmp,STATE);return
                except PermissionError: time.sleep(.03*(i+1))
        finally:
            try: tmp.unlink(missing_ok=True)
            except Exception: pass

    def episode(self,token,direction,now):
        k=(token,direction);e=self.active.get(k)
        if e is None or now-e["last_fresh_signal"]>EPISODE_GAP_SECONDS:
            self.seq+=1;eid="%s:%s:%06d"%(token,direction,self.seq)
            e={"id":eid,"token":token,"direction":direction,"started_monotonic":now,
               "last_fresh_signal":now,"signals":0,"anchor":None,"outcomes":{},"blocked_busy":0}
            self.active[k]=e;self.episodes[eid]=e
            print("[EXACT_EPISODE_START] id=%s token=%s dir=%s"%(eid[-18:],token[:10],direction),flush=True)
        e["last_fresh_signal"]=now;e["signals"]+=1
        return e

    def submit(self,r):
        buy=r.get("buy_venue");sell=r.get("sell_venue")
        if buy=="PUMPSWAP" and sell=="METEORA_DLMM":direction="PUMP_TO_METEORA"
        elif buy=="METEORA_DLMM" and sell=="PUMPSWAP":direction="METEORA_TO_PUMP"
        else:return super().submit(r)
        pair=self.pairs.get(r.get("token"))
        if pair is None:return super().submit(r)
        pa,da,skew,ps,ds=self._freshness(pair)
        fresh=pa is not None and da is not None and pa<=qh.MAX_CROSS_VENUE_AGE_MS and da<=qh.MAX_CROSS_VENUE_AGE_MS
        e=self.episode(r["token"],direction,time.monotonic()) if fresh else None
        captured=[];orig=self.book.enter
        def guarded(pair_,d_,now_):
            k=key(pair_.token,direction,d_["size_sol"])
            if e is not None and e.get("anchor") is not None:return None
            if k in self.busy:
                if e is not None:e["blocked_busy"]+=1
                return None
            pos=orig(pair_,d_,now_)
            if pos is not None:captured.append((pos,k))
            return pos
        self.book.enter=guarded
        try:super().submit(r)
        finally:self.book.enter=orig
        if e is not None and captured and e.get("anchor") is None:
            pos,k=captured[0];self.busy[k]=e["id"]
            e["anchor"]={"size_sol":pos.size_sol,"entry_quote_net_sol":pos.entry_quote_net_sol,
                         "entry_quote_bps":pos.entry_quote_bps,"entry_slot":pos.entry_slot,
                         "pump_age_ms":pa,"dlmm_age_ms":da,"skew_ms":skew,
                         "position_key":[k[0],k[1],k[2]]}
            print("[EXACT_EPISODE_ANCHOR] id=%s token=%s size=%.6f quote=%+.9f bps=%+.2f skew=%.1fms"%(
                e["id"][-18:],pos.token[:10],pos.size_sol,pos.entry_quote_net_sol,pos.entry_quote_bps,skew),flush=True)
            self.persist_exact()

    def capture(self,row):
        k=key(row["token"],row["direction"],row["size_sol"]);eid=self.busy.get(k)
        if not eid:return
        e=self.episodes.get(eid)
        if not e:return
        h=str(float(row["horizon_seconds"]))
        if h not in e["outcomes"]:
            e["outcomes"][h]={"paper_net_sol":float(row["paper_net_sol"]),
                              "actual_age_seconds":float(row["actual_age_seconds"])}
            print("[EXACT_EPISODE_OUTCOME] id=%s token=%s horizon=%gs pnl=%+.9f"%(
                eid[-18:],row["token"][:10],row["horizon_seconds"],row["paper_net_sol"]),flush=True)
            if float(row["horizon_seconds"])>=90.0 and self.busy.get(k)==eid:
                self.busy.pop(k,None)
            self.persist_exact()

    def mark_due(self):
        orig=self.book.update_pair
        def wrapped(pair,now):
            rows=orig(pair,now)
            for row in rows:self.capture(row)
            return rows
        self.book.update_pair=wrapped
        try:super().mark_due()
        finally:self.book.update_pair=orig
        now=time.monotonic()
        if now-self.last_score>=p.HEARTBEAT_SECONDS:
            self.print_score();self.last_score=now

    def print_score(self):
        a=[e for e in self.episodes.values() if e.get("anchor")]
        parts=[]
        for h in HORIZONS:
            vals=[e["outcomes"][str(h)]["paper_net_sol"] for e in a if str(h) in e["outcomes"]]
            parts.append("%gs:e=%d w=%d%% pnl=%+.6f"%(h,len(vals),round(100*sum(v>0 for v in vals)/len(vals)) if vals else 0,sum(vals)))
        print("[EXACT_EPISODE_SCORE] "+" | ".join(parts)+" busy=%d"%len(self.busy),flush=True)
        for token in sorted({e["token"] for e in a}):
            x=[e for e in a if e["token"]==token];v=[e["outcomes"]["2.0"]["paper_net_sol"] for e in x if "2.0" in e["outcomes"]]
            print("[EXACT_TOKEN] token=%s episodes=%d 2s_n=%d 2s_pnl=%+.6f"%(token[:10],len(x),len(v),sum(v)),flush=True)

def install():
    r=hot.install();r.SimulationLane=ExactEpisodeLane;return r

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=None);a=ap.parse_args(argv)
    r=install()
    print("[QARB-039B] EXACT EPISODE/POSITION LINEAGE",flush=True)
    print("[GUARD] one open independent anchor per token/direction/size until 90s maturity",flush=True)
    print("[FIX] no key overwrite while an anchored position is still open",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(r.serve(Path.cwd(),a.seconds))
if __name__=="__main__":main()
