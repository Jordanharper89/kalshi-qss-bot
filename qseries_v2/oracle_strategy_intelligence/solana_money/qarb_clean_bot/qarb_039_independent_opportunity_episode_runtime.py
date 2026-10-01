from __future__ import annotations
import asyncio,json,os,time
from collections import defaultdict
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026h_fresh_crossvenue_paper_gate as qh
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
EPISODE_GAP_SECONDS=float(os.getenv("QARB_EPISODE_GAP_SECONDS","2.0"))
STATE=Path("runtime_state/qseries/qarb_clean_bot/mriya_independent_episode_state.json")
HORIZONS=(2.0,5.0,15.0,30.0,60.0,90.0)

def _k(token,direction,size): return (token,direction,round(float(size),9))

class EpisodeLane(qh.FreshOnlyPaperLane):
    def __init__(self,root,state):
        super().__init__(root,state)
        self.episodes={}
        self.active={}
        self.anchor_keys={}
        self.seq=0
        self._last_episode_score=0.0

    def _persist_episodes(self):
        STATE.parent.mkdir(parents=True,exist_ok=True)
        data={"episode_gap_seconds":EPISODE_GAP_SECONDS,"episodes":list(self.episodes.values()),
              "execution_authority":False,"paper_only":True}
        txt=json.dumps(data,indent=2,sort_keys=True)
        tmp=STATE.with_name(STATE.name+".%d.%d.tmp"%(os.getpid(),time.time_ns()))
        try:
            tmp.write_text(txt,encoding="utf-8")
            for i in range(5):
                try: os.replace(tmp,STATE); return
                except PermissionError: time.sleep(.03*(i+1))
        finally:
            try: tmp.unlink(missing_ok=True)
            except Exception: pass

    def _episode(self,token,direction,now):
        key=(token,direction); cur=self.active.get(key)
        if cur is None or now-cur["last_fresh_signal"]>EPISODE_GAP_SECONDS:
            self.seq+=1; eid="%s:%s:%06d"%(token,direction,self.seq)
            cur={"id":eid,"token":token,"direction":direction,"started_monotonic":now,
                 "last_fresh_signal":now,"signals":0,"entries":0,"anchor":None,"outcomes":{}}
            self.active[key]=cur; self.episodes[eid]=cur
            print("[EPISODE_START] id=%s token=%s dir=%s"%(eid[-18:],token[:10],direction),flush=True)
        cur["last_fresh_signal"]=now;cur["signals"]+=1
        return cur

    def submit(self,r):
        buy=r.get("buy_venue");sell=r.get("sell_venue")
        if buy=="PUMPSWAP" and sell=="METEORA_DLMM": direction="PUMP_TO_METEORA"
        elif buy=="METEORA_DLMM" and sell=="PUMPSWAP": direction="METEORA_TO_PUMP"
        else: return super().submit(r)
        pair=self.pairs.get(r.get("token"))
        if pair is None:return super().submit(r)
        pa,da,skew,ps,ds=self._freshness(pair)
        fresh=pa is not None and da is not None and pa<=qh.MAX_CROSS_VENUE_AGE_MS and da<=qh.MAX_CROSS_VENUE_AGE_MS
        ep=self._episode(r["token"],direction,time.monotonic()) if fresh else None
        captured=[]; orig=self.book.enter
        def cap(pair_,d_,now_):
            pos=orig(pair_,d_,now_)
            if pos is not None: captured.append(pos)
            return pos
        self.book.enter=cap
        try: super().submit(r)
        finally: self.book.enter=orig
        for pos in captured:
            ep["entries"]+=1
            if ep["anchor"] is None:
                ep["anchor"]={"size_sol":pos.size_sol,"entry_quote_net_sol":pos.entry_quote_net_sol,
                              "entry_quote_bps":pos.entry_quote_bps,"entry_slot":pos.entry_slot,
                              "pump_age_ms":pa,"dlmm_age_ms":da,"skew_ms":skew}
                self.anchor_keys[_k(pos.token,direction,pos.size_sol)]=ep["id"]
                print("[EPISODE_ANCHOR] id=%s token=%s size=%.6f quote=%+.9f bps=%+.2f skew=%.1fms"%(
                    ep["id"][-18:],pos.token[:10],pos.size_sol,pos.entry_quote_net_sol,
                    pos.entry_quote_bps,skew),flush=True)
                self._persist_episodes()

    def _capture_outcome(self,row):
        key=_k(row["token"],row["direction"],row["size_sol"])
        eid=self.anchor_keys.get(key)
        if not eid:return
        ep=self.episodes.get(eid)
        if not ep:return
        h=str(float(row["horizon_seconds"]))
        if h in ep["outcomes"]:return
        ep["outcomes"][h]={"paper_net_sol":float(row["paper_net_sol"]),
                           "actual_age_seconds":float(row["actual_age_seconds"])}
        print("[EPISODE_OUTCOME] id=%s token=%s horizon=%gs pnl=%+.9f"%(
            eid[-18:],row["token"][:10],row["horizon_seconds"],row["paper_net_sol"]),flush=True)
        self._persist_episodes()

    def mark_due(self):
        orig=self.book.update_pair
        def cap(pair,now):
            rows=orig(pair,now)
            for row in rows:self._capture_outcome(row)
            return rows
        self.book.update_pair=cap
        try: super().mark_due()
        finally:self.book.update_pair=orig
        now=time.monotonic()
        if now-self._last_episode_score>=p.HEARTBEAT_SECONDS:
            self.print_episode_score();self._last_episode_score=now

    def print_episode_score(self):
        anchors=[x for x in self.episodes.values() if x.get("anchor")]
        parts=[]
        for h in HORIZONS:
            vals=[e["outcomes"][str(h)]["paper_net_sol"] for e in anchors if str(h) in e["outcomes"]]
            parts.append("%gs:e=%d w=%d%% pnl=%+.6f"%(h,len(vals),
                round(100*sum(v>0 for v in vals)/len(vals)) if vals else 0,sum(vals)))
        print("[INDEPENDENT_EPISODE_SCORE] "+" | ".join(parts),flush=True)
        for token in sorted({e["token"] for e in anchors}):
            vals=[e for e in anchors if e["token"]==token]
            h2=[e["outcomes"]["2.0"]["paper_net_sol"] for e in vals if "2.0" in e["outcomes"]]
            print("[EPISODE_TOKEN] token=%s episodes=%d 2s_n=%d 2s_pnl=%+.6f"%(
                token[:10],len(vals),len(h2),sum(h2)),flush=True)

def install():
    runtime=hot.install()
    runtime.SimulationLane=EpisodeLane
    return runtime

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=None);a=ap.parse_args(argv)
    runtime=install()
    print("[QARB-039] INDEPENDENT OPPORTUNITY EPISODE RUNTIME",flush=True)
    print("[EPISODE] fresh qualified signals separated by >%.2fs create a new episode"%EPISODE_GAP_SECONDS,flush=True)
    print("[ANCHOR] first admitted paper entry per episode is the independent outcome anchor",flush=True)
    print("[ENGINE] QARB-038B hotset + original persistent runtime retained",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(runtime.serve(Path.cwd(),a.seconds))
if __name__=="__main__":main()
