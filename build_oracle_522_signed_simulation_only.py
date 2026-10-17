from __future__ import annotations
import argparse, ast, hashlib, json, os, re, sys, urllib.request
from pathlib import Path
BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_522_signed_simulation_only.py'
SCANNER = BASE / 'boss_scanner_live.py'
CP26 = BASE / 'checkpoint26_dlmm_output_ata_readiness.py'
REPORT = Path('runtime_state/oracle/oracle_live_execution/oracle_522/sim_only_report.json')
BLOCK = re.compile(r'(?i)\b(?:sendTransaction|sendRawTransaction|sendBundle|submitBundle|submitTransaction|requestAirdrop)\b')
class Hold(RuntimeError): pass
def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def forbidden(*values):
    return any(BLOCK.search(str(v)) for v in values if v is not None)
def rpc_filter(real):
    def restricted(*args, **kwargs):
        if forbidden(args, kwargs):
            raise Hold('BROADCAST_RPC_METHOD_BLOCKED')
        return real(*args, **kwargs)
    return restricted
def url_filter(real):
    def restricted(url, *args, **kwargs):
        body = getattr(url, 'data', None)
        if body is None and args:
            body = args[0]
        if body is None:
            body = kwargs.get('data')
        if forbidden(body):
            raise Hold('BROADCAST_HTTP_PAYLOAD_BLOCKED')
        return real(url, *args, **kwargs)
    return restricted
def requests_filter(real):
    def restricted(self, method, url, **kwargs):
        if forbidden(kwargs.get('data'), kwargs.get('json')):
            raise Hold('BROADCAST_REQUEST_PAYLOAD_BLOCKED')
        return real(self, method, url, **kwargs)
    return restricted
def record(data):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    temp = REPORT.with_suffix('.tmp')
    try:
        temp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
        os.replace(temp, REPORT)
    finally:
        temp.unlink(missing_ok=True)
def tests():
    called = []
    rpc = rpc_filter(lambda *a, **k: called.append((a, k)) or 42)
    assert rpc('simulateTransaction', ['fixture']) == 42
    try:
        rpc('sendTransaction', ['fixture'])
        raise AssertionError('UNBLOCKED_RPC')
    except Hold: pass
    fake = url_filter(lambda *a, **kw: 11)
    assert fake('https://example.invalid', b'{"method":"simulateTransaction"}') == 11
    try:
        fake('https://example.invalid', b'{"method":"sendTransaction"}')
        raise AssertionError('UNBLOCKED_HTTP')
    except Hold: pass
    request = requests_filter(lambda *a, **kw: 12)
    assert request(None, 'POST', 'https://example.invalid', json={'method':'simulateTransaction'}) == 12
    try:
        request(None, 'POST', 'https://example.invalid', json={'method':'sendTransaction'})
        raise AssertionError('UNBLOCKED_REQUEST')
    except Hold: pass
    assert called and SCANNER != TARGET
    print('[PASS] ORACLE522 simulate_allowed broadcast_rpc_blocked http_guarded requests_guarded',flush=True)
def install():
    if not SCANNER.is_file() or not CP26.is_file():
        raise Hold('CANONICAL_SCANNER_OR_CHECKPOINT26_MISSING')
    src = Path(__file__).read_text(encoding='utf-8')
    ast.parse(src)
    before = checksum(SCANNER)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    temp = TARGET.with_name(TARGET.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(src, encoding='utf-8')
        os.replace(temp, TARGET)
    finally:
        temp.unlink(missing_ok=True)
    if checksum(SCANNER) != before:
        raise Hold('FROZEN_SCANNER_CHANGED')
    print('[PASS] ORACLE522_FULL_INSTALL existing_checkpoint26 read_only_network_guard',flush=True)
def run(seconds):
    if not 30 <= seconds <= 180:
        raise Hold('INVALID_BOUNDED_SECONDS')
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('QSB_LIVE_ARM_MUST_BE_NO')
    if not os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('SIGNER_ENVIRONMENT_MISSING_NO_KEY_PRINTED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise Hold('SOLANA_RPC_URL_MISSING')
    if not os.getenv('SOLANA_WS_URL', '').startswith('wss://'):
        raise Hold('SOLANA_WS_URL_MISSING')
    before = checksum(SCANNER)
    old_url = urllib.request.urlopen
    old_argv = list(sys.argv)
    try: import requests
    except ImportError: requests = None
    old_request = requests.sessions.Session.request if requests else None
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    old_rpc = core.rpc
    urllib.request.urlopen = url_filter(old_url)
    if requests: requests.sessions.Session.request = requests_filter(old_request)
    core.rpc = rpc_filter(old_rpc)
    try:
        from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint21_signed_raw_transaction_simulation_cutover as cp21
        import inspect
        source = inspect.getsource(cp21._signed_simulation_raw)
        if 'simulateTransaction' not in source or 'sigVerify' not in source:
            raise Hold('SIGNED_SIMULATION_CONTRACT_NOT_VERIFIED')
        from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint26_dlmm_output_ata_readiness as cp26
        sys.argv = [old_argv[0], '--seconds', str(seconds)]
        print('[ORACLE522_START] CHECKPOINT26 signer_available=True signing_for_sim_only broadcast=False',flush=True)
        rc = cp26.main()
        if rc is None: rc = 0
        result = {'status':'PASS_CHAIN_RETURNED_UNVERIFIED_NET_PROFIT' if rc == 0 else 'HOLD_CHAIN_NONZERO',
                  'checkpoint26_exit':int(rc),'broadcast':False,'scanner_modified':False,
                  'net_profitability_certified':False,'live_trade_authorized':False}
        record(result)
        print('[ORACLE522_FINAL]',json.dumps(result,sort_keys=True),flush=True)
        return int(rc)
    finally:
        core.rpc = old_rpc
        urllib.request.urlopen = old_url
        if requests: requests.sessions.Session.request = old_request
        sys.argv = old_argv
        if checksum(SCANNER) != before:
            raise Hold('FROZEN_SCANNER_HASH_CHANGED')
def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    for opt in ('install','test','run'):
        mode.add_argument('--'+opt, action='store_true')
    p.add_argument('--seconds',type=int,default=90)
    a = p.parse_args()
    try:
        if a.install:
            install(); return 0
        if a.test:
            tests(); return 0
        return run(a.seconds)
    except Exception as exc:
        reason = str(exc) if isinstance(exc, Hold) else type(exc).__name__
        print('[ORACLE522_HOLD]',reason,flush=True)
        return 2
if __name__ == '__main__':
    raise SystemExit(main())