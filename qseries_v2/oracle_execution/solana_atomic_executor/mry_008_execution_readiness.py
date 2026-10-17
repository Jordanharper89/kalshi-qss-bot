from __future__ import annotations
import copy

CANARY_LAMPORTS=10_000_000

def _programs(rt,token):
    row=rt.q25.q23.worker().warm(token)
    return str(row["program"]),str(rt.q87.c.TOKEN)

def prepare_forward(rt,pair):
    token=str(pair.token)
    pool=str(pair.pump_pool)
    token_program,wsol_program=_programs(rt,token)

    ixs,_=rt.q87.las.q59.native_pump_buy_ixs(
        rt.USER,
        pool,
        CANARY_LAMPORTS,
    )

    pump_index=rt.pump_ix_position(ixs)

    pump_template={
        "pump_pool":pool,
        "instructions":[copy.deepcopy(x) for x in ixs],
        "pump_index":int(pump_index),
        "template_quote_lamports":CANARY_LAMPORTS,
    }

    tx=str(pair.token_x)
    ty=str(pair.token_y)
    programs={
        token:token_program,
        rt.q87.c.WSOL:wsol_program,
    }

    tx_prog=programs.get(tx)
    ty_prog=programs.get(ty)

    if not tx_prog or not ty_prog:
        raise RuntimeError("TOKEN_PROGRAM_NOT_READY")

    user=rt.USER
    mpool=str(pair.meteora_pool)

    ux=rt.q87.c.ata(user,tx,tx_prog)
    uy=rt.q87.c.ata(user,ty,ty_prog)

    rx=rt.q87.c.pda(
        [rt.q87.c.b58d(mpool),rt.q87.c.b58d(tx)],
        rt.q87.c.DLMM,
    )
    ry=rt.q87.c.pda(
        [rt.q87.c.b58d(mpool),rt.q87.c.b58d(ty)],
        rt.q87.c.DLMM,
    )
    oracle=rt.q87.c.pda(
        [b"oracle",rt.q87.c.b58d(mpool)],
        rt.q87.c.DLMM,
    )
    bitmap=rt.q87.c.pda(
        [b"bitmap",rt.q87.c.b58d(mpool)],
        rt.q87.c.DLMM,
    )
    event=rt.q87.c.pda(
        [b"__event_authority"],
        rt.q87.c.DLMM,
    )

    bitmap_account=rt.q87.c.rpc(
        "getAccountInfo",
        [bitmap,{"encoding":"base64","commitment":"processed"}],
    )

    bitmap_key=(
        bitmap
        if isinstance(bitmap_account,dict)
        and bitmap_account.get("value")
        else rt.q87.c.DLMM
    )

    if tx==rt.q87.c.WSOL:
        source=uy
        dest=ux
        swap_for_y=False
    elif ty==rt.q87.c.WSOL:
        source=ux
        dest=uy
        swap_for_y=True
    else:
        raise RuntimeError("DLMM_NOT_WSOL")

    fixed=[
        (mpool,False,True),
        (bitmap_key,False,True),
        (rx,False,True),
        (ry,False,True),
        (source,False,True),
        (dest,False,True),
        (tx,False,False),
        (ty,False,False),
        (oracle,False,True),
        (rt.q87.c.DLMM,False,True),
        (user,True,False),
        (tx_prog,False,False),
        (ty_prog,False,False),
        (event,False,False),
        (rt.q87.c.DLMM,False,False),
    ]

    meteora_template={
        "pool":mpool,
        "token_x":tx,
        "token_y":ty,
        "swap_for_y":bool(swap_for_y),
        "arrays":[
            (int(a[0]),str(a[1]))
            for a in list(pair.arrays)
        ],
        "fixed_accounts":fixed,
    }

    rt.q18.worker().warm(pool)

    return (
        pump_template,
        meteora_template,
        token_program,
    )

def install_forward(rt,pair):
    token=str(pair.token)
    pump,meteora,program=prepare_forward(rt,pair)

    rt.TEMPLATES[token]=pump
    rt.METEORA_TEMPLATES[token]=meteora

    print(
        "[MRIYA_EXECUTION_READY] "
        "token=%s forward=TRUE "
        "reverse=UNCHANGED quote_lamports=%d"
        %(token[:10],CANARY_LAMPORTS),
        flush=True,
    )

    return {
        "token":token,
        "program":program,
        "forward":True,
    }
