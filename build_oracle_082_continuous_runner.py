"""ORACLE-082 one-lifetime original scanner + staged Mriya WS replenishment.

Install using Windows CMD venv. Never reads, clears, prints or stores wallet keys.
"""
import argparse
import ast
import getpass
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import threading
from urllib.parse import quote
import uuid

ROOT = Path.cwd()
PKG = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor'
V50 = PKG / 'oracle_050_original_scanner_executor_consolidation.py'
V54 = PKG / 'oracle_054_reverse_native_handoff.py'
V82 = PKG / 'oracle_082_continuous_inventory_runner.py'
MARK = 'ORACLE082_CONTINUOUS_CUTOVER'
OLD50 = '''        if self.unsigned_simulations or self.native_compiles:
            self.holds["BOUNDED_ONE_SIMULATION_PER_WINDOW"] += 1
            return
'''
NEW50 = '''        # ORACLE082_CONTINUOUS_CUTOVER: bounded continuous native attempts.
        if os.environ.get("ORACLE082_ENABLED") == "1":
            from qseries_v2.oracle_execution.solana_atomic_executor import oracle_082_continuous_inventory_runner as o82
            if not o82.allow_native(self):
                self.holds["ORACLE082_NATIVE_RATE_LIMIT"] += 1
                return
        elif self.unsigned_simulations or self.native_compiles:
            self.holds["BOUNDED_ONE_SIMULATION_PER_WINDOW"] += 1
            return
'''
OLD54 = '''        if self.native_compiles or self.unsigned_simulations:
            stats["bounded_attempt_already_used"] += 1
            return
'''
NEW54 = '''        # ORACLE082_CONTINUOUS_CUTOVER: same rate gate for reverse direction.
        if os.environ.get("ORACLE082_ENABLED") == "1":
            from qseries_v2.oracle_execution.solana_atomic_executor import oracle_082_continuous_inventory_runner as o82
            if not o82.allow_native(self):
                stats["ORACLE082_NATIVE_RATE_LIMIT"] += 1
                return
        elif self.native_compiles or self.unsigned_simulations:
            stats["bounded_attempt_already_used"] += 1
            return
'''
OLDWINDOW = '            status = v53.one_window(root, seconds, index, runid)\n'
NEWWINDOW = '''            # ORACLE082_CONTINUOUS_CUTOVER: hook original scanner lifetime.
            from qseries_v2.oracle_execution.solana_atomic_executor import oracle_082_continuous_inventory_runner as o82
            with o82.activate(root):
                status = v53.one_window(root, seconds, index, runid)
'''
MODULE = r'''"""ORACLE-082 persistent live inventory manager, unsigned execution only.

The original quote math and its scanner are untouched. Acknowledged websocket
subscriptions and staged native templates are required before state publication.
"""
import asyncio
from collections import Counter, deque
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import time

CAPACITY = 384
SHARD_CAP = 64
MAX_PAIRS = 28
STAGE_INTERVAL = 65.0
REGISTRY_MAX_AGE = 600.0
ACK_TIMEOUT = 25.0
VENUE_TIMEOUT = 90.0
MAX_DISCOVERY_RPC_PER_MINUTE = 8


def allow_native(bridge):
    """Shared, nonblocking bounded rate gate for both execution directions."""
    now = time.monotonic()
    with bridge.lock:
        times = getattr(bridge, '_oracle082_attempts', None)
        if times is None:
            times = deque()
            bridge._oracle082_attempts = times
        while times and now - times[0] > 60:
            times.popleft()
        if len(times) >= 10 or (times and now - times[-1] < 0.75):
            return False
        times.append(now)
        return True


class Shard(list):
    pass


class Inventory:
    def __init__(self, root):
        self.root = Path(root)
        self.shards = []
        self.ack = set()
        self.events = {}
        self.manager_task = None
        self.state = None
        self.bridge = None
        self.ws_stats = Counter()
        self.stats = Counter()
        self.failed = {}
        self.recent_sigs = deque(maxlen=1000)
        self.last_stage = 0.0
        self.last_status = 0.0
        self.last_candidate_time = 0.0
        self.staging = set()
        self._original_worker = None

    def init_shards(self, addrs):
        if self.shards:
            raise RuntimeError('ORACLE082_DUPLICATE_SCANNER_SHARDS')
        original = list(dict.fromkeys(addrs))
        if len(original) > CAPACITY:
            raise RuntimeError('ORACLE082_INITIAL_ACCOUNT_CAPACITY_EXCEEDED')
        self.shards = [Shard() for _ in range(CAPACITY // SHARD_CAP)]
        for i, address in enumerate(original):
            self.shards[i % len(self.shards)].append(address)
        return self.shards

    def stage_addresses(self, addrs):
        requested = list(dict.fromkeys(addrs))
        existing = set(a for s in self.shards for a in s)
        newly = [a for a in requested if a not in existing]
        if len(existing) + len(newly) > CAPACITY:
            raise RuntimeError('ORACLE082_SUBSCRIPTION_CAPACITY_HOLD')
        for a in newly:
            possible = [s for s in self.shards if len(s) < SHARD_CAP]
            if not possible:
                raise RuntimeError('ORACLE082_NO_RUNNING_SHARD_CAPACITY')
            min(possible, key=len).append(a)
        self.staging.update(newly)
        return newly

    def release(self, addrs):
        for a in addrs:
            if a in self.staging:
                self.staging.discard(a)
                for s in self.shards:
                    if a in s:
                        s.remove(a)
                self.ack.discard(a)
                self.events.pop(a, None)

    def record_event(self, addr):
        self.events[addr] = time.monotonic()

    def active(self):
        return len(self.state.get('pairs') or []) if self.state else 0

    def refresh_tiers(self):
        if self.bridge is None:
            return
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_050_original_scanner_executor_consolidation as v50)
        # The existing physically verified tier registry is the only authority.
        self.bridge.tiers = v50.latest_tiers(self.root)

    def eligible_candidates(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
            qarb_043b_paced_mriya_token_discovery as discovery)
        registry = discovery.load()
        now = time.time()
        active = {x.token for x in (self.state.get('pairs') or [])}
        rows = []
        for token, info in (registry.get('tokens') or {}).items():
            if token in active or token in self.failed:
                if token in self.failed and time.monotonic() > self.failed[token]:
                    self.failed.pop(token, None)
                else:
                    continue
            seen = float(info.get('last_seen_epoch') or 0)
            if seen > now + 30 or now - seen > REGISTRY_MAX_AGE:
                continue
            rows.append((seen, int(info.get('touches') or 0), token))
        rows.sort(reverse=True)
        return [token for _, _, token in rows]

    def stage_pair(self, token):
        """Off-hot-path hydration and isolated template construction."""
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
            live_account_stream as pd,
            qarb_044_dynamic_exact_crossvenue_binding as binding)
        from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_054_reverse_native_handoff as v54)
        wallet = self.bridge._public_wallet
        if not wallet:
            raise RuntimeError('ORACLE082_PUBLIC_WALLET_MISSING')
        pool = binding.canonical_pump_pool(token)
        raw, owner = core.account(pool)
        decoded = core.decode_pump_pool(raw)
        if (owner != core.PUMP or decoded['base_mint'] != token
                or decoded['quote_mint'] != core.WSOL):
            raise RuntimeError('ORACLE082_INVALID_PUMP_POOL')
        meta = core.discover_dlmm(token)
        if {meta.get('token_x'), meta.get('token_y')} != {token, core.WSOL}:
            raise RuntimeError('ORACLE082_INVALID_DLMM_PAIR')
        saved, limit = pd.engine.candidate_universe, pd.MAX_PAIRS
        try:
            pd.engine.candidate_universe = lambda root: [
                {'token': token, 'pump_pool': pool, 'meteora_meta': meta}]
            pd.MAX_PAIRS = 1
            pairs, _ = pd.prepare_pairs(self.root)
        finally:
            pd.engine.candidate_universe, pd.MAX_PAIRS = saved, limit
        if len(pairs) != 1 or pairs[0].token != token:
            raise RuntimeError('ORACLE082_PAIR_HYDRATION_FAILED')
        pair = pairs[0]
        warm = q23.worker().warm(token)
        if not warm.get('program'):
            raise RuntimeError('ORACLE082_TOKEN_PROGRAM_NOT_WARM')
        # Never reset the live runtime's TEMPLATES / READY_TOKENS dictionaries.
        package = Path(__file__).with_name('runtime.py')
        spec = importlib.util.spec_from_file_location('oracle082_staged_runtime', package)
        staged = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(staged)
        source = {'pairs': [pair]}
        staged.prebuild_templates(source, wallet)
        staged.prebuild_meteora_templates(source, wallet,
                                          [{'token': token, 'program': warm['program']}])
        if token not in staged.READY_TOKENS:
            raise RuntimeError('ORACLE082_NATIVE_TEMPLATE_NOT_READY')
        reverse = v54.warm_reverse_templates(source, wallet, staged,
                                             self.root, Counter())
        if token not in reverse:
            raise RuntimeError('ORACLE082_REVERSE_SELL_TEMPLATE_NOT_READY')
        return pair, dict(staged.TEMPLATES[token]), dict(staged.METEORA_TEMPLATES[token]), reverse[token]

    async def wait_for_ready(self, pair, addrs, stop):
        start = time.monotonic()
        expected = set(addrs)
        while not stop.is_set() and time.monotonic() - start < ACK_TIMEOUT:
            if expected <= self.ack:
                break
            await asyncio.sleep(0.15)
        else:
            return False, 'ORACLE082_SUBSCRIPTION_ACK_TIMEOUT'
        # Fresh updates from BOTH venues, not just successful subscription RPCs.
        armed = time.monotonic()
        pump = {pair.pump_base_vault, pair.pump_quote_vault}
        dlmm = {pair.meteora_pool} | {a[1] for a in pair.arrays}
        while not stop.is_set() and time.monotonic() - armed < VENUE_TIMEOUT:
            if (any(self.events.get(a, 0) >= armed for a in pump)
                    and any(self.events.get(a, 0) >= armed for a in dlmm)):
                return True, 'ACK_AND_TWO_VENUE_EVENTS'
            await asyncio.sleep(0.25)
        return False, 'ORACLE082_TWO_VENUE_LIVE_EVIDENCE_TIMEOUT'

    def promote(self, pair, pump_template, meteora_template, reverse_template):
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
        state = self.state
        token = pair.token
        if token in {p.token for p in state['pairs']}:
            return False
        if len(state['pairs']) >= MAX_PAIRS:
            return False
        i = len(state['pairs'])
        # Atomic event-loop publication, no await between operations.
        rt.TEMPLATES[token] = pump_template
        rt.METEORA_TEMPLATES[token] = meteora_template
        self.bridge._oracle054_templates[token] = reverse_template
        rt.READY_TOKENS.add(token)
        self.bridge.ready.add(token)
        state['pairs'].append(pair)
        state['preg'][pair.pump_base_vault] = (i, 'PUMP_BASE')
        state['preg'][pair.pump_quote_vault] = (i, 'PUMP_QUOTE')
        state['preg'][pair.meteora_pool] = (i, 'DLMM_POOL')
        for j, row in enumerate(pair.arrays):
            state['preg'][row[1]] = (i, 'DLMM_ARRAY_%d' % j)
        state['eps'].setdefault(token, []).extend((m._pump_ep(pair), m._dlmm_ep(pair)))
        for a in pair.watched_accounts():
            if a not in state['addresses']:
                state['addresses'].append(a)
            self.staging.discard(a)
        self.bridge.verified_pairs = len(state['pairs'])
        self.stats['pairs_added'] += 1
        print('[ORACLE082_PROMOTED] token=%s active_pairs=%d acked=True two_venues=True native_both=True tier_authority=UNCHANGED' %
              (token[:10], self.active()), flush=True)
        return True

    async def replenish(self, stop):
        discovery_task = asyncio.create_task(self.discover_mriya(stop))
        try:
            while not stop.is_set():
                now = time.monotonic()
                if now - self.last_status > 30:
                    self.last_status = now
                    print('[ORACLE082_HEALTH] %s' % json.dumps({
                        'active_pairs': self.active(), 'subscribed_accounts': sum(map(len, self.shards)),
                        'acked_accounts': len(self.ack), 'added': self.stats['pairs_added'],
                        'discovery_rpc': self.stats['discovery_rpc'],
                        'native_rate_holds': (self.bridge.holds.get('ORACLE082_NATIVE_RATE_LIMIT', 0)
                                              if self.bridge else 0),
                        'signing': False, 'broadcast': False,
                    }, sort_keys=True), flush=True)
                if self.bridge and now - self.last_candidate_time > 30:
                    self.last_candidate_time = now
                    self.refresh_tiers()
                if (self.bridge and self.state and self.bridge._runtime
                        and self.active() < MAX_PAIRS
                        and now - self.last_stage >= STAGE_INTERVAL):
                    candidates = self.eligible_candidates()
                    if candidates:
                        token = candidates[0]
                        self.last_stage = now
                        new = []
                        try:
                            pair, pump, meteora, reverse = await asyncio.to_thread(self.stage_pair, token)
                            new = self.stage_addresses(pair.watched_accounts())
                            ok, why = await self.wait_for_ready(pair, pair.watched_accounts(), stop)
                            if not ok:
                                raise RuntimeError(why)
                            if not self.promote(pair, pump, meteora, reverse):
                                raise RuntimeError('ORACLE082_PROMOTION_CONFLICT')
                        except asyncio.CancelledError:
                            self.release(new)
                            raise
                        except Exception as exc:
                            self.release(new)
                            self.failed[token] = time.monotonic() + 600
                            self.stats['pair_holds'] += 1
                            print('[ORACLE082_PAIR_HOLD] token=%s reason=%s' %
                                  (token[:10], type(exc).__name__), flush=True)
                await asyncio.sleep(0.25)
        finally:
            discovery_task.cancel()
            await asyncio.gather(discovery_task, return_exceptions=True)

    async def discover_mriya(self, stop):
        import websockets
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
            qarb_043b_paced_mriya_token_discovery as d)
        minute = deque()
        delay = 2.0
        while not stop.is_set():
            try:
                async with websockets.connect(
                        os.environ.get('SOLANA_WS_URL') or core.RPC.replace('https:', 'wss:'),
                        ping_interval=20, ping_timeout=20, max_size=4000000) as ws:
                    await ws.send(json.dumps({'jsonrpc':'2.0','id':82,'method':'logsSubscribe',
                        'params':[{'mentions':[d.MRIYA]}, {'commitment':'confirmed'}]}))
                    delay = 2.0
                    while not stop.is_set():
                        try:
                            message = json.loads(await asyncio.wait_for(ws.recv(), 1.0))
                        except asyncio.TimeoutError:
                            continue
                        if message.get('method') != 'logsNotification':
                            continue
                        signature = (((message.get('params') or {}).get('result') or {}).get('value') or {}).get('signature')
                        if not signature or signature in self.recent_sigs:
                            continue
                        self.recent_sigs.append(signature)
                        t = time.monotonic()
                        while minute and t-minute[0] >= 60:
                            minute.popleft()
                        if len(minute) >= MAX_DISCOVERY_RPC_PER_MINUTE:
                            self.stats['discovery_budget_holds'] += 1
                            continue
                        minute.append(t)
                        self.stats['discovery_rpc'] += 1
                        try:
                            tx = await asyncio.to_thread(core.rpc, 'getTransaction', [signature, {
                                'encoding':'jsonParsed', 'commitment':'confirmed',
                                'maxSupportedTransactionVersion':1}])
                            if not tx:
                                continue
                            tokens = d.tx_mints(tx)
                            if not tokens:
                                continue
                            registry = d.load()
                            now_epoch = time.time()
                            for token in tokens:
                                row = registry.setdefault('tokens', {}).setdefault(token, {
                                    'first_seen_epoch':now_epoch,'last_seen_epoch':now_epoch,'touches':0})
                                row['last_seen_epoch'] = now_epoch
                                row['touches'] = int(row.get('touches', 0)) + 1
                            registry['updated_epoch'] = now_epoch
                            d.save(registry)
                            self.stats['mriya_events'] += 1
                        except Exception as exc:
                            self.stats['discovery_holds'] += 1
                            print('[ORACLE082_DISCOVERY_HOLD] reason=%s' % type(exc).__name__, flush=True)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.stats['discovery_reconnects'] += 1
                print('[ORACLE082_DISCOVERY_RECOVER] reason=%s delay=%.1f' %
                      (type(exc).__name__, delay), flush=True)
                await asyncio.sleep(delay)
                delay = min(30.0, delay * 2)

    async def worker(self, index, shard, q, c, stop):
        import websockets
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
            persistent_profit_runtime as p)
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
        if index == 0 and self.manager_task is None:
            self.manager_task = asyncio.create_task(self.replenish(stop))
        await asyncio.sleep(index * m.STAGGER_SECONDS)
        delay = p.RECONNECT_MIN
        try:
            while not stop.is_set():
                active_sub = {}  # address -> numeric subscription ID
                by_request = {}
                submap = {}
                next_id = 1
                try:
                    async with websockets.connect(m.WS_URL, ping_interval=20,
                            ping_timeout=20, close_timeout=3, max_size=8000000) as ws:
                        c['connections'] += 1
                        delay = p.RECONNECT_MIN
                        while not stop.is_set():
                            for address in tuple(shard):
                                if address not in active_sub and address not in by_request.values():
                                    req_id = next_id
                                    next_id += 1
                                    by_request[req_id] = address
                                    await ws.send(json.dumps({'jsonrpc':'2.0', 'id':req_id,
                                        'method':'accountSubscribe', 'params':[address,
                                        {'encoding':'base64','commitment':'processed'}]}, separators=(',', ':')))
                                    if m.SUB_DELAY_MS:
                                        await asyncio.sleep(m.SUB_DELAY_MS/1000.0)
                            for address, subscription in tuple(active_sub.items()):
                                if address not in shard:
                                    req_id = next_id
                                    next_id += 1
                                    await ws.send(json.dumps({'jsonrpc':'2.0','id':req_id,
                                        'method':'accountUnsubscribe','params':[subscription]}))
                                    active_sub.pop(address, None)
                                    submap.pop(subscription, None)
                                    self.ack.discard(address)
                            try:
                                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.2))
                            except asyncio.TimeoutError:
                                continue
                            if 'id' in msg and isinstance(msg.get('result'), int):
                                addr = by_request.pop(msg['id'], None)
                                if addr:
                                    sid = msg['result']
                                    if addr not in shard:
                                        await ws.send(json.dumps({'jsonrpc':'2.0','id':next_id,
                                            'method':'accountUnsubscribe','params':[sid]}))
                                        next_id += 1
                                    else:
                                        active_sub[addr] = sid
                                        submap[sid] = addr
                                        self.ack.add(addr)
                                        c['acks'] += 1
                                continue
                            ev = m._parse(msg, submap)
                            if not ev:
                                continue
                            self.record_event(ev['address'])
                            c['notifications'] += 1
                            try:
                                q.put_nowait(ev)
                            except asyncio.QueueFull:
                                c['queue_drops'] += 1
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self.stats['ws_reconnects'] += 1
                    c['reconnects'] += 1
                    c['last_ws_error'] = type(exc).__name__
                    print('[ORACLE082_WS_RECOVER] shard=%d reason=%s delay=%.1f' %
                          (index, type(exc).__name__, delay), flush=True)
                    await asyncio.sleep(delay)
                    delay = min(p.RECONNECT_MAX, max(p.RECONNECT_MIN, delay*2))
                finally:
                    self.ack.difference_update(shard)
        finally:
            if index == 0 and self.manager_task is not None:
                self.manager_task.cancel()
                await asyncio.gather(self.manager_task, return_exceptions=True)


@contextmanager
def activate(root):
    if os.environ.get('ORACLE082_ENABLED') != '1':
        yield
        return
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
        persistent_profit_runtime as p, merged_live_runtime as m)
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_050_original_scanner_executor_consolidation as v50)
    manager = Inventory(root)
    old_bind = q25.bind_cached_state
    old_shards = m._shards
    old_worker = p._worker
    old_init = v50.ScannerExecutorBridge.__init__
    old_best = p._best_text

    def record_bridge(bridge, *args, **kwargs):
        old_init(bridge, *args, **kwargs)
        manager.bridge = bridge

    def capture_state(state):
        result = old_bind(state)
        manager.state = state
        return result

    def dynamic_shards(addresses):
        return manager.init_shards(addresses)

    async def dynamic_worker(i, addrs, q, c, stop):
        return await manager.worker(i, addrs, q, c, stop)

    try:
        q25.bind_cached_state = capture_state
        m._shards = dynamic_shards
        p._worker = dynamic_worker
        v50.ScannerExecutorBridge.__init__ = record_bridge
        p._best_text = lambda best: ('None' if not best else 'UNVERIFIED_LOCAL_INDICATION_HIDDEN')
        print('[ORACLE082_CONTINUOUS] ONE_SCANNER_LIFETIME Mriya_background=ON '
              'live_WS_additions=ON true_startup_PNL=OFF signing=FALSE broadcast=FALSE', flush=True)
        yield
    finally:
        q25.bind_cached_state = old_bind
        m._shards = old_shards
        p._worker = old_worker
        v50.ScannerExecutorBridge.__init__ = old_init
        p._best_text = old_best
'''


