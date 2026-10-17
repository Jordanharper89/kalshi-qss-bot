import { pathToFileURL } from "node:url";
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

const PUMPSWAP_POOL =
  "8oo1APyu3UEGAQZVTVmw5Szjg5x9NT7Rw5c2GCta48Wj";

const INPUT_USDC_RAW = "100000000";
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
    headers: { "content-type": "application/json" },
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

function short(value) {
  return String(value).slice(0, 18);
}

console.log("[MTR-024] START");
console.log("[MTR-024] ATOMIC CLOSED-LOOP PURE-QUOTE PREFLIGHT");
console.log(`[RPC] ${RPC_URL}`);

const pump = await loadPackage("@pump-fun/pump-swap-sdk");
const meteora = await loadPackage("@meteora-ag/dlmm");
const web3 = await loadPackage("@solana/web3.js");
const spl = await loadPackage("@solana/spl-token");
const BNModule = await loadPackage("bn.js");

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

const BN = BNModule;

assert(OnlinePumpAmmSdk, "OnlinePumpAmmSdk unavailable");
assert(PUMP_AMM_SDK, "PUMP_AMM_SDK unavailable");
assert(buyQuoteInput, "pure buyQuoteInput unavailable");
assert(DLMM, "Meteora DLMM unavailable");

console.log("[SDK_EXPORTS] PASS");

const connection = new Connection(RPC_URL, "confirmed");

const candidate = new PublicKey(PUBLIC_CANDIDATE);
const fundedUsdc = new PublicKey(FUNDED_USDC_ACCOUNT);
const usdcMint = new PublicKey(USDC_MINT);
const tokenProgram = new PublicKey(TOKEN_PROGRAM);
const pumpProgram = new PublicKey(PUMPSWAP_PROGRAM);
const meteoraProgram = new PublicKey(METEORA_PROGRAM);
const pumpPool = new PublicKey(PUMPSWAP_POOL);

assert(candidate.toBase58() === PUBLIC_CANDIDATE, "candidate mismatch");
assert(fundedUsdc.toBase58() === FUNDED_USDC_ACCOUNT, "funded account mismatch");
assert(usdcMint.toBase58() === USDC_MINT, "USDC mismatch");
assert(tokenProgram.equals(TOKEN_PROGRAM_ID), "Token Program mismatch");
assert(pumpProgram.equals(PUMP_AMM_PROGRAM_ID), "PumpSwap program mismatch");

console.log("[PROGRAM_IDS] PASS");
console.log(`[CANDIDATE] ${candidate.toBase58()}`);
console.log(`[PUMPSWAP_POOL] ${pumpPool.toBase58()}`);

/*
 * Verify the exact funded public proof account directly from chain.
 * No signing and no sending.
 */
const fundedInfo = await rpc("getAccountInfo", [
  fundedUsdc.toBase58(),
  { encoding: "jsonParsed" },
]);

assert(fundedInfo?.value, "funded USDC account missing");

const fundedOwner =
  fundedInfo.value.data?.parsed?.info?.owner;

const fundedMint =
  fundedInfo.value.data?.parsed?.info?.mint;

const fundedAmount =
  fundedInfo.value.data?.parsed?.info?.tokenAmount?.amount;

assert(fundedOwner === PUBLIC_CANDIDATE, "funded account owner mismatch");
assert(fundedMint === USDC_MINT, "funded account mint mismatch");
assert(BigInt(fundedAmount ?? "0") >= BigInt(INPUT_USDC_RAW),
  "funded USDC balance insufficient");

console.log(`[FUNDED_USDC_RAW] ${fundedAmount}`);
console.log("[USDC_FUNDING] PASS");

/*
 * Load the known live PumpSwap pool directly.
 * No Pump.fun discovery endpoint is used.
 */
const onlinePump = new OnlinePumpAmmSdk(connection);

const pumpState =
  await onlinePump.swapSolanaState(
    pumpPool,
    candidate
  );

assert(pumpState, "PumpSwap state unavailable");

const pumpBaseMint =
  pumpState.baseMint ??
  pumpState.pool?.baseMint;

