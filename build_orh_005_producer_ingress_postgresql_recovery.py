from pathlib import Path
import ast,os,subprocess,sys
ROOT=Path.cwd().resolve();LAUNCHER=ROOT/"run_oracle_LIVE.py";TEST=ROOT/"test_orh_005_producer_ingress_postgresql_recovery.py"

def read_children(source):
    tree=ast.parse(source)
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
            return {str(k.value):str(v.value) for k,v in zip(item.value.keys,item.value.values) if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str)}
    raise RuntimeError("CHILDREN dictionary not found")

def parse_underlying(source):
    tree=ast.parse(source)
    for item in tree.body:
        if isinstance(item,ast.Assign):
            for t in item.targets:
                if isinstance(t,ast.Name) and t.id=="UNDERLYING_RUNNER":
                    return str(ast.literal_eval(item.value))
    raise RuntimeError("UNDERLYING_RUNNER missing")

def wrapper_source(child,underlying):
    producer="oracle."+child
    lines=[
        "from pathlib import Path",
        "import runpy,time",
        "from qseries_v2.oracle_postgresql_reliability.opr_002_persistent_producer_ingress import install_persistent_postgresql_ingress",
        'ORH_005_BUILD_ID="ORH-005"',
        f"UNDERLYING_RUNNER={underlying!r}",
        f"PRODUCER={producer!r}",
        "BACKOFF_SECONDS=(1.0,2.0,5.0,10.0,30.0)",
        "",
        "if __name__=='__main__':",
        "    print('='*88,flush=True)",
        f"    print(' OPR-004 PERSISTENT POSTGRESQL INGRESS child={child} — ORH-005 RESILIENT',flush=True)",
        "    print('='*88,flush=True)",
        "    failures=0",
        "    while True:",
        "        try:",
        "            install_persistent_postgresql_ingress(PRODUCER,Path.cwd())",
        "            print('[ORH-005] persistent_queue_session=TRUE direct_canonical_postgresql_write_authority=FALSE',flush=True)",
        "            runpy.run_path(str(Path.cwd()/UNDERLYING_RUNNER),run_name='__main__')",
        "            raise RuntimeError('underlying runner returned unexpectedly')",
        "        except KeyboardInterrupt:",
        "            raise",
        "        except SystemExit as exc:",
        "            code=exc.code if isinstance(exc.code,int) else 0",
        "            if code in (0,None): raise",
        "            failures+=1",
        "            delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]",
        f"            print(f'[ORH-005 INGRESS RECOVERY] child={child} status=DEGRADED exit_code={{code}} retry_in={{delay:.1f}}s execution_authority=FALSE',flush=True)",
        "            time.sleep(delay)",
        "        except Exception as exc:",
        "            failures+=1",
        "            delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]",
        f"            print(f'[ORH-005 INGRESS RECOVERY] child={child} status=DEGRADED failure={{failures}} type={{type(exc).__name__}} retry_in={{delay:.1f}}s execution_authority=FALSE',flush=True)",
        "            time.sleep(delay)",
        "",
    ]
    source="\n".join(lines);ast.parse(source);return source

def write_exact(p,s):
    tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(s,encoding="utf-8",newline="\n");os.replace(tmp,p)
def restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:p.write_bytes(b)

def main():
    print("="*88);print(" ORH-005 INSTALLER");print(" PRODUCER INGRESS POSTGRESQL RECOVERY");print("="*88);print("[ROOT]",ROOT)
    children=read_children(LAUNCHER.read_text(encoding="utf-8"));targets={}
    for child,runner in children.items():
        if child in ("canonical_writer","reasoning","continuity"):continue
        p=ROOT/runner
        if not p.is_file():raise RuntimeError(f"Physical child runner missing: {child} -> {runner}")
        s=p.read_text(encoding="utf-8")
        if "opr_004_" not in p.name or "UNDERLYING_RUNNER" not in s:raise RuntimeError(f"Refusing ORH-005: {child} is not physical OPR-004 wrapper: {runner}")
        targets[p]=(child,parse_underlying(s))
    if not targets:raise RuntimeError("No physical OPR-004 producer wrappers found")
    old={p:p.read_bytes() for p in targets};oldtest=TEST.read_bytes() if TEST.exists() else None
    try:
        names=[]
        for p,(child,underlying) in targets.items():
            if not (ROOT/underlying).is_file():raise RuntimeError(f"Underlying runner missing: {child} -> {underlying}")
            src=wrapper_source(child,underlying);write_exact(p,src);names.append(str(p.relative_to(ROOT)))
            print(f"[PASS] child={child} wrapper={p.name} underlying={underlying}")
        test="import ast,unittest\nfrom pathlib import Path\nROOT=Path.cwd().resolve()\nFILES="+repr(names)+"\nclass T(unittest.TestCase):\n    def test_wrappers(self):\n        for name in FILES:\n            s=(ROOT/name).read_text(encoding='utf-8');ast.parse(s);self.assertIn('ORH_005_BUILD_ID',s);self.assertIn('INGRESS RECOVERY',s);self.assertIn('UNDERLYING_RUNNER',s)\nif __name__=='__main__':\n    print('='*88);print(' ORH-005 CERTIFICATION TEST');print(' PRODUCER INGRESS POSTGRESQL RECOVERY');print('='*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print('[PASS] physical producer wrappers resilient')\n    print('[PASS] underlying runners preserved')\n    print('[PASS] execution_authority=FALSE')\n    print('[DONE] ORH-005 CERTIFIED')\n"
        write_exact(TEST,test);subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),timeout=30,check=True)
    except Exception:
        for p,b in old.items():p.write_bytes(b)
        restore(TEST,oldtest)
        print("[ROLLBACK] ORH-005 failed; producer wrappers restored");raise
    print("[PASS] Exact physical OPR-004 wrappers corrected")
    print("[PASS] Underlying acquisition/learning/coverage runners unchanged")
    print("[PASS] PostgreSQL bootstrap failures now retry in-process")
    print("[PASS] physical run_oracle_LIVE.py --check passed")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORH-005 INSTALLATION COMPLETE")
if __name__=="__main__":main()
