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

const connection = new Connection(RPC, "confirmed");

const candidate = new PublicKey(PUBLIC_CANDIDATE);
const lbPair = new PublicKey(LB_PAIR);
const meteoraProgram = new PublicKey(METEORA_PROGRAM);
const usdcMint = new PublicKey(USDC_MINT);
const usdtMint = new PublicKey(USDT_MINT);
const fundedUsdcAccount = new PublicKey(FUNDED_USDC_ACCOUNT);

function rpcBody(method, params) {
  return {
    jsonrpc: "2.0",
    id: 1,
    method,
    params,
  };
}

async function rawRpc(method, params) {
  const response = await fetch(RPC, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(rpcBody(method, params)),
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

function tokenAmountFromParsedAccount(row) {
  const parsed = row?.account?.data?.parsed;
  const info = parsed?.info;
  const tokenAmount = info?.tokenAmount;

  if (!tokenAmount) {
    return null;
  }

  return {
    mint: info.mint,
    owner: info.owner,
    raw: BigInt(tokenAmount.amount),
    decimals: tokenAmount.decimals,
  };
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
    throw new Error("Funded USDC token account does not exist");
  }

  const parsed = tokenAmountFromParsedAccount({
    account: result.value,
  });

  if (!parsed) {
    throw new Error("Funded account did not return parsed token data");
  }

  console.log(`[FUNDED_ACCOUNT] ${FUNDED_USDC_ACCOUNT}`);
  console.log(`[FUNDED_MINT] ${parsed.mint}`);
  console.log(`[FUNDED_OWNER] ${parsed.owner}`);
  console.log(`[FUNDED_RAW] ${parsed.raw.toString()}`);
  console.log(`[FUNDED_DECIMALS] ${parsed.decimals}`);
  console.log(
    `[ACCOUNT_PROGRAM_OWNER] ${result.value.owner}`
  );

  if (parsed.mint !== USDC_MINT) {
    throw new Error("Funded account mint mismatch");
  }

  if (parsed.owner !== PUBLIC_CANDIDATE) {
    throw new Error("Funded account owner mismatch");
  }

  if (result.value.owner !== TOKEN_PROGRAM) {
    throw new Error("Funded account is not owned by Token Program");
  }

  if (parsed.raw < INPUT_RAW_USDC) {
    throw new Error("Funded USDC account below required input");
  }

  console.log("[FUNDING_ACCOUNT_VERIFICATION] PASS");
}

async function verifyCanonicalAta() {
  const canonicalAta = getAssociatedTokenAddressSync(
    usdcMint,
    candidate,
    false,
    TOKEN_PROGRAM_ID,
    ASSOCIATED_TOKEN_PROGRAM_ID
  );

  console.log(`[CANONICAL_USDC_ATA] ${canonicalAta.toBase58()}`);
  console.log(
    `[FUNDED_ACCOUNT_IS_CANONICAL_ATA] ${
      canonicalAta.equals(fundedUsdcAccount) ? "YES" : "NO"
    }`
  );

  if (canonicalAta.equals(fundedUsdcAccount)) {
    throw new Error(
      "Expected public proof funding account to differ from canonical ATA"
    );
  }

  const ataInfo = await connection.getAccountInfo(
    canonicalAta,
    "confirmed"
  );

  if (ataInfo) {
    console.log("[CANONICAL_ATA_EXISTS] YES");
    console.log(`[CANONICAL_ATA_OWNER] ${ataInfo.owner.toBase58()}`);
  } else {
    console.log("[CANONICAL_ATA_EXISTS] NO");
  }

  return canonicalAta;
}

function instructionDataHex(ix) {
  return Buffer.from(ix.data).toString("hex");
}

function isSwap2Instruction(ix) {
  if (!ix?.programId?.equals(meteoraProgram)) {
    return false;
  }

  const data = instructionDataHex(ix);

  return data.startsWith(SWAP2_DISCRIMINATOR);
}

function printSwapAccounts(ix, canonicalAta) {
  console.log("[SWAP2_ACCOUNT_METAS_BEGIN]");

  ix.keys.forEach((meta, index) => {
    const address = meta.pubkey.toBase58();

    let role = "OTHER";

    if (meta.pubkey.equals(canonicalAta)) {
      role = "CANONICAL_USDC_ATA";
    }

    if (meta.pubkey.equals(fundedUsdcAccount)) {
      role = "FUNDED_USDC_ACCOUNT";
    }

    console.log(
      `[SWAP2_KEY] index=${index} address=${address} signer=${meta.isSigner} writable=${meta.isWritable} role=${role}`
    );
  });

  console.log("[SWAP2_ACCOUNT_METAS_END]");
}

async function main() {
  console.log("[MTR-011] START");
  console.log(`[RPC] ${RPC}`);
  console.log(`[LB_PAIR] ${LB_PAIR}`);
  console.log(`[METEORA_PROGRAM] ${METEORA_PROGRAM}`);
  console.log(`[PUBLIC_CANDIDATE] ${PUBLIC_CANDIDATE}`);
  console.log(`[USDC_MINT] ${USDC_MINT}`);
  console.log(`[USDT_MINT] ${USDT_MINT}`);
  console.log(`[TOKEN_PROGRAM] ${TOKEN_PROGRAM}`);
  console.log(`[FUNDED_USDC_ACCOUNT] ${FUNDED_USDC_ACCOUNT}`);
  console.log(`[INPUT_RAW_USDC] ${INPUT_RAW_USDC.toString()}`);

  await verifyFundedAccount();

  const canonicalAta = await verifyCanonicalAta();

  console.log("[SDK] creating official Meteora DLMM pool");

  const pool = await DLMM.create(
    connection,
    lbPair
  );

  console.log(`[POOL_PUBKEY] ${pool.pubkey.toBase58()}`);
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
      "Pool token binding does not match USDC/USDT target"
    );
  }

  console.log("[POOL_TOKEN_BINDING] PASS");

  console.log("[SDK] refreshing live pool state");

  await pool.refetchStates();

  const swapForY = true;

  console.log(
    `[SWAP_DIRECTION] USDC_X_TO_USDT_Y=${swapForY}`
  );

  console.log("[SDK] requesting live bin arrays");

  const binArrays = await pool.getBinArrayForSwap(
    swapForY,
    4
  );

  console.log(
    `[BIN_ARRAY_COUNT] ${binArrays.length}`
  );

  if (!binArrays.length) {
    throw new Error("No live bin arrays returned");
  }

  console.log("[SDK] generating exact-in quote");

  const quote = await pool.swapQuote(
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
    `[QUOTE_FEE] ${quote.fee?.toString?.() ?? "N/A"}`
  );
  console.log(
    `[QUOTE_PROTOCOL_FEE] ${quote.protocolFee?.toString?.() ?? "N/A"}`
  );
  console.log("[SDK_QUOTE] PASS");

  console.log(
    "[SDK] constructing official pool.swap transaction"
  );

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
      `Expected legacy Transaction from official pool.swap; received ${tx?.constructor?.name ?? typeof tx}`
    );
  }

  console.log("[SDK_SWAP_TRANSACTION] CONSTRUCTED");
  console.log(
    `[SDK_INSTRUCTION_COUNT] ${tx.instructions.length}`
  );

  const swapIndex = tx.instructions.findIndex(
    isSwap2Instruction
  );

  if (swapIndex < 0) {
    throw new Error(
      "Official SDK transaction does not contain Meteora Swap2"
    );
  }

  const swapInstruction = tx.instructions[swapIndex];

  console.log(`[SWAP2_INSTRUCTION_INDEX] ${swapIndex}`);
  console.log(
    `[SWAP2_DISCRIMINATOR] ${instructionDataHex(swapInstruction).slice(0, 16)}`
  );

  if (
    !instructionDataHex(swapInstruction).startsWith(
      SWAP2_DISCRIMINATOR
    )
  ) {
    throw new Error("Swap2 discriminator mismatch");
  }

  printSwapAccounts(
    swapInstruction,
    canonicalAta
  );

  const canonicalAtaIndexes = [];

  swapInstruction.keys.forEach((meta, index) => {
    if (meta.pubkey.equals(canonicalAta)) {
      canonicalAtaIndexes.push(index);
    }
  });

  console.log(
    `[CANONICAL_INPUT_META_COUNT] ${canonicalAtaIndexes.length}`
  );

  if (canonicalAtaIndexes.length !== 1) {
    throw new Error(
      `Expected exactly one canonical input ATA in Swap2; found ${canonicalAtaIndexes.length}`
    );
  }

  const inputIndex = canonicalAtaIndexes[0];

  console.log(
    `[FUNDED_INPUT_BINDING_INDEX] ${inputIndex}`
  );

  const originalMeta =
    swapInstruction.keys[inputIndex];

  if (!originalMeta.isWritable) {
    throw new Error(
      "Canonical input token account meta is not writable"
    );
  }

  swapInstruction.keys[inputIndex] = {
    pubkey: fundedUsdcAccount,
    isSigner: originalMeta.isSigner,
    isWritable: originalMeta.isWritable,
  };

  const reboundMeta =
    swapInstruction.keys[inputIndex];

  console.log(
    `[ORIGINAL_INPUT_ACCOUNT] ${canonicalAta.toBase58()}`
  );
  console.log(
    `[REBOUND_INPUT_ACCOUNT] ${reboundMeta.pubkey.toBase58()}`
  );

  if (
    !reboundMeta.pubkey.equals(fundedUsdcAccount)
  ) {
    throw new Error(
      "Funded input account replacement failed"
    );
  }

  if (!reboundMeta.isWritable) {
    throw new Error(
      "Funded input account lost writable flag"
    );
  }

  console.log("[FUNDED_INPUT_BINDING] PASS");

  const { blockhash } =
    await connection.getLatestBlockhash("confirmed");

  tx.feePayer = candidate;
  tx.recentBlockhash = blockhash;

  const serializedUnsigned = tx.serialize({
    requireAllSignatures: false,
    verifySignatures: false,
  });

  console.log(
    `[UNSIGNED_TX_BYTES] ${serializedUnsigned.length}`
  );
  console.log(
    `[SIGNATURES_PRESENT] ${tx.signatures.length}`
  );
  console.log("[SIGNING] DISABLED");
  console.log("[BROADCAST] DISABLED");

  console.log(
    "[SIMULATION] calling Solana simulateTransaction"
  );

  const simulation = await connection.simulateTransaction(
    tx,
    {
      sigVerify: false,
      replaceRecentBlockhash: true,
      commitment: "confirmed",
    }
  );

  console.log(
    `[SIMULATION_UNITS_CONSUMED] ${simulation.value.unitsConsumed ?? "N/A"}`
  );

  if (simulation.value.logs) {
    console.log("[SIMULATION_LOGS_BEGIN]");

    for (const line of simulation.value.logs) {
      console.log(line);
    }

    console.log("[SIMULATION_LOGS_END]");
  }

  if (simulation.value.err) {
    console.log(
      `[SIMULATION_RESULT] FAIL`
    );
    console.log(
      `[SIMULATION_ERROR] ${JSON.stringify(simulation.value.err)}`
    );

    throw new Error(
      "MTR-011 physical simulation failed"
    );
  }

  console.log("[SIMULATION_RESULT] PASS");
  console.log("[MTR-011] OFFICIAL METEORA SWAP2 WITH VERIFIED FUNDED INPUT SIMULATED SUCCESSFULLY.");
  console.log("[MTR-011] NO SIGNING.");
  console.log("[MTR-011] NO SENDING.");
  console.log("[MTR-011] NO CANONICAL EXECUTOR.");
}

main().catch((error) => {
  console.error(
    `[MTR-011] FAIL: ${error?.stack ?? error}`
  );
  process.exitCode = 1;
});