const pumpQuoteMint =
  pumpState.pool?.quoteMint;

assert(pumpBaseMint, "PumpSwap base mint unavailable");
assert(pumpQuoteMint, "PumpSwap quote mint unavailable");

console.log(`[PUMPSWAP_BASE_MINT] ${pumpBaseMint.toBase58()}`);
console.log(`[PUMPSWAP_QUOTE_MINT] ${pumpQuoteMint.toBase58()}`);

assert(
  pumpQuoteMint.equals(usdcMint),
  "known PumpSwap pool is no longer USDC-quoted"
);

console.log("[PUMPSWAP_USDC_QUOTE] PASS");

/*
 * Exact pure quote.
 *
 * IMPORTANT:
 * PUMP_AMM_SDK.buyQuoteInput() is the instruction builder.
 * The exported buyQuoteInput() is the pure pricing function.
 */
const inputUsdc = new BN(INPUT_USDC_RAW);

const {
  base: pumpBaseOut,
  maxQuote: pumpMaxQuote,
} = buyQuoteInput({
  quote: inputUsdc,
  slippage: SLIPPAGE_PERCENT,
  baseReserve: pumpState.poolBaseAmount,
  quoteReserve: pumpState.poolQuoteAmount,
  virtualQuoteReserves:
    pumpState.pool?.virtualQuoteReserves ?? new BN(0),
  globalConfig: pumpState.globalConfig,
  feeConfig: pumpState.feeConfig,
  baseMint: pumpState.baseMint,
  baseMintAccount: pumpState.baseMintAccount,
  coinCreator: pumpState.pool.coinCreator,
  creator: pumpState.pool.creator,
  quoteMint: pumpState.pool.quoteMint,
  isMayhemMode: pumpState.pool.isMayhemMode,
  creatorFeeBps:
    pumpState.pool.creatorFeeBps ?? 0,
});

assert(pumpBaseOut?.gt?.(new BN(0)), "PumpSwap base output is zero");
assert(pumpMaxQuote?.gte?.(inputUsdc), "PumpSwap max quote below input");

console.log(`[PUMPSWAP_INPUT_USDC] ${inputUsdc.toString()}`);
console.log(`[PUMPSWAP_BASE_OUT] ${pumpBaseOut.toString()}`);
console.log(`[PUMPSWAP_MAX_QUOTE] ${pumpMaxQuote.toString()}`);
console.log("[PUMPSWAP_PURE_QUOTE] PASS");

/*
 * Build PumpSwap instructions from the exact pure quote.
 */
const pumpInstructions =
  await PUMP_AMM_SDK.buyInstructions(
    pumpState,
    pumpBaseOut,
    pumpMaxQuote
  );

assert(
  Array.isArray(pumpInstructions) &&
  pumpInstructions.length > 0,
  "PumpSwap instructions missing"
);

console.log(
  `[PUMPSWAP_INSTRUCTION_COUNT] ${pumpInstructions.length}`
);

/*
 * The SDK uses the candidate's canonical USDC ATA.
 * Replace only that source account with the verified funded account.
 *
 * Do not alter the PumpSwap program accounts.
 */
const canonicalUsdcAta =
  getAssociatedTokenAddressSync(
    usdcMint,
    candidate,
    false,
    TOKEN_PROGRAM_ID
  );

let pumpInputMetaCount = 0;

for (const instruction of pumpInstructions) {
  for (const key of instruction.keys) {
    if (key.pubkey.equals(canonicalUsdcAta)) {
      key.pubkey = fundedUsdc;
      key.isWritable = true;
      pumpInputMetaCount++;
    }
  }
}

assert(
  pumpInputMetaCount >= 1,
  "PumpSwap canonical USDC input account was not found"
);

console.log(
  `[PUMPSWAP_FUNDED_INPUT_REBINDS] ${pumpInputMetaCount}`
);
console.log("[PUMPSWAP_FUNDED_INPUT] PASS");

/*
 * Find a live Meteora DLMM pool for:
 *
 *     PumpSwap base mint <-> USDC
 *
 * The API is used only for market discovery.
 * The selected pool is then validated against live chain state
 * through the official Meteora SDK.
 */
