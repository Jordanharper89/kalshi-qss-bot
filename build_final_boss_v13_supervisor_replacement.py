from __future__ import annotations
"""Complete V13 installer: safe supervisor lifecycle, original single-scanner protected.

Installs only final_boss_v13_supervisor.py, preserves V12 and frozen ORACLE-322.
No new websocket producer, bus writes, funded orders or trading authority.
"""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REL = Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST = ROOT / REL / 'final_boss_v13_supervisor.py'
V12 = ROOT / REL / 'final_boss_v12_replenishment.py'
EXPECTED_V12 = 'f17a4c5903dd22a02b293c802bc0ab3637209bbb70d63381f54cc6a292cda2ec'
SOURCE = r'''from __future__ import annotations
"""Final Boss V13 bounded scanner-epoch supervisor.

Reuses the V12 source-guarded derived ORACLE322 scanner; fixes startup acknowledgement
and durable reporting without altering the scanner, pricing engine or executor.
One scanner and one canonical event producer; never sends a transaction.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'runtime_state/oracle/final_boss_dual'
PKG = 'qseries_v2.oracle_execution.solana_atomic_executor.'
MODULES = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor'
SOURCE = ROOT / 'build_oracle_322_scanner_isolated_discovery.py'
DERIVED = ROOT / 'build_final_boss_v12_scanner_runtime.py'
STATUS = BASE / 'scanner_status.json'
SCAN_LOCK = BASE / 'scanner.lock'
OLD_LOCK = BASE / 'v12_supervisor.lock'
LOCK = BASE / 'v13_supervisor.lock'
REPORT = BASE / 'final_boss_v13_supervisor.json'
V10 = BASE / 'final_boss_v10_admission_stage.json'
CERT = BASE / 'v12_mriya_refresh_certificate.json'
V11 = BASE / 'final_boss_v11_native_bridge.json'
V9 = BASE / 'final_boss_v9_simulation_gate.json'
EXPECTED_V12 = 'f17a4c5903dd22a02b293c802bc0ab3637209bbb70d63381f54cc6a292cda2ec'
GRID = tuple(range(10_000_000, 100_000_001, 5_000_000))

class Hold(RuntimeError):
    pass

def doc(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 900_000:
        return {}
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (ValueError, UnicodeError, OSError):
        return {}

def age(path):
    try:
        return round(max(0.0, time.time() - path.stat().st_mtime), 2)
    except OSError:
        return None

def status_snapshot():
    d = doc(STATUS)
    return {'status': d.get('status'), 'epoch': d.get('epoch'),
            'admitted': d.get('admitted'),
            'candidates_to_executor': d.get('candidates_to_executor'),
            'age_seconds': age(STATUS),
            'mtime_ns': STATUS.stat().st_mtime_ns if STATUS.exists() else 0}

def safe_state():
    s = status_snapshot()
    old = doc(BASE / 'final_boss_v12_replenishment.json')
    v10 = doc(V10)
    v11 = doc(V11)
    v9 = doc(V9)
    cert = doc(CERT)
    return {'scanner': s, 'scanner_lock': SCAN_LOCK.exists(),
            'v12_supervisor_lock': OLD_LOCK.exists(),
            'v13_supervisor_lock': LOCK.exists(),
            'v12_report_exists': (BASE / 'final_boss_v12_replenishment.json').is_file(),
            'v12_report_status': old.get('status'),
            'v12_report_age_seconds': age(BASE / 'final_boss_v12_replenishment.json'),
            'v10_stage_status': v10.get('status'),
            'v10_staged_tokens': len(v10.get('staged_tokens', [])) if isinstance(v10.get('staged_tokens'), list) else 0,
            'v12_refresh_certificate': cert.get('status'),
            'v12_refresh_age_seconds': round(time.time()-cert['at'], 2) if type(cert.get('at')) in (float, int) else None,
            'v11_status': v11.get('status'),
            'v11_matching_events': v11.get('matching_events'),
            'v9_status': v9.get('status'),
            'v9_signed_simulations': v9.get('signed_simulations')}

def running_scanner():
    s = status_snapshot()
    return SCAN_LOCK.exists() or (s['status'] == 'RUNNING'
                and s['age_seconds'] is not None and s['age_seconds'] < 15)

def source_guard():
    from qseries_v2.oracle_execution.solana_atomic_executor import final_boss_v12_replenishment as v12
    source = MODULES / 'final_boss_v12_replenishment.py'
    if not source.is_file() or source.is_symlink():
        raise Hold('V12_MODULE_MISSING')
    actual = hashlib.sha256(source.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    if actual != EXPECTED_V12:
        raise Hold('V12_MODULE_SHA_DRIFT')
    if DERIVED.is_symlink() or not DERIVED.is_file():
        raise Hold('V12_DERIVED_SCANNER_MISSING')
    if not SOURCE.is_file() or SOURCE.is_symlink():
        raise Hold('ORACLE322_ORIGINAL_INSTALLER_MISSING')
    expected, _ = v12.make_builder(SOURCE.read_bytes())
    if DERIVED.read_bytes() != expected:
        raise Hold('DERIVED_SCANNER_SOURCE_DRIFT')
    return v12

def atomic_report(obj):
    BASE.mkdir(parents=True, exist_ok=True)
    data = dict(obj, build='FINAL_BOSS_V13', broadcast=False,
                funded_execution_authority=False,
                live_in_place_rotation=False,
                additional_websockets_from_supervisor=0,
                size_grid_count=len(GRID))
    raw = json.dumps(data, sort_keys=True, indent=2).encode('utf-8')
    with tempfile.NamedTemporaryFile(mode='wb', dir=BASE, suffix='.tmp', delete=False) as f:
        f.write(raw)
        tmp = Path(f.name)
    try:
        os.replace(tmp, REPORT)
    finally:
        tmp.unlink(missing_ok=True)
    print('[FINAL_BOSS_V13_SUPERVISOR]', json.dumps(data, sort_keys=True), flush=True)

def new_child_heartbeat(snapshot, since_ns, change_count, child_alive, lock_exists):
    """No monotonic epoch assumption: require two *new* heartbeats and native admission."""
    if not child_alive or not lock_exists:
        return 0, False
    mt = snapshot.get('mtime_ns', 0)
    is_fresh = snapshot.get('status') == 'RUNNING' and snapshot.get('age_seconds') is not None and snapshot['age_seconds'] <= 12
    if not is_fresh or mt <= since_ns:
        return change_count, False
    change_count += 1
    admitted = snapshot.get('admitted', 0)
    ready = change_count >= 2 and type(admitted) is int and admitted > 0
    return change_count, ready

def await_live_child(proc, before_ns, timeout=90):
    deadline = time.monotonic() + timeout
    last_ns, seen = before_ns, 0
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise Hold('NEW_SCANNER_PROCESS_EXITED_BEFORE_ADMISSION')
        s = status_snapshot()
        if s['mtime_ns'] > last_ns:
            seen, ok = new_child_heartbeat(s, before_ns, seen, True, SCAN_LOCK.exists())
            last_ns = s['mtime_ns']
            if ok:
                return {'acknowledged': True, 'heartbeat_updates': seen,
                        'scanner_epoch': s['epoch'], 'admitted': s['admitted']}
        time.sleep(0.5)
    raise Hold('SCANNER_FRESH_HEARTBEAT_AND_ADMISSION_NOT_CERTIFIED')

def stage_ok():
    c = doc(CERT)
    staged = BASE / 'staged_discovery.json'
    if c.get('status') != 'CERTIFIED' or type(c.get('at')) not in (float, int):
        return False
    if not 0 <= time.time()-c['at'] <= 90 or staged.is_symlink() or not staged.is_file():
        return False
    return hashlib.sha256(staged.read_bytes()).hexdigest() == c.get('stage_sha256')

def scanner_done(scan, timeout=15):
    try:
        scan.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    deadline = time.monotonic()+timeout
    while SCAN_LOCK.exists() and time.monotonic() < deadline:
        time.sleep(.3)
    return not SCAN_LOCK.exists()

def run(epochs, seconds, pairs, observe, signed_sim):
    if not (epochs == 0 or 1 <= epochs <= 1000) or not 150 <= seconds <= 3600 or not 1 <= pairs <= 28:
        raise Hold('INVALID_EPOCH_ARGUMENTS')
    if signed_sim and not observe:
        raise Hold('SIMULATION_REQUIRES_EXECUTOR_OBSERVER')
    if running_scanner() or OLD_LOCK.exists():
        raise Hold('EXISTING_SCANNER_OR_V12_SUPERVISOR_ACTIVE_NO_DUPLICATE')
    v12 = source_guard()
    BASE.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise Hold('V13_SUPERVISOR_LOCK_EXISTS') from None
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    current = 0
    scan = None
    watcher = None
    refresh_thread = None
    refresh = {}
    keep_lock = False
    try:
        while epochs == 0 or current < epochs:
            if running_scanner() or OLD_LOCK.exists():
                raise Hold('SCANNER_OR_OLD_SUPERVISOR_APPEARED_DURING_CUTOVER')
            before = status_snapshot()
            certificate = stage_ok()
            atomic_report({'status': 'LAUNCH_PENDING', 'epoch_iteration':current+1,
                           'previous_scanner_epoch':before['epoch'],
                           'mriya_certificate_available_at_start':certificate,
                           'selected_pair_capacity':pairs, 'observer_requested':observe,
                           'signed_sim_requested':signed_sim})
            scan = subprocess.Popen([sys.executable, str(DERIVED.name), '--launch',
                                     '--seconds', str(seconds), '--pairs', str(pairs)],
                                    cwd=str(ROOT), env=v12.child_env(), stdin=subprocess.DEVNULL)
            atomic_report({'status':'WAITING_FOR_FRESH_HEARTBEATS',
                           'epoch_iteration':current+1, 'scanner_pid':scan.pid,
                           'previous_scanner_epoch':before['epoch'],
                           'mriya_certificate_available_at_start':certificate})
            try:
                evidence = await_live_child(scan, before['mtime_ns'])
            except Hold as error:
                # Never terminate an unacknowledged child or release the lock while it may still own scanner coverage.
                keep_lock = scan.poll() is None
                atomic_report({'status':'HOLD_'+str(error), 'epoch_iteration':current+1,
                               'scanner_pid':scan.pid, 'child_still_running':keep_lock})
                return 2
            current += 1
            atomic_report({'status':'RUNNING_BOUND_EPOCH', 'epoch_iteration':current,
                           'scanner_pid':scan.pid, 'previous_scanner_epoch':before['epoch'],
                           'scanner_epoch':evidence['scanner_epoch'],
                           'admitted':evidence['admitted'],
                           'fresh_heartbeat_updates':evidence['heartbeat_updates'],
                           'mriya_certificate_available_at_start':certificate,
                           'observer_requested':observe, 'signed_sim_requested':signed_sim})
            watcher = None
            if observe:
                argv = [sys.executable, '-m', PKG+'final_boss_v11_native_bridge', '--observe',
                        '--seconds', str(max(10, min(160, seconds-70)))]
                if signed_sim:
                    argv.append('--signed-sim')
                watcher = subprocess.Popen(argv, cwd=str(ROOT),
                                           env=v12.child_env(sign_sim=signed_sim), stdin=subprocess.DEVNULL)
            started = time.monotonic()
            refresh_thread = None
            refresh = {}
            def replenish():
                try:
                    refresh['cert'] = v12.refresh().get('status')
                except Exception as exc:
                    refresh['hold'] = type(exc).__name__.upper()
            while scan.poll() is None:
                if (epochs == 0 or current < epochs) and refresh_thread is None and time.monotonic()-started >= max(5, seconds-80):
                    refresh_thread = threading.Thread(target=replenish, daemon=True)
                    refresh_thread.start()
                time.sleep(.5)
            rc = scan.wait()
            if not scanner_done(scan):
                keep_lock = SCAN_LOCK.exists()
                raise Hold('SCANNER_LOCK_NOT_RELEASED_AFTER_CHILD_EXIT')
            if refresh_thread is not None:
                refresh_thread.join(timeout=30)
                if refresh_thread.is_alive():
                    raise Hold('REFRESH_STILL_IN_PROGRESS_AFTER_SCANNER_EXIT')
            if watcher is not None and watcher.poll() is None:
                try:
                    watcher.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    watcher.terminate()
                    watcher.wait(timeout=10)
            atomic_report({'status':'EPOCH_COMPLETED' if rc == 0 else 'HOLD_SCANNER_NONZERO_EXIT',
                           'epoch_iteration':current, 'scanner_exit_code':rc,
                           'scanner_epoch':status_snapshot()['epoch'],
                           'executor_observer_exit_code': watcher.returncode if watcher else None,
                           'executor_observer_status':doc(V11).get('status'),
                           'next_epoch_mriya_certified':stage_ok(),
                           'refresh_certificate_status':refresh.get('cert'),
                           'refresh_hold_code':refresh.get('hold')})
            if rc:
                return 2
            scan = None
            watcher = None
        atomic_report({'status':'FINISHED', 'epochs_completed':current})
        return 0
    except KeyboardInterrupt:
        keep_lock = scan is not None and scan.poll() is None
        atomic_report({'status':'OPERATOR_INTERRUPT', 'epochs_completed':current,
                       'child_still_running':keep_lock,
                       'scanner_pid':scan.pid if scan else None})
        return 130
    finally:
        if scan is not None and scan.poll() is None:
            keep_lock = True
        if not keep_lock:
            try:
                LOCK.unlink()
            except FileNotFoundError:
                pass

def tests():
    assert len(GRID) == 19 and GRID[0] == 10_000_000 and GRID[-1] == 100_000_000
    base = dict(status='RUNNING', mtime_ns=110, age_seconds=0.5, admitted=9, epoch=1)
    assert new_child_heartbeat(base, 110, 0, True, True) == (0,False)
    assert new_child_heartbeat(base, 100, 0, True, True) == (1,False)
    assert new_child_heartbeat(base, 100, 1, True, True) == (2,True)
    assert new_child_heartbeat(dict(base, admitted=0),100,2,True,True) == (3,False)
    assert new_child_heartbeat(base,100,2,False,True) == (0,False)
    assert new_child_heartbeat(base,100,2,True,False) == (0,False)
    assert new_child_heartbeat(dict(base, status='STOPPED'),100,2,True,True) == (2,False)
    with tempfile.TemporaryDirectory() as folder:
        global REPORT, BASE
        old_report, old_base = REPORT, BASE
        try:
            BASE = Path(folder)
            REPORT = BASE / 'status.json'
            atomic_report({'status':'TEST', 'scanner_pid':123})
            got = doc(REPORT)
            assert got['status'] == 'TEST' and got['broadcast'] is False
            assert got['size_grid_count'] == 19
        finally:
            REPORT, BASE = old_report, old_base
    assert 'sendTransaction' not in run.__code__.co_names
    assert 'sendRawTransaction' not in run.__code__.co_names
    print('[PASS] FINAL_BOSS_V13 fresh double heartbeat, nonzero native admission, no epoch monotonic requirement, durable phase report, locked no-duplicate, no broadcast')

def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--test', action='store_true')
    mode.add_argument('--inspect', action='store_true')
    mode.add_argument('--run', action='store_true')
    p.add_argument('--epochs', type=int, default=2)
    p.add_argument('--epoch-seconds', type=int, default=240)
    p.add_argument('--pairs', type=int, default=28)
    p.add_argument('--observe-executor', action='store_true')
    p.add_argument('--signed-sim', action='store_true')
    a = p.parse_args()
    try:
        if a.test:
            tests()
            return 0
        if a.inspect:
            print('[FINAL_BOSS_V13_INSPECT]',json.dumps(safe_state(), sort_keys=True))
            return 0
        return run(a.epochs, a.epoch_seconds, a.pairs, a.observe_executor, a.signed_sim)
    except Hold as exc:
        print('[FINAL_BOSS_V13_HOLD]',str(exc), flush=True)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
'''

