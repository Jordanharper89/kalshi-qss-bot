from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_163_CRYPTO_LIVE_MULTI_SOURCE_COHORT_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom .oad_162_crypto_cross_source_intelligence_foundation import verify_crypto_source_contracts\nfrom .oad_144_coinbase_live_spot_market_acquisition import acquire_coinbase_live_spot_observations\nfrom .oad_148_solana_mainnet_chain_state_acquisition import acquire_solana_mainnet_chain_state\nfrom .oad_149_solana_finalized_block_activity_acquisition import acquire_solana_finalized_block_activity\nfrom .oad_153_bitcoin_blockstream_chain_tip_block_acquisition import acquire_bitcoin_blockstream_chain_observations\nfrom .oad_154_bitcoin_mempool_fee_pressure_acquisition import acquire_bitcoin_mempool_pressure_observations\nfrom .oad_158_ethereum_finalized_chain_block_acquisition import acquire_ethereum_finalized_chain_observations\nfrom .oad_159_ethereum_fee_transaction_pressure_acquisition import acquire_ethereum_fee_transaction_pressure_observations\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nDIRECTION_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoSourceState:\n    source_family:str\n    state:str\n    observation_count:int\n    error_type:str|None\n    error_message:str|None\n\n@dataclass(frozen=True,slots=True)\nclass CryptoLiveMultiSourceCohort:\n    state:str\n    source_states:tuple\n    observations:tuple\n    available_sources:tuple\n    unavailable_sources:tuple\n    captured_at:str\n    read_only:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef _capture(name,fn):\n    try:\n        obs=tuple(fn())\n        return CryptoSourceState(name,"AVAILABLE",len(obs),None,None),obs\n    except Exception as exc:\n        return CryptoSourceState(name,"UNAVAILABLE",0,type(exc).__name__,str(exc)[:300]),tuple()\n\ndef build_crypto_live_multi_source_cohort(timeout_seconds=20.0,max_coinbase_products=25):\n    verify_crypto_source_contracts()\n    pairs=[]\n    pairs.append(_capture("coinbase",lambda: acquire_coinbase_live_spot_observations(timeout_seconds,max_coinbase_products)))\n    pairs.append(_capture("bitcoin",lambda: tuple(acquire_bitcoin_blockstream_chain_observations(timeout_seconds))+tuple(acquire_bitcoin_mempool_pressure_observations(timeout_seconds))))\n    pairs.append(_capture("ethereum",lambda: tuple(acquire_ethereum_finalized_chain_observations(timeout_seconds))+tuple(acquire_ethereum_fee_transaction_pressure_observations(timeout_seconds))))\n    pairs.append(_capture("solana",lambda: tuple(acquire_solana_mainnet_chain_state(timeout_seconds))+tuple(acquire_solana_finalized_block_activity(timeout_seconds))))\n    states=tuple(x[0] for x in pairs)\n    observations=tuple((state.source_family,o) for state,obs in pairs for o in obs)\n    available=tuple(x.source_family for x in states if x.state=="AVAILABLE")\n    unavailable=tuple(x.source_family for x in states if x.state!="AVAILABLE")\n    state="FULL_COVERAGE" if len(available)==4 else ("PARTIAL_COVERAGE" if available else "NO_COVERAGE")\n    return CryptoLiveMultiSourceCohort(state,states,observations,available,unavailable,datetime.now(timezone.utc).isoformat(),True,False,False,False)\n'
TEST_SOURCE='import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent import oad_163_crypto_live_multi_source_cohort as m\ndef o(subject,obs_type="x"):\n    return SimpleNamespace(subject=subject,observation_type=obs_type,observed_at="2026-08-29T00:00:00+00:00",payload={})\nclass T(unittest.TestCase):\n    def test_isolation(self):\n        with patch.object(m,"acquire_coinbase_live_spot_observations",return_value=(o("BTC-USD"),)),patch.object(m,"acquire_bitcoin_blockstream_chain_observations",return_value=(o("btc"),)),patch.object(m,"acquire_bitcoin_mempool_pressure_observations",return_value=(o("btc2"),)),patch.object(m,"acquire_ethereum_finalized_chain_observations",side_effect=RuntimeError("provider down")),patch.object(m,"acquire_solana_mainnet_chain_state",return_value=(o("sol"),)),patch.object(m,"acquire_solana_finalized_block_activity",return_value=(o("sol2"),)):\n            r=m.build_crypto_live_multi_source_cohort()\n        print("[STATE]",r.state); print("[AVAILABLE]",r.available_sources); print("[UNAVAILABLE]",r.unavailable_sources)\n        self.assertEqual(r.state,"PARTIAL_COVERAGE"); self.assertIn("ethereum",r.unavailable_sources); self.assertIn("bitcoin",r.available_sources)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-163 resilient live multi-source cohort certified")\n'
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
    module=pkg/'oad_163_crypto_live_multi_source_cohort.py'; test=r/'test_oad_163_crypto_live_multi_source_cohort.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-163 CRYPTO LIVE MULTI-SOURCE COHORT INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_162_crypto_cross_source_intelligence_foundation.py', 'oad_144_coinbase_live_spot_market_acquisition.py', 'oad_148_solana_mainnet_chain_state_acquisition.py', 'oad_149_solana_finalized_block_activity_acquisition.py', 'oad_153_bitcoin_blockstream_chain_tip_block_acquisition.py', 'oad_154_bitcoin_mempool_fee_pressure_acquisition.py', 'oad_158_ethereum_finalized_chain_block_acquisition.py', 'oad_159_ethereum_fee_transaction_pressure_acquisition.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_163_crypto_live_multi_source_cohort import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-163 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
