import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path("tools") / "meteora_official_swap2_proof"
ROOT.mkdir(parents=True, exist_ok=True)

PACKAGE_JSON = {
    "name": "meteora-official-swap2-proof",
    "private": True,
    "type": "module",
    "dependencies": {
        "@coral-xyz/anchor": "0.32.1",
        "@meteora-ag/dlmm": "1.9.14",
        "@solana/web3.js": "1.99.0",
    },
}


PROOF_JS = r"""
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
"""


TEST_PY = r"""
from pathlib import Path
import subprocess
import sys


ROOT = (
    Path("tools")
    / "meteora_official_swap2_proof"
)

PROOF = (
    ROOT
    / "meteora_official_swap2_proof.mjs"
)

PACKAGE = ROOT / "package.json"


if not PROOF.exists():
    print("[FAIL] proof harness missing")
    sys.exit(1)

if not PACKAGE.exists():
    print("[FAIL] package.json missing")
    sys.exit(1)


source = PROOF.read_text(
    encoding="utf-8"
)


forbidden = (
    "QSB_SOLANA_PRIVATE_KEY",
    "Keypair.fromSecretKey",
    "sendAndConfirmTransaction",
)


for item in forbidden:
    if item in source:
        print(
            f"[FAIL] forbidden live/private-key path: {item}"
        )
        sys.exit(1)


print(
    "[PASS] isolated proof harness present"
)

print(
    "[PASS] no private-key path"
)

print(
    "[PASS] no live-send path"
)

print(
    "[RUN] official Meteora SDK simulation"
)


result = subprocess.run(
    [
        "node",
        str(PROOF),
    ],
    check=False,
)


if result.returncode != 0:
    print(
        "[FAIL] official Meteora Swap2 simulation failed"
    )
    sys.exit(
        result.returncode
    )


print(
    "[PASS] official Meteora Swap2 standalone simulation"
)
"""


def install_node_dependencies():
    npm = shutil.which("npm.cmd")

    if not npm:
        raise RuntimeError(
            "NPM_CMD_NOT_FOUND"
        )

    print(
        f"[BUILD] npm={npm}"
    )

    subprocess.run(
        [
            npm,
            "install",
            "--no-audit",
            "--no-fund",
        ],
        cwd=str(ROOT),
        check=True,
    )


def apply_upstream_esm_compatibility_fix():
    """
    Exact compatibility fix corresponding to Meteora
    upstream PR #296.

    Published 1.9.14 emits:

        @coral-xyz/anchor/dist/cjs/utils/bytes

    Node ESM rejects that directory import.

    Meteora's upstream fix changes it to:

        @coral-xyz/anchor/dist/cjs/utils/bytes/index.js

    We only change this exact import string.
    No Swap2 logic is modified.
    """

    target = (
        ROOT
        / "node_modules"
        / "@meteora-ag"
        / "dlmm"
        / "dist"
        / "index.mjs"
    )

    if not target.exists():
        raise RuntimeError(
            f"METEORA_SDK_BUNDLE_NOT_FOUND:{target}"
        )

    source = target.read_text(
        encoding="utf-8"
    )

    old = (
        '@coral-xyz/anchor/dist/cjs/utils/bytes";'
    )

    new = (
        '@coral-xyz/anchor/dist/cjs/utils/bytes/index.js";'
    )

    old_count = source.count(old)

    if old_count == 0:
        already_fixed = (
            '@coral-xyz/anchor/dist/cjs/utils/bytes/index.js";'
        )

        if already_fixed in source:
            print(
                "[PASS] Meteora ESM import already fixed"
            )
            return

        raise RuntimeError(
            "METEORA_ESM_IMPORT_SHAPE_UNEXPECTED"
        )

    if old_count != 1:
        raise RuntimeError(
            f"METEORA_ESM_IMPORT_EXPECTED_ONE_GOT_{old_count}"
        )

    source = source.replace(
        old,
        new,
        1,
    )

    target.write_text(
        source,
        encoding="utf-8"
    )

    verify = target.read_text(
        encoding="utf-8"
    )

    if new not in verify:
        raise RuntimeError(
            "METEORA_ESM_COMPATIBILITY_FIX_NOT_VERIFIED"
        )

    print(
        "[PASS] Meteora upstream Node-ESM compatibility fix applied"
    )

    print(
        "[PASS] Swap2 SDK logic untouched"
    )


def main():
    (ROOT / "package.json").write_text(
        json.dumps(
            PACKAGE_JSON,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    (
        ROOT
        / "meteora_official_swap2_proof.mjs"
    ).write_text(
        PROOF_JS,
        encoding="utf-8",
    )

    Path(
        "test_meteora_official_swap2_proof.py"
    ).write_text(
        TEST_PY,
        encoding="utf-8",
    )

    print(
        "[BUILD] Meteora official Swap2 proof harness installed"
    )

    print(
        f"[BUILD] {ROOT / 'package.json'}"
    )

    print(
        f"[BUILD] {ROOT / 'meteora_official_swap2_proof.mjs'}"
    )

    print(
        "[BUILD] test_meteora_official_swap2_proof.py"
    )

    install_node_dependencies()

    apply_upstream_esm_compatibility_fix()

    print(
        "[BUILD] dependency installation and compatibility verification complete"
    )


if __name__ == "__main__":
    main()