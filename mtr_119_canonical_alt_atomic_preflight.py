from __future__ import annotations
import copy,json,threading,time
from pathlib import Path

import mtr_118_target_only_24_route_scale as b118

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as sae
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair as q87
)

ALT="HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r"
PUBLIC_USER="CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR"
OUT=Path("mtr_119_canonical_alt_atomic_preflight.json")
PREWARMED=set()
ROUTE_METEORA={}
ATOMIC=None

def route_key(snap):
    return "%s|%s|%s"%(
        snap["token"],snap["pump_pool"],snap["meteora"]["address"]
    )

def exact_process(state,ev,counter,sim_lane):
    refs=state.get("preg_multi",{}).get(ev["address"])
    if not refs:
        return
    for i,kind in refs:
        pair=state["pairs"][i]
        try:
            changed=sae.persistent.m.pd.apply_account_event(
                pair,kind,ev["address"],ev["raw"],ev["slot"],ev["received_ns"]
            )
        except Exception:
            counter["event_errors"]+=1
            continue
        if not changed:
            continue
        counter["priced_events"]+=1
        snap=sae.immutable_snapshot(pair)
        q20._lane.submit(
            route_key(snap),snap,ev["slot"],ev["received_ns"]
        )

class AtomicPreflight:
    def __init__(self,user):
        self.user=user
        self.cv=threading.Condition()
        self.pending=None
        self.stop=False
        self.attempts=0
        self.compiled=0
        self.simulated=0
        self.pass_count=0
        self.rows=[]
        self.thread=threading.Thread(target=self._loop,daemon=True)
        self.thread.start()

    def submit(self,snap,best,slot,received_ns):
        if best.get("direction")!="PUMP_TO_METEORA":
            return False
        if int(best.get("local_net",0))<=0:
            return False
        with self.cv:
            if self.pass_count:
                return False
            self.pending=(copy.deepcopy(snap),copy.deepcopy(best),slot,received_ns)
            self.cv.notify()
        return True

    def _take(self):
        with self.cv:
            while not self.stop and self.pending is None:
                self.cv.wait(.2)
            if self.pending is None:
                return None
            row=self.pending
            self.pending=None
            return row

    def _loop(self):
        while True:
            item=self._take()
            if item is None:
                if self.stop:
                    return
                continue
            snap,best,slot,received_ns=item
            self.attempts+=1
            started=time.perf_counter_ns()
            key=route_key(snap)
            row={
                "slot":slot,
                "route":key,
                "direction":best["direction"],
                "size_sol":best["size_sol"],
                "local_net_lamports":best["local_net"],
                "local_bps":best["local_bps"],
                "event_age_at_handoff_ms":max(
                    0.0,(started-received_ns)/1e6
                ),
                "alt":ALT,
            }
            try:
                token=str(snap["token"])
                mt=ROUTE_METEORA.get(key)
                if mt is None:
                    raise RuntimeError("ROUTE_METEORA_TEMPLATE_MISSING")
                if str(mt["pool"])!=str(snap["meteora"]["address"]):
                    raise RuntimeError("METEORA_TEMPLATE_BINDING_DRIFT")

                sae.METEORA_TEMPLATES[token]=copy.deepcopy(mt)
                route=sae.same_snapshot_route(self.user,snap,best)

                if str(route["token"])!=token:
                    raise RuntimeError("ATOMIC_TOKEN_DRIFT")

                bh=sae.BLOCKHASH.get()
                candidates=list(q87.repaired_candidates(route))
                attempts=[]
                compiled=None

                for cand in candidates:
                    name=str(cand.get("name","UNKNOWN"))
                    if "PUMP_METEORA_ONLY" in name:
                        continue
                    comp=q87.compile_candidate(
                        self.user,
                        cand["instructions"],
                        [[ALT]],
                        bh,
                    )
                    attempt={
                        "candidate":name,
                        "ok":bool(comp.get("ok")),
                        "bytes":comp.get("bytes"),
                        "alts":comp.get("alts"),
                        "error":comp.get("error"),
                    }
                    attempts.append(attempt)
                    print(
                        "[MTR119_COMPILE] route=%s candidate=%s ok=%s bytes=%s alt=%s"
                        %(key[-24:],name,attempt["ok"],attempt["bytes"],ALT[:12]),
                        flush=True,
                    )
                    if (
                        comp.get("ok")
                        and int(comp.get("bytes") or 99999)<=sae.MAX_TX_BYTES
                    ):
                        compiled={
                            "ok":True,
                            "candidate":name,
                            "bytes":int(comp["bytes"]),
                            "msg":comp["msg"],
                            "raw":comp["unsigned"],
                            "attempts":attempts,
                        }
                        break

                row["compile_attempts"]=attempts
                if compiled is None:
                    raise RuntimeError("NO_LEGAL_CANONICAL_ALT_TX")

                self.compiled+=1
                sim=sae.simulate_current(compiled,self.user)
                self.simulated+=1

                logs=[str(x) for x in (sim.get("logs") or [])]
                pump_seen=any(str(q87.c.PUMP) in x for x in logs)
                meteora_seen=any(str(q87.c.DLMM) in x for x in logs)
                passed=sim.get("err") is None and pump_seen and meteora_seen

                row.update({
                    "compiled":True,
                    "candidate":compiled["candidate"],
                    "bytes":compiled["bytes"],
                    "sim_err":sim.get("err"),
                    "sim_units":sim.get("units"),
                    "pump_program_seen":pump_seen,
                    "meteora_program_seen":meteora_seen,
                    "atomic_two_leg_pass":passed,
                    "preflight_ms":(time.perf_counter_ns()-started)/1e6,
                })

                print(
                    "[MTR119_SIM] route=%s bytes=%d err=%s pump=%s meteora=%s units=%s"
                    %(key[-24:],compiled["bytes"],sim.get("err"),
                      pump_seen,meteora_seen,sim.get("units")),
                    flush=True,
                )

                if passed:
                    self.pass_count+=1
                    print(
                        "[MTR119_ATOMIC_PASS] token=%s slot=%s size=0.010 bps=%+.2f bytes=%d"
                        %(token[:10],slot,float(best["local_bps"]),compiled["bytes"]),
                        flush=True,
                    )
            except Exception as exc:
                row["error"]="%s:%s"%(type(exc).__name__,str(exc)[:500])
                print(
                    "[MTR119_ATOMIC_HOLD] route=%s reason=%s"
                    %(key[-24:],row["error"][:260]),
                    flush=True,
                )
            self.rows.append(row)

    def close(self):
        with self.cv:
            self.stop=True
            self.cv.notify_all()
        self.thread.join(timeout=30)

