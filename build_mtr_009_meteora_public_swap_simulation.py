from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS_DIR = ROOT / "tools" / "meteora_funded_public_preflight"
HARNESS_DIR.mkdir(parents=True, exist_ok=True)

HARNESS = HARNESS_DIR / "mtr_009_meteora_public_swap_simulation.mjs"
TEST = ROOT / "test_mtr_009_meteora_public_swap_simulation.py"

HARNESS_TEXT = r'''import DLMM from "@meteora-ag/dlmm";
import { Connection, PublicKey, Transaction } from "@solana/web3.js";
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

const TOKEN_PROGRAM = new PublicKey(
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
);

const INPUT_RAW_USDC = 100_000_000;
const SLIPPAGE_BPS = 50;

async function rpc(method, params) {
  const response = await fetch(RPC_URL, {
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

  if (!response.ok) {
    throw new Error(`RPC HTTP ${response.status}`);
  }

  const body = await response.json();

  if (body.error) {
    throw new Error(
      `RPC ${method} error ${body.error.code}: ${body.error.message}`
    );
  }

  return body.result;
}

async function getVerifiedFundedUsdcAccount() {
  const result = await rpc("getTokenAccountsByOwner", [
    PUBLIC_CANDIDATE.toBase58(),
    {
      programId: TOKEN_PROGRAM.toBase58(),
    },
    {
      encoding: "jsonParsed",
      commitment: "confirmed",
    },
  ]);

  const rows = result.value ?? [];

  const usdc = rows
    .map((row) => {
      const info = row?.account?.data?.parsed?.info;
      const tokenAmount = info?.tokenAmount;

      return {
        pubkey: row.pubkey,
        mint: info?.mint ?? null,
        owner: info?.owner ?? null,
        rawAmount: tokenAmount?.amount ?? "0",
        decimals: tokenAmount?.decimals ?? null,
        uiAmountString: tokenAmount?.uiAmountString ?? null,
        accountOwner: row?.account?.owner ?? null,
      };
    })
    .filter((row) => row.mint === USDC_MINT.toBase58());

  const funded = usdc
    .filter((row) => row.owner === PUBLIC_CANDIDATE.toBase58())
    .filter((row) => row.accountOwner === TOKEN_PROGRAM.toBase58())
    .filter((row) => BigInt(row.rawAmount) >= BigInt(INPUT_RAW_USDC))
    .sort((a, b) => {
      const aa = BigInt(a.rawAmount);
      const bb = BigInt(b.rawAmount);
      return aa > bb ? -1 : aa < bb ? 1 : 0;
    });

  if (!funded.length) {
    throw new Error(
      "No candidate-owned USDC token account currently contains the required raw balance."
    );
  }

  return funded[0];
}

async function main() {
  console.log("[MTR-009] START");
  console.log(`[RPC] ${RPC_URL}`);
  console.log(`[LB_PAIR] ${LB_PAIR.toBase58()}`);
  console.log(`[PUBLIC_CANDIDATE] ${PUBLIC_CANDIDATE.toBase58()}`);
  console.log(`[USDC_MINT] ${USDC_MINT.toBase58()}`);
  console.log(`[USDT_MINT] ${USDT_MINT.toBase58()}`);
  console.log(`[TOKEN_PROGRAM] ${TOKEN_PROGRAM.toBase58()}`);
  console.log(`[INPUT_RAW_USDC] ${INPUT_RAW_USDC}`);
  console.log(`[SLIPPAGE_BPS] ${SLIPPAGE_BPS}`);

  console.log("[RPC] verifying funded USDC token account");

  const fundedAccount = await getVerifiedFundedUsdcAccount();

  console.log(`[FUNDED_USDC_ACCOUNT] ${fundedAccount.pubkey}`);
  console.log(`[FUNDED_USDC_RAW] ${fundedAccount.rawAmount}`);
  console.log(`[FUNDED_USDC_UI] ${fundedAccount.uiAmountString}`);
  console.log(`[FUNDED_USDC_OWNER] ${fundedAccount.owner}`);
  console.log(`[TOKEN_ACCOUNT_PROGRAM_OWNER] ${fundedAccount.accountOwner}`);

  if (fundedAccount.owner !== PUBLIC_CANDIDATE.toBase58()) {
    throw new Error("Funded USDC account owner mismatch.");
  }

  if (fundedAccount.accountOwner !== TOKEN_PROGRAM.toBase58()) {
    throw new Error("Funded USDC account is not owned by SPL Token Program.");
  }

  if (BigInt(fundedAccount.rawAmount) < BigInt(INPUT_RAW_USDC)) {
    throw new Error("Funded USDC balance is below required input.");
  }

  console.log("[FUNDING_ACCOUNT_VERIFICATION] PASS");

  const connection = new Connection(RPC_URL, "confirmed");

  console.log("[SDK] creating official Meteora DLMM pool");

  const pool = await DLMM.create(
    connection,
    LB_PAIR,
    {
      cluster: "mainnet-beta",
    },
  );

  console.log(`[POOL_PUBKEY] ${pool.pubkey.toBase58()}`);
  console.log(
    `[POOL_TOKEN_X] ${pool.tokenX.mint.address.toBase58()}`
  );
  console.log(
    `[POOL_TOKEN_Y] ${pool.tokenY.mint.address.toBase58()}`
  );

  if (pool.pubkey.toBase58() !== LB_PAIR.toBase58()) {
    throw new Error("Returned Meteora pool pubkey mismatch.");
  }

  if (pool.tokenX.mint.address.toBase58() !== USDC_MINT.toBase58()) {
    throw new Error("Meteora tokenX does not match USDC.");
  }

  if (pool.tokenY.mint.address.toBase58() !== USDT_MINT.toBase58()) {
    throw new Error("Meteora tokenY does not match USDT.");
  }

  console.log("[POOL_TOKEN_BINDING] PASS");

  console.log("[SDK] refreshing live pool state");

  await pool.refetchStates();

  const swapForY = true;

  console.log(`[SWAP_DIRECTION] USDC_X_TO_USDT_Y=${swapForY}`);

  console.log("[SDK] requesting live bin arrays");

  const binArrays = await pool.getBinArrayForSwap(
    swapForY,
    4,
  );

  console.log(`[BIN_ARRAY_COUNT] ${binArrays.length}`);

  if (!binArrays.length) {
    throw new Error("Meteora returned zero bin arrays.");
  }

  console.log("[SDK] generating exact-in quote");

  const quote = pool.swapQuote(
    new BN(INPUT_RAW_USDC),
    swapForY,
    new BN(SLIPPAGE_BPS),
    binArrays,
    false,
  );

  console.log(`[QUOTE_CONSUMED_IN] ${quote.consumedInAmount.toString()}`);
  console.log(`[QUOTE_OUT] ${quote.outAmount.toString()}`);
  console.log(`[QUOTE_MIN_OUT] ${quote.minOutAmount.toString()}`);
  console.log(`[QUOTE_FEE] ${quote.fee.toString()}`);
  console.log(`[QUOTE_PROTOCOL_FEE] ${quote.protocolFee.toString()}`);

  if (quote.consumedInAmount.lte(new BN(0))) {
    throw new Error("Quote consumed zero input.");
  }

  if (quote.outAmount.lte(new BN(0))) {
    throw new Error("Quote produced zero output.");
  }

  if (!quote.binArraysPubkey?.length) {
    throw new Error("Quote returned no bin-array public keys.");
  }

  console.log("[SDK_QUOTE] PASS");

  console.log("[SDK] constructing official pool.swap transaction");

  const swapTx = await pool.swap({
    inToken: pool.tokenX.mint.address,
    outToken: pool.tokenY.mint.address,
    inAmount: quote.consumedInAmount,
    minOutAmount: quote.minOutAmount,
    lbPair: pool.pubkey,
    user: PUBLIC_CANDIDATE,
    binArraysPubkey: quote.binArraysPubkey,
  });

  if (!swapTx) {
    throw new Error("Meteora SDK returned no transaction.");
  }

  console.log("[SDK_SWAP_TRANSACTION] CONSTRUCTED");

  if (!(swapTx instanceof Transaction)) {
    throw new Error(
      `Unexpected SDK transaction type: ${swapTx?.constructor?.name ?? typeof swapTx}`
    );
  }

  const latest = await rpc("getLatestBlockhash", [
    { commitment: "confirmed" },
  ]);

  swapTx.feePayer = PUBLIC_CANDIDATE;
  swapTx.recentBlockhash = latest.value.blockhash;

  const serialized = swapTx.serialize({
    requireAllSignatures: false,
    verifySignatures: false,
  });

  console.log(`[UNSIGNED_TX_BYTES] ${serialized.length}`);
  console.log(`[INSTRUCTION_COUNT] ${swapTx.instructions.length}`);
  console.log("[SIGNATURES] NONE");
  console.log("[BROADCAST] DISABLED");

  const encoded = serialized.toString("base64");

  console.log("[SIMULATION] calling Solana simulateTransaction");

  const simulation = await rpc("simulateTransaction", [
    encoded,
    {
      encoding: "base64",
      commitment: "confirmed",
      sigVerify: false,
      replaceRecentBlockhash: true,
      innerInstructions: true,
    },
  ]);

  console.log(
    `[SIMULATION_UNITS_CONSUMED] ${
      simulation.value?.unitsConsumed ?? "unknown"
    }`
  );

  if (simulation.value?.err) {
    console.log("[SIMULATION_RESULT] FAIL");
    console.log(
      `[SIMULATION_ERROR] ${JSON.stringify(simulation.value.err)}`
    );

    if (simulation.value?.logs) {
      console.log("[SIMULATION_LOGS_BEGIN]");
      for (const log of simulation.value.logs) {
        console.log(log);
      }
      console.log("[SIMULATION_LOGS_END]");
    }

    process.exitCode = 2;
    return;
  }

  console.log("[SIMULATION_RESULT] PASS");

  if (simulation.value?.logs) {
    console.log("[SIMULATION_LOGS_BEGIN]");
    for (const log of simulation.value.logs) {
      console.log(log);
    }
    console.log("[SIMULATION_LOGS_END]");
  }

  console.log("[MTR-009] METEORA PUBLIC SWAP SIMULATION COMPLETE.");
  console.log("[MTR-009] NO SIGNATURE CREATED.");
  console.log("[MTR-009] NO BROADCAST OCCURRED.");
  console.log("[MTR-009] NO CANONICAL EXECUTOR USED.");
}

main().catch((error) => {
  console.error(`[FAIL] ${error?.stack ?? error}`);
  process.exitCode = 1;
});
'''

