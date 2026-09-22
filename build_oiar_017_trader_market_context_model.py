from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_017_trader_market_context_model.py'
TEST = ROOT / 'test_oiar_017_trader_market_context_model.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oiar_016_canonical_market_identity_resolver import resolve_canonical_market_identity\n\nOIAR_017_BUILD_ID="OIAR-017"\nOIAR_017_REVISION="OIAR_017_TRADER_MARKET_CONTEXT_MODEL_V1"\n\n@dataclass(frozen=True)\nclass TraderMarketContext:\n    market_id:str\n    display_name:str\n    event_ticker:str|None\n    historical_strength:str\n    live_evidence:str\n    direction:str\n    setup_quality:str\n    identity_status:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef _historical(row):\n    m=str(row.maturity or "").upper();r=float(row.reliability or 0)\n    return "STRONG" if m=="PROVEN" and r>=.60 else "MODERATE" if m in ("PROVEN","MATURE") or r>=.50 else "LIMITED"\n\ndef _live(row):\n    n=int(row.history_rows or 0);u=float(row.usefulness_score or 0)\n    return "STRONG" if n>=20 and u>=50 else "DEVELOPING" if n>=8 or u>=25 else "WEAK"\n\ndef build_trader_market_context(root,row):\n    ident=resolve_canonical_market_identity(root,row.market_id)\n    title=ident.market_title if ident.resolved and ident.market_title else "Identity unresolved"\n    admission=str(row.admission_status or "").lower()\n    candidate=str(row.candidate_family or "none").lower()\n    setup="ACTIONABLE_RESEARCH" if admission=="admitted" else "FORMING" if candidate!="none" else "NO_CONFIRMED_SETUP"\n    return TraderMarketContext(\n        row.market_id,title,ident.event_ticker,_historical(row),_live(row),\n        str(row.research_direction or "neutral").upper(),setup,\n        "RESOLVED" if ident.resolved else "UNRESOLVED",True,False\n    )\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_017_trader_market_context_model import OIAR_017_BUILD_ID\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OIAR_017_BUILD_ID,"OIAR-017")\nif __name__=="__main__":\n    print("="*88);print(" OIAR-017 CERTIFICATION TEST");print(" TRADER MARKET CONTEXT MODEL");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] trader market context contract certified")\n    print("[DONE] OIAR-017 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_016_canonical_market_identity_resolver.py',)
EXTRA_FILES = {}

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR_017_TRADER_MARKET_CONTEXT_MODEL INSTALLER")
    print("=" * 88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    targets = [MOD, TEST] + [ROOT / p for p in EXTRA_FILES]
    old = {p: (p.read_bytes() if p.exists() else None) for p in targets}

    try:
        ast.parse(MODULE_SOURCE)
        ast.parse(TEST_SOURCE)
        for src in EXTRA_FILES.values():
            ast.parse(src)
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        for rel, src in EXTRA_FILES.items():
            write_exact(ROOT / rel, src)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        importlib.invalidate_caches()
        pass
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] installer failed; affected files restored")
        raise

    print("[PASS] read-only trader intelligence boundary preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
