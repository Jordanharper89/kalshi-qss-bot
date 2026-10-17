from pathlib import Path

HARNESS = r'''import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

function resolvePackage(packageName, searchPaths) {
  const attempts = [];

  for (const searchPath of searchPaths) {
    try {
      const resolved =
        require.resolve(
          packageName,
          {
            paths: [searchPath],
          }
        );

      console.log(
        `[DEPENDENCY_RESOLVED] ${packageName} -> ${resolved}`
      );

      return require(resolved);
    } catch (error) {
      attempts.push(
        `${searchPath}: ${error.message}`
      );
    }
  }

  throw new Error(
    `Unable to resolve ${packageName} through installed dependency tree:\n` +
    attempts.join("\n")
  );
}

function getPackageSearchRoots(packageName) {
  const entry =
    require.resolve(
      packageName
    );

  const roots = [];

  let current = entry;

  for (let i = 0; i < 16; i++) {
    const slash =
      Math.max(
        current.lastIndexOf("\\"),
        current.lastIndexOf("/")
      );

    if (slash <= 0) {
      break;
    }

    current =
      current.substring(
        0,
        slash
      );

    roots.push(current);
  }

  return roots;
}

const pumpRoots =
  getPackageSearchRoots(
    "@pump-fun/pump-swap-sdk"
  );

console.log(
  `[PUMPSWAP_ROOT_SEARCH_PATHS] ${pumpRoots.length}`
);

const web3Module =
  resolvePackage(
    "@solana/web3.js",
    pumpRoots
  );

const splTokenModule =
  resolvePackage(
    "@solana/spl-token",
    pumpRoots
  );

const pumpModule =
  resolvePackage(
    "@pump-fun/pump-swap-sdk",
    pumpRoots
  );

const bnModule =
  resolvePackage(
    "bn.js",
    pumpRoots
  );

const {
  Connection,
  PublicKey,
  Transaction,
} = web3Module;

const {
  NATIVE_MINT,
} = splTokenModule;

const {
  OnlinePumpAmmSdk,
  PUMP_AMM_SDK,
} = pumpModule;

const BN =
  bnModule.default ?? bnModule;

const RPC_URL =
  "https://api.mainnet-beta.solana.com";

const PUBLIC_CANDIDATE =
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR";

const PUMP_AMM_PROGRAM =
  "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA";

const INPUT_LAMPORTS =
  new BN("10000000");

const SLIPPAGE_PERCENT = 5;

const COINS_ENDPOINT =
  "https://frontend-api-v3.pump.fun/coins?offset=0&limit=100&sort=last_trade_timestamp&includeNsfw=false&order=DESC";

function assertKey(
  label,
  value
) {
  console.log(
    `[KEY_CHECK_BEGIN] ${label}`
  );

  console.log(
    `[KEY_VALUE] ${value}`
  );

  console.log(
    `[KEY_LENGTH] ${value.length}`
  );

  const pk =
    new PublicKey(value);

  const normalized =
    pk.toBase58();

  console.log(
    `[KEY_NORMALIZED] ${normalized}`
  );

  if (
    normalized !== value
  ) {
    throw new Error(
      `${label} normalization mismatch`
    );
  }

  console.log(
    `[KEY_CHECK_PASS] ${label}`
  );

  return pk;
}

async function discoverGraduatedPool() {
  console.log(
    "[DISCOVERY] querying current Pump.fun coin universe"
  );

  const response =
    await fetch(
      COINS_ENDPOINT
    );

  if (!response.ok) {
    throw new Error(
      `Pump discovery HTTP ${response.status} ${response.statusText}`
    );
  }

  const payload =
    await response.json();

  const coins =
    Array.isArray(payload)
      ? payload
      : Array.isArray(payload?.coins)
        ? payload.coins
        : [];

  console.log(
    `[DISCOVERY_COIN_COUNT] ${coins.length}`
  );

  for (
    const coin
    of coins
  ) {
    if (!coin) {
      continue;
    }

    if (
      coin.complete !== true
    ) {
      continue;
    }

    const poolValue =
      coin.pump_swap_pool;

    const mintValue =
      coin.mint;

    if (
      !poolValue ||
      !mintValue
    ) {
      continue;
    }

    try {
      const pool =
        new PublicKey(
          poolValue
        );

      const mint =
        new PublicKey(
          mintValue
        );

      console.log(
        "[DISCOVERY] graduated PumpSwap candidate found"
      );

      console.log(
        `[DISCOVERY_MINT] ${mint.toBase58()}`
      );

      console.log(
        `[DISCOVERY_POOL] ${pool.toBase58()}`
      );

      console.log(
        `[DISCOVERY_SYMBOL] ${coin.symbol ?? "UNKNOWN"}`
      );

      return {
        mint,
        pool,
        symbol:
          coin.symbol ?? "UNKNOWN",
      };
    } catch {
      continue;
    }
  }

  throw new Error(
    "No usable graduated PumpSwap pool found in discovery window"
  );
}

async function main() {
  console.log(
    "[MTR-019] START"
  );

  console.log(
    `[RPC] ${RPC_URL}`
  );

  console.log(
    "[DEPENDENCY_RESOLUTION] PASS"
  );

  const connection =
    new Connection(
      RPC_URL,
      "confirmed"
    );

  const candidate =
    assertKey(
      "PUBLIC_CANDIDATE",
      PUBLIC_CANDIDATE
    );

  const pumpProgram =
    assertKey(
      "PUMP_AMM_PROGRAM",
      PUMP_AMM_PROGRAM
    );

  assertKey(
    "NATIVE_MINT",
    NATIVE_MINT.toBase58()
  );

  console.log(
    "[BN_RESOLUTION] PASS"
  );

  console.log(
    `[BN_INPUT] ${INPUT_LAMPORTS.toString()}`
  );

  console.log(
    `[SLIPPAGE_PERCENT] ${SLIPPAGE_PERCENT}`
  );

  const balance =
    await connection.getBalance(
      candidate,
      "confirmed"
    );

  console.log(
    `[CANDIDATE_SOL_LAMPORTS] ${balance}`
  );

  console.log(
    `[CANDIDATE_SOL] ${(balance / 1_000_000_000).toFixed(9)}`
  );

  if (
    balance <
    Number(
      INPUT_LAMPORTS.toString()
    )
  ) {
    throw new Error(
      "Candidate does not have enough SOL for 0.010 SOL input"
    );
  }

  console.log(
    "[CANDIDATE_SOL_FUNDING] PASS"
  );

  const discovered =
    await discoverGraduatedPool();

  console.log(
    `[DISCOVERED_POOL] ${discovered.pool.toBase58()}`
  );

  console.log(
    `[DISCOVERED_MINT] ${discovered.mint.toBase58()}`
  );

  const poolAccount =
    await connection.getAccountInfo(
      discovered.pool,
      "confirmed"
    );

  if (!poolAccount) {
    throw new Error(
      "PumpSwap pool account missing on-chain"
    );
  }

  if (
    !poolAccount.owner.equals(
      pumpProgram
    )
  ) {
    throw new Error(
      `PumpSwap pool owner mismatch: ${poolAccount.owner.toBase58()}`
    );
  }

  console.log(
    "[POOL_PROGRAM_OWNER] PASS"
  );

  console.log(
    "[SDK] creating OnlinePumpAmmSdk"
  );

  const onlineAmm =
    new OnlinePumpAmmSdk(
      connection
    );

  console.log(
    "[SDK] loading live PumpSwap pool state"
  );

  const swapState =
    await onlineAmm.swapSolanaState(
      discovered.pool,
      candidate
    );

  console.log(
    "[PUMP_POOL_STATE] PASS"
  );

  console.log(
    `[STATE_POOL] ${swapState.poolKey.toBase58()}`
  );

  console.log(
    `[STATE_USER] ${swapState.user.toBase58()}`
  );

  if (
    !swapState.user.equals(
      candidate
    )
  ) {
    throw new Error(
      "PumpSwap SDK state user mismatch"
    );
  }

  console.log(
    "[STATE_USER_BINDING] PASS"
  );

  console.log(
    "[SDK] generating exact-input PumpSwap quote"
  );

  const instructions =
    await PUMP_AMM_SDK.buyQuoteInput(
      swapState,
      INPUT_LAMPORTS,
      SLIPPAGE_PERCENT
    );

  if (
    !Array.isArray(
      instructions
    )
  ) {
    throw new Error(
      "PumpSwap SDK did not return instruction array"
    );
  }

  if (
    instructions.length === 0
  ) {
    throw new Error(
      "PumpSwap SDK returned zero instructions"
    );
  }

  console.log(
    `[SDK_INSTRUCTION_COUNT] ${instructions.length}`
  );

  console.log(
    "[SDK_QUOTE] PASS"
  );

  const transaction =
    new Transaction();

  for (
    const instruction
    of instructions
  ) {
    transaction.add(
      instruction
    );
  }

  transaction.feePayer =
    candidate;

  const latest =
    await connection.getLatestBlockhash(
      "confirmed"
    );

  transaction.recentBlockhash =
    latest.blockhash;

  const unsignedBytes =
    transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

  console.log(
    `[UNSIGNED_TX_BYTES] ${unsignedBytes.length}`
  );

  console.log(
    `[INSTRUCTION_COUNT] ${transaction.instructions.length}`
  );

  if (
    unsignedBytes.length === 0
  ) {
    throw new Error(
      "Unsigned transaction serialized to zero bytes"
    );
  }

  console.log(
    "[SDK_TRANSACTION] CONSTRUCTED"
  );

  console.log(
    "[SIGNING] DISABLED"
  );

  console.log(
    "[BROADCAST] DISABLED"
  );

  console.log(
    "[PRIVATE_KEY] NOT USED"
  );

  const encoded =
    unsignedBytes.toString(
      "base64"
    );

  console.log(
    "[RAW_RPC_SIMULATION] method=simulateTransaction"
  );

  console.log(
    "[RAW_RPC_ENCODING] base64"
  );

  console.log(
    "[RAW_RPC_SIG_VERIFY] false"
  );

  console.log(
    "[RAW_RPC_REPLACE_RECENT_BLOCKHASH] true"
  );

  const rpcResponse =
    await fetch(
      RPC_URL,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method:
            "simulateTransaction",
          params: [
            encoded,
            {
              encoding: "base64",
              sigVerify: false,
              replaceRecentBlockhash: true,
              commitment: "confirmed",
            },
          ],
        }),
      }
    );

  const rpcJson =
    await rpcResponse.json();

  if (
    rpcJson.error
  ) {
    throw new Error(
      `[RAW_RPC_ERROR] ${JSON.stringify(rpcJson.error)}`
    );
  }

  const simulation =
    rpcJson?.result?.value;

  if (!simulation) {
    throw new Error(
      "Raw RPC returned no simulation value"
    );
  }

  console.log(
    `[RAW_RPC_SIMULATION_UNITS] ${simulation.unitsConsumed ?? "UNKNOWN"}`
  );

  if (
    simulation.err !== null
  ) {
    console.log(
      "[SIMULATION_RESULT] FAIL"
    );

    console.log(
      `[SIMULATION_ERROR] ${JSON.stringify(simulation.err)}`
    );

    if (
      Array.isArray(
        simulation.logs
      )
    ) {
      console.log(
        "[SIMULATION_LOGS_BEGIN]"
      );

      for (
        const line
        of simulation.logs
      ) {
        console.log(line);
      }

      console.log(
        "[SIMULATION_LOGS_END]"
      );
    }

    throw new Error(
      "PumpSwap unsigned simulation failed"
    );
  }

  console.log(
    "[SIMULATION_RESULT] PASS"
  );

  if (
    Array.isArray(
      simulation.logs
    )
  ) {
    console.log(
      "[SIMULATION_LOGS_BEGIN]"
    );

    for (
      const line
      of simulation.logs
    ) {
      console.log(line);
    }

    console.log(
      "[SIMULATION_LOGS_END]"
    );
  }

  console.log(
    "[MTR-019] PUMPSWAP UNSIGNED SIMULATION COMPLETE"
  );

  console.log(
    "[MTR-019] NO SIGNING."
  );

  console.log(
    "[MTR-019] NO SENDING."
  );

  console.log(
    "[MTR-019] NO CANONICAL EXECUTOR."
  );
}

main().catch(
  (error) => {
    console.error(
      `[MTR-019] FAIL: ${error?.stack ?? error}`
    );

    process.exit(1);
  }
);
'''

