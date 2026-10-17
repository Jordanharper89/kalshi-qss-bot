import { Connection, PublicKey, Transaction } from "@solana/web3.js";
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
  "LBUZKhRxPF3XUpBCj4YzTKgLccjZhTSDM9YuVaPwxo";

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

  let key;

  try {
    key = new PublicKey(value);
  } catch (error) {
    console.error(
      `[KEY_CHECK_FAIL] ${label}: ${error?.message ?? error}`
    );
    throw new Error(
      `${label} is not accepted by @solana/web3.js: ${value}`
    );
  }

  const normalized = key.toBase58();

  console.log(`[KEY_NORMALIZED] ${normalized}`);

  if (normalized !== value) {
    throw new Error(
      `${label} normalization mismatch: ${normalized}`
    );
  }

  console.log(`[KEY_CHECK_PASS] ${label}`);
  return key;
}

console.log("[MTR-012] START");
console.log(`[RPC] ${RPC}`);

const lbPair = provePublicKey("LB_PAIR", LB_PAIR);
const meteoraProgram = provePublicKey(
  "METEORA_PROGRAM",
  METEORA_PROGRAM
);
const candidate = provePublicKey(
  "PUBLIC_CANDIDATE",
  PUBLIC_CANDIDATE
);
const usdcMint = provePublicKey(
  "USDC_MINT",
  USDC_MINT
);
const usdtMint = provePublicKey(
  "USDT_MINT",
  USDT_MINT
);
const tokenProgram = provePublicKey(
  "TOKEN_PROGRAM",
  TOKEN_PROGRAM
);
const fundedUsdcAccount = provePublicKey(
  "FUNDED_USDC_ACCOUNT",
  FUNDED_USDC_ACCOUNT
);

if (!tokenProgram.equals(TOKEN_PROGRAM_ID)) {
  throw new Error(
    "Token program constant does not match @solana/spl-token"
  );
}

console.log("[TOKEN_PROGRAM_BINDING] PASS");

