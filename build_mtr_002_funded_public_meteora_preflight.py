from pathlib import Path
import subprocess
import shutil
import textwrap

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "tools" / "meteora_funded_public_preflight"
OUT.mkdir(parents=True, exist_ok=True)

npm = shutil.which("npm.cmd") or shutil.which("npm")
if not npm:
    raise SystemExit("[FAIL] npm.cmd not found")

package_json = r"""
{
  "name": "meteora-funded-public-preflight",
  "private": true,
  "type": "module",
  "dependencies": {
    "@meteora-ag/dlmm": "1.9.14",
    "@solana/web3.js": "^1.98.4",
    "@solana/spl-token": "^0.4.14"
  }
}
"""

js = r"""
import { Connection, PublicKey, SystemProgram } from "@solana/web3.js";
import {
  getAssociatedTokenAddress,
  getAccount
} from "@solana/spl-token";
import DLMM from "@meteora-ag/dlmm";

const RPC = "https://api.mainnet-beta.solana.com";

const PAIR = new PublicKey(
  "ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq"
);

const USDC = new PublicKey(
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
);

const USDT = new PublicKey(
  "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
);

const TOKEN_PROGRAM = new PublicKey(
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
);

const SYSTEM_PROGRAM = SystemProgram.programId;

const METEORA_PROGRAM = new PublicKey(
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
);

const INPUT_AMOUNT = 100_000_000n;
const SLIPPAGE_BPS = 50;
const MIN_SOL = 20_000_000n;

const PUBLIC_CANDIDATES = [
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR"
];

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function rpcRetry(label, fn, attempts = 5) {
  let last;

  for (let i = 1; i <= attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      last = err;
      const msg = String(err?.message || err);

      if (!/429|Too Many Requests|fetch failed|ECONNRESET|ETIMEDOUT/i.test(msg)) {
        throw err;
      }

      if (i < attempts) {
        const delay = Math.min(1000 * (2 ** (i - 1)), 8000);
        console.log(
          `[RPC-RETRY] ${label} attempt=${i}/${attempts} delay_ms=${delay}`
        );
        await sleep(delay);
      }
    }
  }

  throw last;
}

async function verifyFundedCandidate(connection) {
  console.log("[PUBLIC_HOLDER_DISCOVERY] verifying public candidate");

  for (const candidateString of PUBLIC_CANDIDATES) {
    const owner = new PublicKey(candidateString);

    console.log(`[CANDIDATE] ${owner.toBase58()}`);

    const ownerInfo = await rpcRetry(
      "getAccountInfo(owner)",
      () => connection.getAccountInfo(owner, "confirmed")
    );

    if (!ownerInfo) {
      console.log("[CANDIDATE_REJECT] owner account missing");
      continue;
    }

    if (!ownerInfo.owner.equals(SYSTEM_PROGRAM)) {
      console.log(
        `[CANDIDATE_REJECT] owner_program=${ownerInfo.owner.toBase58()}`
      );
      continue;
    }

    const solLamports = BigInt(ownerInfo.lamports);

    console.log(`[OWNER_SOL_LAMPORTS] ${solLamports}`);

    if (solLamports < MIN_SOL) {
      console.log("[CANDIDATE_REJECT] insufficient SOL");
      continue;
    }

    const ata = await getAssociatedTokenAddress(
      USDC,
      owner,
      false,
      TOKEN_PROGRAM
    );

    console.log(`[USDC_ATA] ${ata.toBase58()}`);

    const ataInfo = await rpcRetry(
      "getAccountInfo(USDC ATA)",
      () => connection.getAccountInfo(ata, "confirmed")
    );

    if (!ataInfo) {
      console.log("[CANDIDATE_REJECT] canonical USDC ATA missing");
      continue;
    }

    if (!ataInfo.owner.equals(TOKEN_PROGRAM)) {
      console.log(
        `[CANDIDATE_REJECT] ATA_PROGRAM=${ataInfo.owner.toBase58()}`
      );
      continue;
    }

    const tokenAccount = await rpcRetry(
      "getAccount(USDC ATA)",
      () => getAccount(
        connection,
        ata,
        "confirmed",
        TOKEN_PROGRAM
      )
    );

    if (!tokenAccount.mint.equals(USDC)) {
      console.log(
        `[CANDIDATE_REJECT] ATA_MINT=${tokenAccount.mint.toBase58()}`
      );
      continue;
    }

    if (!tokenAccount.owner.equals(owner)) {
      console.log(
        `[CANDIDATE_REJECT] ATA_OWNER=${tokenAccount.owner.toBase58()}`
      );
      continue;
    }

    const amount = BigInt(tokenAccount.amount);

    console.log(`[USDC_RAW_BALANCE] ${amount}`);

    if (amount < INPUT_AMOUNT) {
      console.log("[CANDIDATE_REJECT] insufficient USDC");
      continue;
    }

    console.log("[FUNDED_PUBLIC_USDC_HOLDER_PASS]");

    return {
      owner,
      ata,
      solLamports,
      usdcAmount: amount
    };
  }

  throw new Error("NO_VERIFIED_FUNDED_PUBLIC_USDC_HOLDER");
}

async function main() {
  console.log("[MTR-002] START");
  console.log(`[RPC] ${RPC}`);
  console.log(`[LB_PAIR] ${PAIR.toBase58()}`);
  console.log(`[INPUT] ${INPUT_AMOUNT} USDC`);
  console.log(`[SLIPPAGE_BPS] ${SLIPPAGE_BPS}`);

  const connection = new Connection(RPC, "confirmed");

  console.log("[SDK] creating Meteora DLMM pool");

  const pool = await rpcRetry(
    "DLMM.create",
    () => DLMM.create(connection, PAIR, {
      cluster: "mainnet-beta"
    })
  );

  const tokenX = pool.tokenX.mint;
  const tokenY = pool.tokenY.mint;

  console.log(`[POOL_TOKEN_X] ${tokenX.toBase58()}`);
  console.log(`[POOL_TOKEN_Y] ${tokenY.toBase58()}`);

  if (!tokenX.equals(USDC)) {
    throw new Error("EXPECTED_USDC_TOKEN_X_MISMATCH");
  }

  if (!tokenY.equals(USDT)) {
    throw new Error("EXPECTED_USDT_TOKEN_Y_MISMATCH");
  }

  console.log("[POOL_TOKEN_BINDING_PASS]");

  const funded = await verifyFundedCandidate(connection);

  console.log(`[FUNDED_OWNER] ${funded.owner.toBase58()}`);
  console.log(`[FUNDED_ATA] ${funded.ata.toBase58()}`);
  console.log(`[FUNDED_USDC_RAW] ${funded.usdcAmount}`);
  console.log(`[FUNDED_SOL_LAMPORTS] ${funded.solLamports}`);

  const binArrays = await rpcRetry(
    "getBinArrayForSwap",
    () => pool.getBinArrayForSwap(true, 4)
  );

  if (!binArrays || binArrays.length === 0) {
    throw new Error("NO_BIN_ARRAYS");
  }

  console.log(`[BIN_ARRAY_COUNT] ${binArrays.length}`);

  for (const b of binArrays) {
    console.log(`[BIN_ARRAY] ${b.toBase58()}`);
  }

  const quote = await rpcRetry(
    "swapQuote",
    () => pool.swapQuote(
      INPUT_AMOUNT,
      true,
      SLIPPAGE_BPS,
      binArrays,
      false
    )
  );

  console.log(`[QUOTE_CONSUMED_IN] ${quote.consumedInAmount}`);
  console.log(`[QUOTE_OUT] ${quote.outAmount}`);
  console.log(`[QUOTE_MIN_OUT] ${quote.minOutAmount}`);
  console.log(`[QUOTE_FEE] ${quote.fee}`);
  console.log(`[QUOTE_PRICE_IMPACT] ${quote.priceImpact}`);

  if (!quote.binArraysPubkey || quote.binArraysPubkey.length === 0) {
    throw new Error("QUOTE_RETURNED_NO_BIN_ARRAY_PUBKEYS");
  }

  console.log(
    `[QUOTE_BIN_ARRAYS] ${
      quote.binArraysPubkey.map(x => x.toBase58()).join(",")
    }`
  );

  const tx = await rpcRetry(
    "official pool.swap",
    () => pool.swap({
      inToken: tokenX,
      outToken: tokenY,
      inAmount: quote.consumedInAmount,
      lbPair: pool.pubkey,
      user: funded.owner,
      minOutAmount: quote.minOutAmount,
      binArraysPubkey: quote.binArraysPubkey
    })
  );

  if (!tx || !tx.instructions || tx.instructions.length === 0) {
    throw new Error("OFFICIAL_SWAP_RETURNED_NO_INSTRUCTIONS");
  }

  const meteoraInstructions = tx.instructions.filter(
    ix => ix.programId.equals(METEORA_PROGRAM)
  );

  if (meteoraInstructions.length !== 1) {
    throw new Error(
      `EXPECTED_ONE_METEORA_INSTRUCTION_GOT_${meteoraInstructions.length}`
    );
  }

  const meteoraIx = meteoraInstructions[0];

  const discriminator = Buffer.from(
    meteoraIx.data.slice(0, 8)
  ).toString("hex");

  console.log(`[SWAP2_DISCRIMINATOR] ${discriminator}`);

  if (discriminator !== "414b3f4ceb5b5b88") {
    throw new Error("NOT_METEORA_SWAP2");
  }

  console.log(`[METEORA_ACCOUNT_COUNT] ${meteoraIx.keys.length}`);

  if (meteoraIx.keys.length < 17) {
    throw new Error("METEORA_SWAP2_ACCOUNT_COUNT_TOO_LOW");
  }

  console.log("[OFFICIAL_SWAP2_BUILD_PASS]");
  console.log("[STANDALONE_METEORA_PREFLIGHT_PASS]");
  console.log("[MTR-002] COMPLETE");
}

main().catch(err => {
  console.error(`[FAIL] ${err?.stack || err}`);
  process.exit(1);
});
"""

