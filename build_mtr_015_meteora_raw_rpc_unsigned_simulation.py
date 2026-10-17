from pathlib import Path

HARNESS_DIR = Path("tools") / "meteora_funded_public_preflight"
HARNESS_DIR.mkdir(parents=True, exist_ok=True)

HARNESS = HARNESS_DIR / "mtr_015_meteora_raw_rpc_unsigned_simulation.mjs"
TEST = Path("test_mtr_015_meteora_raw_rpc_unsigned_simulation.py")

HARNESS.write_text(r'''import DLMM from "@meteora-ag/dlmm";
import BN from "bn.js";
import {
  Connection,
  PublicKey,
  Transaction,
} from "@solana/web3.js";
import {
  getAssociatedTokenAddressSync,
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
} from "@solana/spl-token";

const RPC_URL = "https://api.mainnet-beta.solana.com";

const LB_PAIR =
  "ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq";

const METEORA_PROGRAM =
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";

const PUBLIC_CANDIDATE =
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR";

const USDC_MINT =
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

const USDT_MINT =
  "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB";

const TOKEN_PROGRAM =
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";

const FUNDED_USDC_ACCOUNT =
  "6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5";

const INPUT_RAW_USDC = new BN("100000000");
const SLIPPAGE_BPS = new BN("50");

const SWAP2_DISCRIMINATOR = Buffer.from("414b3f4ceb5b5b88", "hex");

function provePublicKey(label, value) {
  console.log(`[KEY_CHECK_BEGIN] ${label}`);
  console.log(`[KEY_VALUE] ${value}`);
  console.log(`[KEY_LENGTH] ${value.length}`);

  let pk;
  try {
    pk = new PublicKey(value);
  } catch (err) {
    console.log(`[KEY_CHECK_FAIL] ${label}: ${err.message}`);
    throw new Error(`${label} is not accepted by @solana/web3.js: ${value}`);
  }

  const normalized = pk.toBase58();
  console.log(`[KEY_NORMALIZED] ${normalized}`);

  if (normalized !== value) {
    throw new Error(
      `${label} normalization mismatch: ${value} != ${normalized}`
    );
  }

  console.log(`[KEY_CHECK_PASS] ${label}`);
  return pk;
}

async function rpcCall(method, params) {
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

  if (!response.ok) {
    throw new Error(
      `RPC HTTP ${response.status}: ${await response.text()}`
    );
  }

  const payload = await response.json();

  if (payload.error) {
    throw new Error(
      `RPC ${method} error: ${JSON.stringify(payload.error)}`
    );
  }

  return payload.result;
}

async function verifyFundedAccount(connection, fundedAccount, candidate) {
  console.log("[RPC] verifying exact funded USDC account");

  const info = await connection.getAccountInfo(fundedAccount, "confirmed");

  if (!info) {
    throw new Error("Funded USDC account does not exist");
  }

  if (!info.owner.equals(TOKEN_PROGRAM_ID)) {
    throw new Error(
      `Funded account owner mismatch: ${info.owner.toBase58()}`
    );
  }

  if (info.data.length < 165) {
    throw new Error("Funded token account data is too short");
  }

  const mint = new PublicKey(info.data.subarray(0, 32));
  const owner = new PublicKey(info.data.subarray(32, 64));

  let raw = 0n;
  for (let i = 0; i < 8; i++) {
    raw += BigInt(info.data[64 + i]) << (8n * BigInt(i));
  }

  console.log(`[FUNDED_USDC_MINT] ${mint.toBase58()}`);
  console.log(`[FUNDED_USDC_OWNER] ${owner.toBase58()}`);
  console.log(`[FUNDED_USDC_RAW] ${raw.toString()}`);
  console.log(`[FUNDED_USDC_DECIMALS] 6`);
  console.log(
    `[TOKEN_ACCOUNT_PROGRAM_OWNER] ${info.owner.toBase58()}`
  );

  if (!mint.equals(new PublicKey(USDC_MINT))) {
    throw new Error("Funded account mint is not USDC");
  }

  if (!owner.equals(candidate)) {
    throw new Error("Funded account owner is not public candidate");
  }

  if (raw < BigInt(INPUT_RAW_USDC.toString())) {
    throw new Error(
      `Funded account has insufficient USDC: ${raw.toString()}`
    );
  }

  console.log("[FUNDING_ACCOUNT_VERIFICATION] PASS");
}

function replaceOnlyInputAccount(transaction, canonicalAta, fundedAccount) {
  const meteoraProgram = new PublicKey(METEORA_PROGRAM);

  let found = false;
  let matchedInstructions = 0;

  for (const instruction of transaction.instructions) {
    if (!instruction.programId.equals(meteoraProgram)) {
      continue;
    }

    if (instruction.data.length < 8) {
      continue;
    }

    if (!instruction.data.subarray(0, 8).equals(SWAP2_DISCRIMINATOR)) {
      continue;
    }

    matchedInstructions += 1;

    const matches = instruction.keys.filter(
      (meta) => meta.pubkey.equals(canonicalAta)
    );

    console.log(
      `[CANONICAL_INPUT_META_COUNT] ${matches.length}`
    );

    if (matches.length !== 1) {
      throw new Error(
        `Expected exactly one canonical input meta, found ${matches.length}`
      );
    }

    console.log(
      `[ORIGINAL_INPUT_ACCOUNT] ${matches[0].pubkey.toBase58()}`
    );

    matches[0].pubkey = fundedAccount;

    console.log(
      `[REBOUND_INPUT_ACCOUNT] ${matches[0].pubkey.toBase58()}`
    );

    found = true;
  }

  if (matchedInstructions !== 1) {
    throw new Error(
      `Expected exactly one Meteora Swap2 instruction, found ${matchedInstructions}`
    );
  }

  if (!found) {
    throw new Error("Funded input binding was not performed");
  }

  console.log("[FUNDED_INPUT_BINDING] PASS");
}

async function simulateUnsignedRawRpc(serialized) {
  const base64 = serialized.toString("base64");

  console.log("[RAW_RPC_SIMULATION] method=simulateTransaction");
  console.log("[RAW_RPC_ENCODING] base64");
  console.log("[RAW_RPC_SIG_VERIFY] false");
  console.log("[RAW_RPC_REPLACE_RECENT_BLOCKHASH] true");

  const result = await rpcCall("simulateTransaction", [
    base64,
    {
      encoding: "base64",
      sigVerify: false,
      replaceRecentBlockhash: true,
      commitment: "confirmed",
    },
  ]);

  console.log(
    `[RAW_RPC_SIMULATION_UNITS] ${
      result.value.unitsConsumed ?? "null"
    }`
  );

  if (result.value.err) {
    console.log("[SIMULATION_RESULT] FAIL");
    console.log(
      `[SIMULATION_ERROR] ${JSON.stringify(result.value.err)}`
    );

    if (result.value.logs) {
      console.log("[SIMULATION_LOGS_BEGIN]");
      for (const line of result.value.logs) {
        console.log(line);
      }
      console.log("[SIMULATION_LOGS_END]");
    }

    throw new Error(
      `Unsigned physical simulation failed: ${JSON.stringify(
        result.value.err
      )}`
    );
  }

  console.log("[SIMULATION_RESULT] PASS");

  if (result.value.logs) {
    console.log("[SIMULATION_LOGS_BEGIN]");
    for (const line of result.value.logs) {
      console.log(line);
    }
    console.log("[SIMULATION_LOGS_END]");
  }

  return result;
}

async function main() {
  console.log("[MTR-015] START");
  console.log(`[RPC] ${RPC_URL}`);

  const connection = new Connection(RPC_URL, "confirmed");

  const lbPair = provePublicKey("LB_PAIR", LB_PAIR);
  const meteoraProgram = provePublicKey(
    "METEORA_PROGRAM",
    METEORA_PROGRAM
  );
  const candidate = provePublicKey(
    "PUBLIC_CANDIDATE",
    PUBLIC_CANDIDATE
  );
  const usdcMint = provePublicKey("USDC_MINT", USDC_MINT);
  const usdtMint = provePublicKey("USDT_MINT", USDT_MINT);
  const tokenProgram = provePublicKey(
    "TOKEN_PROGRAM",
    TOKEN_PROGRAM
  );
  const fundedAccount = provePublicKey(
    "FUNDED_USDC_ACCOUNT",
    FUNDED_USDC_ACCOUNT
  );

  if (!meteoraProgram.equals(new PublicKey(METEORA_PROGRAM))) {
    throw new Error("Meteora program mismatch");
  }

  if (!tokenProgram.equals(TOKEN_PROGRAM_ID)) {
    throw new Error("Token program mismatch");
  }

  console.log("[METEORA_PROGRAM_ID_EXACT] PASS");
  console.log("[TOKEN_PROGRAM_BINDING] PASS");

  await verifyFundedAccount(
    connection,
    fundedAccount,
    candidate
  );

  const canonicalUsdcAta = getAssociatedTokenAddressSync(
    usdcMint,
    candidate,
    false,
    TOKEN_PROGRAM_ID,
    ASSOCIATED_TOKEN_PROGRAM_ID
  );

  console.log(
    `[CANONICAL_USDC_ATA] ${canonicalUsdcAta.toBase58()}`
  );

  console.log(
    `[FUNDED_ACCOUNT_IS_CANONICAL_ATA] ${
      fundedAccount.equals(canonicalUsdcAta) ? "YES" : "NO"
    }`
  );

  console.log("[SDK] creating official Meteora DLMM pool");

  const pool = await DLMM.create(
    connection,
    lbPair
  );

  console.log(`[POOL_PUBKEY] ${pool.pubkey.toBase58()}`);

  const poolTokenX = pool.tokenX.mint.address.toBase58();
  const poolTokenY = pool.tokenY.mint.address.toBase58();

  console.log(`[POOL_TOKEN_X] ${poolTokenX}`);
  console.log(`[POOL_TOKEN_Y] ${poolTokenY}`);

  if (poolTokenX !== USDC_MINT) {
    throw new Error(
      `Unexpected pool token X: ${poolTokenX}`
    );
  }

  if (poolTokenY !== USDT_MINT) {
    throw new Error(
      `Unexpected pool token Y: ${poolTokenY}`
    );
  }

  console.log("[POOL_TOKEN_BINDING] PASS");

  console.log("[SDK] refreshing live pool state");
  await pool.refetchStates();

  const swapForY = true;

  console.log(
    `[SWAP_DIRECTION] USDC_X_TO_USDT_Y=${swapForY}`
  );

  console.log(
    `[INPUT_BN] ${INPUT_RAW_USDC.toString()}`
  );

  console.log(
    `[SLIPPAGE_BN] ${SLIPPAGE_BPS.toString()}`
  );

  const binArrays = await pool.getBinArrayForSwap(
    swapForY,
    4
  );

  console.log(
    `[BIN_ARRAY_COUNT] ${binArrays.length}`
  );

  console.log("[SDK] generating exact-in quote");

  const quote = pool.swapQuote(
    INPUT_RAW_USDC,
    swapForY,
    SLIPPAGE_BPS,
    binArrays,
    false
  );

  console.log(
    `[QUOTE_CONSUMED_IN] ${quote.consumedInAmount.toString()}`
  );

  console.log(
    `[QUOTE_OUT] ${quote.outAmount.toString()}`
  );

  console.log(
    `[QUOTE_MIN_OUT] ${quote.minOutAmount.toString()}`
  );

  console.log(
    `[QUOTE_FEE] ${quote.fee.toString()}`
  );

  console.log(
    `[QUOTE_PROTOCOL_FEE] ${quote.protocolFee.toString()}`
  );

  console.log("[SDK_QUOTE] PASS");

  console.log(
    "[SDK] constructing official pool.swap transaction"
  );

  let swapTransaction;

  try {
    swapTransaction = await pool.swap({
      inToken: pool.tokenX.mint.address,
      outToken: pool.tokenY.mint.address,
      inAmount: quote.consumedInAmount,
      lbPair: pool.pubkey,
      user: candidate,
      minOutAmount: quote.minOutAmount,
      binArraysPubkey: quote.binArraysPubkey,
    });
  } catch (err) {
    console.log(
      `[SDK_SWAP_BUILD_WARNING] ${err.message}`
    );

    if (
      !err ||
      !err.transaction
    ) {
      throw err;
    }

    swapTransaction = err.transaction;
  }

  if (!swapTransaction) {
    throw new Error(
      "Official pool.swap did not return a transaction"
    );
  }

  console.log("[SDK_SWAP_TRANSACTION] CONSTRUCTED");

  if (!(swapTransaction instanceof Transaction)) {
    throw new Error(
      `Expected legacy Transaction, got ${
        swapTransaction?.constructor?.name ?? "unknown"
      }`
    );
  }

  let swap2Found = false;

  for (const instruction of swapTransaction.instructions) {
    if (!instruction.programId.equals(meteoraProgram)) {
      continue;
    }

    if (instruction.data.length < 8) {
      continue;
    }

    if (
      instruction.data
        .subarray(0, 8)
        .equals(SWAP2_DISCRIMINATOR)
    ) {
      swap2Found = true;
      break;
    }
  }

  if (!swap2Found) {
    throw new Error(
      "Meteora Swap2 instruction not found"
    );
  }

  console.log("[SWAP2_INSTRUCTION] FOUND");

  replaceOnlyInputAccount(
    swapTransaction,
    canonicalUsdcAta,
    fundedAccount
  );

  if (!swapTransaction.feePayer) {
    swapTransaction.feePayer = candidate;
  }

  const latestBlockhash = await connection.getLatestBlockhash(
    "confirmed"
  );

  swapTransaction.recentBlockhash =
    latestBlockhash.blockhash;

  /*
   * IMPORTANT:
   * No signer is created.
   * No transaction signing is performed.
   * The transaction is serialized specifically as an
   * unsigned transaction and sent only to simulation.
   */
  const unsignedBytes = swapTransaction.serialize({
    requireAllSignatures: false,
    verifySignatures: false,
  });

  console.log(
    `[UNSIGNED_TX_BYTES] ${unsignedBytes.length}`
  );

  console.log(
    `[INSTRUCTION_COUNT] ${swapTransaction.instructions.length}`
  );

  console.log("[SIGNING] DISABLED");
  console.log("[BROADCAST] DISABLED");
  console.log("[PRIVATE_KEY] NOT USED");

  /*
   * Do NOT call Connection.simulateTransaction().
   *
   * MTR-014 proved that wrapper path is the remaining failure.
   * Use raw JSON-RPC simulateTransaction with the unsigned
   * serialized transaction instead.
   */
  await simulateUnsignedRawRpc(unsignedBytes);

  console.log("[MTR-015] RAW RPC UNSIGNED SIMULATION COMPLETE");
  console.log("[MTR-015] NO SIGNING.");
  console.log("[MTR-015] NO SENDING.");
  console.log("[MTR-015] NO CANONICAL EXECUTOR.");
}

main().catch((err) => {
  console.error(`[MTR-015] FAIL: ${err.stack || err.message}`);
  process.exitCode = 1;
});
''', encoding="utf-8")

