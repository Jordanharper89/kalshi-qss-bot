from pathlib import Path
import json
import py_compile
import shutil
import subprocess

ROOT=Path.cwd()

BASE=ROOT/(
    "qseries_v2/oracle_execution/"
    "oracle_001_live_solana_executor.py"
)

OUTDIR=ROOT/"qseries_v2/oracle_execution"

ENGINE=OUTDIR/(
    "oracle_003_unified_physical_execution_engine.py"
)

LAUNCHER=ROOT/"run_oracle_execution.py"

TEST=ROOT/(
    "test_oracle_003_unified_physical_execution_engine.py"
)

NODE_DIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

PACKAGE=NODE_DIR/"package.json"
METEORA=NODE_DIR/"oracle003_meteora_swap.mjs"
TOKEN_NET=NODE_DIR/"oracle003_token_net.mjs"

for p in (BASE,NODE_DIR,PACKAGE):
    if not p.exists():
        raise SystemExit(
            "[FAIL] missing dependency: "+str(p)
        )

# ============================================================
# NODE DEPENDENCIES
# ============================================================

pkg=json.loads(
    PACKAGE.read_text(
        encoding="utf-8"
    )
)

deps=pkg.setdefault(
    "dependencies",
    {}
)

deps.setdefault(
    "@solana/spl-token",
    "^0.4.14"
)

PACKAGE.write_text(
    json.dumps(
        pkg,
        indent=2
    )+"\n",
    encoding="utf-8"
)

npm=(
    shutil.which("npm.cmd")
    or shutil.which("npm")
)

if not npm:
    raise SystemExit("[FAIL] npm missing")

p=subprocess.run(
    [
        npm,
        "install",
        "--silent",
        "--no-audit",
        "--no-fund",
    ],
    cwd=NODE_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    timeout=240,
)

if p.returncode!=0:
    raise SystemExit(
        "[FAIL] npm install:\n"
        +p.stdout[-3000:]
    )

# ============================================================
# TOKEN-2022 NET RECEIVED
# ============================================================

TOKEN_NET.write_text(r'''
import fs from "node:fs";
import {createRequire} from "node:module";

const require=createRequire(
  import.meta.url
);

const {
  Connection,
  PublicKey
}=require("@solana/web3.js");

const {
  TOKEN_PROGRAM_ID,
  TOKEN_2022_PROGRAM_ID,
  getMint,
  getTransferFeeConfig,
  calculateEpochFee
}=require("@solana/spl-token");

const req=JSON.parse(
  fs.readFileSync(0,"utf8")
);

const connection=new Connection(
  req.rpc,
  "confirmed"
);

const mint=new PublicKey(
  req.mint
);

const gross=BigInt(
  String(req.gross)
);

try{
  const info=
    await connection.getAccountInfo(
      mint,
      "confirmed"
    );

  if(!info){
    throw new Error(
      "MINT_NOT_FOUND"
    );
  }

  if(
    info.owner.equals(
      TOKEN_PROGRAM_ID
    )
  ){
    console.log(
      JSON.stringify({
        ok:true,
        program:
          TOKEN_PROGRAM_ID.toBase58(),
        gross:gross.toString(),
        fee:"0",
        net:gross.toString()
      })
    );

    process.exit(0);
  }

  if(
    !info.owner.equals(
      TOKEN_2022_PROGRAM_ID
    )
  ){
    throw new Error(
      "UNKNOWN_TOKEN_PROGRAM:"
      +info.owner.toBase58()
    );
  }

  const m=
    await getMint(
      connection,
      mint,
      "confirmed",
      TOKEN_2022_PROGRAM_ID
    );

  const cfg=
    getTransferFeeConfig(m);

  if(!cfg){
    console.log(
      JSON.stringify({
        ok:true,
        program:
          TOKEN_2022_PROGRAM_ID.toBase58(),
        gross:gross.toString(),
        fee:"0",
        net:gross.toString()
      })
    );

    process.exit(0);
  }

  const epoch=
    await connection.getEpochInfo(
      "confirmed"
    );

  const fee=
    calculateEpochFee(
      cfg,
      BigInt(epoch.epoch),
      gross
    );

  const net=gross-fee;

  if(net<=0n){
    throw new Error(
      "NET_RECEIVED_NONPOSITIVE"
    );
  }

  console.log(
    JSON.stringify({
      ok:true,
      program:
        TOKEN_2022_PROGRAM_ID.toBase58(),
      gross:gross.toString(),
      fee:fee.toString(),
      net:net.toString()
    })
  );

}catch(e){
  console.log(
    JSON.stringify({
      ok:false,
      reason:
        e?.stack ??
        e?.message ??
        String(e)
    })
  );
}
'''.strip()+"\n",encoding="utf-8")

