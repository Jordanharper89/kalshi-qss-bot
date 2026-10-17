from pathlib import Path

ROOT = Path(__file__).resolve().parent
HARNESS_DIR = ROOT / "tools" / "meteora_funded_public_preflight"
HARNESS_DIR.mkdir(parents=True, exist_ok=True)

HARNESS = r'''import { Connection, PublicKey, Transaction } from "@solana/web3.js";
import {
  ASSOCIATED_TOKEN_PROGRAM_ID,
  TOKEN_PROGRAM_ID,
  getAssociatedTokenAddressSync,
} from "@solana/spl-token";
import DLMM from "@meteora-ag/dlmm";

const RPC = "https://api.mainnet-beta.solana.com";

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

const SWAP2_DISCRIMINATOR =
  "414b3f4ceb5b5b88";

const INPUT_RAW_USDC = 100000000n;
const SLIPPAGE_BPS = 50;

function provePublicKey(label, value) {
  console.log(`[KEY_CHECK_BEGIN] ${label}`);
  console.log(`[KEY_VALUE] ${value}`);
  console.log(`[KEY_LENGTH] ${value.length}`);

  const key = new PublicKey(value);
  const normalized = key.toBase58();

  console.log(`[KEY_NORMALIZED] ${normalized}`);

  if (normalized !== value) {
    throw new Error(
      `${label} normalization mismatch`
    );
  }

  console.log(`[KEY_CHECK_PASS] ${label}`);
  return key;
}

console.log("[MTR-013] START");
console.log(`[RPC] ${RPC}`);

const lbPair =
  provePublicKey("LB_PAIR", LB_PAIR);

const meteoraProgram =
  provePublicKey("METEORA_PROGRAM", METEORA_PROGRAM);

const candidate =
  provePublicKey("PUBLIC_CANDIDATE", PUBLIC_CANDIDATE);

const usdcMint =
  provePublicKey("USDC_MINT", USDC_MINT);

const usdtMint =
  provePublicKey("USDT_MINT", USDT_MINT);

const tokenProgram =
  provePublicKey("TOKEN_PROGRAM", TOKEN_PROGRAM);

const fundedUsdcAccount =
  provePublicKey(
    "FUNDED_USDC_ACCOUNT",
    FUNDED_USDC_ACCOUNT
  );

if (
  METEORA_PROGRAM !==
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
) {
  throw new Error(
    "Meteora program constant is not the exact verified program ID"
  );
}

console.log(
  "[METEORA_PROGRAM_ID_EXACT] PASS"
);

if (!tokenProgram.equals(TOKEN_PROGRAM_ID)) {
  throw new Error(
    "Token program mismatch"
  );
}

console.log(
  "[TOKEN_PROGRAM_BINDING] PASS"
);

const connection =
  new Connection(RPC, "confirmed");

async function rawRpc(method, params) {
  const response = await fetch(RPC, {
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
    throw new Error(
      `RPC HTTP ${response.status}`
    );
  }

  const body = await response.json();

  if (body.error) {
    throw new Error(
      `${method}: ${JSON.stringify(body.error)}`
    );
  }

  return body.result;
}

async function verifyFundedAccount() {
  console.log(
    "[RPC] verifying exact funded USDC account"
  );

  const result = await rawRpc(
    "getAccountInfo",
    [
      FUNDED_USDC_ACCOUNT,
      {
        encoding: "jsonParsed",
        commitment: "confirmed",
      },
    ]
  );

  if (!result?.value) {
    throw new Error(
      "Funded USDC account does not exist"
    );
  }

  const info =
    result.value?.data?.parsed?.info;

  if (!info?.tokenAmount) {
    throw new Error(
      "Funded account did not return parsed token data"
    );
  }

  const raw =
    BigInt(info.tokenAmount.amount);

  console.log(
    `[FUNDED_USDC_MINT] ${info.mint}`
  );

  console.log(
    `[FUNDED_USDC_OWNER] ${info.owner}`
  );

  console.log(
    `[FUNDED_USDC_RAW] ${raw.toString()}`
  );

  console.log(
    `[FUNDED_USDC_DECIMALS] ${info.tokenAmount.decimals}`
  );

  console.log(
    `[TOKEN_ACCOUNT_PROGRAM_OWNER] ${result.value.owner}`
  );

  if (info.mint !== USDC_MINT) {
    throw new Error(
      "Funded account mint mismatch"
    );
  }

  if (info.owner !== PUBLIC_CANDIDATE) {
    throw new Error(
      "Funded account owner mismatch"
    );
  }

  if (result.value.owner !== TOKEN_PROGRAM) {
    throw new Error(
      "Funded account program owner mismatch"
    );
  }

  if (raw < INPUT_RAW_USDC) {
    throw new Error(
      "Funded USDC balance below required input"
    );
  }

  console.log(
    "[FUNDING_ACCOUNT_VERIFICATION] PASS"
  );
}

async function main() {
  await verifyFundedAccount();

  const canonicalAta =
    getAssociatedTokenAddressSync(
      usdcMint,
      candidate,
      false,
      TOKEN_PROGRAM_ID,
      ASSOCIATED_TOKEN_PROGRAM_ID
    );

  console.log(
    `[CANONICAL_USDC_ATA] ${canonicalAta.toBase58()}`
  );

  if (
    canonicalAta.equals(
      fundedUsdcAccount
    )
  ) {
    throw new Error(
      "Funded account unexpectedly equals canonical ATA"
    );
  }

  console.log(
    "[FUNDED_ACCOUNT_IS_CANONICAL_ATA] NO"
  );

  console.log(
    "[SDK] creating official Meteora DLMM pool"
  );

  const pool =
    await DLMM.create(
      connection,
      lbPair
    );

  console.log(
    `[POOL_PUBKEY] ${pool.pubkey.toBase58()}`
  );

  console.log(
    `[POOL_TOKEN_X] ${pool.tokenX.mint.address.toBase58()}`
  );

  console.log(
    `[POOL_TOKEN_Y] ${pool.tokenY.mint.address.toBase58()}`
  );

  if (
    !pool.tokenX.mint.address.equals(usdcMint) ||
    !pool.tokenY.mint.address.equals(usdtMint)
  ) {
    throw new Error(
      "Pool token binding mismatch"
    );
  }

  console.log(
    "[POOL_TOKEN_BINDING] PASS"
  );

  await pool.refetchStates();

  const swapForY = true;

  console.log(
    `[SWAP_DIRECTION] USDC_X_TO_USDT_Y=${swapForY}`
  );

  const binArrays =
    await pool.getBinArrayForSwap(
      swapForY,
      4
    );

  console.log(
    `[BIN_ARRAY_COUNT] ${binArrays.length}`
  );

  if (!binArrays.length) {
    throw new Error(
      "No bin arrays returned"
    );
  }

  const quote =
    await pool.swapQuote(
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
    "[SDK_QUOTE] PASS"
  );

  console.log(
    "[SDK] constructing official pool.swap transaction"
  );

  const tx =
    await pool.swap({
      inToken:
        pool.tokenX.publicKey,
      outToken:
        pool.tokenY.publicKey,
      inAmount:
        quote.consumedInAmount,
      lbPair:
        pool.pubkey,
      user:
        candidate,
      minOutAmount:
        quote.minOutAmount,
      binArraysPubkey:
        quote.binArraysPubkey,
    });

  if (!(tx instanceof Transaction)) {
    throw new Error(
      "Official pool.swap did not return Transaction"
    );
  }

  console.log(
    "[SDK_SWAP_TRANSACTION] CONSTRUCTED"
  );

  const swapInstruction =
    tx.instructions.find(
      (ix) =>
        ix.programId.equals(
          meteoraProgram
        ) &&
        Buffer.from(ix.data)
          .toString("hex")
          .startsWith(
            SWAP2_DISCRIMINATOR
          )
    );

  if (!swapInstruction) {
    throw new Error(
      "Meteora Swap2 instruction not found"
    );
  }

  console.log(
    "[SWAP2_INSTRUCTION] FOUND"
  );

  const canonicalIndexes = [];

  swapInstruction.keys.forEach(
    (meta, index) => {
      if (
        meta.pubkey.equals(
          canonicalAta
        )
      ) {
        canonicalIndexes.push(index);
      }
    }
  );

  console.log(
    `[CANONICAL_INPUT_META_COUNT] ${canonicalIndexes.length}`
  );

  if (
    canonicalIndexes.length !== 1
  ) {
    throw new Error(
      `Expected exactly one canonical input ATA; found ${canonicalIndexes.length}`
    );
  }

  const inputIndex =
    canonicalIndexes[0];

  const original =
    swapInstruction.keys[
      inputIndex
    ];

  console.log(
    `[ORIGINAL_INPUT_ACCOUNT] ${original.pubkey.toBase58()}`
  );

  if (!original.isWritable) {
    throw new Error(
      "Input account is not writable"
    );
  }

  swapInstruction.keys[
    inputIndex
  ] = {
    pubkey:
      fundedUsdcAccount,
    isSigner:
      original.isSigner,
    isWritable:
      original.isWritable,
  };

  console.log(
    `[REBOUND_INPUT_ACCOUNT] ${swapInstruction.keys[inputIndex].pubkey.toBase58()}`
  );

  if (
    !swapInstruction.keys[
      inputIndex
    ].pubkey.equals(
      fundedUsdcAccount
    )
  ) {
    throw new Error(
      "Funded input rebinding failed"
    );
  }

  console.log(
    "[FUNDED_INPUT_BINDING] PASS"
  );

  const { blockhash } =
    await connection.getLatestBlockhash(
      "confirmed"
    );

  tx.feePayer = candidate;
  tx.recentBlockhash =
    blockhash;

  const unsigned =
    tx.serialize({
      requireAllSignatures:
        false,
      verifySignatures:
        false,
    });

  console.log(
    `[UNSIGNED_TX_BYTES] ${unsigned.length}`
  );

  console.log(
    `[INSTRUCTION_COUNT] ${tx.instructions.length}`
  );

  console.log(
    "[SIGNING] DISABLED"
  );

  console.log(
    "[BROADCAST] DISABLED"
  );

  console.log(
    "[SIMULATION] calling Solana simulateTransaction"
  );

  const simulation =
    await connection.simulateTransaction(
      tx,
      {
        sigVerify: false,
        replaceRecentBlockhash:
          true,
        commitment:
          "confirmed",
      }
    );

  console.log(
    `[SIMULATION_UNITS_CONSUMED] ${
      simulation.value.unitsConsumed ??
      "N/A"
    }`
  );

  if (
    simulation.value.logs
  ) {
    console.log(
      "[SIMULATION_LOGS_BEGIN]"
    );

    for (
      const line
      of simulation.value.logs
    ) {
      console.log(line);
    }

    console.log(
      "[SIMULATION_LOGS_END]"
    );
  }

  if (
    simulation.value.err
  ) {
    console.log(
      "[SIMULATION_RESULT] FAIL"
    );

    console.log(
      `[SIMULATION_ERROR] ${JSON.stringify(
        simulation.value.err
      )}`
    );

    throw new Error(
      "MTR-013 physical simulation failed"
    );
  }

  console.log(
    "[SIMULATION_RESULT] PASS"
  );

  console.log(
    "[MTR-013] OFFICIAL METEORA SWAP2 WITH VERIFIED FUNDED INPUT SIMULATED SUCCESSFULLY."
  );

  console.log(
    "[MTR-013] NO SIGNING."
  );

  console.log(
    "[MTR-013] NO SENDING."
  );

  console.log(
    "[MTR-013] NO CANONICAL EXECUTOR."
  );
}

main().catch(
  (error) => {
    console.error(
      `[MTR-013] FAIL: ${
        error?.stack ?? error
      }`
    );

    process.exitCode = 1;
  }
);
'''