EXPECTED_V13 = '4e8502ec6664b5e97d6d13388ddfa4d886a55159e8fbf4fb205aefc057cf8d91'

def sha(raw):
    return hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()

def install():
    want = SOURCE.encode('utf-8')
    if sha(want) != EXPECTED_V13:
        raise RuntimeError('V13_FULL_SOURCE_HASH_MISMATCH')
    if not V12.is_file() or V12.is_symlink() or sha(V12.read_bytes()) != EXPECTED_V12:
        raise RuntimeError('V12_TRUSTED_SOURCE_SHA_DRIFT')
    if DEST.is_symlink():
        raise RuntimeError('V13_TARGET_IS_SYMLINK')
    if DEST.exists():
        if sha(DEST.read_bytes()) != EXPECTED_V13:
            raise RuntimeError('V13_EXISTING_TARGET_DRIFT')
        print('[PASS] V13_ALREADY_INSTALLED_EXACT')
        return
    DEST.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=DEST.parent,suffix='.tmp',delete=False) as f:
        f.write(want)
        temp=Path(f.name)
    try:
        os.replace(temp,DEST)
    finally:
        temp.unlink(missing_ok=True)
    if sha(DEST.read_bytes()) != EXPECTED_V13:
        raise RuntimeError('V13_READBACK_SHA_MISMATCH')
    print('[INSTALLED] V13_FRESH_HEARTBEAT_SUPERVISOR',DEST.relative_to(ROOT))
    print('[SHA256]',EXPECTED_V13)
    print('[PRESERVED] V12_ORIGINAL, ORACLE322_SCANNER, Q18/Q20/Q25, ORACLE402, CANONICAL_BUS')
    print('[SCOPE] REPORTING_PLUS_BOUNDED_EPOCH_LIFECYCLE_ONLY; NO_BROADCAST')

def test():
    raw=SOURCE.encode('utf-8')
    assert sha(raw)==EXPECTED_V13
    compile(SOURCE,'<complete_v13_supervisor>','exec')
    with tempfile.TemporaryDirectory() as folder:
        temp=Path(folder)/REL/'final_boss_v13_supervisor.py'
        temp.parent.mkdir(parents=True,exist_ok=True)
        temp.write_bytes(raw)
        cp=subprocess.run([sys.executable,str(temp),'--test'],cwd=folder,
                         capture_output=True,text=True,timeout=30)
        if cp.returncode != 0:
            print(cp.stdout,cp.stderr)
            raise RuntimeError('V13_PHYSICAL_TEST_FAILED')
        print(cp.stdout.strip())
    print('[PASS] V13_INSTALLER full source, locked start, double heartbeat, admitted>0, stable-epoch acknowledgement, 19 sizes')

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true')
    g.add_argument('--install',action='store_true')
    a=p.parse_args()
    try:
        if a.test:test()
        else:install()
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
        print('[V13_INSTALLER_HOLD]',type(exc).__name__,str(exc)[:120])
        return 2

if __name__=='__main__':
    raise SystemExit(main())