def update_source(source, old, new, label):
    if source.count(old) != 1:
        raise RuntimeError(label + '_SOURCE_ANCHOR_NOT_UNIQUE')
    changed = source.replace(old, new, 1)
    ast.parse(changed)
    return changed


def transformations():
    old50 = V50.read_text(encoding='utf-8')
    old54 = V54.read_text(encoding='utf-8')
    if MARK in old50 or MARK in old54:
        raise RuntimeError('ORACLE082_ALREADY_INSTALLED_USE_TEST')
    if 'ORACLE081_TRUTH_AND_USAGE_BOUNDARY' not in old54:
        raise RuntimeError('ORACLE081_API_METER_REQUIRED_BEFORE_082')
    new50 = update_source(old50, OLD50, NEW50, 'ORACLE050_RATE_GATE')
    new54 = update_source(old54, OLD54, NEW54, 'ORACLE054_RATE_GATE')
    new54 = update_source(new54, OLDWINDOW, NEWWINDOW, 'ORACLE054_WINDOW')
    ast.parse(MODULE)
    return {V50:new50, V54:new54, V82:MODULE}


def test():
    from types import SimpleNamespace
    for path in (V50,V54,V82):
        ast.parse(path.read_text(encoding='utf-8'))
    assert MARK in V50.read_text(encoding='utf-8')
    assert MARK in V54.read_text(encoding='utf-8')
    assert V82.read_text(encoding='utf-8') == MODULE
    spec = importlib.util.spec_from_file_location('oracle082_fixture', V82)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    inventory = mod.Inventory(ROOT)
    shards = inventory.init_shards(['EXAMPLE%d'%i for i in range(270)])
    assert len(shards)==6 and max(map(len, shards)) <= 64
    added = inventory.stage_addresses(['EXAMPLE270','EXAMPLE271'])
    assert added == ['EXAMPLE270','EXAMPLE271']
    inventory.ack.update(added)
    inventory.release(added)
    assert not inventory.staging and all(a not in inventory.ack for a in added)
    fake = SimpleNamespace(lock=threading.Lock())
    assert mod.allow_native(fake) is True
    assert mod.allow_native(fake) is False
    try:
        inventory.stage_addresses(['EXAMPLE%d'%i for i in range(500, 620)])
        raise AssertionError('CAPACITY_NOT_ENFORCED')
    except RuntimeError as exc:
        assert 'CAPACITY' in str(exc) or 'SHARD' in str(exc)
    print('[PASS] ORACLE082_SHARD_SUBSCRIBE_STAGE_AND_ROLLBACK')
    print('[PASS] ORACLE082_SHARED_NATIVE_RATE_LIMIT')
    print('[PASS] ORACLE082_LOCAL_SOURCE_AST_AND_PRESERVATION')
    print('[BOUNDARY] OFFLINE_NO_RPC_NO_SIGNING_NO_BROADCAST')


