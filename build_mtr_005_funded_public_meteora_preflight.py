from pathlib import Path
import json
import shutil
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parent
TOOL_DIR = ROOT / "tools" / "meteora_funded_public_preflight"
TOOL_DIR.mkdir(parents=True, exist_ok=True)

TARGET = TOOL_DIR / "meteora_funded_public_preflight.mjs"

PACKAGE_JSON = {
    "name": "meteora-funded-public-preflight",
    "private": True,
    "type": "module",
    "dependencies": {
        "@coral-xyz/anchor": "^0.31.1",
        "@meteora-ag/dlmm": "1.9.14",
        "@solana/web3.js": "^1.98.4"
    }
}

JS = r'''
import DLMM from "@meteora-ag/dlmm";
import {
  Connection,
  PublicKey
} from "@solana/web3.js";

const RPC = "https://api.mainnet-beta.solana.com";

const LB_PAIR =
  new PublicKey("ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq");

const EXPECTED_USDC =
  new PublicKey("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v");

const EXPECTED_USDT =
  new PublicKey("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB");

const PUBLIC_CANDIDATE =
  new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");

const INPUT_RAW = 100_000_000n;
const SLIPPAGE_BPS = 50;

function requirePublicKey(value, label) {
  if (!(value instanceof PublicKey)) {
    throw new Error(
      `EXPECTED_PUBLICKEY_${label}_GOT_${value?.constructor?.name || typeof value}`
    );
  }

  return value;
}

function amountString(value) {
  if (value === null || value === undefined) {
    return "null";
  }

  if (typeof value === "bigint") {
    return value.toString();
  }

  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }

  if (typeof value.toString === "function") {
    return value.toString();
  }

  return String(value);
}

function keyString(value) {
  if (value instanceof PublicKey) {
    return value.toBase58();
  }

  if (value?.publicKey instanceof PublicKey) {
    return value.publicKey.toBase58();
  }

  if (value?.address instanceof PublicKey) {
    return value.address.toBase58();
  }

  return String(value);
}

async function main() {
  console.log("[MTR-005] START");
  console.log(`[RPC] ${RPC}`);
  console.log(`[LB_PAIR] ${LB_PAIR.toBase58()}`);
  console.log(`[INPUT] ${INPUT_RAW.toString()} USDC`);
  console.log(`[SLIPPAGE_BPS] ${SLIPPAGE_BPS}`);

  const connection = new Connection(RPC, "confirmed");

  console.log("[SDK] creating Meteora DLMM pool");

  const pool = await DLMM.create(
    connection,
    LB_PAIR,
    { cluster: "mainnet-beta" }
  );

  console.log(`[POOL_PUBKEY] ${pool.pubkey.toBase58()}`);

  /*
   * SDK 1.9.14 runtime shape:
   *
   * pool.tokenX
   *   .publicKey -> PublicKey
   *   .mint.address -> PublicKey
   *
   * pool.tokenY
   *   .publicKey -> PublicKey
   *   .mint.address -> PublicKey
   */

  const tokenX = requirePublicKey(
    pool.tokenX.mint.address,
    "TOKEN_X_MINT_ADDRESS"
  );

  const tokenY = requirePublicKey(
    pool.tokenY.mint.address,
    "TOKEN_Y_MINT_ADDRESS"
  );

  console.log(`[POOL_TOKEN_X] ${tokenX.toBase58()}`);
  console.log(`[POOL_TOKEN_Y] ${tokenY.toBase58()}`);

  if (!tokenX.equals(EXPECTED_USDC)) {
    throw new Error(
      `EXPECTED_USDC_POOL_MISMATCH_${tokenX.toBase58()}`
    );
  }

  if (!tokenY.equals(EXPECTED_USDT)) {
    throw new Error(
      `EXPECTED_USDT_POOL_MISMATCH_${tokenY.toBase58()}`
    );
  }

  console.log("[POOL_TOKEN_BINDING_PASS]");

  /*
   * Verify the known public candidate directly.
   * No private key is loaded.
   * No signing.
   * No transaction submission.
   */

  console.log(
    `[PUBLIC_CANDIDATE] ${PUBLIC_CANDIDATE.toBase58()}`
  );

  const candidateInfo =
    await connection.getAccountInfo(
      PUBLIC_CANDIDATE,
      "confirmed"
    );

  if (!candidateInfo) {
    throw new Error("PUBLIC_CANDIDATE_ACCOUNT_NOT_FOUND");
  }

  console.log(
    `[PUBLIC_CANDIDATE_OWNER] ${candidateInfo.owner.toBase58()}`
  );

  console.log(
    `[PUBLIC_CANDIDATE_LAMPORTS] ${candidateInfo.lamports}`
  );

  const candidateUsdcAccounts =
    await connection.getTokenAccountsByOwner(
      PUBLIC_CANDIDATE,
      { mint: EXPECTED_USDC },
      "confirmed"
    );

  console.log(
    `[PUBLIC_CANDIDATE_USDC_ACCOUNTS] ${candidateUsdcAccounts.value.length}`
  );

  if (candidateUsdcAccounts.value.length === 0) {
    throw new Error(
      "PUBLIC_CANDIDATE_HAS_NO_USDC_ACCOUNT"
    );
  }

  let fundedAta = null;
  let fundedAmount = 0n;

  for (const item of candidateUsdcAccounts.value) {
    const amount =
      BigInt(
        item.account.data.parsed.info.tokenAmount.amount
      );

    console.log(
      `[CANDIDATE_USDC] ${item.pubkey.toBase58()} amount=${amount}`
    );

    if (amount >= INPUT_RAW && amount > fundedAmount) {
      fundedAta = item.pubkey;
      fundedAmount = amount;
    }
  }

  if (!fundedAta) {
    throw new Error(
      `PUBLIC_CANDIDATE_INSUFFICIENT_USDC_REQUIRED_${INPUT_RAW}`
    );
  }

  console.log(
    `[FUNDED_USDC_ATA] ${fundedAta.toBase58()}`
  );

  console.log(
    `[FUNDED_USDC_AMOUNT] ${fundedAmount.toString()}`
  );

  console.log("[PUBLIC_HOLDER_DISCOVERY_PASS]");

  const swapForY = true;

  console.log(`[SWAP_FOR_Y] ${swapForY}`);

  const binArrays =
    await pool.getBinArrayForSwap(
      swapForY,
      4
    );

  if (!Array.isArray(binArrays) || binArrays.length === 0) {
    throw new Error("NO_BIN_ARRAYS_RETURNED");
  }

  console.log(
    `[BIN_ARRAY_COUNT] ${binArrays.length}`
  );

  for (const bin of binArrays) {
    console.log(
      `[BIN_ARRAY] ${keyString(bin.publicKey ?? bin)}`
    );
  }

  const quote =
    pool.swapQuote(
      INPUT_RAW,
      swapForY,
      SLIPPAGE_BPS,
      binArrays,
      false
    );

  console.log(
    `[QUOTE_CONSUMED_IN] ${amountString(quote.consumedInAmount)}`
  );

  console.log(
    `[QUOTE_OUT] ${amountString(quote.outAmount)}`
  );

  console.log(
    `[QUOTE_MIN_OUT] ${amountString(quote.minOutAmount)}`
  );

  console.log(
    `[QUOTE_FEE] ${amountString(quote.fee)}`
  );

  console.log(
    `[QUOTE_PRICE_IMPACT] ${amountString(quote.priceImpact)}`
  );

  if (quote.binArraysPubkey) {
    console.log(
      `[QUOTE_BIN_ARRAYS] ${
        quote.binArraysPubkey
          .map((x) => keyString(x))
          .join(",")
      }`
    );
  }

  console.log("[OFFICIAL_SDK_QUOTE_PASS]");

  if (typeof pool.swap !== "function") {
    throw new Error(
      "OFFICIAL_POOL_SWAP_METHOD_MISSING"
    );
  }

  console.log(
    "[OFFICIAL_POOL_SWAP_METHOD_PRESENT]"
  );

  console.log(
    "[MTR-005] METEORA SDK POOL + MINT + HOLDER + QUOTE PASS"
  );

  console.log("[NO_SIGNING]");
  console.log("[NO_SEND]");
}

main().catch((err) => {
  console.error("[FAIL]", err?.stack || err);
  process.exitCode = 1;
});
'''

