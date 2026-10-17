from pathlib import Path

TARGET = Path(
    "tools/pumpswap_funded_public_preflight/"
    "mtr_020_atomic_pumpswap_meteora_preflight.mjs"
)

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));

function resolvePackage(name) {
  return require.resolve(name, { paths: [process.cwd(), HERE] });
}

function loadPackage(name) {
  return require(resolvePackage(name));
}

const web3 = loadPackage("@solana/web3.js");
const spl = loadPackage("@solana/spl-token");
const DLMMModule = await import(resolvePackage("@meteora-ag/dlmm"));
const PumpModule = await import(resolvePackage("@pump-fun/pump-swap-sdk"));
const BNModule = loadPackage("bn.js");

const {
  Connection,
  PublicKey,
  Transaction,
} = web3;

const {
  NATIVE_MINT,
  TOKEN_PROGRAM_ID,
  TOKEN_2022_PROGRAM_ID,
  getAssociatedTokenAddressSync,
} = spl;

const DLMM = DLMMModule.default;
const {
  OnlinePumpAmmSdk,
  PUMP_AMM_SDK,
} = PumpModule;

const BN = BNModule.default ?? BNModule;

const RPC = "https://api.mainnet-beta.solana.com";

const PUBLIC_CANDIDATE =
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR";

const PUMP_AMM_PROGRAM =
  "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA";

const METEORA_PROGRAM =
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";

const USDC =
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

const INPUT_USDC = new BN("10000"); // 0.010000 USDC
const SLIPPAGE_BPS = 50;

const connection = new Connection(RPC, "confirmed");
const candidate = new PublicKey(PUBLIC_CANDIDATE);
const pumpProgram = new PublicKey(PUMP_AMM_PROGRAM);
const meteoraProgram = new PublicKey(METEORA_PROGRAM);
const usdcMint = new PublicKey(USDC);

console.log("[MTR-020] START");
console.log(`[RPC] ${RPC}`);
console.log("[MODE] UNSIGNED ATOMIC TWO-LEG SIMULATION ONLY");

function assertKey(name, value) {
  const pk = new PublicKey(value);
  console.log(`[KEY_CHECK_PASS] ${name}=${pk.toBase58()}`);
  return pk;
}

function instructionDataHex(ix) {
  return Buffer.from(ix.data ?? []).toString("hex");
}

function cloneMeta(meta, replacement) {
  return {
    pubkey: meta.pubkey.equals(replacement.oldKey)
      ? replacement.newKey
      : meta.pubkey,
    isSigner: meta.isSigner,
    isWritable: meta.isWritable,
  };
}

