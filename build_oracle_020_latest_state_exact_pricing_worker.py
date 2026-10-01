from pathlib import Path
import py_compile
import textwrap

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_020_latest_state_exact_pricing_worker.py"
TEST=ROOT/"test_oracle_020_latest_state_exact_pricing_worker.py"
RUN=ROOT/"run_oracle_020_latest_state_exact_pricing_worker.py"

module_src=r"""
from __future__ import annotations

import argparse
import asyncio
import json
import threading
import time
from pathlib import Path

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

FAST_SIZES=(0.001,0.010,0.050)
EXPAND_SIZES=(0.180,0.500,1.400)
EXPAND_GATE_BPS=-100.0
MAX_START_AGE_MS=750.0

persistent=q19.persistent
_original_process_event=None
_lane=None

class LatestStateLane:
    def __init__(self):
        self.cv=threading.Condition()
        self.latest={}
        self.stop=False
        self.thread=None
        self.submitted=0
        self.replaced=0
        self.processed=0
        self.stale_drops=0
        self.scan_replaced=0
        self.positive=0
        self.evaluations=0
        self.event_start_ms=[]
        self.scan_ms=[]
        self.best=None
        self.warmed=set()

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread=threading.Thread(target=self._loop,name="oracle020-latest-state",daemon=True)
        self.thread.start()

    def submit(self,token,snap,slot,received_ns):
        with self.cv:
            self.submitted+=1
            if token in self.latest:
                self.replaced+=1
            self.latest[token]=(snap,int(slot),int(received_ns),self.submitted)
            self.cv.notify()

    def newer_waiting(self,token,generation):
        with self.cv:
            row=self.latest.get(token)
            return bool(row and int(row[3])>int(generation))

    def _take(self):
        with self.cv:
            while not self.latest and not self.stop:
                self.cv.wait(.25)
            if self.stop and not self.latest:
                return None
            token,nextrow=next(iter(self.latest.items()))
            del self.latest[token]
            return token,nextrow

    def _warm(self,snap):
        pool=snap["pump_pool"]
        if pool in self.warmed:
            return
        q18.worker().warm(pool)
        self.warmed.add(pool)

    def _price(self,token,row):
        snap,slot,received_ns,generation=row
        start_ms=max(0.0,(time.perf_counter_ns()-received_ns)/1e6)
        self.event_start_ms.append(start_ms)
        if start_ms>MAX_START_AGE_MS:
            self.stale_drops+=1
            print("[ORACLE020_STALE_DROP] token=%s slot=%s age_ms=%.3f"%(token[:10],slot,start_ms),flush=True)
            return

        self._warm(snap)
        started=time.perf_counter_ns()
        rows=[]

        for size in FAST_SIZES:
            rows.extend(q18.exact_snapshot_opportunities(snap,size))
            self.evaluations+=2
            if self.newer_waiting(token,generation):
                self.scan_replaced+=1
                print("[ORACLE020_SCAN_REPLACED] token=%s slot=%s after_size=%.3f"%(token[:10],slot,size),flush=True)
                return

        best=max(rows,key=lambda x:x["local_net"])

        if float(best["local_bps"])>=EXPAND_GATE_BPS:
            for size in EXPAND_SIZES:
                rows.extend(q18.exact_snapshot_opportunities(snap,size))
                self.evaluations+=2
                if self.newer_waiting(token,generation):
                    self.scan_replaced+=1
                    print("[ORACLE020_SCAN_REPLACED] token=%s slot=%s after_size=%.3f"%(token[:10],slot,size),flush=True)
                    return
            best=max(rows,key=lambda x:x["local_net"])

        scan_ms=(time.perf_counter_ns()-started)/1e6
        self.scan_ms.append(scan_ms)
        self.processed+=1

        if int(best["local_net"])>0:
            self.positive+=1
        if self.best is None or int(best["local_net"])>int(self.best["local_net"]):
            self.best=dict(best)

        print(
            "[ORACLE020_EXACT_LATEST] token=%s slot=%s dir=%s size=%.3f "
            "bps=%+.2f net=%+d start_ms=%.3f scan_ms=%.3f"
            %(token[:10],slot,best["direction"],float(best["size_sol"]),
              float(best["local_bps"]),int(best["local_net"]),start_ms,scan_ms),
            flush=True,
        )

    def _loop(self):
        while True:
            item=self._take()
            if item is None:
                return
            token,row=item
            try:
                self._price(token,row)
            except Exception as exc:
                print("[ORACLE020_PRICE_REJECT] token=%s reason=%s:%s"%(
                    token[:10],type(exc).__name__,str(exc)[:220]),flush=True)

    def close(self):
        with self.cv:
            self.stop=True
            self.cv.notify_all()
        if self.thread:
            self.thread.join(timeout=10)

def _pair_snapshot(pair):
    return {
        "token":pair.token,
        "pump_pool":pair.pump_pool,
        "meteora":{
            "address":pair.meteora_pool,
            "token_x":pair.token_x,
            "token_y":pair.token_y,
            "decimals_x":pair.decimals_x,
            "decimals_y":pair.decimals_y,
        },
        "dlmm_state":pair.dlmm_state,
        "pump_base_reserve":int(pair.pump_base_reserve),
        "pump_quote_reserve":int(pair.pump_quote_reserve),
    }

def _patched_process_event(state,ev,c,sim_lane):
    address=ev["address"]
    preg=state.get("preg",{})
    if address not in preg:
        return _original_process_event(state,ev,c,sim_lane)

    i,kind=preg[address]
    pair=state["pairs"][i]
    try:
        changed=persistent.m.pd.apply_account_event(
            pair,kind,address,ev["raw"],ev["slot"],ev["received_ns"]
        )
    except Exception:
        c["event_errors"]+=1
        return

    if not changed:
        return

    c["priced_events"]+=1
    _lane.submit(pair.token,_pair_snapshot(pair),ev["slot"],ev["received_ns"])

def install():
    global _original_process_event,_lane
    q18.install_exact_hot_math()

    if not hasattr(persistent,"_process_event"):
        raise RuntimeError("PERSISTENT_PROCESS_EVENT_SEAM_MISSING")

    _original_process_event=persistent._process_event
    _lane=LatestStateLane()
    _lane.start()

    _patched_process_event._oracle020_latest_state=True
    persistent._process_event=_patched_process_event
    return _lane

def _p99(rows):
    if not rows:
        return None
    s=sorted(rows)
    return s[min(len(s)-1,int(len(s)*.99))]

def report(lane):
    payload={
        "oracle_build":"ORACLE-020",
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "submitted":lane.submitted,
        "replaced_before_start":lane.replaced,
        "processed":lane.processed,
        "stale_drops":lane.stale_drops,
        "scan_replaced":lane.scan_replaced,
        "evaluations":lane.evaluations,
        "positive":lane.positive,
        "p99_event_start_ms":_p99(lane.event_start_ms),
        "p99_scan_ms":_p99(lane.scan_ms),
        "best":lane.best,
        "broadcast":False,
    }
    out=Path("runtime_state/oracle/oracle_live_execution/oracle_020_latest_state_exact_pricing_worker.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload,out

async def _serve(seconds):
    result=persistent.serve(Path.cwd(),seconds)
    if hasattr(result,"__await__"):
        return await result
    return result

def run(seconds=60.0):
    lane=install()

    print("[ORACLE-020] LATEST-STATE EXACT PRICING WORKER",flush=True)
    print("[TRANSPORT] existing QARB-061D WebSocket stream",flush=True)
    print("[EVENT_THREAD] state mutation only; exact scan removed",flush=True)
    print("[COALESCE] newest snapshot replaces stale pending snapshot per token",flush=True)
    print("[STALE_START] >750ms dropped before pricing",flush=True)
    print("[MID_SCAN] newer token state aborts older multi-size scan",flush=True)
    print("[HOT_MATH] ORACLE-018 exact PumpSwap SDK + hydrated DLMM",flush=True)
    print("[PRIVATE_KEY] not required",flush=True)
    print("[BROADCAST] disabled",flush=True)

    try:
        asyncio.run(_serve(float(seconds)))
    finally:
        lane.close()
        payload,out=report(lane)
        print(
            "[ORACLE020_COMPLETE] submitted=%d replaced=%d processed=%d stale=%d "
            "scan_replaced=%d evaluations=%d positive=%d p99_start_ms=%s p99_scan_ms=%s"
            %(payload["submitted"],payload["replaced_before_start"],payload["processed"],
              payload["stale_drops"],payload["scan_replaced"],payload["evaluations"],
              payload["positive"],str(payload["p99_event_start_ms"]),str(payload["p99_scan_ms"])),
            flush=True,
        )
        print("[REPORT] %s"%out,flush=True)
        print("[BROADCAST] disabled",flush=True)

        if getattr(q18,"_worker",None) is not None:
            q18._worker.close()
            q18._worker=None

    return 0

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=60.0)
    a=ap.parse_args(argv)
    return run(a.seconds)

if __name__=="__main__":
    raise SystemExit(main())
"""

