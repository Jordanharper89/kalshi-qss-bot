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
function bytes(info,sim=false){
 if(!info||!info.data)return null;
 return sim?Buffer.from(info.data[0],"base64"):Buffer.from(info.data);
}
function raw(info,sim=false){
 const b=bytes(info,sim); if(!b||b.length<72)return null;
 return new BN(b.subarray(64,72),"le");
}
function mint(info,sim=false){
 const b=bytes(info,sim); if(!b||b.length<32)return null;
 try{return new PublicKey(b.subarray(0,32)).toBase58()}catch{return null}
}

(async()=>{
 console.log("[MTR-072] START");
 console.log("[SCOPE] corrected Swap2 token-account flow; simulation only");

 const m=await DLMM.create(c,MET);
 const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
 const base=W.equals(x)?y:x,y2x=W.equals(y);
 const bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(100),bins);
 console.log(`[PAIR] base=${base.toBase58()} wsol=${W.toBase58()}`);
 console.log(`[QUOTE] in=${INPUT} out=${q.outAmount} protected_min=${q.minOutAmount}`);

 const built=await m.swap({
  inToken:W,outToken:base,inAmount:INPUT,minOutAmount:new BN(0),
  lbPair:MET,user:USER,binArraysPubkey:q.binArraysPubkey
 });
 const all=ixs(built);
 const swap=all.find(z=>z.programId.toBase58()==="LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo");
 if(!swap)throw Error("SWAP2_NOT_FOUND");

 const seen=new Set(),writable=[];
 for(const k of swap.keys){
  if(!k.isWritable)continue;
  const s=k.pubkey.toBase58();
  if(!seen.has(s)){seen.add(s);writable.push(k.pubkey)}
 }
 const infos=await c.getMultipleAccountsInfo(writable,"confirmed");
 const tokenKeys=[],pre={};

 for(let i=0;i<writable.length;i++){
  const a=infos[i]; if(!a)continue;
  const owner=a.owner.toBase58();
  if(owner==="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"||
     owner==="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"){
   const s=writable[i].toBase58();
   tokenKeys.push(writable[i]);
   pre[s]={amount:raw(a),mint:mint(a),owner};
  }
 }
 console.log(`[WRITABLE_TOKEN_ACCOUNTS] ${tokenKeys.length}`);
 tokenKeys.forEach(k=>console.log(`[TRACK] ${k.toBase58()} mint=${pre[k.toBase58()].mint}`));

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({
  payerKey:USER,recentBlockhash:bh.blockhash,instructions:all
 }).compileToV0Message();
 const tx=new VersionedTransaction(msg);

 const sim=await c.simulateTransaction(tx,{
  sigVerify:false,replaceRecentBlockhash:true,commitment:"confirmed",
  accounts:{encoding:"base64",addresses:tokenKeys.map(k=>k.toBase58())}
 });
 console.log(`[SIM_ERR] ${JSON.stringify(sim.value.err)}`);
 console.log(`[SIM_UNITS] ${sim.value.unitsConsumed??"null"}`);
 if(sim.value.err)throw Error("ZERO_MIN_SIM_FAILED");

 for(let i=0;i<tokenKeys.length;i++){
  const s=tokenKeys[i].toBase58(),p=pre[s];
  const post=raw(sim.value.accounts[i],true);
  if(post===null||p.amount===null)continue;
  console.log(`[FLOW] account=${s} mint=${p.mint} pre=${p.amount} post=${post} delta=${post.sub(p.amount)}`);
 }

 console.log(`[SDK_QUOTED_RAW] ${q.outAmount}`);
 console.log("[RESULT] METEORA_SWAP2_TOKEN_FLOW_CAPTURED");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-072] COMPLETE");
})().catch(e=>{
 console.error("[MTR-072] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
