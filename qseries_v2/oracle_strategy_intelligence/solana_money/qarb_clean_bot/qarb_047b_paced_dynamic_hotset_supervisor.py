from __future__ import annotations
import asyncio,json,subprocess,sys,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026g_token_freshness_profit_audit as qg
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_039b_exact_episode_position_lineage as ex
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_045b_evidence_window_hotset_lifecycle as life
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_046_token_age_edge_decay as decay

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
GEN_DIR=Path("runtime_state/qseries/qarb_clean_bot/dynamic_generations")
_ORIG_PREPARE=pd.prepare_pairs

def binding_universe(path):
    d=json.loads(Path(path).read_text(encoding="utf-8"))
    return [{"token":x["token"],"pump_pool":x["pump_pool"],"meteora_meta":x["meteora_meta"]} for x in d.get("rows",[])]

def prepare_from(path,root):
    old=pd.engine.candidate_universe;oldmax=pd.MAX_PAIRS
    pd.engine.candidate_universe=lambda _:binding_universe(path);pd.MAX_PAIRS=16
    try:return _ORIG_PREPARE(Path(root))
    finally:pd.engine.candidate_universe=old;pd.MAX_PAIRS=oldmax

class AgeDrainLane(ex.ExactEpisodeLane):
    def __init__(self,root,state,meta,admit_seconds,generation):
        self.meta=meta;self.admit_seconds=float(admit_seconds);self.generation=generation
        self.started=time.monotonic();self.age_written=set()
        super().__init__(root,state)
    def persist_exact(self):
        GEN_DIR.mkdir(parents=True,exist_ok=True)
        path=GEN_DIR/("episode_state_%s.json"%self.generation)
        path.write_text(json.dumps({"generation":self.generation,"episodes":list(self.episodes.values()),
            "paper_only":True,"execution_authority":False},indent=2,sort_keys=True),encoding="utf-8")
    def submit(self,r):
        if time.monotonic()-self.started>self.admit_seconds:return
        before={k for k,e in self.episodes.items() if e.get("anchor")}
        super().submit(r);now=time.time()
        for eid,e in self.episodes.items():
            if eid in before or not e.get("anchor"):continue
            info=self.meta.get(e["token"],{})
            e["anchor"]["token_age_seconds"]=max(0.0,now-float(info.get("first_seen_epoch",now)))
            e["anchor"]["seconds_since_last_seen_at_entry"]=max(0.0,now-float(info.get("last_seen_epoch",now)))
            e["anchor"]["generation"]=self.generation;self.persist_exact()
            print("[AGE_ANCHOR] gen=%s token=%s token_age=%.1fs last_seen_age=%.1fs"%(
                self.generation,e["token"][:10],e["anchor"]["token_age_seconds"],e["anchor"]["seconds_since_last_seen_at_entry"]),flush=True)
    def capture(self,row):
        k=ex.key(row["token"],row["direction"],row["size_sol"]);eid=self.busy.get(k)
        super().capture(row)
        if not eid:return
        e=self.episodes.get(eid)
        if not e or not e.get("anchor"):return
        h=float(row["horizon_seconds"]);tag=(eid,h)
        if tag in self.age_written:return
        self.age_written.add(tag)
        decay.append({"generation":self.generation,"episode_id":eid,"token":row["token"],
            "token_age_seconds":e["anchor"].get("token_age_seconds",0.0),
            "seconds_since_last_seen_at_entry":e["anchor"].get("seconds_since_last_seen_at_entry",0.0),
            "horizon_seconds":h,"paper_net_sol":float(row["paper_net_sol"]),"recorded_epoch":time.time()})

async def generation_worker(bindings,seconds,admit_seconds,generation):
    d=json.loads(Path(bindings).read_text(encoding="utf-8"))
    meta={x["token"]:x.get("lifecycle",{}) for x in d.get("rows",[])}
    def prep(root):return prepare_from(bindings,root)
    qg.VENUE_TS.clear();p.m.pd.prepare_pairs=prep;p.m.pd.apply_account_event=qg.tracked_apply
    class Lane(AgeDrainLane):
        def __init__(self,root,state):super().__init__(root,state,meta,admit_seconds,generation)
    p.SimulationLane=Lane
    print("[GENERATION_START] gen=%s tokens=%s admit=%.1fs drain_until=%.1fs"%(
        generation,[x[:10] for x in meta],admit_seconds,seconds),flush=True)
    return await p.serve(Path.cwd(),seconds)

def write_generation(rows,g):
    GEN_DIR.mkdir(parents=True,exist_ok=True)
    path=GEN_DIR/("bindings_%06d.json"%g)
    path.write_text(json.dumps({"rows":rows,"generation":g,"created_epoch":time.time(),
        "execution_authority":False},indent=2,sort_keys=True),encoding="utf-8")
    return path

def supervisor(seconds=600,refresh_seconds=30,drain_seconds=125):
    GEN_DIR.mkdir(parents=True,exist_ok=True)
    discovery=subprocess.Popen([sys.executable,"run_qarb_043b_paced_mriya_token_discovery.py"])
    children=[];started=time.monotonic();g=0
    try:
        time.sleep(6)
        while time.monotonic()-started<float(seconds):
            payload,active=life.classify()
            if active:
                g+=1;path=write_generation(active,g)
                cmd=[sys.executable,"run_qarb_047b_paced_dynamic_hotset_supervisor.py","--worker",
                     "--bindings",str(path),"--generation",str(g),"--seconds",str(drain_seconds),
                     "--admit-seconds",str(refresh_seconds)]
                children.append(subprocess.Popen(cmd))
                print("[HOTSWAP] generation=%d active=%s old_generations_drain_in_parallel"%(
                    g,[x["token"][:10] for x in active]),flush=True)
            else:print("[HOTSWAP_HOLD] no HOT/ACTIVE exact-bound tokens",flush=True)
            children=[x for x in children if x.poll() is None]
            remain=float(seconds)-(time.monotonic()-started)
            if remain<=0:break
            time.sleep(min(float(refresh_seconds),remain))
    finally:
        try:discovery.terminate()
        except Exception:pass
        deadline=time.time()+float(drain_seconds)+5
        for ch in children:
            try:ch.wait(timeout=max(1,deadline-time.time()))
            except Exception:
                try:ch.terminate()
                except Exception:pass
    decay.analyze()
    print("[SUPERVISOR_DONE] generations=%d execution_authority=FALSE"%g,flush=True)

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=600)
    ap.add_argument("--refresh-seconds",type=float,default=30);ap.add_argument("--drain-seconds",type=float,default=125)
    ap.add_argument("--worker",action="store_true");ap.add_argument("--bindings");ap.add_argument("--generation",type=int,default=0)
    ap.add_argument("--admit-seconds",type=float,default=30);a=ap.parse_args(argv)
    if a.worker:return asyncio.run(generation_worker(a.bindings,a.seconds,a.admit_seconds,a.generation))
    print("[QARB-047B] PACED DYNAMIC HOTSET GENERATION SUPERVISOR",flush=True)
    print("[DISCOVERY] QARB-043B paced websocket discovery child",flush=True)
    print("[LIFECYCLE] QARB-045B 10m evidence window",flush=True)
    print("[ROTATION] generation refresh every %.1fs; prior generations drain outcomes"%a.refresh_seconds,flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return supervisor(a.seconds,a.refresh_seconds,a.drain_seconds)
if __name__=="__main__":main()
