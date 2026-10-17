from __future__ import annotations
"""Final Boss V14: complete guarded replacement of core.py DLMM bin-array RPC path.

The local repository copy is the source of truth: generate and atomically install a
complete replacement core.py after AST/source contract validation and exact backup.
No parallel scanner, socket, signing, order, or account mutation is introduced.
"""
import argparse
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
REL = Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
TARGET = ROOT / REL
BACKUPS = ROOT / 'runtime_state/oracle/final_boss_dual'
SCANNER_LOCK = BACKUPS / 'scanner.lock'
SCAN_STATUS = BACKUPS / 'scanner_status.json'
V12_LOCK = BACKUPS / 'v12_supervisor.lock'
V13_LOCK = BACKUPS / 'v13_supervisor.lock'
GITHUB_CORE_BLOB = '614cd4962f608ec7fab5efded76d8262bd2fdfbf'

# Helius getProgramAccountsV2 config/result use camelCase in JSON-RPC.
# Each account must carry DLMM bin-array pool identity at offset 24.
NEW_FUNC = '''def dlmm_arrays(pool):
    """Hydrate every on-chain DLMM bin array with Helius cursor pagination.

    Returns exactly the legacy list[(signed_bin_index,pubkey,raw)] sorted by index.
    Never use a partial page set, unbounded scan, cached stale bin, or fallback to
    getProgramAccounts. Original native quote/build methods remain unchanged.
    """
    import time as _v14_time
    if not isinstance(pool, str) or not 32 <= len(pool) <= 44:
        raise RuntimeError("DLMM_V14_INVALID_POOL")
    expected_pool = b58d(pool)
    if len(expected_pool) != 32:
        raise RuntimeError("DLMM_V14_INVALID_POOL_BYTES")
    if not isinstance(RPC, str) or not RPC.startswith("https://mainnet.helius-rpc.com/"):
        raise RuntimeError("DLMM_V14_HELIUS_RPC_REQUIRED")
    next_key = None
    visited_keys = set()
    by_pubkey = {}
    maximum_pages = 12
    for page in range(maximum_pages):
        opts = {"encoding": "base64", "commitment": "processed",
                "filters": [{"memcmp": {"offset": 24, "bytes": pool}}],
                "limit": 128}
        if next_key is not None:
            opts["paginationKey"] = next_key
        payload = None
        for attempt in range(3):
            try:
                payload = rpc("getProgramAccountsV2", [DLMM, opts])
                break
            except RuntimeError as exc:
                message = str(exc)
                retry = any(x in message.lower() for x in
                            ("overload", "deprioritized", "429", "too many requests", "-32603"))
                if not retry or attempt == 2:
                    raise RuntimeError("DLMM_V14_HELIUS_PAGE_RPC_REJECTED") from None
                _v14_time.sleep(0.25 * (2 ** attempt))
        if not isinstance(payload, dict) or not isinstance(payload.get("accounts"), list):
            raise RuntimeError("DLMM_V14_BAD_PAGE_ENVELOPE")
        rows = payload["accounts"]
        if len(rows) > 128:
            raise RuntimeError("DLMM_V14_OVERSIZED_PAGE")
        for entry in rows:
            if not isinstance(entry, dict) or not isinstance(entry.get("pubkey"), str):
                raise RuntimeError("DLMM_V14_BAD_ACCOUNT_ROW")
            info = entry.get("account")
            if not isinstance(info, dict):
                raise RuntimeError("DLMM_V14_BAD_ACCOUNT_DATA")
            if info.get("owner") not in (None, DLMM):
                raise RuntimeError("DLMM_V14_BIN_OWNER_MISMATCH")
            data = info.get("data")
            if not isinstance(data, list) or len(data) < 2 or data[1] != "base64" or not isinstance(data[0], str):
                raise RuntimeError("DLMM_V14_BIN_ENCODING")
            try:
                raw = base64.b64decode(data[0], validate=True)
            except (ValueError, base64.binascii.Error):
                raise RuntimeError("DLMM_V14_INVALID_BASE64") from None
            if len(raw) < 56 or raw[24:56] != expected_pool:
                raise RuntimeError("DLMM_V14_BIN_POOL_IDENTITY_MISMATCH")
            key = entry["pubkey"]
            if key in by_pubkey and by_pubkey[key] != raw:
                raise RuntimeError("DLMM_V14_CONFLICTING_DUPLICATE_ACCOUNT")
            by_pubkey[key] = raw
            if len(by_pubkey) > 1536:
                raise RuntimeError("DLMM_V14_MAX_ARRAYS_EXCEEDED")
        if "paginationKey" in payload:
            cursor = payload["paginationKey"]
        elif "pagination_key" in payload:
            cursor = payload["pagination_key"]
        else:
            raise RuntimeError("DLMM_V14_MISSING_PAGINATION_KEY")
        if cursor is None:
            out = [(struct.unpack_from("<q", raw, 8)[0], key, raw)
                   for key, raw in by_pubkey.items()]
            out.sort(key=lambda x: (x[0], x[1]))
            if not out:
                raise RuntimeError("NO_DLMM_BIN_ARRAYS")
            return out
        if not isinstance(cursor, str) or not cursor or len(cursor) > 2048 or cursor in visited_keys:
            raise RuntimeError("DLMM_V14_PAGINATION_CURSOR_INVALID_OR_REPEATED")
        visited_keys.add(cursor)
        next_key = cursor
    raise RuntimeError("DLMM_V14_PAGINATION_PAGE_CAP_INCOMPLETE")
'''

