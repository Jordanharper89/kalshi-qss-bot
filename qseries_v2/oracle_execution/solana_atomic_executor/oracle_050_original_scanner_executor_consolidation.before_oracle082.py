"""ORACLE-050: one-source scanner/executor integration installer.

Installs a new, isolated wrapper around the existing Oracle-025/020/018
scanner. Does not replace scanner files, spawn a new scanner, or sign orders.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import unittest
from collections import Counter, deque
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


VERSION = "ORACLE_050_ORIGINAL_SCANNER_EXECUTOR_CONSOLIDATION"
ROOT_PACKAGE = Path("qseries_v2/oracle_execution/solana_atomic_executor")
TARGET = ROOT_PACKAGE / "oracle_050_original_scanner_executor_consolidation.py"
REPORT = Path("runtime_state/oracle/oracle_live_execution/ORACLE_050_CONSOLIDATION.json")
JOURNAL = Path("runtime_state/oracle/oracle_live_execution/ORACLE_050_EXECUTOR_HANDOFF.jsonl")
SCANNER_FILES = (
    Path("qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py"),
    Path("qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py"),
    Path("qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py"),
    Path("qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/persistent_profit_runtime.py"),
    Path("qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/merged_live_runtime.py"),
    Path("qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/live_account_stream.py"),
    Path("qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/qarb_060b_existing_runtime_multidex_cutover.py"),
    Path("qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/qarb_060b2_single_hydration_cached_runner_cutover.py"),
)
EXECUTOR_FILES = (
    ROOT_PACKAGE / "runtime.py",
    ROOT_PACKAGE / "oracle_atomic_closeout.py",
    ROOT_PACKAGE / "oracle_024_fresh_candidate_revalidation.py",
)
CANARY_LAMPORTS = 10_000_000
MAX_AGE_NS = 750_000_000
# Always demand a positive margin after a conservative fixed fee reserve.
# This is a screening buffer, NOT a claim of exact network costs.
SCREENING_FEE_RESERVE = 100_000
SAFE_ENV = {
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "TEMP", "TMP",
    "COMSPEC", "APPDATA", "LOCALAPPDATA", "USERPROFILE", "HOMEDRIVE",
    "HOMEPATH", "SOLANA_RPC_URL", "SOLANA_WS_URL", "QSB_SOLANA_RPC_URL",
    "QSB_SOLANA_WALLET", "QARB_WS_SHARD_SIZE", "QARB_WS_SUBSCRIBE_DELAY_MS",
    "QARB_WS_SHARD_STAGGER_SECONDS", "QARB_PERSISTENT_MAX_PAIRS",
    "QARB_HOT_PAIRS", "QARB_MAX_ACCOUNTS", "QARB_MAX_TOKENS",
    "QARB_DISCOVERY_BUDGET", "NODE_OPTIONS", "PYTHONIOENCODING",
}


def scrub(env):
    clean = {k: v for k, v in env.items() if k.upper() in SAFE_ENV}
    clean["PYTHONIOENCODING"] = "utf-8"
    # Restore the user's prior wide warm-inventory configuration without
    # capping the ORIGINAL scanner at an accidental 4/12-pair default.
    clean.setdefault("QARB_HOT_PAIRS", "28")
    clean.setdefault("QARB_PERSISTENT_MAX_PAIRS", "28")
    clean.setdefault("QARB_MAX_ACCOUNTS", "384")
    clean.setdefault("QARB_MAX_TOKENS", "40")
    clean.setdefault("QARB_DISCOVERY_BUDGET", "120")
    return clean


def hash_sources(root):
    return {str(p): hashlib.sha256((root / p).read_bytes()).hexdigest()
            for p in SCANNER_FILES if (root / p).is_file()}


def original_contract(root):
    checks = {str(p): (root / p).is_file() for p in SCANNER_FILES + EXECUTOR_FILES}
    missing = [p for p, exists in checks.items() if not exists]
    return {"source_files": checks, "missing": missing, "ready": not missing}


def tier_for(token, registry, now=None):
    # Never invent eligibility from a token's appearance in Mriya.
    now = time.time() if now is None else now
    if not isinstance(registry, dict):
        return "UNVERIFIED"
    created = registry.get("created_epoch")
    if not isinstance(created, (int, float)) or now - created > 600 or created > now + 30:
        return "UNVERIFIED"
    for row in registry.get("rows", []):
        if isinstance(row, dict) and row.get("token") == token:
            life = row.get("lifecycle") or {}
            stage = str(life.get("stage") or row.get("tier") or "").upper().replace("_", "-").replace(" ", "-")
            return stage if stage in ("ULTRA-HOT", "HOT", "ACTIVE") else "INELIGIBLE"
    return "UNVERIFIED"


def latest_tiers(root):
    path = root / "runtime_state/qseries/qarb_clean_bot/mriya_dynamic_active_bindings.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def eligible_quote(row, ready, stamp_ns, now_ns, tier):
    if not isinstance(row, dict):
        return "HOLD_BAD_QUOTE"
    if tier not in ("ULTRA-HOT", "HOT", "ACTIVE"):
        return "HOLD_NO_FRESH_TIER_ADMISSION"
    if row.get("direction") not in ("PUMP_TO_METEORA", "METEORA_TO_PUMP"):
        return "HOLD_UNSUPPORTED_DIRECTION"
    token = row.get("token")
    if not isinstance(token, str) or not token or token not in ready:
        return "HOLD_NATIVE_TEMPLATE_NOT_READY"
    if type(stamp_ns) is not int or stamp_ns > now_ns or now_ns - stamp_ns > MAX_AGE_NS:
        return "HOLD_STALE_SNAPSHOT"
    net = row.get("local_net")
    size = row.get("start")
    if type(net) is not int or type(size) is not int or size <= 0:
        return "HOLD_NONEXACT_ECONOMICS"
    if net <= SCREENING_FEE_RESERVE:
        return "HOLD_NO_POSITIVE_POST_RESERVE"
    return "PRE_SIMULATION_CANDIDATE_ONLY"


class ScannerExecutorBridge:
    """Passive quote tap on the original q18 function; never a second scanner."""
    def __init__(self, root, clock=time.perf_counter_ns):
        self.root = Path(root)
        self.clock = clock
        self.ready = set()
        self.tiers = latest_tiers(self.root)
        self.quote_events = 0
        self.scanner_positives = 0
        self.handoff_count = 0
        self.holds = Counter()
        self.native_status = "NOT_PREPARED"
        self.native_error = None
        self.verified_pairs = 0
        self.lock = threading.Lock()
        self.pending = deque(maxlen=128)
        self.native_pending = deque(maxlen=8)
        self._runtime = None
        self._public_wallet = None
        self.native_compiles = 0
        self.unsigned_simulations = 0
        self.unsigned_sim_passes = 0
        self._q18 = None
        self._q25 = None
        self._q20 = None
        self._original_price = None
        self._thread_context = threading.local()
        self._original_quote = None
        self._original_warm = None
        self._original_run = None
        self.ingress_written = 0
        self.ingress_stop = threading.Event()
        self.ingress_thread = None

    def on_quote(self, snap, rows, observed_ns):
        # Runs on the EXISTING scanner's pricing thread: no RPC, no WS,
        # no SDK quoting, no blocking filesystem I/O, and no signing.
        self.quote_events += 1
        for row in rows:
            if not isinstance(row, dict):
                continue
            if isinstance(row.get("local_net"), int) and row["local_net"] > 0:
                self.scanner_positives += 1
            stage = tier_for(row.get("token"), self.tiers)
            verdict = eligible_quote(row, self.ready, observed_ns, self.clock(), stage)
            if verdict != "PRE_SIMULATION_CANDIDATE_ONLY":
                self.holds[verdict] += 1
                continue
            # Single-writer, in-memory handoff of existing exact scanner result.
            compact = {
                "token": row["token"], "direction": row["direction"],
                "start_lamports": row["start"],
                "quoted_net_lamports": row["local_net"],
                "pump_pool": str(row.get("pump_pool", "")),
                "meteora_pool": str((row.get("meteora") or {}).get("address", "")),
                "tier": stage, "observed_ns": observed_ns,
                "native_templates_ready": True, "simulation_pass": False,
                "fee_residue_verified": False, "execution_authority": False,
            }
            if len(self.pending) == self.pending.maxlen:
                self.holds["HANDOFF_QUEUE_CAP_REACHED"] += 1
                continue
            self.pending.append(compact)
            self.handoff_count += 1
            if row["direction"] == "PUMP_TO_METEORA":
                # Only the existing canonical executor supports this native
                # direction in its same-snapshot builder. Never fake reverse.
                if len(self.native_pending) < self.native_pending.maxlen:
                    import copy
                    self.native_pending.append((copy.deepcopy(snap), dict(row), observed_ns))
                else:
                    self.holds["NATIVE_PRECHECK_QUEUE_FULL"] += 1
            else:
                self.holds["REVERSE_NATIVE_BOUND_NOT_CERTIFIED"] += 1

    # ORACLE060_BACKGROUND_TIER_REFRESH: filesystem reads stay off pricing thread.
    def _oracle060_tier_refresh_loop(self):
        while not self.ingress_stop.wait(2.0):
            try:
                fresh = latest_tiers(self.root)
                if not isinstance(fresh, dict):
                    continue
                created = fresh.get("created_epoch")
                if not isinstance(created, (int, float)):
                    continue
                now = time.time()
                if created > now + 30 or now - created > 600:
                    continue
                old = self.tiers if isinstance(self.tiers, dict) else {}
                if created >= old.get("created_epoch", -1):
                    self.tiers = fresh
            except (OSError, ValueError, TypeError):
                continue

    def start_ingress(self):
        if self.ingress_thread is not None:
            raise RuntimeError("INGRESS_ALREADY_RUNNING")
        self._oracle060_tier_thread = threading.Thread(
            target=self._oracle060_tier_refresh_loop,
            name="oracle060-tier-refresh", daemon=True)
        self._oracle060_tier_thread.start()
        self.ingress_thread = threading.Thread(
            target=self._consume, name="oracle050-native-handoff", daemon=True)
        self.ingress_thread.start()

    def _consume(self):
        # ORACLE078_FRESH_NATIVE_FIRST_JOURNAL_CERTIFIED
        from collections import deque
        output = self.root / JOURNAL
        output.parent.mkdir(parents=True, exist_ok=True)
        journaled = set()
        history = deque(maxlen=1024)

        def key(row, stamp):
            return (row.get("token"), row.get("direction"),
                    row.get("start_lamports", row.get("start")), stamp)

        def persist(row):
            born = row.get("observed_ns")
            if type(born) is not int or born > self.clock() or self.clock() - born > MAX_AGE_NS:
                self.holds["HANDOFF_EXPIRED_BEFORE_CONSUMPTION"] += 1
                return False
            row["gate"] = "AWAITING_ATOMIC_SIMULATION_AND_ACTUAL_NET_PROFIT"
            try:
                with output.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, sort_keys=True) + "\n")
                self.ingress_written += 1
                k = key(row, born)
                if k not in journaled:
                    if len(history) == history.maxlen:
                        journaled.discard(history.popleft())
                    history.append(k)
                    journaled.add(k)
                return True
            except OSError:
                self.holds["HANDOFF_PERSISTENCE_FAILED"] += 1
                return False

        while not self.ingress_stop.is_set() or self.pending or self.native_pending:
            # A live WS feed can keep pending nonempty indefinitely.
            # Prioritize the freshest native entry, but persist its matching
            # inert handoff BEFORE attempting an unsigned simulation.
            if self.native_pending:
                item = self.native_pending.pop()
                snap, opportunity, born_ns = item
                if (type(born_ns) is not int or born_ns > self.clock()
                        or self.clock() - born_ns > MAX_AGE_NS):
                    self.holds["NATIVE_SNAPSHOT_STALE_BEFORE_BUILD"] += 1
                    continue
                k = key(opportunity, born_ns)
                if k not in journaled:
                    match = next((r for r in tuple(self.pending)
                                  if key(r, r.get("observed_ns")) == k), None)
                    if match is None:
                        self.holds["NATIVE_JOURNAL_MATCH_MISSING"] += 1
                        continue
                    try:
                        self.pending.remove(match)
                    except ValueError:
                        self.holds["NATIVE_JOURNAL_MATCH_LOST"] += 1
                        continue
                    if not persist(match):
                        self.holds["NATIVE_JOURNAL_WRITE_HOLD"] += 1
                        continue
                if self.clock() - born_ns > MAX_AGE_NS:
                    self.holds["NATIVE_SNAPSHOT_STALE_BEFORE_BUILD"] += 1
                    continue
                self._simulate_p2m_once(item)
                continue
            if self.pending:
                persist(self.pending.popleft())
                continue
            time.sleep(.02)

    def _simulate_p2m_once(self, item):
        if self.unsigned_simulations or self.native_compiles:
            self.holds["BOUNDED_ONE_SIMULATION_PER_WINDOW"] += 1
            return
        snap, opportunity, born_ns = item
        if self._runtime is None or not self._public_wallet:
            self.holds["NATIVE_RUNTIME_UNAVAILABLE"] += 1
            return
        if self.clock() - born_ns > MAX_AGE_NS:
            self.holds["NATIVE_SNAPSHOT_STALE_BEFORE_BUILD"] += 1
            return
        self.native_compiles += 1
        try:
            route = self._runtime.same_snapshot_route(self._public_wallet, snap, opportunity)
            built = self._runtime.compile_current(self._public_wallet, route)
            if not isinstance(built, dict) or built.get("ok") is not True:
                self.holds["NATIVE_ATOMIC_COMPILE_REJECTED"] += 1
                return
            if self.clock() - born_ns > MAX_AGE_NS:
                self.holds["NATIVE_SNAPSHOT_STALE_BEFORE_SIM"] += 1
                return
            # unsigned simulateTransaction only; no signature, no send.
            sim = self._runtime.simulate_current(built, self._public_wallet)
            self.unsigned_simulations += 1
            if isinstance(sim, dict) and sim.get("err") is None:
                self.unsigned_sim_passes += 1
                self.holds["SIM_PASS_NET_PROFIT_AND_RESIDUE_UNCERTIFIED"] += 1
            else:
                self.holds["SIGNED_OR_UNSIGNED_SIM_REJECTED"] += 1
                print("[ATOMIC_SIM] REJECTED", _oracle067_sim_truth(sim), flush=True)
        except Exception as exc:
            self.holds["ATOMIC_SIM_" + type(exc).__name__] += 1

    def close_ingress(self):
        self.ingress_stop.set()
        if self.ingress_thread is not None:
            self.ingress_thread.join(timeout=5)
            if self.ingress_thread.is_alive():
                self.holds["INGRESS_SHUTDOWN_INCOMPLETE"] += 1

    def install(self, q18, q25, q20):
        if self._q18 is not None:
            raise RuntimeError("BRIDGE_ALREADY_INSTALLED")
        self._q18, self._q25, self._q20 = q18, q25, q20
        self._original_price = q20.LatestStateLane._price
        original_price = self._original_price

        def stamped_price(lane, token, row):
            # q20's row owns the canonical received_ns from the ORIGINAL WS.
            prior = getattr(self._thread_context, "received_ns", None)
            self._thread_context.received_ns = row[2]
            try:
                return original_price(lane, token, row)
            finally:
                self._thread_context.received_ns = prior

        q20.LatestStateLane._price = stamped_price
        self._original_quote = q18.exact_snapshot_opportunities
        self._original_warm = q25.install_hot_math_and_prewarm
        original_quote = self._original_quote
        original_warm = self._original_warm

        def quote_tap(snap, size):
            stamp = getattr(self._thread_context, "received_ns", None)
            if type(stamp) is not int:
                self.holds["NO_ORIGINAL_SCANNER_EVENT_TIMESTAMP"] += 1
                stamp = 0  # fail closed for executor eligibility
            try:
                rows = original_quote(snap, size)
            except Exception as exc:
                self.holds["ORIGINAL_EXACT_QUOTE_" + type(exc).__name__] += 1
                raise  # never hide original scanner failure or substitute prices
            self.on_quote(snap, rows, stamp)
            return rows  # original scanner sees the exact original result

        def warm_and_prepare(state):
            warmed = original_warm(state)
            self.verified_pairs = len(state.get("pairs") or [])
            self.prepare_native(state, warmed)
            return warmed  # original scanner's hydration remains authoritative

        q18.exact_snapshot_opportunities = quote_tap
        q25.install_hot_math_and_prewarm = warm_and_prepare

    def prepare_native(self, state, warmed):
        wallet = os.environ.get("QSB_SOLANA_WALLET", "").strip()
        if not wallet:
            self.native_status = "HOLD_PUBLIC_WALLET_MISSING"
            return
        try:
            from solders.pubkey import Pubkey
            from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
            Pubkey.from_string(wallet)
            # Production executor's native template preparation, without orders.
            # q25's original warm() has ALREADY installed native token
            # semantics. Calling rt.install_proven_hot_math here would
            # reenter the patched q25 warm hook recursively.
            rt.USER = wallet
            rt.prebuild_templates(state, wallet)
            rt.prebuild_meteora_templates(state, wallet, warmed)
            self.ready = set(rt.READY_TOKENS)
            self._runtime = rt
            self._public_wallet = wallet
            self.native_status = "NATIVE_TEMPLATES_READY" if self.ready else "HOLD_NO_NATIVE_TEMPLATES"
        except Exception as exc:
            self.native_status = "HOLD_NATIVE_" + type(exc).__name__
            self.native_error = type(exc).__name__
            self.ready.clear()
            self._runtime = None

    def restore(self):
        if self._q18 is not None:
            self._q18.exact_snapshot_opportunities = self._original_quote
        if self._q25 is not None:
            self._q25.install_hot_math_and_prewarm = self._original_warm
        if self._q20 is not None:
            self._q20.LatestStateLane._price = self._original_price
        self._q18 = self._q25 = self._q20 = None

    def drain(self):
        out = []
        while self.pending:
            row = self.pending.popleft()
            if self.clock() - row["observed_ns"] > MAX_AGE_NS:
                self.holds["HANDOFF_EXPIRED_BEFORE_CONSUMPTION"] += 1
            else:
                out.append(row)
        return out

    def report(self):
        return {
            "revision": VERSION, "source": "ORIGINAL_Q25_Q20_Q18_SCANNER",
            "scanner_transport_replaced": False,
            "standalone_oracle047_used": False,
            "standalone_oracle049_used": False,
            "tier_registry_fresh": (isinstance(self.tiers, dict) and
                isinstance(self.tiers.get("created_epoch"), (int, float)) and
                0 <= time.time() - self.tiers["created_epoch"] <= 600),
            "native_status": self.native_status,
            "native_ready_tokens": len(self.ready),
            "original_scanner_hydrated_pairs": self.verified_pairs,
            "configured_warm_target": os.environ.get("QARB_HOT_PAIRS", "UNKNOWN"),
            "configured_watched_account_capacity": os.environ.get("QARB_MAX_ACCOUNTS", "UNKNOWN"),
            "original_exact_quote_rows": self.quote_events,
            "positive_scanner_quotes": self.scanner_positives,
            "pre_simulation_handoffs": self.handoff_count,
            "handoffs_persisted": self.ingress_written,
            "native_compile_attempts": self.native_compiles,
            "unsigned_atomic_simulations": self.unsigned_simulations,
            "unsigned_atomic_simulation_passes": self.unsigned_sim_passes,
            "holds": dict(self.holds),
            "simulation_certified": False,
            "net_profit_certified": False,
            "signing": False, "broadcast": False,
            "first_canary_lamports": CANARY_LAMPORTS,
            "tier_authority": "EXISTING_RUNTIME_NOT_REPLACED",
            "mriya_rotation_inside_original_socket_certified": False,
        }


def atomic_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def run_original(root, seconds):
    contract = original_contract(root)
    if not contract["ready"]:
        print("[HOLD] ORIGINAL_SOURCE_MISSING", json.dumps(contract["missing"]))
        return 2
    # No secret may enter the scanner child; parent environment stays unchanged.
    if any("PRIVATE_KEY" in k.upper() or "SECRET_KEY" in k.upper() for k in os.environ):
        print("[HOLD] CHILD_SECRET_ENVIRONMENT")
        return 2
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core

    original_signing = {name: getattr(core, name, None) for name in ("keypair", "signed_tx", "send")}
    def deny(*_args, **_kwargs):
        raise RuntimeError("ORACLE050_EXECUTION_DENIED")
    for name in original_signing:
        setattr(core, name, deny)

    before = hash_sources(root)
    bridge = ScannerExecutorBridge(root)
    bridge.install(q18, q25, q20)
    bridge.start_ingress()
    status = "COMPLETED"
    try:
        print("[SCANNER] ORIGINAL_Q25_Q20_Q18", flush=True)
        print("[TRANSPORT] ORIGINAL_PERSISTENT_WS_ONLY", flush=True)
        print("[MONEY] NATIVE_PREBUILD_AND_PRE_SIMULATION_HANDOFF_ONLY", flush=True)
        print("[SCANNER_SOURCE] FROZEN [SIGNING] FALSE [BROADCAST] FALSE", flush=True)
        q25.run(float(seconds))
    except Exception as exc:
        status = "HOLD_ORIGINAL_RUNTIME_" + type(exc).__name__
        print("[HOLD]", status, flush=True)
    finally:
        bridge.close_ingress()
        bridge.restore()
        for name, fn in original_signing.items():
            setattr(core, name, fn)
        payload = bridge.report()
        payload["status"] = status
        if status == "COMPLETED" and not bridge.quote_events:
            payload["status"] = "HOLD_ORIGINAL_SCANNER_NO_EXACT_QUOTES"
        elif status == "COMPLETED" and bridge.ready:
            payload["status"] = "ORIGINAL_SCANNER_LIVE_NATIVE_TEMPLATES_BOUND"
        elif status == "COMPLETED":
            payload["status"] = "ORIGINAL_SCANNER_LIVE_NATIVE_PREP_HOLD"
        payload["scanner_sources_unchanged"] = before == hash_sources(root)
        # Never persist key material, signatures, URLs or raw snapshots.
        atomic_write(root / REPORT, payload)
        print("[ORACLE050_RESULT]", json.dumps(payload, sort_keys=True), flush=True)
        print("[REPORT]", root / REPORT, flush=True)
    return 0 if payload["status"] == "ORIGINAL_SCANNER_LIVE_NATIVE_TEMPLATES_BOUND" and payload["scanner_sources_unchanged"] else 2


def service(root, seconds):
    # One original scanner child at a time; no Oracle-047/049 startup.
    print("[SERVICE] ORIGINAL_SCANNER_SEQUENTIAL_WINDOWS", flush=True)
    windows = 0
    consecutive_failures = 0
    try:
        while True:
            code = parent(root, seconds)
            windows += 1
            consecutive_failures = 0 if code == 0 else consecutive_failures + 1
            print("[SERVICE_WINDOW]", windows, "exit_code", code, flush=True)
            if consecutive_failures >= 3:
                print("[SERVICE_HOLD] THREE_FAILED_WINDOWS_NO_RETRY_LOOP", flush=True)
                return 2
            time.sleep(2 if code == 0 else (10 * consecutive_failures))
    except KeyboardInterrupt:
        print("[SERVICE_STOP] windows", windows, flush=True)
        return 130


def child(root, seconds):
    sys.path.insert(0, str(root.resolve()))
    return run_original(root, seconds)


def parent(root, seconds):
    cmd = [sys.executable, "-I", "-u", str(Path(__file__).resolve()),
           "--child", "--seconds", str(seconds)]
    clean = scrub(os.environ)
    # Parent retains its environment; child gets neither a signing key nor wallet secret.
    p = subprocess.run(cmd, cwd=root, env=clean)
    return p.returncode


class Tests(unittest.TestCase):
    def test_no_secret(self):
        env = scrub({"QSB_SOLANA_PRIVATE_KEY": "x"})
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY", env)
        self.assertEqual(env["QARB_HOT_PAIRS"], "28")
        self.assertEqual(env["QARB_MAX_ACCOUNTS"], "384")

    def test_tiers(self):
        r = {"created_epoch": 100, "rows": [{"token": "A", "lifecycle": {"stage": "HOT"}}]}
        self.assertEqual(tier_for("A", r, now=120), "HOT")
        self.assertEqual(tier_for("A", r, now=800), "UNVERIFIED")

    def test_nonpositive_hold(self):
        x = {"token": "A", "direction": "PUMP_TO_METEORA", "start": 10_000_000,
             "local_net": -1}
        self.assertEqual(eligible_quote(x, {"A"}, 100, 110, "HOT"), "HOLD_NO_POSITIVE_POST_RESERVE")

    def test_stale_hold(self):
        x = {"token": "A", "direction": "PUMP_TO_METEORA", "start": 10_000_000,
             "local_net": 1_000_000}
        self.assertEqual(eligible_quote(x, {"A"}, 1, MAX_AGE_NS+2, "HOT"), "HOLD_STALE_SNAPSHOT")

    def test_native_hold(self):
        x = {"token": "A", "direction": "PUMP_TO_METEORA", "start": 10_000_000,
             "local_net": 1_000_000}
        self.assertEqual(eligible_quote(x, set(), 100, 110, "HOT"), "HOLD_NATIVE_TEMPLATE_NOT_READY")

    def test_live_scanner_hook_preserves_original_output(self):
        class Fake18:
            def exact_snapshot_opportunities(self, s, size):
                return [{"token": "A", "direction": "PUMP_TO_METEORA", "start": 10_000_000,
                         "local_net": 1_000_000, "pump_pool": "P", "meteora": {"address": "M"}}]
        class Fake25:
            def install_hot_math_and_prewarm(self, s):
                return ["native"]
        a, b = Fake18(), Fake25()
        class Fake20:
            class LatestStateLane:
                def _price(self, token, row):
                    return a.exact_snapshot_opportunities(row[0], .010)
        c = Fake20()
        original = a.exact_snapshot_opportunities
        bridge = ScannerExecutorBridge(Path.cwd(), clock=lambda: 100)
        bridge.tiers = {"created_epoch": time.time(), "rows": [{"token": "A", "lifecycle": {"stage": "HOT"}}]}
        bridge.ready = {"A"}
        bridge.install(a, b, c)
        rows = c.LatestStateLane()._price("A", ({"token": "A"}, 10, 99, 1))
        self.assertEqual(rows[0]["local_net"], 1_000_000)
        self.assertEqual(bridge.handoff_count, 1)
        self.assertEqual(len(bridge.drain()), 1)
        bridge.restore()
        self.assertEqual(a.exact_snapshot_opportunities.__func__, original.__func__)

    def test_ingress_persists_prehandoff_without_orders(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            b = ScannerExecutorBridge(temp)
            b.pending.append({"token": "A", "direction": "PUMP_TO_METEORA",
                              "observed_ns": b.clock(), "execution_authority": False,
                              "simulation_pass": False})
            b.start_ingress()
            time.sleep(.06)
            b.close_ingress()
            output = Path(temp) / JOURNAL
            rows = [json.loads(s) for s in output.read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["gate"], "AWAITING_ATOMIC_SIMULATION_AND_ACTUAL_NET_PROFIT")
            self.assertFalse(rows[0]["execution_authority"])

    def test_stale_original_event_cannot_be_relaundered(self):
        class Scanner:
            def exact_snapshot_opportunities(self, snap, size):
                return [{"token": "A", "direction": "PUMP_TO_METEORA",
                         "start": 10_000_000, "local_net": 300_000}]
        class Warm:
            def install_hot_math_and_prewarm(self, state):
                return []
        a, b = Scanner(), Warm()
        class LaneModule:
            class LatestStateLane:
                def _price(self, token, row):
                    return a.exact_snapshot_opportunities(row[0], .01)
        c = LaneModule()
        bridge = ScannerExecutorBridge(Path.cwd(), clock=lambda: MAX_AGE_NS + 1000)
        bridge.ready = {"A"}
        bridge.tiers = {"created_epoch": time.time(),
                        "rows": [{"token": "A", "lifecycle": {"stage": "HOT"}}]}
        bridge.install(a, b, c)
        try:
            c.LatestStateLane()._price("A", ({"token": "A"}, 4, 1, 1))
            self.assertEqual(bridge.handoff_count, 0)
            self.assertTrue(bridge.holds["HOLD_STALE_SNAPSHOT"])
        finally:
            bridge.restore()

    def test_native_compilation_and_unsigned_sim_once(self):
        class Native:
            @staticmethod
            def same_snapshot_route(wallet, snap, opportunity):
                return {"token": opportunity["token"]}
            @staticmethod
            def compile_current(wallet, route):
                return {"ok": True, "raw": b"unsigned"}
            @staticmethod
            def simulate_current(built, wallet):
                return {"err": None}
        bridge = ScannerExecutorBridge(Path.cwd(), clock=lambda: 10)
        bridge._runtime = Native
        bridge._public_wallet = "public"
        candidate = ({"token": "A"}, {"token": "A", "direction": "PUMP_TO_METEORA"}, 9)
        bridge._simulate_p2m_once(candidate)
        bridge._simulate_p2m_once(candidate)
        self.assertEqual(bridge.unsigned_simulations, 1)
        self.assertEqual(bridge.unsigned_sim_passes, 1)
        self.assertTrue(bridge.holds["BOUNDED_ONE_SIMULATION_PER_WINDOW"])

    def test_quote_exception_is_not_hidden(self):
        class Fail18:
            def exact_snapshot_opportunities(self, snap, size):
                raise RuntimeError("PUMP_QUOTE_FAIL")
        class Fail25:
            def install_hot_math_and_prewarm(self, state):
                return []
        a, b = Fail18(), Fail25()
        class Fail20:
            class LatestStateLane:
                def _price(self, token, row):
                    return a.exact_snapshot_opportunities(row[0], .01)
        c = Fail20()
        bridge = ScannerExecutorBridge(Path.cwd())
        bridge.install(a, b, c)
        try:
            with self.assertRaises(RuntimeError):
                c.LatestStateLane()._price("A", ({}, 1, bridge.clock(), 1))
            self.assertEqual(bridge.holds["ORIGINAL_EXACT_QUOTE_RuntimeError"], 1)
        finally:
            bridge.restore()

    def test_no_new_scanner(self):
        self.assertEqual(ScannerExecutorBridge(Path.cwd()).report()["source"],
                         "ORIGINAL_Q25_Q20_Q18_SCANNER")

    def test_canary(self):
        self.assertEqual(CANARY_LAMPORTS, 10_000_000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--service", action="store_true")
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--seconds", type=int, default=90)
    args = ap.parse_args()
    root = Path.cwd()
    if args.test:
        run = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if run.wasSuccessful() else 1
    if args.audit:
        row = original_contract(root)
        row.update({"revision": VERSION, "original_sources_sha256": hash_sources(root),
                    "scanner_will_be_reused": True, "execution_authority": False})
        print("[CONSOLIDATION_CONTRACT]", json.dumps(row, sort_keys=True))
        return 0 if row["ready"] else 2
    if args.child:
        return child(root, args.seconds)
    if args.run or args.service:
        if not 60 <= args.seconds <= 3600:
            print("[HOLD] SECONDS_MUST_BE_60_TO_3600")
            return 2
        if args.service:
            return service(root, args.seconds)
        return parent(root, args.seconds)
    if not (root / ROOT_PACKAGE).is_dir():
        print("[HOLD] EXECUTOR_DIRECTORY_MISSING")
        return 2
    target = root / TARGET
    if Path(__file__).resolve() != target.resolve():
        shutil.copyfile(Path(__file__), target)
    print("[PASS]", VERSION)
    print("[SCANNER] ORIGINAL_Q25_Q20_Q18_PRESERVED")
    print("[ORACLE047_OR049] NOT_USED")
    print("[SIGNING] FALSE [BROADCAST] FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
