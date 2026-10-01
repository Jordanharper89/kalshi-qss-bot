"""Install into the existing Oracle subsystem; stop on physical failure."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys
ROOT=Path(__file__).resolve().parent
FILES={'test_ooi_027b_registered_child_lifecycle_certification.py': "import importlib\nimport tempfile\nfrom pathlib import Path\nfrom unittest.mock import patch\nfrom test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require,E,FIXED\nfrom test_ooi_019_retained_evidence_snapshot import A\nfrom test_ooi_021_existing_oos_observation_cycle import append_candidate\nfrom test_ooi_022_restart_safe_observation_session import main as certify_restart\nfrom test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock\nR=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_026_registered_child_observation')\n\ndef main():\n    certify_restart()\n    with tempfile.TemporaryDirectory() as tmp, fixed_validation_clock(), patch.object(E,'utc_now',return_value=FIXED):\n        fixture(tmp);A.retain_snapshot(snapshot(tmp),tmp);append_candidate(tmp,candidate())\n        runtime=R.RegisteredChildObservation(tmp)\n        root=Path(tmp)\n        paths=[root/E.PREDICTIONS,root/E.RESOLUTIONS]\n        baseline=[p.read_bytes() for p in paths]\n        runtime.prepare('2026-09-17T00:00:20+00:00')\n        status=runtime.complete({'unresolved':1},'2026-09-17T00:00:21+00:00')\n        require(status['observation']['active_owned_count']==1,'existing OOS lost accepted fixture')\n        require(status['observation']['duplicates']==1,'handoff duplicated registered candidate')\n        runtime.prepare('2026-09-17T00:01:11+00:00')\n        expired=runtime.complete({'unresolved':1},'2026-09-17T00:01:12+00:00')\n        require(expired['observation']['active_owned_count']==0,'expired candidate retained')\n        require([p.read_bytes() for p in paths]==baseline,'observer modified source ledgers')\n        require(runtime.round_count==2,'completed round sequence lost')\n    print('[PASS] OOI-027 real session/OOS admission, deduplication, expiry, restart recovery, source immutability')\n    print('[SCOPE] Deterministic fixtures; live admission and 24/7 activation remain unclaimed')\n    print('[PASS] execution_authority=FALSE')\n\nif __name__=='__main__':main()\n"}
PINS={'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_026_registered_child_observation.py': 'c4894df07fd523dc064f974cbb828590e53abd7ddb84ad0e03478fb3d91ffeb3', 'run_slop_buy_pressure_live.py': '70801e3a8ab3ee01a83fbfb16e140fac3cc17b183d9bc93b772ca749f46728dd'}
TEST='test_ooi_027b_registered_child_lifecycle_certification.py'
PREVIOUS='test_ooi_026b_registered_child_observation.py'

def require(ok,message):
    if not ok:raise RuntimeError(message)

def write(path,raw):
    temp=path.with_name(path.name+'.install.tmp')
    require(not temp.exists(),'Existing installation temporary file: '+str(temp))
    try:
        temp.write_bytes(raw);os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()

def clear_cache(path):
    cache=path.parent/'__pycache__'
    if cache.is_dir():
        for item in cache.glob(path.stem+'.*.pyc'):item.unlink()

def main():
    require((ROOT/PREVIOUS).is_file(),'Preceding certified test missing')
    for relative,expected in PINS.items():
        path=ROOT/relative
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,
                'Certified source differs: '+relative)
    original={}
    for relative,source in FILES.items():
        path=ROOT/relative
        require(path.parent.is_dir(),'Existing subsystem missing: '+str(path.parent))
        compile(source,str(path),'exec')
        original[relative]=path.read_bytes() if path.exists() else None
        require(relative in PINS or original[relative] is None or original[relative]==source.encode('utf-8'),
                'Existing target differs: '+relative)
    require(subprocess.run([sys.executable,'-B',str(ROOT/PREVIOUS)],cwd=str(ROOT)).returncode==0,
            'Preceding physical boundary failed; no files changed')
    changed=[]
    try:
        for relative,source in FILES.items():
            path=ROOT/relative
            require((path.read_bytes() if path.exists() else None)==original[relative],'Concurrent source change')
            write(path,source.encode('utf-8'));clear_cache(path);changed.append(relative)
        require(subprocess.run([sys.executable,'-B',str(ROOT/TEST)],cwd=str(ROOT)).returncode==0,
                'Installed deterministic test failed')
    except BaseException:
        for relative in reversed(changed):
            # Retain new tests as failure evidence; restore production changes.
            if relative==TEST:continue
            path=ROOT/relative
            if path.exists() and path.read_bytes()==FILES[relative].encode('utf-8'):
                if original[relative] is None:path.unlink()
                else:write(path,original[relative])
                clear_cache(path)
        print('[ROLLBACK] prior production sources restored; test retained',flush=True)
        raise
    print('[PASS] OOI-027B installed and physically tested; execution_authority=FALSE',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('[FAIL] OOI-027B: '+str(exc),flush=True)
        print('[STOP] Do not run the next installer; return full traceback/output',flush=True)
        raise