class InstallerHold(RuntimeError):
    pass

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def git_blob(raw):
    normalized = raw.replace(b'\r\n', b'\n')
    return hashlib.sha1(('blob %s\0' % len(normalized)).encode() + normalized).hexdigest()

def read_legacy(src):
    tree = ast.parse(src)
    found = [f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == 'dlmm_arrays']
    if len(found) != 1:
        raise InstallerHold('DLMM_FUNCTION_NOT_UNIQUE')
    f = found[0]
    segment = ast.get_source_segment(src, f) or ''
    required = ['getProgramAccounts', 'memcmp', 'offset', 'DLMM', 'base64', 'struct.unpack_from', 'return out']
    if any(x not in segment for x in required):
        raise InstallerHold('LOCAL_CORE_DLMM_LAYOUT_UNRECOGNIZED')
    if 'getProgramAccountsV2' in segment:
        raise InstallerHold('LOCAL_CORE_ALREADY_USING_PAGINATED_DISCOVERY')
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    if not {'rpc', 'account', 'dlmm_quote', 'discover_dlmm', 'b58d'}.issubset(names):
        # b58d could be imported rather than a local function, if so inspect separately
        if not {'rpc', 'account', 'dlmm_quote', 'discover_dlmm'}.issubset(names) or 'b58d' not in src:
            raise InstallerHold('LOCAL_CORE_API_CONTRACT_CHANGED')
    return f

def build_complete(raw):
    try:
        src = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise InstallerHold('CORE_ENCODING_NOT_UTF8') from None
    try:
        f = read_legacy(src)
    except (SyntaxError, ValueError):
        raise InstallerHold('LOCAL_CORE_NOT_VALID_PYTHON') from None
    if src.count('def dlmm_arrays(') != 1:
        raise InstallerHold('DLMM_TEXT_DEFINITION_NOT_UNIQUE')
    lines = src.splitlines(keepends=True)
    upgraded = ''.join(lines[:f.lineno - 1]) + NEW_FUNC + '\n' + ''.join(lines[f.end_lineno:])
    orig_ast = ast.parse(src)
    new_ast = ast.parse(upgraded)
    def strip_dlmm(tree):
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'dlmm_arrays':
                node.body = [ast.Pass()]
        return ast.dump(tree, include_attributes=False)
    if strip_dlmm(orig_ast) != strip_dlmm(new_ast):
        raise InstallerHold('CORE_UNRELATED_SOURCE_CHANGED')
    compile(upgraded, str(TARGET), 'exec')
    return upgraded.encode('utf-8')

