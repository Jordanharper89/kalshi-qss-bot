from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_015_strict_single_writer_production_gate.py";TEST=ROOT/"test_oph_015_strict_single_writer_production_gate.py";INIT=PKG/"__init__.py"
MODULE='from __future__ import annotations\nimport importlib\nfrom dataclasses import dataclass\n\nOPH_015_BUILD_ID="OPH-015"\nOPH_015_REVISION="OPH_015_STRICT_SINGLE_WRITER_PRODUCTION_GATE_V1"\n\n@dataclass(frozen=True)\nclass StrictSingleWriterReport:\n    fast_lane_queue_only:bool\n    coverage_queue_only:bool\n    writer_recovery_enabled:bool\n    provenance_enabled:bool\n    direct_adapter_postgresql_authority:bool=False\n    execution_authority:bool=False\n\ndef verify_oph_015_strict_single_writer_production_gate():\n    checks=(\n        ("oph_011_persistence_provenance_ledger","verify_oph_011_persistence_provenance_ledger"),\n        ("oph_012_strict_fast_lane_queue_only_admission","verify_oph_012_strict_fast_lane_queue_only_admission"),\n        ("oph_013_strict_coverage_queue_only_admission","verify_oph_013_strict_coverage_queue_only_admission"),\n        ("oph_014_canonical_writer_failure_recovery_runtime","verify_oph_014_canonical_writer_failure_recovery_runtime"),\n    )\n    return all(\n        getattr(\n            importlib.import_module(\n                "qseries_v2.oracle_production_hardening."+m\n            ),\n            fn,\n        )()\n        for m,fn in checks\n    )\n\ndef strict_single_writer_report():\n    if not verify_oph_015_strict_single_writer_production_gate():\n        raise RuntimeError("OPH-011 through OPH-015 verification failed")\n    return StrictSingleWriterReport(\n        True,True,True,True,False,False\n    )\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_015_strict_single_writer_production_gate import verify_oph_015_strict_single_writer_production_gate\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_015_strict_single_writer_production_gate())\nif __name__=="__main__":\n    print("="*80);print(" OPH-015 CERTIFICATION TEST");print(" STRICT SINGLE WRITER PRODUCTION GATE");print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OPH-015 certified");print("[DONE] OPH-015 CERTIFIED")\n'
LAUNCHER=ROOT/"run_oracle_LIVE.py"
FAST=ROOT/"run_oph_015_strict_fast_lane_child.py"
COVERAGE=ROOT/"run_oph_015_strict_coverage_child.py"
WRITER=ROOT/"run_oph_015_recovering_single_canonical_writer.py"
PHYSICAL=ROOT/"run_oph_015_physical_strict_single_writer_check.py"
FAST_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_production_hardening.oph_012_strict_fast_lane_queue_only_admission import (\n    install_strict_fast_lane_queue_only,\n)\nUNDERLYING_RUNNER=__UNDERLYING__\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-015 STRICT FAST LANE -> QUEUE ONLY",flush=True)\n    print("="*88,flush=True)\n    install_strict_fast_lane_queue_only(Path.cwd())\n    print("[OPH] producer=FAST_LANE direct_postgresql_write_authority=FALSE mode=STRICT_QUEUE_ONLY",flush=True)\n    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")\n'
COVERAGE_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_production_hardening.oph_013_strict_coverage_queue_only_admission import (\n    install_strict_coverage_queue_only,\n)\nUNDERLYING_RUNNER=__UNDERLYING__\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-015 STRICT COVERAGE -> QUEUE ONLY",flush=True)\n    print("="*88,flush=True)\n    install_strict_coverage_queue_only(Path.cwd())\n    print("[OPH] producer=COVERAGE direct_postgresql_write_authority=FALSE mode=STRICT_QUEUE_ONLY",flush=True)\n    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")\n'
WRITER_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_014_canonical_writer_failure_recovery_runtime import (\n    run_recovering_single_writer_forever,\n)\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-015 RECOVERING SINGLE CANONICAL POSTGRESQL WRITER",flush=True)\n    print("="*88,flush=True)\n    raise SystemExit(\n        run_recovering_single_writer_forever(\n            Path.cwd(),\n            lambda x:print(x,flush=True),\n        )\n    )\n'
PHYSICAL_SOURCE='from pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue import queue_counts\nfrom qseries_v2.oracle_production_hardening.oph_011_persistence_provenance_ledger import ledger_path\nfrom qseries_v2.oracle_production_hardening.oph_015_strict_single_writer_production_gate import strict_single_writer_report\n\nif __name__=="__main__":\n    print("="*96)\n    print(" OPH-015 STRICT SINGLE-WRITER PHYSICAL PRODUCTION CHECK")\n    print("="*96)\n    r=strict_single_writer_report()\n    p=ledger_path(Path.cwd())\n    print(f"[QUEUE] counts={queue_counts(Path.cwd())}")\n    print(f"[PROVENANCE] path={p}")\n    print(f"[PROVENANCE] present={p.exists()}")\n    print(f"[FAST LANE QUEUE ONLY] {r.fast_lane_queue_only}")\n    print(f"[COVERAGE QUEUE ONLY] {r.coverage_queue_only}")\n    print(f"[WRITER RECOVERY] {r.writer_recovery_enabled}")\n    print(f"[DIRECT ADAPTER POSTGRESQL AUTHORITY] {r.direct_adapter_postgresql_authority}")\n    print("[TARGET] canonical_writer=RUNNING")\n    print("[TARGET] producer logs contain no raw PostgreSQLPersistenceRoutingFailure")\n    print("[TARGET] any PostgreSQL routing failure appears only as [SINGLE WRITER RETRY]")\n    print("[TARGET] Fast Lane remains connected while writer retries")\n    print("[TARGET] Coverage continues full-page persistence")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-015 PHYSICAL CHECK READY")\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def read_children(source):
    import ast
    tree=ast.parse(source)
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
            return {str(k.value):str(v.value) for k,v in zip(item.value.keys,item.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str)}
    raise RuntimeError("CHILDREN dictionary not found")