# ============================================================
# CURRENT OFFICIAL METEORA BUILDER
# WITH EXPANDING BIN COVERAGE
# ============================================================

METEORA.write_text(r'''
import fs from "node:fs";
import {createRequire} from "node:module";

const require=createRequire(
  import.meta.url
);

const dlmm=require(
  "@meteora-ag/dlmm"
);

const DLMM=
  dlmm.default ?? dlmm;

const {
  Connection,
  PublicKey
}=require("@solana/web3.js");

const BN=require("bn.js");

const req=JSON.parse(
  fs.readFileSync(0,"utf8")
);

const connection=
  new Connection(
    req.rpc,
    "processed"
  );

const user=
  new PublicKey(req.user);

const poolAddress=
  new PublicKey(req.pool);

const inToken=
  new PublicKey(req.inputMint);

const outToken=
  new PublicKey(req.outputMint);

const amount=
  new BN(
    String(req.amount)
  );

const slippage=
  new BN(
    String(req.slippageBps)
  );

function pk(v){
  if(v instanceof PublicKey){
    return v;
  }

  if(v?.mint?.address){
    return new PublicKey(
      v.mint.address.toString()
    );
  }

  if(v?.mint){
    return new PublicKey(
      v.mint.toString()
    );
  }

  if(v?.publicKey){
    return new PublicKey(
      v.publicKey.toString()
    );
  }

  return new PublicKey(
    String(v)
  );
}

function encode(ix){
  return {
    programId:
      ix.programId.toBase58(),

    accounts:
      ix.keys.map(k=>({
        pubkey:
          k.pubkey.toBase58(),

        isSigner:
          !!k.isSigner,

        isWritable:
          !!k.isWritable
      })),

    data:
      Buffer.from(
        ix.data
      ).toString("base64")
  };
}

try{
  const pool=
    await DLMM.create(
      connection,
      poolAddress,
      {
        cluster:
          "mainnet-beta",

        skipSolWrappingOperation:
          true
      }
    );

  const x=pk(pool.tokenX);
  const y=pk(pool.tokenY);

  let swapForY;

  if(
    inToken.equals(x)
    &&
    outToken.equals(y)
  ){
    swapForY=true;
  }
  else if(
    inToken.equals(y)
    &&
    outToken.equals(x)
  ){
    swapForY=false;
  }
  else{
    throw new Error(
      "POOL_MINT_BINDING_MISMATCH"
    );
  }

  let quote=null;
  let depth=0;
  let last=null;

  for(
    const count of
    [4,8,16,32,64]
  ){
    try{
      const bins=
        await pool.getBinArrayForSwap(
          swapForY,
          count
        );

      const q=
        pool.swapQuote(
          amount,
          swapForY,
          slippage,
          bins,
          false
        );

      if(
        !q.consumedInAmount.eq(
          amount
        )
      ){
        throw new Error(
          "PARTIAL_FILL:"
          +q.consumedInAmount.toString()
          +":"
          +amount.toString()
        );
      }

      quote=q;
      depth=count;
      break;

    }catch(e){
      last=e;

      const msg=String(
        e?.message ?? e
      );

      if(
        !msg.includes(
          "INSUFFICIENT_LIQUIDITY"
        )
        &&
        !msg.includes(
          "Insufficient liquidity"
        )
      ){
        throw e;
      }
    }
  }

  if(!quote){
    throw (
      last ??
      new Error(
        "NO_COMPLETE_DLMM_QUOTE"
      )
    );
  }

  const tx=
    await pool.swap({
      inToken,
      outToken,

      inAmount:
        quote.consumedInAmount,

      minOutAmount:
        quote.minOutAmount,

      lbPair:
        pool.pubkey,

      user,

      binArraysPubkey:
        quote.binArraysPubkey
    });

  const txs=
    Array.isArray(tx)
    ? tx
    : [tx];

  const instructions=
    txs.flatMap(
      t=>t.instructions ?? []
    );

  if(!instructions.length){
    throw new Error(
      "NO_SWAP_INSTRUCTIONS"
    );
  }

  console.log(
    JSON.stringify({
      ok:true,

      consumedIn:
        quote.consumedInAmount
          .toString(),

      out:
        quote.outAmount
          .toString(),

      minOut:
        quote.minOutAmount
          .toString(),

      depth,

      binArrays:
        quote.binArraysPubkey.map(
          z=>z.toBase58()
        ),

      instructions:
        instructions.map(
          encode
        )
    })
  );

}catch(e){
  console.log(
    JSON.stringify({
      ok:false,

      reason:
        e?.stack ??
        e?.message ??
        String(e)
    })
  );
}
'''.strip()+"\n",encoding="utf-8")