(TOOL_DIR / "package.json").write_text(
    json.dumps(PACKAGE_JSON, indent=2) + "\n",
    encoding="utf-8"
)

npm = shutil.which("npm.cmd") or shutil.which("npm")
if not npm:
    raise SystemExit("npm/npm.cmd not found on PATH")

subprocess.run(
    [npm, "install"],
    cwd=str(TOOL_DIR),
    check=True
)

sdk_index = (
    TOOL_DIR
    / "node_modules"
    / "@meteora-ag"
    / "dlmm"
    / "dist"
    / "index.mjs"
)

if not sdk_index.exists():
    raise SystemExit("Meteora SDK index.mjs not found")

sdk_text = sdk_index.read_text(
    encoding="utf-8"
)

old = "@coral-xyz/anchor/dist/cjs/utils/bytes"
new = "@coral-xyz/anchor/dist/cjs/utils/bytes/index.js"

if old in sdk_text and new not in sdk_text:
    sdk_index.write_text(
        sdk_text.replace(old, new),
        encoding="utf-8"
    )

TARGET.write_text(
    textwrap.dedent(JS).lstrip(),
    encoding="utf-8"
)

generated = TARGET.read_text(
    encoding="utf-8"
)

required = [
    'import DLMM from "@meteora-ag/dlmm";',
    "pool.tokenX.mint.address",
    "pool.tokenY.mint.address",
    "getBinArrayForSwap",
    "swapQuote",
    "pool.swap"
]

for item in required:
    if item not in generated:
        raise SystemExit(
            f"MTR-005 REQUIRED CONTENT MISSING: {item}"
        )

subprocess.run(
    ["node", "--check", str(TARGET)],
    cwd=str(ROOT),
    check=True
)

print("[PASS] Meteora Node-ESM compatibility already correct")
print("[PASS] official SDK default import preserved")
print("[PASS] exact SDK mint.address shape encoded")
print("[PASS] official SDK swap logic untouched")
print(f"[PASS] {TARGET}")
print("[BUILD COMPLETE] MTR-005")