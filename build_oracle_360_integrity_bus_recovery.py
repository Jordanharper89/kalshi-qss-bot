"""ORACLE-360: certified 352 restoration and bounded 351 bus coalescing repair.

No RPC/WS client, key access, scanner modifications, signing or broadcasting.
Fail closed on uncertified originals; never change audits or expected hashes.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
import unittest

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
SOURCE_351 = ROOT / 'oracle_351_fast_bank_parity.py'
SOURCE_352 = ROOT / 'oracle_352_scanner_bank_alignment.py'
INSTALLER_352 = Path('build_oracle_352_scanner_bank_alignment.py')
BRIDGE_359 = Path('build_oracle_359_lock_safe_handoff.py')
SAFETY_MARKER = 'ORACLE360_KEEP_LATEST_STRICT_V1'

REVISION_388_SHA256 = 'b2ecf80539eb6f23e230ddf6d54823799a01b0e2e8895df462f2c48a25039870'
PINNED_388_FILES = {'build_oracle_322_scanner_isolated_discovery.py': '60c9a4d8acc4259a01f37c64332caea6139e49a84a719ada7e7fe4ec17bab57b', 'qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py': 'e579d68ac26210ef98ba015180126782669144e81fc5eb2010f0d9586ced767c', 'build_oracle_368_source_boundary_repair.py': 'f9c75028aca71202cdbd9bc97ffa0629cceeba54f9688ee1b0f0aac6b0c3206d', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_368_source_boundary_repair.py': 'f9c75028aca71202cdbd9bc97ffa0629cceeba54f9688ee1b0f0aac6b0c3206d', 'build_oracle_378_native_profit_path_visibility.py': '28aabad0712212b1576aedbb58c25456fedde854b86603a0041ccc71a6782d5e', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_378_native_reverse_atomic.py': '28aabad0712212b1576aedbb58c25456fedde854b86603a0041ccc71a6782d5e', 'build_oracle_384_exact_pool_free_rpc_repair.py': '93c5073a847180f69a7660de6a6cb53b175785c2122fa93476f01917f18d15d7', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_384_exact_pool_free_rpc_repair.py': '93c5073a847180f69a7660de6a6cb53b175785c2122fa93476f01917f18d15d7', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_376_native_sdk/oracle_378_sdk_reverse_unsigned.mjs': '07219743598d49ddc380ca9014b471a0db83c734d9b1d0a7e0cee0dce93800ca', 'build_oracle_363_scanner_bus_binding_replacement.py': '9ecce2d0f12d300675f42e30111d98cf099e1ec2b2a1d41b56ce207f2a82ec9a', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_363_verified_scanner_bus_binding.py': '9ecce2d0f12d300675f42e30111d98cf099e1ec2b2a1d41b56ce207f2a82ec9a'}
FROZEN_PRICER_HASHES = {'q18': ('qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py', '87a60094706e5f4043a161bd606f68e7fbea076819076dbd3f231db6a058db26'), 'q20': ('qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py', '48e1197ebc329e794f0be7108b53ed40a6a1cae961e2fc02c3b1c44b2afcdc75'), 'q25': ('qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py', '8794a5a072cb29c8817bbf247bd60bb11d6e582b20c35e3e99b63bc4cd01a292')}

REPLACEMENT = '''def keep_latest(rows):
    """ORACLE360_KEEP_LATEST_STRICT_V1: coalesce well-formed live nominations only.

    Never promote telemetry, malformed rows, or records lacking admission fields.
    Downstream oracle352 identity, canary, freshness, and bank gates remain intact.
    """
    from collections.abc import Mapping
    required = ('id','token','pump_pool','meteora_pool','direction',
                'size_lamports','created_ns')
    keyed = {}
    if not isinstance(rows, (list, tuple)):
        return []
    for raw in rows:
        if isinstance(raw, Mapping):
            n = dict(raw)
        elif hasattr(raw, 'keys'):
            try:
                n = {k: raw[k] for k in raw.keys()}
            except (TypeError, KeyError, ValueError, IndexError):
                continue
        else:
            continue
        if any(k not in n for k in required):
            continue
        if not all(isinstance(n[k], str) and n[k] for k in
                   ('token','pump_pool','meteora_pool')):
            continue
        if n['direction'] not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
            continue
        try:
            ident = int(n['id'])
            size = int(n['size_lamports'])
            stamp = int(n['created_ns'])
        except (ValueError, TypeError, OverflowError):
            continue
        if any(isinstance(n[k], (float, bool)) or str(n[k]) != str(v)
               for k,v in (('id',ident),('size_lamports',size),('created_ns',stamp))):
            continue
        if ident <= 0 or stamp <= 0 or not 10000000 <= size <= 100000000:
            continue
        key = (n['token'],n['pump_pool'],n['meteora_pool'],n['direction'],size)
        if key not in keyed or ident > int(keyed[key]['id']):
            keyed[key] = n
    return sorted(keyed.values(), key=lambda n:int(n['id']))
'''


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def run_checked(cmd, label):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if p.returncode:
        # Exit code and known safe failure type only; never print arbitrary subprocess output.
        error = 'INSTALLED_SOURCE_TAMPERED' if 'INSTALLED_SOURCE_TAMPERED' in p.stderr else 'SUBPROCESS_FAILED'
        raise RuntimeError(f'{label}:{error}:exit={p.returncode}')
    return p


def transform(src):
    tree = ast.parse(src)
    defs = [node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name == 'keep_latest']
    if len(defs) != 1 or not isinstance(defs[0],ast.FunctionDef):
        raise RuntimeError('KEEP_LATEST_DEFINITION_NOT_UNIQUE')
    fn = defs[0]
    lines = src.splitlines(keepends=True)
    before = ''.join(lines[:fn.lineno - 1])
    after = ''.join(lines[fn.end_lineno:])
    text = before + REPLACEMENT + ('\n' if not REPLACEMENT.endswith('\n') else '') + after
    compile(text, str(SOURCE_351), 'exec')
    return text


def guard_audit():
    """ORACLE389 migrated certified scanner audit, no legacy-fingerprint bypass.

    Pins exact bytes of the replacement ORACLE388 scanner + native/ingress
    artifacts, validates the immutable Q18/Q20/Q25 audit in the launcher, and
    retains ORACLE351/352 binary/structure checks in audit().
    """
    if not all(p.is_file() for p in (SOURCE_351, SOURCE_352, INSTALLER_352)):
        raise RuntimeError('ORACLE389_ORIGINAL_GUARD_DEPENDENCY_MISSING')
    revision=Path('build_oracle_388_optimal_size_alignment.py')
    if not revision.is_file():raise RuntimeError('ORACLE389_388_CERTIFIER_MISSING')
    raw=revision.read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(raw).hexdigest()!=REVISION_388_SHA256:
        raise RuntimeError('ORACLE389_388_CERTIFIER_CHANGED')
    for relative,expected in sorted(PINNED_388_FILES.items()):
        path=Path(relative)
        if not path.is_file() or hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=expected:
            raise RuntimeError('ORACLE389_CERTIFIED_SOURCE_MISMATCH:'+relative)
    # Exact frozen original prices must match the separately witnessed hashes.
    for name, (rel, expected) in FROZEN_PRICER_HASHES.items():
        path=Path(rel)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('ORACLE389_FROZEN_PRICER_HASH_MISMATCH:'+name)
    # Independently re-run original scanner launcher audit, no spoofing.
    run_checked([sys.executable,'build_oracle_322_scanner_isolated_discovery.py','--audit'],
                'ORACLE389_ORIGINAL_PRICER_FREEZE')
    # The source package is pinned above, and its embedded contract is re-tested.
    run_checked([sys.executable,str(revision),'--audit'], 'ORACLE389_388_SOURCE_CONTRACT')
    print('[ORACLE389_SCANNER_REVISION_AUDIT_PASS] Q18_Q20_Q25_FROZEN '
          '11_CERTIFIED_388_FILES NO_SCANNER_MODIFICATION',flush=True)

def install():
    if not INSTALLER_352.is_file() or not SOURCE_351.is_file() or not SOURCE_352.is_file():
        raise RuntimeError('REQUIRED_ORIGINAL_SOURCE_MISSING_STOP')
    # Source preconditions: original 351 must contain exactly the known function with key fields.
    current = SOURCE_351.read_text(encoding='utf-8')
    if SAFETY_MARKER not in current and not all(s in current for s in
         ('def keep_latest(rows):', "n['size_lamports']", "n['meteora_pool']", "n['id']")):
        raise RuntimeError('ORACLE351_SOURCE_CONTRACT_UNKNOWN_STOP')
    updated = transform(current)
    if SAFETY_MARKER not in updated:
        raise RuntimeError('GUARD_NOT_COMPILED_STOP')
    # ORACLE389: original 352 is left untouched; validate pinned 388 revision.
    guard_audit()
    # Stage 351 replacement without touching frozen scanner or original 352.
    if current != updated:
        backup = SOURCE_351.with_name(SOURCE_351.stem + '.oracle360_pre_' + sha(current)[:16] + '.bak')
        if not backup.exists():
            backup.write_text(current,encoding='utf-8')
        if backup.read_text(encoding='utf-8') != current:
            raise RuntimeError('BACKUP_COLLISION_STOP')
        temp = SOURCE_351.with_name(SOURCE_351.name + '.oracle360.tmp')
        temp.write_text(updated,encoding='utf-8')
        py_compile.compile(str(temp),doraise=True)
        os.replace(temp,SOURCE_351)
    audit()
    print('[ORACLE360_INSTALL_PASS] SOURCE351='+sha(updated)+' ORACLE388_SHA_PINNED SCANNER322_UNTOUCHED',flush=True)


def audit():
    guard_audit()
    s = SOURCE_351.read_text(encoding='utf-8')
    if SAFETY_MARKER not in s or transform(s) != s:
        raise RuntimeError('ORACLE351_GUARD_MISSING_OR_NONCANONICAL')
    py_compile.compile(str(SOURCE_351),doraise=True)
    py_compile.compile(str(SOURCE_352),doraise=True)
    print('[ORACLE360_AUDIT_PASS] ORACLE388_PINNED_REVISION Q18_Q20_Q25_FROZEN 351_BUS_GUARDED NO_SIGN_NO_BROADCAST',flush=True)


def tests():
    original = ('from __future__ import annotations\n'
                'def keep_latest(rows):\n'
                '    keyed={}\n'
                '    for n in rows:\n'
                '        k=(n["token"],n["pump_pool"],n["meteora_pool"],n["direction"],n["size_lamports"])\n'
                '        keyed[k]=n\n'
                '    return list(keyed.values())\n'
                'def sentinel(): return 42\n')
    row = dict(id=7,token='tok',pump_pool='pp',meteora_pool='mm',direction='PUMP_TO_METEORA',size_lamports=10000000,created_ns=124)
    ns={}
    exec(transform(original),ns)
    fn=ns['keep_latest']
    class T(unittest.TestCase):
        def test_good(self): self.assertEqual(fn([row]),[row])
        def test_string_entry(self): self.assertEqual(fn(['bad',row]),[row])
        def test_none(self): self.assertEqual(fn([None,row]),[row])
        def test_missing(self): self.assertEqual(fn([{'id':8},row]),[row])
        def test_wrong_direction(self): self.assertEqual(fn([dict(row,direction='OTHER')]),[])
        def test_below_canary(self): self.assertEqual(fn([dict(row,size_lamports=9999999)]),[])
        def test_upper_bound(self): self.assertEqual(len(fn([dict(row,size_lamports=100000000)])),1)
        def test_above_upper_bound(self): self.assertEqual(fn([dict(row,size_lamports=100000001)]),[])
        def test_duplicate_newer(self): self.assertEqual(fn([dict(row,id=9),row])[0]['id'],9)
        def test_duplicate_older(self): self.assertEqual(fn([row,dict(row,id=3)])[0]['id'],7)
        def test_distinct_size(self): self.assertEqual(len(fn([row,dict(row,id=8,size_lamports=20000000)])),2)
        def test_noncanonical(self): self.assertEqual(fn([dict(row,id=7.0)]),[])
        def test_idempotent(self): self.assertEqual(transform(transform(original)),transform(original))
        def test_preserve_code(self): self.assertEqual(ns['sentinel'](),42)
        def test_dict_batch_reject(self): self.assertEqual(fn({'events':[row]}),[])
        def test_compile(self): compile(transform(original),'fixture','exec')
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not result.wasSuccessful():return 1
    print('[ORACLE360_TEST_PASS]',result.testsRun,flush=True)
    return 0


def main():
    p=argparse.ArgumentParser()
    for name in ('install','test','audit'):p.add_argument('--'+name,action='store_true')
    a=p.parse_args()
    if not (a.install or a.test or a.audit):p.error('SELECT_MODE')
    if a.test and tests():return 1
    if a.install:install()
    if a.audit:audit()
    return 0

if __name__=='__main__':sys.exit(main())
