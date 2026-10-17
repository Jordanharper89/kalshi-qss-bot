const {Connection,PublicKey,TransactionMessage,
VersionedTransaction}=require("@solana/web3.js");
const {getAssociatedTokenAddressSync,unpackAccount}=require("@solana/spl-token");
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
function tokenAmount(a){
 if(!a||!a.data)return null;
 const b=Buffer.from(a.data[0],"base64");
 return new BN(b.subarray(64,72),"le");
}

(async()=>{
 console.log("[MTR-068] START");
 console.log("[SCOPE] standalone Meteora diagnostic minOut=0; simulation only");

 const m=await DLMM.create(c,MET);
 const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
 const base=W.equals(x)?y:x;
 const y2x=W.equals(y);
 const bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(100),bins);

 console.log(`[PAIR] base=${base.toBase58()} wsol=${W.toBase58()}`);
 console.log(`[QUOTE] in=${INPUT} out=${q.outAmount} protected_min=${q.minOutAmount}`);

 const baseProgram=W.equals(x)?m.tokenY.owner:m.tokenX.owner;
 const baseAta=getAssociatedTokenAddressSync(base,USER,false,baseProgram);
 console.log(`[DESTINATION_ATA] ${baseAta.toBase58()}`);

 const built=await m.swap({
  inToken:W,outToken:base,inAmount:INPUT,
  minOutAmount:new BN(0),lbPair:MET,user:USER,
  binArraysPubkey:q.binArraysPubkey
 });
 const all=ixs(built);
 console.log(`[INSTRUCTIONS] ${all.length}`);

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({
  payerKey:USER,recentBlockhash:bh.blockhash,instructions:all
 }).compileToV0Message();

 const tx=new VersionedTransaction(msg);

 const sim=await c.simulateTransaction(tx,{
  sigVerify:false,
  replaceRecentBlockhash:true,
  commitment:"confirmed",
  accounts:{encoding:"base64",addresses:[baseAta.toBase58()]}
 });

 console.log(`[SIM_ERR] ${JSON.stringify(sim.value.err)}`);
 console.log(`[SIM_UNITS] ${sim.value.unitsConsumed??"null"}`);

 if(sim.value.err){
  for(const l of (sim.value.logs||[]).slice(-30))
   console.log(`[SIM_LOG] ${l}`);
  throw Error("ZERO_MIN_METEORA_SIMULATION_FAILED");
 }

 const acct=sim.value.accounts&&sim.value.accounts[0];
 if(!acct)throw Error("DESTINATION_ACCOUNT_NOT_RETURNED");

 const actual=tokenAmount(acct);
 if(actual===null)throw Error("DESTINATION_AMOUNT_NOT_DECODED");

 console.log(`[SIM_DESTINATION_RAW] ${actual}`);
 console.log(`[SDK_QUOTED_RAW] ${q.outAmount}`);
 console.log(`[SDK_PROTECTED_MIN_RAW] ${q.minOutAmount}`);

 const vsQuote=actual.sub(new BN(q.outAmount.toString()));
 const vsMin=actual.sub(new BN(q.minOutAmount.toString()));
 console.log(`[DELTA_VS_QUOTE] ${vsQuote}`);
 console.log(`[DELTA_VS_PROTECTED_MIN] ${vsMin}`);
 console.log(`[WOULD_PASS_PROTECTED_MIN] ${!vsMin.isNeg()}`);

 console.log("[RESULT] METEORA_PHYSICAL_SIMULATED_OUTPUT_CAPTURED");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-068] COMPLETE");
})().catch(e=>{
 console.error("[MTR-068] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