def live_lock_held():
    # Never replace a module while the scanner/supervisor may import it mid-epoch.
    return any(p.exists() for p in (SCANNER_LOCK, V12_LOCK, V13_LOCK))

def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, suffix='.tmp', delete=False) as fp:
        fp.write(data)
        tmp = Path(fp.name)
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)

def install():
    if live_lock_held():
        raise InstallerHold('SCANNER_OR_SUPERVISOR_LOCK_PRESENT_NO_INSTALL')
    if not TARGET.is_file() or TARGET.is_symlink():
        raise InstallerHold('CORE_FILE_MISSING_OR_LINK')
    old = TARGET.read_bytes()
    try:
        upgraded = build_complete(old)
    except InstallerHold as exc:
        # Idempotency: after a successful install the new function is exactly V14.
        source = old.decode('utf-8-sig')
        f = next((n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'dlmm_arrays'), None)
        if f and (ast.get_source_segment(source, f) or '').strip() == NEW_FUNC.strip():
            print('[PASS] V14_ALREADY_INSTALLED_SHA256', digest(old))
            return
        raise exc
    BACKUPS.mkdir(parents=True, exist_ok=True)
    backup = BACKUPS / ('native_core_pre_v14_' + digest(old)[:16] + '.bak')
    if backup.exists() and backup.read_bytes() != old:
        raise InstallerHold('BACKUP_COLLISION')
    if not backup.exists():
        write_atomic(backup, old)
    if TARGET.read_bytes() != old:
        raise InstallerHold('CONCURRENT_CORE_SOURCE_CHANGE_NO_INSTALL')
    write_atomic(TARGET, upgraded)
    if TARGET.read_bytes() != upgraded:
        raise InstallerHold('CORE_READBACK_MISMATCH')
    print('[PASS] V14_FULL_CORE_REPLACEMENT')
    print('[BACKUP]', backup.relative_to(ROOT))
    print('[GITHUB_SOURCE_BLOB_REFERENCE]', GITHUB_CORE_BLOB)
    print('[LOCAL_PRIOR_GIT_BLOB]', git_blob(old))
    print('[SHA256]', digest(upgraded))
    print('[PRESERVED] scanner ownership; Q18/Q20/Q25; V13; ORACLE402; exact quote; no broadcast')

