
from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-297'
TITLE='GMGN WALLET/TRADER CLI CAPABILITY BOUNDARY'
EXPECTED='build_oad_297_gmgn_wallet_trader_cli_capability_boundary.py'
MODULE='oad_297_gmgn_wallet_trader_cli_capability_boundary.py'
TEST='test_oad_297_gmgn_wallet_trader_cli_capability_boundary.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_287_gmgn_clean_provider_foundation.py', ('def require_gmgn_provider', 'def run_gmgn_cli', 'class GMGNRateLimitError'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nimport json\nfrom .oad_287_gmgn_clean_provider_foundation import require_gmgn_provider, run_gmgn_cli, GMGNRateLimitError\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nROUTES=("holders","traders")\n@dataclass(frozen=True,slots=True)\nclass GMGNWalletTraderCapability:\n    route:str\n    help_ok:bool\n    command_visible:bool\n    execution_authority:bool=False\ndef _text(v):\n    if isinstance(v,(bytes,bytearray)): return v.decode("utf-8","replace")\n    return str(v or "")\ndef verify_wallet_trader_cli_capabilities(timeout_seconds=30.0):\n    a=require_gmgn_provider(timeout_seconds); out=[]\n    for route in ROUTES:\n        p=run_gmgn_cli(a.cli_path,["token",route,"--help"],timeout_seconds,True)\n        t=((p.stdout or "")+"\\n"+(p.stderr or "")).strip()\n        out.append(GMGNWalletTraderCapability(route,p.returncode==0 and bool(t),route.lower() in t.lower() or "usage" in t.lower(),False))\n    return tuple(out)\ndef _decode_json(v):\n    t=_text(v).strip()\n    try: return json.loads(t)\n    except Exception:\n        a=t.find("{"); b=t.rfind("}")\n        if a>=0 and b>a: return json.loads(t[a:b+1])\n    raise RuntimeError("GMGN wallet/trader route returned non-JSON output")\ndef call_wallet_trader_route(route,token_address,timeout_seconds=30.0):\n    route=str(route).strip().lower()\n    if route not in ROUTES: raise ValueError("unsupported GMGN wallet/trader route")\n    token=str(token_address).strip()\n    if not token: raise ValueError("token_address required")\n    a=require_gmgn_provider(timeout_seconds)\n    p=run_gmgn_cli(a.cli_path,["token",route,"--chain","sol","--address",token,"--raw"],timeout_seconds,False)\n    out=_text(p.stdout); err=_text(p.stderr); detail=(err or out).strip()\n    if p.returncode!=0:\n        u=detail.upper()\n        if "429" in u or "RATE_LIMIT" in u: raise GMGNRateLimitError("GMGN_RATE_LIMITED",300.0)\n        raise RuntimeError("GMGN "+route+" command failed rc="+str(p.returncode)+": "+detail[:1000])\n    data=_decode_json(p.stdout)\n    if isinstance(data,dict) and str(data.get("code"))=="429": raise GMGNRateLimitError("GMGN_RATE_LIMITED",300.0)\n    return data\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_297_gmgn_wallet_trader_cli_capability_boundary import *\nclass T(unittest.TestCase):\n    def test_physical_capability(self):\n        rows=verify_wallet_trader_cli_capabilities()\n        for x in rows: print("[GMGN CLI]",x.route,"help_ok=",x.help_ok,"command_visible=",x.command_visible)\n        self.assertEqual(tuple(x.route for x in rows),("holders","traders"))\n        self.assertTrue(all(x.help_ok and x.command_visible for x in rows))\n        self.assertTrue(READ_ONLY); self.assertFalse(EXECUTION_AUTHORITY)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-297 official GMGN holders/traders CLI capability boundary physically certified")\n'

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def checked_write(path, source):
    s=textwrap.dedent(source).lstrip()
    ast.parse(s, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp")
    t.write_text(s, encoding="utf-8", newline="\n")
    os.replace(t, path)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE
    test=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]", r)

    for rel, markers in DEPENDENCIES:
        p=r/rel
        if not p.is_file():
            raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8")
        ast.parse(s, filename=str(p))
        for marker in markers:
            if marker not in s:
                raise RuntimeError("exact dependency marker missing: "+rel+" -> "+marker)
        print("[PASS] exact dependency verified:", rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        checked_write(module, MODULE_SOURCE)
        checked_write(test, TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        checked_write(init, "\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("frozen boundary changed: "+p.name)

        print("[PASS] module installed:", module.relative_to(r))
        print("[PASS] test installed:", test.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] provider labels remain claims, not Oracle truth")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
