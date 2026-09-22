
from __future__ import annotations
import ast, hashlib, os, subprocess, sys, textwrap
from pathlib import Path

BUILD_ID = 'OAD-259'
REVISION = 'OAD_259_SOLANA_STABLECOIN_PHYSICAL_LIVE_ACQUISITION_CERTIFICATION_V1'
TITLE = 'SOLANA STABLECOIN PHYSICAL LIVE ACQUISITION CERTIFICATION'
MODULE_NAME = 'oad_259_solana_stablecoin_physical_live_acquisition_certification.py'
TEST_NAME = 'test_oad_259_solana_stablecoin_physical_live_acquisition_certification.py'
DEPENDENCIES = ['qseries_v2/oracle_adapters/independent/oad_255_solana_stablecoin_supply_intelligence.py', 'qseries_v2/oracle_adapters/independent/oad_252_crypto_independent_source_expansion_foundation.py']
MODULE_SOURCE = '\nfrom dataclasses import dataclass\nfrom decimal import Decimal\nfrom .oad_255_solana_stablecoin_supply_intelligence import acquire_solana_stablecoin_supply\nfrom .oad_252_crypto_independent_source_expansion_foundation import verify_independent_crypto_observation\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n@dataclass(frozen=True,slots=True)\nclass SolanaStablecoinPhysicalCertification:\n    symbol:str; mint:str; amount_raw:str; decimals:int; ui_amount_string:str; provider:str; provenance_hash:str; certified:bool; execution_authority:bool=False\ndef certify_live_solana_stablecoin_supply(symbol="USDC",timeout_seconds=20.0):\n    x=acquire_solana_stablecoin_supply(symbol=symbol,timeout=timeout_seconds)\n    if not verify_independent_crypto_observation(x): raise RuntimeError("OAD-252 provenance verification failed")\n    p=x.payload\n    if Decimal(str(p["amount_raw"]))<=0: raise RuntimeError("invalid finalized stablecoin supply")\n    return SolanaStablecoinPhysicalCertification(str(p["symbol"]),str(p["mint"]),str(p["amount_raw"]),int(p["decimals"]),str(p.get("ui_amount_string") or ""),x.provider,x.provenance_hash,True,False)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_259_solana_stablecoin_physical_live_acquisition_certification import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  r=certify_live_solana_stablecoin_supply("USDC")\n  print("[PHYSICAL] symbol=",r.symbol); print("[PHYSICAL] mint=",r.mint); print("[PHYSICAL] amount_raw=",r.amount_raw); print("[PHYSICAL] decimals=",r.decimals)\n  self.assertEqual(r.symbol,"USDC"); self.assertTrue(r.certified)\nif __name__=="__main__":\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful(): raise SystemExit(1)\n print("[PASS] OAD-259 physical live finalized Solana USDC supply certified")\n'

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
