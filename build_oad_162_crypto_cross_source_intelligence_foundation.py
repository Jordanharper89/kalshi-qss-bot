from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_162_CRYPTO_CROSS_SOURCE_INTELLIGENCE_FOUNDATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nDIRECTION_ENABLED=False\n\nMARKET_NATIVE_SOURCE="coinbase"\nCHAIN_SOURCES=("bitcoin","ethereum","solana")\nASSETS=("BTC","ETH","SOL")\n\n@dataclass(frozen=True,slots=True)\nclass CryptoSourceContract:\n    source_family:str\n    source_class:str\n    independent_evidence:bool\n    asset_scope:tuple\n    role:str\n    read_only:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef crypto_source_contracts():\n    return (\n        CryptoSourceContract("coinbase","market_native_reference",False,ASSETS,"market_reference"),\n        CryptoSourceContract("bitcoin","underlying_chain_state_observation",True,("BTC",),"underlying_network_evidence"),\n        CryptoSourceContract("ethereum","underlying_chain_state_observation",True,("ETH",),"underlying_network_evidence"),\n        CryptoSourceContract("solana","underlying_chain_state",True,("SOL",),"underlying_network_evidence"),\n    )\n\ndef verify_crypto_source_contracts():\n    c=crypto_source_contracts()\n    if tuple(x.source_family for x in c)!=("coinbase","bitcoin","ethereum","solana"):\n        raise RuntimeError("crypto source contract order mismatch")\n    if c[0].independent_evidence is not False:\n        raise RuntimeError("Coinbase must remain market-native, not independent evidence")\n    if not all(x.independent_evidence is True for x in c[1:]):\n        raise RuntimeError("base-chain evidence contract mismatch")\n    if any(x.probability_enabled or x.direction_enabled or x.execution_authority for x in c):\n        raise RuntimeError("forbidden authority enabled")\n    return c\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_162_crypto_cross_source_intelligence_foundation import verify_crypto_source_contracts\nclass T(unittest.TestCase):\n    def test_contracts(self):\n        c=verify_crypto_source_contracts()\n        print("[SOURCES]",tuple(x.source_family for x in c))\n        print("[MARKET_NATIVE_INDEPENDENT]",c[0].independent_evidence)\n        print("[CHAIN_INDEPENDENT]",tuple(x.independent_evidence for x in c[1:]))\n        self.assertEqual(len(c),4)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-162 crypto cross-source intelligence foundation certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_162_crypto_cross_source_intelligence_foundation.py'; test=r/'test_oad_162_crypto_cross_source_intelligence_foundation.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-162 CRYPTO CROSS-SOURCE INTELLIGENCE FOUNDATION INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_144_coinbase_live_spot_market_acquisition.py', 'oad_151_solana_onchain_physical_runtime_certification.py', 'oad_156_bitcoin_onchain_physical_runtime_certification.py', 'oad_161_ethereum_onchain_physical_runtime_certification.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_162_crypto_cross_source_intelligence_foundation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-162 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
