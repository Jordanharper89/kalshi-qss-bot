"""ORACLE-051 full installer: original scanner 0.010+ sizes and existing ALT native compile.

Copies this complete file to executor package; makes no changes to original scanner source.
No signing, order sending, ALT creation, ALT extension, or wallet private-key access.
"""
from __future__ import annotations
import re

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

VERSION = "ORACLE_051_ORIGINAL_SCANNER_ALT_AND_SIZE_GATE"
PKG = Path("qseries_v2/oracle_execution/solana_atomic_executor")
MODULE = PKG / "oracle_051_original_scanner_alt_and_size_gate.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_051_ALT_SIZE_GATE.json")
MIN_LAMPORTS = 10_000_000
FIRST_CANARY_LAMPORTS = 10_000_000
LIMIT = 1232
ALT_PROGRAM = "AddressLookupTab1e1111111111111111111111111"


def sizes_at_least_010(values):
    chosen = tuple(float(x) for x in values if float(x) >= .010 - 1e-12)
    if not chosen or chosen[0] < .010 - 1e-12:
        raise RuntimeError("ORACLE051_EXECUTION_SIZE_CURVE_EMPTY")
    return chosen


def guarded_quote(row, original_verdict):
    if not isinstance(row, dict):
        return "HOLD_BAD_QUOTE"
    size = row.get("start")
    if type(size) is not int or size < MIN_LAMPORTS:
        return "HOLD_BELOW_010_SOL_MINIMUM"
    return original_verdict


def candidate_is_safe(row):
    if not isinstance(row, dict):
        return False
    name = str(row.get("name") or "")
    if not name or "PUMP_METEORA_ONLY" in name:
        return False
    ixs = row.get("instructions")
    if not isinstance(ixs, list) or len(ixs) < 3:
        return False
    return all(isinstance(i, dict) and i.get("programId") and isinstance(i.get("accounts"), list)
               and isinstance(i.get("data"), str) for i in ixs)


def instruction_keys(ixs):
    program_ids = {str(x.get("programId") or "") for x in ixs}
    accounts = {}
    for ix in ixs:
        for a in ix.get("accounts") or []:
            k = str(a.get("pubkey") or "")
            if not k:
                continue
            old = accounts.get(k, (False, False))
            accounts[k] = (old[0] or bool(a.get("isSigner")), old[1] or bool(a.get("isWritable")))
    return program_ids, accounts


def saved_table_candidates(root, token, extra=None):
    path = (Path(root) / "runtime_state/qseries/qarb_execution_engineering/qarb_096_micro_alt.json")
    choices = []
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            rec = (doc.get("tables") or {}).get(token) or {}
            if isinstance(rec, dict) and isinstance(rec.get("address"), str):
                choices.append(rec["address"])
        except (OSError, ValueError, TypeError):
            pass
    if extra:
        choices.append(extra)
    return list(dict.fromkeys(x.strip() for x in choices if isinstance(x, str) and x.strip()))


def verified_table(core, address, user, ixs):
    # Read-only on-chain attestation before handing addresses to the canonical v0 compiler.
    if not isinstance(address, str) or address == user:
        return None, "INVALID_LOOKUP_TABLE_ADDRESS"
    try:
        from solders.pubkey import Pubkey
        Pubkey.from_string(address)
        response = core.rpc("getAccountInfo", [address, {"encoding": "base64", "commitment": "confirmed"}])
        value = (response or {}).get("value")
        if not isinstance(value, dict) or value.get("owner") != ALT_PROGRAM:
            return None, "NOT_AN_ADDRESS_LOOKUP_TABLE"
        datum = value.get("data")
        if not isinstance(datum, list) or not datum:
            return None, "ALT_DATA_MISSING"
        raw = base64.b64decode(datum[0], validate=True)
        if len(raw) < 56 or (len(raw) - 56) % 32:
            return None, "ALT_BINARY_STATE_INVALID"
        entries = [raw[i:i+32] for i in range(56, len(raw), 32)]
        programs, meta = instruction_keys(ixs)
        useful = []
        for k, (signer, _writable) in meta.items():
            if k == user or signer or k in programs:
                continue
            try:
                needle = core.b58d(k)
            except Exception:
                continue
            if needle in entries:
                useful.append(k)
        if len(set(useful)) < 2:
            return None, "ALT_INSUFFICIENT_INSTRUCTION_COVERAGE"
        return {"address": address, "covered_accounts": len(set(useful)),
                "address_count": len(entries)}, None
    except Exception as exc:
        return None, "ALT_CHECK_" + type(exc).__name__


