
"""ORACLE-507 full executor-only installer: Windows-safe SQLite admission."""
from pathlib import Path
from contextlib import closing
import ast
import os
import sqlite3
import tempfile
import time

P = Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAMES = ('oracle_506_targeted_native_hydration.py',
         'oracle_506_execution_engine.py', 'oracle_506_atomic_sim_machine.py')

CAPACITY = '''def scanner_capacity(hb):
    """Use the current scanner's authoritative, same-epoch SQLite heartbeat."""
    import sqlite3
    import time
    from contextlib import closing
    if not isinstance(hb, dict) or type(hb.get('epoch')) is not int:
        raise Hold('SCANNER_HEARTBEAT_EPOCH_INVALID')
    path = (BASE / 'candidate_bus.sqlite3').resolve()
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro',
                                     uri=True, timeout=0.5)) as db:
            row = db.execute('SELECT epoch,admitted,unix_ns FROM heartbeat '
                             'ORDER BY unix_ns DESC LIMIT 1').fetchone()
    except (sqlite3.Error, OSError, ValueError):
        raise Hold('SCANNER_LIVE_SQLITE_HEARTBEAT_UNAVAILABLE') from None
    if row is None:
        raise Hold('SCANNER_LIVE_SQLITE_HEARTBEAT_MISSING')
    epoch, admitted, unix_ns = row
    if type(epoch) is not int or epoch != hb['epoch']:
        raise Hold('SCANNER_LIVE_SQLITE_EPOCH_MISMATCH')
    if type(admitted) is not int or not 0 <= admitted <= 28:
        raise Hold('SCANNER_LIVE_SQLITE_ADMITTED_INVALID')
    if type(unix_ns) is not int:
        raise Hold('SCANNER_LIVE_SQLITE_CLOCK_INVALID')
    age_ns = time.time_ns() - unix_ns
    if not -2_000_000_000 <= age_ns <= 10_000_000_000:
        raise Hold('SCANNER_LIVE_SQLITE_HEARTBEAT_STALE')
    return admitted

'''


def once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'HOLD_SOURCE_DRIFT_{label}_{count}')
    return source.replace(old, new, 1)


def build():
    sources = {}
    for name in NAMES:
        src = P / name
        if not src.is_file():
            raise RuntimeError('HOLD_ORACLE506_SOURCE_MISSING_' + name)
        sources[name] = src.read_text(encoding='utf-8')
    engine = sources[NAMES[1]]
    start, finish = 'def scanner_capacity(hb):\n', '\ndef scanner_identity_inventory('
    if engine.count(start) != 1 or engine.count(finish) != 1:
        raise RuntimeError('HOLD_ADMISSION_FUNCTION_BOUNDARY_CHANGED')
    before, remainder = engine.split(start, 1)
    discarded, after = remainder.split(finish, 1)
    if ('SCANNER_FRESH_ADMITTED_COUNT_MISSING' not in discarded
            or 'snapshot_file(' not in discarded):
        raise RuntimeError('HOLD_506_ADMISSION_CONTRACT_CHANGED')
    engine = before + CAPACITY + 'def scanner_identity_inventory(' + after
    engine = once(engine, "mod('oracle_506_targeted_native_hydration')",
                  "mod('oracle_507_targeted_native_hydration')", 'HYDRATION_MODULE')
    engine = once(engine, 'oracle_506_native_engine.json',
                  'oracle_507_native_engine.json', 'ENGINE_REPORT')
    engine = once(engine, 'oracle_506_transient_inbox.json',
                  'oracle_507_transient_inbox.json', 'ENGINE_INBOX')
    engine = engine.replace('ORACLE506_EXACT_NATIVE_TARGETED_EXECUTOR',
                            'ORACLE507_EXACT_NATIVE_TARGETED_EXECUTOR')
    launcher = sources[NAMES[2]]
    launcher = once(launcher, 'oracle_506_execution_engine',
                    'oracle_507_execution_engine', 'LAUNCH_MODULE')
    launcher = once(launcher, 'oracle_506_atomic_sim_machine.json',
                    'oracle_507_atomic_sim_machine.json', 'LAUNCH_REPORT')
    launcher = once(launcher, 'oracle_506_native_engine.json',
                    'oracle_507_native_engine.json', 'LAUNCH_ENGINE_REPORT')
    launcher = launcher.replace('ORACLE506', 'ORACLE507')
    native = sources[NAMES[0]]
    outputs = {P / 'oracle_507_targeted_native_hydration.py': native,
               P / 'oracle_507_execution_engine.py': engine,
               P / 'oracle_507_atomic_sim_machine.py': launcher}
    for path, source in outputs.items():
        ast.parse(source, filename=str(path))
    required = ('TARGET_WARMED_WAIT_NEW_EVENT',
                'SCANNER_EXACT_TRIPLE_ON_DEMAND_ONLY',
                'TARGET_SAVED_WALLET_SIGNER_MISMATCH',
                'bind_helius_core_rpc(core)')
    if any(term not in native + engine for term in required):
        raise RuntimeError('HOLD_EXECUTION_GUARD_CHANGED')
    functions = [node for node in ast.parse(engine).body
                 if isinstance(node, ast.FunctionDef) and node.name == 'work']
    if len(functions) != 1:
        raise RuntimeError('HOLD_WORK_FUNCTION_MISSING')
    for call in ast.walk(functions[0]):
        if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr == 'prewarm'
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == 'provider'):
            raise RuntimeError('HOLD_BLANKET_PREWARM_IN_WORK')
    return outputs


