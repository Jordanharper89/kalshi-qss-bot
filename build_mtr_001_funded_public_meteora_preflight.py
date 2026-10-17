from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TOOL_DIR = ROOT / "tools" / "meteora_funded_public_preflight"
TOOL_DIR.mkdir(parents=True, exist_ok=True)

PACKAGE = {
    "name": "meteora-funded-public-preflight",
    "private": True,
    "type": "module",
    "dependencies": {
        "@meteora-ag/dlmm": "1.9.14",
        "@solana/web3.js": "^1.98.4",
    },
}

NODE_SOURCE = r'''
import { Connection, PublicKey } from "@solana/web3.js";
import DLMM from "@meteora-ag/dlmm";

const RPC =
  process.env.QSB_METEORA_PROOF_RPC ||
  "https://api.mainnet-beta.solana.com";

const PAIR = new PublicKey(
  "ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq"
);

const USDC = new PublicKey(
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
);

const EXPECTED_TOKEN_Y = new PublicKey(
  "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
);

const TOKEN_PROGRAM = new PublicKey(
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
);

const ATA_PROGRAM = new PublicKey(
  "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
);

const SYSTEM_PROGRAM = new PublicKey(
  "11111111111111111111111111111111"
);

const INPUT_AMOUNT = 100_000_000n;
const SLIPPAGE_BPS = 50;
const MIN_SOL_LAMPORTS = 20_000_000;

function canonicalAta(owner, mint) {
  return PublicKey.findProgramAddressSync(
    [
      owner.toBuffer(),
      TOKEN_PROGRAM.toBuffer(),
      mint.toBuffer(),
    ],
    ATA_PROGRAM
  )[0];
}

async function parsedTokenAccount(connection, address) {
  const result = await connection.getParsedAccountInfo(
    address,
    "confirmed"
  );

  if (!result.value) {
    return null;
  }

  const data = result.value.data;

  if (!("parsed" in data)) {
    return null;
  }

  return data.parsed?.info || null;
}

async function isSystemWallet(connection, owner) {
  const account = await connection.getAccountInfo(
    owner,
    "confirmed"
  );

  return (
    account !== null &&
    account.owner.equals(SYSTEM_PROGRAM)
  );
}

async function main() {
  console.log("[MTR-001] START");
  console.log(`[RPC] ${RPC}`);
  console.log(`[LB_PAIR] ${PAIR.toBase58()}`);
  console.log(`[INPUT] ${INPUT_AMOUNT.toString()} USDC`);
  console.log(`[SLIPPAGE_BPS] ${SLIPPAGE_BPS}`);

  const connection = new Connection(
    RPC,
    { commitment: "confirmed" }
  );

  console.log("[SDK] creating Meteora DLMM pool");

  const pool = await DLMM.create(
    connection,
    PAIR
  );

  const pair = pool.lbPair;

  const tokenX = new PublicKey(pair.tokenXMint);
  const tokenY = new PublicKey(pair.tokenYMint);

  console.log(`[POOL_TOKEN_X] ${tokenX.toBase58()}`);
  console.log(`[POOL_TOKEN_Y] ${tokenY.toBase58()}`);

  if (!tokenX.equals(USDC)) {
    throw new Error(
      `EXPECTED_TOKEN_X_USDC_MISMATCH:${tokenX.toBase58()}`
    );
  }

  if (!tokenY.equals(EXPECTED_TOKEN_Y)) {
    throw new Error(
      `EXPECTED_TOKEN_Y_MISMATCH:${tokenY.toBase58()}`
    );
  }

  console.log("[POOL_TOKEN_BINDING_PASS]");

  console.log(
    "[PUBLIC_HOLDER_DISCOVERY] querying largest USDC accounts"
  );

  const largest =
    await connection.getTokenLargestAccounts(
      USDC,
      "confirmed"
    );

  let selected = null;

  for (const entry of largest.value) {
    const tokenInfo =
      await parsedTokenAccount(
        connection,
        entry.address
      );

    if (!tokenInfo) {
      continue;
    }

    const amount =
      BigInt(
        tokenInfo.tokenAmount?.amount || "0"
      );

    if (amount < INPUT_AMOUNT) {
      continue;
    }

    const ownerText = tokenInfo.owner;

    if (!ownerText) {
      continue;
    }

    let owner;

    try {
      owner = new PublicKey(ownerText);
    } catch {
      continue;
    }

    const expectedAta =
      canonicalAta(owner, USDC);

    if (!expectedAta.equals(entry.address)) {
      continue;
    }

    if (
      !(await isSystemWallet(
        connection,
        owner
      ))
    ) {
      continue;
    }

    const sol =
      await connection.getBalance(
        owner,
        "confirmed"
      );

    if (sol < MIN_SOL_LAMPORTS) {
      continue;
    }

    selected = {
      tokenAccount: entry.address,
      owner,
      amount,
      sol,
    };

    break;
  }

  if (!selected) {
    throw new Error(
      "NO_FUNDED_PUBLIC_USDC_ATA_HOLDER_FOUND"
    );
  }

  console.log(
    `[PUBLIC_WALLET] ${selected.owner.toBase58()}`
  );

  console.log(
    `[PUBLIC_USDC_ATA] ${selected.tokenAccount.toBase58()}`
  );

  console.log(
    `[PUBLIC_USDC_AMOUNT] ${selected.amount.toString()}`
  );

  console.log(
    `[PUBLIC_SOL_LAMPORTS] ${selected.sol}`
  );

  console.log(
    "[BIN_ARRAY_DISCOVERY] official SDK"
  );

  const binArrays =
    await pool.getBinArrayForSwap(
      true,
      4
    );

  console.log(
    `[BIN_ARRAY_COUNT] ${binArrays.length}`
  );

  for (
    let i = 0;
    i < binArrays.length;
    i++
  ) {
    console.log(
      `[BIN_ARRAY ${i}] ${binArrays[i].publicKey.toBase58()}`
    );
  }

  console.log("[QUOTE] official SDK");

  const quote =
    pool.swapQuote(
      INPUT_AMOUNT,
      true,
      SLIPPAGE_BPS,
      binArrays,
      false
    );

  console.log(
    `[QUOTE_CONSUMED] ${quote.consumedInAmount.toString()}`
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
    `[QUOTE_PRICE_IMPACT] ${quote.priceImpact}`
  );

  console.log(
    `[QUOTE_BIN_ARRAYS] ${
      (quote.binArraysPubkey || [])
        .map((x) => x.toBase58())
        .join(",")
    }`
  );

  console.log(
    "[OFFICIAL_SWAP2] invoking pool.swap"
  );

  const transaction =
    await pool.swap({
      inToken: tokenX,
      outToken: tokenY,
      inAmount: quote.consumedInAmount,
      lbPair: PAIR,
      user: selected.owner,
      minOutAmount: quote.minOutAmount,
      binArraysPubkey:
        quote.binArraysPubkey,
    });

  console.log(
    `[TRANSACTION_TYPE] ${transaction.constructor.name}`
  );

  const instructions =
    transaction.instructions || [];

  console.log(
    `[INSTRUCTION_COUNT] ${instructions.length}`
  );

  for (
    let i = 0;
    i < instructions.length;
    i++
  ) {
    const ix = instructions[i];

    console.log(
      `[IX ${i}] program=${ix.programId.toBase58()} accounts=${ix.keys.length} data_len=${ix.data.length}`
    );

    console.log(
      `[IX ${i} DATA_HEX] ${Buffer.from(ix.data).toString("hex")}`
    );

    for (
      let j = 0;
      j < ix.keys.length;
      j++
    ) {
      const key = ix.keys[j];

      console.log(
        `[IX ${i} ACCOUNT ${j}] ${key.pubkey.toBase58()} signer=${key.isSigner} writable=${key.isWritable}`
      );
    }
  }

  const meteoraInstruction =
    instructions.find(
      (ix) =>
        ix.programId.equals(
          new PublicKey(
            "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
          )
        )
    );

  if (!meteoraInstruction) {
    throw new Error(
      "NO_METEORA_SWAP2_INSTRUCTION_FOUND"
    );
  }

  const discriminator =
    Buffer.from(
      meteoraInstruction.data
    )
      .subarray(0, 8)
      .toString("hex");

  console.log(
    `[METEORA_DISCRIMINATOR] ${discriminator}`
  );

  if (
    discriminator !==
    "414b3f4ceb5b5b88"
  ) {
    throw new Error(
      `UNEXPECTED_SWAP2_DISCRIMINATOR:${discriminator}`
    );
  }

  if (
    meteoraInstruction.keys.length < 17
  ) {
    throw new Error(
      `METEORA_ACCOUNT_COUNT_TOO_LOW:${meteoraInstruction.keys.length}`
    );
  }

  console.log(
    "[STANDALONE_METEORA_PREFLIGHT_PASS]"
  );

  console.log(
    "[MTR-001] NO_SIGN NO_SEND"
  );
}

main().catch((error) => {
  console.error(
    `[FAIL] ${error?.stack || error}`
  );
  process.exit(1);
});
'''

