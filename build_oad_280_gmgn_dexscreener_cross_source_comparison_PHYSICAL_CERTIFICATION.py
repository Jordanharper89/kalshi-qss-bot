from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED_FILENAME="build_oad_280_gmgn_dexscreener_cross_source_comparison_PHYSICAL_CERTIFICATION.py"
MODULE_NAME="oad_280_gmgn_dexscreener_cross_source_comparison.py"
TEST_NAME="test_oad_280_gmgn_dexscreener_cross_source_comparison.py"

MODULE_SOURCE=r"""
from __future__ import annotations

from dataclasses import dataclass
from .oad_279_gmgn_solana_token_intelligence_adapter import (
    acquire_current_gmgn_solana_token_intelligence,
)
from .oad_263_solana_token_pool_identity_liquidity import (
    acquire_solana_token_pool_identity_liquidity,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False


@dataclass(frozen=True, slots=True)
class CrossSourceComparison:
    token_address: str
    comparable_fields: int
    agreements: int
    contradictions: int
    details: tuple
    execution_authority: bool=False


def _first_dict(obj):
    if isinstance(obj,dict):
        return obj
    if isinstance(obj,list) and obj and isinstance(obj[0],dict):
        return obj[0]
    return {}


def _walk_numeric(obj,names):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if str(k).lower() in names and isinstance(v,(int,float)):
                return float(v)
        for v in obj.values():
            r=_walk_numeric(v,names)
            if r is not None: return r
    elif isinstance(obj,list):
        for v in obj:
            r=_walk_numeric(v,names)
            if r is not None: return r
    return None


def compare_gmgn_dexscreener_for_token(token_address, gmgn_obs=None, dex_obs=None):
    token=str(token_address).strip()
    if gmgn_obs is None:
        from .oad_279_gmgn_solana_token_intelligence_adapter import acquire_gmgn_solana_token_intelligence
        gmgn_obs=acquire_gmgn_solana_token_intelligence(token)
    if dex_obs is None:
        dex_obs=acquire_solana_token_pool_identity_liquidity(token)

    gmgn_payload=gmgn_obs.payload
    dex_payload=dex_obs.payload

    pairs=[]
    metric_defs=(
        ("price",{"price","price_usd","priceusd"},{"price_usd","price","priceusd"}),
        ("liquidity",{"liquidity","liquidity_usd","liquidityusd"},{"liquidity_usd","liquidity","liquidityusd"}),
        ("volume_h24",{"volume","volume_h24","volume24h","volume_24h"},{"volume_h24","volume","volume24h","volume_24h"}),
    )

    comparable=agreements=contradictions=0
    for label,g_names,d_names in metric_defs:
        gv=_walk_numeric(gmgn_payload,{x.lower() for x in g_names})
        dv=_walk_numeric(dex_payload,{x.lower() for x in d_names})
        state="NOT_COMPARABLE"
        if gv is not None and dv is not None:
            comparable+=1
            denom=max(abs(gv),abs(dv),1e-12)
            rel=abs(gv-dv)/denom
            if rel<=0.20:
                agreements+=1; state="AGREE_WITHIN_20PCT"
            else:
                contradictions+=1; state="CONTRADICTION_GT_20PCT"
        pairs.append((label,gv,dv,state))

    return CrossSourceComparison(token,comparable,agreements,contradictions,tuple(pairs),False)


def acquire_physical_gmgn_dexscreener_comparison():
    gmgn=acquire_current_gmgn_solana_token_intelligence()
    token=gmgn.token_address
    dex=acquire_solana_token_pool_identity_liquidity(token)
    return compare_gmgn_dexscreener_for_token(token,gmgn,dex)
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_280_gmgn_dexscreener_cross_source_comparison import (
    EXECUTION_AUTHORITY,PUBLICATION_ALLOWED,PROBABILITY_ENABLED,DIRECTION_ENABLED,
    acquire_physical_gmgn_dexscreener_comparison,
)

class T(unittest.TestCase):
    def test_physical_cross_source(self):
        r=acquire_physical_gmgn_dexscreener_comparison()
        print("[PHYSICAL] token=",r.token_address)
        print("[PHYSICAL] comparable=",r.comparable_fields)
        print("[PHYSICAL] agreements=",r.agreements)
        print("[PHYSICAL] contradictions=",r.contradictions)
        print("[PHYSICAL] details=",r.details)
        self.assertTrue(r.token_address)
        self.assertGreaterEqual(r.comparable_fields,1)
        self.assertEqual(r.agreements+r.contradictions,r.comparable_fields)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(PROBABILITY_ENABLED); self.assertFalse(DIRECTION_ENABLED); self.assertFalse(PUBLICATION_ALLOWED); self.assertFalse(EXECUTION_AUTHORITY)

if __name__=="__main__":
    print("="*120); print(" OAD-280 PHYSICAL CERTIFICATION TEST"); print(" GMGN ↔ DEXSCREENER CROSS-SOURCE COMPARISON"); print("="*120)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] physical GMGN ↔ DexScreener comparison certified")
    print("[PASS] contradictions preserved, not averaged away")
    print("[DONE] OAD-280 PHYSICALLY CERTIFIED")
"""

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path)); path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,path)

def main():
    if Path(__file__).name!=EXPECTED_FILENAME: raise RuntimeError("installer identity mismatch")
    root=locate_root(); pkg=root/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/MODULE_NAME; test=root/TEST_NAME; init=pkg/"__init__.py"
    print("="*120); print(" OAD-280 GMGN ↔ DEXSCREENER CROSS-SOURCE COMPARISON INSTALLER"); print("="*120); print("[ROOT]",root)
    for rel,symbol in (
        ("qseries_v2/oracle_adapters/independent/oad_279_gmgn_solana_token_intelligence_adapter.py","acquire_current_gmgn_solana_token_intelligence"),
        ("qseries_v2/oracle_adapters/independent/oad_263_solana_token_pool_identity_liquidity.py","acquire_solana_token_pool_identity_liquidity"),
    ):
        p=root/rel
        if not p.is_file() or ("def "+symbol+"(") not in p.read_text(encoding="utf-8"): raise RuntimeError("dependency missing: "+rel+" -> "+symbol)
        print("[PASS] exact dependency verified:",rel)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE); write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+module.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] OAD-280 installed")
        print("[PASS] physical cross-source test installed")
        print("[PASS] contradictions preserved explicitly")
        print("[PASS] no direction/probability/execution")
        print("[DONE] OAD-280 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OAD-280 restored"); raise

if __name__=="__main__": main()