(OUT / "package.json").write_text(
    textwrap.dedent(package_json).strip() + "\n",
    encoding="utf-8"
)

target = OUT / "meteora_funded_public_preflight.mjs"

target.write_text(
    textwrap.dedent(js).strip() + "\n",
    encoding="utf-8"
)

subprocess.run(
    [npm, "install", "--no-audit", "--no-fund"],
    cwd=OUT,
    check=True
)

sdk_index = (
    OUT /
    "node_modules" /
    "@meteora-ag" /
    "dlmm" /
    "dist" /
    "index.mjs"
)

if not sdk_index.exists():
    raise SystemExit("[FAIL] Meteora SDK index.mjs missing")

sdk = sdk_index.read_text(encoding="utf-8")

old = "@coral-xyz/anchor/dist/cjs/utils/bytes"
new = "@coral-xyz/anchor/dist/cjs/utils/bytes/index.js"

if old in sdk and new not in sdk:
    sdk = sdk.replace(old, new)
    sdk_index.write_text(sdk, encoding="utf-8")
    print("[PASS] Meteora Node-ESM compatibility fix applied")
elif new in sdk:
    print("[PASS] Meteora Node-ESM compatibility already correct")
else:
    print("[PASS] no Anchor bytes compatibility replacement required")

# HARD GUARD: verify the actual generated file, not the source installer.
actual = target.read_text(encoding="utf-8")

if 'import DLMM from "@meteora-ag/dlmm";' not in actual:
    raise SystemExit(
        "[FAIL] GENERATED HARNESS DOES NOT CONTAIN DEFAULT DLMM IMPORT"
    )

if 'import { DLMM } from "@meteora-ag/dlmm";' in actual:
    raise SystemExit(
        "[FAIL] GENERATED HARNESS STILL CONTAINS NAMED DLMM IMPORT"
    )

print("[PASS] generated harness uses Meteora default DLMM export")
print("[PASS] official SDK swap logic untouched")
print(f"[PASS] {target}")
print("[BUILD COMPLETE] MTR-002")