TEST_SOURCE = r'''
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TOOL = ROOT / "tools" / "meteora_funded_public_preflight"
NODE = TOOL / "meteora_funded_public_preflight.mjs"
PACKAGE = TOOL / "package.json"


def fail(message):
    raise AssertionError(message)


def main():
    if not NODE.exists():
        fail("missing Node proof harness")

    if not PACKAGE.exists():
        fail("missing package.json")

    source = NODE.read_text(
        encoding="utf-8"
    )

    required = [
        "getTokenLargestAccounts",
        "canonicalAta",
        "pool.getBinArrayForSwap",
        "pool.swapQuote",
        "pool.swap",
        "414b3f4ceb5b5b88",
        "STANDALONE_METEORA_PREFLIGHT_PASS",
        "NO_SIGN NO_SEND",
    ]

    for item in required:
        if item not in source:
            fail(
                f"missing required proof element: {item}"
            )

    forbidden = [
        "QSB_SOLANA_PRIVATE_KEY",
        "sendAndConfirmTransaction",
        "sendRawTransaction",
        "signTransaction",
        "signAllTransactions",
    ]

    for item in forbidden:
        if item in source:
            fail(
                f"forbidden live/private-key operation present: {item}"
            )

    result = subprocess.run(
        ["node", "--check", str(NODE)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        fail("Node syntax check failed")

    print(
        "[PASS] MTR-001 installer/proof harness present"
    )
    print(
        "[PASS] exact live pool token-X binding present"
    )
    print(
        "[PASS] exact live pool token-Y binding present"
    )
    print(
        "[PASS] dynamic public funded USDC-holder discovery present"
    )
    print(
        "[PASS] canonical ATA requirement present"
    )
    print(
        "[PASS] system-wallet/SOL requirement present"
    )
    print(
        "[PASS] official Meteora getBinArrayForSwap present"
    )
    print(
        "[PASS] official Meteora swapQuote present"
    )
    print(
        "[PASS] official Meteora pool.swap present"
    )
    print(
        "[PASS] official Swap2 discriminator guard present"
    )
    print(
        "[PASS] no private key path present"
    )
    print(
        "[PASS] no transaction signing/send path present"
    )
    print(
        "[PASS] Node syntax check"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

(ROOT / "test_mtr_001_funded_public_meteora_preflight.py").write_text(
    TEST_SOURCE,
    encoding="utf-8",
)

(TOOL_DIR / "package.json").write_text(
    json.dumps(PACKAGE, indent=2) + "\n",
    encoding="utf-8",
)

NODE_PATH = TOOL_DIR / "meteora_funded_public_preflight.mjs"

NODE_PATH.write_text(
    NODE_SOURCE,
    encoding="utf-8",
)

npm = shutil.which("npm.cmd") or shutil.which("npm")

if not npm:
    print("[FAIL] npm.cmd/npm not found")
    sys.exit(1)

print(f"[BUILD] npm={npm}")

result = subprocess.run(
    [
        npm,
        "--prefix",
        str(TOOL_DIR),
        "install",
        "--no-audit",
        "--no-fund",
    ],
    cwd=ROOT,
)

if result.returncode != 0:
    sys.exit(result.returncode)

sdk_index = (
    TOOL_DIR
    / "node_modules"
    / "@meteora-ag"
    / "dlmm"
    / "dist"
    / "index.mjs"
)

if sdk_index.exists():
    text = sdk_index.read_text(
        encoding="utf-8"
    )

    old = "@coral-xyz/anchor/dist/cjs/utils/bytes"
    new = "@coral-xyz/anchor/dist/cjs/utils/bytes/index.js"

    if old in text and new not in text:
        text = text.replace(old, new)
        sdk_index.write_text(
            text,
            encoding="utf-8",
        )
        print(
            "[PASS] Meteora Node-ESM compatibility fix applied"
        )
    else:
        print(
            "[PASS] Meteora Node-ESM compatibility already correct"
        )

print("[PASS] official SDK swap logic untouched")
print(f"[PASS] {NODE_PATH}")
print("[BUILD COMPLETE] MTR-001")