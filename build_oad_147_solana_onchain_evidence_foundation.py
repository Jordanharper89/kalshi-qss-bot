from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_147_SOLANA_ONCHAIN_EVIDENCE_FOUNDATION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_147_solana_onchain_evidence_foundation.py'; test=r/'test_oad_147_solana_onchain_evidence_foundation.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-147 SOLANA ON-CHAIN EVIDENCE FOUNDATION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_068_exact_postgresql_independent_readback.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
    oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
    if 147>=150:
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified")
        print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom hashlib import sha256\nfrom typing import Any,Mapping\nimport json\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nEXECUTION_AUTHORITY=False\nPROVIDER="api.mainnet.solana.com"\nSOURCE_CLASS="underlying_chain_state"\nINDEPENDENT_EVIDENCE=True\nMAINNET_RPC="https://api.mainnet.solana.com"\n\n@dataclass(frozen=True)\nclass SolanaOnchainObservation:\n    source_id:str\n    provider:str\n    chain:str\n    network:str\n    observation_type:str\n    subject:str\n    observed_at:str\n    source_url:str\n    payload:Mapping[str,Any]\n    provenance_hash:str\n    source_class:str=SOURCE_CLASS\n    independent_evidence:bool=True\n    execution_authority:bool=False\n\ndef utcnow_iso():\n    return datetime.now(timezone.utc).isoformat()\n\ndef build_solana_onchain_observation(*,source_id,observation_type,subject,observed_at,payload,source_url=MAINNET_RPC):\n    if source_url != MAINNET_RPC:\n        raise ValueError("only official Solana mainnet public RPC admitted by this foundation")\n    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)\n    ph=sha256((PROVIDER+"|"+source_url+"|"+canonical).encode()).hexdigest()\n    return SolanaOnchainObservation(\n        str(source_id),PROVIDER,"solana","mainnet",str(observation_type),str(subject),\n        str(observed_at),source_url,dict(payload),ph,SOURCE_CLASS,True,False\n    )\n\ndef validate_solana_onchain_observation(o):\n    return (\n        o.provider==PROVIDER and o.chain=="solana" and o.network=="mainnet"\n        and o.source_class==SOURCE_CLASS and o.independent_evidence is True\n        and o.execution_authority is False and o.source_url==MAINNET_RPC\n        and len(o.provenance_hash)==64\n    )\n'); write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_147_solana_onchain_evidence_foundation import build_solana_onchain_observation,validate_solana_onchain_observation\nclass T(unittest.TestCase):\n    def test_foundation(self):\n        o=build_solana_onchain_observation(source_id="solana:slot:1",observation_type="chain_state",subject="mainnet slot",observed_at="2026-08-29T00:00:00+00:00",payload={"slot":1})\n        self.assertTrue(validate_solana_onchain_observation(o)); self.assertTrue(o.independent_evidence); self.assertFalse(o.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-147 Solana on-chain evidence foundation certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_147_solana_onchain_evidence_foundation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-147 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