def compile_existing_alt(user, route, core, q87, root, extra_alt=None):
    # ORACLE077_PERSISTENT_NATIVE_DISPATCH
    if __import__('os').environ.get('ORACLE077_ENABLED') == '1':
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_077_native_executor as ex77
        return ex77.compile_native(user, route, core, q87, root, extra_alt)
    # This is an unsigned, full-helper compilation only. Never touches keypair/signed_tx/send.
    result = {"ok": False, "reason": "HOLD", "attempts": [], "used_alts": [],
              "min_trade_lamports": MIN_LAMPORTS}
    start = route.get("start_lamports")
    if type(start) is not int or start < MIN_LAMPORTS:
        result["reason"] = "HOLD_BELOW_010_SOL_MINIMUM"
        return result
    token = str(route.get("token") or "")
    if not token:
        result["reason"] = "HOLD_TOKEN_MISSING"
        return result
    candidates = [x for x in q87.repaired_candidates(route) if candidate_is_safe(x)]
    if not candidates:
        result["reason"] = "HOLD_NO_HELPER_COMPLETE_CANDIDATE"
        return result
    choices = saved_table_candidates(root, token, extra_alt)
    for val in route.get("base_alts") or []:
        if isinstance(val, str) and val not in choices:
            choices.append(val)
    # Use complete native routes; do not optimize by removing essential ATA / wrap / close helpers.
    from_vetted = []
    blockhash = None
    for ixrow in candidates:
        # The canonical pool programs must remain present exactly once each.
        programs = [i["programId"] for i in ixrow["instructions"]]
        if programs.count(core.PUMP) != 1 or programs.count(core.DLMM) != 1:
            result["attempts"].append({"candidate": ixrow["name"],
                                       "error": "HOLD_MISSING_OR_DUPLICATE_VENUE_LEG"})
            continue
        known = []
        for address in choices[:4]:
            if address in {x["address"] for x in known}:
                continue
            rec, error = verified_table(core, address, user, ixrow["instructions"])
            if rec:
                known.append(rec)
            elif error:
                result["attempts"].append({"candidate": ixrow["name"], "alt_check": error})
        attempted_alts = set()
        for selected in (known, known[:1], []):
            addresses = [x["address"] for x in selected]
            if tuple(addresses) in attempted_alts:
                continue
            attempted_alts.add(tuple(addresses))
            try:
                if blockhash is None:
                    blockhash = core.rpc("getLatestBlockhash", [{"commitment": "processed"}])["value"]["blockhash"]
                msg, raw = core.compile_v0(user, ixrow["instructions"], addresses, blockhash)
                raw = bytes(raw)
                if len(raw) > LIMIT or not raw or raw[0] != 1 or raw[1:65] != bytes(64):
                    raise RuntimeError("NONCANONICAL_UNSIGNED_V0_PACKET")
                if raw[65] != 128:
                    raise RuntimeError("NOT_A_VERSIONED_V0_MESSAGE")
                from_vetted.append({"name": ixrow["name"], "msg": msg, "raw": raw,
                                    "bytes": len(raw), "alts": addresses})
                result["attempts"].append({"candidate": ixrow["name"],
                                           "alt_count": len(addresses), "bytes": len(raw), "ok": True})
            except Exception as exc:
                code = str(exc)
                if code.startswith("ATOMIC_TX_TOO_LARGE:"):
                    code = "ATOMIC_TX_TOO_LARGE:" + code.rsplit(":", 1)[1]
                else:
                    # ORACLE059_NATIVE_COMPILE_TRUTH
                    code = type(exc).__name__
                detail = str(exc)
                detail = re.sub(r"(?i)(api-key=)[^&\s]+", r"\1[REDACTED]", detail)
                detail = re.sub(r"(?i)(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+", r"\1=[REDACTED]", detail)
                result["attempts"].append({"candidate": ixrow["name"],
                    "alt_count": len(addresses), "error": code, "detail": detail[:240]})
        if from_vetted:
            # Stop after a legal helper-complete route; prefer smallest valid unsigned packet.
            break
    if not from_vetted:
        result["reason"] = "HOLD_NO_LEGAL_HELPER_COMPLETE_V0"
        # ORACLE071_COMPILER_ATTEMPT_TRUTH
        for attempt in result['attempts'][:8]:
            print('[ORACLE071_COMPILE_ATTEMPT]', {k: attempt.get(k) for k in ('candidate', 'alt_count', 'alt_check', 'error', 'detail', 'bytes') if k in attempt}, flush=True)
        return result
    best = min(from_vetted, key=lambda x: x["bytes"])
    result.update({"ok": True, "msg": best["msg"], "raw": best["raw"],
                   "bytes": best["bytes"], "candidate": best["name"],
                   "used_alts": best["alts"], "reason": "LEGAL_UNSIGNED_V0"})
    return result


