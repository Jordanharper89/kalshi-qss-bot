from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "tools" / "meteora_funded_public_preflight"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HARNESS = OUT_DIR / "mtr_010_meteora_funded_input_binding_simulation.mjs"
TEST = ROOT / "test_mtr_010_meteora_funded_input_binding_simulation.py"

HARNESS.write_text(r'''import DLMM from "@meteora-ag/dlmm";
import {
  Connection,
  PublicKey,
  Transaction,
} from "@solana/web3.js";
import {
  ASSOCIATED_TOKEN_PROGRAM_ID,
  TOKEN_PROGRAM_ID,
  getAssociatedTokenAddressSync,
} from "@solana/spl-token";
import BN from "bn.js";

const RPC_URL = "https://api.mainnet-beta.solana.com";

const LB_PAIR = new PublicKey(
  "ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq"
);

const PUBLIC_CANDIDATE = new PublicKey(
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR"
);

const USDC_MINT = new PublicKey(
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
);

const USDT_MINT = new PublicKey(
  "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
);

const TOKEN_PROGRAM = TOKEN_PROGRAM_ID;

const FUNDED_USDC_ACCOUNT = new PublicKey(
  "6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5"
);

const INPUT_RAW_USDC = 100_000_000;
const SLIPPAGE_BPS = 50;

async function rpc(method, params) {
  const response = await fetch(RPC_URL, {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method,
      params,
    }),
  });

  if (!response.ok) {
    throw new Error(`RPC HTTP ${response.status}`);
  }

  const payload = await response.json();

  if (payload.error) {
    throw new Error(JSON.stringify(payload.error));
  }

  return payload.result;
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function main() {
  console.log("[MTR-010] START");
  console.log(`[RPC] ${RPC_URL}`);
  console.log(`[LB_PAIR] ${LB_PAIR.toBase58()}`);
  console.log(`[PUBLIC_CANDIDATE] ${PUBLIC_CANDIDATE.toBase58()}`);
  console.log(`[USDC_MINT] ${USDC_MINT.toBase58()}`);
  console.log(`[USDT_MINT] ${USDT_MINT.toBase58()}`);
  console.log(`[TOKEN_PROGRAM] ${TOKEN_PROGRAM.toBase58()}`);
  console.log(`[FUNDED_USDC_ACCOUNT] ${FUNDED_USDC_ACCOUNT.toBase58()}`);
  console.log(`[INPUT_RAW_USDC] ${INPUT_RAW_USDC}`);
  console.log(`[SLIPPAGE_BPS] ${SLIPPAGE_BPS}`);

  console.log("[RPC] verifying exact funded input account");

  const fundedInfo = await rpc("getAccountInfo", [
    FUNDED_USDC_ACCOUNT.toBase58(),
    {encoding: "jsonParsed", commitment: "confirmed"},
  ]);

  assert(fundedInfo && fundedInfo.value, "Funded token account does not exist");

  const parsed = fundedInfo.value.data?.parsed;
  const info = parsed?.info;

  assert(parsed?.type === "account", "Funded account is not an SPL token account");
  assert(info?.mint === USDC_MINT.toBase58(), "Funded account mint mismatch");
  assert(
    info?.owner === PUBLIC_CANDIDATE.toBase58(),
    "Funded account owner mismatch"
  );
  assert(
    fundedInfo.value.owner === TOKEN_PROGRAM.toBase58(),
    "Funded account program owner mismatch"
  );

  const fundedRaw = BigInt(info.tokenAmount.amount);

  console.log(`[FUNDED_USDC_RAW] ${fundedRaw.toString()}`);
  console.log(`[FUNDED_USDC_UI] ${info.tokenAmount.uiAmountString}`);
  console.log(`[FUNDED_USDC_OWNER] ${info.owner}`);
  console.log(`[FUNDED_ACCOUNT_PROGRAM_OWNER] ${fundedInfo.value.owner}`);

  assert(
    fundedRaw >= BigInt(INPUT_RAW_USDC),
    "Funded account does not contain required input"
  );

  console.log("[FUNDING_ACCOUNT_VERIFICATION] PASS");

  const canonicalInputAta = getAssociatedTokenAddressSync(
    USDC_MINT,
    PUBLIC_CANDIDATE,
    false,
    TOKEN_PROGRAM,
    ASSOCIATED_TOKEN_PROGRAM_ID,
  );

  console.log(`[CANONICAL_USDC_ATA] ${canonicalInputAta.toBase58()}`);
  console.log(
    `[FUNDED_ACCOUNT_EQUALS_CANONICAL_ATA] ${
      canonicalInputAta.equals(FUNDED_USDC_ACCOUNT) ? "YES" : "NO"
    }`
  );

  assert(
    !canonicalInputAta.equals(FUNDED_USDC_ACCOUNT),
    "Diagnostic requires funded account to be distinct from candidate ATA"
  );

  const ataInfo = await rpc("getAccountInfo", [
    canonicalInputAta.toBase58(),
    {encoding: "jsonParsed", commitment: "confirmed"},
  ]);

  let ataRaw = 0n;

  if (ataInfo?.value?.data?.parsed?.info?.tokenAmount?.amount !== undefined) {
    ataRaw = BigInt(
      ataInfo.value.data.parsed.info.tokenAmount.amount
    );
  }

  console.log(`[CANONICAL_USDC_ATA_RAW] ${ataRaw.toString()}`);

  console.log("[SDK] creating official Meteora DLMM pool");

  const connection = new Connection(RPC_URL, "confirmed");

  const pool = await DLMM.create(connection, LB_PAIR, {
    cluster: "mainnet-beta",
  });

  console.log(`[POOL_PUBKEY] ${pool.pubkey.toBase58()}`);
  console.log(`[POOL_TOKEN_X] ${pool.tokenX.mint.address.toBase58()}`);
  console.log(`[POOL_TOKEN_Y] ${pool.tokenY.mint.address.toBase58()}`);

  assert(
    pool.pubkey.equals(LB_PAIR),
    "Pool pubkey mismatch"
  );

  assert(
    pool.tokenX.mint.address.equals(USDC_MINT),
    "Pool token X is not USDC"
  );

  assert(
    pool.tokenY.mint.address.equals(USDT_MINT),
    "Pool token Y is not USDT"
  );

  console.log("[POOL_TOKEN_BINDING] PASS");

  await pool.refetchStates();

  console.log("[SDK] requesting live bin arrays");

  const swapYtoX = false;

  const binArrays = await pool.getBinArrayForSwap(
    swapYtoX,
    4
  );

  console.log(`[BIN_ARRAY_COUNT] ${binArrays.length}`);

  const quote = pool.swapQuote(
    new BN(INPUT_RAW_USDC),
    swapYtoX,
    new BN(SLIPPAGE_BPS),
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

  assert(
    quote.consumedInAmount.eq(new BN(INPUT_RAW_USDC)),
    "Quote consumed input mismatch"
  );

  console.log("[SDK_QUOTE] PASS");

  console.log("[SDK] constructing official pool.swap transaction");

  let swapTx;

  try {
    swapTx = await pool.swap({
      inToken: pool.tokenX.mint.address,
      outToken: pool.tokenY.mint.address,
      inAmount: quote.consumedInAmount,
      minOutAmount: quote.minOutAmount,
      lbPair: pool.pubkey,
      user: PUBLIC_CANDIDATE,
      binArraysPubkey: quote.binArraysPubkey,
    });
  } catch (error) {
    console.log("[SDK_SWAP_BUILD_WARNING]");
    console.log(String(error));
    throw error;
  }

  assert(
    swapTx instanceof Transaction,
    "Official SDK did not return a Transaction"
  );

  console.log("[SDK_SWAP_TRANSACTION] CONSTRUCTED");

  const swapInstruction = swapTx.instructions.find(
    (ix) =>
      ix.programId.equals(
        new PublicKey("LBUZKhRxPF3XUpBCj4YzTKgLccjZhTSDM9YuVaPwxo")
      ) &&
      ix.data.length >= 8 &&
      ix.data.subarray(0, 8).equals(
        Buffer.from("414b3f4ceb5b5b88", "hex")
      )
  );

  assert(
    swapInstruction,
    "Official SDK Swap2 instruction not found"
  );

  console.log(
    `[SWAP2_ACCOUNT_COUNT] ${swapInstruction.keys.length}`
  );

  const canonicalIndex = swapInstruction.keys.findIndex(
    (meta) => meta.pubkey.equals(canonicalInputAta)
  );

  const fundedIndex = swapInstruction.keys.findIndex(
    (meta) => meta.pubkey.equals(FUNDED_USDC_ACCOUNT)
  );

  console.log(`[CANONICAL_INPUT_ATA_INDEX] ${canonicalIndex}`);
  console.log(`[FUNDED_INPUT_ACCOUNT_INDEX] ${fundedIndex}`);

  assert(
    canonicalIndex >= 0,
    "Canonical candidate USDC ATA not present in official Swap2"
  );

  assert(
    fundedIndex < 0,
    "Funded account unexpectedly already present in official Swap2"
  );

  const originalMeta = swapInstruction.keys[canonicalIndex];

  console.log(
    `[ORIGINAL_INPUT_ACCOUNT] ${originalMeta.pubkey.toBase58()}`
  );

  swapInstruction.keys[canonicalIndex] = {
    pubkey: FUNDED_USDC_ACCOUNT,
    isSigner: originalMeta.isSigner,
    isWritable: originalMeta.isWritable,
  };

  console.log(
    `[BOUND_INPUT_ACCOUNT] ${swapInstruction.keys[canonicalIndex].pubkey.toBase58()}`
  );

  assert(
    swapInstruction.keys[canonicalIndex].pubkey.equals(
      FUNDED_USDC_ACCOUNT
    ),
    "Funded input account binding failed"
  );

  console.log("[FUNDED_INPUT_BINDING] PASS");

  swapTx.feePayer = PUBLIC_CANDIDATE;

  const latest = await connection.getLatestBlockhash("confirmed");
  swapTx.recentBlockhash = latest.blockhash;

  const serialized = swapTx.serialize({
    requireAllSignatures: false,
    verifySignatures: false,
  });

  console.log(`[UNSIGNED_TX_BYTES] ${serialized.length}`);
  console.log(`[INSTRUCTION_COUNT] ${swapTx.instructions.length}`);
  console.log("[SIGNATURES] NONE");
  console.log("[BROADCAST] DISABLED");

  console.log("[SIMULATION] calling Solana simulateTransaction");

  const simulation = await connection.simulateTransaction(
    swapTx,
    {
      commitment: "confirmed",
      sigVerify: false,
      replaceRecentBlockhash: true,
      innerInstructions: true,
    }
  );

  console.log(
    `[SIMULATION_UNITS_CONSUMED] ${
      simulation.value.unitsConsumed ?? "unknown"
    }`
  );

  if (simulation.value.err) {
    console.log("[SIMULATION_RESULT] FAIL");
    console.log(
      `[SIMULATION_ERROR] ${JSON.stringify(simulation.value.err)}`
    );
    console.log("[SIMULATION_LOGS_BEGIN]");

    for (const line of simulation.value.logs ?? []) {
      console.log(line);
    }

    console.log("[SIMULATION_LOGS_END]");
    process.exitCode = 2;
    return;
  }

  console.log("[SIMULATION_RESULT] PASS");

  console.log("[SIMULATION_LOGS_BEGIN]");

  for (const line of simulation.value.logs ?? []) {
    console.log(line);
  }

  console.log("[SIMULATION_LOGS_END]");
  console.log("[MTR-010] FUNDED INPUT ACCOUNT BINDING SIMULATION COMPLETE.");
  console.log("[MTR-010] NO SIGNING.");
  console.log("[MTR-010] NO SENDING.");
  console.log("[MTR-010] NO CANONICAL EXECUTOR.");
}

main().catch((error) => {
  console.error("[MTR-010] FATAL");
  console.error(error?.stack ?? String(error));
  process.exitCode = 1;
});
''', encoding="utf-8")

