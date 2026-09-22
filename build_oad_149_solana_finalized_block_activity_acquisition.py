from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_149_SOLANA_FINALIZED_BLOCK_ACTIVITY_ACQUISITION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_149_solana_finalized_block_activity_acquisition.py'; test=r/'test_oad_149_solana_finalized_block_activity_acquisition.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-149 SOLANA FINALIZED BLOCK ACTIVITY ACQUISITION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_147_solana_onchain_evidence_foundation.py', 'oad_148_solana_mainnet_chain_state_acquisition.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
    oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
    if 149>=150:
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified")
        print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom datetime import datetime,timezone\nfrom .oad_147_solana_onchain_evidence_foundation import build_solana_onchain_observation,validate_solana_onchain_observation,utcnow_iso\nfrom .oad_148_solana_mainnet_chain_state_acquisition import _rpc\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\n\ndef acquire_solana_finalized_block_activity(timeout_seconds=20.0,max_slot_lookback=8):\n    head=int(_rpc("getSlot",[{"commitment":"finalized"}],timeout_seconds))\n    block=None; slot=None\n    for candidate in range(head, max(head-int(max_slot_lookback),0)-1, -1):\n        try:\n            block=_rpc("getBlock",[candidate,{"commitment":"finalized","transactionDetails":"signatures","rewards":False,"maxSupportedTransactionVersion":0}],timeout_seconds)\n        except Exception:\n            block=None\n        if isinstance(block,dict):\n            slot=candidate; break\n    if block is None or slot is None: raise RuntimeError("no finalized Solana block found inside bounded lookback")\n    signatures=tuple(block.get("signatures") or ())\n    bt=block.get("blockTime")\n    observed=datetime.fromtimestamp(int(bt),timezone.utc).isoformat() if bt is not None else utcnow_iso()\n    payload={\n        "slot":slot,\n        "block_height":block.get("blockHeight"),\n        "block_time":bt,\n        "blockhash":block.get("blockhash"),\n        "previous_blockhash":block.get("previousBlockhash"),\n        "parent_slot":block.get("parentSlot"),\n        "signature_count":len(signatures),\n        "sample_signatures":signatures[:10],\n    }\n    o=build_solana_onchain_observation(\n        source_id=f"solana:mainnet:block:{slot}:{block.get(\'blockhash\')}",\n        observation_type="finalized_block_activity",subject=f"Solana finalized block {slot}",\n        observed_at=observed,payload=payload)\n    if not validate_solana_onchain_observation(o): raise RuntimeError("Solana block-activity validation failed")\n    return (o,)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_149_solana_finalized_block_activity_acquisition as m\nclass T(unittest.TestCase):\n    def test_block(self):\n        def rpc(method,params,timeout):\n            if method=="getSlot": return 1000\n            if method=="getBlock": return {"blockHeight":900,"blockTime":1787970000,"blockhash":"abc","previousBlockhash":"def","parentSlot":999,"signatures":["s1","s2","s3"]}\n        with patch.object(m,"_rpc",side_effect=rpc):\n            r=m.acquire_solana_finalized_block_activity()\n        print("[BLOCK_SLOT]",r[0].payload["slot"]); print("[SIGNATURE_COUNT]",r[0].payload["signature_count"])\n        self.assertEqual(r[0].payload["signature_count"],3)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-149 Solana finalized block-activity acquisition certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_149_solana_finalized_block_activity_acquisition import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-149 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
