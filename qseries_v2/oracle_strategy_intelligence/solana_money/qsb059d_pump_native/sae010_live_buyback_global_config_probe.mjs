import {Connection} from "@solana/web3.js";
import {
  OnlinePumpAmmSdk,
  GLOBAL_CONFIG_PDA
} from "@pump-fun/pump-swap-sdk";

const rpc=process.env.SOLANA_RPC_URL ||
  "https://api.mainnet-beta.solana.com";

const sdk=new OnlinePumpAmmSdk(
  new Connection(rpc,"confirmed")
);

if (
  !sdk.program ||
  !sdk.program.account ||
  !sdk.program.account.globalConfig ||
  !sdk.program.account.globalConfig.fetch
) {
  throw new Error("GLOBAL_CONFIG_FETCH_INTERFACE_MISSING");
}

const gc=await sdk.program.account.globalConfig.fetch(
  GLOBAL_CONFIG_PDA
);

const raw=
  gc.buybackFeeRecipients ||
  gc.buyback_fee_recipients ||
  [];

const recipients=raw.map(
  x=>x?.toBase58 ? x.toBase58() : String(x)
);

console.log(
  "[SAE010_GLOBAL_CONFIG]",
  GLOBAL_CONFIG_PDA.toBase58()
);

console.log(
  "[SAE010_BUYBACK_COUNT]",
  recipients.length
);

recipients.forEach((x,i)=>{
  console.log(
    `[SAE010_BUYBACK] index=${i} pubkey=${x}`
  );
});

if (recipients.length!==8) {
  throw new Error(
    "EXPECTED_8_BUYBACK_RECIPIENTS_GOT_"+recipients.length
  );
}

console.log("[PASS] SAE-010 live buyback GlobalConfig truth");
