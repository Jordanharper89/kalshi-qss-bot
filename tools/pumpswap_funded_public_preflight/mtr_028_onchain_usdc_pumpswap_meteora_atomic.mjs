import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

const RPC_URL =
  "https://api.mainnet-beta.solana.com";

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

const INPUT_USDC_RAW =
  BigInt("100000000");

function assert(condition, message) {
  if (!condition) {
    throw new Error(
      `[ASSERTION FAILED] ${message}`
    );
  }
}

async function loadPackage(name) {
  const resolved =
    require.resolve(name);

  const url =
    pathToFileURL(resolved).href;

  const imported =
    await import(url);

  return imported.default ?? imported;
}

async function rpc(method, params) {
  const response =
    await fetch(RPC_URL, {
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

  const json =
    await response.json();

  if (json.error) {
    throw new Error(
      `[RPC_ERROR] ${method}: ${JSON.stringify(json.error)}`
    );
  }

  return json.result;
}

console.log("[MTR-028] START");
console.log(
  "[MTR-028] ON-CHAIN PUMPSWAP -> METEORA ATOMIC PREFLIGHT"
);
console.log(`[RPC] ${RPC_URL}`);

const pump =
  await loadPackage(
    "@pump-fun/pump-swap-sdk"
  );

const meteora =
  await loadPackage(
    "@meteora-ag/dlmm"
  );

const web3 =
  await loadPackage(
    "@solana/web3.js"
  );

const spl =
  await loadPackage(
    "@solana/spl-token"
  );

const BN =
  await loadPackage(
    "bn.js"
  );

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
  "buyQuoteInput unavailable"
);

assert(
  DLMM,
  "DLMM unavailable"
);

assert(
  typeof DLMM.getLbPairs ===
    "function",
  "DLMM.getLbPairs unavailable"
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
 * PUBLIC PROOF USDC ACCOUNT
 * ---------------------------------------------------------------
 */

const fundedInfo =
  await rpc(
    "getAccountInfo",
    [
      fundedUsdc.toBase58(),
      {
        encoding:
          "jsonParsed",
      },
    ]
  );

assert(
  fundedInfo?.value,
  "funded USDC account missing"
);

const fundedParsed =
  fundedInfo.value
    .data
    ?.parsed
    ?.info;

assert(
  fundedParsed,
  "funded USDC parsed data missing"
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
    fundedParsed
      .tokenAmount
      ?.amount ??
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
 * PUMPSWAP ON-CHAIN USDC DISCOVERY
 * ---------------------------------------------------------------
 */

const pumpAccounts =
  await rpc(
    "getProgramAccounts",
    [
      PUMPSWAP_PROGRAM,
      {
        commitment:
          "confirmed",

        encoding:
          "base64",

        filters: [
          {
            memcmp: {
              offset: 75,
              bytes:
                USDC_MINT,
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
  Array.isArray(
    pumpAccounts
  ),
  "PumpSwap pool response invalid"
);

console.log(
  `[ONCHAIN_USDC_POOL_COUNT] ${pumpAccounts.length}`
);

assert(
  pumpAccounts.length > 0,
  "no PumpSwap USDC pools found"
);

const onlinePump =
  new OnlinePumpAmmSdk(
    connection
  );

let selectedPumpPool =
  null;

let selectedPumpState =
  null;

for (
  const account of pumpAccounts
) {
  const poolKey =
    new PublicKey(
      account.pubkey
    );

  try {
    const state =
      await onlinePump
        .swapSolanaState(
          poolKey,
          candidate
        );

    if (!state?.pool) {
      continue;
    }

    const quoteMint =
      state.pool.quoteMint;

    if (
      !quoteMint.equals(
        usdcMint
      )
    ) {
      continue;
    }

    if (
      !state.poolBaseAmount ||
      !state.poolQuoteAmount
    ) {
      continue;
    }

    if (
      !state.poolBaseAmount.gt(
        new BN(0)
      ) ||
      !state.poolQuoteAmount.gt(
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
      `[PUMPSWAP_BASE_MINT] ${state.baseMint.toBase58()}`
    );

    console.log(
      `[PUMPSWAP_QUOTE_MINT] ${quoteMint.toBase58()}`
    );

    console.log(
      `[PUMPSWAP_BASE_RESERVE] ${state.poolBaseAmount.toString()}`
    );

    console.log(
      `[PUMPSWAP_QUOTE_RESERVE] ${state.poolQuoteAmount.toString()}`
    );

    break;

  } catch {
    console.log(
      `[PUMPSWAP_POOL_SKIP] ${poolKey.toBase58()}`
    );
  }
}

assert(
  selectedPumpPool &&
  selectedPumpState,
  "no live PumpSwap USDC pool could be loaded"
);

console.log(
  "[PUMPSWAP_ONCHAIN_DISCOVERY] PASS"
);

/*
 * ---------------------------------------------------------------
 * PUMPSWAP PURE QUOTE
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
      0.5,

    baseReserve:
      selectedPumpState
        .poolBaseAmount,

    quoteReserve:
      selectedPumpState
        .poolQuoteAmount,

    virtualQuoteReserves:
      selectedPumpState
        .pool
        .virtualQuoteReserves ??
      new BN(0),

    globalConfig:
      selectedPumpState
        .globalConfig,

    feeConfig:
      selectedPumpState
        .feeConfig,

    baseMint:
      selectedPumpState
        .baseMint,

    baseMintAccount:
      selectedPumpState
        .baseMintAccount,

    coinCreator:
      selectedPumpState
        .pool
        .coinCreator,

    creator:
      selectedPumpState
        .pool
        .creator,

    quoteMint:
      selectedPumpState
        .pool
        .quoteMint,

    isMayhemMode:
      selectedPumpState
        .pool
        .isMayhemMode,

    creatorFeeBps:
      selectedPumpState
        .pool
        .creatorFeeBps ??
      new BN(0),
  });

assert(
  pumpQuote?.base?.gt?.(
    new BN(0)
  ),
  "PumpSwap base output is zero"
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
 * PUMPSWAP INSTRUCTIONS
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

const canonicalUsdcAta =
  getAssociatedTokenAddressSync(
    usdcMint,
    candidate,
    false,
    TOKEN_PROGRAM_ID
  );

let inputRebinds =
  0;

for (
  const instruction of
  pumpInstructions
) {
  for (
    const key of
    instruction.keys
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

      inputRebinds++;
    }
  }
}

assert(
  inputRebinds >= 1,
  "funded USDC source was not rebound"
);

console.log(
  `[PUMPSWAP_FUNDED_INPUT_REBINDS] ${inputRebinds}`
);

console.log(
  "[PUMPSWAP_FUNDED_INPUT] PASS"
);

/*
 * ---------------------------------------------------------------
 * METEORA ON-CHAIN DISCOVERY
 *
 * IMPORTANT:
 * getLbPairs() returns:
 *
 * {
 *   publicKey: PublicKey,
 *   account: {
 *     tokenXMint: PublicKey,
 *     tokenYMint: PublicKey,
 *     ...
 *   }
 * }
 *
 * Use the actual SDK account shape directly.
 * ---------------------------------------------------------------
 */

console.log(
  "[METEORA_DISCOVERY] using official DLMM.getLbPairs()"
);

const lbPairs =
  await DLMM.getLbPairs(
    connection,
    {
      cluster:
        "mainnet-beta",
    }
  );

assert(
  Array.isArray(
    lbPairs
  ),
  "DLMM.getLbPairs returned invalid result"
);

console.log(
  `[METEORA_LB_PAIR_COUNT] ${lbPairs.length}`
);

assert(
  lbPairs.length > 0,
  "no Meteora LB pairs discovered"
);

const targetBaseMint =
  selectedPumpState.baseMint;

let meteoraCandidates =
  [];

for (
  const pair of lbPairs
) {
  const pairAccount =
    pair.account;

  if (
    !pairAccount
  ) {
    continue;
  }

  const tokenXMint =
    pairAccount.tokenXMint;

  const tokenYMint =
    pairAccount.tokenYMint;

  if (
    !tokenXMint ||
    !tokenYMint
  ) {
    continue;
  }

  const x =
    tokenXMint instanceof PublicKey
      ? tokenXMint
      : new PublicKey(
          tokenXMint
        );

  const y =
    tokenYMint instanceof PublicKey
      ? tokenYMint
      : new PublicKey(
          tokenYMint
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

  if (
    exactPair
  ) {
    meteoraCandidates.push(
      {
        publicKey:
          pair.publicKey,

        account:
          pairAccount,

        tokenXMint:
          x,

        tokenYMint:
          y,
      }
    );
  }
}

console.log(
  `[METEORA_BASE_USDC_CANDIDATES] ${meteoraCandidates.length}`
);

assert(
  meteoraCandidates.length > 0,
  "no Meteora BASE/USDC pair found on-chain"
);

/*
 * ---------------------------------------------------------------
 * METEORA SDK VALIDATION
 * ---------------------------------------------------------------
 */

let meteoraPool =
  null;

let meteoraPoolAddress =
  null;

let meteoraX =
  null;

let meteoraY =
  null;

for (
  const candidatePair of
  meteoraCandidates
) {
  try {
    const pool =
      await DLMM.create(
        connection,
        candidatePair.publicKey,
        {
          cluster:
            "mainnet-beta",
        }
      );

    await pool.refetchStates();

    const x =
      new PublicKey(
        pool.tokenX.mint.address
      );

    const y =
      new PublicKey(
        pool.tokenY.mint.address
      );

    const exact =
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

    if (
      !exact
    ) {
      continue;
    }

    meteoraPool =
      pool;

    meteoraPoolAddress =
      candidatePair.publicKey;

    meteoraX =
      x;

    meteoraY =
      y;

    break;

  } catch {
    console.log(
      `[METEORA_POOL_SKIP] ${candidatePair.publicKey.toBase58()}`
    );
  }
}

assert(
  meteoraPool &&
  meteoraPoolAddress,
  "no Meteora BASE/USDC candidate passed SDK validation"
);

console.log(
  `[METEORA_POOL] ${meteoraPoolAddress.toBase58()}`
);

console.log(
  `[METEORA_TOKEN_X] ${meteoraX.toBase58()}`
);

console.log(
  `[METEORA_TOKEN_Y] ${meteoraY.toBase58()}`
);

console.log(
  "[METEORA_ONCHAIN_DISCOVERY] PASS"
);

console.log(
  "[ATOMIC_PAIR_IDENTITY] PASS"
);

/*
 * ---------------------------------------------------------------
 * METEORA QUOTE
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
  await meteoraPool
    .getBinArrayForSwap(
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
  "Meteora minimum output is zero"
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
 * METEORA TRANSACTION
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
  "Meteora transaction was not legacy Transaction"
);

console.log(
  "[METEORA_SWAP_TRANSACTION] CONSTRUCTED"
);

/*
 * ---------------------------------------------------------------
 * ATOMIC COMPOSITION
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
  await connection
    .getLatestBlockhash(
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
 * RAW UNSIGNED SIMULATION
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
    simulation.logs ??
    []
  ) {
    console.log(line);
  }

  throw new Error(
    `[SIMULATION_FAILED] ${JSON.stringify(simulation.err)}`
  );
}

const logs =
  simulation.logs ??
  [];

const pumpSeen =
  logs.some(
    line =>
      line.includes(
        PUMPSWAP_PROGRAM
      )
  );

const meteoraSeen =
  logs.some(
    line =>
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
  "[MTR-028] ATOMIC TWO-LEG PREFLIGHT PASS"
);

console.log(
  "[MTR-028] PUMPSWAP: USDC -> BASE"
);

console.log(
  "[MTR-028] METEORA: BASE -> USDC"
);

console.log(
  "[MTR-028] ONE UNSIGNED TRANSACTION"
);

console.log(
  "[MTR-028] NO SIGNING."
);

console.log(
  "[MTR-028] NO SENDING."
);

console.log(
  "[MTR-028] NO CANONICAL EXECUTOR."
);
