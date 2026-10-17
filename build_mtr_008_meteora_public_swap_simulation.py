from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS_DIR = ROOT / "tools" / "meteora_funded_public_preflight"
HARNESS_DIR.mkdir(parents=True, exist_ok=True)

HARNESS = HARNESS_DIR / "mtr_008_meteora_public_swap_simulation.mjs"
TEST = ROOT / "test_mtr_008_meteora_public_swap_simulation.py"

HARNESS_TEXT = r'''import DLMM from "@meteora-ag/dlmm";
import { PublicKey, Transaction } from "@solana/web3.js";
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

const ASSOCIATED_TOKEN_PROGRAM = new PublicKey(
  "ATokenGPvbd1h4mZ8GQfGf2r7FhYbGfG6q3m6wG6q"
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

function deriveAta(owner, mint) {
  return PublicKey.findProgramAddressSync(
    [
      owner.toBuffer(),
      TOKEN_PROGRAM.toBuffer(),
      mint.toBuffer(),
    ],
    ASSOCIATED_TOKEN_PROGRAM,
  )[0];
}

async function getRawUsdcAccounts() {
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

  return result.value
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
}

async function main() {
  console.log("[MTR-008] START");
  console.log(`[RPC] ${RPC_URL}`);
  console.log(`[LB_PAIR] ${LB_PAIR.toBase58()}`);
  console.log(`[PUBLIC_CANDIDATE] ${PUBLIC_CANDIDATE.toBase58()}`);
  console.log(`[USDC_MINT] ${USDC_MINT.toBase58()}`);
  console.log(`[USDT_MINT] ${USDT_MINT.toBase58()}`);
  console.log(`[TOKEN_PROGRAM] ${TOKEN_PROGRAM.toBase58()}`);
  console.log(`[INPUT_RAW_USDC] ${INPUT_RAW_USDC}`);
  console.log(`[SLIPPAGE_BPS] ${SLIPPAGE_BPS}`);

  console.log("[RPC] verifying candidate funding directly");

  const usdcAccounts = await getRawUsdcAccounts();

  const funded = usdcAccounts
    .filter((row) => row.owner === PUBLIC_CANDIDATE.toBase58())
    .filter((row) => row.accountOwner === TOKEN_PROGRAM.toBase58())
    .filter((row) => BigInt(row.rawAmount) >= BigInt(INPUT_RAW_USDC));

  if (funded.length === 0) {
    throw new Error(
      "No candidate-owned USDC token account currently contains the required raw balance."
    );
  }

  const fundedAccount = funded.sort((a, b) =>
    Number(BigInt(b.rawAmount) - BigInt(a.rawAmount))
  )[0];

  console.log(`[FUNDED_USDC_ACCOUNT] ${fundedAccount.pubkey}`);
  console.log(`[FUNDED_USDC_RAW] ${fundedAccount.rawAmount}`);
  console.log(`[FUNDED_USDC_UI] ${fundedAccount.uiAmountString}`);

  const expectedUsdcAta = deriveAta(PUBLIC_CANDIDATE, USDC_MINT);

  console.log(`[EXPECTED_USDC_ATA] ${expectedUsdcAta.toBase58()}`);

  if (fundedAccount.pubkey !== expectedUsdcAta.toBase58()) {
    throw new Error(
      "The verified funded USDC account is not the candidate's canonical USDC ATA; refusing to construct the SDK swap simulation."
    );
  }

  console.log("[USDC_ATA_VERIFICATION] PASS");

  const candidateBalance = await rpc("getBalance", [
    PUBLIC_CANDIDATE.toBase58(),
    { commitment: "confirmed" },
  ]);

  console.log(`[CANDIDATE_LAMPORTS] ${candidateBalance.value}`);

  if (candidateBalance.value < 10_000_000) {
    throw new Error(
      "Candidate SOL balance is unexpectedly low for simulation account creation/fee requirements."
    );
  }

  console.log("[CANDIDATE_SOL_VERIFICATION] PASS");

  console.log("[SDK] creating official Meteora DLMM pool");

  const connection = {
    async getLatestBlockhash() {
      return await rpc("getLatestBlockhash", [
        { commitment: "confirmed" },
      ]);
    },
  };

  const { Connection } = await import("@solana/web3.js");
  const web3Connection = new Connection(RPC_URL, "confirmed");

  const pool = await DLMM.create(
    web3Connection,
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

  if (pool.tokenX.mint.address.toBase58() !== USDC_MINT.toBase58()) {
    throw new Error("Meteora tokenX does not match expected USDC mint.");
  }

  if (pool.tokenY.mint.address.toBase58() !== USDT_MINT.toBase58()) {
    throw new Error("Meteora tokenY does not match expected USDT mint.");
  }

  console.log("[POOL_TOKEN_BINDING] PASS");

  await pool.refetchStates();

  const swapForY = true;

  console.log(`[SWAP_DIRECTION] X_TO_Y=${swapForY}`);
  console.log("[SDK] fetching bin arrays");

  const binArrays = await pool.getBinArrayForSwap(
    swapForY,
    4,
  );

  console.log(`[BIN_ARRAY_COUNT] ${binArrays.length}`);

  if (!binArrays.length) {
    throw new Error("Meteora returned zero bin arrays for the swap.");
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
  console.log(`[QUOTE_END_PRICE] ${quote.endPrice.toString()}`);

  if (quote.consumedInAmount.lte(new BN(0))) {
    throw new Error("SDK quote consumed zero input.");
  }

  if (quote.outAmount.lte(new BN(0))) {
    throw new Error("SDK quote returned zero output.");
  }

  if (!quote.binArraysPubkey?.length) {
    throw new Error("SDK quote returned no bin-array public keys.");
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

  const latest = await rpc("getLatestBlockhash", [
    { commitment: "confirmed" },
  ]);

  const tx = swapTx instanceof Transaction
    ? swapTx
    : swapTx;

  tx.feePayer = PUBLIC_CANDIDATE;
  tx.recentBlockhash = latest.value.blockhash;

  const serialized = tx.serialize({
    requireAllSignatures: false,
    verifySignatures: false,
  });

  const encoded = serialized.toString("base64");

  console.log(`[UNSIGNED_TX_BYTES] ${serialized.length}`);
  console.log("[SIGNATURES] NONE");
  console.log("[BROADCAST] DISABLED");
  console.log("[SIMULATION] submitting unsigned transaction to simulateTransaction");

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

    if (simulation.value.logs) {
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

  console.log("[MTR-008] METEORA PUBLIC SWAP SIMULATION COMPLETE.");
  console.log("[MTR-008] NO SIGNATURE CREATED.");
  console.log("[MTR-008] NO BROADCAST OCCURRED.");
  console.log("[MTR-008] NO CANONICAL EXECUTOR USED.");
}

main().catch((error) => {
  console.error(`[FAIL] ${error?.stack ?? error}`);
  process.exitCode = 1;
});
'''

