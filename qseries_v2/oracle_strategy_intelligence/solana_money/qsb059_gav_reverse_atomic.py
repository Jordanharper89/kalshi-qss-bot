from __future__ import annotations
import base64,json,os,struct
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

CASE_REPORT="runtime_state/qseries/qsb058_gav_profitable_case/report.json"
MIN_NET_BPS=float(os.getenv("QSB_059_MIN_NET_BPS","20"))
SLIPPAGE_BPS=int(os.getenv("QSB_059_SLIPPAGE_BPS","20"))

def load_case(root):
    p=Path(root)/CASE_REPORT
    if not p.is_file():
        raise RuntimeError("QSB058_REPORT_MISSING")
    r=json.loads(p.read_text(encoding="utf-8"))
    b=r.get("binding") or {}
    if not b.get("resolved") or not b.get("current_binding_ok"):
        raise RuntimeError("QSB058_BINDING_NOT_READY")
    return r,b

def dlmm_reverse_ix(user,meta,input_amount,quote_result):
    pool=meta["address"]
    tx_prog=c.account(meta["token_x"])[1]
    ty_prog=c.account(meta["token_y"])[1]
    ux=c.ata(user,meta["token_x"],tx_prog)
    uy=c.ata(user,meta["token_y"],ty_prog)
    rx=c.pda([c.b58d(pool),c.b58d(meta["token_x"])],c.DLMM)
    ry=c.pda([c.b58d(pool),c.b58d(meta["token_y"])],c.DLMM)
    oracle=c.pda([b"oracle",c.b58d(pool)],c.DLMM)
    bitmap=c.pda([b"bitmap",c.b58d(pool)],c.DLMM)
    try:
        c.account(bitmap)
        bitmap_key=bitmap
    except Exception:
        bitmap_key=c.DLMM
    ev=c.pda([b"__event_authority"],c.DLMM)

    # Reverse direction is token -> WSOL.
    if meta["token_x"]==c.WSOL:
        source=uy;dest=ux
        swap_for_y=False
    elif meta["token_y"]==c.WSOL:
        source=ux;dest=uy
        swap_for_y=True
    else:
        raise RuntimeError("DLMM_PAIR_NOT_WSOL")

    if bool(quote_result.get("swap_for_y"))!=swap_for_y:
        raise RuntimeError("DLMM_QUOTE_DIRECTION_MISMATCH")

    ac=[
      (pool,False,True),(bitmap_key,False,True),(rx,False,True),(ry,False,True),
      (source,False,True),(dest,False,True),
      (meta["token_x"],False,False),(meta["token_y"],False,False),(oracle,False,True),
      (c.DLMM,False,True),(user,True,False),(tx_prog,False,False),(ty_prog,False,False),
      (ev,False,False),(c.DLMM,False,False)
    ]

    arr=c.dlmm_arrays(pool)
    crossed=max(1,int(quote_result.get("bins_crossed") or 1))
    n=min(len(arr),max(1,(crossed+69)//70))
    chosen=arr[:n] if swap_for_y else list(reversed(arr))[:n]
    ac += [(x[1],False,True) for x in chosen]

    min_out=int(quote_result["raw_out"])*(10000-SLIPPAGE_BPS)//10000
    data=bytes([248,198,158,145,225,117,135,200])+struct.pack("<QQ",int(input_amount),min_out)
    return {
        "programId":c.DLMM,
        "accounts":[{"pubkey":p,"isSigner":s,"isWritable":w} for p,s,w in ac],
        "data":base64.b64encode(data).decode(),
    }

MRIYA_WALLET="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
COMPUTE_BUDGET="ComputeBudget111111111111111111111111111111"
MEMO_PROGRAMS={
    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
    "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo",
}

def recent_mriya_alt_keys(limit=24):
    out=[];seen=set()
    try:
        sigs=c.rpc("getSignaturesForAddress",[MRIYA_WALLET,{"limit":int(limit),"commitment":"processed"}]) or []
    except Exception:
        return []
    for row in sigs:
        sig=row.get("signature")
        if not sig or row.get("err") is not None:
            continue
        try:
            tx=c.rpc("getTransaction",[sig,{"encoding":"json","commitment":"processed","maxSupportedTransactionVersion":0}])
        except Exception:
            continue
        msg=(((tx or {}).get("transaction") or {}).get("message") or {})
        for lk in msg.get("addressTableLookups") or []:
            k=lk.get("accountKey")
            if k and k not in seen:
                seen.add(k);out.append(k)
        if len(out)>=16:
            break
    return out

def compact_ixs(ixs):
    import base64
    result=[];compute={}
    for ix in ixs:
        pid=ix.get("programId")
        if pid in MEMO_PROGRAMS:
            continue
        if pid==COMPUTE_BUDGET:
            try:
                raw=base64.b64decode(ix.get("data") or "")
                tag=raw[0] if raw else -1
            except Exception:
                tag=-1
            compute[tag]=ix
            continue
        result.append(ix)
    return [compute[k] for k in sorted(compute)] + result

def compile_compact(user,ixs,base_alts,blockhash):
    attempts=[]
    alt_sets=[
        list(dict.fromkeys(base_alts)),
        list(dict.fromkeys(list(base_alts)+recent_mriya_alt_keys())),
    ]
    last=None
    for idx,alts in enumerate(alt_sets,1):
        try:
            msg,raw=c.compile_v0(user,compact_ixs(ixs),alts,blockhash)
            print("[TX_SIZE] attempt=%d bytes=%d alts=%d"%(idx,len(raw),len(alts)),flush=True)
            return msg,raw,alts
        except RuntimeError as e:
            last=e
            if not str(e).startswith("ATOMIC_TX_TOO_LARGE:"):
                raise
            size=int(str(e).split(":")[-1])
            attempts.append({"attempt":idx,"size":size,"alts":len(alts)})
            print("[TX_SIZE] attempt=%d bytes=%d TOO_LARGE alts=%d"%(idx,size,len(alts)),flush=True)
    raise RuntimeError("ATOMIC_TX_TOO_LARGE_AFTER_COMPACTION:"+str(attempts)+" last="+str(last))


def native_pump_buy_ixs(user,pump_pool,start_lamports):
    import json,os,shutil,subprocess
    from pathlib import Path

    b=Path.cwd()/(
        "qseries_v2/oracle_strategy_intelligence/"
        "solana_money/qsb059d_pump_native"
    )

    node_exe=shutil.which("node")

    # Windows subprocess(shell=False) must execute npm.cmd,
    # not the extensionless npm shim.
    npm_exe=(
        shutil.which("npm.cmd")
        if os.name=="nt"
        else shutil.which("npm")
    )

    if node_exe is None:
        raise RuntimeError(
            "NODE_MISSING"
        )

    if npm_exe is None:
        raise RuntimeError(
            "NPM_EXECUTABLE_MISSING"
        )

    marker=(
        b/
        "node_modules/@pump-fun/"
        "pump-swap-sdk/package.json"
    )

    if not marker.is_file():
        p=subprocess.run(
            [
                npm_exe,
                "install",
                "--silent",
                "--no-audit",
                "--no-fund",
            ],
            cwd=b,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=240
        )

        if p.returncode!=0:
            raise RuntimeError(
                "PUMPSWAP_SDK_INSTALL_FAILED:"
                +p.stdout[-2000:]
            )

    req={
        "rpc":
            os.getenv(
                "SOLANA_RPC_URL",
                "https://api.mainnet-beta.solana.com"
            ),

        "user":
            user,

        "pool":
            pump_pool,

        "quoteLamports":
            int(start_lamports),

        "slippagePct":
            SLIPPAGE_BPS/100.0
    }

    p=subprocess.run(
        [
            node_exe,
            "build_buy_ix.mjs"
        ],
        cwd=b,
        input=json.dumps(req),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=45
    )

    if p.returncode!=0:
        raise RuntimeError(
            "PUMP_NATIVE_NODE_FAILED:"
            +p.stderr[-2000:]
        )

    try:
        j=json.loads(
            p.stdout.strip()
            .splitlines()[-1]
        )

    except Exception:
        raise RuntimeError(
            "PUMP_NATIVE_BAD_JSON:"
            +p.stdout[-2000:]
        )

    if not j.get("ok"):
        raise RuntimeError(
            "PUMP_NATIVE_BUILD_FAILED:"
            +str(j.get("reason"))
        )

    ixs=j.get(
        "instructions"
    ) or []

    if not any(
        ix.get("programId")==c.PUMP
        for ix in ixs
    ):
        raise RuntimeError(
            "PUMP_NATIVE_PROGRAM_IX_MISSING"
        )


    for px in ixs:
        if px.get("programId")!=c.PUMP:
            continue
        aa=list(px.get("accounts") or [])
        print("[SAE007B_PUMP_ACCOUNTS] total=%d"%len(aa),flush=True)
        for i,a in enumerate(aa):
            role=("FIXED" if i<23 else "REMAINING_%d"%(i-22))
            print("[SAE007B_ACCOUNT] index=%d number=%d role=%s pubkey=%s signer=%s writable=%s"%(
                i,i+1,role,a.get("pubkey"),a.get("isSigner"),a.get("isWritable")),flush=True)
    return (
        ixs,
        int(
            j.get("baseOut")
            or 0
        )
    )


COMPUTE_BUDGET="ComputeBudget111111111111111111111111111111"
MEMO_PROGRAMS={
    "MemoSq4gqABAXKb96qn8TysNcWxMyWCqXgDLGmfcHr",
    "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo",
}

def _ix_tag(ix):
    import base64
    try:
        d=base64.b64decode(ix.get("data") or "")
        return d[0] if d else None
    except Exception:
        return None

def _minimal_helper(ix,phase):
    pid=ix.get("programId")
    if pid in MEMO_PROGRAMS or pid==COMPUTE_BUDGET:
        return False
    if pid==c.SYSTEM:
        return phase=="pre"
    if pid==c.ATA:
        return phase=="pre"
    if pid in (c.TOKEN,c.TOKEN22):
        tag=_ix_tag(ix)
        if phase=="pre":
            return tag==17
        return tag==9
    return False

def api_pump_route(user,token,start):
    pump64,pump_token_out=c.pump_tx(user,c.WSOL,token,start)
    if pump_token_out<=0:
        raise RuntimeError("PUMP_BUY_OUTPUT_ZERO")
    p_ixs,alts=c.resolve_pump_instructions(pump64)
    if not any(ix.get("programId")==c.PUMP for ix in p_ixs):
        raise RuntimeError("PUMP_PROGRAM_IX_NOT_FOUND")
    return p_ixs,alts,pump_token_out

def candidate_instruction_sets(p_ixs,m_ix):
    pi=next(i for i,x in enumerate(p_ixs) if x.get("programId")==c.PUMP)
    pre=p_ixs[:pi]
    pump=p_ixs[pi]
    post=p_ixs[pi+1:]

    full=pre+[pump,m_ix]+post

    compact=[x for x in pre if x.get("programId") not in MEMO_PROGRAMS and x.get("programId")!=COMPUTE_BUDGET]
    compact += [pump,m_ix]
    compact += [x for x in post if x.get("programId") not in MEMO_PROGRAMS and x.get("programId")!=COMPUTE_BUDGET]

    minimal=[x for x in pre if _minimal_helper(x,"pre")] + [pump,m_ix]
    minimal += [x for x in post if _minimal_helper(x,"post")]

    shell=[pump,m_ix]

    out=[]
    seen=set()
    for name,ixs in (
        ("FULL",full),
        ("NO_COMPUTE_MEMO",compact),
        ("WRAP_SWAP_CLOSE",minimal),
        ("PUMP_METEORA_ONLY",shell),
    ):
        key=tuple((x.get("programId"),x.get("data"),tuple(a.get("pubkey") for a in x.get("accounts") or [])) for x in ixs)
        if key in seen:
            continue
        seen.add(key)
        out.append((name,ixs))
    return out

def compose_reverse_candidates(user,token,pump_pool,meteora_pool,start_sol):
    start=int(round(float(start_sol)*1e9))
    meta=c.discover_dlmm(token)
    if meta["address"]!=meteora_pool:
        raise RuntimeError("METEORA_BINDING_DRIFT")
    p_ixs,alts,pump_token_out=api_pump_route(user,token,start)
    mq=c.dlmm_quote(meta,pump_token_out,token)
    end=int(mq["raw_out"])
    local_net=end-start
    local_bps=local_net/start*10000.0
    m_ix=dlmm_reverse_ix(user,meta,pump_token_out,mq)
    return {
        "start_lamports":start,
        "pump_token_out_raw":pump_token_out,
        "meteora_end_lamports":end,
        "pre_sim_net_lamports":local_net,
        "pre_sim_bps":local_bps,
        "alts":alts,
        "candidates":candidate_instruction_sets(p_ixs,m_ix),
    }

def attempt_candidate_simulations(user,kp,route,blockhash):
    rows=[]
    for name,ixs in route["candidates"]:
        try:
            msg,unsigned=c.compile_v0(user,ixs,route["alts"],blockhash)
            raw=c.signed_tx(msg,kp) if kp is not None else unsigned
            size=len(raw)
        except RuntimeError as e:
            txt=str(e)
            size=int(txt.rsplit(":",1)[-1]) if txt.startswith("ATOMIC_TX_TOO_LARGE:") else None
            rows.append({"name":name,"compiled":False,"bytes":size,"error":txt})
            print("[CANDIDATE] %s bytes=%s COMPILE_FAIL=%s"%(name,size,txt),flush=True)
            continue
        sim=c.simulate(raw,user,sigverify=(kp is not None))
        pnl=sim.get("pnl")
        bps=(pnl/route["start_lamports"]*10000.0 if pnl is not None else None)
        good=sim.get("err") is None and pnl is not None and pnl>0 and bps>=MIN_NET_BPS
        row={"name":name,"compiled":True,"bytes":size,"sim_err":sim.get("err"),
             "sim_units":sim.get("units"),"sim_pnl_lamports":pnl,"sim_bps":bps,
             "profitable":good}
        rows.append(row)
        print("[CANDIDATE] %s bytes=%d sim_err=%s pnl=%s bps=%s PROFITABLE=%s"%(
            name,size,sim.get("err"),
            ("NA" if pnl is None else "%+.9f"%(pnl/1e9)),
            ("NA" if bps is None else "%+.2f"%bps),good),flush=True)
        if good:
            return row,rows
    return None,rows
def compose_reverse_atomic(user,token,pump_pool,meteora_pool,start_sol):
    return compose_reverse_candidates(user,token,pump_pool,meteora_pool,start_sol)


def run(root=None,start_sol=0.05):
    root=Path(root or Path.cwd())
    report,binding=load_case(root)
    token=binding["token"]
    pump_pool=binding["pump_pool"]
    meteora_pool=binding["meteora_pool"]
    kp,user=c.sim_identity()
    print("[QSB-059E] PYTHON-ONLY ADAPTIVE ATOMIC MINIMIZER",flush=True)
    print("[CASE] token=%s pump=%s meteora=%s"%(token,pump_pool,meteora_pool),flush=True)
    print("[SIZE] %.6f SOL"%float(start_sol),flush=True)
    print("[SIGNER] %s"%("LOCAL_PRIVATE_KEY" if kp is not None else "SIM_ONLY_PUBLIC_KEY"),flush=True)
    print("[DEPENDENCIES] Python only | npm=NONE | node=NONE | Jupiter=NONE",flush=True)

    route=compose_reverse_candidates(user,token,pump_pool,meteora_pool,float(start_sol))
    print("[PRE_SIM] net=%+.9f SOL bps=%+.2f"%(
        route["pre_sim_net_lamports"]/1e9,route["pre_sim_bps"]),flush=True)

    bh=c.rpc("getLatestBlockhash",[{"commitment":"processed"}])["value"]["blockhash"]
    winner,attempts=attempt_candidate_simulations(user,kp,route,bh)

    out=root/"runtime_state/qseries/qsb059e_python_only_atomic/report.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    payload={
        "revision":"QSB_059E_PYTHON_ONLY_ADAPTIVE_ATOMIC_MINIMIZER_V1",
        "token":token,"pump_pool":pump_pool,"meteora_pool":meteora_pool,
        "direction":"PUMP_TO_METEORA","start_sol":float(start_sol),
        "pre_sim_net_sol":route["pre_sim_net_lamports"]/1e9,
        "pre_sim_bps":route["pre_sim_bps"],
        "attempts":attempts,"winner":winner,
        "profitable_simulation":bool(winner and winner.get("profitable")),
        "execution_authority":False,"real_money_moved":False,
        "next_required_boundary":"QSB_060_LIVE_PROFIT_GATE_AND_BROADCAST_ARM" if winner else "QSB_059F_ACCOUNT_PREP_OR_ALT_REQUIRED",
    }
    out.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print("[REPORT] "+str(out),flush=True)
    print("[MONEY] %s"%("PROFITABLE_ATOMIC_SIMULATION" if winner else "NO_PROFITABLE_ATOMIC_SIMULATION"),flush=True)
    print("[MODE] execution_authority=FALSE real_money_moved=FALSE",flush=True)
    return payload

if __name__=="__main__":
    run()
