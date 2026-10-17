"""ORACLE-092 complete installer: extend existing verified ALT discovery.
Read-only installation. Scanner, signing, broadcast, ALT state unchanged.
"""
import argparse
import ast
import shutil
import tempfile
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_074_native_v0_compiler.py')
SOURCE = '"""ORACLE-092: verified registered ALT discovery and bounded, verified ALT subset search for two-leg unsigned v0.\nNo ALT creation/extension; no signer or broadcaster authority.\n"""\nimport itertools\nimport re\nimport json\nfrom pathlib import Path\nfrom build_oracle_072_route_contract import validate_route, MAX_TX_BYTES\n\nWIRE_LIMIT = min(int(MAX_TX_BYTES), 1232)\n\ndef _redact(value):\n    s = str(value)\n    s = re.sub(r\'(?i)(api-key=)[^&\\s]+\', r\'\\1[REDACTED]\', s)\n    s = re.sub(r\'(?i)(private.?key|secret|authorization)\\s*[=:]\\s*[^\\s,}]+\', r\'\\1=[REDACTED]\', s)\n    return s[:160]\n\ndef _alt_sets(verified):\n    """Try every unique subset of up to four verified tables, including no ALT."""\n    rows = list(verified[:4])\n    yield []\n    for n in range(1, len(rows) + 1):\n        for subset in itertools.combinations(rows, n):\n            yield list(subset)\n\n\nALT_KEYS = frozenset((\'address\', \'alt_address\', \'alt\', \'lookup_table\',\n                      \'lookup_table_address\', \'address_lookup_table\'))\n\ndef _local_alt_candidates(root, token):\n    """Read only bounded ALT manifests. Every address still needs RPC attestation."""\n    base = Path(root)\n    directories = (\n        base / \'runtime_state/qseries/qarb_execution_engineering\',\n        base / \'runtime_state/oracle/oracle_live_execution\',\n    )\n    found = []\n    files_seen = 0\n    def walk(obj, depth=0):\n        if depth > 7:\n            return\n        if isinstance(obj, dict):\n            for k, v in obj.items():\n                low = str(k).lower()\n                if low in ALT_KEYS and isinstance(v, str):\n                    if 32 <= len(v) <= 44 and re.fullmatch(r\'[1-9A-HJ-NP-Za-km-z]+\', v):\n                        found.append(v)\n                elif low in (\'tables\', \'alts\', \'lookup_tables\', \'alt_registry\',\n                             \'shared_alts\', \'shared\', \'tokens\', \'registry\'):\n                    walk(v, depth+1)\n                elif k == token:\n                    walk(v, depth+1)\n        elif isinstance(obj, list):\n            for item in obj[:64]:\n                walk(item, depth+1)\n    for folder in directories:\n        if not folder.is_dir():\n            continue\n        for path in sorted(folder.glob(\'*.json\')):\n            if files_seen >= 40:\n                break\n            if not any(s in path.name.lower() for s in (\'alt\', \'lookup\', \'registry\')):\n                continue\n            try:\n                if path.stat().st_size > 256000:\n                    continue\n                doc = json.loads(path.read_text(encoding=\'utf-8\'))\n            except (OSError, ValueError, UnicodeError):\n                continue\n            files_seen += 1\n            walk(doc)\n    return list(dict.fromkeys(found))[:24]\n\ndef compile_existing_alt(user, route, core, q87, root, extra_alt=None, v51=None):\n    if v51 is None:\n        from qseries_v2.oracle_execution.solana_atomic_executor import (\n            oracle_051_original_scanner_alt_and_size_gate as v51)\n    result = {\'ok\': False, \'reason\': \'HOLD\', \'attempts\': [], \'used_alts\': [],\n              \'min_trade_lamports\': 10_000_000}\n    if not isinstance(route, dict):\n        result[\'reason\'] = \'HOLD_ROUTE_INVALID\'\n        return result\n    start = route.get(\'start_lamports\')\n    if type(start) is not int or start < 10_000_000:\n        result[\'reason\'] = \'HOLD_BELOW_010_SOL_MINIMUM\'\n        return result\n    token = route.get(\'token\')\n    if not isinstance(token, str) or not token:\n        result[\'reason\'] = \'HOLD_TOKEN_MISSING\'\n        return result\n    candidates = [c for c in q87.repaired_candidates(route)\n                  if v51.candidate_is_safe(c)]\n    if not candidates:\n        result[\'reason\'] = \'HOLD_NO_HELPER_COMPLETE_CANDIDATE\'\n        return result\n    choices = list(dict.fromkeys(\n        v51.saved_table_candidates(root, token, extra_alt) +\n        [x for x in route.get(\'base_alts\', []) if isinstance(x, str)] +\n        _local_alt_candidates(root, token)))\n    best = None\n    blockhash = None\n    for cand in candidates:\n        name = str(cand.get(\'name\', \'UNKNOWN\'))\n        ixs = cand[\'instructions\']\n        gate = validate_route(route, core.PUMP, core.DLMM, ixs)\n        if gate != \'ADMITTED\':\n            result[\'attempts\'].append({\'candidate\': name, \'error\': gate})\n            continue\n        verified = []\n        for address in choices[:24]:\n            try:\n                rec, err = v51.verified_table(core, address, user, ixs)\n                if rec:\n                    verified.append(rec)\n                elif err:\n                    result[\'attempts\'].append({\'candidate\': name, \'alt_check\': _redact(err)})\n            except Exception as exc:\n                result[\'attempts\'].append({\'candidate\': name,\n                                           \'alt_check\': type(exc).__name__})\n        verified.sort(key=lambda r: -int(r.get(\'covered_accounts\', 0)))\n        print(\'[ORACLE092_ALT_COVERAGE] candidate=%s addresses=%d verified=%d best_coverage=%d\' %\n              (name, len(choices), len(verified),\n               max((int(r.get(\'covered_accounts\', 0)) for r in verified), default=0)), flush=True)\n        for alts in _alt_sets(verified):\n            try:\n                if blockhash is None:\n                    bh = core.rpc(\'getLatestBlockhash\', [{\'commitment\': \'processed\'}])\n                    blockhash = bh[\'value\'][\'blockhash\']\n                msg, raw = core.compile_v0(user, ixs, alts, blockhash)\n                raw = bytes(raw)\n                size = len(raw)\n                if size > WIRE_LIMIT:\n                    raise RuntimeError(\'ATOMIC_TX_TOO_LARGE:%d\' % size)\n                if size < 66 or raw[0] != 1 or raw[1:65] != bytes(64) or raw[65] != 128:\n                    raise RuntimeError(\'NONCANONICAL_UNSIGNED_V0_PACKET\')\n                result[\'attempts\'].append({\'candidate\': name, \'alt_count\': len(alts),\n                                           \'bytes\': size, \'ok\': True})\n                if best is None or size < best[\'bytes\']:\n                    best = {\'ok\': True, \'reason\': \'LEGAL_UNSIGNED_V0\', \'msg\': msg,\n                            \'raw\': raw, \'bytes\': size, \'candidate\': name,\n                            \'used_alts\': alts, \'token\': token,\n                            \'start_lamports\': start}\n            except Exception as exc:\n                result[\'attempts\'].append({\'candidate\': name, \'alt_count\': len(alts),\n                                           \'error\': type(exc).__name__,\n                                           \'detail\': _redact(exc)})\n    if best is not None:\n        result.update(best)\n        print(\'[ORACLE088_COMPILED] candidate=%s bytes=%d alts=%d\' %\n              (best[\'candidate\'], best[\'bytes\'], len(best[\'used_alts\'])), flush=True)\n        return result\n    result[\'reason\'] = \'HOLD_NO_LEGAL_HELPER_COMPLETE_V0\'\n    for item in result[\'attempts\'][:8]:\n        print(\'[ORACLE088_COMPILE_REJECT]\', item, flush=True)\n    return result\n'


