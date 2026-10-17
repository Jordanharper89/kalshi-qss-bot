from pathlib import Path

OUT = Path(
    "tools/pumpswap_funded_public_preflight/"
    "mtr_026_onchain_usdc_pumpswap_meteora_atomic.mjs"
)

OUT.parent.mkdir(parents=True, exist_ok=True)

code = r'''import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

const RPC_URL = "https://api.mainnet-beta.solana.com";

const PUBLIC_CANDIDATE =
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR";

const FUNDED_USDC_ACCOUNT =
  "6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5";

const USDC_MINT =
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

const TOKEN_PROGRAM =
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";

const PUMPSWAP_PROGRAM =
  "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA";

const METEORA_PROGRAM =
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";

/*
 * IMPORTANT:
 * BigInt is a function, NOT a constructor.
 */
const INPUT_USDC_RAW =
  BigInt("100000000");

const SLIPPAGE_PERCENT = 0.5;

function assert(condition, message) {
  if (!condition) {
    throw new Error(`[ASSERTION FAILED] ${message}`);
  }
}

async function loadPackage(name) {
  const resolved = require.resolve(name);
  const url = pathToFileURL(resolved).href;
  const imported = await import(url);
  return imported.default ?? imported;
}

async function rpc(method, params) {
  const response = await fetch(RPC_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
      method,
      params,
    }),
  });

  const json = await response.json();

  if (json.error) {
    throw new Error(
      `[RPC_ERROR] ${method}: ${JSON.stringify(json.error)}`
    );
  }

  return json.result;
}

console.log("[MTR-026] START");
console.log(
  "[MTR-026] ON-CHAIN USDC PUMPSWAP -> METEORA ATOMIC PREFLIGHT"
);
console.log(`[RPC] ${RPC_URL}`);

const pump =
  await loadPackage("@pump-fun/pump-swap-sdk");

const meteora =
  await loadPackage("@meteora-ag/dlmm");

const web3 =
  await loadPackage("@solana/web3.js");

const spl =
  await loadPackage("@solana/spl-token");

const BN =
  await loadPackage("bn.js");

const {
  OnlinePumpAmmSdk,
  PUMP_AMM_SDK,
  buyQuoteInput,
  PUMP_AMM_PROGRAM_ID,
} = pump;

const DLMM =
  meteora.DLMM ??
  meteora.default ??
  meteora;

const {
  Connection,
  PublicKey,
  Transaction,
} = web3;

const {
  TOKEN_PROGRAM_ID,
  getAssociatedTokenAddressSync,
} = spl;

assert(
  OnlinePumpAmmSdk,
  "OnlinePumpAmmSdk unavailable"
);

assert(
  PUMP_AMM_SDK,
  "PUMP_AMM_SDK unavailable"
);

assert(
  buyQuoteInput,
  "pure buyQuoteInput unavailable"
);

assert(
  DLMM,
  "Meteora DLMM unavailable"
);

console.log("[SDK_EXPORTS] PASS");

const connection =
  new Connection(
    RPC_URL,
    "confirmed"
  );

const candidate =
  new PublicKey(
    PUBLIC_CANDIDATE
  );

const fundedUsdc =
  new PublicKey(
    FUNDED_USDC_ACCOUNT
  );

const usdcMint =
  new PublicKey(
    USDC_MINT
  );

const tokenProgram =
  new PublicKey(
    TOKEN_PROGRAM
  );

const pumpProgram =
  new PublicKey(
    PUMPSWAP_PROGRAM
  );

const meteoraProgram =
  new PublicKey(
    METEORA_PROGRAM
  );

assert(
  pumpProgram.equals(
    PUMP_AMM_PROGRAM_ID
  ),
  "PumpSwap program mismatch"
);

assert(
  tokenProgram.equals(
    TOKEN_PROGRAM_ID
  ),
  "Token program mismatch"
);

console.log("[PROGRAM_IDS] PASS");
console.log(
  `[CANDIDATE] ${candidate.toBase58()}`
);

/*
 * ---------------------------------------------------------------
 * 1. Verify the exact public proof wallet's funded USDC account.
 * ---------------------------------------------------------------
 */

const fundedInfo =
  await rpc(
    "getAccountInfo",
    [
      fundedUsdc.toBase58(),
      {
        encoding: "jsonParsed",
      },
    ]
  );

assert(
  fundedInfo?.value,
  "funded USDC account missing"
);

const fundedParsed =
  fundedInfo.value.data?.parsed?.info;

assert(
  fundedParsed,
  "funded account parsed data missing"
);

assert(
  fundedParsed.owner ===
    PUBLIC_CANDIDATE,
  "funded USDC owner mismatch"
);

assert(
  fundedParsed.mint ===
    USDC_MINT,
  "funded USDC mint mismatch"
);

const fundedRaw =
  BigInt(
    fundedParsed.tokenAmount?.amount ??
    "0"
  );

assert(
  fundedRaw >=
    INPUT_USDC_RAW,
  "insufficient public USDC"
);

console.log(
  `[FUNDED_USDC_RAW] ${fundedRaw.toString()}`
);

console.log(
  "[USDC_FUNDING] PASS"
);

/*
 * ---------------------------------------------------------------
 * 2. Discover PumpSwap USDC pools directly from Solana.
 *
 * No Pump.fun API.
 * No Pump.fun universe discovery.
 * No 429 retry loop.
 *
 * PumpSwap pool:
 *   base_mint  offset = 43
 *   quote_mint offset = 75
 * ---------------------------------------------------------------
 */

const quoteMintOffset = 75;

const poolAccounts =
  await rpc(
    "getProgramAccounts",
    [
      PUMPSWAP_PROGRAM,
      {
        commitment: "confirmed",
        encoding: "base64",
        filters: [
          {
            memcmp: {
              offset: quoteMintOffset,
              bytes: USDC_MINT,
            },
          },
        ],
        dataSlice: {
          offset: 0,
          length: 0,
        },
      },
    ]
  );

assert(
  Array.isArray(poolAccounts),
  "PumpSwap program-account response invalid"
);

console.log(
  `[ONCHAIN_USDC_POOL_COUNT] ${poolAccounts.length}`
);

assert(
  poolAccounts.length > 0,
  "no on-chain PumpSwap USDC pools found"
);

/*
 * ---------------------------------------------------------------
 * 3. Load candidate pools through the official PumpSwap SDK.
 * ---------------------------------------------------------------
 */

const onlinePump =
  new OnlinePumpAmmSdk(
    connection
  );

let selectedPumpPool = null;
let selectedPumpState = null;

for (
  const account of poolAccounts
) {
  const poolKey =
    new PublicKey(
      account.pubkey
    );

  try {
    const state =
      await onlinePump.swapSolanaState(
        poolKey,
        candidate
      );

    if (!state?.pool) {
      continue;
    }

    const baseMint =
      state.baseMint;

    const quoteMint =
      state.pool.quoteMint;

    if (
      !quoteMint.equals(
        usdcMint
      )
    ) {
      continue;
    }

    const baseReserve =
      state.poolBaseAmount;

    const quoteReserve =
      state.poolQuoteAmount;

    if (
      !baseReserve?.gt?.(
        new BN(0)
      ) ||
      !quoteReserve?.gt?.(
        new BN(0)
      )
    ) {
      continue;
    }

    selectedPumpPool =
      poolKey;

    selectedPumpState =
      state;

    console.log(
      `[PUMPSWAP_POOL_SELECTED] ${poolKey.toBase58()}`
    );

    console.log(
      `[PUMPSWAP_BASE_MINT] ${baseMint.toBase58()}`
    );

    console.log(
      `[PUMPSWAP_QUOTE_MINT] ${quoteMint.toBase58()}`
    );

    console.log(
      `[PUMPSWAP_BASE_RESERVE] ${baseReserve.toString()}`
    );

    console.log(
      `[PUMPSWAP_QUOTE_RESERVE] ${quoteReserve.toString()}`
    );

    break;

  } catch (error) {
    console.log(
      `[PUMPSWAP_POOL_SKIP] ${poolKey.toBase58()}`
    );
  }
}

assert(
  selectedPumpPool &&
  selectedPumpState,
  "no live on-chain PumpSwap USDC pool could be loaded"
);

console.log(
  "[PUMPSWAP_ONCHAIN_DISCOVERY] PASS"
);

/*
 * ---------------------------------------------------------------
 * 4. Pure PumpSwap quote:
 *
 *     USDC -> BASE
 *
 * IMPORTANT:
 * exported buyQuoteInput() is the pure pricing function.
 * PUMP_AMM_SDK.buyInstructions() builds instructions.
 * ---------------------------------------------------------------
 */

const inputUsdc =
  new BN(
    INPUT_USDC_RAW.toString()
  );

const pumpQuote =
  buyQuoteInput({
    quote:
      inputUsdc,

    slippage:
      SLIPPAGE_PERCENT,

    baseReserve:
      selectedPumpState.poolBaseAmount,

    quoteReserve:
      selectedPumpState.poolQuoteAmount,

    virtualQuoteReserves:
      selectedPumpState.pool
        .virtualQuoteReserves ??
      new BN(0),

    globalConfig:
      selectedPumpState.globalConfig,

    feeConfig:
      selectedPumpState.feeConfig,

    baseMint:
      selectedPumpState.baseMint,

    baseMintAccount:
      selectedPumpState.baseMintAccount,

    coinCreator:
      selectedPumpState.pool.coinCreator,

    creator:
      selectedPumpState.pool.creator,

    quoteMint:
      selectedPumpState.pool.quoteMint,

    isMayhemMode:
      selectedPumpState.pool.isMayhemMode,

    creatorFeeBps:
      selectedPumpState.pool.creatorFeeBps ??
      new BN(0),
  });

assert(
  pumpQuote?.base?.gt?.(
    new BN(0)
  ),
  "PumpSwap quote returned zero base"
);

assert(
  pumpQuote?.maxQuote?.gte?.(
    inputUsdc
  ),
  "PumpSwap max quote below input"
);

const pumpBaseOut =
  pumpQuote.base;

const pumpMaxQuote =
  pumpQuote.maxQuote;

console.log(
  `[PUMPSWAP_INPUT_USDC] ${inputUsdc.toString()}`
);

console.log(
  `[PUMPSWAP_BASE_OUT] ${pumpBaseOut.toString()}`
);

console.log(
  `[PUMPSWAP_MAX_QUOTE] ${pumpMaxQuote.toString()}`
);

console.log(
  "[PUMPSWAP_PURE_QUOTE] PASS"
);

/*
 * ---------------------------------------------------------------
 * 5. Build official PumpSwap instructions.
 * ---------------------------------------------------------------
 */

const pumpInstructions =
  await PUMP_AMM_SDK.buyInstructions(
    selectedPumpState,
    pumpBaseOut,
    pumpMaxQuote
  );

assert(
  Array.isArray(
    pumpInstructions
  ) &&
  pumpInstructions.length > 0,
  "PumpSwap instructions missing"
);

console.log(
  `[PUMPSWAP_INSTRUCTION_COUNT] ${pumpInstructions.length}`
);

/*
 * The official builder expects the candidate's canonical USDC ATA.
 * The public proof wallet's actual funded account is different.
 *
 * Rebind ONLY the source USDC account.
 */

const canonicalUsdcAta =
  getAssociatedTokenAddressSync(
    usdcMint,
    candidate,
    false,
    TOKEN_PROGRAM_ID
  );

let pumpInputRebinds = 0;

for (
  const instruction of pumpInstructions
) {
  for (
    const key of instruction.keys
  ) {
    if (
      key.pubkey.equals(
        canonicalUsdcAta
      )
    ) {
      key.pubkey =
        fundedUsdc;

      key.isWritable =
        true;

      pumpInputRebinds++;
    }
  }
}

assert(
  pumpInputRebinds >= 1,
  "PumpSwap funded USDC source was not rebound"
);

console.log(
  `[PUMPSWAP_FUNDED_INPUT_REBINDS] ${pumpInputRebinds}`
);

console.log(
  "[PUMPSWAP_FUNDED_INPUT] PASS"
);

/*
 * ---------------------------------------------------------------
 * 6. Discover exact Meteora BASE/USDC pair.
 * ---------------------------------------------------------------
 */

console.log(
  "[METEORA_DISCOVERY] querying DLMM pair universe"
);

const meteoraResponse =
  await fetch(
    "https://dlmm-api.meteora.ag/pair/all"
  );

assert(
  meteoraResponse.ok,
  `Meteora pair API HTTP ${meteoraResponse.status}`
);

const meteoraPairs =
  await meteoraResponse.json();

assert(
  Array.isArray(
    meteoraPairs
  ),
  "Meteora pair response invalid"
);

const targetBaseMint =
  selectedPumpState.baseMint;

function getField(
  object,
  names
) {
  for (
    const name of names
  ) {
    if (
      object?.[name] !== undefined &&
      object?.[name] !== null
    ) {
      return object[name];
    }
  }

  return null;
}

const matchingMeteoraPairs =
  meteoraPairs.filter(
    (pair) => {
      const address =
        getField(
          pair,
          [
            "address",
            "pair_address",
            "lb_pair",
          ]
        );

      const x =
        getField(
          pair,
          [
            "mint_x",
            "token_x_mint",
            "mintX",
          ]
        );

      const y =
        getField(
          pair,
          [
            "mint_y",
            "token_y_mint",
            "mintY",
          ]
        );

      if (
        !address ||
        !x ||
        !y
      ) {
        return false;
      }

      return (
        (
          String(x) ===
            targetBaseMint.toBase58() &&
          String(y) ===
            USDC_MINT
        ) ||
        (
          String(y) ===
            targetBaseMint.toBase58() &&
          String(x) ===
            USDC_MINT
        )
      );
    }
  );

console.log(
  `[METEORA_MATCH_COUNT] ${matchingMeteoraPairs.length}`
);

assert(
  matchingMeteoraPairs.length > 0,
  "no Meteora BASE/USDC pair found"
);

let meteoraPool = null;
let meteoraPoolAddress = null;

for (
  const pair of matchingMeteoraPairs
) {
  const address =
    getField(
      pair,
      [
        "address",
        "pair_address",
        "lb_pair",
      ]
    );

  try {
    const pool =
      await DLMM.create(
        connection,
        new PublicKey(address)
      );

    await pool.refetchStates();

    const x =
      new PublicKey(
        pool.tokenX.mint?.address ??
        pool.tokenX.publicKey ??
        pool.tokenX
      );

    const y =
      new PublicKey(
        pool.tokenY.mint?.address ??
        pool.tokenY.publicKey ??
        pool.tokenY
      );

    const exactPair =
      (
        x.equals(
          targetBaseMint
        ) &&
        y.equals(
          usdcMint
        )
      ) ||
      (
        y.equals(
          targetBaseMint
        ) &&
        x.equals(
          usdcMint
        )
      );

    if (!exactPair) {
      continue;
    }

    meteoraPool =
      pool;

    meteoraPoolAddress =
      address;

    break;

  } catch {
    console.log(
      `[METEORA_POOL_SKIP] ${address}`
    );
  }
}

assert(
  meteoraPool &&
  meteoraPoolAddress,
  "no live Meteora BASE/USDC pool passed exact validation"
);

console.log(
  `[METEORA_POOL] ${meteoraPoolAddress}`
);

const meteoraX =
  new PublicKey(
    meteoraPool.tokenX.mint?.address ??
    meteoraPool.tokenX.publicKey ??
    meteoraPool.tokenX
  );

const meteoraY =
  new PublicKey(
    meteoraPool.tokenY.mint?.address ??
    meteoraPool.tokenY.publicKey ??
    meteoraPool.tokenY
  );

assert(
  (
    meteoraX.equals(
      targetBaseMint
    ) &&
    meteoraY.equals(
      usdcMint
    )
  ) ||
  (
    meteoraY.equals(
      targetBaseMint
    ) &&
    meteoraX.equals(
      usdcMint
    )
  ),
  "Meteora exact pair identity failed"
);

console.log(
  `[METEORA_TOKEN_X] ${meteoraX.toBase58()}`
);

console.log(
  `[METEORA_TOKEN_Y] ${meteoraY.toBase58()}`
);

console.log(
  "[ATOMIC_PAIR_IDENTITY] PASS"
);

/*
 * ---------------------------------------------------------------
 * 7. Meteora BASE -> USDC quote.
 * ---------------------------------------------------------------
 */

const swapForY =
  meteoraX.equals(
    targetBaseMint
  ) &&
  meteoraY.equals(
    usdcMint
  );

const binArrays =
  await meteoraPool.getBinArrayForSwap(
    swapForY,
    4
  );

assert(
  binArrays.length > 0,
  "Meteora bin arrays unavailable"
);

const meteoraQuote =
  await meteoraPool.swapQuote(
    pumpBaseOut,
    swapForY,
    new BN(50),
    binArrays,
    false
  );

assert(
  meteoraQuote?.minOutAmount?.gt?.(
    new BN(0)
  ),
  "Meteora minimum USDC output is zero"
);

console.log(
  `[METEORA_INPUT_BASE] ${pumpBaseOut.toString()}`
);

console.log(
  `[METEORA_MIN_USDC_OUT] ${meteoraQuote.minOutAmount.toString()}`
);

console.log(
  `[METEORA_BIN_ARRAYS] ${binArrays.length}`
);

console.log(
  "[METEORA_QUOTE] PASS"
);

/*
 * ---------------------------------------------------------------
 * 8. Build official Meteora transaction.
 * ---------------------------------------------------------------
 */

let meteoraTx;

try {
  meteoraTx =
    await meteoraPool.swap({
      inToken:
        swapForY
          ? meteoraX
          : meteoraY,

      outToken:
        swapForY
          ? meteoraY
          : meteoraX,

      inAmount:
        pumpBaseOut,

      lbPair:
        meteoraPool.pubkey,

      user:
        candidate,

      minOutAmount:
        meteoraQuote.minOutAmount,

      binArraysPubkey:
        meteoraQuote.binArraysPubkey,
    });

} catch (error) {
  if (
    error?.transaction
  ) {
    meteoraTx =
      error.transaction;

    console.log(
      "[METEORA_SWAP_TRANSACTION] recovered"
    );
  } else {
    throw error;
  }
}

assert(
  meteoraTx instanceof Transaction,
  "Meteora did not return legacy Transaction"
);

console.log(
  "[METEORA_SWAP_TRANSACTION] CONSTRUCTED"
);

/*
 * ---------------------------------------------------------------
 * 9. Compose the two legs atomically.
 *
 * PumpSwap:
 *     USDC -> BASE
 *
 * Meteora:
 *     BASE -> USDC
 * ---------------------------------------------------------------
 */

const atomicTx =
  new Transaction();

for (
  const instruction of
  pumpInstructions
) {
  atomicTx.add(
    instruction
  );
}

for (
  const instruction of
  meteoraTx.instructions
) {
  atomicTx.add(
    instruction
  );
}

atomicTx.feePayer =
  candidate;

const latest =
  await connection.getLatestBlockhash(
    "confirmed"
  );

atomicTx.recentBlockhash =
  latest.blockhash;

const unsignedBytes =
  atomicTx.serialize({
    requireAllSignatures:
      false,

    verifySignatures:
      false,
  });

console.log(
  `[ATOMIC_UNSIGNED_BYTES] ${unsignedBytes.length}`
);

console.log(
  `[ATOMIC_INSTRUCTION_COUNT] ${atomicTx.instructions.length}`
);

assert(
  unsignedBytes.length <= 1232,
  `atomic transaction too large: ${unsignedBytes.length}`
);

/*
 * ---------------------------------------------------------------
 * 10. Raw JSON-RPC simulation.
 *
 * No signing.
 * No sending.
 * No canonical executor.
 * ---------------------------------------------------------------
 */

const base64 =
  Buffer
    .from(unsignedBytes)
    .toString("base64");

console.log(
  "[RAW_RPC_SIMULATION] method=simulateTransaction"
);

console.log(
  "[RAW_RPC_ENCODING] base64"
);

console.log(
  "[RAW_RPC_SIG_VERIFY] false"
);

console.log(
  "[RAW_RPC_REPLACE_RECENT_BLOCKHASH] true"
);

const simulation =
  await rpc(
    "simulateTransaction",
    [
      base64,
      {
        encoding:
          "base64",

        sigVerify:
          false,

        replaceRecentBlockhash:
          true,

        commitment:
          "confirmed",
      },
    ]
  );

if (
  simulation.err
) {
  console.log(
    "[SIMULATION_LOGS]"
  );

  for (
    const line of
    simulation.logs ?? []
  ) {
    console.log(line);
  }

  throw new Error(
    `[SIMULATION_FAILED] ${JSON.stringify(simulation.err)}`
  );
}

const logs =
  simulation.logs ?? [];

const pumpSeen =
  logs.some(
    (line) =>
      line.includes(
        PUMPSWAP_PROGRAM
      )
  );

const meteoraSeen =
  logs.some(
    (line) =>
      line.includes(
        METEORA_PROGRAM
      )
  );

assert(
  pumpSeen,
  "PumpSwap program absent from simulation logs"
);

assert(
  meteoraSeen,
  "Meteora program absent from simulation logs"
);

console.log(
  `[RAW_RPC_SIMULATION_UNITS] ${simulation.unitsConsumed ?? "unknown"}`
);

console.log(
  "[PUMPSWAP_SIMULATION] PASS"
);

console.log(
  "[METEORA_SIMULATION] PASS"
);

console.log(
  "[ATOMIC_SIMULATION] PASS"
);

console.log("");
console.log(
  "[MTR-026] ATOMIC TWO-LEG PREFLIGHT PASS"
);

console.log(
  "[MTR-026] PUMPSWAP: USDC -> BASE"
);

console.log(
  "[MTR-026] METEORA: BASE -> USDC"
);

console.log(
  "[MTR-026] ONE UNSIGNED TRANSACTION"
);

console.log(
  "[MTR-026] NO SIGNING."
);

console.log(
  "[MTR-026] NO SENDING."
);

console.log(
  "[MTR-026] NO CANONICAL EXECUTOR."
);
'''

OUT.write_text(code, encoding="utf-8")

print(f"[CREATED] {OUT}")
print("[MTR-026] installer complete")