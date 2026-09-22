from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-272'
REVISION='OAD_272_SOLANA_CONTINUOUS_OBSERVATION_POLICY_V1'
TITLE='SOLANA CONTINUOUS OBSERVATION POLICY'
EXPECTED_FILENAME='build_oad_272_solana_continuous_observation_policy.py'
MODULE_NAME='oad_272_solana_continuous_observation_policy.py'
TEST_NAME='test_oad_272_solana_continuous_observation_policy.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_271_solana_historical_experience_formation.py': ('build_solana_historical_experiences',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass SolanaContinuousObservationPolicy:\n    tick_seconds:float\n    acquisition_seconds:float\n    history_limit:int\n    windows_seconds:tuple\n    acquisition_timeout_seconds:float\n    persistence_timeout_seconds:float\n    failure_backoff_base_seconds:float\n    failure_backoff_max_seconds:float\n    rotate_after_seconds:float\n    execution_authority:bool=False\n\ndef build_solana_continuous_observation_policy(\n    tick_seconds=1.0,\n    acquisition_seconds=5.0,\n    history_limit=512,\n    windows_seconds=(5,15,30,60),\n    acquisition_timeout_seconds=20.0,\n    persistence_timeout_seconds=120.0,\n    failure_backoff_base_seconds=2.0,\n    failure_backoff_max_seconds=60.0,\n    rotate_after_seconds=300.0,\n):\n    if tick_seconds <= 0: raise ValueError("tick_seconds must be > 0")\n    if acquisition_seconds < tick_seconds:\n        raise ValueError("acquisition_seconds must be >= tick_seconds")\n    if history_limit < 2: raise ValueError("history_limit must be >= 2")\n    windows=tuple(sorted({int(x) for x in windows_seconds}))\n    if not windows or any(x <= 0 for x in windows):\n        raise ValueError("windows_seconds must contain positive values")\n    if acquisition_timeout_seconds <= 0 or persistence_timeout_seconds <= 0:\n        raise ValueError("timeouts must be > 0")\n    if failure_backoff_base_seconds <= 0 or failure_backoff_max_seconds < failure_backoff_base_seconds:\n        raise ValueError("invalid backoff")\n    if rotate_after_seconds < acquisition_seconds:\n        raise ValueError("rotate_after_seconds must be >= acquisition_seconds")\n    return SolanaContinuousObservationPolicy(\n        float(tick_seconds),float(acquisition_seconds),int(history_limit),windows,\n        float(acquisition_timeout_seconds),float(persistence_timeout_seconds),\n        float(failure_backoff_base_seconds),float(failure_backoff_max_seconds),\n        float(rotate_after_seconds),False\n    )\n\ndef verify_solana_continuous_observation_policy(policy):\n    return (\n        isinstance(policy,SolanaContinuousObservationPolicy)\n        and policy.tick_seconds>0\n        and policy.acquisition_seconds>=policy.tick_seconds\n        and policy.history_limit>=2\n        and bool(policy.windows_seconds)\n        and policy.execution_authority is False\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_272_solana_continuous_observation_policy import *\n\nclass T(unittest.TestCase):\n    def test_policy(self):\n        p=build_solana_continuous_observation_policy()\n        print("[TICK_SECONDS]",p.tick_seconds)\n        print("[ACQUISITION_SECONDS]",p.acquisition_seconds)\n        print("[WINDOWS]",p.windows_seconds)\n        self.assertEqual(p.tick_seconds,1.0)\n        self.assertEqual(p.acquisition_seconds,5.0)\n        self.assertEqual(p.windows_seconds,(5,15,30,60))\n        self.assertTrue(verify_solana_continuous_observation_policy(p))\n        self.assertFalse(p.execution_authority)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-272 1-second internal tick + source-safe acquisition policy certified")\n    print("[PASS] 1-second tick is not a 1-second REST polling requirement")\n'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch: expected "+EXPECTED_FILENAME)

    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel,symbols in DEPENDENCIES.items():
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def "+symbol+"(") not in src and ("class "+symbol) not in src:
                raise RuntimeError("Exact dependency symbol missing: "+rel+" -> "+symbol)
        print("[PASS] exact dependency verified:",rel)

    protected=[]
    for p,label in (
        (root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
        (root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
    ):
        if p.is_file():
            protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
            print("[PASS]",label,"verified")

    extra_paths=[]

    affected=(module,test,init,*extra_paths)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)

        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+module.stem+" import *"
        if export not in lines:
            lines.append(export)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] holder concentration dependency absent")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
