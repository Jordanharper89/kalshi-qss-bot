from __future__ import annotations

import argparse
import base64
import copy

from . import checkpoint25_expanded_live_universe_cutover as c25
from . import checkpoint7_live_90s_fee_ranked_watch as c7
from . import runtime as r

FORWARD="PUMP_TO_METEORA"
REVERSE="METEORA_TO_PUMP"

ATA_PROGRAM="ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
SYSTEM_PROGRAM="11111111111111111111111111111111"
DLMM_PROGRAM="LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"

ORIGINAL_ROUTE=None


def _pubkey(row):
    return str((row or {}).get("pubkey") or "")


def _exact_dlmm_ix(route):
    direct=route.get("meteora_ix")
    if isinstance(direct,dict) and str(direct.get("programId") or "")==DLMM_PROGRAM:
        return direct

    found=[]
    for _,ixs in list(route.get("original_candidates") or []):
        for ix in list(ixs or []):
            if str(ix.get("programId") or "")==DLMM_PROGRAM:
                found.append(ix)

    if not found:
        raise RuntimeError("CHECKPOINT26_DLMM_INSTRUCTION_MISSING")

    first=found[0]
    key=(
        str(first.get("data") or ""),
        tuple(_pubkey(x) for x in list(first.get("accounts") or [])),
    )

    for ix in found[1:]:
        other=(
            str(ix.get("data") or ""),
            tuple(_pubkey(x) for x in list(ix.get("accounts") or [])),
        )
        if other!=key:
            raise RuntimeError("CHECKPOINT26_DLMM_CANDIDATE_DRIFT")

    return first


def _token_program_for_exact_ata(user,mint,exact_ata):
    matches=[]
    for program in (r.q87.c.TOKEN,r.q87.c.TOKEN22):
        derived=str(r.q87.c.ata(user,mint,program))
        if derived==str(exact_ata):
            matches.append(str(program))

    if len(matches)!=1:
        raise RuntimeError(
            "CHECKPOINT26_EXACT_ATA_PROGRAM_MATCH:"
            +str(len(matches))
            +":mint="+str(mint)
            +":ata="+str(exact_ata)
        )

    return matches[0]


def _create_idempotent_ix(user,ata,mint,token_program):
    return {
        "programId":ATA_PROGRAM,
        "accounts":[
            {"pubkey":str(user),"isSigner":True,"isWritable":True},
            {"pubkey":str(ata),"isSigner":False,"isWritable":True},
            {"pubkey":str(user),"isSigner":False,"isWritable":False},
            {"pubkey":str(mint),"isSigner":False,"isWritable":False},
            {"pubkey":SYSTEM_PROGRAM,"isSigner":False,"isWritable":False},
            {"pubkey":str(token_program),"isSigner":False,"isWritable":False},
        ],
        "data":base64.b64encode(b"\x01").decode(),
    }


def _existing_exact_create_before(ixs,dlmm_index,exact_ata):
    for ix in list(ixs[:dlmm_index]):
        if str(ix.get("programId") or "")!=ATA_PROGRAM:
            continue
        accounts=list(ix.get("accounts") or [])
        if len(accounts)>=2 and _pubkey(accounts[1])==str(exact_ata):
            return True
    return False


def _inject_before_dlmm(ixs,create_ix,exact_ata):
    out=[copy.deepcopy(x) for x in list(ixs or [])]
    positions=[
        i for i,ix in enumerate(out)
        if str(ix.get("programId") or "")==DLMM_PROGRAM
    ]
    if len(positions)!=1:
        raise RuntimeError("CHECKPOINT26_DLMM_POSITION_COUNT:"+str(len(positions)))

    pos=positions[0]
    if not _existing_exact_create_before(out,pos,exact_ata):
        out.insert(pos,copy.deepcopy(create_ix))

    new_positions=[
        i for i,ix in enumerate(out)
        if str(ix.get("programId") or "")==DLMM_PROGRAM
    ]
    if len(new_positions)!=1:
        raise RuntimeError("CHECKPOINT26_DLMM_POST_INSERT_COUNT")

    dlmm_pos=new_positions[0]
    if not _existing_exact_create_before(out,dlmm_pos,exact_ata):
        raise RuntimeError("CHECKPOINT26_EXACT_ATA_NOT_BEFORE_DLMM")

    return out


