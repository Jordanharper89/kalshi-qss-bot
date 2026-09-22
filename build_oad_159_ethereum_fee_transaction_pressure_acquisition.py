from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_159_ETHEREUM_FEE_TRANSACTION_PRESSURE_ACQUISITION_V1'
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
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_159_ethereum_fee_transaction_pressure_acquisition.py'; test=r/'test_oad_159_ethereum_fee_transaction_pressure_acquisition.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-159 ETHEREUM FEE AND TRANSACTION PRESSURE ACQUISITION INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_157_ethereum_onchain_evidence_foundation.py', 'oad_158_ethereum_finalized_chain_block_acquisition.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    if 159>=160:
        canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
        oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified")
        print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom .oad_157_ethereum_onchain_evidence_foundation import build_ethereum_onchain_observation,validate_ethereum_onchain_observation,utcnow_iso\nfrom .oad_158_ethereum_finalized_chain_block_acquisition import _rpc,_hexint\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\ndef acquire_ethereum_fee_transaction_pressure_observations(timeout_seconds=20.0):\n    gas_price=_hexint(_rpc("eth_gasPrice",[],timeout_seconds))\n    fee_history=_rpc("eth_feeHistory",["0x5","latest",[10,50,90]],timeout_seconds)\n    tx_count=_hexint(_rpc("eth_getBlockTransactionCountByNumber",["latest"],timeout_seconds))\n    latest=_rpc("eth_getBlockByNumber",["latest",False],timeout_seconds)\n    if not isinstance(fee_history,dict) or not isinstance(latest,dict):\n        raise RuntimeError("Ethereum pressure source unavailable")\n    now=utcnow_iso()\n    base_fees=tuple(_hexint(x) for x in (fee_history.get("baseFeePerGas") or ()))\n    rewards=tuple(tuple(_hexint(v) for v in row) for row in (fee_history.get("reward") or ()))\n    ratios=tuple(fee_history.get("gasUsedRatio") or ())\n    fee=build_ethereum_onchain_observation(\n        source_id=f"ethereum:mainnet:fee-pressure:{latest.get(\'number\')}:{gas_price}:{now}",\n        observation_type="execution_fee_pressure",\n        subject="Ethereum mainnet execution fee pressure",\n        observed_at=now,\n        payload={\n            "gas_price_wei":gas_price,\n            "oldest_block":_hexint(fee_history.get("oldestBlock")),\n            "base_fee_per_gas_wei":base_fees,\n            "gas_used_ratio":ratios,\n            "priority_fee_reward_wei_p10_p50_p90":rewards,\n        })\n    activity=build_ethereum_onchain_observation(\n        source_id=f"ethereum:mainnet:latest-activity:{latest.get(\'number\')}:{latest.get(\'hash\')}",\n        observation_type="latest_block_transaction_pressure",\n        subject="Ethereum latest block transaction pressure",\n        observed_at=now,\n        payload={\n            "block_number":_hexint(latest.get("number")),\n            "block_hash":latest.get("hash"),\n            "transaction_count":tx_count,\n            "gas_limit":_hexint(latest.get("gasLimit")),\n            "gas_used":_hexint(latest.get("gasUsed")),\n            "base_fee_per_gas":_hexint(latest.get("baseFeePerGas")),\n            "blob_gas_used":_hexint(latest.get("blobGasUsed")),\n            "excess_blob_gas":_hexint(latest.get("excessBlobGas")),\n        })\n    if not validate_ethereum_onchain_observation(fee) or not validate_ethereum_onchain_observation(activity):\n        raise RuntimeError("Ethereum pressure observation validation failed")\n    return (fee,activity)\n')
        write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_159_ethereum_fee_transaction_pressure_acquisition as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        values={\n            "eth_gasPrice":"0x3b9aca00",\n            "eth_feeHistory":{"oldestBlock":"0x60","baseFeePerGas":["0x1","0x2"],"gasUsedRatio":[0.5],"reward":[["0x3","0x4","0x5"]]},\n            "eth_getBlockTransactionCountByNumber":"0x64",\n            "eth_getBlockByNumber":{"number":"0x65","hash":"0xabc","gasLimit":"0x100","gasUsed":"0x80","baseFeePerGas":"0x2"}\n        }\n        with patch.object(m,"_rpc",side_effect=lambda method,params,timeout: values[method]):\n            r=m.acquire_ethereum_fee_transaction_pressure_observations()\n        print("[OBSERVATIONS]",len(r)); print("[GAS_PRICE]",r[0].payload["gas_price_wei"]); print("[TX_COUNT]",r[1].payload["transaction_count"])\n        self.assertEqual(len(r),2); self.assertEqual(r[1].payload["transaction_count"],100)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-159 Ethereum fee/transaction pressure acquisition certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_159_ethereum_fee_transaction_pressure_acquisition import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-159 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