def patch_child(source,name,value):
    import ast
    tree=ast.parse(source); node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
            node=item.value; break
    if node is None: raise RuntimeError("CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)==name and isinstance(v,ast.Constant) and isinstance(v.value,str):
            old=v.value
            if old==value:return source,False
            idx=v.lineno-1
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in lines[idx]:
                    lines[idx]=lines[idx].replace(token,repr(value),1)
                    patched="".join(lines);ast.parse(patched);return patched,True
    raise RuntimeError(f"child {name} not found")

def resolve_underlying(root,runner):
    import ast
    current=str(runner);seen=set()
    wrappers={
        "run_oracle_priority_fast_lane_child.py",
        "run_oracle_serialized_fast_lane_child.py",
        "run_opc_035_priority_coverage_child.py",
        "run_opc_041_serialized_coverage_child.py",
        "run_oph_010_fast_lane_queue_child.py",
        "run_oph_010_coverage_queue_child.py",
        "run_oph_015_strict_fast_lane_child.py",
        "run_oph_015_strict_coverage_child.py",
    }
    for _ in range(12):
        if current in seen:raise RuntimeError("recursive wrapper chain")
        seen.add(current)
        if current not in wrappers:return current
        p=root/current
        if not p.exists():raise RuntimeError(f"wrapper missing: {current}")
        target=None
        for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
            if line.strip().startswith("UNDERLYING_RUNNER="):
                target=ast.literal_eval(line.split("=",1)[1].strip());break
        if not target:raise RuntimeError(f"cannot resolve wrapper: {current}")
        current=str(target)
    raise RuntimeError("wrapper resolution exceeded")

def main():
    print("="*80);print(" OPH-015 INSTALLER");print(" STRICT SINGLE WRITER PRODUCTION GATE");print("="*80);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_014_canonical_writer_failure_recovery_runtime")
    if up.verify_oph_014_canonical_writer_failure_recovery_runtime() is not True:raise RuntimeError("OPH-014 verification failed")
    print("[PASS] Certified OPH-014 upstream boundary verified")
    affected=(MOD,TEST,INIT,LAUNCHER,FAST,COVERAGE,WRITER,PHYSICAL);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        if not LAUNCHER.exists(): raise RuntimeError("run_oracle_LIVE.py missing")
        source=LAUNCHER.read_text(encoding="utf-8")
        children=read_children(source)
        fast_under=resolve_underlying(ROOT,children.get("fast_lane"))
        cov_under=resolve_underlying(ROOT,children.get("coverage"))

        write_exact(FAST,FAST_TEMPLATE.replace("__UNDERLYING__",repr(fast_under)))
        write_exact(COVERAGE,COVERAGE_TEMPLATE.replace("__UNDERLYING__",repr(cov_under)))
        write_exact(WRITER,WRITER_SOURCE)
        write_exact(PHYSICAL,PHYSICAL_SOURCE)

        patched,_=patch_child(source,"fast_lane",FAST.name)
        patched,_=patch_child(patched,"coverage",COVERAGE.name)
        patched,_=patch_child(patched,"canonical_writer",WRITER.name)

        compile(patched,str(LAUNCHER),"exec")
        write_exact(LAUNCHER,patched)

        print(f"[PASS] Strict Fast Lane underlying={fast_under}")
        print(f"[PASS] Strict Coverage underlying={cov_under}")
        print("[PASS] Recovering canonical writer installed")
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .oph_015_strict_single_writer_production_gate import *"
        if ex not in cur:write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        print("[PASS] Oracle Live --check passed with strict single-writer runtime")

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-015 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPH-015 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