def _bind_exact_output_ata(user,snap,opportunity,route):
    direction=str(opportunity.get("direction") or "")
    if direction not in (FORWARD,REVERSE):
        raise RuntimeError("CHECKPOINT26_DIRECTION_UNSUPPORTED:"+direction)

    token=str(snap.get("token") or "")
    if not token:
        raise RuntimeError("CHECKPOINT26_TOKEN_MISSING")

    mint=str(r.q87.c.WSOL) if direction==FORWARD else token

    dlmm=_exact_dlmm_ix(route)
    accounts=list(dlmm.get("accounts") or [])
    if len(accounts)<6:
        raise RuntimeError("CHECKPOINT26_DLMM_ACCOUNTS_SHORT:"+str(len(accounts)))

    exact_ata=_pubkey(accounts[5])
    if not exact_ata:
        raise RuntimeError("CHECKPOINT26_USER_TOKEN_OUT_EMPTY")

    token_program=_token_program_for_exact_ata(user,mint,exact_ata)
    create_ix=_create_idempotent_ix(user,exact_ata,mint,token_program)

    original=list(route.get("original_candidates") or [])
    if not original:
        raise RuntimeError("CHECKPOINT26_CANDIDATES_MISSING")

    rebound=[]
    for row in original:
        if not isinstance(row,(list,tuple)) or len(row)!=2:
            raise RuntimeError("CHECKPOINT26_CANDIDATE_SHAPE")
        name,ixs=row
        rebound.append((
            name,
            _inject_before_dlmm(ixs,create_ix,exact_ata),
        ))

    route=dict(route)
    route["original_candidates"]=rebound
    route["meteora_ix"]=copy.deepcopy(dlmm)
    route["checkpoint26_output_ata"]={
        "direction":direction,
        "mint":mint,
        "ata":exact_ata,
        "token_program":token_program,
        "create_idempotent":True,
        "before_dlmm":True,
    }

    print(
        "[CHECKPOINT26_ATA_BOUND] "
        "dir=%s dest=%s mint=%s token_program=%s "
        "candidates=%d before_dlmm=True"
        %(
            direction,
            exact_ata[:12],
            mint[:12],
            token_program[:12],
            len(rebound),
        ),
        flush=True,
    )

    return route


def _route_with_exact_output_ata(user,snap,opportunity):
    route=ORIGINAL_ROUTE(user,snap,opportunity)
    return _bind_exact_output_ata(user,snap,opportunity,route)


def main():
    global ORIGINAL_ROUTE

    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=3600.0)
    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError("CHECKPOINT26_SECONDS_MUST_BE_POSITIVE")

    old_route=c7._route
    ORIGINAL_ROUTE=old_route

    try:
        c7._route=_route_with_exact_output_ata

        print(
            "[CHECKPOINT26_ACTIVATION] "
            "exact_dlmm_output_ata_before_swap=True "
            "create_idempotent=True token2022_aware=True",
            flush=True,
        )
        print(
            "[CHECKPOINT26_BINDING] "
            "user_token_out=exact_dlmm_account_5 "
            "ata_program_derived_by_exact_address_match",
            flush=True,
        )
        print(
            "[CHECKPOINT26_ORDER] "
            "CreateIdempotent -> DLMM Swap for every candidate",
            flush=True,
        )
        print(
            "[CHECKPOINT26_HOT_PATH] ata_derivation=local rpc_added=False",
            flush=True,
        )
        print(
            "[CHECKPOINT26_CHAIN] checkpoint25 -> pair route -> "
            "exact output ATA create -> canonical ALT -> "
            "real fee -> freshness -> signed sim",
            flush=True,
        )
        print("[BROADCAST] disabled",flush=True)

        return c25.main()

    finally:
        c7._route=old_route
        print("[CHECKPOINT26_PATCH_RESTORED] true",flush=True)


if __name__=="__main__":
    raise SystemExit(main())