console.log("[METEORA_DISCOVERY] querying DLMM pair universe");

const meteoraResponse =
  await fetch("https://dlmm-api.meteora.ag/pair/all");

assert(
  meteoraResponse.ok,
  `Meteora pair API HTTP ${meteoraResponse.status}`
);

const meteoraPairs =
  await meteoraResponse.json();

assert(
  Array.isArray(meteoraPairs),
  "Meteora pair API did not return an array"
);

function field(pair, names) {
  for (const name of names) {
    if (pair?.[name] !== undefined &&
        pair?.[name] !== null) {
      return pair[name];
    }
  }
  return null;
}

const matchingPairs = meteoraPairs.filter((pair) => {
  const address = field(pair, [
    "address",
    "pair_address",
    "lb_pair",
  ]);

  const x = field(pair, [
    "mint_x",
    "token_x_mint",
    "mintX",
  ]);

  const y = field(pair, [
    "mint_y",
    "token_y_mint",
    "mintY",
  ]);

  if (!address || !x || !y) {
    return false;
  }

  const pairMints = [
    String(x),
    String(y),
  ];

  return (
    pairMints.includes(pumpBaseMint.toBase58()) &&
    pairMints.includes(USDC_MINT)
  );
});

assert(
  matchingPairs.length > 0,
  "no Meteora DLMM pair found for PumpSwap base mint / USDC"
);

console.log(
  `[METEORA_MATCH_COUNT] ${matchingPairs.length}`
);

let meteoraPoolAddress = null;
let meteoraPool = null;

for (const candidatePair of matchingPairs) {
  const address = field(candidatePair, [
    "address",
    "pair_address",
    "lb_pair",
  ]);

  try {
    const testPool =
      await DLMM.create(
        connection,
        new PublicKey(address)
      );

    await testPool.refetchStates();

    const xMint =
      testPool.tokenX.mint?.address ??
      testPool.tokenX.publicKey ??
      testPool.tokenX;

    const yMint =
      testPool.tokenY.mint?.address ??
      testPool.tokenY.publicKey ??
      testPool.tokenY;

    const x = new PublicKey(xMint);
    const y = new PublicKey(yMint);

    const exactPair =
      (x.equals(pumpBaseMint) && y.equals(usdcMint)) ||
      (x.equals(usdcMint) && y.equals(pumpBaseMint));

    if (!exactPair) {
      continue;
    }

    meteoraPoolAddress = address;
    meteoraPool = testPool;

    break;
  } catch (error) {
    console.log(
      `[METEORA_CANDIDATE_SKIP] ${address} ${short(error?.message ?? error)}`
    );
  }
}

assert(
  meteoraPoolAddress && meteoraPool,
  "no live Meteora DLMM pool passed exact mint validation"
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
  (meteoraX.equals(pumpBaseMint) && meteoraY.equals(usdcMint)) ||
  (meteoraX.equals(usdcMint) && meteoraY.equals(pumpBaseMint)),
  "Meteora pair identity mismatch"
);

console.log(
  `[METEORA_TOKEN_X] ${meteoraX.toBase58()}`
);
console.log(
  `[METEORA_TOKEN_Y] ${meteoraY.toBase58()}`
);
console.log("[ATOMIC_PAIR_IDENTITY] PASS");

/*
 * PumpSwap outputs BASE.
 *
 * Meteora must consume BASE and output USDC.
 *
 * swapForY=true means X -> Y.
 */
const swapForY =
  meteoraX.equals(pumpBaseMint) &&
  meteoraY.equals(usdcMint);

const swapForX =
  meteoraY.equals(pumpBaseMint) &&
  meteoraX.equals(usdcMint);

assert(
  swapForY || swapForX,
  "unable to determine Meteora base-to-USDC direction"
);