def install():
    required = [V50,V54,PKG/'oracle_080_v1_atomic_fallback.py',
                PKG/'oracle_081_api_truth_meter.py']
    if not all(p.is_file() for p in required):
        raise RuntimeError('ORACLE082_MISSING_REQUIRED_079_080_081_SOURCE')
    if MARK in V50.read_text(encoding='utf-8'):
        test()
        print('[PASS] ORACLE082_ALREADY_INSTALLED')
        return
    updates = transformations()
    for path, content in updates.items():
        if path == V82 and path.exists() and path.read_text(encoding='utf-8') != content:
            raise RuntimeError('ORACLE082_MODULE_CONFLICT')
    originals = {p:p.read_text(encoding='utf-8') for p in (V50,V54)}
    made = not V82.exists()
    for path in (V50,V54):
        backup = path.with_name(path.stem + '.before_oracle082.py')
        if backup.exists() and backup.read_text(encoding='utf-8') != originals[path]:
            raise RuntimeError('ORACLE082_BACKUP_CONFLICT_' + path.name)
        if not backup.exists():
            backup.write_text(originals[path],encoding='utf-8')
    try:
        for path, content in updates.items():
            stage = path.with_suffix('.oracle082.tmp')
            stage.write_text(content, encoding='utf-8')
            stage.replace(path)
        test()
    except BaseException:
        for path, content in originals.items():
            path.write_text(content,encoding='utf-8')
        if made:
            V82.unlink(missing_ok=True)
        print('[ROLLBACK] ORACLE082_PREVIOUS_RUNTIME_RESTORED')
        raise
    print('[PASS] ORACLE082_CONTINUOUS_RUNNER_INSTALLED')
    print('[PATH] ONE_ORIGINAL_WS_SCANNER_LIFETIME + BACKGROUND_MRIYA + V0_OR_V1_UNSIGNED')