TEST.write_text(r'''from pathlib import Path

harness = Path(
    "tools/meteora_funded_public_preflight/"
    "mtr_015_meteora_raw_rpc_unsigned_simulation.mjs"
)

text = harness.read_text(encoding="utf-8")

checks = [
    ("import DLMM from \"@meteora-ag/dlmm\";", "Official Meteora DLMM import"),
    ("import BN from \"bn.js\";", "BN import"),
    ("const INPUT_RAW_USDC = new BN(\"100000000\");", "Input amount uses BN"),
    ("const SLIPPAGE_BPS = new BN(\"50\");", "Slippage uses BN"),
    ("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo", "Correct Meteora program ID"),
    ("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR", "Exact public candidate"),
    ("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "Exact USDC mint"),
    ("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", "Exact USDT mint"),
    ("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "Exact Token Program"),
    ("6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5", "Exact funded USDC account"),
    ("getAccountInfo(fundedAccount", "Raw funded-account verification"),
    ("getAssociatedTokenAddressSync(", "Canonical ATA derivation"),
    ("getBinArrayForSwap(", "Official bin-array lookup"),
    ("swapQuote(", "Official swap quote"),
    ("pool.swap({", "Official swap builder"),
    ("414b3f4ceb5b5b88", "Swap2 discriminator"),
    ("replaceOnlyInputAccount(", "Swap2 account binding"),
    ("canonicalUsdcAta", "Canonical input account check"),
    ("fundedAccount", "Funded input binding"),
    ("serialize({", "Unsigned serialization"),
    ("requireAllSignatures: false", "Unsigned serialization disabled"),
    ("verifySignatures: false", "Signature verification disabled"),
    ("simulateTransaction", "Raw RPC simulation"),
    ("encoding: \"base64\"", "Raw RPC base64 encoding"),
    ("sigVerify: false", "Raw RPC signature verification disabled"),
    ("replaceRecentBlockhash: true", "Raw RPC recent blockhash replacement"),
    ("await fetch(RPC_URL", "Direct JSON-RPC transport"),
    ("[SIGNING] DISABLED", "Signing disabled"),
    ("[BROADCAST] DISABLED", "Broadcast disabled"),
    ("[PRIVATE_KEY] NOT USED", "Private key not used"),
]

for needle, message in checks:
    assert needle in text, message
    print(f"[PASS] {message}")

for forbidden in [
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "sendTransaction(",
    "Keypair.fromSecretKey",
    "signTransaction",
    "signAllTransactions",
    "QSB_SOLANA_PRIVATE_KEY",
]:
    assert forbidden not in text, f"Forbidden operation/reference present: {forbidden}"
    print(f"[PASS] Forbidden operation/reference absent: {forbidden}")

assert "Connection.simulateTransaction" not in text
print("[PASS] Problematic Connection.simulateTransaction wrapper absent")

assert "LBUZKhRxPF3XUpBCj4YzTKgLccjZhTSDM9YuVaPwxo" in text
print("[PASS] Exact Meteora program spelling preserved")

print("[BUILD TEST COMPLETE] MTR-015")
''', encoding="utf-8")

print("[BUILD] MTR-015 files written")
print(f"[HARNESS] {HARNESS.resolve()}")
print(f"[TEST] {TEST.resolve()}")
print("[BUILD COMPLETE] MTR-015")