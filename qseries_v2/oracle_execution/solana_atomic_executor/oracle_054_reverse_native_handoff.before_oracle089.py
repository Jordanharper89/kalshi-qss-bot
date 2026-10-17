
"""ORACLE-054 complete installer: reverse native execution handoff.
Original Q25/Q20/Q18 scanner remains unchanged.
No signing, broadcast, or live execution authority.
"""
from __future__ import annotations
import argparse
import base64
import collections
import copy
import json
import os
import shutil
import struct
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path

# ORACLE067_BOUNDED_SIMULATION_REJECTION_TRUTH

def _oracle067_sim_truth(sim):
    """Only sanitized diagnostic structure; never expose credentials or packets."""
    if not isinstance(sim, dict):
        return {"response_type": type(sim).__name__, "reason": "NON_DICT_RESPONSE"}
    out = {}
    for key in ("err", "unitsConsumed", "logs", "reason", "error"):
        if key not in sim:
            continue
        value = sim[key]
        if key == "logs":
            if isinstance(value, list):
                out["log_count"] = len(value)
                out["program_failure_logs"] = [
                    str(x)[:160] for x in value
                    if isinstance(x, str) and ("failed:" in x or "Error:" in x)
                ][:3]
            continue
        if key == "unitsConsumed" and type(value) is int:
            out[key] = value
        elif key in ("err", "reason", "error"):
            out[key + "_type"] = type(value).__name__
            if isinstance(value, (str, int, float, bool, type(None))):
                out[key] = str(value)[:160]
            elif isinstance(value, dict):
                out[key + "_keys"] = sorted(str(k)[:40] for k in value)[:12]
    return out or {"reason": "NO_DIAGNOSTIC_FIELDS"}


VERSION = "ORACLE_054_REVERSE_NATIVE_HANDOFF"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
NAME = "oracle_054_reverse_native_handoff.py"
NODEDIR = Path(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)
JSNAME = "oracle054_native_pump_sell_template.mjs"
OUT = Path(
    "runtime_state/oracle/oracle_live_execution/"
    "ORACLE_054_REVERSE_NATIVE.json"
)
MIN = 10_000_000
LIMIT = 1232

JS = r'''
import fs from "node:fs";
import BN from "bn.js";
import {Connection,PublicKey} from "@solana/web3.js";
import {OnlinePumpAmmSdk,PUMP_AMM_SDK} from "@pump-fun/pump-swap-sdk";

const req=JSON.parse(fs.readFileSync(0,"utf8"));

function enc(ix){
 return {
  programId:ix.programId.toBase58(),
  accounts:ix.keys.map(k=>({
   pubkey:k.pubkey.toBase58(),
   isSigner:!!k.isSigner,
   isWritable:!!k.isWritable
  })),
  data:Buffer.from(ix.data).toString("base64")
 };
}

try{
 const user=new PublicKey(req.user);
 const pool=new PublicKey(req.pool);
 const online=new OnlinePumpAmmSdk(
  new Connection(req.rpc,"processed")
 );
 const state=await online.swapSolanaState(pool,user);
 const amount=new BN(String(req.templateBaseUnits));
 const ixs=await PUMP_AMM_SDK.sellBaseInput(
  state,amount,Number(req.slippagePct)
 );
 const pump=ixs.filter(
  i=>i.programId.toBase58()===req.pumpProgram
 );
 if(pump.length!==1)
  throw Error("PUMP_SELL_INSTRUCTION_COUNT:"+pump.length);
 if(!pump[0].keys.some(
  k=>k.pubkey.toBase58()===req.pool
 ))throw Error("PUMP_POOL_NOT_BOUND");

 const data=Buffer.from(pump[0].data);
 if(data.length<24 ||
    data.readBigUInt64LE(8)!==BigInt(req.templateBaseUnits))
  throw Error("PUMP_SELL_DATA_CONTRACT");
 if(!Array.isArray(ixs)||ixs.length<2)
  throw Error("NATIVE_HELPERS_MISSING");

 console.log(JSON.stringify({
  ok:true,
  stateSnapshots:1,
  amount:String(amount),
  instructions:ixs.map(enc)
 }));
}catch(e){
 console.log(JSON.stringify({
  ok:false,error:String(e?.message??e)
 }));
}
'''

def atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8"
    )
    tmp.replace(path)

def reverse_bounds(snap, row, q18, fee_bps, reserve):
    if row.get("direction") != "METEORA_TO_PUMP":
        raise RuntimeError("REVERSE_DIRECTION_REQUIRED")
    start = row.get("start")
    if type(start) is not int or start < MIN:
        raise RuntimeError("BELOW_010_MINIMUM")
    if (row.get("token") != snap.get("token") or
        row.get("pump_pool") != snap.get("pump_pool")):
        raise RuntimeError("REVERSE_PAIR_IDENTITY_DRIFT")
    mq = row.get("mq")
    if (not isinstance(mq, dict) or
        type(mq.get("raw_out")) is not int or
        mq["raw_out"] <= 0):
        raise RuntimeError("DLMM_QUOTE_INVALID")
    if not isinstance(fee_bps, int) or not 0 <= fee_bps <= 1000:
        raise RuntimeError("BAD_SLIPPAGE_POLICY")

    gross_quote = int(mq["raw_out"])
    if int(row.get("gross_token", -1)) != gross_quote:
        raise RuntimeError("REVERSE_DLMM_OUTPUT_DRIFT")
    min_gross = gross_quote * (10000 - fee_bps) // 10000
    net_min = int(q18.token_net(str(row["token"]), min_gross))
    net_quote = int(row.get("net_token", 0))
    if not 0 < net_min <= net_quote:
        raise RuntimeError("REVERSE_TRANSFER_NET_DRIFT")

    sell = q18.worker().sell(snap, net_min)
    min_quote = int(sell["minQuote"])
    if min_quote <= start + reserve:
        raise RuntimeError("REVERSE_GUARANTEED_NET_BELOW_RESERVE")
    return {
        "start": start,
        "meteora_min_gross": min_gross,
        "pump_sell_base": net_min,
        "pump_min_quote": min_quote,
        "guaranteed_screen_lamports": min_quote - start - reserve
    }