def set_minimum_size_curve(q20, m, pd):
    old = (q20.FAST_SIZES, m.SIZES, pd.SIZES)
    q20.FAST_SIZES = sizes_at_least_010(q20.FAST_SIZES)
    pd.SIZES = sizes_at_least_010(pd.SIZES)
    m.SIZES = sizes_at_least_010(m.SIZES)
    return old


def install_hooks(root):
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_050_original_scanner_executor_consolidation as v50
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87

    prior_sizes = set_minimum_size_curve(q20, m, pd)
    old_eligible = v50.eligible_quote
    old_compile = rt.compile_current
    old_simulate = rt.simulate_current
    extra = os.environ.get("QSB_ORACLE_EXEC_ALT_ADDRESS", "").strip() or None
    stats = {"compile_attempts": 0, "legal_compiles": 0, "simulation_attempts": 0,
             "alt_compiles": 0, "min_pricing_size": min(q20.FAST_SIZES),
             "last_candidate": None, "last_alt_count": 0,
             "last_compile_status": "NOT_ATTEMPTED", "last_simulation_error": "NOT_ATTEMPTED"}

    def admission(row, ready, stamp_ns, now_ns, tier):
        return guarded_quote(row, old_eligible(row, ready, stamp_ns, now_ns, tier))

    def compile_hook(user, route):
        stats["compile_attempts"] += 1
        result = compile_existing_alt(user, route, core, q87, root, extra)
        stats["last_compile_status"] = result.get("reason")
        stats["last_alt_count"] = len(result.get("used_alts") or [])
        stats["last_candidate"] = result.get("candidate")
        if result.get("ok"):
            stats["legal_compiles"] += 1
            stats["alt_compiles"] += bool(result.get("used_alts"))
        print("[ORACLE051_NATIVE] status=%s candidate=%s bytes=%s alts=%s attempts=%d" % (
            result.get("reason"), str(result.get("candidate")), result.get("bytes"),
            len(result.get("used_alts") or []), len(result.get("attempts") or [])), flush=True)
        # ORACLE059_NATIVE_COMPILE_TRUTH - bounded per-candidate compiler outcomes.
        for attempt in (result.get("attempts") or [])[:12]:
            safe = {k: attempt.get(k) for k in ("candidate","alt_count","bytes","error","detail","alt_check") if k in attempt}
            print("[ORACLE059_COMPILE_ATTEMPT] " + json.dumps(safe,sort_keys=True,default=str),flush=True)
        # Do not print wallet, RPC URL, ALT file contents, or secret information.
        return result

    def simulation_hook(compiled, user):
        stats["simulation_attempts"] += 1
        sim = old_simulate(compiled, user)
        code = sim.get("err") if isinstance(sim, dict) else "UNKNOWN"
        stats["last_simulation_error"] = code
        print("[ORACLE051_SIM] status=%s units=%s" % (
            "PASS_NET_UNCERTIFIED" if code is None else "REJECTED",
            sim.get("units") if isinstance(sim, dict) else None), flush=True)
        return sim

    def scrub_hook(env):
        out = original_scrub(env)
        val = env.get("QSB_ORACLE_EXEC_ALT_ADDRESS")
        if val:
            out["QSB_ORACLE_EXEC_ALT_ADDRESS"] = val
        return out

    original_scrub = v50.scrub
    v50.eligible_quote = admission
    rt.compile_current = compile_hook
    rt.simulate_current = simulation_hook
    if __import__('os').environ.get('ORACLE077_ENABLED') == '1':
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_077_native_executor as ex77
        ex77.guard(core)
        rt.simulate_current = ex77.simulate_native
        print('[ORACLE051_NATIVE] [ORACLE077_SIMULATOR_ATTACHED]', flush=True)
    v50.scrub = scrub_hook

    def restore():
        v50.eligible_quote = old_eligible
        rt.compile_current = old_compile
        rt.simulate_current = old_simulate
        v50.scrub = original_scrub
        q20.FAST_SIZES, m.SIZES, pd.SIZES = prior_sizes

    return v50, stats, restore


