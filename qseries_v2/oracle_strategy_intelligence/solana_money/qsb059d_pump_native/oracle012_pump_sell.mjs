import fs from "node:fs";
import {createRequire} from "node:module";

const require=createRequire(
  import.meta.url
);

const {
  Connection,
  PublicKey
}=require(
  "@solana/web3.js"
);

const {
  OnlinePumpAmmSdk,
  PUMP_AMM_SDK
}=require(
  "@pump-fun/pump-swap-sdk"
);

const BN=require(
  "bn.js"
);

const req=JSON.parse(
  fs.readFileSync(
    0,
    "utf8"
  )
);

const connection=
  new Connection(
    req.rpc,
    "processed"
  );

const user=
  new PublicKey(
    req.user
  );

const pool=
  new PublicKey(
    req.pool
  );

const slippage=
  Number(
    req.slippagePct
  );

const amounts=
  (
    req.baseAmounts
    ??[]
  ).map(
    x=>new BN(
      String(x)
    )
  );

if(
  amounts.length!==2
){
  throw new Error(
    "EXPECTED_TWO_BASE_AMOUNTS"
  );
}

function parsePumpSell(
  ixs,
  expectedAmount
){
  const pumpIxs=
    ixs.filter(
      ix=>
        ix.programId.toBase58()
        ===req.pumpProgram
    );

  if(
    pumpIxs.length!==1
  ){
    throw new Error(
      "PUMP_SELL_IX_COUNT:"
      +pumpIxs.length
    );
  }

  const raw=
    Buffer.from(
      pumpIxs[0].data
    );

  if(
    raw.length<24
  ){
    throw new Error(
      "PUMP_SELL_DATA_TOO_SHORT:"
      +raw.length
    );
  }

  const baseIn=
    raw.readBigUInt64LE(
      8
    );

  const minQuoteOut=
    raw.readBigUInt64LE(
      16
    );

  if(
    baseIn.toString()
    !==expectedAmount.toString()
  ){
    throw new Error(
      "PUMP_SELL_INPUT_MISMATCH:"
      +baseIn.toString()
      +":expected="
      +expectedAmount.toString()
    );
  }

  return {
    baseIn:
      baseIn.toString(),

    minQuoteOut:
      minQuoteOut.toString()
  };
}

try{

  const online=
    new OnlinePumpAmmSdk(
      connection
    );

  // ---------------------------------------------------------
  // CRITICAL:
  // ONE physical Pump state snapshot for both calculations.
  // ---------------------------------------------------------

  const state=
    await online.swapSolanaState(
      pool,
      user
    );

  const firstIxs=
    await PUMP_AMM_SDK.sellBaseInput(
      state,
      amounts[0],
      slippage
    );

  const secondIxs=
    await PUMP_AMM_SDK.sellBaseInput(
      state,
      amounts[1],
      slippage
    );

  const first=
    parsePumpSell(
      firstIxs,
      amounts[0]
    );

  const second=
    parsePumpSell(
      secondIxs,
      amounts[1]
    );

  console.log(
    JSON.stringify({
      ok:true,

      stateSnapshots:
        1,

      first,
      second
    })
  );

}catch(e){

  console.log(
    JSON.stringify({
      ok:false,

      reason:
        e?.stack
        ??e?.message
        ??String(e)
    })
  );
}
