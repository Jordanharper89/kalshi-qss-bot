from pathlib import Path

ROOT=Path.cwd()
B=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native"

MJS=B/"sae012_direct_pumpswap_buyexact_sim_probe.mjs"
TEST=ROOT/"test_sae_012_direct_pumpswap_buyexact_sim_probe.py"

MJS.write_text(r'''
import {
  Connection,
  PublicKey,
  Transaction,
  TransactionInstruction
} from "@solana/web3.js";

import {
  OnlinePumpAmmSdk,
  PUMP_AMM_SDK,
  PUMP_AMM_PROGRAM_ID,
  OFFLINE_PUMP_AMM_PROGRAM
} from "@pump-fun/pump-swap-sdk";

const RPC=process.env.SOLANA_RPC_URL ||
  "https://api.mainnet-beta.solana.com";

const USER=new PublicKey(
  "MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
);

/*
Current physically warmed Pump pools from canonical startup.
Try each until one reaches PumpSwap program execution.
*/
const POOLS=[
  "5mfeK1Pygz1rK6sbKXZUrdYdE24NgsMee56N8HKabVZY",
  "5wNu5QhdpRGrL37ffcd6TMMqZugQgxwafgz477rShtHy",
  "4w2cysotX6czaUGmmWg13hDpY4QEMG2CzeKYEQyK9Ama",
  "B3QKPLFQmioyC5yaAHtkRcrzrtbfdcpZTxcxhWd83Urk"
].map(x=>new PublicKey(x));

const connection=new Connection(RPC,"processed");
const sdk=new OnlinePumpAmmSdk(connection);

async function probe(poolKey) {
  console.log("\n[SAE012_POOL]",poolKey.toBase58());

  const state=await sdk.swapSolanaState(
    poolKey,
    USER
  );

  /*
  Build the normal SDK buy account list.
  Very small minimum output deliberately avoids economic/slippage
  rejection; this probe is about account-contract validity only.
  */
  const baseOut=1n;
  const quoteIn=1_000_000n;

  const instructions=await PUMP_AMM_SDK.buyInstructions(
    state,
    baseOut,
    quoteIn
  );

  const buyIndex=instructions.findIndex(ix=>
    ix.programId.equals(PUMP_AMM_PROGRAM_ID) &&
    ix.data.length>8
  );

  if (buyIndex<0)
    throw new Error("PUMP_BUY_INSTRUCTION_NOT_FOUND");

  const original=instructions[buyIndex];

  const data=
    OFFLINE_PUMP_AMM_PROGRAM.coder.instruction.encode(
      "buyExactQuoteIn",
      {
        spendableQuoteIn:quoteIn,
        minBaseAmountOut:baseOut,
        trackVolume:{0:true}
      }
    );

  instructions[buyIndex]=new TransactionInstruction({
    programId:original.programId,
    keys:original.keys,
    data
  });

  console.log(
    "[SAE012_PUMP_KEYS]",
    original.keys.length
  );

  original.keys.forEach((k,i)=>{
    if(i>=23){
      console.log(
        `[SAE012_REMAINING] number=${i+1} `+
        `pubkey=${k.pubkey.toBase58()} `+
        `writable=${k.isWritable}`
      );
    }
  });

  const {blockhash}=await connection.getLatestBlockhash(
    "processed"
  );

  const tx=new Transaction({
    feePayer:USER,
    recentBlockhash:blockhash
  });

  tx.add(...instructions);

  /*
  Produce zeroed placeholder signatures.
  RPC simulation runs with signature verification disabled.
  Nothing is sent.
  */
  tx.setSigners(USER);

  const raw=tx.serialize({
    requireAllSignatures:false,
    verifySignatures:false
  });

  const encoded=raw.toString("base64");

  const body={
    jsonrpc:"2.0",
    id:1,
    method:"simulateTransaction",
    params:[
      encoded,
      {
        encoding:"base64",
        sigVerify:false,
        replaceRecentBlockhash:true,
        commitment:"processed"
      }
    ]
  };

  const response=await fetch(RPC,{
    method:"POST",
    headers:{"content-type":"application/json"},
    body:JSON.stringify(body)
  });

  const json=await response.json();

  if(json.error){
    console.log(
      "[SAE012_RPC_ERROR]",
      JSON.stringify(json.error)
    );
    return false;
  }

  const value=json.result?.value;

  console.log(
    "[SAE012_SIM_ERR]",
    JSON.stringify(value?.err ?? null)
  );

  for(const line of value?.logs ?? []){
    if(
      line.includes("6058") ||
      line.includes("6062") ||
      line.includes("Buyback") ||
      line.includes("PoolV2") ||
      line.includes("Program log:")
    ){
      console.log("[SAE012_LOG]",line);
    }
  }

  if(value?.err===null){
    console.log(
      "[SAE012_DIRECT_PUMP_SIM_PASS]",
      poolKey.toBase58()
    );
    return true;
  }

  const logs=(value?.logs ?? []).join("\n");

  if(logs.includes("BuybackFeeRecipientMissing")){
    console.log(
      "[SAE012_6058_REPRODUCED]",
      poolKey.toBase58()
    );
    return true;
  }

  console.log(
    "[SAE012_OTHER_REJECT]",
    poolKey.toBase58()
  );

  return false;
}

for(const pool of POOLS){
  try{
    const decisive=await probe(pool);
    if(decisive) break;
  }catch(e){
    console.log(
      "[SAE012_POOL_ERROR]",
      pool.toBase58(),
      e?.stack || String(e)
    );
  }
}

console.log("[SAE012_COMPLETE]");
console.log("[BROADCAST] disabled");
'''.lstrip(),encoding="utf-8")

TEST.write_text(r'''
from pathlib import Path
import unittest

class T(unittest.TestCase):

    def test_probe_exists(self):
        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
        )
        self.assertTrue(p.is_file())

    def test_no_send_transaction(self):
        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
        )
        s=p.read_text(encoding="utf-8")
        self.assertNotIn("sendTransaction(",s)
        self.assertIn("simulateTransaction",s)
        self.assertIn("buyExactQuoteIn",s)
        self.assertIn("sigVerify:false",s)

    def test_four_physical_pools(self):
        s=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qsb059d_pump_native/"
            "sae012_direct_pumpswap_buyexact_sim_probe.mjs"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            s.count('"5mfeK1')+
            s.count('"5wNu5Q')+
            s.count('"4w2cys')+
            s.count('"B3QKPL'),
            4
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
'''.lstrip(),encoding="utf-8")

print("[PASS] SAE-012 direct PumpSwap BuyExactQuoteIn sim probe installed")
print("[MODE] standalone account-contract simulation")
print("[PRIVATE_KEY] not required")
print("[BROADCAST] disabled")