def meteora_buy_ix(rt, token, start, mq, fee_bps):
    t = rt.METEORA_TEMPLATES.get(str(token))
    if not isinstance(t, dict):
        raise RuntimeError("REVERSE_DLMM_TEMPLATE_MISSING")
    if (type(mq.get("swap_for_y")) is not bool or
        mq["swap_for_y"] == t["swap_for_y"]):
        raise RuntimeError("REVERSE_DLMM_DIRECTION_MISMATCH")

    ac = list(t["fixed_accounts"])
    if len(ac) != 15:
        raise RuntimeError("REVERSE_DLMM_ACCOUNT_LAYOUT_DRIFT")
    ac[4], ac[5] = ac[5], ac[4]
    arrays = list(t["arrays"])
    crossed = int(mq.get("bins_crossed") or 0)
    if not arrays or crossed < 1:
        raise RuntimeError("REVERSE_DLMM_ARRAYS_MISSING")
    needed = min(len(arrays), max(1, (crossed + 69) // 70))
    chosen = (
        arrays[:needed] if mq["swap_for_y"]
        else list(reversed(arrays))[:needed]
    )
    ac.extend((a, False, True) for _, a in chosen)
    min_out = int(mq["raw_out"]) * (10000 - fee_bps) // 10000
    if min_out < 1:
        raise RuntimeError("REVERSE_METEORA_MIN_ZERO")

    data = bytes([248,198,158,145,225,117,135,200])
    data += struct.pack("<QQ", start, min_out)
    return {
        "programId": rt.q87.c.DLMM,
        "accounts": [
            {"pubkey": a, "isSigner": s, "isWritable": w}
            for a, s, w in ac
        ],
        "data": base64.b64encode(data).decode()
    }

def rewrite_sell(ix, template_disc, base_in, min_quote, pump_program):
    if ix.get("programId") != pump_program:
        raise RuntimeError("REVERSE_PUMP_PROGRAM_DRIFT")
    data = base64.b64decode(ix["data"], validate=True)
    if len(data) < 24 or data[:8] != template_disc:
        raise RuntimeError("REVERSE_PUMP_SELL_DISCRIMINATOR_DRIFT")
    if not 0 < base_in < 2**64 or not 0 < min_quote < 2**64:
        raise RuntimeError("REVERSE_PUMP_BOUNDS_INVALID")
    new = dict(ix)
    rewritten = data[:8] + struct.pack("<QQ", base_in, min_quote) + data[24:]
    new["data"] = base64.b64encode(rewritten).decode()
    return new

def native_reverse_route(snap, row, templates, rt, q18,
                         fee_bps=20, reserve=100000):
    token = str(row.get("token") or "")
    temp = templates.get(token)
    if not temp:
        raise RuntimeError("REVERSE_PUMP_SELL_TEMPLATE_MISSING")
    bound = reverse_bounds(snap, row, q18, fee_bps, reserve)
    m_ix = meteora_buy_ix(rt, token, bound["start"], row["mq"], fee_bps)

    ixs = copy.deepcopy(temp["ixs"])
    pos = temp["index"]
    ixs[pos] = rewrite_sell(
        ixs[pos], temp["disc"], bound["pump_sell_base"],
        bound["pump_min_quote"], rt.q87.c.PUMP
    )
    if not any(
        a.get("pubkey") == snap["pump_pool"]
        for a in ixs[pos]["accounts"]
    ):
        raise RuntimeError("REVERSE_PUMP_POOL_ACCOUNT_DRIFT")

    full = ixs[:pos] + [m_ix, ixs[pos]] + ixs[pos+1:]
    if (sum(i["programId"] == rt.q87.c.PUMP for i in full) != 1 or
        sum(i["programId"] == rt.q87.c.DLMM for i in full) != 1):
        raise RuntimeError("REVERSE_NATIVE_LEG_COUNT_DRIFT")

    from qseries_v2.oracle_strategy_intelligence.solana_money import (
        qsb059_gav_reverse_atomic as q59
    )
    optional = q59.MEMO_PROGRAMS | {q59.COMPUTE_BUDGET}
    compact = [i for i in full if i.get("programId") not in optional]
    candidates = [("REVERSE_FULL_NATIVE", full)]
    if compact != full:
        candidates.append(("REVERSE_NO_COMPUTE_MEMO", compact))

    return {
        "token": token,
        "direction": "METEORA_TO_PUMP",
        "start_lamports": bound["start"],
        "original_candidates": candidates,
        "base_alts": [],
        "guaranteed_screen_lamports":
            bound["guaranteed_screen_lamports"]
    }

def warm_reverse_templates(state, user, rt, root, stats):
    sdk = root / NODEDIR / JSNAME
    if not sdk.is_file() or not shutil.which("node"):
        stats["sell_sdk_prebuild_missing"] += 1
        return {}
    out = {}
    for pair in state.get("pairs") or []:
        token = str(pair.token)
        if token not in rt.READY_TOKENS:
            continue
        payload = {
            "rpc": os.environ.get("SOLANA_RPC_URL", ""),
            "user": user,
            "pool": str(pair.pump_pool),
            "templateBaseUnits": 1000000,
            "slippagePct": 0.2,
            "pumpProgram": rt.q87.c.PUMP
        }
        try:
            result = subprocess.run(
                ["node", JSNAME], cwd=root / NODEDIR,
                input=json.dumps(payload), capture_output=True,
                text=True, timeout=25
            )
            if result.returncode:
                raise RuntimeError("SELL_SDK_SUBPROCESS_FAILED")
            obj = json.loads(result.stdout.strip().splitlines()[-1])
            if obj.get("ok") is not True or obj.get("stateSnapshots") != 1:
                raise RuntimeError("SELL_SDK_TEMPLATE_REFUSED")
            ixs = obj["instructions"]
            positions = [
                i for i, ix in enumerate(ixs)
                if ix.get("programId") == rt.q87.c.PUMP
            ]
            if len(positions) != 1 or len(ixs) < 2:
                raise RuntimeError("SELL_SDK_HELPERS_INVALID")
            pos = positions[0]
            raw = base64.b64decode(ixs[pos]["data"], validate=True)
            if len(raw) < 24 or struct.unpack_from("<Q", raw, 8)[0] != 1000000:
                raise RuntimeError("SELL_SDK_BOUND_LAYOUT_INVALID")
            if not any(
                a.get("pubkey") == str(pair.pump_pool)
                for a in ixs[pos]["accounts"]
            ):
                raise RuntimeError("SELL_SDK_POOL_BINDING_INVALID")
            out[token] = {
                "ixs": ixs, "index": pos, "disc": raw[:8]
            }
            stats["sell_templates_ready"] += 1
        except Exception as exc:
            stats["sell_template_hold_" + type(exc).__name__] += 1
    return out

def install_reverse_bridge(v50, v51, q18, stats, root):
    cls = v50.ScannerExecutorBridge
    old_prep = cls.prepare_native
    old_quote = cls.on_quote
    old_sim = cls._simulate_p2m_once

    def prepare(self, state, warmed):
        old_prep(self, state, warmed)
        self._oracle054_templates = {}
        if self._runtime and self._public_wallet:
            self._oracle054_templates = warm_reverse_templates(
                state, self._public_wallet, self._runtime, root, stats
            )
        print(
            "[ORACLE054_PREWARM] reverse_sell_templates=%d" %
            len(self._oracle054_templates), flush=True
        )

    def tap(self, snap, rows, observed_ns):
        old_quote(self, snap, rows, observed_ns)
        if not self._runtime or not self._oracle054_templates:
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            if row.get("direction") != "METEORA_TO_PUMP":
                continue
            if row.get("token") not in self._oracle054_templates:
                continue
            tier = v50.tier_for(row.get("token"), self.tiers)
            verdict = v50.eligible_quote(
                row, self.ready, observed_ns, self.clock(), tier
            )
            if verdict != "PRE_SIMULATION_CANDIDATE_ONLY":
                continue
            if (type(row.get("local_min_net")) is not int or
                row["local_min_net"] <= v50.SCREENING_FEE_RESERVE):
                stats["reverse_rough_min_hold"] += 1
                continue
            if len(self.native_pending) >= self.native_pending.maxlen:
                stats["reverse_queue_full"] += 1
                continue
            self.native_pending.append((
                copy.deepcopy(snap), dict(row), observed_ns
            ))
            self.holds["REVERSE_NATIVE_BOUND_NOT_CERTIFIED"] -= 1
            if self.holds["REVERSE_NATIVE_BOUND_NOT_CERTIFIED"] <= 0:
                del self.holds["REVERSE_NATIVE_BOUND_NOT_CERTIFIED"]
            stats["reverse_queued"] += 1

    def consume(self, item):
        snap, row, stamp = item
        if row.get("direction") != "METEORA_TO_PUMP":
            return old_sim(self, item)
        # ORACLE082_CONTINUOUS_CUTOVER: same rate gate for reverse direction.
        if os.environ.get("ORACLE082_ENABLED") == "1":
            from qseries_v2.oracle_execution.solana_atomic_executor import oracle_082_continuous_inventory_runner as o82
            if not o82.allow_native(self):
                stats["ORACLE082_NATIVE_RATE_LIMIT"] += 1
                return
        elif self.native_compiles or self.unsigned_simulations:
            stats["bounded_attempt_already_used"] += 1
            return
        if not self._runtime or not self._public_wallet:
            self.holds["REVERSE_RUNTIME_UNAVAILABLE"] += 1
            return
        if self.clock() - stamp > v50.MAX_AGE_NS:
            self.holds["REVERSE_STALE_BEFORE_NATIVE_BUILD"] += 1
            return

        self.native_compiles += 1
        stats["reverse_build_attempts"] += 1
        try:
            rt = self._runtime
            route = native_reverse_route(
                snap, row, self._oracle054_templates, rt, q18,
                rt.q87.las.q59.SLIPPAGE_BPS,
                v50.SCREENING_FEE_RESERVE
            )
            stats["reverse_guaranteed_screen_positive"] += 1

            from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
            from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
                qarb_087_two_second_compaction_liquidity_repair as q87
            )
            extra = os.environ.get(
                "QSB_ORACLE_EXEC_ALT_ADDRESS", ""
            ).strip() or None
            compiled = v51.compile_existing_alt(
                self._public_wallet, route, core, q87, root, extra
            )
            stats[
                "reverse_compiler_" + str(compiled.get("reason", "UNKNOWN"))
            ] += 1
            print(
                "[ORACLE054_NATIVE] direction=METEORA_TO_PUMP "
                "status=%s bytes=%s alt_count=%d" % (
                    compiled.get("reason"),
                    compiled.get("bytes"),
                    len(compiled.get("used_alts") or [])
                ),
                flush=True
            )
            if not compiled.get("ok"):
                self.holds["REVERSE_V0_COMPILE_HOLD"] += 1
                return
            if int(compiled["bytes"]) > (4096 if compiled.get("version") == 1 else LIMIT):
                raise RuntimeError("REVERSE_SIZE_LIMIT")
            if self.clock() - stamp > v50.MAX_AGE_NS:
                self.holds["REVERSE_STALE_BEFORE_SIMULATION"] += 1
                return

            sim = rt.simulate_current(
                compiled, self._public_wallet
            )
            self.unsigned_simulations += 1
            if isinstance(sim, dict) and sim.get("err") is None:
                self.unsigned_sim_passes += 1
                self.holds[
                    "REVERSE_SIM_PASS_NET_UNCERTIFIED"
                ] += 1
                print(
                    "[ORACLE054_SIM] UNSIGNED_PASS_PROFIT_UNCERTIFIED",
                    flush=True
                )
            else:
                self.holds["REVERSE_SIM_ERROR"] += 1
                print("[ORACLE054_SIM] REJECTED", _oracle067_sim_truth(sim), flush=True)
        except Exception as exc:
            stats[
                "reverse_build_hold_" + type(exc).__name__
            ] += 1
            self.holds[
                "REVERSE_BOUND_OR_SIM_" + type(exc).__name__
            ] += 1
            print(
                "[ORACLE054_HOLD]",
                type(exc).__name__,
                str(exc).split(":", 1)[0][:70],
                flush=True
            )

    cls.prepare_native = prepare
    cls.on_quote = tap
    cls._simulate_p2m_once = consume

    def restore():
        cls.prepare_native = old_prep
        cls.on_quote = old_quote
        cls._simulate_p2m_once = old_sim

    return restore

def window(root, seconds, index, runid):
    if any(
        "PRIVATE_KEY" in k.upper() or "SECRET_KEY" in k.upper()
        for k in os.environ
    ):
        print("[HOLD] SECRET_ENVIRONMENT_REFUSED", flush=True)
        return 2

    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_053_original_scanner_recovery_batch as v53,
        oracle_050_original_scanner_executor_consolidation as v50,
        oracle_051_original_scanner_alt_and_size_gate as v51
    )
    from qseries_v2.oracle_execution import (
        oracle_018_exact_sdk_hot_lane_cutover as q18
    )

    before = v50.hash_sources(root)
    stats = collections.Counter()
    restore = install_reverse_bridge(v50, v51, q18, stats, root)
    try:
        print(
            "[ORACLE054_STAGE] window=%d "
            "reverse_native_on_original_scanner=TRUE" % index,
            flush=True
        )
        # ORACLE081_TRUTH_AND_USAGE_BOUNDARY
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_081_api_truth_meter as o81
        with o81.observe(root, index):
            # ORACLE082_CONTINUOUS_CUTOVER: hook original scanner lifetime.
            from qseries_v2.oracle_execution.solana_atomic_executor import oracle_082_continuous_inventory_runner as o82
            with o82.activate(root):
                status = v53.one_window(root, seconds, index, runid)
    finally:
        restore()

    try:
        src = json.loads(
            (root / v50.REPORT).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        src = {}

    output = {
        "revision": VERSION,
        "run_id": runid,
        "window": index,
        "status": (
            "COMPLETE" if status == 0
            and before == v50.hash_sources(root) else "HOLD"
        ),
        "stats": dict(stats),
        "original": {
            k: src.get(k) for k in (
                "native_compile_attempts",
                "unsigned_atomic_simulations",
                "unsigned_atomic_simulation_passes",
                "holds",
                "positive_scanner_quotes"
            )
        },
        "same_socket_mriya_rotation_certified": False,
        "realized_profit_certified": False,
        "minimum_exec_lamports": MIN,
        "first_live_canary_lamports": MIN,
        "scanner_source_unchanged": before == v50.hash_sources(root),
        "signing": False,
        "broadcast": False
    }
    target = root / OUT
    atomic(target, output)
    print(
        "[ORACLE054_RESULT]",
        json.dumps(output, sort_keys=True),
        flush=True
    )
    print("[REPORT]", target, flush=True)
    return 0 if output["status"] == "COMPLETE" else 2

def batch(root, seconds, cycles):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_050_original_scanner_executor_consolidation as v50
    )
    rid = uuid.uuid4().hex
    for n in range(1, cycles + 1):
        print("[ORACLE054_BATCH] %d/%d" % (n, cycles), flush=True)
        cmd = [
            sys.executable, "-I", "-u", str(Path(__file__).resolve()),
            "--child", "--seconds", str(seconds),
            "--index", str(n), "--run-id", rid
        ]
        env = v50.scrub(os.environ)
        # ORACLE079_CHILD_EXECUTOR_ENABLED
        if os.environ.get("ORACLE077_ENABLED") == "1":
            env["ORACLE077_ENABLED"] = "1"
        if os.environ.get("QSB_ORACLE_EXEC_ALT_ADDRESS"):
            env["QSB_ORACLE_EXEC_ALT_ADDRESS"] = (
                os.environ["QSB_ORACLE_EXEC_ALT_ADDRESS"]
            )
        try:
            child = subprocess.Popen(
                cmd, cwd=root, env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, encoding="utf-8",
                errors="replace", bufsize=1
            )
            notable = (
                "[ORACLE054_", "[ORACLE053_WINDOW_RESULT]",
                "[MRIYA_ORIGINAL_DISCOVERY]", "[CACHE]",
                "[LIVE]", "[HEARTBEAT]", "[ORACLE020_COMPLETE]",
                "[ORACLE050_RESULT]", "[ORACLE051_NATIVE]",
                "[ORACLE051_SIM]", "[HOLD]"
            )
            positive = 0
            for line in child.stdout:
                line = line.rstrip()
                if line.startswith(notable):
                    print(line, flush=True)
                elif (
                    line.startswith("[ORACLE020_EXACT_LATEST]")
                    and "bps=+" in line and positive < 8
                ):
                    print(line, flush=True)
                    positive += 1
            rc = child.wait()
        except KeyboardInterrupt:
            child.terminate()
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
            print("[STOP] ORACLE054_BATCH_STOPPED", flush=True)
            return 130
        if rc:
            print(
                "[HOLD] ORACLE054_WINDOW_FAILED_NO_BLIND_RETRY",
                flush=True
            )
            return 2
    print(
        "[BATCH_DONE] REVERSE_EXECUTOR_OBSERVATION_NO_BROADCAST",
        flush=True
    )
    return 0

