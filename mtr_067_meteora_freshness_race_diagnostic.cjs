const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000"),SLIP=new BN(100);
const c=new Connection(RPC,"confirmed");

function now(){return Date.now()}
async function quote(tag){
 const t0=now(),slot0=await c.getSlot("confirmed");
 const m=await DLMM.create(c,MET);
 const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
 const y2x=W.equals(y);
 const bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,SLIP,bins);
 const slot1=await c.getSlot("confirmed"),t1=now();
 console.log(`[${tag}] slot0=${slot0} slot1=${slot1} ms=${t1-t0} out=${q.outAmount} min=${q.minOutAmount}`);
 return {m,x,y,y2x,bins,q,slot:slot1,time:t1};
}

(async()=>{
 console.log("[MTR-067] START");
 console.log("[SCOPE] Meteora quote/build freshness race; no signing; no sending");

 const a=await quote("QUOTE_A");
 const build0=now(),buildSlot0=await c.getSlot("confirmed");
 let buildErr=null,tx=null;

 try{
  tx=await a.m.swap({
   inToken:W,outToken:W.equals(a.x)?a.y:a.x,inAmount:INPUT,
   minOutAmount:a.q.minOutAmount,lbPair:MET,user:USER,
   binArraysPubkey:a.q.binArraysPubkey
  });
 }catch(e){buildErr=e}

 const buildSlot1=await c.getSlot("confirmed"),build1=now();
 console.log(`[BUILD_WINDOW] slot0=${buildSlot0} slot1=${buildSlot1} delta=${buildSlot1-buildSlot0} ms=${build1-build0}`);
 console.log(`[QUOTE_TO_BUILD_END] slots=${buildSlot1-a.slot} ms=${build1-a.time}`);
 console.log(`[BUILD_RETURNED] ${tx?true:false}`);
 console.log(`[BUILD_ERROR] ${buildErr?String(buildErr.message||buildErr):"null"}`);

 const b=await quote("QUOTE_B");
 const outDelta=new BN(b.q.outAmount.toString()).sub(new BN(a.q.outAmount.toString()));
 const minDelta=new BN(b.q.minOutAmount.toString()).sub(new BN(a.q.minOutAmount.toString()));

 console.log(`[REQUOTE_DELTA] out_raw=${outDelta} min_raw=${minDelta}`);
 console.log(`[A_MIN_VS_B_OUT] a_min=${a.q.minOutAmount} b_out=${b.q.outAmount}`);

 const below=new BN(b.q.outAmount.toString()).lt(new BN(a.q.minOutAmount.toString()));
 console.log(`[POST_STATE_BELOW_ENCODED_MIN] ${below}`);

 if(buildErr && below){
  console.log("[RESULT] METEORA_FRESHNESS_RACE_PHYSICALLY_CONFIRMED");
  console.log("[NEXT_GATE] SAME_SLOT_QUOTE_BUILD_SIMULATION_PATH");
 }else if(buildErr){
  console.log("[RESULT] BUILD_FAILED_WITHOUT_POST_QUOTE_CROSSING_MIN");
  console.log("[NEXT_GATE] METEORA_ACCOUNT_STATE_SEMANTICS_DIAGNOSIS");
 }else{
  console.log("[RESULT] BUILD_RETURNED_WITH_TIMED_FRESHNESS_EVIDENCE");
  console.log("[NEXT_GATE] IMMEDIATE_ATOMIC_SIMULATION_WITH_FRESHNESS_REVALIDATION");
 }
 console.log("[MTR-067] COMPLETE");
})().catch(e=>{
 console.error("[MTR-067] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
