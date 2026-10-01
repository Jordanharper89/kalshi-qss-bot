import fs from "node:fs";
import BN from "bn.js";
import {Connection,PublicKey} from "@solana/web3.js";
import {
  OnlinePumpAmmSdk,
  PUMP_AMM_SDK,
  buyQuoteInput
} from "@pump-fun/pump-swap-sdk";

const req=JSON.parse(
  fs.readFileSync(0,"utf8")
);

const connection=new Connection(
  req.rpc,
  "processed"
);

const user=new PublicKey(
  req.user
);

const poolKey=new PublicKey(
  req.pool
);

const quoteLamports=new BN(
  String(req.quoteLamports)
);

const slippage=Number(
  req.slippagePct ?? 0.2
);

function encIx(ix){
  return {
    programId:
      ix.programId.toBase58(),

    accounts:
      ix.keys.map(
        k=>({
          pubkey:
            k.pubkey.toBase58(),

          isSigner:
            !!k.isSigner,

          isWritable:
            !!k.isWritable
        })
      ),

    data:
      Buffer.from(
        ix.data
      ).toString("base64")
  };
}

try{
  const online=
    new OnlinePumpAmmSdk(
      connection
    );

  /*
   * PHYSICAL LIVE STATE.
   *
   * This contains the exact current:
   * - pool reserves
   * - fee config
   * - global config
   * - mint/account metadata
   * - creator/coin-creator state
   */
  const state=
    await online.swapSolanaState(
      poolKey,
      user
    );

  /*
   * PumpSwap SDK 1.20.0 fee-aware pricing.
   *
   * This is the SAME pricing function used by
   * PUMP_AMM_SDK.buyQuoteInput internally.
   *
   * Exact quote input:
   *     1,000,000 lamports for QARB-096
   *
   * Output:
   *     base = token amount expected from that
   *     exact quote input under CURRENT fee state.
   */
  const pricing=
    buyQuoteInput({
      quote:
        quoteLamports,

      slippage:
        slippage,

      baseReserve:
        state.poolBaseAmount,

      quoteReserve:
        state.poolQuoteAmount,

      baseMintAccount:
        state.baseMintAccount,

      baseMint:
        state.pool.baseMint,

      coinCreator:
        state.pool.coinCreator,

      creator:
        state.pool.creator,

      feeConfig:
        state.feeConfig,

      globalConfig:
        state.globalConfig
    });

  const baseOut=
    pricing.base;

  const maxQuote=
    pricing.maxQuote;

  if (!baseOut) {
    throw new Error(
      "BUY_QUOTE_INPUT_BASE_MISSING"
    );
  }

  if (
    new BN(
      String(baseOut)
    ).lte(
      new BN(0)
    )
  ){
    throw new Error(
      "BUY_QUOTE_INPUT_BASE_NONPOSITIVE"
    );
  }

  /*
   * Build the real PumpSwap transaction instructions
   * from THE SAME state and exact quote input.
   *
   * No stale API expectedOutAmount.
   * No manual fixed Pump fee.
   * No fake autocomplete method.
   */
  const ixs=
    await PUMP_AMM_SDK.buyQuoteInput(
      state,
      quoteLamports,
      slippage
    );

  if (
    !Array.isArray(ixs)
    || ixs.length===0
  ){
    throw new Error(
      "PUMP_BUY_INSTRUCTIONS_EMPTY"
    );
  }

  console.log(
    JSON.stringify({
      ok:true,

      baseOut:
        String(baseOut),

      maxQuote:
        maxQuote
        ? String(maxQuote)
        : null,

      quoteIn:
        String(quoteLamports),

      slippagePct:
        slippage,

      pricingAuthority:
        "PUMP_SWAP_SDK_1_20_0_BUY_QUOTE_INPUT",

      instructions:
        ixs.map(encIx)
    })
  );

}catch(e){
  console.log(
    JSON.stringify({
      ok:false,
      reason:
        e?.stack
        ?? e?.message
        ?? String(e)
    })
  );
}