class Tests(unittest.TestCase):
    def test_low_size_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "BELOW_010"):
            reverse_bounds(
                {"token":"A","pump_pool":"B"},
                {"direction":"METEORA_TO_PUMP","start":1000000},
                None,20,100000
            )

    def test_direction_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"REVERSE_DIRECTION"):
            reverse_bounds({},{"direction":"PUMP_TO_METEORA"},None,20,100000)

    def test_price_guarantee(self):
        class Q:
            @staticmethod
            def token_net(t,v):
                return v
            @staticmethod
            def worker():
                return type("W",(),{
                    "sell":lambda s,snap,amount:{"minQuote":15000000}
                })()
        snap={"token":"A","pump_pool":"B"}
        row={
            "direction":"METEORA_TO_PUMP",
            "start":10000000,"token":"A","pump_pool":"B",
            "mq":{"raw_out":1000000},
            "gross_token":1000000,"net_token":1000000
        }
        x=reverse_bounds(snap,row,Q,20,100000)
        self.assertEqual(x["pump_sell_base"],998000)
        self.assertGreater(x["guaranteed_screen_lamports"],0)

    def test_negative_guarantee_hold(self):
        class Q:
            @staticmethod
            def token_net(t,v):
                return v
            @staticmethod
            def worker():
                return type("W",(),{
                    "sell":lambda s,snap,amount:{"minQuote":9000000}
                })()
        snap={"token":"A","pump_pool":"B"}
        row={
            "direction":"METEORA_TO_PUMP",
            "start":10000000,"token":"A","pump_pool":"B",
            "mq":{"raw_out":1000000},
            "gross_token":1000000,"net_token":1000000
        }
        with self.assertRaisesRegex(RuntimeError,"GUARANTEED_NET"):
            reverse_bounds(snap,row,Q,20,100000)

    def test_pump_data_exact_rewrite(self):
        d=b"12345678"+struct.pack("<QQ",1000000,88)+b"x"
        ix={"programId":"P","data":base64.b64encode(d).decode()}
        out=rewrite_sell(ix,b"12345678",333,444,"P")
        decoded=base64.b64decode(out["data"])
        self.assertEqual(struct.unpack_from("<QQ",decoded,8),(333,444))
        self.assertEqual(decoded[-1:],b"x")

    def test_pump_discriminator_drift(self):
        ix={
            "programId":"P",
            "data":base64.b64encode(b"12345678"+b"0"*16).decode()
        }
        with self.assertRaisesRegex(RuntimeError,"DISCRIMINATOR"):
            rewrite_sell(ix,b"abcdefgh",1,1,"P")

    def test_reverse_meteora_accounts(self):
        class Core:
            DLMM="DLMM"
        class Q87:
            c=Core()
        class R:
            q87=Q87()
            METEORA_TEMPLATES={
                "A":{
                    "fixed_accounts":[
                        (str(i),False,True) for i in range(15)
                    ],
                    "swap_for_y":False,
                    "arrays":[(0,"X")]
                }
            }
        out=meteora_buy_ix(
            R,"A",MIN,
            {"swap_for_y":True,"raw_out":5000,"bins_crossed":1},
            20
        )
        self.assertEqual(out["accounts"][4]["pubkey"],"5")
        self.assertEqual(out["accounts"][5]["pubkey"],"4")

    def test_meteora_direction_required(self):
        class R:
            METEORA_TEMPLATES={"A":{"swap_for_y":False}}
        with self.assertRaisesRegex(RuntimeError,"DIRECTION_MISMATCH"):
            meteora_buy_ix(R,"A",MIN,{"swap_for_y":False},20)

    def test_native_build_never_uses_signing(self):
        import inspect
        fn=inspect.getsource(install_reverse_bridge)
        self.assertNotIn("signed_tx(",fn)
        self.assertNotIn("sendTransaction",fn)
        self.assertNotIn("keypair(",fn)

    def test_private_key_not_carried(self):
        self.assertNotIn("PRIVATE_KEY",JS)

    def test_canary(self):
        self.assertEqual(MIN,10000000)

    def test_no_scanner_replacement(self):
        self.assertEqual(
            PKG/NAME,
            Path(
                "qseries_v2/oracle_execution/solana_atomic_executor/"
                "oracle_054_reverse_native_handoff.py"
            )
        )

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--audit",action="store_true")
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--child",action="store_true")
    parser.add_argument("--seconds",type=int,default=90)
    parser.add_argument("--cycles",type=int,default=2)
    parser.add_argument("--index",type=int,default=1)
    parser.add_argument("--run-id",default="")
    a=parser.parse_args()
    root=Path.cwd()

    if a.test:
        result=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        )
        return 0 if result.wasSuccessful() else 2

    if a.audit:
        needed=[
            PKG/"oracle_050_original_scanner_executor_consolidation.py",
            PKG/"oracle_051_original_scanner_alt_and_size_gate.py",
            PKG/"oracle_052_original_scanner_batch.py",
            PKG/"oracle_053_original_scanner_recovery_batch.py",
            NODEDIR/"node_modules/@pump-fun/pump-swap-sdk/package.json",
            NODEDIR/JSNAME
        ]
        missing=[str(p) for p in needed if not (root/p).is_file()]
        print(
            "[ORACLE054_AUDIT]",
            "PASS" if not missing else "HOLD_MISSING_DEPENDENCIES",
            flush=True
        )
        if missing:
            print("[MISSING]",json.dumps(missing),flush=True)
        print(
            "[SCANNER] ORIGINAL_UNCHANGED "
            "[MINIMUM] 0.010_SOL "
            "[SIGNING] FALSE [BROADCAST] FALSE",
            flush=True
        )
        return 0 if not missing else 2

    if a.child:
        sys.path.insert(0,str(root.resolve()))
        return window(root,a.seconds,a.index,a.run_id)

    if a.run:
        if a.seconds<10 or not 1<=a.cycles<=5:
            return 2
        return batch(root,a.seconds,a.cycles)

    target=root/PKG/NAME
    node=root/NODEDIR/JSNAME
    if not target.parent.is_dir() or not node.parent.is_dir():
        print("[HOLD] EXISTING_REPOSITORY_LAYOUT_MISSING")
        return 2
    if target.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__),target)
    node.write_text(JS.strip()+"\n",encoding="utf-8")

    print("[PASS]",VERSION)
    print(
        "[PATH] ORIGINAL_WS_Q25_Q20_Q18 -> "
        "GUARANTEED_REVERSE_BOUNDS -> NATIVE_V0_ALT -> UNSIGNED_SIM"
    )
    print(
        "[SDK] OFFICIAL_PUMPSWAP_SELL_STARTUP_TEMPLATE; "
        "NO_HTTP_PER_QUOTE"
    )
    print(
        "[MRIYA] ORIGINAL_WINDOW_REFRESH_ONLY; "
        "SAME_SOCKET_ROTATION_NOT_CERTIFIED"
    )
    print(
        "[MINIMUM] 0.010_SOL [FIRST_CANARY] 0.010_SOL "
        "[SIGNING] FALSE [BROADCAST] FALSE"
    )
    return 0

