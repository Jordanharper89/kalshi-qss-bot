from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_035_priority_persistence_activation_gate.py"
TEST=ROOT/"test_opc_035_priority_persistence_activation_gate.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nimport importlib\nfrom dataclasses import dataclass\n\nOPC_035_BUILD_ID="OPC-035"\nOPC_035_REVISION="OPC_035_PRIORITY_PERSISTENCE_ACTIVATION_GATE_V1"\n\n@dataclass(frozen=True)\nclass PriorityPersistenceActivation:\n    fast_lane_wrapped:bool\n    coverage_wrapped:bool\n    frozen_oad_modified:bool=False\n    frozen_ola_modified:bool=False\n    execution_authority:bool=False\n\ndef verify_opc_035_priority_persistence_activation_gate():\n    checks=(\n        ("opc_031_persistence_priority_contract","verify_opc_031_persistence_priority_contract"),\n        ("opc_032_cross_process_persistence_arbiter","verify_opc_032_cross_process_persistence_arbiter"),\n        ("opc_033_priority_router_patch","verify_opc_033_priority_router_patch"),\n        ("opc_034_coverage_microbatch_yield_policy","verify_opc_034_coverage_microbatch_yield_policy"),\n    )\n    return all(\n        getattr(\n            importlib.import_module(\n                "qseries_v2.oracle_pre_settlement_coverage."+mod\n            ),\n            fn,\n        )()\n        for mod,fn in checks\n    )\n\ndef activation_report():\n    if not verify_opc_035_priority_persistence_activation_gate():\n        raise RuntimeError("OPC-031 through OPC-035 verification failed")\n    return PriorityPersistenceActivation(True,True,False,False,False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_035_priority_persistence_activation_gate import verify_opc_035_priority_persistence_activation_gate\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_035_priority_persistence_activation_gate())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-035 CERTIFICATION TEST")\n    print(" PRIORITY PERSISTENCE ACTIVATION GATE")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-035 certified")\n    print("[DONE] OPC-035 CERTIFIED")\n'
LAUNCHER=ROOT/"run_oracle_LIVE.py"
FAST_WRAPPER=ROOT/"run_oracle_priority_fast_lane_child.py"
COVERAGE_WRAPPER=ROOT/"run_opc_035_priority_coverage_child.py"
FAST_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_033_priority_router_patch import install_priority_router_patch\n\nUNDERLYING_RUNNER=__UNDERLYING__\n\nif __name__=="__main__":\n    print("="*80,flush=True)\n    print(" ORACLE FAST-LANE PRIORITY PERSISTENCE WRAPPER",flush=True)\n    print("="*80,flush=True)\n    install_priority_router_patch("fast_lane",Path.cwd())\n    print(f"[PRIORITY] FAST_LANE writer arbitration active underlying={UNDERLYING_RUNNER}",flush=True)\n    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")\n'
COVERAGE_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_033_priority_router_patch import install_priority_router_patch\n\nUNDERLYING_RUNNER=__UNDERLYING__\n\nif __name__=="__main__":\n    print("="*80,flush=True)\n    print(" ORACLE COVERAGE YIELDING PERSISTENCE WRAPPER",flush=True)\n    print("="*80,flush=True)\n    install_priority_router_patch("coverage",Path.cwd())\n    print(f"[PRIORITY] COVERAGE writer arbitration active microbatch=25 underlying={UNDERLYING_RUNNER}",flush=True)\n    runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name="__main__")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def read_children(source):
    import ast
    tree=ast.parse(source)
    node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                node=item.value
                break
    if node is None:
        raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")
    result={}
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and isinstance(v,ast.Constant):
            result[str(k.value)]=str(v.value)
    return result

def patch_child_value(source,child_name,new_value):
    import ast
    tree=ast.parse(source)
    node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                node=item.value
                break
    if node is None:
        raise RuntimeError("CHILDREN dictionary not found")

    lines=source.splitlines(keepends=True)

    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)==str(child_name):
            if not isinstance(v,ast.Constant) or not isinstance(v.value,str):
                raise RuntimeError(f"{child_name} runner is not a literal string")
            old=v.value
            if old==new_value:
                return source,False
            idx=v.lineno-1
            line=lines[idx]
            candidates=(repr(old),'"'+old+'"',"'"+old+"'")
            replaced=False
            for token in candidates:
                if token in line:
                    line=line.replace(token,repr(new_value),1)
                    replaced=True
                    break
            if not replaced:
                raise RuntimeError(f"unable to patch {child_name} runner line")
            lines[idx]=line
            patched="".join(lines)
            ast.parse(patched)
            return patched,True

    raise RuntimeError(f"{child_name} child entry not found")

def main():
    print("="*80)
    print(" OPC-035 INSTALLER")
    print(" PRIORITY PERSISTENCE ACTIVATION GATE")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_034_coverage_microbatch_yield_policy")
    if up.verify_opc_034_coverage_microbatch_yield_policy() is not True:
        raise RuntimeError("Certified OPC-034 verification failed")
    print("[PASS] Certified OPC-034 upstream boundary verified")

    affected=(MOD,TEST,INIT,LAUNCHER,FAST_WRAPPER,COVERAGE_WRAPPER)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        if not LAUNCHER.exists():
            raise RuntimeError("run_oracle_LIVE.py missing")

        original=LAUNCHER.read_text(encoding="utf-8")
        children=read_children(original)

        fast_underlying=children.get("fast_lane")
        coverage_underlying=children.get("coverage")

        if not fast_underlying or not coverage_underlying:
            raise RuntimeError("fast_lane/coverage child entries missing")

        if fast_underlying=="run_oracle_priority_fast_lane_child.py":
            raise RuntimeError("fast_lane already points to priority wrapper; refusing recursive wrapper")
        if coverage_underlying=="run_opc_035_priority_coverage_child.py":
            raise RuntimeError("coverage already points to priority wrapper; refusing recursive wrapper")

        fast_source=FAST_TEMPLATE.replace("__UNDERLYING__",repr(fast_underlying))
        coverage_source=COVERAGE_TEMPLATE.replace("__UNDERLYING__",repr(coverage_underlying))

        write_exact(FAST_WRAPPER,fast_source)
        write_exact(COVERAGE_WRAPPER,coverage_source)

        patched,_=patch_child_value(
            original,
            "fast_lane",
            "run_oracle_priority_fast_lane_child.py",
        )
        patched,_=patch_child_value(
            patched,
            "coverage",
            "run_opc_035_priority_coverage_child.py",
        )
        write_exact(LAUNCHER,patched)

        print(f"[PASS] Fast lane priority wrapper underlying={fast_underlying}")
        print(f"[PASS] Coverage yielding wrapper underlying={coverage_underlying}")
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_035_priority_persistence_activation_gate import *"
        if export not in current:
            write_exact(INIT,current.rstrip()+"\n"+export+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )
        compile(FAST_WRAPPER.read_text(encoding="utf-8"),str(FAST_WRAPPER),"exec")
        compile(COVERAGE_WRAPPER.read_text(encoding="utf-8"),str(COVERAGE_WRAPPER),"exec")
        compile(LAUNCHER.read_text(encoding="utf-8"),str(LAUNCHER),"exec")
        subprocess.run(
            [sys.executable,str(LAUNCHER),"--check"],
            cwd=str(ROOT),
            check=True,
        )
        print("[PASS] Oracle Live --check passed with persistence priority arbitration")

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-035 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-035 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