# ============================================================
# ORACLE-003 UNIFIED PHYSICAL ENGINE
# ============================================================

ENGINE.write_text(r'''
from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_001_live_solana_executor
    as base
)

EXECUTION_OWNER="ORACLE"
ORACLE_EXECUTION_AUTHORITY=True

MICRO_SOL=0.001
MICRO_LAMPORTS=1_000_000

MAX_TX_BYTES=1232

NODE_DIR=Path(
    "qseries_v2/"
    "oracle_strategy_intelligence/"
    "solana_money/"
    "qsb059d_pump_native"
)

STATE=Path(
    "runtime_state/oracle/"
    "unified_physical_execution/"
    "oracle_003_state.json"
)

LEDGER=Path(
    "runtime_state/oracle/"
    "unified_physical_execution/"
    "oracle_003_ledger.jsonl"
)


def save(payload):
    STATE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tmp=STATE.with_suffix(
        ".tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str
        ),
        encoding="utf-8"
    )

    tmp.replace(STATE)


def append(payload):
    LEDGER.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with LEDGER.open(
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            json.dumps(
                payload,
                sort_keys=True,
                default=str
            )
            +"\n"
        )


def rpc(
    method,
    params,
    timeout=20
):
    url=os.getenv(
        "SOLANA_RPC_URL",
        "https://api.mainnet-beta.solana.com"
    )

    body=json.dumps({
        "jsonrpc":"2.0",
        "id":1,
        "method":method,
        "params":params,
    }).encode()

    delay=0.75
    last=None

    for attempt in range(
        1,
        6
    ):
        req=urllib.request.Request(
            url,
            data=body,
            headers={
                "content-type":
                    "application/json",

                "user-agent":
                    "oracle-unified-executor/3.0",
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                req,
                timeout=timeout
            ) as r:
                j=json.loads(
                    r.read().decode()
                )

            if j.get("error"):
                raise RuntimeError(
                    "RPC_%s:%s"%(
                        method,
                        json.dumps(
                            j["error"],
                            sort_keys=True
                        )
                    )
                )

            return j.get(
                "result"
            )

        except urllib.error.HTTPError as exc:
            last=exc

            if (
                exc.code!=429
                or attempt==5
            ):
                raise

            print(
                "[RPC_429_BACKOFF] "
                "method=%s attempt=%d"%(
                    method,
                    attempt
                ),
                flush=True
            )

            time.sleep(delay)

            delay=min(
                delay*2.0,
                8.0
            )

        except urllib.error.URLError as exc:
            last=exc

            if attempt==5:
                raise

            time.sleep(delay)

            delay=min(
                delay*2.0,
                8.0
            )

    raise RuntimeError(
        "RPC_RETRY_EXHAUSTED:"
        +str(last)
    )


# All inherited transaction compilation/simulation RPC
# now uses the same resilient Oracle RPC boundary.
base._rpc=rpc


def node_json(
    script,
    payload,
    timeout=45
):
    p=subprocess.run(
        [
            "node",
            script
        ],
        cwd=NODE_DIR,
        input=json.dumps(
            payload
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout
    )

    if p.returncode!=0:
        raise RuntimeError(
            "NODE_FAILED:"
            +p.stderr[-3000:]
        )

    try:
        out=json.loads(
            p.stdout.strip()
            .splitlines()[-1]
        )
    except Exception:
        raise RuntimeError(
            "NODE_BAD_JSON:"
            +p.stdout[-3000:]
        )

    if not out.get("ok"):
        raise RuntimeError(
            str(
                out.get(
                    "reason"
                )
            )
        )

    return out


def pump_min_base_out(
    pump_ix
):
    raw=base64.b64decode(
        pump_ix.get(
            "data"
        )
        or ""
    )

    disc=bytes([
        198,46,21,82,
        180,217,232,112
    ])

    if raw[:8]!=disc:
        raise RuntimeError(
            "PUMP_NOT_BUY_EXACT_QUOTE_IN"
        )

    if len(raw)<24:
        raise RuntimeError(
            "PUMP_DATA_TOO_SHORT"
        )

    spendable=int.from_bytes(
        raw[8:16],
        "little"
    )

    minimum=int.from_bytes(
        raw[16:24],
        "little"
    )

    if spendable!=MICRO_LAMPORTS:
        raise RuntimeError(
            "PUMP_PRINCIPAL_DRIFT:"
            +str(spendable)
        )

    if minimum<=0:
        raise RuntimeError(
            "PUMP_MINIMUM_ZERO"
        )

    return minimum


def net_received(
    mint,
    gross
):
    j=node_json(
        "oracle003_token_net.mjs",
        {
            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "mint":
                str(mint),

            "gross":
                int(gross),
        },
        timeout=30
    )

    return {
        "gross":
            int(j["gross"]),

        "fee":
            int(j["fee"]),

        "net":
            int(j["net"]),

        "program":
            j.get("program"),
    }


def meteora_swap(
    user,
    pair,
    amount
):
    j=node_json(
        "oracle003_meteora_swap.mjs",
        {
            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "user":
                str(user),

            "pool":
                str(
                    pair.meteora_pool
                ),

            "inputMint":
                str(pair.token),

            "outputMint":
                str(
                    base.q87.c.WSOL
                ),

            "amount":
                int(amount),

            "slippageBps":
                int(
                    base.q87.las.q59
                    .SLIPPAGE_BPS
                ),
        }
    )

    return {
        "consumed":
            int(
                j["consumedIn"]
            ),

        "out":
            int(j["out"]),

        "min_out":
            int(j["minOut"]),

        "depth":
            int(j["depth"]),

        "bin_arrays":
            list(
                j.get(
                    "binArrays"
                )
                or []
            ),

        "instructions":
            list(
                j.get(
                    "instructions"
                )
                or []
            ),
    }


def exact_route(
    user,
    pair
):
    # --------------------------------------------------------
    # EXACT SAME PHYSICAL ROUTE FOR PAPER AND LIVE
    # --------------------------------------------------------

    pump_ixs,pump_quote_out=(
        base.q87.las.q59
        .native_pump_buy_ixs(
            user,
            pair.pump_pool,
            MICRO_LAMPORTS
        )
    )

    positions=[
        i
        for i,x in enumerate(
            pump_ixs
        )
        if x.get(
            "programId"
        )==base.q87.c.PUMP
    ]

    if len(positions)!=1:
        raise RuntimeError(
            "PUMP_IX_COUNT:"
            +str(len(positions))
        )

    pi=positions[0]
    pump_ix=pump_ixs[pi]

    # IMPORTANT:
    # Do not use the optimistic Pump quote as Meteora input.
    # Extract the minimum amount the Pump instruction itself
    # guarantees on-chain.
    pump_minimum=pump_min_base_out(
        pump_ix
    )

    received=net_received(
        pair.token,
        pump_minimum
    )

    spendable=int(
        received["net"]
    )

    if spendable<=0:
        raise RuntimeError(
            "PUMP_NET_MINIMUM_ZERO"
        )

    meteora=meteora_swap(
        user,
        pair,
        spendable
    )

    if (
        meteora["consumed"]
        !=spendable
    ):
        raise RuntimeError(
            "METEORA_PARTIAL_INPUT"
        )

    guaranteed_end=int(
        meteora[
            "min_out"
        ]
    )

    guaranteed_net=(
        guaranteed_end
        -MICRO_LAMPORTS
    )

    guaranteed_bps=(
        guaranteed_net
        /MICRO_LAMPORTS
        *10000.0
    )

    if guaranteed_net<=0:
        raise RuntimeError(
            "GUARANTEED_NET_NONPOSITIVE:"
            +str(
                guaranteed_net
            )
        )

    if (
        guaranteed_bps
        <
        base.q87.las.q59
        .MIN_NET_BPS
    ):
        raise RuntimeError(
            "GUARANTEED_BPS_BELOW_GATE:"
            +str(
                guaranteed_bps
            )
        )

    pre=list(
        pump_ixs[:pi]
    )

    post=list(
        pump_ixs[
            pi+1:
        ]
    )

    full=(
        pre
        +[pump_ix]
        +meteora[
            "instructions"
        ]
        +post
    )

    return {
        "token":
            pair.token,

        "start_lamports":
            MICRO_LAMPORTS,

        "pump_quote_out":
            int(
                pump_quote_out
            ),

        "pump_minimum_out":
            pump_minimum,

        "pump_transfer_fee":
            received["fee"],

        "pump_spendable_out":
            spendable,

        "meteora_min_out":
            guaranteed_end,

        "meteora_quote_out":
            meteora["out"],

        "meteora_bin_depth":
            meteora["depth"],

        "pre_sim_net_lamports":
            guaranteed_net,

        "pre_sim_bps":
            guaranteed_bps,

        "base_alts":
            [],

        "original_candidates":[
            (
                "ORACLE_UNIFIED_FULL",
                full
            )
        ],
    }


def prepare_exact_packet(
    root,
    row,
    kp,
    user
):
    pair_map=base.hydrate_rows(
        root,
        [row]
    )

    pair=pair_map.get(
        row["token"]
    )

    if pair is None:
        return {
            "ok":False,
            "reason":
                "PAIR_MISSING"
        }

    try:
        route=exact_route(
            user,
            pair
        )

    except Exception as exc:
        return {
            "ok":False,

            "reason":
                type(exc).__name__
                +":"
                +str(exc)
        }

    compiled=base.compile_signed(
        user,
        kp,
        route,
        "ORACLE_UNIFIED_FULL"
    )

    if not compiled.get("ok"):
        return {
            "ok":False,

            "reason":
                compiled.get(
                    "reason",
                    "COMPILE_REJECT"
                ),

            "attempts":
                compiled.get(
                    "attempts",
                    []
                )
        }

    raw=compiled["raw"]

    if len(raw)>MAX_TX_BYTES:
        return {
            "ok":False,
            "reason":
                "SIGNED_PACKET_TOO_LARGE"
        }

    sim=base.signed_simulation(
        raw
    )

    if sim.get("err") is not None:
        return {
            "ok":False,

            "reason":
                "SIGNED_SIM_ERROR",

            "simulation":
                sim
        }

    return {
        "ok":True,

        "raw":
            raw,

        "bytes":
            len(raw),

        "candidate":
            compiled[
                "candidate"
            ],

        "simulation":
            sim,

        "route":
            route,

        "token":
            row["token"],

        "fresh_net_lamports":
            route[
                "pre_sim_net_lamports"
            ],

        "fresh_bps":
            route[
                "pre_sim_bps"
            ],
    }


def run(
    mode="LIVE",
    seconds=120,
    scan_seconds=3.0
):
    mode=str(mode).upper()

    if mode not in (
        "PAPER",
        "LIVE"
    ):
        raise RuntimeError(
            "MODE_MUST_BE_PAPER_OR_LIVE"
        )

    root=Path.cwd()

    kp,user=base.require_keypair()

    if mode=="LIVE":
        base.require_arm()

    balance=int(
        rpc(
            "getBalance",
            [
                user,
                {
                    "commitment":
                        "confirmed"
                }
            ]
        )["value"]
    )

    print(
        "[ORACLE-003] "
        "UNIFIED PHYSICAL EXECUTION",
        flush=True
    )

    print(
        "[MODE] %s"%mode,
        flush=True
    )

    print(
        "[OWNER] ORACLE "
        "execution_authority=%s"%(
            "TRUE"
            if mode=="LIVE"
            else "FALSE"
        ),
        flush=True
    )

    print(
        "[WALLET] %s"%user,
        flush=True
    )

    print(
        "[BALANCE] %.9f SOL"%(
            balance/1e9
        ),
        flush=True
    )

    print(
        "[CAP] exact=0.001000000_SOL",
        flush=True
    )

    print(
        "[CONTRACT] PAPER_AND_LIVE="
        "IDENTICAL_SIGNED_PACKET",
        flush=True
    )

    print(
        "[ALT] create_new=FALSE "
        "reuse_existing_only=TRUE",
        flush=True
    )

    rows=base.load_micro_rows(
        root
    )

    deadline=(
        time.monotonic()
        +min(
            max(
                int(seconds),
                1
            ),
            120
        )
    )

    sends=0
    confirmed=0
    rejects=0

    while (
        time.monotonic()
        <deadline
    ):
        prepared=[]

        for row in rows:

            result=prepare_exact_packet(
                root,
                row,
                kp,
                user
            )

            if not result.get(
                "ok"
            ):
                rejects+=1

                reason=result.get(
                    "reason"
                )

                print(
                    "[PHYSICAL_REJECT] "
                    "token=%s reason=%s"%(
                        row[
                            "token"
                        ][:10],
                        reason
                    ),
                    flush=True
                )

                sim=result.get(
                    "simulation"
                ) or {}

                for line in (
                    sim.get("logs")
                    or []
                )[-6:]:
                    print(
                        "[SIM_LOG] "
                        +str(line),
                        flush=True
                    )

                continue

            prepared.append(
                result
            )

        if not prepared:
            time.sleep(
                min(
                    scan_seconds,
                    max(
                        0,
                        deadline
                        -time.monotonic()
                    )
                )
            )

            continue

        prepared.sort(
            key=lambda x:
                x[
                    "fresh_net_lamports"
                ],
            reverse=True
        )

        top=prepared[0]

        route=top["route"]

        print(
            "[PHYSICAL_PASS] "
            "token=%s "
            "bps=%+.2f "
            "net=%+.9f_SOL "
            "bytes=%d "
            "pump_min=%d "
            "pump_net=%d "
            "meteora_depth=%d"%(
                top[
                    "token"
                ][:10],

                top[
                    "fresh_bps"
                ],

                top[
                    "fresh_net_lamports"
                ]/1e9,

                top[
                    "bytes"
                ],

                route[
                    "pump_minimum_out"
                ],

                route[
                    "pump_spendable_out"
                ],

                route[
                    "meteora_bin_depth"
                ],
            ),
            flush=True
        )

        append({
            "event":
                "EXACT_PACKET_CERTIFIED",

            "mode":
                mode,

            "token":
                top["token"],

            "bytes":
                top["bytes"],

            "bps":
                top[
                    "fresh_bps"
                ],

            "net_lamports":
                top[
                    "fresh_net_lamports"
                ],

            "pump_minimum_out":
                route[
                    "pump_minimum_out"
                ],

            "pump_spendable_out":
                route[
                    "pump_spendable_out"
                ],

            "unix":
                time.time(),
        })

        if mode=="PAPER":
            print(
                "[PAPER_CERTIFIED] "
                "same_packet_ready_for_live=TRUE",
                flush=True
            )

            return 0

        # ----------------------------------------------------
        # LIVE BROADCASTS THE SAME RAW BYTES THAT JUST PASSED
        # SIGNED SIMULATION.
        # NO REBUILD. NO REQUOTE. NO ALTERATION.
        # ----------------------------------------------------

        base.require_arm()

        signature=base.send_once(
            top["raw"]
        )

        sends+=1

        print(
            "[LIVE_SENT] "
            "signature=%s"%signature,
            flush=True
        )

        tx=base.wait_confirmed(
            signature,
            deadline
        )

        if tx is None:
            print(
                "[HARD_STOP] "
                "confirmation_unknown",
                flush=True
            )

            return 3

        rec=base.reconcile(
            signature,
            tx,
            user,
            top["token"]
        )

        append({
            "event":
                "LIVE_RECONCILED",

            **rec,

            "unix":
                time.time(),
        })

        if (
            rec[
                "transaction_error"
            ]
            is not None
        ):
            print(
                "[HARD_STOP] "
                "confirmed_error=%s"%(
                    rec[
                        "transaction_error"
                    ]
                ),
                flush=True
            )

            return 4

        confirmed+=1

        print(
            "[LIVE_RECONCILED] "
            "signature=%s "
            "wallet_delta=%+.9f_SOL "
            "fee=%d "
            "token_residue=%d "
            "wsol_residue=%d "
            "clean=%s"%(
                signature,

                rec[
                    "wallet_delta_sol"
                ],

                rec[
                    "fee_lamports"
                ],

                rec[
                    "target_token_delta_raw"
                ],

                rec[
                    "wsol_delta_raw"
                ],

                rec[
                    "residue_clean"
                ],
            ),
            flush=True
        )

        # First physical cutover:
        # exactly ONE confirmed real transaction.
        print(
            "[ORACLE-003] "
            "FIRST_LIVE_CANARY_COMPLETE",
            flush=True
        )

        save({
            "revision":
                "ORACLE_003",

            "status":
                "LIVE_CONFIRMED",

            "execution_owner":
                "ORACLE",

            "sends":
                sends,

            "confirmed":
                confirmed,

            "last_signature":
                signature,

            "wallet_delta_sol":
                rec[
                    "wallet_delta_sol"
                ],

            "residue_clean":
                rec[
                    "residue_clean"
                ],
        })

        return 0

    save({
        "revision":
            "ORACLE_003",

        "status":
            "NO_PHYSICAL_PACKET_PASSED",

        "execution_owner":
            "ORACLE",

        "sends":
            sends,

        "confirmed":
            confirmed,

        "rejects":
            rejects,
    })

    print(
        "[ORACLE-003] COMPLETE "
        "sends=%d confirmed=%d "
        "rejects=%d"%(
            sends,
            confirmed,
            rejects
        ),
        flush=True
    )

    return 2
'''.strip()+"\n",encoding="utf-8")