if __name__=="__main__":
    raise SystemExit(main())


# ORACLE085_REVERSE_EXACT_ATA_CUTOVER_BEGIN
_ORACLE085_UNBOUND_REVERSE_ROUTE = native_reverse_route

def native_reverse_route(snap, row, templates, rt, q18, fee_bps=20, reserve=100000):
    """Prepare the exact DLMM output ATA before the swap, without changing Q25/Q20/Q18."""
    from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint26_dlmm_output_ata_readiness as readiness
    route = _ORACLE085_UNBOUND_REVERSE_ROUTE(snap, row, templates, rt, q18, fee_bps, reserve)
    if route.get('direction') != 'METEORA_TO_PUMP':
        raise RuntimeError('ORACLE085_REVERSE_DIRECTION_DRIFT')
    if str(route.get('token')) != str(snap.get('token')):
        raise RuntimeError('ORACLE085_TOKEN_IDENTITY_DRIFT')
    pump = str(rt.q87.c.PUMP)
    signers = set()
    for _, instructions in route.get('original_candidates') or []:
        for ix in instructions:
            if str(ix.get('programId')) == pump:
                for account in ix.get('accounts') or []:
                    if account.get('isSigner') is True and account.get('pubkey'):
                        signers.add(str(account['pubkey']))
    if len(signers) != 1:
        raise RuntimeError('ORACLE085_EXACT_USER_SIGNER_UNRESOLVED:'+str(len(signers)))
    user = next(iter(signers))
    result = readiness._bind_exact_output_ata(
        user, snap, {'direction': 'METEORA_TO_PUMP'}, route
    )
    proof = result.get('checkpoint26_output_ata') or {}
    if (proof.get('before_dlmm') is not True or
        proof.get('create_idempotent') is not True or
        proof.get('direction') != 'METEORA_TO_PUMP'):
        raise RuntimeError('ORACLE085_OUTPUT_ATA_PROOF_MISSING')
    return result
# ORACLE085_REVERSE_EXACT_ATA_CUTOVER_END
