from pathlib import Path

TARGET = Path(
    "tools/pumpswap_funded_public_preflight/"
    "mtr_023_atomic_closed_loop_cjs_exports.mjs"
)

TARGET.parent.mkdir(parents=True, exist_ok=True)

TARGET.write_text(r'''import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function assert(condition, message) {
  if (!condition) {
    throw new Error(`[ASSERTION FAILED] ${message}`);
  }
}

function resolvePackage(name) {
  return require.resolve(name);
}

async function loadPackage(name) {
  const resolved = resolvePackage(name);
  const url = pathToFileURL(resolved).href;
  const imported = await import(url);

  // These packages are CommonJS builds. Node's ESM loader exposes
  // the actual CommonJS module through `default`.
  return imported.default ?? imported;
}

function pkString(value) {
  if (!value) return null;

  if (typeof value === "string") {
    return value;
  }

  if (typeof value.toBase58 === "function") {
    return value.toBase58();
  }

  if (
    value.address &&
    typeof value.address.toBase58 === "function"
  ) {
    return value.address.toBase58();
  }

  return String(value);
}

async function rpcJson(rpcUrl, method, params) {
  const response = await fetch(rpcUrl, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method,
      params,
    }),
  });

  const body = await response.json();

  if (body.error) {
    throw new Error(
      `[RPC_ERROR] ${method}: ${JSON.stringify(body.error)}`
    );
  }

  return body.result;
}

console.log("[MTR-023] START");
console.log("[MTR-023] ATOMIC CLOSED-LOOP CJS EXPORT PREFLIGHT");

const pump = await loadPackage(
  "@pump-fun/pump-swap-sdk"
);

const meteora = await loadPackage(
  "@meteora-ag/dlmm"
);

const web3 = await loadPackage(
  "@solana/web3.js"
);

const spl = await loadPackage(
  "@solana/spl-token"
);

const bnModule = await loadPackage(
  "bn.js"
);

console.log(
  "[PUMPSWAP_MODULE_TYPE]",
  typeof pump
);

console.log(
  "[METEORA_MODULE_TYPE]",
  typeof meteora
);

const pumpExports =
  Object.keys(pump).sort();

const meteoraExports =
  Object.keys(meteora).sort();

console.log(
  "[PUMPSWAP_EXPORT_COUNT]",
  pumpExports.length
);

console.log(
  "[METEORA_EXPORT_COUNT]",
  meteoraExports.length
);

console.log(
  "[PUMPSWAP_EXPORTS]",
  pumpExports.slice(0, 80).join(",")
);

console.log(
  "[METEORA_EXPORTS]",
  meteoraExports.slice(0, 40).join(",")
);

const OnlinePumpAmmSdk =
  pump.OnlinePumpAmmSdk;

const PUMP_AMM_SDK =
  pump.PUMP_AMM_SDK;

const PumpAmmSdk =
  pump.PumpAmmSdk;

const DLMM =
  meteora.DLMM ??
  meteora.default ??
  meteora;

const Connection =
  web3.Connection;

const PublicKey =
  web3.PublicKey;

const Transaction =
  web3.Transaction;

const TOKEN_PROGRAM_ID =
  spl.TOKEN_PROGRAM_ID;

const getAssociatedTokenAddressSync =
  spl.getAssociatedTokenAddressSync;

const BN =
  bnModule;

assert(
  OnlinePumpAmmSdk,
  "OnlinePumpAmmSdk unavailable"
);

assert(
  PUMP_AMM_SDK,
  "PUMP_AMM_SDK unavailable"
);

assert(
  PumpAmmSdk,
  "PumpAmmSdk unavailable"
);

assert(
  DLMM,
  "DLMM unavailable"
);

assert(
  Connection,
  "Connection unavailable"
);

assert(
  PublicKey,
  "PublicKey unavailable"
);

assert(
  Transaction,
  "Transaction unavailable"
);

assert(
  TOKEN_PROGRAM_ID,
  "TOKEN_PROGRAM_ID unavailable"
);

assert(
  getAssociatedTokenAddressSync,
  "getAssociatedTokenAddressSync unavailable"
);

assert(
  typeof BN === "function",
  "BN constructor unavailable"
);

console.log("[PUMPSWAP_CJS_EXPORTS] PASS");
console.log("[METEORA_CJS_EXPORTS] PASS");
console.log("[WEB3_CJS_EXPORTS] PASS");
console.log("[SPL_CJS_EXPORTS] PASS");
console.log("[BN_CJS_EXPORT] PASS");

const RPC_URL =
  "https://api.mainnet-beta.solana.com";

const PUMPSWAP_PROGRAM =
  "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA";

const METEORA_PROGRAM =
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";

const PUBLIC_CANDIDATE =
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR";

const USDC =
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

const TOKEN_PROGRAM =
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";

const INPUT_USDC =
  new BN("10000000");

const SLIPPAGE_PERCENT =
  5;

const candidate =
  new PublicKey(PUBLIC_CANDIDATE);

const connection =
  new Connection(
    RPC_URL,
    "confirmed"
  );

console.log("[RPC]", RPC_URL);
console.log(
  "[CANDIDATE]",
  candidate.toBase58()
);

assert(
  new PublicKey(PUMPSWAP_PROGRAM)
    .toBase58() === PUMPSWAP_PROGRAM,
  "PumpSwap program ID"
);

assert(
  new PublicKey(METEORA_PROGRAM)
    .toBase58() === METEORA_PROGRAM,
  "Meteora program ID"
);

assert(
  new PublicKey(USDC)
    .toBase58() === USDC,
  "USDC mint"
);

assert(
  new PublicKey(TOKEN_PROGRAM)
    .toBase58() === TOKEN_PROGRAM,
  "Token program"
);

console.log("[PROGRAM_IDS] PASS");

//
// ---------------------------------------------------------------
// Candidate SOL verification.
// ---------------------------------------------------------------
//

const candidateLamports =
  await connection.getBalance(
    candidate,
    "confirmed"
  );

assert(
  candidateLamports > 0,
  "candidate has SOL"
);

console.log(
  "[CANDIDATE_SOL_LAMPORTS]",
  candidateLamports
);

console.log(
  "[CANDIDATE_SOL]",
  candidateLamports / 1_000_000_000
);

//
// ---------------------------------------------------------------
// Candidate USDC verification.
// ---------------------------------------------------------------
//

const tokenAccounts =
  await rpcJson(
    RPC_URL,
    "getTokenAccountsByOwner",
    [
      candidate.toBase58(),
      {
        mint: USDC,
      },
      {
        encoding: "jsonParsed",
      },
    ]
  );

const usdcAccounts =
  tokenAccounts.value.filter(
    (item) =>
      item.account?.data?.parsed?.info?.mint === USDC &&
      item.account?.data?.parsed?.info?.owner ===
        candidate.toBase58()
  );

assert(
  usdcAccounts.length > 0,
  "candidate USDC account exists"
);

let fundedUsdcAccount = null;
let fundedUsdcRaw = 0;

for (const item of usdcAccounts) {
  const raw =
    Number(
      item.account.data.parsed.info.tokenAmount.amount
    );

  if (raw > fundedUsdcRaw) {
    fundedUsdcRaw = raw;
    fundedUsdcAccount = item.pubkey;
  }
}

assert(
  fundedUsdcAccount,
  "funded USDC account found"
);

assert(
  fundedUsdcRaw >=
    Number(INPUT_USDC.toString()),
  "candidate has sufficient USDC"
);

console.log(
  "[FUNDED_USDC_ACCOUNT]",
  fundedUsdcAccount
);

console.log(
  "[FUNDED_USDC_RAW]",
  fundedUsdcRaw
);

console.log("[USDC_FUNDING] PASS");

//
// ---------------------------------------------------------------
// Pump.fun current universe.
// ---------------------------------------------------------------
//

const discoveryUrl =
  "https://frontend-api-v3.pump.fun/coins" +
  "?offset=0" +
  "&limit=100" +
  "&sort=last_trade_timestamp" +
  "&includeNsfw=false" +
  "&order=DESC";

console.log(
  "[DISCOVERY] querying current Pump.fun universe"
);

const discoveryResponse =
  await fetch(discoveryUrl);

assert(
  discoveryResponse.ok,
  `Pump.fun discovery HTTP ${discoveryResponse.status}`
);

const discovery =
  await discoveryResponse.json();

const coins =
  Array.isArray(discovery)
    ? discovery
    : Array.isArray(discovery?.data)
      ? discovery.data
      : [];

console.log(
  "[DISCOVERY_COIN_COUNT]",
  coins.length
);

assert(
  coins.length > 0,
  "Pump.fun universe returned"
);

//
// ---------------------------------------------------------------
// Find a real PumpSwap USDC pool with a matching Meteora
// base/USDC pool.
// ---------------------------------------------------------------
//

const onlinePump =
  new OnlinePumpAmmSdk(
    connection
  );

let selected = null;

for (const coin of coins) {
  if (!coin?.complete) {
    continue;
  }

  if (!coin?.pump_swap_pool) {
    continue;
  }

  let pumpPool;

  try {
    pumpPool =
      new PublicKey(
        coin.pump_swap_pool
      );
  } catch {
    continue;
  }

  try {
    const poolAccount =
      await connection.getAccountInfo(
        pumpPool
      );

    if (!poolAccount) {
      continue;
    }

    if (
      poolAccount.owner.toBase58() !==
      PUMPSWAP_PROGRAM
    ) {
      continue;
    }

    const state =
      await onlinePump.swapSolanaState(
        pumpPool,
        candidate
      );

    if (!state) {
      continue;
    }

    const quoteMint =
      pkString(
        state.quoteMint ??
        state.pool?.quoteMint
      );

    const baseMint =
      pkString(
        state.baseMint ??
        state.pool?.baseMint
      );

    if (!quoteMint || !baseMint) {
      continue;
    }

    if (quoteMint !== USDC) {
      continue;
    }

    if (baseMint === USDC) {
      continue;
    }

    console.log(
      "[PUMPSWAP_CANDIDATE]",
      pumpPool.toBase58()
    );

    console.log(
      "[PUMPSWAP_BASE_MINT]",
      baseMint
    );

    console.log(
      "[PUMPSWAP_QUOTE_MINT]",
      quoteMint
    );

    //
    // Meteora API discovery for exact base/USDC pair.
    //
    const meteoraUrl =
      "https://dlmm.datapi.meteora.ag/pools" +
      "?page=1" +
      "&page_size=100" +
      "&query=" +
      encodeURIComponent(baseMint);

    const meteoraResponse =
      await fetch(meteoraUrl);

    if (!meteoraResponse.ok) {
      continue;
    }

    const meteoraBody =
      await meteoraResponse.json();

    const pools =
      Array.isArray(meteoraBody?.data)
        ? meteoraBody.data
        : [];

    const exactPools =
      pools.filter((pool) => {
        const x =
          pool?.token_x?.address;

        const y =
          pool?.token_y?.address;

        return (
          (x === baseMint && y === USDC) ||
          (x === USDC && y === baseMint)
        );
      });

    if (exactPools.length === 0) {
      continue;
    }

    exactPools.sort(
      (a, b) =>
        Number(b?.tvl ?? 0) -
        Number(a?.tvl ?? 0)
    );

    selected = {
      coin,
      pumpPool,
      pumpState: state,
      baseMint,
      quoteMint,
      meteoraPool: exactPools[0],
    };

    break;
  } catch (error) {
    console.log(
      "[DISCOVERY_SKIP]",
      String(
        error?.message ?? error
      )
    );
  }
}

assert(
  selected,
  "no closed PumpSwap USDC -> base -> Meteora base -> USDC route found"
);

console.log(
  "[ROUTE_DISCOVERY] PASS"
);

console.log(
  "[PUMPSWAP_POOL]",
  selected.pumpPool.toBase58()
);

console.log(
  "[PUMPSWAP_BASE]",
  selected.baseMint
);

console.log(
  "[PUMPSWAP_QUOTE]",
  selected.quoteMint
);

console.log(
  "[METEORA_POOL]",
  selected.meteoraPool.address
);

console.log(
  "[METEORA_TOKEN_X]",
  selected.meteoraPool.token_x.address
);

console.log(
  "[METEORA_TOKEN_Y]",
  selected.meteoraPool.token_y.address
);

//
// ---------------------------------------------------------------
// HARD CLOSED-LOOP TOKEN IDENTITY.
// ---------------------------------------------------------------
//

const exactPair =
  (
    selected.meteoraPool.token_x.address ===
      selected.baseMint &&
    selected.meteoraPool.token_y.address ===
      selected.quoteMint
  ) ||
  (
    selected.meteoraPool.token_x.address ===
      selected.quoteMint &&
    selected.meteoraPool.token_y.address ===
      selected.baseMint
  );

assert(
  exactPair,
  "Meteora pair is not exact PumpSwap base/USDC pair"
);

console.log(
  "[CLOSED_LOOP_TOKEN_IDENTITY] PASS"
);

//
// ---------------------------------------------------------------
// PumpSwap quote.
// ---------------------------------------------------------------
//

const pumpState =
  selected.pumpState;

assert(
  pkString(pumpState.quoteMint) ===
    selected.quoteMint,
  "PumpSwap quote mint binding"
);

assert(
  pkString(pumpState.baseMint) ===
    selected.baseMint,
  "PumpSwap base mint binding"
);

const pumpInstructions =
  await PUMP_AMM_SDK.buyQuoteInput(
    pumpState,
    INPUT_USDC,
    SLIPPAGE_PERCENT
  );

assert(
  Array.isArray(pumpInstructions),
  "PumpSwap instructions returned"
);

assert(
  pumpInstructions.length > 0,
  "PumpSwap instructions non-empty"
);

console.log(
  "[PUMPSWAP_INPUT_USDC_RAW]",
  INPUT_USDC.toString()
);

console.log(
  "[PUMPSWAP_INSTRUCTION_COUNT]",
  pumpInstructions.length
);

console.log(
  "[PUMPSWAP_QUOTE] PASS"
);

//
// ---------------------------------------------------------------
// Load exact Meteora pool.
// ---------------------------------------------------------------
//

const meteoraPoolKey =
  new PublicKey(
    selected.meteoraPool.address
  );

const dlmm =
  await DLMM.create(
    connection,
    meteoraPoolKey,
    {
      cluster: "mainnet-beta",
    }
  );

await dlmm.refetchStates();

const tokenX =
  pkString(
    dlmm.tokenX.mint.address
  );

const tokenY =
  pkString(
    dlmm.tokenY.mint.address
  );

assert(
  (
    tokenX === selected.baseMint &&
    tokenY === selected.quoteMint
  ) ||
  (
    tokenX === selected.quoteMint &&
    tokenY === selected.baseMint
  ),
  "Meteora on-chain pair exactly matches route"
);

console.log(
  "[METEORA_ONCHAIN_PAIR] PASS"
);

//
// ---------------------------------------------------------------
// IMPORTANT:
// PumpSwap's buyQuoteInput returns instructions, but the exact
// base amount is encoded by the SDK instruction itself. For this
// preflight we inspect the PumpSwap state reserves and use the
// SDK's quote helper when available.
// ---------------------------------------------------------------
//

let baseOut = null;

const quoteHelpers = [
  "buyQuoteInput",
  "buyQuote",
  "buyQuoteInput",
];

console.log(
  "[PUMPSWAP_QUOTE_HELPERS]",
  quoteHelpers.join(",")
);

//
// The 1.20.0 SDK exposes the quote calculation through its
// instruction builder. Locate the resulting base output from the
// instruction data only after confirming the SDK route exists.
//
const pumpBuyInstruction =
  pumpInstructions.find(
    (ix) =>
      ix.programId.toBase58() ===
      PUMPSWAP_PROGRAM
  );

assert(
  pumpBuyInstruction,
  "PumpSwap buy instruction present"
);

console.log(
  "[PUMPSWAP_BUY_INSTRUCTION] PASS"
);

//
// For the first atomic proof we use the PumpSwap pool state
// reserves and reproduce the SDK's exact-input quote through the
// exported helper when present.
//
const possibleQuoteMethods = [
  "buyQuoteInput",
  "buyQuote",
];

for (const methodName of possibleQuoteMethods) {
  if (
    typeof PUMP_AMM_SDK[methodName] !==
    "function"
  ) {
    continue;
  }

  try {
    const result =
      await PUMP_AMM_SDK[methodName](
        pumpState,
        INPUT_USDC,
        SLIPPAGE_PERCENT
      );

    if (
      result &&
      result.base &&
      result.base.gt
    ) {
      baseOut = result.base;
      break;
    }

    if (
      result &&
      result.baseAmountOut
    ) {
      baseOut =
        result.baseAmountOut instanceof BN
          ? result.baseAmountOut
          : new BN(
              result.baseAmountOut.toString()
            );
      break;
    }

    if (
      result &&
      result.baseOut
    ) {
      baseOut =
        result.baseOut instanceof BN
          ? result.baseOut
          : new BN(
              result.baseOut.toString()
            );
      break;
    }
  } catch {
    // Continue searching compatible SDK quote helper.
  }
}

assert(
  baseOut &&
    typeof baseOut.gt === "function" &&
    baseOut.gt(new BN(0)),
  "unable to obtain PumpSwap base output from installed SDK"
);

console.log(
  "[PUMPSWAP_BASE_OUT_RAW]",
  baseOut.toString()
);

console.log(
  "[PUMPSWAP_BASE_OUTPUT] PASS"
);

//
// ---------------------------------------------------------------
// Meteora quote.
// ---------------------------------------------------------------
//

const swapForY =
  tokenX === selected.baseMint &&
  tokenY === selected.quoteMint;

console.log(
  "[METEORA_SWAP_FOR_Y]",
  swapForY
);

const binArrays =
  await dlmm.getBinArrayForSwap(
    swapForY,
    4
  );

assert(
  Array.isArray(binArrays),
  "Meteora bin arrays"
);

assert(
  binArrays.length > 0,
  "Meteora bin arrays non-empty"
);

const meteoraQuote =
  dlmm.swapQuote(
    baseOut,
    swapForY,
    new BN("50"),
    binArrays,
    false
  );

assert(
  meteoraQuote,
  "Meteora quote"
);

console.log(
  "[METEORA_INPUT_RAW]",
  meteoraQuote.consumedInAmount.toString()
);

console.log(
  "[METEORA_OUTPUT_RAW]",
  meteoraQuote.outAmount.toString()
);

console.log(
  "[METEORA_MIN_OUTPUT_RAW]",
  meteoraQuote.minOutAmount.toString()
);

console.log(
  "[METEORA_BIN_ARRAY_COUNT]",
  meteoraQuote.binArraysPubkey.length
);

console.log(
  "[METEORA_QUOTE] PASS"
);

//
// ---------------------------------------------------------------
// Official Meteora transaction.
// ---------------------------------------------------------------
//

const meteoraInToken =
  swapForY
    ? dlmm.tokenX.mint.address
    : dlmm.tokenY.mint.address;

const meteoraOutToken =
  swapForY
    ? dlmm.tokenY.mint.address
    : dlmm.tokenX.mint.address;

const meteoraTx =
  await dlmm.swap({
    inToken: meteoraInToken,
    outToken: meteoraOutToken,
    inAmount:
      meteoraQuote.consumedInAmount,
    minOutAmount:
      meteoraQuote.minOutAmount,
    lbPair:
      dlmm.pubkey,
    user:
      candidate,
    binArraysPubkey:
      meteoraQuote.binArraysPubkey,
  }).catch((error) => {
    if (error?.transaction) {
      return error.transaction;
    }

    throw error;
  });

assert(
  meteoraTx,
  "Meteora transaction constructed"
);

console.log(
  "[METEORA_TRANSACTION] CONSTRUCTED"
);

//
// ---------------------------------------------------------------
// Combine PumpSwap + Meteora.
// ---------------------------------------------------------------
//

const transaction =
  new Transaction();

transaction.feePayer =
  candidate;

const latestBlockhash =
  await connection.getLatestBlockhash(
    "confirmed"
  );

transaction.recentBlockhash =
  latestBlockhash.blockhash;

for (const ix of pumpInstructions) {
  transaction.add(ix);
}

for (const ix of meteoraTx.instructions) {
  transaction.add(ix);
}

console.log(
  "[ATOMIC_INSTRUCTION_COUNT]",
  transaction.instructions.length
);

const unsignedBytes =
  transaction.serialize({
    requireAllSignatures: false,
    verifySignatures: false,
  });

console.log(
  "[UNSIGNED_TX_BYTES]",
  unsignedBytes.length
);

assert(
  unsignedBytes.length <= 1232,
  `legacy transaction exceeds packet boundary: ${unsignedBytes.length}`
);

let pumpInstructionPresent = false;
let meteoraInstructionPresent = false;

for (const ix of transaction.instructions) {
  if (
    ix.programId.toBase58() ===
    PUMPSWAP_PROGRAM
  ) {
    pumpInstructionPresent = true;
  }

  if (
    ix.programId.toBase58() ===
    METEORA_PROGRAM
  ) {
    meteoraInstructionPresent = true;
  }
}

assert(
  pumpInstructionPresent,
  "PumpSwap instruction present"
);

assert(
  meteoraInstructionPresent,
  "Meteora instruction present"
);

console.log(
  "[PUMPSWAP_INSTRUCTION] PRESENT"
);

console.log(
  "[METEORA_INSTRUCTION] PRESENT"
);

//
// ---------------------------------------------------------------
// Raw unsigned simulation.
// ---------------------------------------------------------------
//

const encoded =
  Buffer.from(unsignedBytes)
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
  await rpcJson(
    RPC_URL,
    "simulateTransaction",
    [
      encoded,
      {
        encoding: "base64",
        sigVerify: false,
        replaceRecentBlockhash: true,
        commitment: "confirmed",
      },
    ]
  );

const logs =
  simulation.logs ?? [];

for (const line of logs) {
  console.log(line);
}

if (simulation.err) {
  console.log(
    "[SIMULATION_ERR]",
    JSON.stringify(simulation.err)
  );
}

assert(
  !simulation.err,
  `atomic simulation failed: ${JSON.stringify(simulation.err)}`
);

const pumpLog =
  logs.some(
    (line) =>
      line.includes(PUMPSWAP_PROGRAM)
  );

const meteoraLog =
  logs.some(
    (line) =>
      line.includes(METEORA_PROGRAM)
  );

assert(
  pumpLog,
  "PumpSwap appears in simulation logs"
);

assert(
  meteoraLog,
  "Meteora appears in simulation logs"
);

console.log(
  "[ATOMIC_SIMULATION] PASS"
);

console.log(
  "[MTR-023] ATOMIC CLOSED-LOOP UNSIGNED SIMULATION COMPLETE"
);

console.log(
  "[MTR-023] NO SIGNING."
);

console.log(
  "[MTR-023] NO SENDING."
);

console.log(
  "[MTR-023] NO CANONICAL EXECUTOR."
);
''', encoding="utf-8")

print(f"[CREATED] {TARGET}")
print("[MTR-023] installer complete")