def offline_test():
    class Hold(Exception):
        pass
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'candidate_bus.sqlite3'
        with closing(sqlite3.connect(path)) as db:
            db.execute('CREATE TABLE heartbeat(epoch INTEGER,admitted INTEGER,unix_ns INTEGER)')
            db.execute('INSERT INTO heartbeat VALUES(7,11,?)', (time.time_ns(),))
            db.commit()
        scope = {'BASE': Path(tmp), 'Hold': Hold}
        exec(CAPACITY, scope)
        capacity = scope['scanner_capacity']
        assert capacity({'epoch': 7}) == 11
        cases = (
            ('UPDATE heartbeat SET admitted=29', (), 'SCANNER_LIVE_SQLITE_ADMITTED_INVALID'),
            ('UPDATE heartbeat SET admitted=11,epoch=8', (), 'SCANNER_LIVE_SQLITE_EPOCH_MISMATCH'),
            ('UPDATE heartbeat SET epoch=7,unix_ns=?',
             (time.time_ns()-20_000_000_000,), 'SCANNER_LIVE_SQLITE_HEARTBEAT_STALE'),
        )
        for query, params, code in cases:
            with closing(sqlite3.connect(path)) as db:
                db.execute(query, params)
                db.commit()
            try:
                capacity({'epoch': 7})
            except Hold as exc:
                assert str(exc) == code, (str(exc), code)
            else:
                raise AssertionError('HOLD_NOT_ENFORCED_' + code)
        # Explicit deletion catches leaked handles on Windows before temp cleanup.
        path.unlink()
    print('[PASS] WINDOWS_SAFE_SQLITE_CLOSED; admission, epoch, staleness guards')


def main():
    offline_test()
    outputs = build()
    staged = []
    try:
        for target, source in outputs.items():
            with tempfile.NamedTemporaryFile('w', encoding='utf-8',
                    dir=P, prefix='oracle507_', suffix='.tmp', delete=False) as f:
                f.write(source)
                staged.append((Path(f.name), target))
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    print('[PASS] ORACLE-507 full executor-only modules installed: 3')
    print('[PRESERVE] scanner frozen; ORACLE-506, signer, fresh candidate gates')
    print('[MODE] offline installation; no RPC, wallet read, signing or broadcast')


if __name__ == '__main__':
    main()
