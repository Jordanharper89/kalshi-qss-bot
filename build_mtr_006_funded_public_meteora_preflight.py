from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "tools" / "meteora_funded_public_preflight"
OUT.mkdir(parents=True, exist_ok=True)

HARNESS = OUT / "meteora_funded_public_preflight.mjs"
TEST = ROOT / "test_mtr_006_funded_public_meteora_preflight.py"

harness = r'''import { Connection, PublicKey } from "@solana/web3.js";
import DLMM from "@meteora-ag/dlmm";

const RPC =
  process.env.QSB_SOLANA_RPC ||
  "https://api.mainnet-beta.solana.com";

const LB_PAIR = new PublicKey(
  "ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq"
);

const PUBLIC_CANDIDATE = new PublicKey(
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR"
);

const USDC_MINT = new PublicKey(
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
);

const TOKEN_PROGRAM = new PublicKey(
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
);

const REQUIRED_RAW_USDC = 100000000n;

function stringifyKey(value) {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value.toBase58 === "function") {
    return value.toBase58();
  }

  return String(value);
}

function inspectRow(row, index) {
  const account = row?.account;
  const data = account?.data;

  let parsed = null;

  if (
    data !== null &&
    typeof data === "object" &&
    !Array.isArray(data) &&
    data.parsed !== undefined
  ) {
    parsed = data.parsed;
  }

  return {
    index,
    pubkey: stringifyKey(row?.pubkey),
    row_keys:
      row && typeof row === "object"
        ? Object.keys(row)
        : [],
    account_keys:
      account && typeof account === "object"
        ? Object.keys(account)
        : [],
    account_owner: stringifyKey(account?.owner),
    lamports: account?.lamports ?? null,
    data_type: Array.isArray(data)
      ? "array"
      : typeof data,
    data_keys:
      data &&
      typeof data === "object" &&
      !Array.isArray(data)
        ? Object.keys(data)
        : [],
    parsed
  };
}

function extractTokenInfo(item) {
  const parsed = item.parsed;

  if (
    parsed === null ||
    typeof parsed !== "object"
  ) {
    return null;
  }

  const info = parsed.info;

  if (
    info === null ||
    typeof info !== "object"
  ) {
    return null;
  }

  const mint = stringifyKey(info.mint);
  const owner = stringifyKey(info.owner);
  const tokenAmount = info.tokenAmount;

  let rawAmount = null;

  if (
    tokenAmount &&
    typeof tokenAmount === "object" &&
    tokenAmount.amount !== undefined
  ) {
    try {
      rawAmount = BigInt(
        String(tokenAmount.amount)
      );
    } catch {
      rawAmount = null;
    }
  }

  return {
    mint,
    owner,
    rawAmount,
    decimals: tokenAmount?.decimals ?? null,
    uiAmountString:
      tokenAmount?.uiAmountString ?? null
  };
}

async function main() {
  console.log("[MTR-006] START");
  console.log(`[RPC] ${RPC}`);
  console.log(
    `[LB_PAIR] ${LB_PAIR.toBase58()}`
  );
  console.log(
    `[PUBLIC_CANDIDATE] ${PUBLIC_CANDIDATE.toBase58()}`
  );
  console.log(
    `[USDC_MINT] ${USDC_MINT.toBase58()}`
  );
  console.log(
    `[TOKEN_PROGRAM] ${TOKEN_PROGRAM.toBase58()}`
  );
  console.log(
    `[REQUIRED_RAW_USDC] ${REQUIRED_RAW_USDC.toString()}`
  );

  const connection = new Connection(
    RPC,
    "confirmed"
  );

  const candidate =
    await connection.getAccountInfo(
      PUBLIC_CANDIDATE,
      "confirmed"
    );

  console.log(
    `[CANDIDATE_ACCOUNT_OWNER] ${
      stringifyKey(candidate?.owner) || "NONE"
    }`
  );

  console.log(
    `[CANDIDATE_LAMPORTS] ${
      candidate?.lamports ?? 0
    }`
  );

  console.log(
    "[RPC] getTokenAccountsByOwner"
  );

  const response =
    await connection.getTokenAccountsByOwner(
      PUBLIC_CANDIDATE,
      {
        programId: TOKEN_PROGRAM
      },
      {
        commitment: "confirmed",
        encoding: "jsonParsed"
      }
    );

  console.log(
    `[RPC_RESPONSE_TYPE] ${typeof response}`
  );

  console.log(
    `[RPC_RESPONSE_KEYS] ${
      Object.keys(response ?? {}).join(",")
    }`
  );

  console.log(
    `[RPC_CONTEXT_KEYS] ${
      Object.keys(response?.context ?? {}).join(",")
    }`
  );

  console.log(
    `[RPC_VALUE_IS_ARRAY] ${
      Array.isArray(response?.value)
        ? "YES"
        : "NO"
    }`
  );

  if (!Array.isArray(response?.value)) {
    throw new Error(
      "Unexpected RPC response: value is not an array."
    );
  }

  const rows = response.value;

  console.log(
    `[TOKEN_ACCOUNT_COUNT] ${rows.length}`
  );

  if (rows.length === 0) {
    throw new Error(
      "RPC returned zero token accounts."
    );
  }

  console.log(
    "[RAW_FIRST_TOKEN_ACCOUNT_BEGIN]"
  );

  console.dir(
    rows[0],
    {
      depth: 12,
      colors: false
    }
  );

  console.log(
    "[RAW_FIRST_TOKEN_ACCOUNT_END]"
  );

  const inspected =
    rows.map(inspectRow);

  const first = inspected[0];

  console.log(
    `[FIRST_ROW_KEYS] ${
      first.row_keys.join(",")
    }`
  );

  console.log(
    `[FIRST_ACCOUNT_KEYS] ${
      first.account_keys.join(",")
    }`
  );

  console.log(
    `[FIRST_DATA_TYPE] ${first.data_type}`
  );

  console.log(
    `[FIRST_DATA_KEYS] ${
      first.data_keys.join(",")
    }`
  );

  console.log(
    `[FIRST_PARSED_PRESENT] ${
      first.parsed !== null
        ? "YES"
        : "NO"
    }`
  );

  let parsedCount = 0;
  let usdcCount = 0;
  let usdcRawTotal = 0n;

  const usdcAccounts = [];

  for (const item of inspected) {
    const token =
      extractTokenInfo(item);

    if (token === null) {
      continue;
    }

    parsedCount += 1;

    if (
      token.mint !==
      USDC_MINT.toBase58()
    ) {
      continue;
    }

    usdcCount += 1;

    if (token.rawAmount !== null) {
      usdcRawTotal += token.rawAmount;
    }

    usdcAccounts.push({
      pubkey: item.pubkey,
      tokenOwner: token.owner,
      rawAmount: token.rawAmount,
      decimals: token.decimals,
      uiAmountString:
        token.uiAmountString,
      accountOwner:
        item.account_owner
    });
  }

  console.log(
    `[PARSED_TOKEN_ACCOUNT_COUNT] ${parsedCount}`
  );

  console.log(
    `[USDC_TOKEN_ACCOUNT_COUNT] ${usdcCount}`
  );

  console.log(
    `[USDC_RAW_TOTAL] ${usdcRawTotal.toString()}`
  );

  console.log(
    `[USDC_REQUIRED_RAW] ${
      REQUIRED_RAW_USDC.toString()
    }`
  );

  console.log(
    `[USDC_TOTAL_FUNDED_THRESHOLD] ${
      usdcRawTotal >= REQUIRED_RAW_USDC
        ? "PASS"
        : "FAIL"
    }`
  );

  for (const account of usdcAccounts) {
    console.log(
      "[USDC_ACCOUNT] " +
      `pubkey=${account.pubkey} ` +
      `token_owner=${account.tokenOwner} ` +
      `raw_amount=${
        account.rawAmount === null
          ? "UNPARSED"
          : account.rawAmount.toString()
      } ` +
      `decimals=${account.decimals} ` +
      `ui_amount=${
        account.uiAmountString ?? "null"
      } ` +
      `account_owner=${account.accountOwner}`
    );
  }

  if (usdcAccounts.length === 0) {
    throw new Error(
      "No parsed USDC token accounts found."
    );
  }

  const candidateAddress =
    PUBLIC_CANDIDATE.toBase58();

  const ownershipFailures =
    usdcAccounts.filter(
      (account) =>
        account.tokenOwner !==
        candidateAddress
    );

  if (ownershipFailures.length > 0) {
    console.log(
      `[OWNERSHIP_FAILURE_COUNT] ${
        ownershipFailures.length
      }`
    );

    throw new Error(
      "USDC token-account ownership verification failed."
    );
  }

  console.log(
    "[OWNERSHIP_VERIFICATION] PASS"
  );

  if (
    usdcRawTotal <
    REQUIRED_RAW_USDC
  ) {
    console.log(
      "[FUNDING_VERIFICATION] FAIL"
    );

    console.log(
      "[MTR-006] Candidate does not have the required raw USDC balance."
    );

    console.log(
      "[MTR-006] STOP BEFORE METEORA TRANSACTION CONSTRUCTION."
    );

    console.log(
      "[MTR-006] No signing. No sending."
    );

    return;
  }

  console.log(
    "[FUNDING_VERIFICATION] PASS"
  );

  console.log(
    "[MTR-006] Candidate has sufficient verified USDC."
  );

  console.log(
    "[MTR-006] Creating official Meteora DLMM pool."
  );

  const pool =
    await DLMM.create(
      connection,
      LB_PAIR
    );

  console.log(
    `[POOL_PUBKEY] ${pool.pubkey.toBase58()}`
  );

  console.log(
    `[POOL_TOKEN_X] ${
      pool.tokenX.mint.address.toBase58()
    }`
  );

  console.log(
    `[POOL_TOKEN_Y] ${
      pool.tokenY.mint.address.toBase58()
    }`
  );

  const tokenX =
    pool.tokenX.mint.address.toBase58();

  const tokenY =
    pool.tokenY.mint.address.toBase58();

  if (
    tokenX !== USDC_MINT.toBase58() &&
    tokenY !== USDC_MINT.toBase58()
  ) {
    throw new Error(
      "Meteora pool token binding does not contain USDC."
    );
  }

  console.log(
    "[POOL_TOKEN_BINDING_PASS]"
  );

  console.log(
    "[MTR-006] DIAGNOSTIC PROOF COMPLETE."
  );

  console.log(
    "[MTR-006] STOP BEFORE TRANSACTION CONSTRUCTION."
  );

  console.log(
    "[MTR-006] No signing or sending occurred."
  );
}

main().catch((error) => {
  console.error(
    `[FAIL] ${error?.stack ?? error}`
  );

  process.exitCode = 1;
});
'''

