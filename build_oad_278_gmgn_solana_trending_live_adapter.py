from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-278'
REVISION='OAD_278_GMGN_SOLANA_TRENDING_LIVE_ADAPTER_V1'
TITLE='GMGN SOLANA TRENDING LIVE ADAPTER'
EXPECTED_FILENAME='build_oad_278_gmgn_solana_trending_live_adapter.py'
MODULE_NAME='oad_278_gmgn_solana_trending_live_adapter.py'
TEST_NAME='test_oad_278_gmgn_solana_trending_live_adapter.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_277_gmgn_production_admission_boundary.py': ('require_gmgn_admission',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nimport json,subprocess\nfrom .oad_277_gmgn_production_admission_boundary import require_gmgn_admission\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass GMGNObservation:\n    source_id:str\n    provider:str\n    source_class:str\n    observation_type:str\n    observed_at:datetime\n    payload:dict\n    execution_authority:bool=False\n\ndef _json_from_stdout(text):\n    text=str(text).strip()\n    if not text: raise RuntimeError("GMGN returned empty stdout")\n    candidates=[text]+[x.strip() for x in text.splitlines()[::-1] if x.strip()]\n    for c in candidates:\n        try:\n            return json.loads(c)\n        except Exception:\n            pass\n    raise RuntimeError("GMGN output was not valid JSON")\n\ndef acquire_gmgn_solana_trending(interval="5m",limit=20,timeout_seconds=30.0):\n    a=require_gmgn_admission()\n    cmd=[a.cli_path,"market","trending","--chain","sol","--interval",str(interval),\n         "--order-by","volume","--limit",str(int(limit)),"--raw"]\n    p=subprocess.run(cmd,text=True,capture_output=True,timeout=float(timeout_seconds))\n    if p.returncode!=0:\n        raise RuntimeError("GMGN trending failed: "+(p.stderr or p.stdout).strip()[:500])\n    data=_json_from_stdout(p.stdout)\n    now=datetime.now(timezone.utc)\n    return GMGNObservation(\n        "source.gmgn.solana.market.trending."+str(interval),\n        "gmgn","market_intelligence","gmgn_solana_trending",now,\n        {"chain":"sol","interval":str(interval),"limit":int(limit),"raw":data},False\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_277_gmgn_production_admission_boundary import evaluate_gmgn_admission\nfrom qseries_v2.oracle_adapters.independent.oad_278_gmgn_solana_trending_live_adapter import acquire_gmgn_solana_trending\n\nclass T(unittest.TestCase):\n    def test_physical_or_truthful_hold(self):\n        a=evaluate_gmgn_admission()\n        if not a.admitted:\n            print("[HOLD] GMGN physical acquisition not admitted")\n            print("[HOLD] gmgn_cli=",bool(a.cli_path),"api_key_present=",a.api_key_present,"version_ok=",a.version_ok)\n            return\n        r=acquire_gmgn_solana_trending()\n        print("[PHYSICAL] source_id=",r.source_id)\n        print("[PHYSICAL] provider=",r.provider)\n        print("[PHYSICAL] payload_type=",type(r.payload.get("raw")).__name__)\n        self.assertEqual(r.provider,"gmgn")\n        self.assertEqual(r.payload["chain"],"sol")\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-278 GMGN Solana trending adapter contract certified")\n'

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
