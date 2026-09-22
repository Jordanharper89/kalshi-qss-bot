from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_148_SOLANA_MAINNET_CHAIN_STATE_ACQUISITION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_148_solana_mainnet_chain_state_acquisition.py'; test=r/'test_oad_148_solana_mainnet_chain_state_acquisition.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-148 SOLANA MAINNET CHAIN-STATE ACQUISITION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_147_solana_onchain_evidence_foundation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
    oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
    if 148>=150:
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified")
        print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.request import Request,urlopen\nfrom .oad_147_solana_onchain_evidence_foundation import MAINNET_RPC,build_solana_onchain_observation,utcnow_iso,validate_solana_onchain_observation\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\ndef _rpc(method,params,timeout_seconds):\n    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode("utf-8")\n    req=Request(MAINNET_RPC,data=body,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Content-Type":"application/json","Accept":"application/json"},method="POST")\n    with urlopen(req,timeout=timeout_seconds) as r:\n        data=json.loads(r.read().decode("utf-8"))\n    if data.get("error"): raise RuntimeError(f"Solana RPC {method} error: {data[\'error\']}")\n    return data.get("result")\n\ndef acquire_solana_mainnet_chain_state(timeout_seconds=20.0):\n    slot=int(_rpc("getSlot",[{"commitment":"finalized"}],timeout_seconds))\n    height=int(_rpc("getBlockHeight",[{"commitment":"finalized"}],timeout_seconds))\n    epoch=_rpc("getEpochInfo",[{"commitment":"finalized"}],timeout_seconds)\n    tx_count=int(_rpc("getTransactionCount",[{"commitment":"finalized"}],timeout_seconds))\n    now=utcnow_iso()\n    payload={"slot":slot,"block_height":height,"transaction_count":tx_count,"epoch_info":epoch}\n    o=build_solana_onchain_observation(\n        source_id=f"solana:mainnet:chain-state:{slot}:{height}",\n        observation_type="finalized_chain_state",subject="Solana mainnet finalized chain state",\n        observed_at=now,payload=payload)\n    if not validate_solana_onchain_observation(o): raise RuntimeError("Solana chain-state validation failed")\n    return (o,)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_148_solana_mainnet_chain_state_acquisition as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        vals={"getSlot":500,"getBlockHeight":450,"getEpochInfo":{"epoch":700,"slotIndex":12,"slotsInEpoch":432000},"getTransactionCount":123456}\n        with patch.object(m,"_rpc",side_effect=lambda method,params,timeout: vals[method]):\n            r=m.acquire_solana_mainnet_chain_state()\n        print("[CHAIN_STATE]",r[0].payload)\n        self.assertEqual(r[0].payload["slot"],500); self.assertEqual(r[0].payload["transaction_count"],123456)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-148 Solana mainnet chain-state acquisition certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_148_solana_mainnet_chain_state_acquisition import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-148 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