async function rpc(method, params) {
  const response = await fetch(RPC, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
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

const candidateKey = assertKey("PUBLIC_CANDIDATE", PUBLIC_CANDIDATE);
assertKey("PUMP_AMM_PROGRAM", PUMP_AMM_PROGRAM);
assertKey("METEORA_PROGRAM", METEORA_PROGRAM);
assertKey("USDC_MINT", USDC);

const candidateInfo = await connection.getAccountInfo(candidateKey);

if (!candidateInfo) {
  throw new Error("[CANDIDATE] account missing");
}

console.log(
  `[CANDIDATE_SOL_LAMPORTS] ${candidateInfo.lamports}`
);
console.log(
  `[CANDIDATE_SOL] ${(candidateInfo.lamports / 1e9).toFixed(9)}`
);

if (candidateInfo.lamports <= 0) {
  throw new Error("[CANDIDATE_SOL_FUNDING] FAIL");
}

console.log("[CANDIDATE_SOL_FUNDING] PASS");

const tokenRpc = await rpc("getTokenAccountsByOwner", [
  candidateKey.toBase58(),
  {
    mint: usdcMint.toBase58(),
  },
  {
    encoding: "jsonParsed",
  },
]);

const usdcAccounts = tokenRpc.value ?? [];

let fundedUsdcAccount = null;
let fundedUsdcRaw = 0n;

for (const entry of usdcAccounts) {
  const info = entry.account?.data?.parsed?.info;
  if (!info) continue;

  const raw = BigInt(info.tokenAmount?.amount ?? "0");

  if (raw > fundedUsdcRaw) {
    fundedUsdcRaw = raw;
    fundedUsdcAccount = new PublicKey(entry.pubkey);
  }
}

if (!fundedUsdcAccount || fundedUsdcRaw < BigInt(INPUT_USDC.toString())) {
  throw new Error(
    `[USDC_FUNDING] insufficient candidate USDC raw=${fundedUsdcRaw}`
  );
}

console.log(
  `[FUNDED_USDC_ACCOUNT] ${fundedUsdcAccount.toBase58()}`
);
console.log(`[FUNDED_USDC_RAW] ${fundedUsdcRaw}`);
console.log("[USDC_FUNDING] PASS");

const canonicalUsdcAta = getAssociatedTokenAddressSync(
  usdcMint,
  candidateKey,
  false,
  TOKEN_PROGRAM_ID
);

console.log(
  `[CANONICAL_USDC_ATA] ${canonicalUsdcAta.toBase58()}`
);

console.log("[DISCOVERY] querying current Pump.fun universe");

const discoveryResponse = await fetch(
  "https://frontend-api-v3.pump.fun/coins?offset=0&limit=100&sort=last_trade_timestamp&includeNsfw=false&order=DESC"
);

if (!discoveryResponse.ok) {
  throw new Error(
    `[DISCOVERY] HTTP ${discoveryResponse.status}`
  );
}

const coins = await discoveryResponse.json();

console.log(`[DISCOVERY_COIN_COUNT] ${coins.length}`);

const pumpSdk = new OnlinePumpAmmSdk(connection);

let pumpState = null;
let pumpCoin = null;
let pumpPool = null;

for (const coin of coins) {
  if (!coin?.complete) continue;
  if (!coin?.pump_swap_pool) continue;

  const poolKey = new PublicKey(coin.pump_swap_pool);

  try {
    const owner = await connection.getAccountInfo(poolKey);

    if (!owner || !owner.owner.equals(pumpProgram)) {
      continue;
    }

    const state = await pumpSdk.swapSolanaState(
      poolKey,
      candidateKey
    );

    if (!state?.pool) continue;

    const quoteMint = new PublicKey(state.pool.quoteMint);

    if (!quoteMint.equals(usdcMint)) {
      continue;
    }

    pumpState = state;
    pumpCoin = coin;
    pumpPool = poolKey;

    break;
  } catch {
    continue;
  }
}

if (!pumpState) {
  throw new Error(
    "[DISCOVERY] no current PumpSwap USDC-quoted pool found in sampled universe"
  );
}

const pumpBaseMint = new PublicKey(pumpState.pool.baseMint);

console.log("[PUMPSWAP_CANDIDATE] PASS");
console.log(`[PUMPSWAP_SYMBOL] ${pumpCoin.symbol ?? "UNKNOWN"}`);
console.log(`[PUMPSWAP_MINT] ${pumpBaseMint.toBase58()}`);
console.log(`[PUMPSWAP_POOL] ${pumpPool.toBase58()}`);
console.log(
  `[PUMPSWAP_QUOTE_MINT] ${new PublicKey(
    pumpState.pool.quoteMint
  ).toBase58()}`
);

if (!new PublicKey(pumpState.user).equals(candidateKey)) {
  throw new Error("[PUMPSWAP_USER_BINDING] FAIL");
}

console.log("[PUMPSWAP_USER_BINDING] PASS");

console.log(
  "[METEORA_DISCOVERY] loading current DLMM universe for token intersection"
);

const lbPairs = await DLMM.getLbPairs(connection, {
  cluster: "mainnet-beta",
});

console.log(`[METEORA_LB_PAIR_COUNT] ${lbPairs.length}`);

let meteoraPoolAddress = null;
let meteoraState = null;

for (const entry of lbPairs) {
  try {
    const pubkey =
      entry.publicKey ??
      entry.pubkey ??
      entry.address;

    if (!pubkey) continue;

    const poolAddress =
      pubkey instanceof PublicKey
        ? pubkey
        : new PublicKey(pubkey);

    const pool = await DLMM.create(
      connection,
      poolAddress,
      { cluster: "mainnet-beta" }
    );

    const x = pool.tokenX.mint.address
      ? new PublicKey(pool.tokenX.mint.address)
      : new PublicKey(pool.tokenX.publicKey ?? pool.tokenX.mint);

    const y = pool.tokenY.mint.address
      ? new PublicKey(pool.tokenY.mint.address)
      : new PublicKey(pool.tokenY.publicKey ?? pool.tokenY.mint);

    if (!x.equals(pumpBaseMint) && !y.equals(pumpBaseMint)) {
      continue;
    }

    meteoraPoolAddress = poolAddress;
    meteoraState = pool;

    break;
  } catch {
    continue;
  }
}

if (!meteoraPoolAddress || !meteoraState) {
  throw new Error(
    `[METEORA_DISCOVERY] no DLMM pool found for PumpSwap mint ${pumpBaseMint.toBase58()}`
  );
}

console.log("[METEORA_INTERSECTION] PASS");
console.log(
  `[METEORA_POOL] ${meteoraPoolAddress.toBase58()}`
);
console.log(
  `[METEORA_TOKEN_X] ${meteoraState.tokenX.publicKey.toBase58()}`
);
console.log(
  `[METEORA_TOKEN_Y] ${meteoraState.tokenY.publicKey.toBase58()}`
);

const pumpInputAccount =
  pumpState.userQuoteTokenAccount ??
  getAssociatedTokenAddressSync(
    usdcMint,
    candidateKey,
    false,
    TOKEN_PROGRAM_ID
  );

console.log(
  `[PUMPSWAP_CANONICAL_INPUT] ${pumpInputAccount.toBase58()}`
);
console.log(
  `[PUMPSWAP_FUNDED_INPUT] ${fundedUsdcAccount.toBase58()}`
);

const pumpInstructions =
  await PUMP_AMM_SDK.buyQuoteInput(
    pumpState,
    INPUT_USDC,
    5
  );

if (!pumpInstructions.length) {
  throw new Error("[PUMPSWAP_INSTRUCTIONS] EMPTY");
}

console.log(
  `[PUMPSWAP_INSTRUCTION_COUNT] ${pumpInstructions.length}`
);

const pumpBuyInstruction = [...pumpInstructions]
  .reverse()
  .find(ix =>
    ix.programId.equals(pumpProgram) &&
    ix.keys.some(k => k.pubkey.equals(pumpInputAccount))
  );

if (!pumpBuyInstruction) {
  throw new Error(
    "[PUMPSWAP_INPUT_BINDING] Buy instruction containing canonical USDC input not found"
  );
}

console.log("[PUMPSWAP_BUY_INSTRUCTION] FOUND");

const pumpReboundInstructions = pumpInstructions.map(ix => {
  if (ix !== pumpBuyInstruction) {
    return ix;
  }

  return new web3.TransactionInstruction({
    programId: ix.programId,
    keys: ix.keys.map(meta =>
      cloneMeta(meta, {
        oldKey: pumpInputAccount,
        newKey: fundedUsdcAccount,
      })
    ),
    data: ix.data,
  });
});

const pumpBindingCount =
  pumpBuyInstruction.keys.filter(k =>
    k.pubkey.equals(pumpInputAccount)
  ).length;

console.log(
  `[PUMPSWAP_CANONICAL_INPUT_META_COUNT] ${pumpBindingCount}`
);

if (pumpBindingCount !== 1) {
  throw new Error(
    "[PUMPSWAP_INPUT_BINDING] expected exactly one canonical input meta"
  );
}

console.log("[PUMPSWAP_FUNDED_INPUT_BINDING] PASS");

const pumpQuoteBase =
  PUMP_AMM_SDK.buyQuoteInput
    ? null
    : null;

// Calculate expected PumpSwap base output using the public
// high-level autocomplete calculation against the live state.
const baseOut =
  PUMP_AMM_SDK.swapAutocompleteBaseFromQuote
    ? await PUMP_AMM_SDK.swapAutocompleteBaseFromQuote(
        pumpState,
        INPUT_USDC,
        5,
        "quoteToBase"
      )
    : null;

if (!baseOut || !baseOut.gtn(0)) {
  throw new Error(
    "[PUMPSWAP_OUTPUT_QUOTE] SDK did not return positive base output"
  );
}

console.log(`[PUMPSWAP_BASE_OUT] ${baseOut.toString()}`);

const meteoraBaseIsX =
  meteoraState.tokenX.publicKey.equals(pumpBaseMint);

const swapForY = meteoraBaseIsX;

console.log(
  `[METEORA_DIRECTION] pump_token_is_tokenX=${meteoraBaseIsX}`
);
console.log(
  `[METEORA_SWAP_FOR_Y] ${swapForY}`
);

const binArrays =
  await meteoraState.getBinArrayForSwap(
    swapForY,
    4
  );

const meteoraQuote =
  meteoraState.swapQuote(
    baseOut,
    swapForY,
    new BN(SLIPPAGE_BPS),
    binArrays,
    false
  );

console.log(
  `[METEORA_INPUT_RAW] ${meteoraQuote.consumedInAmount.toString()}`
);
console.log(
  `[METEORA_OUTPUT_RAW] ${meteoraQuote.outAmount.toString()}`
);
console.log(
  `[METEORA_MIN_OUTPUT_RAW] ${meteoraQuote.minOutAmount.toString()}`
);

if (!meteoraQuote.consumedInAmount.eq(baseOut)) {
  throw new Error(
    "[ATOMIC_AMOUNT_BINDING] Meteora consumed amount differs from PumpSwap expected output"
  );
}

console.log("[ATOMIC_AMOUNT_BINDING] PASS");

const meteoraTx =
  await meteoraState.swap({
    inToken: meteoraBaseIsX
      ? meteoraState.tokenX.publicKey
      : meteoraState.tokenY.publicKey,
    outToken: meteoraBaseIsX
      ? meteoraState.tokenY.publicKey
      : meteoraState.tokenX.publicKey,
    inAmount: meteoraQuote.consumedInAmount,
    minOutAmount: meteoraQuote.minOutAmount,
    lbPair: meteoraState.pubkey,
    user: candidateKey,
    binArraysPubkey: meteoraQuote.binArraysPubkey,
  });

console.log("[METEORA_SWAP_TRANSACTION] CONSTRUCTED");

const atomicTx = new Transaction();

for (const ix of pumpReboundInstructions) {
  atomicTx.add(ix);
}

for (const ix of meteoraTx.instructions) {
  atomicTx.add(ix);
}

atomicTx.feePayer = candidateKey;

const { blockhash } =
  await connection.getLatestBlockhash("confirmed");

atomicTx.recentBlockhash = blockhash;

const serialized = atomicTx.serialize({
  requireAllSignatures: false,
  verifySignatures: false,
});

console.log(
  `[ATOMIC_UNSIGNED_TX_BYTES] ${serialized.length}`
);
console.log(
  `[ATOMIC_INSTRUCTION_COUNT] ${atomicTx.instructions.length}`
);

if (serialized.length > 1232) {
  console.log(
    `[ATOMIC_TX_SIZE_WARNING] ${serialized.length} bytes exceeds legacy packet target`
  );
}

const simulation = await rpc("simulateTransaction", [
  serialized.toString("base64"),
  {
    encoding: "base64",
    sigVerify: false,
    replaceRecentBlockhash: true,
    commitment: "confirmed",
  },
]);

console.log("[RAW_RPC_SIMULATION] method=simulateTransaction");
console.log("[RAW_RPC_ENCODING] base64");
console.log("[RAW_RPC_SIG_VERIFY] false");
console.log("[RAW_RPC_REPLACE_RECENT_BLOCKHASH] true");

if (simulation.err) {
  console.log(
    `[SIMULATION_RESULT] FAIL ${JSON.stringify(simulation.err)}`
  );

  if (simulation.logs) {
    console.log("[SIMULATION_LOGS_BEGIN]");
    for (const line of simulation.logs) {
      console.log(line);
    }
    console.log("[SIMULATION_LOGS_END]");
  }

  throw new Error(
    `[MTR-020] atomic simulation failed: ${JSON.stringify(simulation.err)}`
  );
}

console.log(
  `[RAW_RPC_SIMULATION_UNITS] ${simulation.unitsConsumed ?? "UNKNOWN"}`
);

console.log("[SIMULATION_RESULT] PASS");

if (simulation.logs) {
  console.log("[SIMULATION_LOGS_BEGIN]");
  for (const line of simulation.logs) {
    console.log(line);
  }
  console.log("[SIMULATION_LOGS_END]");
}

const sawPump =
  simulation.logs?.some(line =>
    line.includes(PUMP_AMM_PROGRAM)
  ) ?? false;

const sawMeteora =
  simulation.logs?.some(line =>
    line.includes(METEORA_PROGRAM)
  ) ?? false;

if (!sawPump) {
  throw new Error(
    "[ATOMIC_VENUE_PROOF] PumpSwap program absent from simulation logs"
  );
}

if (!sawMeteora) {
  throw new Error(
    "[ATOMIC_VENUE_PROOF] Meteora program absent from simulation logs"
  );
}

console.log("[PUMPSWAP_PROGRAM_EXECUTED] PASS");
console.log("[METEORA_PROGRAM_EXECUTED] PASS");
console.log("[ATOMIC_TWO_LEG_EXECUTION] PASS");

console.log("[MTR-020] ATOMIC TWO-LEG UNSIGNED SIMULATION COMPLETE");
console.log("[MTR-020] NO SIGNING.");
console.log("[MTR-020] NO SENDING.");
console.log("[MTR-020] NO CANONICAL EXECUTOR.");
'''

TARGET.write_text(code, encoding="utf-8")

print(f"[CREATED] {TARGET}")
print("[MTR-020] installer complete")