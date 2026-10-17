const {Connection,PublicKey,TransactionMessage,
VersionedTransaction}=require("@solana/web3.js");
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
function show(v){
 if(v===null||v===undefined)return String(v);
 if(BN.isBN(v))return v.toString();
 if(v instanceof PublicKey)return v.toBase58();
 if(typeof v==="bigint")return v.toString();
 if(Array.isArray(v))return "["+v.map(show).join(",")+"]";
 if(typeof v==="object"){
  const o={};
  for(const [k,x] of Object.entries(v))o[k]=show(x);
  return JSON.stringify(o);
 }
 return String(v);
}

(async()=>{
 console.log("[MTR-078] START");
 console.log("[SCOPE] successful Swap2 event truth; simulation only");

 const m=await DLMM.create(c,MET);
 const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
 const base=W.equals(x)?y:x,y2x=W.equals(y);
 const bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(100),bins);

 console.log(`[PAIR] base=${base.toBase58()} wsol=${W.toBase58()}`);
 console.log(`[QUOTE] in=${INPUT} out=${q.outAmount} min=${q.minOutAmount}`);

 const built=await m.swap({
  inToken:W,outToken:base,inAmount:INPUT,minOutAmount:new BN(0),
  lbPair:MET,user:USER,binArraysPubkey:q.binArraysPubkey
 });
 const all=ixs(built);

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({
  payerKey:USER,recentBlockhash:bh.blockhash,instructions:all
 }).compileToV0Message();
 const tx=new VersionedTransaction(msg);

 const sim=await c.simulateTransaction(tx,{
  sigVerify:false,replaceRecentBlockhash:true,commitment:"confirmed"
 });

 console.log(`[SIM_ERR] ${JSON.stringify(sim.value.err)}`);
 console.log(`[SIM_UNITS] ${sim.value.unitsConsumed??"null"}`);
 if(sim.value.err)throw Error("ZERO_MIN_SIM_FAILED");

 let decoded=0;
 for(const line of sim.value.logs||[]){
  if(!line.startsWith("Program data: "))continue;
  const data=line.slice("Program data: ".length).trim();
  try{
   const evt=m.program.coder.events.decode(data);
   if(!evt)continue;
   decoded++;
   console.log(`[EVENT_NAME] ${evt.name}`);
   console.log(`[EVENT_DATA] ${show(evt.data)}`);
  }catch(e){}
 }

 console.log(`[DECODED_EVENTS] ${decoded}`);
 console.log(`[SDK_QUOTED_RAW] ${q.outAmount}`);

 if(decoded===0)
  console.log("[RESULT] NO_DECODABLE_SWAP2_EVENT");
 else
  console.log("[RESULT] SWAP2_PROGRAM_EVENT_TRUTH_CAPTURED");

 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-078] COMPLETE");
})().catch(e=>{
 console.error("[MTR-078] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
