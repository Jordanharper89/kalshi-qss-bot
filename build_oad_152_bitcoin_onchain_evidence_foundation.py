from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_152_BITCOIN_ONCHAIN_EVIDENCE_FOUNDATION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_152_bitcoin_onchain_evidence_foundation.py'; test=r/'test_oad_152_bitcoin_onchain_evidence_foundation.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-152 BITCOIN ON-CHAIN EVIDENCE FOUNDATION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_068_exact_postgresql_independent_readback.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    if 152>=155:
        canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
        oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified"); print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom hashlib import sha256\nfrom typing import Any,Mapping\nimport json\nREAD_ONLY=True; PROBABILITY_ENABLED=False; EXECUTION_AUTHORITY=False\nCHAIN="bitcoin"; NETWORK="mainnet"\nSOURCE_CLASS="underlying_chain_state_observation"; INDEPENDENT_EVIDENCE=True\nBLOCKSTREAM_PROVIDER="blockstream.info"; MEMPOOL_PROVIDER="mempool.space"\nALLOWED_PROVIDERS=(BLOCKSTREAM_PROVIDER,MEMPOOL_PROVIDER)\n@dataclass(frozen=True)\nclass BitcoinOnchainObservation:\n    source_id:str; provider:str; provider_role:str; chain:str; network:str\n    observation_type:str; subject:str; observed_at:str; source_url:str\n    payload:Mapping[str,Any]; provenance_hash:str\n    source_class:str=SOURCE_CLASS; independent_evidence:bool=True; execution_authority:bool=False\ndef utcnow_iso(): return datetime.now(timezone.utc).isoformat()\ndef build_bitcoin_onchain_observation(*,source_id,provider,provider_role,observation_type,subject,observed_at,source_url,payload):\n    if provider not in ALLOWED_PROVIDERS: raise ValueError("unapproved Bitcoin public chain observer")\n    if provider not in source_url: raise ValueError("Bitcoin source_url/provider mismatch")\n    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)\n    ph=sha256((provider+"|"+source_url+"|"+canonical).encode()).hexdigest()\n    return BitcoinOnchainObservation(str(source_id),str(provider),str(provider_role),CHAIN,NETWORK,str(observation_type),str(subject),str(observed_at),str(source_url),dict(payload),ph,SOURCE_CLASS,True,False)\ndef validate_bitcoin_onchain_observation(o):\n    return (o.provider in ALLOWED_PROVIDERS and o.chain==CHAIN and o.network==NETWORK and o.source_class==SOURCE_CLASS and o.independent_evidence is True and o.execution_authority is False and o.provider in o.source_url and len(o.provenance_hash)==64)\n'); write(test,'import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_152_bitcoin_onchain_evidence_foundation import build_bitcoin_onchain_observation,validate_bitcoin_onchain_observation\nclass T(unittest.TestCase):\n    def test_foundation(self):\n        o=build_bitcoin_onchain_observation(source_id="bitcoin:tip:1",provider="blockstream.info",provider_role="public_chain_observer",observation_type="chain_tip",subject="Bitcoin mainnet tip",observed_at="2026-08-29T00:00:00+00:00",source_url="https://blockstream.info/api/blocks/tip/height",payload={"height":1})\n        self.assertTrue(validate_bitcoin_onchain_observation(o)); self.assertTrue(o.independent_evidence); self.assertFalse(o.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-152 Bitcoin on-chain evidence foundation certified")\n    print("[PASS] public observer provenance explicit; no provider mislabeled as Bitcoin itself")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_152_bitcoin_onchain_evidence_foundation import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-152 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
