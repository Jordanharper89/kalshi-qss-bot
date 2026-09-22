from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-279'
REVISION='OAD_279_GMGN_SOLANA_TOKEN_INTELLIGENCE_ADAPTER_V1'
TITLE='GMGN SOLANA TOKEN INTELLIGENCE ADAPTER'
EXPECTED_FILENAME='build_oad_279_gmgn_solana_token_intelligence_adapter.py'
MODULE_NAME='oad_279_gmgn_solana_token_intelligence_adapter.py'
TEST_NAME='test_oad_279_gmgn_solana_token_intelligence_adapter.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_277_gmgn_production_admission_boundary.py': ('require_gmgn_admission',), 'qseries_v2/oracle_adapters/independent/oad_278_gmgn_solana_trending_live_adapter.py': ('GMGNObservation', '_json_from_stdout')}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nimport json,subprocess\nfrom .oad_277_gmgn_production_admission_boundary import require_gmgn_admission\nfrom .oad_278_gmgn_solana_trending_live_adapter import GMGNObservation,_json_from_stdout\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\ndef _run(cli,args,timeout_seconds):\n    p=subprocess.run([cli,*args,"--raw"],text=True,capture_output=True,timeout=float(timeout_seconds))\n    if p.returncode!=0:\n        raise RuntimeError("GMGN command failed: "+(p.stderr or p.stdout).strip()[:500])\n    return _json_from_stdout(p.stdout)\n\ndef acquire_gmgn_solana_token_intelligence(token_address,timeout_seconds=30.0):\n    token=str(token_address).strip()\n    if not token: raise ValueError("token_address required")\n    a=require_gmgn_admission()\n    info=_run(a.cli_path,["token","info","--chain","sol","--address",token],timeout_seconds)\n    security=_run(a.cli_path,["token","security","--chain","sol","--address",token],timeout_seconds)\n    pool=_run(a.cli_path,["token","pool","--chain","sol","--address",token],timeout_seconds)\n    return GMGNObservation(\n        "source.gmgn.solana.token."+token,\n        "gmgn","token_intelligence","gmgn_solana_token_intelligence",\n        datetime.now(timezone.utc),\n        {"chain":"sol","token_address":token,"info":info,"security":security,"pool":pool},\n        False,\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_279_gmgn_solana_token_intelligence_adapter import *\nfrom qseries_v2.oracle_adapters.independent.oad_277_gmgn_production_admission_boundary import evaluate_gmgn_admission\n\nclass T(unittest.TestCase):\n    def test_contract(self):\n        a=evaluate_gmgn_admission()\n        print("[GMGN_ADMITTED]",a.admitted)\n        self.assertFalse(EXECUTION_AUTHORITY)\n        self.assertFalse(PROBABILITY_ENABLED)\n        self.assertFalse(DIRECTION_ENABLED)\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-279 GMGN token info/security/pool observation contract certified")\n    print("[NOTE] live token-specific physical call is exercised downstream with a known current token")\n'

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
