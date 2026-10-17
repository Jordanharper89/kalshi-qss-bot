const RPC =
  process.env.QSB_SOLANA_RPC ||
  "https://api.mainnet-beta.solana.com";

const PUBLIC_CANDIDATE =
  "CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR";

const USDC_MINT =
  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";

const TOKEN_PROGRAM =
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";

const REQUIRED_RAW_USDC = 100000000n;

async function rpc(method, params) {
  const response = await fetch(RPC, {
    method: "POST",
    headers: {
      "content-type": "application/json"
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method,
      params
    })
  });

  const text = await response.text();

  let json;

  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(
      `RPC returned non-JSON HTTP ${response.status}: ${text.slice(0, 1000)}`
    );
  }

  if (!response.ok) {
    throw new Error(
      `RPC HTTP ${response.status}: ${JSON.stringify(json)}`
    );
  }

  if (json.error) {
    throw new Error(
      `RPC ${method} error: ${JSON.stringify(json.error)}`
    );
  }

  return json;
}

async function main() {
  console.log("[MTR-007] START");
  console.log(`[RPC] ${RPC}`);
  console.log(
    `[PUBLIC_CANDIDATE] ${PUBLIC_CANDIDATE}`
  );
  console.log(
    `[USDC_MINT] ${USDC_MINT}`
  );
  console.log(
    `[TOKEN_PROGRAM] ${TOKEN_PROGRAM}`
  );
  console.log(
    `[REQUIRED_RAW_USDC] ${REQUIRED_RAW_USDC.toString()}`
  );

  const response = await rpc(
    "getTokenAccountsByOwner",
    [
      PUBLIC_CANDIDATE,
      {
        programId: TOKEN_PROGRAM
      },
      {
        encoding: "jsonParsed",
        commitment: "confirmed"
      }
    ]
  );

  console.log(
    `[RPC_TOP_LEVEL_KEYS] ${
      Object.keys(response).join(",")
    }`
  );

  console.log(
    `[RPC_RESULT_KEYS] ${
      Object.keys(response.result ?? {}).join(",")
    }`
  );

  console.log(
    `[RPC_CONTEXT_KEYS] ${
      Object.keys(response.result?.context ?? {}).join(",")
    }`
  );

  const rows = response.result?.value;

  console.log(
    `[VALUE_IS_ARRAY] ${
      Array.isArray(rows)
        ? "YES"
        : "NO"
    }`
  );

  if (!Array.isArray(rows)) {
    throw new Error(
      "Raw RPC result.value is not an array."
    );
  }

  console.log(
    `[TOKEN_ACCOUNT_COUNT] ${rows.length}`
  );

  if (rows.length === 0) {
    throw new Error(
      "Raw RPC returned zero token accounts."
    );
  }

  console.log(
    "[RAW_FIRST_TOKEN_ACCOUNT_BEGIN]"
  );

  console.log(
    JSON.stringify(
      rows[0],
      null,
      2
    )
  );

  console.log(
    "[RAW_FIRST_TOKEN_ACCOUNT_END]"
  );

  const first = rows[0];

  console.log(
    `[FIRST_ROW_KEYS] ${
      Object.keys(first ?? {}).join(",")
    }`
  );

  console.log(
    `[FIRST_ACCOUNT_KEYS] ${
      Object.keys(first?.account ?? {}).join(",")
    }`
  );

  console.log(
    `[FIRST_DATA_TYPE] ${
      Array.isArray(first?.account?.data)
        ? "array"
        : typeof first?.account?.data
    }`
  );

  console.log(
    `[FIRST_DATA_KEYS] ${
      first?.account?.data &&
      typeof first.account.data === "object" &&
      !Array.isArray(first.account.data)
        ? Object.keys(first.account.data).join(",")
        : ""
    }`
  );

  const usdcAccounts = [];
  let usdcRawTotal = 0n;

  for (const row of rows) {
    const pubkey = row?.pubkey;
    const account = row?.account;
    const data = account?.data;

    const parsed =
      data &&
      typeof data === "object" &&
      !Array.isArray(data)
        ? data.parsed
        : null;

    const info =
      parsed &&
      typeof parsed === "object"
        ? parsed.info
        : null;

    const mint =
      info?.mint ?? "";

    const owner =
      info?.owner ?? "";

    const tokenAmount =
      info?.tokenAmount;

    if (mint !== USDC_MINT) {
      continue;
    }

    let rawAmount = null;

    if (
      tokenAmount &&
      typeof tokenAmount === "object" &&
      tokenAmount.amount !== undefined
    ) {
      try {
        rawAmount =
          BigInt(
            String(tokenAmount.amount)
          );
      } catch {
        rawAmount = null;
      }
    }

    if (rawAmount !== null) {
      usdcRawTotal += rawAmount;
    }

    usdcAccounts.push({
      pubkey,
      owner,
      rawAmount,
      decimals:
        tokenAmount?.decimals ?? null,
      uiAmountString:
        tokenAmount?.uiAmountString ?? null,
      accountOwner:
        account?.owner ?? null
    });
  }

  console.log(
    `[USDC_TOKEN_ACCOUNT_COUNT] ${usdcAccounts.length}`
  );

  console.log(
    `[USDC_RAW_TOTAL] ${usdcRawTotal.toString()}`
  );

  console.log(
    `[USDC_REQUIRED_RAW] ${REQUIRED_RAW_USDC.toString()}`
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
      `owner=${account.owner} ` +
      `raw_amount=${
        account.rawAmount === null
          ? "UNPARSED"
          : account.rawAmount.toString()
      } ` +
      `decimals=${account.decimals} ` +
      `ui_amount=${
        account.uiAmountString ?? "null"
      } ` +
      `account_owner=${
        account.accountOwner ?? "null"
      }`
    );
  }

  const ownershipFailures =
    usdcAccounts.filter(
      (account) =>
        account.owner !==
        PUBLIC_CANDIDATE
    );

  console.log(
    `[OWNERSHIP_FAILURE_COUNT] ${
      ownershipFailures.length
    }`
  );

  if (ownershipFailures.length > 0) {
    throw new Error(
      "One or more USDC accounts do not identify the public candidate as owner."
    );
  }

  if (usdcAccounts.length > 0) {
    console.log(
      "[OWNERSHIP_VERIFICATION] PASS"
    );
  } else {
    console.log(
      "[OWNERSHIP_VERIFICATION] FAIL"
    );
  }

  if (
    usdcRawTotal >=
    REQUIRED_RAW_USDC
  ) {
    console.log(
      "[FUNDING_VERIFICATION] PASS"
    );
  } else {
    console.log(
      "[FUNDING_VERIFICATION] FAIL"
    );
  }

  console.log(
    "[MTR-007] RAW RPC TOKEN-ACCOUNT PROBE COMPLETE."
  );

  console.log(
    "[MTR-007] NO SIGNING."
  );

  console.log(
    "[MTR-007] NO SENDING."
  );

  console.log(
    "[MTR-007] NO METEORA SWAP CONSTRUCTION."
  );
}

main().catch((error) => {
  console.error(
    `[FAIL] ${error?.stack ?? error}`
  );

  process.exitCode = 1;
});