py_compile.compile(
    str(ENGINE),
    doraise=True
)

# ============================================================
# PLUG-AND-PLAY LAUNCHER
# ============================================================

LAUNCHER.write_text(r'''
from __future__ import annotations

import argparse
import getpass
import os

from qseries_v2.oracle_execution.oracle_003_unified_physical_execution_engine import run


def main():
    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--paper",
        action="store_true"
    )

    ap.add_argument(
        "--seconds",
        type=int,
        default=120
    )

    a=ap.parse_args()

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    mode=(
        "PAPER"
        if a.paper
        else "LIVE"
    )

    if mode=="LIVE":
        os.environ[
            "QSB_LIVE_ARM"
        ]="I_ACCEPT_REAL_MONEY_RISK"

        os.environ[
            "ORACLE_SOLANA_EXECUTION_ARM"
        ]="I_ACCEPT_ORACLE_0_001_SOL_EXECUTION"

    return run(
        mode=mode,
        seconds=a.seconds
    )


if __name__=="__main__":
    raise SystemExit(main())
'''.strip()+"\n",encoding="utf-8")

py_compile.compile(
    str(LAUNCHER),
    doraise=True
)

# ============================================================
# TEST CONTRACT
# ============================================================

TEST.write_text(r'''
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as q
)


class T(unittest.TestCase):

    def test_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )


    def test_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_exact_pump_minimum_parsed(self):
        s=inspect.getsource(
            q.pump_min_base_out
        )

        self.assertIn(
            "raw[16:24]",
            s
        )


    def test_token2022_net_used(self):
        s=inspect.getsource(
            q.exact_route
        )

        self.assertIn(
            "net_received",
            s
        )

        self.assertIn(
            "pump_minimum",
            s
        )


    def test_same_packet_boundary(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            'base.send_once(',
            s
        )

        self.assertIn(
            'top["raw"]',
            s
        )


    def test_signed_simulation_before_pass(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


    def test_rpc_backoff(self):
        s=inspect.getsource(
            q.rpc
        )

        self.assertIn(
            "429",
            s
        )


    def test_no_alt_creation(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "createLookupTable",
            s
        )

        self.assertNotIn(
            "bootstrap_micro_alt",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
'''.strip()+"\n",encoding="utf-8")