TEST.write_text(r'''from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT / "tools" / "meteora_funded_public_preflight" / "mtr_010_meteora_funded_input_binding_simulation.mjs"

text = HARNESS.read_text(encoding="utf-8")

checks = [
    ('from "@meteora-ag/dlmm"', "Official Meteora DLMM import missing"),
    ('ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq', "LB pair missing"),
    ('CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR', "Public candidate missing"),
    ('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', "USDC mint missing"),
    ('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB', "USDT mint missing"),
    ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', "Token program missing"),
    ('6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5', "Funded USDC account missing"),
    ('getAccountInfo', "Direct account verification missing"),
    ('getAssociatedTokenAddressSync', "Canonical ATA derivation missing"),
    ('getBinArrayForSwap', "Official bin-array path missing"),
    ('swapQuote', "Official swap quote missing"),
    ('pool.swap', "Official pool.swap missing"),
    ('414b3f4ceb5b5b88', "Swap2 discriminator guard missing"),
    ('swapInstruction.keys', "Swap2 account-meta inspection missing"),
    ('FUNDED_INPUT_BINDING', "Funded input binding missing"),
    ('simulateTransaction', "Simulation missing"),
    ('sigVerify: false', "sigVerify=false missing"),
    ('requireAllSignatures: false', "Unsigned serialization missing"),
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
    print(f"[PASS] No {forbidden} present")

print("[BUILD TEST COMPLETE] MTR-010")
''', encoding="utf-8")

print("[BUILD] MTR-010 files written")
print(f"[HARNESS] {HARNESS}")
print(f"[TEST] {TEST}")
print("[BUILD COMPLETE] MTR-010")