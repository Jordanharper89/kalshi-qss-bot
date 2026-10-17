
"""ORACLE-506: full executor-only Helius SDK binding and report correction."""
from pathlib import Path
import ast
import os
import tempfile

PKG = Path('qseries_v2/oracle_execution/solana_atomic_executor')
CORE = Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
FILES = ('oracle_505_targeted_native_hydration.py',
         'oracle_505_execution_engine.py', 'oracle_505_atomic_sim_machine.py')

def once(text, old, new, label):
    if text.count(old) != 1:
        raise RuntimeError('HOLD_SOURCE_DRIFT_' + label + '_COUNT_' + str(text.count(old)))
    return text.replace(old, new, 1)

def verify_sdk():
    source = CORE.read_text(encoding='utf-8')
    ast.parse(source, filename=str(CORE))
    if ('DLMM_V14_HELIUS_RPC_REQUIRED' not in source
            or 'def dlmm_arrays(' not in source
            or 'RPC.startswith("https://mainnet.helius-rpc.com/")' not in source):
        raise RuntimeError('HOLD_DLMM_SDK_RPC_CONTRACT_CHANGED')
    print('[SDK_CONTRACT] core.RPC global; Helius mainnet HTTPS endpoint required')

BIND = '''def bind_helius_core_rpc(core, endpoint=None):
    """Bind existing RPC endpoint in executor memory; do not print credentials."""
    import os
    from urllib.parse import urlsplit, parse_qs
    sources = (endpoint,) if endpoint is not None else (
        os.environ.get('SOLANA_RPC_URL'),
        os.environ.get('QSB_SOLANA_RPC_URL'),
        os.environ.get('HELIUS_RPC_URL'),
        getattr(core, 'RPC', None))
    selected = None
    for url in sources:
        if not isinstance(url, str) or not url:
            continue
        try:
            p = urlsplit(url)
            keys = parse_qs(p.query).get('api-key', [])
            if (p.scheme == 'https' and p.hostname == 'mainnet.helius-rpc.com'
                    and p.username is None and p.password is None
                    and p.path in ('', '/') and keys and keys[0]):
                selected = url
                break
        except ValueError:
            continue
    if selected is None:
        raise TargetHold('TARGET_HELIUS_CORE_RPC_NOT_CONFIGURED')
    if not hasattr(core, 'RPC'):
        raise TargetHold('TARGET_HELIUS_CORE_RPC_GLOBAL_MISSING')
    core.RPC = selected
    if core.RPC != selected or not core.RPC.startswith('https://mainnet.helius-rpc.com/'):
        raise TargetHold('TARGET_HELIUS_CORE_RPC_BIND_FAILED')
    return True


'''

def check_no_blanket_prewarm(code):
    """Only inspect executable work() AST; ignore comments and test strings."""
    tree = ast.parse(code)
    funcs = [x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
             and x.name == 'work']
    if len(funcs) != 1:
        raise RuntimeError('HOLD_WORK_FUNCTION_UNAVAILABLE')
    calls = [x for x in ast.walk(funcs[0]) if isinstance(x, ast.Call)]
    if any(isinstance(c.func, ast.Attribute) and c.func.attr == 'prewarm'
           and isinstance(c.func.value, ast.Name) and c.func.value.id == 'provider'
           for c in calls):
        raise RuntimeError('HOLD_REAL_BLANKET_PREWARM_CALL')

def build():
    verify_sdk()
    src = {name: (PKG / name).read_text(encoding='utf-8') for name in FILES}
    h = src[FILES[0]]
    h = once(h, 'def ensure_exact_builder(', BIND + 'def ensure_exact_builder(', 'helper')
    core_import = ('    from qseries_v2.oracle_strategy_intelligence.solana_money.'
                   'native_atomic_money_machine import core\n    token=row.get(\'token\',\'\')')
    h = once(h, core_import, core_import.replace('    token=row.get',
              '    bind_helius_core_rpc(core)\n    token=row.get'), 'bind_before_native_warm')
    e = src[FILES[1]]
    e = once(e, "mod('oracle_505_targeted_native_hydration')",
             "mod('oracle_506_targeted_native_hydration')", 'engine_dependency')
    e = once(e, 'oracle_505_native_engine.json',
             'oracle_506_native_engine.json', 'engine_report')
    e = once(e, 'oracle_505_transient_inbox.json',
             'oracle_506_transient_inbox.json', 'engine_inbox')
    e = e.replace('ORACLE505_EXACT_NATIVE_TARGETED_EXECUTOR',
                  'ORACLE506_EXACT_NATIVE_TARGETED_EXECUTOR')
    a = src[FILES[2]]
    a = once(a, 'oracle_505_execution_engine',
             'oracle_506_execution_engine', 'launcher_dependency')
    a = once(a, 'oracle_505_atomic_sim_machine.json',
             'oracle_506_atomic_sim_machine.json', 'launcher_report')
    if 'oracle_504_native_engine.json' not in a:
        raise RuntimeError('HOLD_UNEXPECTED_505_FINAL_REPORT_SOURCE')
    a = a.replace('oracle_504_native_engine.json', 'oracle_506_native_engine.json')
    a = a.replace('oracle_505_native_engine.json', 'oracle_506_native_engine.json')
    a = a.replace('ORACLE505', 'ORACLE506')
    if ('oracle_504_native_engine.json' in a or 'oracle_505_native_engine.json' in a
            or 'oracle_504_execution_engine' in a):
        raise RuntimeError('HOLD_STALE_LAUNCHER_DEPENDENCY')
    output = {PKG/'oracle_506_targeted_native_hydration.py': h,
              PKG/'oracle_506_execution_engine.py': e,
              PKG/'oracle_506_atomic_sim_machine.py': a}
    for path, source in output.items():
        ast.parse(source, filename=str(path))
    if any(x not in h+e for x in ('TARGET_SAVED_WALLET_SIGNER_MISMATCH',
            'TARGET_WARMED_WAIT_NEW_EVENT', 'SCANNER_EXACT_TRIPLE_ON_DEMAND_ONLY')):
        raise RuntimeError('HOLD_PROTECTION_CONTRACT_NOT_PRESERVED')
    check_no_blanket_prewarm(e)
    if 'broadcast' not in a:
        raise RuntimeError('HOLD_EXECUTION_BOUNDARY_CHANGED')
    return output

def main():
    check_no_blanket_prewarm('def work():\n    pass\n'
                             'def tests():\n    assert "provider.prewarm()" not in "work"\n')
    output = build()
    staged = []
    try:
        for path, source in output.items():
            with tempfile.NamedTemporaryFile('w', encoding='utf-8',
                    suffix='.tmp', prefix='oracle506_', dir=PKG, delete=False) as f:
                f.write(source)
                staged.append((Path(f.name), path))
        for temporary, dest in staged:
            os.replace(temporary, dest)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    print('[PASS] ORACLE-506 executor-only modules installed:', len(output))
    print('[PASS] real-call AST guard ignores offline test strings')
    print('[PRESERVE] scanner, ORACLE-344 bus, ORACLE-505, saved wallet')
    print('[MODE] installation only; NO RPC, NO SIGNING, NO BROADCAST')

if __name__ == '__main__':
    main()