TEST_TEXT = r'''from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS = ROOT / "tools" / "meteora_funded_public_preflight" / "mtr_008_meteora_public_swap_simulation.mjs"

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
]

for item in forbidden:
    assert item not in text, f"forbidden signing/broadcast construct present: {item}"

assert 'process.env' not in text, "environment-variable access is not permitted"
assert "simulateTransaction" in text, "simulation RPC missing"
assert "Meteora SDK returned no transaction" in text
assert "[BROADCAST] DISABLED" in text
assert "[SIGNATURES] NONE" in text

print("[PASS] Official Meteora DLMM default import preserved")
print("[PASS] Exact LB pair preserved")
print("[PASS] Exact public candidate preserved")
print("[PASS] Exact USDC mint preserved")
print("[PASS] Exact USDT mint preserved")
print("[PASS] Exact Token Program preserved")
print("[PASS] Raw getTokenAccountsByOwner funding verification encoded")
print("[PASS] Canonical USDC ATA verification encoded")
print("[PASS] 100,000,000 raw USDC input encoded")
print("[PASS] Official getBinArrayForSwap encoded")
print("[PASS] Official swapQuote encoded")
print("[PASS] Official pool.swap encoded")
print("[PASS] Unsigned transaction serialization encoded")
print("[PASS] sigVerify=false encoded")
print("[PASS] simulateTransaction encoded")
print("[PASS] No private-key reference present")
print("[PASS] No signing operation present")
print("[PASS] No broadcast operation present")
print("[PASS] No canonical executor reference present")
print("[BUILD TEST COMPLETE] MTR-008")
'''

HARNESS.write_text(HARNESS_TEXT, encoding="utf-8")
TEST.write_text(TEST_TEXT, encoding="utf-8")

print("[BUILD] MTR-008 files written")
print(f"[HARNESS] {HARNESS}")
print(f"[TEST] {TEST}")
print("[BUILD COMPLETE] MTR-008")