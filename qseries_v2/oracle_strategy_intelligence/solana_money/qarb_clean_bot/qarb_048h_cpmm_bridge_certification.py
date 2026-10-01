from __future__ import annotations
import json,subprocess,sys
from pathlib import Path

def main():
    root=Path.cwd()
    capture=root/"run_qarb_030_mriya_dex_instruction_account_capture.py"
    if capture.is_file():
        print("[REFRESH] running certified QARB-030 Mriya exact instruction capture",flush=True)
        rc=subprocess.call([sys.executable,str(capture)])
        if rc!=0:
            raise SystemExit("[FAIL] QARB-030 refresh failed rc=%d"%rc)

    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_mriya_bridge as b

    desc=b.discover(root)
    print("[CPMM_DESCRIPTOR_COUNT]",len(desc))
    for x in desc[:20]:
        print("[CPMM_DESCRIPTOR] pool=%s token_a=%s token_b=%s vault_a=%s vault_b=%s"%(
            x.pool[:12],x.token_a[:12],x.token_b[:12],x.vault_a[:12],x.vault_b[:12]))

    state=m.prepare(root)
    cap=m.capability(state)
    cpmm_eps=[]
    for token,eps in state.get("eps",{}).items():
        for ep in eps:
            if getattr(ep,"venue",None)=="RAYDIUM_CPMM":
                cpmm_eps.append((token,ep))
    print("[CAPABILITY]",json.dumps(cap,sort_keys=True))
    print("[CPMM_HYDRATED_STATES]",len(state.get("cstates",[])))
    print("[CPMM_ENDPOINT_COUNT]",len(cpmm_eps))
    for token,ep in cpmm_eps:
        print("[CPMM_ENDPOINT] token=%s pool=%s"%(token[:12],ep.pool[:12]))
    print("[ADDRESSES]",len(state.get("addresses",[])))
    print("[MODE] READ_ONLY=True execution_authority=FALSE")
    if not desc:
        raise SystemExit("[HOLD] no exact Mriya CPMM descriptors")
    if not state.get("cstates"):
        raise SystemExit("[HOLD] descriptors found but no CPMM state hydrated")
    if not cpmm_eps:
        raise SystemExit("[HOLD] CPMM hydrated but no WSOL-priced CPMM endpoint; next boundary is multi-base route graph")
    print("[PASS] RAYDIUM_CPMM physically entered merged live pricing graph")

if __name__=="__main__":main()
