from pathlib import Path
from hashlib import sha256
from textwrap import dedent

ROOT = Path.cwd()
PKG = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor'
PREV = PKG / 'oracle_054_reverse_native_handoff.py'
DEST = PKG / 'oracle_055_parity_simulation_guard.py'
TEST = ROOT / 'test_oracle_055_parity_simulation_guard.py'
if not PREV.is_file():
    raise SystemExit('[HOLD] Missing certified ORACLE-054 source: ' + str(PREV))
if not (ROOT/'qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py').is_file():
    raise SystemExit('[HOLD] Original Q18 pricing module missing; no modifications made')
if DEST.exists() and 'ORACLE054_SHA256' not in DEST.read_text(encoding='utf-8',errors='replace'):
    raise SystemExit('[HOLD] Refusing to replace an unknown existing module')
if TEST.exists() and 'test_01_source_lock' not in TEST.read_text(encoding='utf-8',errors='replace'):
    raise SystemExit('[HOLD] Refusing to replace an unknown existing test file')
digest = sha256(PREV.read_bytes()).hexdigest()
code = r'''from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import sys
import time

ORACLE054_SHA256 = "__DIGEST__"
PREV = Path(__file__).with_name("oracle_054_reverse_native_handoff.py")
REPORT = Path("runtime_state/oracle/oracle_live_execution/oracle_055_parity_simulation_guard.json")
MIN_SIZE_SOL = 0.010
EXECUTION_AUTHORITY = False
BROADCAST = False
SIGNING = False
DIRECTIONS = ("METEORA_TO_PUMP", "PUMP_TO_METEORA")


def unchanged_source(path=PREV, expected=ORACLE054_SHA256):
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected


def public_field(value):
    # Secrets are never copied to the report. No raw RPC URLs or transaction bytes.
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, str):
            value = re.sub(r"(?i)(api-key|token|authorization|secret|private_key)=([^\s&]+)", r"\1=[REDACTED]", value)
            value = re.sub(r"https?://[^\s]+", "[URL_REDACTED]", value)
            return value[:220]
        return value
    return str(type(value).__name__)


def state_digest(snapshot):
    """Immutable, venue-relevant input fingerprint. Unknowns stay unknown."""
    fields = ("token", "pump_pool", "pump_base_reserve", "pump_quote_reserve",
              "meteora", "lb_bytes", "arrays_raw")
    if not isinstance(snapshot, dict) or not all(k in snapshot for k in fields):
        return None
    def clean(v):
        if isinstance(v, bytes):
            return {"raw_sha256": hashlib.sha256(v).hexdigest(), "len": len(v)}
        if isinstance(v, (tuple, list)):
            return [clean(x) for x in v]
        if isinstance(v, dict):
            return {str(k): clean(x) for k, x in sorted(v.items())}
        if isinstance(v, (str, int, float, bool)) or v is None:
            return v
        return {"type": type(v).__name__}  # Never serialize live SDK objects.
    raw = json.dumps({k: clean(snapshot[k]) for k in fields}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def compare_quote(a, b, epsilon_bps=0.05):
    for key in ("token", "direction", "size_sol", "pump_pool", "meteora_pool"):
        if a.get(key) != b.get(key):
            return "NOT_COMPARABLE_ROUTE"
    if not a.get("state_sha256") or not b.get("state_sha256"):
        return "HOLD_NO_IMMUTABLE_STATE_PROOF"
    if a["state_sha256"] != b["state_sha256"]:
        return "STATE_CHANGED_NOT_PRICE_PARITY_PROOF"
    try:
        return ("SAME_STATE_PRICER_PARITY" if abs(float(a["bps"])-float(b["bps"])) <= epsilon_bps
                else "SAME_STATE_PRICE_DIVERGENCE")
    except (KeyError, ValueError, TypeError):
        return "HOLD_MISSING_PRICE_EVIDENCE"


def simulation_diagnostic(response):
    value = response.get("value", response) if isinstance(response, dict) else {}
    if not isinstance(value, dict):
        return {"category": "INVALID_SIMULATION_ENVELOPE", "verified": False}
    err = value.get("err", "MISSING_ERR_FIELD")
    units = value.get("unitsConsumed")
    logs = value.get("logs") or []
    last = [public_field(line) for line in logs[-4:] if isinstance(line, str)]
    joined = " ".join(str(x) for x in logs[-10:]).lower()
    error_text = str(err).lower()
    if err is None and isinstance(units, int) and units > 0:
        category = "SIM_EXECUTED_NO_PROFIT_CERTIFICATION"
    elif "blockhash" in error_text:
        category = "BLOCKHASH_OR_FRESHNESS_REJECT"
    elif "account" in error_text or "account" in joined:
        category = "ACCOUNT_OR_PROGRAM_REJECT"
    elif "custom program error" in joined or "instructionerror" in error_text:
        category = "PROGRAM_INSTRUCTION_REJECT"
    elif not units:
        category = "REJECTED_WITHOUT_REPORTED_COMPUTE"
    else:
        category = "SIMULATION_REJECTED"
    return {"category": category, "verified": False,
            "err_type": public_field(type(err).__name__),
            "err_summary": public_field(str(err)),
            "units_consumed": units if isinstance(units, int) else None,
            "log_tail": last}


def atomic_gate(row):
    """No claim of executable profit without explicit independent evidence."""
    required = ("size_sol", "direction", "venue_order", "source_fresh", "accounts_reconciled",
                "sim_err", "sim_units", "fees_complete", "residue_raw", "net_lamports",
                "atomic_two_legs", "state_parity_verified")
    missing = [k for k in required if k not in row]
    if missing:
        return "HOLD_MISSING_" + ",".join(missing)
    try:
        if float(row["size_sol"]) < MIN_SIZE_SOL:
            return "HOLD_BELOW_010_CANARY_MINIMUM"
    except (ValueError, TypeError):
        return "HOLD_INVALID_SIZE"
    direction = row["direction"]
    if direction not in DIRECTIONS:
        return "HOLD_UNKNOWN_DIRECTION"
    expected = ("METEORA", "PUMPSWAP") if direction == "METEORA_TO_PUMP" else ("PUMPSWAP", "METEORA")
    if tuple(row["venue_order"]) != expected:
        return "HOLD_REVERSED_NATIVE_LEG_ORDER"
    if row["sim_err"] is not None or not isinstance(row["sim_units"], int) or row["sim_units"] <= 0:
        return "HOLD_FAILED_ATOMIC_SIMULATION"
    if not all(row[x] is True for x in ("source_fresh", "accounts_reconciled", "fees_complete",
                                           "atomic_two_legs", "state_parity_verified")):
        return "HOLD_INCOMPLETE_ATOMIC_PROOF"
    if row["residue_raw"] != 0:
        return "HOLD_INTERMEDIATE_TOKEN_RESIDUE"
    if not isinstance(row["net_lamports"], int) or row["net_lamports"] <= 0:
        return "HOLD_NONPOSITIVE_NET_AFTER_ALL_FEES"
    return "UNSIGNED_SIMULATION_EVIDENCE_ONLY_NO_BROADCAST"


class QuoteProbe:
    def __init__(self):
        self.rows = 0
        self.by_key = {}
        self.transitions = {}
        self.samples = []
        self.errors = []

    def observe(self, snap, size, rows):
        # Call-through observation only: never change the SDK pricing return values.
        fingerprint = state_digest(snap)
        if not isinstance(snap, dict):
            return
        slot = int(snap.get("source_slot") or 0)
        event = int(snap.get("source_event_ns") or 0)
        phase = "EVENT_TAGGED" if slot > 0 and event > 0 else "UNKNOWN_NOT_TRUSTED_AS_LIVE"
        for r in rows if isinstance(rows, (list, tuple)) else ():
            if not isinstance(r, dict):
                continue
            key = (str(r.get("token")), str(r.get("direction")), str(r.get("size_sol")))
            pool = (r.get("meteora") or {}).get("address") if isinstance(r.get("meteora"), dict) else None
            o = {"token": key[0][:12], "direction": key[1], "size_sol": r.get("size_sol"),
                 "pump_pool": r.get("pump_pool"), "meteora_pool": pool,
                 "slot": slot, "phase": phase, "state_sha256": fingerprint,
                 "bps": r.get("local_bps")}
            self.rows += 1
            if key in self.by_key:
                result = compare_quote(self.by_key[key], o)
                self.transitions[result] = self.transitions.get(result, 0) + 1
                if len(self.samples) < 16 and result != "SAME_STATE_PRICER_PARITY":
                    self.samples.append({"token": key[0][:12], "direction": key[1],
                                         "prev_slot": self.by_key[key]["slot"], "slot": slot,
                                         "result": result,
                                         "prev_bps": self.by_key[key]["bps"], "bps": o["bps"]})
            self.by_key[key] = o


class Monitor:
    def __init__(self, downstream):
        self.out = downstream
        self.partial = ""
        self.lines = 0
        self.price_lines = 0
        self.sim_rejections = 0
        self.zero_unit_rejections = 0
        self.mriya_lines = 0
        self.account_shards = set()
        self.rejections = []
        self.startup_spreads = []
        self.live_spreads = []

    def write(self, text):
        self.out.write(text)
        self.partial += text
        while "\n" in self.partial:
            line, self.partial = self.partial.split("\n", 1)
            self.consume(line[:4000])
        if len(self.partial) > 8192:
            self.partial = ""
        return len(text)

    def flush(self):
        self.out.flush()

    def isatty(self):
        return False

    @property
    def encoding(self):
        return getattr(self.out, "encoding", "utf-8")

    def consume(self, line):
        self.lines += 1
        low = line.lower()
        if "mriya" in low:
            self.mriya_lines += 1
        if "websocket" in low or "ws_shard" in low:
            m = re.search(r"(?:shards|ws_shards)=([0-9]+)", low)
            if m:
                self.account_shards.add(int(m.group(1)))
        if "bps=" in low and ("exact" in low or "startup" in low or "hydrated" in low):
            self.price_lines += 1
            m = re.search(r"bps=([+-]?[0-9.]+)", line)
            if m:
                val = float(m.group(1))
                dest = self.live_spreads if ("EXACT_LATEST" in line or "EXACT_IMMUTABLE" in line) else self.startup_spreads
                if len(dest) < 3000:
                    dest.append(val)
        if "rejected" in low or "sim_err" in low or "simulation error" in low:
            self.sim_rejections += 1
            if re.search(r"(?:units|units_consumed|unitsconsumed)[=: ]+0\b", low):
                self.zero_unit_rejections += 1
            if len(self.rejections) < 12:
                self.rejections.append(public_field(line))


def save_report(probe, monitor, exit_code, failure=None):
    result = {"build": "ORACLE-055", "status": "HOLD_NO_EXECUTABLE_PROFIT_CERTIFICATION",
              "oracle_054_source_unchanged": unchanged_source(),
              "oracle_054_sha256": ORACLE054_SHA256,
              "single_original_054_launcher": True,
              "standalone_scanner_created": False,
              "signing_added": False, "broadcast_added": False,
              "min_trade_sol": MIN_SIZE_SOL, "first_live_canary_sol": 0.010,
              "quote_probe_rows": probe.rows,
              "quote_state_transition_counts": probe.transitions,
              "quote_transition_samples": probe.samples,
              "log_lines": monitor.lines, "live_exact_log_rows": len(monitor.live_spreads),
              "startup_or_unknown_price_rows": len(monitor.startup_spreads),
              "startup_max_bps": max(monitor.startup_spreads, default=None),
              "live_max_bps": max(monitor.live_spreads, default=None),
              "simulation_rejection_lines": monitor.sim_rejections,
              "rejected_zero_unit_lines": monitor.zero_unit_rejections,
              "simulation_rejection_samples": monitor.rejections,
              "mriya_log_lines": monitor.mriya_lines,
              "seen_websocket_shard_counts": sorted(monitor.account_shards),
              "mriya_replenishment_certified": False,
              "native_correction_certified": False,
              "executable_profit_certified": False,
              "exit_code": exit_code,
              "failure": public_field(failure)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("[ORACLE055_REPORT]", REPORT)
    print("[ORACLE055_HOLD] Startup prices are not executable profit; failed sims never advance")
    return result


def run(seconds):
    if not unchanged_source():
        raise RuntimeError("ORACLE054_SOURCE_CHANGED_SINCE_055_INSTALL:REINSTALL_AFTER_INSPECTION")
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    import importlib
    import contextlib
    q18 = importlib.import_module("qseries_v2.oracle_execution.oracle_018_exact_sdk_hot_lane_cutover")
    original = q18.exact_snapshot_opportunities
    probe = QuoteProbe()
    def measured(snap, size):
        rows = original(snap, size)
        try:
            probe.observe(snap, size, rows)
        except Exception as exc:
            if len(probe.errors) < 5:
                probe.errors.append(type(exc).__name__)
        return rows
    q18.exact_snapshot_opportunities = measured
    monitor = Monitor(sys.stdout)
    rc = 0
    failure = None
    prior = sys.argv[:]
    sys.argv = [str(PREV), "--run", "--seconds", str(seconds), "--cycles", "1"]
    try:
        with contextlib.redirect_stdout(monitor):
            try:
                runpy.run_module("qseries_v2.oracle_execution.solana_atomic_executor.oracle_054_reverse_native_handoff", run_name="__main__")
            except SystemExit as x:
                rc = x.code if isinstance(x.code, int) else int(bool(x.code))
    except Exception as exc:
        rc = 1
        failure = type(exc).__name__ + ":" + str(exc)[:160]
        print("[ORACLE055_NATIVE_RUNTIME_EXCEPTION]", type(exc).__name__)
    finally:
        sys.argv = prior
        q18.exact_snapshot_opportunities = original
        save_report(probe, monitor, rc, failure)
    return rc


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--seconds", type=float, default=900.0)
    args = parser.parse_args(argv)
    if args.test:
        import unittest
        from test_oracle_055_parity_simulation_guard import Tests
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    if args.audit:
        print("[ORACLE055_SOURCE]", "PASS" if unchanged_source() else "HOLD_SOURCE_DRIFT")
        print("[Q18]", "ORIGINAL_PRESERVED")
        print("[MONEY]", "SIGNING_FALSE BROADCAST_FALSE PROFIT_NOT_CERTIFIED")
        return 0 if unchanged_source() else 1
    if args.run:
        return run(args.seconds)
    parser.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''.replace('__DIGEST__',digest)
tests = r'''import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_055_parity_simulation_guard as m