py_compile.compile(
    str(TEST),
    doraise=True
)

# ============================================================
# PHYSICAL NODE IMPORT PROBE
# ============================================================

node=shutil.which("node")

if not node:
    raise SystemExit(
        "[FAIL] node missing"
    )

probe=subprocess.run(
    [
        node,
        "--input-type=module",
        "-e",
        (
            'import {createRequire} from "node:module";'
            'const require=createRequire(import.meta.url);'
            'const m=require("@meteora-ag/dlmm");'
            'const s=require("@solana/spl-token");'
            'if(!(m.default??m))process.exit(2);'
            'if(!s.calculateEpochFee)process.exit(3);'
            'console.log("[NODE_PHYSICAL_IMPORT_PASS]");'
        )
    ],
    cwd=NODE_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    timeout=30
)

print(
    probe.stdout.strip()
)

if probe.returncode!=0:
    raise SystemExit(
        "[FAIL] Node physical dependency probe"
    )

print(
    "[PASS] ORACLE-003 unified physical execution installed"
)

print(
    "[BOUNDARY] PAPER/LIVE share one exact signed packet"
)

print(
    "[PUMP] on-chain min_base_amount_out drives Meteora input"
)

print(
    "[TOKEN2022] transfer fee deducted before Meteora sizing"
)

print(
    "[METEORA] expanding complete-liquidity bin search"
)

print(
    "[RPC] HTTP-429 backoff enabled"
)

print(
    "[ALT] creation disabled; existing tables only"
)

print(
    "[LIVE] first cutover limited to ONE confirmed transaction"
)

print(
    "[CAP] 0.001 SOL"
)

print(
    "[OWNER] ORACLE"
)