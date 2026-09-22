from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_158_ETHEREUM_FINALIZED_CHAIN_BLOCK_ACQUISITION_V1'
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
    module=pkg/'oad_158_ethereum_finalized_chain_block_acquisition.py'; test=r/'test_oad_158_ethereum_finalized_chain_block_acquisition.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-158 ETHEREUM FINALIZED CHAIN AND BLOCK ACQUISITION INSTALLER"); print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_157_ethereum_onchain_evidence_foundation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    if 158>=160:
        canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
        oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified")
        print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom datetime import datetime,timezone\nfrom urllib.request import Request,urlopen\nfrom .oad_157_ethereum_onchain_evidence_foundation import MAINNET_RPC,build_ethereum_onchain_observation,validate_ethereum_onchain_observation,utcnow_iso\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\ndef _rpc(method,params,timeout_seconds):\n    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode("utf-8")\n    req=Request(MAINNET_RPC,data=body,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Content-Type":"application/json","Accept":"application/json"},method="POST")\n    with urlopen(req,timeout=timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    if data.get("error"):\n        raise RuntimeError(f"Ethereum RPC {method} error: {data[\'error\']}")\n    return data.get("result")\n\ndef _hexint(v):\n    return None if v is None else int(str(v),16)\n\ndef acquire_ethereum_finalized_chain_observations(timeout_seconds=20.0):\n    chain_id=_hexint(_rpc("eth_chainId",[],timeout_seconds))\n    latest_number=_hexint(_rpc("eth_blockNumber",[],timeout_seconds))\n    block=_rpc("eth_getBlockByNumber",["finalized",False],timeout_seconds)\n    if not isinstance(block,dict):\n        raise RuntimeError("Ethereum finalized block unavailable")\n    finalized_number=_hexint(block.get("number"))\n    ts=_hexint(block.get("timestamp"))\n    observed=datetime.fromtimestamp(ts,timezone.utc).isoformat() if ts is not None else utcnow_iso()\n    txs=tuple(block.get("transactions") or ())\n    state=build_ethereum_onchain_observation(\n        source_id=f"ethereum:mainnet:state:{chain_id}:{latest_number}:{finalized_number}",\n        observation_type="finalized_chain_state",\n        subject="Ethereum mainnet finalized chain state",\n        observed_at=observed,\n        payload={\n            "chain_id":chain_id,\n            "latest_block_number":latest_number,\n            "finalized_block_number":finalized_number,\n            "latest_minus_finalized":None if latest_number is None or finalized_number is None else latest_number-finalized_number,\n        })\n    activity=build_ethereum_onchain_observation(\n        source_id=f"ethereum:mainnet:finalized-block:{finalized_number}:{block.get(\'hash\')}",\n        observation_type="finalized_block_activity",\n        subject=f"Ethereum finalized block {finalized_number}",\n        observed_at=observed,\n        payload={\n            "block_number":finalized_number,\n            "block_hash":block.get("hash"),\n            "parent_hash":block.get("parentHash"),\n            "timestamp":ts,\n            "transaction_count":len(txs),\n            "gas_limit":_hexint(block.get("gasLimit")),\n            "gas_used":_hexint(block.get("gasUsed")),\n            "base_fee_per_gas":_hexint(block.get("baseFeePerGas")),\n            "blob_gas_used":_hexint(block.get("blobGasUsed")),\n            "excess_blob_gas":_hexint(block.get("excessBlobGas")),\n            "size":_hexint(block.get("size")),\n        })\n    if not validate_ethereum_onchain_observation(state) or not validate_ethereum_onchain_observation(activity):\n        raise RuntimeError("Ethereum finalized observation validation failed")\n    return (state,activity)\n')
        write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_158_ethereum_finalized_chain_block_acquisition as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        values={\n            "eth_chainId":"0x1",\n            "eth_blockNumber":"0x64",\n            "eth_getBlockByNumber":{"number":"0x60","hash":"0xabc","parentHash":"0xdef","timestamp":"0x6a2f1000","transactions":["0x1","0x2"],"gasLimit":"0x1c9c380","gasUsed":"0xe4e1c0","baseFeePerGas":"0x3b9aca00","size":"0x1000"}\n        }\n        with patch.object(m,"_rpc",side_effect=lambda method,params,timeout: values[method]):\n            r=m.acquire_ethereum_finalized_chain_observations()\n        print("[OBSERVATIONS]",len(r)); print("[FINALIZED_BLOCK]",r[1].payload["block_number"]); print("[TX_COUNT]",r[1].payload["transaction_count"])\n        self.assertEqual(len(r),2); self.assertEqual(r[0].payload["chain_id"],1); self.assertEqual(r[1].payload["transaction_count"],2)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-158 Ethereum finalized chain/block acquisition certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_158_ethereum_finalized_chain_block_acquisition import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-158 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
