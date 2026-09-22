
from __future__ import annotations
import ast, hashlib, os, subprocess, sys, textwrap
from pathlib import Path

BUILD_ID = 'OAD-258'
REVISION = 'OAD_258_SOLANA_DEX_LIQUIDITY_PHYSICAL_LIVE_ACQUISITION_CERTIFICATION_V1'
TITLE = 'SOLANA DEX LIQUIDITY PHYSICAL LIVE ACQUISITION CERTIFICATION'
MODULE_NAME = 'oad_258_solana_dex_liquidity_physical_live_acquisition_certification.py'
TEST_NAME = 'test_oad_258_solana_dex_liquidity_physical_live_acquisition_certification.py'
DEPENDENCIES = ['qseries_v2/oracle_adapters/independent/oad_254_solana_dex_liquidity_intelligence.py', 'qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py']
MODULE_SOURCE = '\nfrom dataclasses import dataclass\nfrom .oad_254_solana_dex_liquidity_intelligence import acquire_solana_dex_liquidity\nfrom .oad_252_crypto_independent_source_expansion_foundation import verify_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass SolanaDexPhysicalCertification:\n    query:str; pair_count:int; pair_addresses:tuple; dex_ids:tuple; provider:str; provenance_hash:str; certified:bool; execution_authority:bool=False\ndef certify_live_solana_dex_liquidity(query="SOL/USDC",limit=25,timeout_seconds=20.0):\n    x=acquire_solana_dex_liquidity(query=query,limit=limit,timeout=timeout_seconds)\n    if not verify_independent_crypto_observation(x): raise RuntimeError("OAD-252 provenance verification failed")\n    rows=tuple(x.payload.get("pairs") or ())\n    if not rows: raise RuntimeError("live Solana DEX response contained no pairs")\n    addresses=tuple(str(r.get("pair_address") or "") for r in rows)\n    if not any(addresses): raise RuntimeError("live Solana DEX pair identities missing")\n    dexes=tuple(sorted({str(r.get("dex_id") or "") for r in rows if r.get("dex_id")}))\n    return SolanaDexPhysicalCertification(str(query),len(rows),addresses,dexes,x.provider,x.provenance_hash,True,False)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_258_solana_dex_liquidity_physical_live_acquisition_certification import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=certify_live_solana_dex_liquidity()\n  print("[PHYSICAL] query=",r.query); print("[PHYSICAL] pair_count=",r.pair_count); print("[PHYSICAL] dex_ids=",r.dex_ids); print("[PHYSICAL] first_pair=",r.pair_addresses[0])\n  self.assertGreater(r.pair_count,0); self.assertTrue(r.certified)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-258 physical live Solana DEX liquidity acquisition certified")\n'

def locate_root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"
    freeze=root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    kalshi=root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel in DEPENDENCIES:
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        print("[PASS] dependency verified:",rel)

    frozen={}
    for p,label in ((freeze,"Frozen OPH-023"),(kalshi,"Frozen Kalshi OAD-055")):
        if p.is_file():
            frozen[p]=hashlib.sha256(p.read_bytes()).hexdigest()
            print("[PASS]",label,"verified")

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
