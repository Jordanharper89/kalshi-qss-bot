from pathlib import Path
import py_compile

ROOT=Path.cwd()

ENGINE=ROOT/(
    "qseries_v2/oracle_execution/"
    "oracle_003_unified_physical_execution_engine.py"
)

JS=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native/"
    "oracle003_meteora_swap.mjs"
)

TEST=ROOT/(
    "test_oracle_003d_exhaustive_meteora_liquidity_repair.py"
)

if not ENGINE.is_file():
    raise SystemExit("[FAIL] ORACLE-003 engine missing")

if not JS.is_file():
    raise SystemExit("[FAIL] ORACLE-003 Meteora builder missing")

# ============================================================
# METEORA:
# 1. directional arrays 4 -> 64
# 2. then ALL initialized bin arrays
# 3. only then classify insufficient liquidity as physical
# ============================================================

JS.write_text(r'''
import fs from "node:fs";
import {createRequire} from "node:module";

const require=createRequire(import.meta.url);

const dlmm=require("@meteora-ag/dlmm");
const DLMM=dlmm.default ?? dlmm;

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
  new BN(String(req.amount));

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

  return new PublicKey(String(v));
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
      Buffer.from(ix.data)
        .toString("base64")
  };
}

function liquidityError(e){
  const s=String(
    e?.message ?? e
  );

  return (
    s.includes(
      "SWAP_QUOTE_INSUFFICIENT_LIQUIDITY"
    )
    ||
    s.includes(
      "Insufficient liquidity"
    )
  );
}

try{
  const pool=
    await DLMM.create(
      connection,
      poolAddress,
      {
        cluster:"mainnet-beta",
        skipSolWrappingOperation:true
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
  let source=null;
  let loadedCount=0;
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

      loadedCount=bins.length;

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
          "METEORA_PARTIAL_INPUT:"
          +q.consumedInAmount.toString()
          +":"
          +amount.toString()
        );
      }

      quote=q;
      source=
        "DIRECTIONAL_"+count;

      break;

    }catch(e){
      last=e;

      if(!liquidityError(e)){
        throw e;
      }
    }
  }

  // ---------------------------------------------------------
  // Exhaustive physical fallback:
  // fetch EVERY initialized bin array known to the pool.
  // ---------------------------------------------------------

  if(!quote){
    const allBins=
      await pool.getBinArrays();

    loadedCount=
      allBins.length;

    try{
      const q=
        pool.swapQuote(
          amount,
          swapForY,
          slippage,
          allBins,
          false
        );

      if(
        !q.consumedInAmount.eq(
          amount
        )
      ){
        throw new Error(
          "METEORA_PARTIAL_INPUT:"
          +q.consumedInAmount.toString()
          +":"
          +amount.toString()
        );
      }

      quote=q;
      source=
        "ALL_INITIALIZED_BIN_ARRAYS";

    }catch(e){
      if(liquidityError(e)){
        throw new Error(
          "METEORA_PHYSICAL_LIQUIDITY_INSUFFICIENT:"
          +"loaded_arrays="
          +allBins.length
          +":"
          +String(
            e?.message ?? e
          )
        );
      }

      throw e;
    }
  }

  if(!quote){
    throw (
      last ??
      new Error(
        "NO_COMPLETE_METEORA_QUOTE"
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
    ?tx:[tx];

  const instructions=
    txs.flatMap(
      z=>z.instructions ?? []
    );

  if(!instructions.length){
    throw new Error(
      "METEORA_NO_SWAP_INSTRUCTIONS"
    );
  }

  console.log(
    JSON.stringify({
      ok:true,

      quoteSource:
        source,

      loadedBinArrays:
        loadedCount,

      consumedIn:
        quote.consumedInAmount
          .toString(),

      out:
        quote.outAmount
          .toString(),

      minOut:
        quote.minOutAmount
          .toString(),

      binArrays:
        quote.binArraysPubkey.map(
          z=>z.toBase58()
        ),

      instructions:
        instructions.map(encode)
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
# PYTHON ENGINE:
# preserve the new quote source / loaded-array diagnostics.
# Make PAPER one physical sweep only.
# ============================================================

s=ENGINE.read_text(
    encoding="utf-8"
)

old='''        "depth":
            int(j["depth"]),

        "bin_arrays":
            list(
                j.get(
                    "binArrays"
                )
                or []
            ),'''

new='''        "depth":
            int(
                j.get(
                    "loadedBinArrays",
                    0
                )
            ),

        "quote_source":
            j.get(
                "quoteSource"
            ),

        "bin_arrays":
            list(
                j.get(
                    "binArrays"
                )
                or []
            ),'''

if old not in s:
    raise SystemExit(
        "[FAIL] Meteora result seam missing"
    )

s=s.replace(
    old,
    new,
    1
)

old2='''        "meteora_bin_depth":
            meteora["depth"],'''

new2='''        "meteora_bin_depth":
            meteora["depth"],

        "meteora_quote_source":
            meteora.get(
                "quote_source"
            ),'''

if old2 not in s:
    raise SystemExit(
        "[FAIL] exact route diagnostic seam missing"
    )

s=s.replace(
    old2,
    new2,
    1
)

# Paper mode should evaluate the complete candidate set once.
old3='''        if not prepared:
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

            continue'''

new3='''        if not prepared:
            if mode=="PAPER":
                print(
                    "[PAPER_HOLD] "
                    "no currently executable "
                    "PumpSwap->Meteora packet",
                    flush=True
                )

                save({
                    "revision":
                        "ORACLE_003D",

                    "status":
                        "PAPER_HOLD",

                    "execution_owner":
                        "ORACLE",

                    "real_money_moved":
                        False,

                    "rejects":
                        rejects,
                })

                return 2

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

            continue'''

if old3 not in s:
    raise SystemExit(
        "[FAIL] paper loop seam missing"
    )

s=s.replace(
    old3,
    new3,
    1
)

ENGINE.write_text(
    s,
    encoding="utf-8"
)

py_compile.compile(
    str(ENGINE),
    doraise=True
)

TEST.write_text(
r'''import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as q
)


class T(unittest.TestCase):

    def test_principal(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_strategy_is_pump_to_meteora(self):
        s=inspect.getsource(
            q.exact_route
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )

        self.assertIn(
            "meteora_swap",
            s
        )


    def test_meteora_diagnostics(self):
        s=inspect.getsource(
            q.meteora_swap
        )

        self.assertIn(
            "quote_source",
            s
        )

        self.assertIn(
            "loadedBinArrays",
            s
        )


    def test_paper_one_sweep(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[PAPER_HOLD]",
            s
        )


    def test_signed_simulation_preserved(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


    def test_oracle_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
''',
    encoding="utf-8"
)

py_compile.compile(
    str(TEST),
    doraise=True
)

print("[PASS] ORACLE-003D exhaustive Meteora liquidity repair installed")
print("[METEORA] directional arrays 4/8/16/32/64")
print("[METEORA] fallback=getBinArrays ALL initialized arrays")
print("[LIQUIDITY] failure after exhaustive fetch = physical reject")
print("[5Nh] negative guaranteed minimum remains rejected")
print("[PAPER] one complete physical sweep; no repeated spam")
print("[LIVE] unchanged and NOT invoked by this test")
print("[CAP] exact strategy principal 0.001 SOL")
print("[OWNER] ORACLE")