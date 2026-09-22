
from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-300'
TITLE='SOLANA WALLET/TRADER CLAIM NORMALIZATION'
EXPECTED='build_oad_300_solana_wallet_trader_claim_normalization.py'
MODULE='oad_300_solana_wallet_trader_claim_normalization.py'
TEST='test_oad_300_solana_wallet_trader_claim_normalization.py'
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_299_gmgn_solana_trader_intelligence.py', ('def acquire_current_gmgn_holder_and_trader_pair',))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_299_gmgn_solana_trader_intelligence import acquire_current_gmgn_holder_and_trader_pair\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass ProviderClaim:\n    wallet_address:str|None\n    claim_kind:str\n    provider:str\n    claim_payload:dict\n    oracle_verified:bool=False\n@dataclass(frozen=True,slots=True)\nclass WalletTraderIntelligence:\n    token_address:str\n    holder_rows:int\n    trader_rows:int\n    provider_claims:tuple\n    execution_authority:bool=False\ndef _resource(x):\n    if isinstance(x,dict) and "data" in x: return x.get("data")\n    return x\ndef _rows(x):\n    x=_resource(x)\n    if isinstance(x,list): return tuple(y for y in x if isinstance(y,dict))\n    if isinstance(x,dict):\n        for key in ("holders","traders","list","items","rank"):\n            v=x.get(key)\n            if isinstance(v,list): return tuple(y for y in v if isinstance(y,dict))\n        return (x,)\n    return ()\ndef _wallet(row):\n    for k in ("address","wallet_address","wallet","owner","maker"):\n        v=row.get(k)\n        if v: return str(v)\n    return None\ndef normalize_current_gmgn_wallet_trader_intelligence(timeout_seconds=30.0):\n    h,t=acquire_current_gmgn_holder_and_trader_pair(timeout_seconds)\n    hr=_rows(h.raw); tr=_rows(t.raw); claims=[]\n    for kind,rows in (("holder",hr),("trader",tr)):\n        for row in rows: claims.append(ProviderClaim(_wallet(row),kind,"gmgn",dict(row),False))\n    return WalletTraderIntelligence(h.token_address,len(hr),len(tr),tuple(claims),False)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_300_solana_wallet_trader_claim_normalization import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=normalize_current_gmgn_wallet_trader_intelligence()\n        print("[PHYSICAL] token=",r.token_address); print("[PHYSICAL] holder_rows=",r.holder_rows); print("[PHYSICAL] trader_rows=",r.trader_rows); print("[PHYSICAL] provider_claims=",len(r.provider_claims))\n        self.assertTrue(r.token_address); self.assertEqual(len(r.provider_claims),r.holder_rows+r.trader_rows)\n        self.assertTrue(all(x.provider=="gmgn" and x.oracle_verified is False for x in r.provider_claims))\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-300 wallet/trader provider-claim normalization physically certified")\n    print("[PASS] GMGN labels remain provider claims, not Oracle truth")\n'

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
