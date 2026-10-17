from pathlib import Path

target=Path("mtr_069_meteora_output_delta_proof.cjs")
target.write_text(r'''const {Connection,PublicKey,TransactionMessage,
VersionedTransaction}=require("@solana/web3.js");
const {getAssociatedTokenAddressSync}=require("@solana/spl-token");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000"),c=new Connection(RPC,"confirmed");

function ixs(x){
 if(!x)return[];
 if(Array.isArray(x))return x.flatMap(ixs);
 if(x.instructions)return x.instructions;
 if(x.transaction&&x.transaction.instructions)return x.transaction.instructions;
 if(x.programId&&x.keys)return[x];
 return[];
}
function amountFromInfo(info){
 if(!info)return new BN(0);
 const b=Buffer.from(info.data);
 if(b.length<72)throw Error("TOKEN_ACCOUNT_TOO_SHORT");
 return new BN(b.subarray(64,72),"le");
}
function amountFromSim(a){
 if(!a)return new BN(0);
 const b=Buffer.from(a.data[0],"base64");
 if(b.length<72)throw Error("SIM_TOKEN_ACCOUNT_TOO_SHORT");
 return new BN(b.subarray(64,72),"le");
}

(async()=>{
 console.log("[MTR-069] START");
 console.log("[SCOPE] exact Meteora pre/post token delta; simulation only");

 const m=await DLMM.create(c,MET);
 const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
 const base=W.equals(x)?y:x;
 const baseProgram=W.equals(x)?m.tokenY.owner:m.tokenX.owner;
 const ata=getAssociatedTokenAddressSync(base,USER,false,baseProgram);

 const preInfo=await c.getAccountInfo(ata,"confirmed");
 const pre=amountFromInfo(preInfo);
 console.log(`[DESTINATION_ATA] ${ata.toBase58()}`);
 console.log(`[PRE_RAW] ${pre}`);

 const y2x=W.equals(y);
 const bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(100),bins);
 console.log(`[QUOTE] in=${INPUT} out=${q.outAmount} protected_min=${q.minOutAmount}`);

 const built=await m.swap({
  inToken:W,outToken:base,inAmount:INPUT,
  minOutAmount:new BN(0),lbPair:MET,user:USER,
  binArraysPubkey:q.binArraysPubkey
 });
 const all=ixs(built);

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({
  payerKey:USER,recentBlockhash:bh.blockhash,instructions:all
 }).compileToV0Message();
 const tx=new VersionedTransaction(msg);

 const sim=await c.simulateTransaction(tx,{
  sigVerify:false,replaceRecentBlockhash:true,commitment:"confirmed",
  accounts:{encoding:"base64",addresses:[ata.toBase58()]}
 });

 console.log(`[SIM_ERR] ${JSON.stringify(sim.value.err)}`);
 console.log(`[SIM_UNITS] ${sim.value.unitsConsumed??"null"}`);

 if(sim.value.err){
  for(const l of (sim.value.logs||[]).slice(-25))
   console.log(`[SIM_LOG] ${l}`);
  throw Error("METEORA_ZERO_MIN_SIM_FAILED");
 }

 const post=amountFromSim(sim.value.accounts&&sim.value.accounts[0]);
 const delta=post.sub(pre);
 const quote=new BN(q.outAmount.toString());
 const protectedMin=new BN(q.minOutAmount.toString());

 console.log(`[POST_RAW] ${post}`);
 console.log(`[ACTUAL_OUTPUT_DELTA_RAW] ${delta}`);
 console.log(`[SDK_QUOTED_RAW] ${quote}`);
 console.log(`[SDK_PROTECTED_MIN_RAW] ${protectedMin}`);
 console.log(`[DELTA_MINUS_QUOTE] ${delta.sub(quote)}`);
 console.log(`[DELTA_MINUS_MIN] ${delta.sub(protectedMin)}`);
 console.log(`[DELTA_MEETS_PROTECTED_MIN] ${delta.gte(protectedMin)}`);

 if(delta.eq(quote))
  console.log("[RESULT] SDK_QUOTE_MATCHES_PHYSICAL_OUTPUT_DELTA");
 else
  console.log("[RESULT] SDK_QUOTE_DIFFERS_FROM_PHYSICAL_OUTPUT_DELTA");

 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-069] COMPLETE");
})().catch(e=>{
 console.error("[MTR-069] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
''',encoding="utf-8")

print(f"[BUILD] wrote {target}")
print("[BUILD] exact Meteora pre/post output-delta proof")
print("[SCOPE] diagnostic minOut=0; no private key; no signing; no sending")