TEST = r'''from pathlib import Path

ROOT = Path(__file__).resolve().parent

HARNESS = (
    ROOT
    / "tools"
    / "meteora_funded_public_preflight"
    / "mtr_013_meteora_correct_program_id.mjs"
)

text = HARNESS.read_text(
    encoding="utf-8"
)

checks = [
    (
        'import DLMM from "@meteora-ag/dlmm";',
        "Official Meteora DLMM import present"
    ),
    (
        "ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq",
        "Exact LB pair present"
    ),
    (
        "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
        "Correct Meteora program ID present"
    ),
    (
        "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR",
        "Exact public candidate present"
    ),
    (
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "Exact USDC mint present"
    ),
    (
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "Exact USDT mint present"
    ),
    (
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "Exact Token Program present"
    ),
    (
        "6RXrRoKVw31yhfiUqLLKiwHoWwuTRdoAYePCiuD1wDx5",
        "Exact funded USDC account present"
    ),
    (
        "provePublicKey",
        "Runtime PublicKey validation present"
    ),
    (
        "[METEORA_PROGRAM_ID_EXACT] PASS",
        "Exact Meteora program assertion present"
    ),
    (
        "getAccountInfo",
        "Funded account verification present"
    ),
    (
        "getAssociatedTokenAddressSync",
        "Canonical ATA derivation present"
    ),
    (
        "getBinArrayForSwap",
        "Official bin-array lookup present"
    ),
    (
        "swapQuote",
        "Official quote present"
    ),
    (
        "pool.swap",
        "Official swap builder present"
    ),
    (
        "414b3f4ceb5b5b88",
        "Swap2 discriminator present"
    ),
    (
        "swapInstruction.keys",
        "Swap2 account-meta binding present"
    ),
    (
        "CANONICAL_INPUT_META_COUNT",
        "Canonical input check present"
    ),
    (
        "FUNDED_INPUT_BINDING",
        "Funded input binding present"
    ),
    (
        "simulateTransaction",
        "Physical simulation present"
    ),
    (
        "sigVerify: false",
        "Signature verification disabled"
    ),
    (
        "requireAllSignatures: false",
        "Unsigned transaction serialization present"
    ),
    (
        "verifySignatures: false",
        "Unsigned signature verification disabled"
    ),
    (
        "[SIGNING] DISABLED",
        "Signing disabled"
    ),
    (
        "[BROADCAST] DISABLED",
        "Broadcast disabled"
    ),
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
]:
    assert forbidden not in text, (
        f"Forbidden operation present: {forbidden}"
    )
    print(
        f"[PASS] Forbidden operation absent: {forbidden}"
    )

assert "QSB_SOLANA_PRIVATE_KEY" not in text
print(
    "[PASS] Private-key environment reference absent"
)

assert (
    "LBUZKhRxPF3XUpBCj4YzTKgLccjZhTSDM9YuVaPwxo"
    not in text
)
print(
    "[PASS] Old invalid Meteora program ID absent"
)

assert (
    "ATokenGPvbdGVxr1b4h1mZ8GQfG2r7FhYbGfG6q3m6wG6q"
    not in text
)
print(
    "[PASS] Invalid ATA program constant absent"
)

print(
    "[BUILD TEST COMPLETE] MTR-013"
)
'''

harness_path = (
    HARNESS_DIR /
    "mtr_013_meteora_correct_program_id.mjs"
)

test_path = (
    ROOT /
    "test_mtr_013_meteora_correct_program_id.py"
)

harness_path.write_text(
    HARNESS,
    encoding="utf-8"
)

test_path.write_text(
    TEST,
    encoding="utf-8"
)

print("[BUILD] MTR-013 files written")
print(f"[HARNESS] {harness_path}")
print(f"[TEST] {test_path}")
print("[BUILD COMPLETE] MTR-013")