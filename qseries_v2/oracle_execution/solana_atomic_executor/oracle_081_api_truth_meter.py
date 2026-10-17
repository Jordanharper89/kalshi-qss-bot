"""ORACLE-081 observational instrument and startup PNL separation.
Counts outgoing Helius urllib JSON RPC requests and inbound WebSocket payload
bytes. Credit costs are estimates, not Helius dashboard billing amounts.
"""
from contextlib import contextmanager
from collections import Counter
import importlib
import json
from pathlib import Path
import re
import threading
import time
import urllib.parse
import urllib.request

RPC_COST_TEN = frozenset((
    'getProgramAccounts', 'getTransaction', 'getSignaturesForAddress',
    'getBlock', 'getBlocks', 'getBlockTime', 'getBlockSignatures',
    'getConfirmedTransaction', 'getConfirmedBlock',
))

def safe_method(request):
    try:
        raw = getattr(request, 'data', None)
        if not isinstance(raw, bytes):
            return 'UNKNOWN_HTTP'
        value = json.loads(raw.decode('utf-8'))
        if not isinstance(value, dict):
            return 'UNKNOWN_RPC'
        name = value.get('method')
        if isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_]{1,64}', name):
            return name
        return 'UNKNOWN_RPC'
    except (ValueError, UnicodeDecodeError, TypeError):
        return 'UNKNOWN_RPC'

def helius_request(req):
    try:
        url = req.full_url if hasattr(req, 'full_url') else str(req)
        host = (urllib.parse.urlsplit(url).hostname or '').lower()
        return host == 'helius-rpc.com' or host.endswith('.helius-rpc.com')
    except (ValueError, TypeError):
        return False

class Usage:
    def __init__(self):
        self.lock = threading.Lock()
        self.rpc = Counter()
        self.ws_bytes = 0
        self.ws_messages = 0
        self.start = time.monotonic()

    def request(self, req):
        if not helius_request(req):
            return
        method = safe_method(req)
        with self.lock:
            self.rpc[method] += 1

    def message(self, value):
        n = len(value.encode('utf-8')) if isinstance(value, str) else (
            len(value) if isinstance(value, bytes) else 0)
        with self.lock:
            self.ws_bytes += n
            self.ws_messages += 1

    def report(self):
        with self.lock:
            methods = dict(sorted(self.rpc.items()))
            wsbytes = self.ws_bytes
            messages = self.ws_messages
        count = sum(methods.values())
        rpc_credits = sum((10 if m in RPC_COST_TEN else 1) * n
                          for m, n in methods.items())
        stream_credits = round(wsbytes / 1_000_000 * 20.0, 3)
        return {
            'rpc_requests_observed': count,
            'rpc_by_method': methods,
            'estimated_rpc_credits': rpc_credits,
            'websocket_messages_observed': messages,
            'websocket_payload_bytes_observed': wsbytes,
            'estimated_ws_credits_at_20_per_mb': stream_credits,
            'estimated_combined_credits': round(rpc_credits + stream_credits, 3),
            'elapsed_seconds': round(time.monotonic() - self.start, 2),
            'note': 'Partial instrumented local estimate. Helius dashboard is billing authority.',
            'startup_snapshot_as_profit_disabled': True,
            'signing': False, 'broadcast': False,
        }

def websocket_recv_patches(meter):
    originals = []
    for module, name in (
        ('websockets.asyncio.connection', 'Connection'),
        ('websockets.legacy.protocol', 'WebSocketCommonProtocol'),
    ):
        try:
            cls = getattr(importlib.import_module(module), name)
            old = cls.recv
        except (ImportError, AttributeError):
            continue
        async def counting_recv(self, *args, _old=old, **kwargs):
            data = await _old(self, *args, **kwargs)
            meter.message(data)
            return data
        cls.recv = counting_recv
        originals.append((cls, old))
    return originals

@contextmanager
def observe(root, index):
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as live

    meter = Usage()
    original_initial = live._initial_scan
    original_urlopen = urllib.request.urlopen
    stop = threading.Event()

    def ignored_initial_scan(*_args, **_kwargs):
        print('[ORACLE054_STARTUP_PNL] INITIAL_HYDRATION_NOT_AN_EXECUTABLE_PROFIT', flush=True)
        return None

    def counting_urlopen(request, *args, **kwargs):
        meter.request(request)
        return original_urlopen(request, *args, **kwargs)

    def heartbeat():
        while not stop.wait(30.0):
            r = meter.report()
            print('[ORACLE054_API_USAGE] estimated_credits=%s http=%s ws_MB=%.3f startup_profit=SUPPRESSED' % (
                r['estimated_combined_credits'], r['rpc_requests_observed'],
                r['websocket_payload_bytes_observed']/1e6), flush=True)

    ws_old = []
    t = None
    try:
        live._initial_scan = ignored_initial_scan
        urllib.request.urlopen = counting_urlopen
        ws_old = websocket_recv_patches(meter)
        t = threading.Thread(target=heartbeat, name='oracle081-meter', daemon=True)
        t.start()
        print('[ORACLE054_PNL_POLICY] STARTUP_SNAPSHOT_PNL_SUPPRESSED FRESH_EXECUTABLE_ONLY', flush=True)
        yield meter
    finally:
        stop.set()
        if t is not None:
            t.join(timeout=2)
        urllib.request.urlopen = original_urlopen
        live._initial_scan = original_initial
        for cls, old in reversed(ws_old):
            cls.recv = old
        result = meter.report()
        result['observation_window'] = index
        path = Path(root) / 'runtime_state/oracle/oracle_live_execution/oracle_081_api_truth_meter.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')
        tmp.replace(path)
        print('[ORACLE054_API_USAGE_FINAL] %s' % json.dumps({
            k: result[k] for k in ('rpc_requests_observed','rpc_by_method',
                'estimated_rpc_credits','websocket_payload_bytes_observed',
                'estimated_ws_credits_at_20_per_mb','estimated_combined_credits')}, sort_keys=True), flush=True)
        print('[ORACLE054_PNL_TRUTH] INITIAL_PNL_UNTRUSTED SIMULATED_PNL_UNCERTIFIED REALIZED_PNL_NOT_MEASURED', flush=True)