class Lane(q20.LatestStateLane):
    def __init__(self):
        super().__init__()
        self.warmed=set(PREWARMED)

    def _price(self,key,row):
        snap,slot,received_ns,generation=row
        start_ms=max(0.0,(time.perf_counter_ns()-received_ns)/1e6)
        self.event_start_ms.append(start_ms)
        if start_ms>q20.MAX_START_AGE_MS:
            self.stale_drops+=1
            return

        started=time.perf_counter_ns()
        rows=q18.exact_snapshot_opportunities(snap,0.010)
        self.evaluations+=2
        if self.newer_waiting(key,generation):
            self.scan_replaced+=1
            return

        best=max(rows,key=lambda x:int(x["local_net"]))
        scan_ms=(time.perf_counter_ns()-started)/1e6
        self.scan_ms.append(scan_ms)
        self.processed+=1

        if int(best["local_net"])>0:
            self.positive+=1
        if self.best is None or int(best["local_net"])>int(self.best["local_net"]):
            self.best=dict(best)

        print(
            "[MTR119_EXACT] token=%s slot=%s dir=%s size=0.010 bps=%+.2f "
            "net=%+d start_ms=%.3f scan_ms=%.3f"
            %(str(snap["token"])[:10],slot,best["direction"],
              float(best["local_bps"]),int(best["local_net"]),start_ms,scan_ms),
            flush=True,
        )

        if int(best["local_net"])>0:
            if best["direction"]=="PUMP_TO_METEORA":
                if ATOMIC.submit(snap,best,slot,received_ns):
                    print(
                        "[MTR119_HANDOFF] token=%s slot=%s bps=%+.2f"
                        %(str(snap["token"])[:10],slot,float(best["local_bps"])),
                        flush=True,
                    )
            else:
                print(
                    "[MTR119_POSITIVE_HOLD] token=%s direction=%s reason=DIRECTION_NOT_YET_ATOMIC_CERTIFIED"
                    %(str(snap["token"])[:10],best["direction"]),
                    flush=True,
                )