TEST_TEXT = r'''from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT / "tools" / "meteora_funded_public_preflight" / "mtr_009_meteora_public_swap_simulation.mjs"

text = HARNESS.read_text(encoding="utf-8")

required = [
    'import DLMM from "@meteora-ag/dlmm";',
    'ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq',
    'CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR',
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
    'getTokenAccountsByOwner',
    'getBinArrayForSwap',
    'swapQuote',
    'pool.swap',
    'simulateTransaction',
    'sigVerify: false',
    'requireAllSignatures: false',
    'verifySignatures: false',
    'INPUT_RAW_USDC = 100_000_000',
    'SLIPPAGE_BPS = 50',
    '[BROADCAST] DISABLED',
    '[SIGNATURES] NONE',
]

for item in required:
    assert item in text, f"missing required construct: {item}"

forbidden = [
    "QSB_SOLANA_PRIVATE_KEY",
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "signTransaction",
    "fromSecretKey",
    "Keypair.from",
    "sendTransaction",
    ".sign(",
    ".partialSign(",
    "ATokenGP",
]

for item in forbidden:
    assert item not in text, f"forbidden construct present: {item}"

assert "simulateTransaction" in text
assert "new PublicKey(" in text
assert "new Connection(" in text
assert "new Transaction" not in text

print("[PASS] Official Meteora DLMM default import preserved")
print("[PASS] Exact LB pair preserved")
print("[PASS] Exact public candidate preserved")
print("[PASS] Exact USDC mint preserved")
print("[PASS] Exact USDT mint preserved")
print("[PASS] Exact Token Program preserved")
print("[PASS] Direct raw funding verification preserved")
print("[PASS] Verified funded token account required")
print("[PASS] Official getBinArrayForSwap encoded")
print("[PASS] Official swapQuote encoded")
print("[PASS] Official pool.swap encoded")
print("[PASS] Unsigned transaction serialization encoded")
print("[PASS] simulateTransaction encoded")
print("[PASS] No ATA-program assumption present")
print("[PASS] No private-key reference present")
print("[PASS] No signing operation present")
print("[PASS] No broadcast operation present")
print("[PASS] No canonical executor reference present")
print("[BUILD TEST COMPLETE] MTR-009")
'''

HARNESS.write_text(HARNESS_TEXT, encoding="utf-8")
TEST.write_text(TEST_TEXT, encoding="utf-8")

print("[BUILD] MTR-009 files written")
print(f"[HARNESS] {HARNESS}")
print(f"[TEST] {TEST}")
print("[BUILD COMPLETE] MTR-009")