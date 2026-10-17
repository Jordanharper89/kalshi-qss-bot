"""ORACLE-082 persistent live inventory manager, unsigned execution only.

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
