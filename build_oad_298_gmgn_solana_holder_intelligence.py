
from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-298'
TITLE='GMGN SOLANA HOLDER INTELLIGENCE'
EXPECTED='build_oad_298_gmgn_solana_holder_intelligence.py'
MODULE='oad_298_gmgn_solana_holder_intelligence.py'
TEST='test_oad_298_gmgn_solana_holder_intelligence.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_292_solana_bounded_multisource_token_universe.py', ('def discover_bounded_multisource_solana_universe',)), ('qseries_v2/oracle_adapters/independent/oad_297_gmgn_wallet_trader_cli_capability_boundary.py', ('def call_wallet_trader_route',))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_292_solana_bounded_multisource_token_universe import discover_bounded_multisource_solana_universe\nfrom .oad_297_gmgn_wallet_trader_cli_capability_boundary import call_wallet_trader_route\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass GMGNHolderObservation:\n    token_address:str\n    observed_at:datetime\n    raw:object\n    execution_authority:bool=False\ndef acquire_gmgn_token_holders(token_address,timeout_seconds=30.0):\n    token=str(token_address).strip()\n    if not token: raise ValueError("token_address required")\n    return GMGNHolderObservation(token,datetime.now(timezone.utc),call_wallet_trader_route("holders",token,timeout_seconds),False)\ndef acquire_current_gmgn_token_holders(timeout_seconds=30.0):\n    u=discover_bounded_multisource_solana_universe(timeout_seconds); errors=[]\n    for c in u.candidates:\n        try: return acquire_gmgn_token_holders(c.token_address,timeout_seconds)\n        except Exception as e: errors.append(c.token_address+":"+type(e).__name__+":"+str(e)[:120])\n    raise RuntimeError("no current bounded Solana token completed GMGN holders acquisition: "+" | ".join(errors[:5]))\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_298_gmgn_solana_holder_intelligence import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        x=acquire_current_gmgn_token_holders()\n        print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] raw_type=",type(x.raw).__name__)\n        self.assertTrue(x.token_address); self.assertIsNotNone(x.raw); self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-298 live GMGN Solana holder intelligence physically certified")\n'

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