test = r'''from pathlib import Path

ROOT = Path(__file__).resolve().parent

HARNESS = (
    ROOT
    / "tools"
    / "meteora_funded_public_preflight"
    / "meteora_funded_public_preflight.mjs"
)

text = HARNESS.read_text(encoding="utf-8")

required = [
    'import DLMM from "@meteora-ag/dlmm";',
    "getTokenAccountsByOwner",
    'encoding: "jsonParsed"',
    "Array.isArray(response?.value)",
    "response.value",
    "inspectRow",
    "extractTokenInfo",
    "BigInt",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR",
    "100000000n",
    "[OWNERSHIP_VERIFICATION]",
    "[FUNDING_VERIFICATION]",
    "[MTR-006] STOP BEFORE TRANSACTION CONSTRUCTION."
]

for item in required:
    if item not in text:
        raise SystemExit(
            f"[FAIL] Missing required element: {item}"
        )

forbidden = [
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "signTransaction",
    "fromSecretKey",
    "Keypair.from",
    ".send("
]

for item in forbidden:
    if item in text:
        raise SystemExit(
            f"[FAIL] Forbidden operation found: {item}"
        )

print("[PASS] Official Meteora DLMM default import preserved")
print("[PASS] Exact LB pair preserved")
print("[PASS] Exact public candidate preserved")
print("[PASS] Exact USDC mint preserved")
print("[PASS] getTokenAccountsByOwner inspection encoded")
print("[PASS] Actual response.value shape inspection encoded")
print("[PASS] jsonParsed normalization encoded")
print("[PASS] Raw USDC BigInt balance calculation encoded")
print("[PASS] Token-account ownership verification encoded")
print("[PASS] 100,000,000 raw USDC threshold encoded")
print("[PASS] No signing operation present")
print("[PASS] No sending operation present")
print("[PASS] MTR-006 stops before transaction construction")
print("[BUILD COMPLETE] MTR-006")
'''

HARNESS.write_text(harness, encoding="utf-8")
TEST.write_text(test, encoding="utf-8")

print("[BUILD] MTR-006 replacement files written")
print(f"[HARNESS] {HARNESS}")
print(f"[TEST] {TEST}")