TEST = r'''from pathlib import Path

HARNESS = Path(
    "tools/pumpswap_funded_public_preflight/"
    "mtr_019_pumpswap_dependency_resolution_preflight.mjs"
)

text = HARNESS.read_text(
    encoding="utf-8"
)

checks = [
    (
        "PumpSwap dependency resolver",
        "function resolvePackage(",
    ),
    (
        "Solana web3 dependency resolution",
        '"@solana/web3.js"',
    ),
    (
        "Solana SPL dependency resolution",
        '"@solana/spl-token"',
    ),
    (
        "PumpSwap SDK dependency resolution",
        '"@pump-fun/pump-swap-sdk"',
    ),
    (
        "BN dependency resolution",
        '"bn.js"',
    ),
    (
        "Node require.resolve",
        "require.resolve(",
    ),
    (
        "Exact PumpSwap program ID",
        "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
    ),
    (
        "Exact public candidate",
        "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR",
    ),
    (
        "Native SOL",
        "NATIVE_MINT",
    ),
    (
        "0.010 SOL input",
        'new BN("10000000")',
    ),
    (
        "Official pool state",
        "swapSolanaState",
    ),
    (
        "Official buy quote",
        "buyQuoteInput",
    ),
    (
        "Pool owner verification",
        "POOL_PROGRAM_OWNER",
    ),
    (
        "User binding",
        "STATE_USER_BINDING",
    ),
    (
        "Unsigned serialization",
        "requireAllSignatures: false",
    ),
    (
        "Signature verification disabled",
        "verifySignatures: false",
    ),
    (
        "Raw RPC simulation",
        '"simulateTransaction"',
    ),
    (
        "Base64 encoding",
        '"base64"',
    ),
    (
        "Signature verification false",
        "sigVerify: false",
    ),
    (
        "Recent blockhash replacement",
        "replaceRecentBlockhash: true",
    ),
    (
        "Signing disabled",
        "[SIGNING] DISABLED",
    ),
    (
        "Broadcast disabled",
        "[BROADCAST] DISABLED",
    ),
    (
        "Private key unused",
        "[PRIVATE_KEY] NOT USED",
    ),
]

for label, needle in checks:
    assert needle in text, (
        f"{label}: missing"
    )

    print(
        f"[PASS] {label}"
    )

for needle in [
    "sendAndConfirmTransaction",
    "sendRawTransaction",
    "sendTransaction(",
    "Keypair.fromSecretKey",
    "signTransaction",
    "signAllTransactions",
    "QSB_SOLANA_PRIVATE_KEY",
    "Connection.simulateTransaction",
]:
    assert needle not in text, (
        f"Forbidden operation/reference present: {needle}"
    )

    print(
        "[PASS] Forbidden operation/reference absent: "
        f"{needle}"
    )

print(
    "[TEST COMPLETE] "
    "MTR-019 static safety and construction checks PASS"
)
'''

root = Path(
    "tools/pumpswap_funded_public_preflight"
)

root.mkdir(
    parents=True,
    exist_ok=True
)

harness_path = (
    root /
    "mtr_019_pumpswap_dependency_resolution_preflight.mjs"
)

test_path = Path(
    "test_mtr_019_pumpswap_dependency_resolution_preflight.py"
)

harness_path.write_text(
    HARNESS,
    encoding="utf-8"
)

test_path.write_text(
    TEST,
    encoding="utf-8"
)

print(
    "[BUILD] MTR-019 files written"
)

print(
    f"[HARNESS] {harness_path.resolve()}"
)

print(
    f"[TEST] {test_path.resolve()}"
)

print(
    "[BUILD COMPLETE] MTR-019"
)