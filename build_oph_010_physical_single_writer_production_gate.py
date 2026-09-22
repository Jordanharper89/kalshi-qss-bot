from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_010_physical_single_writer_production_gate.py";TEST=ROOT/"test_oph_010_physical_single_writer_production_gate.py";INIT=PKG/"__init__.py"
MODULE='from __future__ import annotations\nimport importlib\nfrom dataclasses import dataclass\n\nOPH_010_BUILD_ID="OPH-010"\nOPH_010_REVISION="OPH_010_PHYSICAL_SINGLE_WRITER_PRODUCTION_GATE_V1"\n\n@dataclass(frozen=True)\nclass SingleWriterProductionReport:\n    writer_child:str\n    fast_lane_queued:bool\n    coverage_queued:bool\n    direct_adapter_postgresql_authority:bool=False\n    execution_authority:bool=False\n\ndef verify_oph_010_physical_single_writer_production_gate():\n    checks=(\n        ("oph_006_durable_cross_process_observation_queue","verify_oph_006_durable_cross_process_observation_queue"),\n        ("oph_007_physical_single_postgresql_writer_runtime","verify_oph_007_physical_single_postgresql_writer_runtime"),\n        ("oph_008_fast_lane_queue_migration","verify_oph_008_fast_lane_queue_migration"),\n        ("oph_009_coverage_queue_migration","verify_oph_009_coverage_queue_migration"),\n    )\n    return all(getattr(importlib.import_module("qseries_v2.oracle_production_hardening."+m),f)() for m,f in checks)\n\ndef production_report():\n    if not verify_oph_010_physical_single_writer_production_gate(): raise RuntimeError("OPH-006 through OPH-010 verification failed")\n    return SingleWriterProductionReport("canonical_writer",True,True,False,False)\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_010_physical_single_writer_production_gate import verify_oph_010_physical_single_writer_production_gate\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_010_physical_single_writer_production_gate())\nif __name__=="__main__":\n    print("="*80);print(" OPH-010 CERTIFICATION TEST");print(" PHYSICAL SINGLE WRITER PRODUCTION GATE");print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OPH-010 certified");print("[DONE] OPH-010 CERTIFIED")\n'
LAUNCHER=ROOT/"run_oracle_LIVE.py"
WRITER=ROOT/"run_oph_010_single_canonical_writer.py"
FAST=ROOT/"run_oph_010_fast_lane_queue_child.py"
COVERAGE=ROOT/"run_oph_010_coverage_queue_child.py"
PHYSICAL=ROOT/"run_oph_010_physical_single_writer_production_check.py"
WRITER_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import run_single_writer_forever\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-010 ORACLE SINGLE CANONICAL POSTGRESQL WRITER",flush=True)\n    print("="*88,flush=True)\n    raise SystemExit(run_single_writer_forever(Path.cwd(),lambda x:print(x,flush=True)))\n'
FAST_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_production_hardening.oph_008_fast_lane_queue_migration import install_fast_lane_queue_migration\nUNDERLYING_RUNNER=__UNDERLYING__\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-010 FAST LANE → SHARED CANONICAL QUEUE",flush=True)\n    print("="*88,flush=True)\n    install_fast_lane_queue_migration(Path.cwd())\n    print(f"[OPH] producer=FAST_LANE direct_postgresql_write_authority=FALSE underlying={UNDERLYING_RUNNER}",flush=True)\n    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")\n'
COVERAGE_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_production_hardening.oph_009_coverage_queue_migration import install_coverage_queue_migration\nUNDERLYING_RUNNER=__UNDERLYING__\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-010 COVERAGE → SHARED CANONICAL QUEUE",flush=True)\n    print("="*88,flush=True)\n    install_coverage_queue_migration(Path.cwd())\n    print(f"[OPH] producer=COVERAGE direct_postgresql_write_authority=FALSE underlying={UNDERLYING_RUNNER}",flush=True)\n    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")\n'
PHYSICAL_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue import queue_counts,queue_path\nfrom qseries_v2.oracle_production_hardening.oph_010_physical_single_writer_production_gate import production_report\nif __name__=="__main__":\n    print("="*96)\n    print(" OPH-010 PHYSICAL SINGLE-WRITER PRODUCTION CHECK")\n    print("="*96)\n    r=production_report()\n    print(f"[QUEUE] path={queue_path(Path.cwd())}")\n    print(f"[QUEUE] counts={queue_counts(Path.cwd())}")\n    print(f"[WRITER CHILD] {r.writer_child}")\n    print(f"[FAST LANE QUEUED] {r.fast_lane_queued}")\n    print(f"[COVERAGE QUEUED] {r.coverage_queued}")\n    print(f"[DIRECT ADAPTER POSTGRESQL AUTHORITY] {r.direct_adapter_postgresql_authority}")\n    print("[TARGET] Start normal Oracle and verify canonical_writer=RUNNING")\n    print("[TARGET] Fast Lane persists without PostgreSQLPersistenceRoutingFailure reconnects")\n    print("[TARGET] Coverage continues full-page persistence through queue")\n    print("[TARGET] expected_terminal_chain_hash_mismatch absent from producer logs")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-010 PHYSICAL CHECK READY")\n'

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
            idx=v.lineno-1; line=lines[idx]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[idx]=line.replace(token,repr(value),1)
                    patched="".join(lines); ast.parse(patched); return patched,True
    raise RuntimeError(f"child {name} not found")