def child(seconds):
    sys.path.insert(0, str(ROOT))
    if os.environ.get('ORACLE082_ENABLED') != '1':
        raise RuntimeError('ORACLE082_CHILD_CUTOVER_FLAG_REQUIRED')
    if any('PRIVATE_KEY' in name.upper() or 'SECRET_KEY' in name.upper()
           for name in os.environ):
        raise RuntimeError('ORACLE082_SECRET_ENV_DENIED')
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_054_reverse_native_handoff as v54
    return v54.window(ROOT, seconds, 1, uuid.uuid4().hex)


def launch(seconds):
    test()
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_050_original_scanner_executor_consolidation as v50
    key = getpass.getpass('Helius API key (hidden): ').strip()
    if not key:
        raise RuntimeError('HELIUS_API_KEY_REQUIRED')
    env = v50.scrub(os.environ)
    for name in tuple(env):
        if 'PRIVATE_KEY' in name.upper() or 'SECRET_KEY' in name.upper():
            env.pop(name, None)
    api_key = quote(key, safe='')
    env.update({'ORACLE077_ENABLED':'1','ORACLE082_ENABLED':'1',
        'SOLANA_RPC_URL':'https://mainnet.helius-rpc.com/?api-key='+api_key,
        'SOLANA_WS_URL':'wss://mainnet.helius-rpc.com/?api-key='+api_key})
    key = None
    print('[ORACLE082_START] one_lifetime=True api_meter=True PNL_initial=False signing=False broadcast=False', flush=True)
    print('[ORACLE082_MODE] Ctrl+C to stop. No sequential batches or second CMD needed.', flush=True)
    try:
        return subprocess.call([sys.executable,'-I','-u',str(Path(__file__).resolve()),
                                '--child','--seconds',str(seconds)],env=env,cwd=ROOT)
    except KeyboardInterrupt:
        print('[ORACLE082_STOP] OPERATOR_REQUESTED',flush=True)
        return 130


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--child', action='store_true')
    ap.add_argument('--forever',action='store_true')
    ap.add_argument('--seconds',type=float,default=300.0)
    args=ap.parse_args()
    if args.child:
        raise SystemExit(child(args.seconds))
    elif args.test:
        test()
    elif args.run or args.forever:
        raise SystemExit(launch(315360000 if args.forever else args.seconds))
    else:
        install()
