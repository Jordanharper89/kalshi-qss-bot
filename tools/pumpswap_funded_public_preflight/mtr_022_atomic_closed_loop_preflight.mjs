import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function resolvePackage(name) {
  return require.resolve(name);
}

async function loadPackage(name) {
  const resolved = resolvePackage(name);
  const url = pathToFileURL(resolved).href;
  return await import(url);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(`[ASSERTION FAILED] ${message}`);
  }
}

function pkString(value) {
  if (!value) return null;
  if (typeof value === "string") return value;
  if (typeof value.toBase58 === "function") return value.toBase58();
  if (value.address && typeof value.address.toBase58 === "function") {
    return value.address.toBase58();
  }
  return String(value);
}

async function rpcJson(rpcUrl, method, params) {
  const response = await fetch(rpcUrl, {
    method: "POST",
    headers: { "content-type": "application/json" },
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

const pumpModule = await loadPackage("@pump-fun/pump-swap-sdk");
const meteoraModule = await loadPackage("@meteora-ag/dlmm");
const web3Module = await loadPackage("@solana/web3.js");
const splModule = await loadPackage("@solana/spl-token");
const bnModule = await loadPackage("bn.js");

const {
  OnlinePumpAmmSdk,
  PUMP_AMM_SDK,
} = pumpModule;

const DLMM =
  meteoraModule.default ??
  meteoraModule.DLMM ??
  meteoraModule;

const {
  Connection,
  PublicKey,
  Transaction,
} = web3Module;

const {
  TOKEN_PROGRAM_ID,
  getAssociatedTokenAddressSync,
} = splModule;

const BN =
  bnModule.default ??
  bnModule;

assert(OnlinePumpAmmSdk, "OnlinePumpAmmSdk unavailable");
assert(PUMP_AMM_SDK, "PUMP_AMM_SDK unavailable");
assert(DLMM, "DLMM unavailable");
assert(Connection, "Connection unavailable");
assert(PublicKey, "PublicKey unavailable");
assert(Transaction, "Transaction unavailable");
assert(BN, "BN unavailable");

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
  new Connection(RPC_URL, "confirmed");

console.log("[MTR-022] START");
console.log("[MTR-022] ATOMIC CLOSED-LOOP PREFLIGHT");
console.log("[RPC]", RPC_URL);
console.log("[CANDIDATE]", candidate.toBase58());

assert(
  new PublicKey(PUMPSWAP_PROGRAM).toBase58() === PUMPSWAP_PROGRAM,
  "PumpSwap program ID"
);

assert(
  new PublicKey(METEORA_PROGRAM).toBase58() === METEORA_PROGRAM,
  "Meteora program ID"
);

assert(
  new PublicKey(USDC).toBase58() === USDC,
  "USDC mint"
);

assert(
  new PublicKey(TOKEN_PROGRAM).toBase58() === TOKEN_PROGRAM,
  "Token program"
);

console.log("[PROGRAM_IDS] PASS");

//
// ---------------------------------------------------------------------
// 1. Verify public candidate funding.
// ---------------------------------------------------------------------
//

const candidateInfo =
  await connection.getAccountInfo(candidate);

assert(candidateInfo, "candidate account exists");

const candidateLamports =
  await connection.getBalance(candidate, "confirmed");

console.log(
  "[CANDIDATE_SOL_LAMPORTS]",
  candidateLamports
);

console.log(
  "[CANDIDATE_SOL]",
  candidateLamports / 1_000_000_000
);

assert(
  candidateLamports > 0,
  "candidate has SOL"
);

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
  tokenAccounts.value
    .filter(
      (item) =>
        item.account?.data?.parsed?.info?.mint === USDC &&
        item.account?.data?.parsed?.info?.owner ===
          candidate.toBase58()
    );

assert(
  usdcAccounts.length > 0,
  "candidate has USDC token account"
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

console.log(
  "[FUNDED_USDC_ACCOUNT]",
  fundedUsdcAccount
);

console.log(
  "[FUNDED_USDC_RAW]",
  fundedUsdcRaw
);

assert(
  fundedUsdcRaw >= Number(INPUT_USDC.toString()),
  "candidate has enough USDC for proof input"
);

console.log("[USDC_FUNDING] PASS");

//
// ---------------------------------------------------------------------
// 2. Discover current PumpSwap graduated pools.
// ---------------------------------------------------------------------
//

const discoveryUrl =
  "https://frontend-api-v3.pump.fun/coins" +
  "?offset=0" +
  "&limit=100" +
  "&sort=last_trade_timestamp" +
  "&includeNsfw=false" +
  "&order=DESC";

console.log("[DISCOVERY] Pump.fun graduated universe");

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
  "Pump.fun returned coins"
);

//
// ---------------------------------------------------------------------
// 3. Use PumpSwap SDK state to find a USDC-quoted pool whose base
//    token also has a Meteora DLMM pool.
// ---------------------------------------------------------------------
//

const onlinePump =
  new OnlinePumpAmmSdk(connection);

let selected = null;

for (const coin of coins) {
  if (!coin?.complete) continue;
  if (!coin?.pump_swap_pool) continue;

  const mintString =
    coin.mint;

  if (!mintString) continue;

  let poolKey;

  try {
    poolKey =
      new PublicKey(coin.pump_swap_pool);
  } catch {
    continue;
  }

  try {
    const owner =
      await connection.getAccountInfo(poolKey);

    if (!owner) continue;

    if (
      owner.owner.toBase58() !==
      PUMPSWAP_PROGRAM
    ) {
      continue;
    }

    const state =
      await onlinePump.swapSolanaState(
        poolKey,
        candidate
      );

    if (!state) continue;

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
      poolKey.toBase58()
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
    // ---------------------------------------------------------------
    // Meteora indexed discovery for the exact pair:
    // PumpSwap base <-> PumpSwap quote (USDC)
    // ---------------------------------------------------------------
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

    const meteoraPool =
      exactPools[0];

    selected = {
      coin,
      pumpPool: poolKey,
      pumpState: state,
      baseMint,
      quoteMint,
      meteoraPool,
    };

    break;
  } catch (error) {
    console.log(
      "[DISCOVERY_SKIP]",
      mintString,
      String(error?.message ?? error)
    );
  }
}

assert(
  selected,
  "no current PumpSwap USDC/base pool with matching Meteora base/USDC pool"
);

console.log("[ROUTE_DISCOVERY] PASS");

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
// ---------------------------------------------------------------------
// 4. HARD CLOSED-LOOP ASSERTION.
// ---------------------------------------------------------------------
//

const meteoraHasBase =
  selected.meteoraPool.token_x.address ===
    selected.baseMint ||
  selected.meteoraPool.token_y.address ===
    selected.baseMint;

const meteoraHasQuote =
  selected.meteoraPool.token_x.address ===
    selected.quoteMint ||
  selected.meteoraPool.token_y.address ===
    selected.quoteMint;

assert(
  meteoraHasBase,
  "Meteora contains exact PumpSwap base mint"
);

assert(
  meteoraHasQuote,
  "Meteora contains exact PumpSwap quote mint"
);

console.log(
  "[CLOSED_LOOP_TOKEN_IDENTITY] PASS"
);

//
// ---------------------------------------------------------------------
// 5. PumpSwap exact-input quote.
// ---------------------------------------------------------------------
//

console.log("[PUMPSWAP] loading live state");

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
  "PumpSwap returned instructions"
);

assert(
  pumpInstructions.length > 0,
  "PumpSwap instruction set non-empty"
);

//
// Official SDK exposes the autocomplete calculation for the exact
// quote input. Use it only to determine the base amount that the
// PumpSwap buy instruction is designed to receive.
//
const pumpBaseOut =
  await PUMP_AMM_SDK.swapAutocompleteBaseFromQuote(
    selected.pumpPool,
    INPUT_USDC,
    SLIPPAGE_PERCENT,
    "quoteToBase"
  ).catch(() => null);

let baseOut =
  pumpBaseOut;

if (
  baseOut === null ||
  baseOut === undefined
) {
  //
  // Some SDK versions accept the state object instead of the pool key.
  //
  baseOut =
    await PUMP_AMM_SDK.swapAutocompleteBaseFromQuote(
      pumpState,
      INPUT_USDC,
      SLIPPAGE_PERCENT,
      "quoteToBase"
    );
}

assert(
  baseOut !== null &&
  baseOut !== undefined,
  "PumpSwap base output calculation"
);

if (!(baseOut instanceof BN)) {
  baseOut =
    new BN(baseOut.toString());
}

assert(
  baseOut.gt(new BN(0)),
  "PumpSwap base output positive"
);

console.log(
  "[PUMPSWAP_INPUT_USDC_RAW]",
  INPUT_USDC.toString()
);

console.log(
  "[PUMPSWAP_BASE_OUT_RAW]",
  baseOut.toString()
);

console.log(
  "[PUMPSWAP_INSTRUCTION_COUNT]",
  pumpInstructions.length
);

console.log("[PUMPSWAP_QUOTE] PASS");

//
// ---------------------------------------------------------------------
// 6. Meteora exact-input quote using PumpSwap's base output.
// ---------------------------------------------------------------------
//

const meteoraPoolKey =
  new PublicKey(
    selected.meteoraPool.address
  );

console.log(
  "[METEORA] loading exact discovered pool"
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
  pkString(dlmm.tokenX.mint.address);

const tokenY =
  pkString(dlmm.tokenY.mint.address);

assert(
  (tokenX === selected.baseMint &&
    tokenY === selected.quoteMint) ||
  (tokenX === selected.quoteMint &&
    tokenY === selected.baseMint),
  "Meteora on-chain token pair exactly matches PumpSwap pair"
);

console.log(
  "[METEORA_ONCHAIN_PAIR] PASS"
);

//
// Meteora swap direction:
// true  = X -> Y
// false = Y -> X
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

const meteoraSlippageBps =
  new BN("50");

const meteoraQuote =
  dlmm.swapQuote(
    baseOut,
    swapForY,
    meteoraSlippageBps,
    binArrays,
    false
  );

assert(
  meteoraQuote,
  "Meteora quote exists"
);

assert(
  meteoraQuote.consumedInAmount,
  "Meteora consumed input"
);

assert(
  meteoraQuote.outAmount,
  "Meteora output"
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

console.log("[METEORA_QUOTE] PASS");

//
// ---------------------------------------------------------------------
// 7. Build official Meteora transaction.
// ---------------------------------------------------------------------
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
    inAmount: meteoraQuote.consumedInAmount,
    minOutAmount: meteoraQuote.minOutAmount,
    lbPair: dlmm.pubkey,
    user: candidate,
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
// ---------------------------------------------------------------------
// 8. Combine both official instruction sets into ONE legacy transaction.
// ---------------------------------------------------------------------
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

//
// Legacy Solana packets have a hard practical size boundary.
// Do not send or sign if the physical proof cannot fit.
//
assert(
  unsignedBytes.length <= 1232,
  `atomic transaction exceeds legacy packet boundary: ${unsignedBytes.length}`
);

//
// ---------------------------------------------------------------------
// 9. Verify both venue programs are physically represented.
// ---------------------------------------------------------------------
//

const pumpProgram =
  new PublicKey(PUMPSWAP_PROGRAM);

const meteoraProgram =
  new PublicKey(METEORA_PROGRAM);

let pumpInstructionPresent = false;
let meteoraInstructionPresent = false;

for (const ix of transaction.instructions) {
  if (ix.programId.equals(pumpProgram)) {
    pumpInstructionPresent = true;
  }

  if (ix.programId.equals(meteoraProgram)) {
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
// ---------------------------------------------------------------------
// 10. Direct JSON-RPC unsigned simulation.
// ---------------------------------------------------------------------
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

if (simulation.err) {
  console.log(
    "[SIMULATION_ERR]",
    JSON.stringify(simulation.err)
  );
}

const logs =
  simulation.logs ?? [];

for (const line of logs) {
  console.log(line);
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
  "PumpSwap program appears in simulation logs"
);

assert(
  meteoraLog,
  "Meteora program appears in simulation logs"
);

console.log(
  "[ATOMIC_SIMULATION] PASS"
);

console.log(
  "[MTR-022] ATOMIC CLOSED-LOOP UNSIGNED SIMULATION COMPLETE"
);

console.log(
  "[MTR-022] NO SIGNING."
);

console.log(
  "[MTR-022] NO SENDING."
);

console.log(
  "[MTR-022] NO CANONICAL EXECUTOR."
);
