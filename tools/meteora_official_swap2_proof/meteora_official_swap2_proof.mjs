
import DLMM from "@meteora-ag/dlmm";
import { BN } from "@coral-xyz/anchor";
import {
  Connection,
  PublicKey,
  Transaction,
} from "@solana/web3.js";

const RPC_URL =
  process.env.METEORA_PROOF_RPC_URL ||
  process.env.QSB_SOLANA_RPC_URL ||
  "https://api.mainnet-beta.solana.com";

const LB_PAIR = new PublicKey(
  process.env.METEORA_PROOF_LB_PAIR ||
  "ARwi1S4DaiTG5DX7S4M4ZsrXqpMD1MrTmbu9ue2tpmEq"
);

/*
  Public Circle wallet used only as a simulation owner.
  NO PRIVATE KEY IS USED.
*/
const USER = new PublicKey(
  process.env.METEORA_PROOF_USER ||
  "7VHUFJHWu2CuExkJcJrzhQPJ2oygupTWkL2A2For4BmE"
);

const USDC = new PublicKey(
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
);

const INPUT_RAW = new BN(
  process.env.METEORA_PROOF_INPUT_RAW || "100000000"
);

const SLIPPAGE_BPS = new BN(
  process.env.METEORA_PROOF_SLIPPAGE_BPS || "50"
);

const DLMM_PROGRAM_ID = new PublicKey(
  "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
);


function dumpInstruction(ix, index) {
  console.log(
    `\n[IX ${index}] program=${ix.programId.toBase58()}`
  );

  console.log(
    `  data_len=${ix.data.length} data_hex=${
      Buffer.from(ix.data).toString("hex")
    }`
  );

  console.log(
    `  accounts=${ix.keys.length}`
  );

  ix.keys.forEach((k, i) => {
    console.log(
      `    [${i}] ${k.pubkey.toBase58()} ` +
      `signer=${k.isSigner} writable=${k.isWritable}`
    );
  });
}