class Tests(unittest.TestCase):
    def function(self, reply):
        namespace = {'rpc': reply, 'b58d': lambda x: b'P'*32,
                     'DLMM': 'TEST_DLMM_PROGRAM', 'RPC': 'https://mainnet.helius-rpc.com/?api-key=TEST',
                     'struct': __import__('struct'), 'base64': base64}
        exec(compile(NEW_FUNC, '<v14_func>', 'exec'), namespace)
        return namespace['dlmm_arrays']
    def row(self, index=1, pool=b'P'*32, key='X'*44):
        import struct
        raw = b'\0'*8 + struct.pack('<q', index) + b'\0'*8 + pool + b'\0'*16
        return {'pubkey': key, 'account': {'owner': 'TEST_DLMM_PROGRAM', 'data': [base64.b64encode(raw).decode(), 'base64']}}
    def test_two_pages_only_v2_and_inherited_contract(self):
        requests=[]
        def fake(method, args):
            requests.append((method,args))
            if len(requests)==1:return {'accounts':[self.row(2,key='B'*44)], 'paginationKey':'cursor-a'}
            return {'accounts':[self.row(1,key='A'*44)],'paginationKey':None}
        result=self.function(fake)('A'*44)
        self.assertEqual([r[0] for r in result],[1,2])
        self.assertEqual([x[0] for x in requests],['getProgramAccountsV2']*2)
        self.assertEqual(requests[1][1][1]['paginationKey'],'cursor-a')
        self.assertEqual(requests[0][1][1]['filters'][0]['memcmp']['offset'],24)
    def test_wrong_pool_rejected(self):
        fn=self.function(lambda m,a:{'accounts':[self.row(pool=b'Z'*32)],'paginationKey':None})
        with self.assertRaisesRegex(RuntimeError,'IDENTITY_MISMATCH'):fn('A'*44)
    def test_cursor_loop_rejected(self):
        fn=self.function(lambda m,a:{'accounts':[self.row()], 'paginationKey':'same'})
        with self.assertRaisesRegex(RuntimeError,'CURSOR_INVALID_OR_REPEATED'):fn('A'*44)
    def test_partial_payload_rejected(self):
        fn=self.function(lambda m,a:{'accounts':[self.row()]})
        with self.assertRaisesRegex(RuntimeError,'MISSING_PAGINATION_KEY'):fn('A'*44)
    def test_empty_complete_result_rejected(self):
        fn=self.function(lambda m,a:{'accounts':[], 'paginationKey':None})
        with self.assertRaisesRegex(RuntimeError,'NO_DLMM_BIN_ARRAYS'):fn('A'*44)
    def test_bounded_overload_failure(self):
        calls=[]
        def fail(m,a):
            calls.append(1)
            raise RuntimeError('RPC -32603 account index service overloaded')
        fn=self.function(fail)
        with patch('time.sleep',lambda x:None):
            with self.assertRaisesRegex(RuntimeError,'PAGE_RPC_REJECTED'):fn('A'*44)
        self.assertEqual(len(calls),3)
    def test_conflicting_duplicate_rejected(self):
        def fake(m,args):
            if 'paginationKey' not in args[1]:return {'accounts':[self.row(1,key='B'*44)],'paginationKey':'c'}
            return {'accounts':[self.row(2,key='B'*44)],'paginationKey':None}
        with self.assertRaisesRegex(RuntimeError,'CONFLICTING_DUPLICATE'):self.function(fake)('A'*44)
    def test_full_source_ast_unrelated_preserved(self):
        fixture='''import base64,struct\nDLMM="p"\nRPC="x"\ndef b58d(x):return b"P"*32\ndef rpc(m,p):pass\ndef account(x):pass\ndef discover_dlmm(x):pass\ndef dlmm_arrays(pool):\n    rows=rpc("getProgramAccounts",[DLMM,{"filters":[{"memcmp":{"offset":24,"bytes":pool}}]}])\n    out=[]\n    for x in rows:\n        d=base64.b64decode(x["account"]["data"][0]);out.append((struct.unpack_from("<q",d,8)[0],x["pubkey"],d))\n    return out\ndef dlmm_quote(x):return "preserved"\n'''
        updated=build_complete(fixture.encode()).decode()
        self.assertIn('def dlmm_quote(x):return "preserved"',updated)
        self.assertNotIn('getProgramAccounts",',updated)
        self.assertIn('getProgramAccountsV2',updated)

def run_tests():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise InstallerHold('V14_DETERMINISTIC_TEST_FAILURE')
    print('[PASS] V14 pagination, pool binding, fail-closed incomplete pages, atomic full replacement')

def audit():
    if not TARGET.is_file():raise InstallerHold('CORE_FILE_MISSING')
    content=TARGET.read_bytes()
    source=content.decode('utf-8-sig')
    fn=next((n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='dlmm_arrays'),None)
    segment=ast.get_source_segment(source,fn) if fn else None
    print('[V14_AUDIT]',json.dumps({'core_sha256':digest(content),
        'github_reference_blob':GITHUB_CORE_BLOB,'local_git_blob':git_blob(content),
        'v14_installed':bool(segment and segment.strip()==NEW_FUNC.strip()),
        'scanner_or_supervisor_lock':live_lock_held(), 'broadcast':False},sort_keys=True))

def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--test',action='store_true')
    group.add_argument('--install',action='store_true')
    group.add_argument('--audit',action='store_true')
    opts=ap.parse_args()
    try:
        if opts.test:run_tests()
        elif opts.install:install()
        else:audit()
        return 0
    except (OSError,ValueError,InstallerHold,SyntaxError) as exc:
        print('[V14_HOLD]',str(exc)[:200])
        return 2

if __name__=='__main__':raise SystemExit(main())