console.log(
  `[METEORA_SWAP_FOR_Y] ${swapForY}`
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
  meteoraQuote?.minOutAmount?.gt?.(new BN(0)),
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
console.log("[METEORA_QUOTE] PASS");

/*
 * Build official Meteora swap transaction.
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
      inAmount: pumpBaseOut,
      lbPair: meteoraPool.pubkey,
      user: candidate,
      minOutAmount: meteoraQuote.minOutAmount,
      binArraysPubkey:
        meteoraQuote.binArraysPubkey,
    });
} catch (error) {
  if (error?.transaction) {
    meteoraTx = error.transaction;
    console.log("[METEORA_SWAP_TRANSACTION] recovered from SDK wrapper error");
  } else {
    throw error;
  }
}

assert(
  meteoraTx instanceof Transaction,
  "Meteora did not return legacy Transaction"
);

console.log("[METEORA_SWAP_TRANSACTION] CONSTRUCTED");

/*
 * Atomic composition:
 *
 * PumpSwap:
 *     USDC -> BASE
 *
 * Meteora:
 *     BASE -> USDC
 *
 * Both execute in one unsigned transaction.
 */
const atomicTx = new Transaction();

for (const ix of pumpInstructions) {
  atomicTx.add(ix);
}

for (const ix of meteoraTx.instructions) {
  atomicTx.add(ix);
}

atomicTx.feePayer = candidate;

const latest =
  await connection.getLatestBlockhash("confirmed");

atomicTx.recentBlockhash =
  latest.blockhash;

const unsignedBytes =
  atomicTx.serialize({
    requireAllSignatures: false,
    verifySignatures: false,
  });

assert(
  unsignedBytes.length <= 1232,
  `atomic legacy transaction too large: ${unsignedBytes.length} bytes`
);

console.log(`[ATOMIC_UNSIGNED_BYTES] ${unsignedBytes.length}`);
console.log(
  `[ATOMIC_INSTRUCTION_COUNT] ${atomicTx.instructions.length}`
);

/*
 * Direct JSON-RPC simulation.
 *
 * No Connection.simulateTransaction wrapper.
 * No signing.
 * No sending.
 */
const base64 =
  Buffer.from(unsignedBytes).toString("base64");

console.log(
  "[RAW_RPC_SIMULATION] method=simulateTransaction"
);
console.log("[RAW_RPC_ENCODING] base64");
console.log("[RAW_RPC_SIG_VERIFY] false");
console.log("[RAW_RPC_REPLACE_RECENT_BLOCKHASH] true");

const simulation =
  await rpc("simulateTransaction", [
    base64,
    {
      encoding: "base64",
      sigVerify: false,
      replaceRecentBlockhash: true,
      commitment: "confirmed",
    },
  ]);

if (simulation.err) {
  console.log(
    "[SIMULATION_LOGS]"
  );

  for (const line of simulation.logs ?? []) {
    console.log(line);
  }

  throw new Error(
    `[SIMULATION_FAILED] ${JSON.stringify(simulation.err)}`
  );
}

const logs = simulation.logs ?? [];

const pumpSeen =
  logs.some((line) =>
    line.includes(PUMPSWAP_PROGRAM)
  );

const meteoraSeen =
  logs.some((line) =>
    line.includes(METEORA_PROGRAM)
  );

assert(
  pumpSeen,
  "PumpSwap program did not appear in simulation logs"
);

assert(
  meteoraSeen,
  "Meteora program did not appear in simulation logs"
);

console.log(
  `[RAW_RPC_SIMULATION_UNITS] ${simulation.unitsConsumed ?? "unknown"}`
);
console.log("[PUMPSWAP_SIMULATION] PASS");
console.log("[METEORA_SIMULATION] PASS");
console.log("[ATOMIC_SIMULATION] PASS");

console.log("");
console.log("[MTR-024] ATOMIC TWO-LEG PREFLIGHT PASS");
console.log("[MTR-024] PUMPSWAP: USDC -> BASE");
console.log("[MTR-024] METEORA: BASE -> USDC");
console.log("[MTR-024] ONE UNSIGNED TRANSACTION");
console.log("[MTR-024] NO SIGNING.");
console.log("[MTR-024] NO SENDING.");
console.log("[MTR-024] NO CANONICAL EXECUTOR.");