def test():
    ast.parse(SOURCE)
    namespace = {}
    # Verify no RPC is required to discover local manifests.
    import sys
    from types import ModuleType
    fake = ModuleType('build_oracle_072_route_contract')
    fake.validate_route = lambda *_: 'ADMITTED'
    fake.MAX_TX_BYTES = 1232
    previous = sys.modules.get(fake.__name__)
    try:
        sys.modules[fake.__name__] = fake
        exec(compile(SOURCE, '<oracle092>', 'exec'), namespace)
    finally:
        if previous is None:
            sys.modules.pop(fake.__name__, None)
        else:
            sys.modules[fake.__name__] = previous
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        folder = root / 'runtime_state/oracle/oracle_live_execution'
        folder.mkdir(parents=True)
        good = '11111111111111111111111111111112'
        (folder / 'shared_alt_registry.json').write_text(
            '{"shared_alts":[{"lookup_table_address":"'+good+'"}]}', encoding='utf-8')
        assert namespace['_local_alt_candidates'](root, 'TOKEN') == [good]
        assert len(list(namespace['_alt_sets']([{'address': str(x)} for x in range(4)]))) == 16
        assert len(list(namespace['_alt_sets']([]))) == 1
    if TARGET.exists():
        ast.parse(TARGET.read_text(encoding='utf-8'))
    print('[PASS] ORACLE092_ALT_DISCOVERY_AND_SUBSET_TESTS')
    print('[BOUNDARY] NO_RPC_DURING_INSTALL NO_ALT_MUTATION NO_SIGNING NO_BROADCAST NO_SCANNER_EDIT')


def install():
    test()
    if not TARGET.is_file():
        raise RuntimeError('ORACLE092_TARGET_MISSING')
    existing = TARGET.read_text(encoding='utf-8')
    if 'ORACLE-092: verified registered ALT discovery' in existing:
        print('[PASS] ORACLE092_ALREADY_INSTALLED')
        return
    if 'ORACLE-088: bounded, verified ALT subset search' not in existing:
        raise RuntimeError('ORACLE092_REQUIRES_UNMODIFIED_ORACLE088_COMPILER')
    backup = TARGET.with_name(TARGET.stem + '.before_oracle092.py')
    if backup.exists():
        raise RuntimeError('ORACLE092_BACKUP_ALREADY_EXISTS')
    shutil.copy2(TARGET, backup)
    tmp = TARGET.with_suffix('.oracle092.tmp')
    try:
        tmp.write_text(SOURCE, encoding='utf-8')
        ast.parse(tmp.read_text(encoding='utf-8'))
        tmp.replace(TARGET)
    except Exception:
        tmp.unlink(missing_ok=True)
        TARGET.write_text(existing, encoding='utf-8')
        raise
    print('[PASS] ORACLE092_EXISTING_ALT_DISCOVERY_INSTALLED')
    print('[TARGET]', TARGET)
    print('[BACKUP]', backup)
    print('[HOLD] NO_ATOMIC_SIMULATION_CERTIFIED; NO_NEW_ONCHAIN_ALT_CREATED')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    args = ap.parse_args()
    test() if args.test else install()