async function main() {
  console.log(
    "[METEORA-OFFICIAL-SWAP2-PROOF] START"
  );

  console.log(`[RPC] ${RPC_URL}`);
  console.log(`[LB_PAIR] ${LB_PAIR.toBase58()}`);
  console.log(`[USER] ${USER.toBase58()}`);
  console.log(
    `[INPUT_RAW_USDC] ${INPUT_RAW.toString()}`
  );
  console.log(
    `[SLIPPAGE_BPS] ${SLIPPAGE_BPS.toString()}`
  );

  const connection = new Connection(
    RPC_URL,
    "confirmed"
  );

  const userAccount =
    await connection.getAccountInfo(
      USER,
      "confirmed"
    );

  if (!userAccount) {
    throw new Error(
      "PROOF_USER_ACCOUNT_NOT_FOUND"
    );
  }

  const userLamports =
    await connection.getBalance(
      USER,
      "confirmed"
    );

  console.log(
    `[USER_SOL_LAMPORTS] ${userLamports}`
  );

  /*
    Official Meteora SDK.
  */
  const pool = await DLMM.create(
    connection,
    LB_PAIR,
    {
      cluster: "mainnet-beta",
    }
  );

  /*
    Fresh pool state.
  */
  await pool.refetchStates();

  const tokenX =
    pool.tokenX.publicKey;

  const tokenY =
    pool.tokenY.publicKey;

  console.log(
    `[TOKEN_X] ${tokenX.toBase58()}`
  );

  console.log(
    `[TOKEN_Y] ${tokenY.toBase58()}`
  );

  let swapForY;

  if (tokenX.equals(USDC)) {
    swapForY = true;
  } else if (tokenY.equals(USDC)) {
    swapForY = false;
  } else {
    throw new Error(
      "PROOF_POOL_IS_NOT_USDC_PAIR"
    );
  }

  const outToken =
    swapForY ? tokenY : tokenX;

  console.log(
    `[INPUT_MINT] ${USDC.toBase58()}`
  );

  console.log(
    `[OUTPUT_MINT] ${outToken.toBase58()}`
  );

  console.log(
    `[SWAP_FOR_Y] ${swapForY}`
  );

  /*
    Official SDK bin-array selection.
  */
  const binArrays =
    await pool.getBinArrayForSwap(
      swapForY,
      4
    );

  console.log(
    `[BIN_ARRAY_COUNT] ${binArrays.length}`
  );

  for (const b of binArrays) {
    console.log(
      `[BIN_ARRAY] ${b.publicKey.toBase58()}`
    );
  }

  if (binArrays.length === 0) {
    throw new Error(
      "NO_BIN_ARRAYS_RETURNED"
    );
  }

  /*
    Official SDK quote.
  */
  const quote =
    pool.swapQuote(
      INPUT_RAW,
      swapForY,
      SLIPPAGE_BPS,
      binArrays,
      false
    );

  console.log(
    `[QUOTE_CONSUMED_IN] ${
      quote.consumedInAmount.toString()
    }`
  );

  console.log(
    `[QUOTE_OUT] ${
      quote.outAmount.toString()
    }`
  );

  console.log(
    `[QUOTE_MIN_OUT] ${
      quote.minOutAmount.toString()
    }`
  );

  console.log(
    `[QUOTE_FEE] ${
      quote.fee.toString()
    }`
  );

  console.log(
    `[QUOTE_PRICE_IMPACT] ${
      quote.priceImpact.toString()
    }`
  );

  console.log(
    `[QUOTE_BIN_ARRAYS] ${
      quote.binArraysPubkey
        .map((x) => x.toBase58())
        .join(",")
    }`
  );

  /*
    CRITICAL:
    Let Meteora's own SDK construct Swap2.
  */
  const tx = await pool.swap({
    inToken: USDC,
    outToken,
    inAmount: quote.consumedInAmount,
    minOutAmount: quote.minOutAmount,
    lbPair: pool.pubkey,
    user: USER,
    binArraysPubkey:
      quote.binArraysPubkey,
  });

  if (!(tx instanceof Transaction)) {
    throw new Error(
      `UNEXPECTED_TRANSACTION_TYPE:${
        tx?.constructor?.name ||
        typeof tx
      }`
    );
  }

  console.log(
    `\n[TX_INSTRUCTION_COUNT] ${
      tx.instructions.length
    }`
  );

  tx.instructions.forEach(
    dumpInstruction
  );

  const dlmmInstructions =
    tx.instructions.filter(
      (ix) =>
        ix.programId.equals(
          DLMM_PROGRAM_ID
        )
    );

  console.log(
    `\n[DLMM_INSTRUCTION_COUNT] ${
      dlmmInstructions.length
    }`
  );

  if (dlmmInstructions.length !== 1) {
    throw new Error(
      `EXPECTED_ONE_DLMM_INSTRUCTION_GOT_${
        dlmmInstructions.length
      }`
    );
  }

  const swapIx =
    dlmmInstructions[0];

  console.log(
    `[DLMM_DISCRIMINATOR] ${
      Buffer.from(swapIx.data)
        .subarray(0, 8)
        .toString("hex")
    }`
  );

  console.log(
    `[DLMM_ACCOUNT_COUNT] ${
      swapIx.keys.length
    }`
  );

  console.log(
    `[DLMM_DATA_LEN] ${
      swapIx.data.length
    }`
  );

  /*
    Simulation only.
    No signing.
    No sending.
  */
  const latest =
    await connection.getLatestBlockhash(
      "confirmed"
    );

  tx.feePayer = USER;
  tx.recentBlockhash =
    latest.blockhash;

  const serialized =
    tx.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

  console.log(
    `[SERIALIZED_LEN] ${
      serialized.length
    }`
  );

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
    "\n[SIM_LOGS]"
  );

  if (simulation.value.logs) {
    for (
      const line of
      simulation.value.logs
    ) {
      console.log(line);
    }
  }

  console.log(
    `\n[SIM_ERR] ${
      JSON.stringify(
        simulation.value.err
      )
    }`
  );

  if (
    simulation.value.err !== null
  ) {
    throw new Error(
      "METEORA_OFFICIAL_SWAP2_SIMULATION_FAILED"
    );
  }

  console.log(
    "\n[PROOF] STANDALONE_METEORA_PREFLIGHT_PASS"
  );

  console.log(
    "[PROOF] OFFICIAL_SDK_SWAP2_ACCEPTED_BY_MAINNET_SIMULATION"
  );

  console.log(
    "[PROOF] NO_PRIVATE_KEY_USED"
  );

  console.log(
    "[PROOF] NO_LIVE_SEND"
  );
}


main().catch((err) => {
  console.error(
    `[FAIL] ${err?.stack || err}`
  );

  process.exit(1);
});