test_src=r"""
import inspect
import unittest

from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20

class DummyLane:
    def __init__(self):
        self.rows=[]
    def submit(self,*args):
        self.rows.append(args)

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q20.EXECUTION_AUTHORITY)
        self.assertTrue(q20.PAPER_ONLY)
        self.assertFalse(q20.REAL_MONEY_MOVED)

    def test_latest_state_contract(self):
        lane=q20.LatestStateLane()
        lane.submit("T",{"x":1},1,1)
        lane.submit("T",{"x":2},2,2)
        self.assertEqual(lane.submitted,2)
        self.assertEqual(lane.replaced,1)
        self.assertEqual(lane.latest["T"][0]["x"],2)

    def test_stale_gate(self):
        self.assertEqual(q20.MAX_START_AGE_MS,750.0)

    def test_event_thread_does_not_price(self):
        s=inspect.getsource(q20._patched_process_event)
        self.assertIn("apply_account_event",s)
        self.assertIn("_lane.submit",s)
        self.assertNotIn("exact_snapshot_opportunities",s)

    def test_worker_is_exact(self):
        s=inspect.getsource(q20.LatestStateLane._price)
        self.assertIn("exact_snapshot_opportunities",s)
        self.assertIn("newer_waiting",s)

    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q20)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)
        self.assertNotIn("sendTransaction",s)

    def test_sizes(self):
        self.assertEqual(q20.FAST_SIZES,(0.001,0.010,0.050))
        self.assertEqual(q20.EXPAND_SIZES,(0.180,0.500,1.400))

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

run_src=r"""
from qseries_v2.oracle_execution.oracle_020_latest_state_exact_pricing_worker import main
if __name__=="__main__":
    raise SystemExit(main())
"""

MOD.write_text(textwrap.dedent(module_src).lstrip(),encoding="utf-8")
TEST.write_text(textwrap.dedent(test_src).lstrip(),encoding="utf-8")
RUN.write_text(textwrap.dedent(run_src).lstrip(),encoding="utf-8")

for f in (MOD,TEST,RUN):
    py_compile.compile(str(f),doraise=True)

print("[PASS] ORACLE-020 latest-state exact pricing worker installed")
print("[TRANSPORT] QARB-061D preserved")
print("[EVENT_THREAD] exact pricing removed from WebSocket event path")
print("[COALESCE] latest-state-per-token")
print("[STALE] >750ms start rejected")
print("[MID_SCAN] superseded scans aborted")
print("[HOT_MATH] ORACLE-018 exact SDK preserved")
print("[PRIVATE_KEY] not required")
print("[BROADCAST] disabled")
print("[OWNER] ORACLE")