def run_once(root, seconds, service=False):
    import hashlib
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_050_original_scanner_executor_consolidation as v50
    sources = v50.hash_sources(root)
    v50mod, stats, restore = install_hooks(root)
    status = 2
    try:
        print("[SCANNER] ORIGINAL_Q25_Q20_Q18_SHARD_TRANSPORT_UNCHANGED", flush=True)
        print("[SIZE_MIN] 0.010_SOL [FIRST_CANARY] 0.010_SOL", flush=True)
        print("[COMPILER] FULL_NATIVE_HELPERS_AND_EXISTING_ALT", flush=True)
        print("[SIGNING] FALSE [BROADCAST] FALSE", flush=True)
        status = v50mod.run_original(root, seconds)
    finally:
        restore()
        original_report = root / v50.REPORT
        original_status = "REPORT_MISSING"
        if original_report.is_file():
            try:
                original_status = json.loads(original_report.read_text(encoding="utf-8")).get("status", "UNKNOWN")
            except (OSError, ValueError):
                original_status = "REPORT_UNREADABLE"
        payload = {"revision": VERSION, "status": "ORIGINAL_SCANNER_ALT_SIZE_GATE_OBSERVED",
                   "original_scanner_status": original_status, "original_exit_code": status,
                   "scanner_source_hashes_unchanged": sources == v50.hash_sources(root),
                   "first_canary_lamports": FIRST_CANARY_LAMPORTS,
                   "minimum_executable_lamports": MIN_LAMPORTS,
                   "signing": False, "broadcast": False,
                   "live_native_profit_certified": False, "statistics": stats,
                   "original_scanner_report": str(v50.REPORT)}
        report = root / REPORT
        report.parent.mkdir(parents=True, exist_ok=True)
        temp = report.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        temp.replace(report)
        print("[ORACLE051_REPORT]", report, flush=True)
        if not payload["scanner_source_hashes_unchanged"]:
            status = 2
    return status


def parent(root, seconds):
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_050_original_scanner_executor_consolidation as v50
    cmd = [sys.executable, "-I", "-u", str(Path(__file__).resolve()), "--child", "--seconds", str(seconds)]
    env = v50.scrub(os.environ)
    if os.environ.get("QSB_ORACLE_EXEC_ALT_ADDRESS"):
        env["QSB_ORACLE_EXEC_ALT_ADDRESS"] = os.environ["QSB_ORACLE_EXEC_ALT_ADDRESS"]
    return subprocess.call(cmd, cwd=root, env=env)


def service(root, seconds):
    consecutive_failures = 0
    try:
        while True:
            result = parent(root, seconds)
            consecutive_failures = consecutive_failures + 1 if result else 0
            print("[ORACLE051_WINDOW] exit_code=%d" % result, flush=True)
            if consecutive_failures >= 3:
                print("[HOLD] THREE_FAILED_WINDOWS", flush=True)
                return 2
            time.sleep(2 if result == 0 else 10 * consecutive_failures)
    except KeyboardInterrupt:
        print("[STOP] ORACLE051_SERVICE", flush=True)
        return 130