const connection = new Connection(RPC, "confirmed");

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
    throw new Error(`RPC HTTP ${response.status}`);
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
  console.log("[RPC] verifying exact funded USDC token account");

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
      "Verified funded USDC token account does not exist"
    );
  }

  const parsed = result.value?.data?.parsed?.info;

  if (!parsed?.tokenAmount) {
    throw new Error(
      "Funded account did not return parsed token amount"
    );
  }

  const rawAmount = BigInt(
    parsed.tokenAmount.amount
  );

  console.log(
    `[FUNDED_USDC_ACCOUNT] ${FUNDED_USDC_ACCOUNT}`
  );
  console.log(
    `[FUNDED_USDC_MINT] ${parsed.mint}`
  );
  console.log(
    `[FUNDED_USDC_OWNER] ${parsed.owner}`
  );
  console.log(
    `[FUNDED_USDC_RAW] ${rawAmount.toString()}`
  );
  console.log(
    `[FUNDED_USDC_DECIMALS] ${parsed.tokenAmount.decimals}`
  );
  console.log(
    `[TOKEN_ACCOUNT_PROGRAM_OWNER] ${result.value.owner}`
  );

  if (parsed.mint !== USDC_MINT) {
    throw new Error(
      "Funded account mint mismatch"
    );
  }

  if (parsed.owner !== PUBLIC_CANDIDATE) {
    throw new Error(
      "Funded account owner mismatch"
    );
  }

  if (result.value.owner !== TOKEN_PROGRAM) {
    throw new Error(
      "Funded account Token Program owner mismatch"
    );
  }

  if (rawAmount < INPUT_RAW_USDC) {
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

  if (canonicalAta.equals(fundedUsdcAccount)) {
    throw new Error(
      "Funded proof account unexpectedly equals canonical ATA"
    );
  }

  console.log(
    "[FUNDED_ACCOUNT_IS_CANONICAL_ATA] NO"
  );

  console.log(
    "[SDK] creating official Meteora DLMM pool"
  );

  const pool = await DLMM.create(
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

  console.log("[POOL_TOKEN_BINDING] PASS");

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

  console.log("[SDK_QUOTE] PASS");

  const tx = await pool.swap({
    inToken: pool.tokenX.publicKey,
    outToken: pool.tokenY.publicKey,
    inAmount: quote.consumedInAmount,
    lbPair: pool.pubkey,
    user: candidate,
    minOutAmount: quote.minOutAmount,
    binArraysPubkey: quote.binArraysPubkey,
  });

  if (!(tx instanceof Transaction)) {
    throw new Error(
      "Official pool.swap did not return Transaction"
    );
  }

  const swapInstruction =
    tx.instructions.find((ix) =>
      ix.programId.equals(meteoraProgram) &&
      Buffer.from(ix.data)
        .toString("hex")
        .startsWith(SWAP2_DISCRIMINATOR)
    );

  if (!swapInstruction) {
    throw new Error(
      "Official Swap2 instruction not found"
    );
  }

  console.log(
    "[SWAP2_INSTRUCTION] FOUND"
  );

  const canonicalIndexes = [];

  swapInstruction.keys.forEach(
    (meta, index) => {
      if (meta.pubkey.equals(canonicalAta)) {
        canonicalIndexes.push(index);
      }
    }
  );

  console.log(
    `[CANONICAL_INPUT_META_COUNT] ${canonicalIndexes.length}`
  );

  if (canonicalIndexes.length !== 1) {
    throw new Error(
      `Expected one canonical input ATA in Swap2; found ${canonicalIndexes.length}`
    );
  }

  const inputIndex =
    canonicalIndexes[0];

  const original =
    swapInstruction.keys[inputIndex];

  if (!original.isWritable) {
    throw new Error(
      "Canonical input account is not writable"
    );
  }

  console.log(
    `[ORIGINAL_INPUT_ACCOUNT] ${original.pubkey.toBase58()}`
  );

  swapInstruction.keys[inputIndex] = {
    pubkey: fundedUsdcAccount,
    isSigner: original.isSigner,
    isWritable: original.isWritable,
  };

  console.log(
    `[REBOUND_INPUT_ACCOUNT] ${swapInstruction.keys[inputIndex].pubkey.toBase58()}`
  );

  if (
    !swapInstruction.keys[inputIndex]
      .pubkey
      .equals(fundedUsdcAccount)
  ) {
    throw new Error(
      "Funded input account rebinding failed"
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
  tx.recentBlockhash = blockhash;

  const unsigned =
    tx.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

  console.log(
    `[UNSIGNED_TX_BYTES] ${unsigned.length}`
  );

  console.log(
    `[INSTRUCTION_COUNT] ${tx.instructions.length}`
  );

  console.log("[SIGNING] DISABLED");
  console.log("[BROADCAST] DISABLED");

  const simulation =
    await connection.simulateTransaction(
      tx,
      {
        sigVerify: false,
        replaceRecentBlockhash: true,
        commitment: "confirmed",
      }
    );

  console.log(
    `[SIMULATION_UNITS_CONSUMED] ${
      simulation.value.unitsConsumed ?? "N/A"
    }`
  );

  if (simulation.value.logs) {
    console.log(
      "[SIMULATION_LOGS_BEGIN]"
    );

    for (const line of simulation.value.logs) {
      console.log(line);
    }

    console.log(
      "[SIMULATION_LOGS_END]"
    );
  }

  if (simulation.value.err) {
    console.log(
      "[SIMULATION_RESULT] FAIL"
    );

    console.log(
      `[SIMULATION_ERROR] ${JSON.stringify(
        simulation.value.err
      )}`
    );

    throw new Error(
      "MTR-012 physical simulation failed"
    );
  }

  console.log(
    "[SIMULATION_RESULT] PASS"
  );

  console.log(
    "[MTR-012] OFFICIAL METEORA SWAP2 WITH VERIFIED FUNDED INPUT SIMULATED SUCCESSFULLY."
  );

  console.log(
    "[MTR-012] NO SIGNING."
  );

  console.log(
    "[MTR-012] NO SENDING."
  );

  console.log(
    "[MTR-012] NO CANONICAL EXECUTOR."
  );
}

main().catch((error) => {
  console.error(
    `[MTR-012] FAIL: ${error?.stack ?? error}`
  );
  process.exitCode = 1;
});
