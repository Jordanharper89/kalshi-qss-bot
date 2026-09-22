from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-277'
REVISION='OAD_277_GMGN_PRODUCTION_ADMISSION_BOUNDARY_V1'
TITLE='GMGN PRODUCTION ADMISSION BOUNDARY'
EXPECTED_FILENAME='build_oad_277_gmgn_production_admission_boundary.py'
MODULE_NAME='oad_277_gmgn_production_admission_boundary.py'
TEST_NAME='test_oad_277_gmgn_production_admission_boundary.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_276_solana_continuous_observation_production_runner.py': ('evaluate_solana_continuous_runner',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport os, shutil, subprocess\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass GMGNAdmission:\n    cli_path:str|None\n    api_key_present:bool\n    version_ok:bool\n    admitted:bool\n    execution_authority:bool=False\n\ndef locate_gmgn_cli():\n    return shutil.which("gmgn-cli") or shutil.which("gmgn-cli.cmd")\n\ndef evaluate_gmgn_admission(timeout_seconds=10.0):\n    cli=locate_gmgn_cli()\n    key=bool(os.environ.get("GMGN_API_KEY","").strip())\n    version_ok=False\n    if cli:\n        try:\n            p=subprocess.run([cli,"--version"],text=True,capture_output=True,timeout=float(timeout_seconds))\n            version_ok=(p.returncode==0)\n        except Exception:\n            version_ok=False\n    return GMGNAdmission(cli,key,version_ok,bool(cli and key and version_ok),False)\n\ndef require_gmgn_admission(timeout_seconds=10.0):\n    a=evaluate_gmgn_admission(timeout_seconds)\n    if not a.cli_path:\n        raise RuntimeError("GMGN_NOT_ADMITTED: gmgn-cli not found on PATH")\n    if not a.api_key_present:\n        raise RuntimeError("GMGN_NOT_ADMITTED: GMGN_API_KEY is not configured")\n    if not a.version_ok:\n        raise RuntimeError("GMGN_NOT_ADMITTED: gmgn-cli version check failed")\n    return a\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_277_gmgn_production_admission_boundary import *\n\nclass T(unittest.TestCase):\n    def test_admission_is_truthful(self):\n        a=evaluate_gmgn_admission()\n        print("[GMGN] cli_path=",a.cli_path)\n        print("[GMGN] api_key_present=",a.api_key_present)\n        print("[GMGN] version_ok=",a.version_ok)\n        print("[GMGN] admitted=",a.admitted)\n        self.assertFalse(a.execution_authority)\n        self.assertEqual(a.admitted,bool(a.cli_path and a.api_key_present and a.version_ok))\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-277 truthful GMGN production-admission boundary certified")\n    print("[NOTE] admitted=FALSE is a valid HOLD until gmgn-cli + GMGN_API_KEY are provisioned")\n'

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

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] GMGN remains observation-only")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