class Tests(unittest.TestCase):
    def test_size_curve(self):
        self.assertEqual(sizes_at_least_010((.001, .005, .010, .015, .180)), (.01, .015, .18))

    def test_no_micro_handoff(self):
        self.assertEqual(guarded_quote({"start": 1_000_000}, "PRE_SIMULATION_CANDIDATE_ONLY"),
                         "HOLD_BELOW_010_SOL_MINIMUM")

    def test_exact_canary(self):
        self.assertEqual(FIRST_CANARY_LAMPORTS, 10_000_000)

    def test_shell_exclusion(self):
        row = {"name": "PUMP_METEORA_ONLY", "instructions": [{"programId": "p", "accounts": [], "data": ""}] * 3}
        self.assertFalse(candidate_is_safe(row))

    def test_saved_table(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "runtime_state/qseries/qarb_execution_engineering/qarb_096_micro_alt.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"tables": {"T": {"address": "ALT"}}}))
            self.assertEqual(saved_table_candidates(d, "T"), ["ALT"])

    def test_compile_size_and_existing_alt(self):
        class Core:
            PUMP = "PUMP"
            DLMM = "DLMM"
            @staticmethod
            def compile_v0(user, ixs, alts, blockhash):
                if not alts:
                    raise RuntimeError("ATOMIC_TX_TOO_LARGE:1257")
                return b"\x80msg", bytes([1]) + bytes(64) + bytes([128]) + bytes(1000)
            @staticmethod
            def rpc(method, params):
                return {"value": {"blockhash": "BH"}}
        class Q87:
            @staticmethod
            def repaired_candidates(route):
                return [{"name": "FULL", "instructions": [
                    {"programId": n, "accounts": [], "data": ""}
                    for n in ("SYSTEM", "PUMP", "DLMM")]}]
        route = {"token": "T", "start_lamports": 10_000_000,
                 "original_candidates": [], "base_alts": ["ALT"]}
        with patch(__name__ + ".verified_table", return_value=({"address": "ALT", "covered_accounts": 3}, None)):
            result = compile_existing_alt("USER", route, Core(), Q87(), Path.cwd())
        self.assertTrue(result["ok"])
        self.assertEqual(result["used_alts"], ["ALT"])
        self.assertLessEqual(result["bytes"], LIMIT)

    def test_reject_noncanary_small(self):
        route = {"token": "T", "start_lamports": 1_000_000}
        result = compile_existing_alt("W", route, None, None, Path.cwd())
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "HOLD_BELOW_010_SOL_MINIMUM")

    def test_code_has_no_signing(self):
        import inspect
        source = inspect.getsource(compile_existing_alt)
        self.assertNotIn("signed_tx(", source)
        self.assertNotIn("send(", source)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--audit", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--service", action="store_true")
    p.add_argument("--child", action="store_true")
    p.add_argument("--seconds", type=int, default=120)
    args = p.parse_args()
    root = Path.cwd()
    if args.test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    if args.audit:
        target = root / PKG / "oracle_050_original_scanner_executor_consolidation.py"
        print("[Q50_DEPENDENCY]", target.is_file())
        print("[MINIMUM_SIZE_SOL] 0.010")
        print("[FIRST_CANARY_SOL] 0.010")
        print("[ORIGINAL_SCANNER] FROZEN")
        print("[SIGNING] FALSE [BROADCAST] FALSE")
        return 0 if target.is_file() else 2
    if args.child:
        sys.path.insert(0, str(root.resolve()))
        return run_once(root, args.seconds)
    if args.run or args.service:
        if args.seconds < 60 or args.seconds > 3600:
            print("[HOLD] DURATION_60_TO_3600")
            return 2
        return service(root, args.seconds) if args.service else parent(root, args.seconds)
    target = root / MODULE
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if target.resolve() != Path(__file__).resolve():
        shutil.copyfile(Path(__file__), target)
    print("[PASS]", VERSION)
    print("[ORIGINAL_SCANNER] PRESERVED")
    print("[MIN_EXECUTION_SIZE] 0.010_SOL")
    print("[FIRST_CANARY] 0.010_SOL")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