class Tests(unittest.TestCase):
    def test_01_source_lock(self):
        self.assertTrue(m.unchanged_source())
    def test_02_state_hash_reproducible(self):
        s=dict(token="t",pump_pool="p",pump_base_reserve=3,pump_quote_reserve=4,
               meteora={"address":"m"},lb_bytes=b"a",arrays_raw=((1,2,b"b"),))
        self.assertEqual(m.state_digest(s),m.state_digest(dict(reversed(list(s.items())))))
    def test_03_missing_state_not_parity(self):
        self.assertIsNone(m.state_digest({"token":"t"}))
    def test_04_state_difference(self):
        x=dict(token="t",direction="METEORA_TO_PUMP",size_sol=.010,pump_pool="p",meteora_pool="m",bps=3,state_sha256="a")
        self.assertEqual(m.compare_quote(x,dict(x,state_sha256="b")),"STATE_CHANGED_NOT_PRICE_PARITY_PROOF")
    def test_05_same_state_mismatch(self):
        x=dict(token="t",direction="METEORA_TO_PUMP",size_sol=.010,pump_pool="p",meteora_pool="m",bps=99,state_sha256="a")
        self.assertEqual(m.compare_quote(x,dict(x,bps=-10)),"SAME_STATE_PRICE_DIVERGENCE")
    def test_06_same_state_parity(self):
        x=dict(token="t",direction="METEORA_TO_PUMP",size_sol=.010,pump_pool="p",meteora_pool="m",bps=99,state_sha256="a")
        self.assertEqual(m.compare_quote(x,dict(x,bps=99.01)),"SAME_STATE_PRICER_PARITY")
    def test_07_size_floor(self):
        r=self.good();r["size_sol"] = .005
        self.assertEqual(m.atomic_gate(r),"HOLD_BELOW_010_CANARY_MINIMUM")
    def test_08_reverse_order(self):
        r=self.good();r["venue_order"]=["PUMPSWAP","METEORA"]
        self.assertEqual(m.atomic_gate(r),"HOLD_REVERSED_NATIVE_LEG_ORDER")
    def test_09_simulation_rejection(self):
        self.assertEqual(m.simulation_diagnostic({"value":{"err":{"InstructionError":[0,1]},"unitsConsumed":0}})["verified"],False)
        r=self.good();r["sim_err"]={"InstructionError":[0,1]};r["sim_units"]=0
        self.assertEqual(m.atomic_gate(r),"HOLD_FAILED_ATOMIC_SIMULATION")
    def test_10_fee_residue(self):
        r=self.good();r["residue_raw"]=1
        self.assertEqual(m.atomic_gate(r),"HOLD_INTERMEDIATE_TOKEN_RESIDUE")
        r=self.good();r["fees_complete"]=False
        self.assertEqual(m.atomic_gate(r),"HOLD_INCOMPLETE_ATOMIC_PROOF")
    def test_11_positive_unsigned_not_live(self):
        self.assertEqual(m.atomic_gate(self.good()),"UNSIGNED_SIMULATION_EVIDENCE_ONLY_NO_BROADCAST")
        self.assertFalse(m.SIGNING or m.BROADCAST or m.EXECUTION_AUTHORITY)
    def test_12_safe_redaction(self):
        self.assertNotIn("SECRET123",m.public_field("https://example.com/?api-key=SECRET123"))
    def test_13_drift_guard(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"file.py";p.write_text("changed")
            self.assertFalse(m.unchanged_source(p,"deadbeef"))
    def test_14_no_evidence_no_profit(self):
        self.assertTrue(m.atomic_gate({}).startswith("HOLD_MISSING_"))
    @staticmethod
    def good():
        return {"size_sol":.010,"direction":"METEORA_TO_PUMP", "venue_order":["METEORA","PUMPSWAP"],
                "source_fresh":True,"accounts_reconciled":True,"sim_err":None,"sim_units":1000,
                "fees_complete":True,"residue_raw":0,"net_lamports":100,"atomic_two_legs":True,
                "state_parity_verified":True}

if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
PKG.mkdir(parents=True,exist_ok=True)
dtmp=DEST.with_suffix('.py.tmp')
ttmp=TEST.with_suffix('.py.tmp')
dtmp.write_text(code,encoding='utf-8')
ttmp.write_text(tests,encoding='utf-8')
dtmp.replace(DEST)
ttmp.replace(TEST)
print('[PASS] ORACLE-055 installed',DEST)
print('[PASS] ORACLE-055 deterministic tests installed',TEST)
print('[PRESERVED] ORACLE-054 sha256='+digest[:16])
print('[PRESERVED] Original Q25/Q20/Q18 live WebSocket scanner, Mriya, learning, recovery, native executor unchanged')
print('[BOUNDARY] Observation + unsigned simulation evidence only; no signing or broadcasting added')
