from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_153_BITCOIN_BLOCKSTREAM_CHAIN_TIP_BLOCK_ACQUISITION_V1'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/'oad_153_bitcoin_blockstream_chain_tip_block_acquisition.py'; test=r/'test_oad_153_bitcoin_blockstream_chain_tip_block_acquisition.py'; init=pkg/"__init__.py"
    print("="*112); print(" OAD-153 BITCOIN BLOCKSTREAM CHAIN TIP AND BLOCK ACQUISITION INSTALLER"); print("="*112); print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for d in ['oad_152_bitcoin_onchain_evidence_foundation.py']:
        if not (pkg/d).is_file(): raise RuntimeError("Required dependency missing: "+d)
        print("[PASS] dependency verified:",d)
    if 153>=155:
        canonical=r/"qseries_v2"/"oracle_intelligence"/"live_acquisition"/"oracle_live_read_only_acquisition_runtime.py"
        oph=r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
        if not canonical.is_file(): raise RuntimeError("Canonical observation runtime missing")
        if not oph.is_file(): raise RuntimeError("OPH-019 universal PostgreSQL queue missing")
        print("[PASS] exact canonical observation runtime verified"); print("[PASS] OPH-019 universal PostgreSQL queue verified")
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,'from __future__ import annotations\nimport json\nfrom urllib.request import Request,urlopen\nfrom .oad_152_bitcoin_onchain_evidence_foundation import build_bitcoin_onchain_observation,validate_bitcoin_onchain_observation,utcnow_iso\nBASE="https://blockstream.info/api"; PROVIDER="blockstream.info"\nREAD_ONLY=True; PROBABILITY_ENABLED=False; EXECUTION_AUTHORITY=False\ndef _get_text(url,timeout_seconds):\n    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0 read-only","Accept":"text/plain,application/json"})\n    with urlopen(req,timeout=timeout_seconds) as r: return r.read().decode("utf-8").strip()\ndef _get_json(url,timeout_seconds): return json.loads(_get_text(url,timeout_seconds))\ndef acquire_bitcoin_blockstream_chain_observations(timeout_seconds=20.0):\n    height=int(_get_text(BASE+"/blocks/tip/height",timeout_seconds))\n    tip_hash=_get_text(BASE+"/blocks/tip/hash",timeout_seconds)\n    block=_get_json(BASE+"/block/"+tip_hash,timeout_seconds); now=utcnow_iso()\n    tip=build_bitcoin_onchain_observation(source_id=f"bitcoin:blockstream:tip:{height}:{tip_hash}",provider=PROVIDER,provider_role="public_chain_observer",observation_type="chain_tip",subject="Bitcoin mainnet chain tip",observed_at=now,source_url=BASE+"/blocks/tip/height",payload={"height":height,"tip_hash":tip_hash})\n    blk=build_bitcoin_onchain_observation(source_id=f"bitcoin:blockstream:block:{height}:{tip_hash}",provider=PROVIDER,provider_role="public_chain_observer",observation_type="tip_block_activity",subject=f"Bitcoin mainnet block {height}",observed_at=now,source_url=BASE+"/block/"+tip_hash,payload={"height":block.get("height"),"block_hash":block.get("id") or tip_hash,"timestamp":block.get("timestamp"),"tx_count":block.get("tx_count"),"size":block.get("size"),"weight":block.get("weight"),"merkle_root":block.get("merkle_root"),"previousblockhash":block.get("previousblockhash"),"difficulty":block.get("difficulty")})\n    if not validate_bitcoin_onchain_observation(tip) or not validate_bitcoin_onchain_observation(blk): raise RuntimeError("Bitcoin Blockstream observation validation failed")\n    return (tip,blk)\n'); write(test,'import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_153_bitcoin_blockstream_chain_tip_block_acquisition as m\nclass T(unittest.TestCase):\n    def test_mapping(self):\n        def text(url,timeout):\n            if url.endswith("/height"): return "900000"\n            if url.endswith("/hash"): return "abc"\n            raise AssertionError(url)\n        block={"id":"abc","height":900000,"timestamp":1787970000,"tx_count":3000,"size":1500000,"weight":3990000,"merkle_root":"mr","previousblockhash":"prev","difficulty":100}\n        with patch.object(m,"_get_text",side_effect=text),patch.object(m,"_get_json",return_value=block):\n            r=m.acquire_bitcoin_blockstream_chain_observations()\n        print("[OBSERVATIONS]",len(r)); print("[TIP_HEIGHT]",r[0].payload["height"]); print("[TX_COUNT]",r[1].payload["tx_count"])\n        self.assertEqual(len(r),2); self.assertEqual(r[1].payload["tx_count"],3000)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-153 Bitcoin Blockstream chain-tip/block acquisition certified")\n')
        lines=init.read_text(encoding="utf-8").splitlines(); exp="from .oad_153_bitcoin_blockstream_chain_tip_block_acquisition import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r)); print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE"); print("[DONE] OAD-153 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
