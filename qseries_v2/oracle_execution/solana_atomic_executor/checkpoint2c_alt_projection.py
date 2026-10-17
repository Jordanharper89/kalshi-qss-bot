from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r

FAKE_ALT="11111111111111111111111111111111"

def main():
    state,_=r.q25.prepare_once(".")
    r.q25.bind_cached_state(state)
    warmed=r.install_proven_hot_math(state)
    _,r.USER=r.q87.c.sim_identity()
    r.prebuild_templates(state,r.USER)
    r.prebuild_meteora_templates(state,r.USER,warmed)

    for p in state.get("pairs") or []:
        if str(p.token) not in r.READY_TOKENS:
            continue

        r.q18.worker().warm(str(p.pump_pool))
        snap=r.immutable_snapshot(p)

        rows=r.q18.exact_snapshot_opportunities(snap,0.001)
        opp=next(x for x in rows if x["direction"]=="PUMP_TO_METEORA")
        route=r.same_snapshot_route(r.USER,snap,opp)

        full=next(
            x for x in r.q87.repaired_candidates(route)
            if x["name"]=="FULL"
        )

        ixs=full["instructions"]
        programs={x["programId"] for x in ixs}
        addresses=[]
        seen=set()

        for ix in ixs:
            for a in ix.get("accounts") or []:
                pk=a["pubkey"]
                if pk==r.USER or pk in programs or a["isSigner"] or pk in seen:
                    continue
                seen.add(pk)
                addresses.append(pk)

        addresses=addresses[:8]

        if len(addresses)<4:
            raise RuntimeError("ALT_ELIGIBLE_ADDRESSES_TOO_FEW")

        original=r.q87.c.alt_accounts
        r.q87.c.alt_accounts=lambda keys:{
            FAKE_ALT:[r.q87.c.b58d(x) for x in addresses]
        }

        try:
            bh=r.q87.c.rpc("getLatestBlockhash",[{"commitment":"processed"}])["value"]["blockhash"]
            msg,raw=r.q87.c.compile_v0(r.USER,ixs,[FAKE_ALT],bh)
        finally:
            r.q87.c.alt_accounts=original

        print("[CHECKPOINT2C_ALT_ADDRESSES] count=%d"%len(addresses),flush=True)
        for i,x in enumerate(addresses):
            print("[CHECKPOINT2C_ALT] index=%d pubkey=%s"%(i,x),flush=True)

        print("[CHECKPOINT2C_PROJECTED_BYTES] %d"%len(raw),flush=True)

        if len(raw)>1232:
            raise RuntimeError("ALT_PROJECTION_STILL_OVERSIZE:%d"%len(raw))

        print("[CHECKPOINT2C_ALT_PROJECTION_PASS] bytes=%d savings_at_least=%d"%(
            len(raw),1296-len(raw)),flush=True)
        return 0

    raise RuntimeError("NO_READY_FORWARD_PAIR")

if __name__=="__main__":
    raise SystemExit(main())