def prebuild_route_templates(state,user,warmed):
    global ROUTE_METEORA
    ROUTE_METEORA={}
    pump_by_token={}
    for p in state["pairs"]:
        prior=pump_by_token.setdefault(str(p.token),str(p.pump_pool))
        if prior!=str(p.pump_pool):
            raise RuntimeError("MULTI_PUMP_SAME_TOKEN_TEMPLATE_COLLISION")

    sae.prebuild_templates(state,user)
    pump_ready=set(sae.READY_TOKENS)
    if not pump_ready:
        raise RuntimeError("NO_PUMP_TEMPLATES")

    for n,pair in enumerate(state["pairs"],1):
        token=str(pair.token)
        if token not in pump_ready:
            continue
        sae.READY_TOKENS={token}
        sae.prebuild_meteora_templates(
            {"pairs":[pair]},
            user,
            warmed,
        )
        template=sae.METEORA_TEMPLATES.get(token)
        if template is None:
            continue
        snap=sae.immutable_snapshot(pair)
        key=route_key(snap)
        ROUTE_METEORA[key]=copy.deepcopy(template)
        print(
            "[MTR119_ROUTE_TEMPLATE] %d/%d token=%s meteora=%s arrays=%d"
            %(n,len(state["pairs"]),token[:10],str(pair.meteora_pool)[:12],
              len(template.get("arrays") or [])),
            flush=True,
        )

    sae.READY_TOKENS=set(pump_ready)
    print(
        "[MTR119_TEMPLATE_SUMMARY] pump_tokens=%d route_meteora=%d"
        %(len(pump_ready),len(ROUTE_METEORA)),
        flush=True,
    )

def main():
    global ATOMIC,PREWARMED
    print("[MTR-119] START",flush=True)
    print("[GATE] fresh corrected exact 0.010 PUMP_TO_METEORA positive -> canonical ALT unsigned atomic preflight",flush=True)
    print("[ALT] "+ALT,flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)

    state,cap=b118.prepare_once(Path.cwd())
    q25.bind_cached_state(state)
    warmed=q25.install_hot_math_and_prewarm(state)

    user=PUBLIC_USER
    sae.USER=user
    prebuild_route_templates(state,user,warmed)

    PREWARMED={str(p.pump_pool) for p in state["pairs"]}
    for pool in PREWARMED:
        q18.worker().warm(pool)

    sae.BLOCKHASH.start()
    ATOMIC=AtomicPreflight(user)

    q20.FAST_SIZES=(0.010,)
    q20.FULL_SIZE_CURVE=(0.010,)
    q20.EXPAND_SIZES=()
    q20._patched_process_event=exact_process
    q20.LatestStateLane=Lane

    try:
        rc=q20.run(120.0)
    finally:
        ATOMIC.close()
        sae.BLOCKHASH.close()

    lane=q20._lane
    result={
        "mtr":"MTR-119",
        "pairs":len(state["pairs"]),
        "route_templates":len(ROUTE_METEORA),
        "submitted":lane.submitted,
        "processed":lane.processed,
        "positive":lane.positive,
        "stale":lane.stale_drops,
        "p99_start_ms":q20._p99(lane.event_start_ms),
        "p99_scan_ms":q20._p99(lane.scan_ms),
        "atomic_attempts":ATOMIC.attempts,
        "compiled":ATOMIC.compiled,
        "simulated":ATOMIC.simulated,
        "atomic_pass":ATOMIC.pass_count,
        "atomic_rows":ATOMIC.rows[-20:],
        "alt":ALT,
        "execution_authority":False,
        "signing":False,
        "broadcast":False,
        "private_key_used":False,
        "return_code":rc,
    }
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,default=str),encoding="utf-8")

    print(
        "[SUMMARY] pairs=%d templates=%d processed=%d positive=%d stale=%d "
        "atomic_attempts=%d compiled=%d simulated=%d atomic_pass=%d"
        %(result["pairs"],result["route_templates"],result["processed"],
          result["positive"],result["stale"],result["atomic_attempts"],
          result["compiled"],result["simulated"],result["atomic_pass"]),
        flush=True,
    )

    if result["atomic_pass"]>0:
        print("[RESULT] ATOMIC_TWO_LEG_PREFLIGHT_PASS",flush=True)
    elif result["atomic_attempts"]>0:
        print("[RESULT] ATOMIC_TWO_LEG_PREFLIGHT_ATTEMPTED_NOT_CERTIFIED",flush=True)
    else:
        print("[RESULT] NO_FRESH_P2M_010_POSITIVE_IN_WINDOW",flush=True)

    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-119] COMPLETE",flush=True)

if __name__=="__main__":
    main()