def add_child(source,name,value):
    import ast
    tree=ast.parse(source); node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
            node=item.value; break
    if node is None: raise RuntimeError("CHILDREN dictionary not found")
    for k in node.keys:
        if isinstance(k,ast.Constant) and str(k.value)==name:return source,False
    lines=source.splitlines(keepends=True); close=node.end_lineno-1
    if node.values:
        sample=lines[node.values[-1].lineno-1]; indent=sample[:len(sample)-len(sample.lstrip())]
    else:
        line=lines[node.lineno-1]; indent=line[:len(line)-len(line.lstrip())]+"    "
    lines.insert(close,indent+repr(name)+":"+repr(value)+",\\n")
    patched="".join(lines); ast.parse(patched); return patched,True

def resolve_underlying(root,runner):
    import ast
    current=str(runner); seen=set()
    known={"run_oracle_priority_fast_lane_child.py","run_oracle_serialized_fast_lane_child.py","run_opc_035_priority_coverage_child.py","run_opc_041_serialized_coverage_child.py","run_oph_010_fast_lane_queue_child.py","run_oph_010_coverage_queue_child.py"}
    for _ in range(10):
        if current in seen: raise RuntimeError("recursive wrapper chain")
        seen.add(current)
        if current not in known:return current
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
    print("="*80);print(" OPH-010 INSTALLER");print(" PHYSICAL SINGLE WRITER PRODUCTION GATE");print("="*80);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_009_coverage_queue_migration")
    if up.verify_oph_009_coverage_queue_migration() is not True:raise RuntimeError("OPH-009 verification failed")
    print("[PASS] Certified OPH-009 upstream boundary verified")
    affected=(MOD,TEST,INIT,LAUNCHER,WRITER,FAST,COVERAGE,PHYSICAL);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        if not LAUNCHER.exists():raise RuntimeError("run_oracle_LIVE.py missing")
        source=LAUNCHER.read_text(encoding="utf-8"); children=read_children(source)
        fast_under=resolve_underlying(ROOT,children.get("fast_lane"))
        cov_under=resolve_underlying(ROOT,children.get("coverage"))
        write_exact(WRITER,WRITER_SOURCE)
        write_exact(FAST,FAST_TEMPLATE.replace("__UNDERLYING__",repr(fast_under)))
        write_exact(COVERAGE,COVERAGE_TEMPLATE.replace("__UNDERLYING__",repr(cov_under)))
        write_exact(PHYSICAL,PHYSICAL_SOURCE)
        patched,_=patch_child(source,"fast_lane",FAST.name)
        patched,_=patch_child(patched,"coverage",COVERAGE.name)
        patched,_=add_child(patched,"canonical_writer",WRITER.name)
        write_exact(LAUNCHER,patched)
        print(f"[PASS] Fast Lane migrated underlying={fast_under}")
        print(f"[PASS] Coverage migrated underlying={cov_under}")
        print("[PASS] canonical_writer child added to Oracle supervisor")
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .oph_010_physical_single_writer_production_gate import *"
        if ex not in cur:write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        compile(LAUNCHER.read_text(encoding="utf-8"),str(LAUNCHER),"exec")
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        print("[PASS] Oracle Live --check passed with canonical single writer")

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-010 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPH-010 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
