from pathlib import Path

target=Path("mtr_071_meteora_swap2_token_flow.cjs")
target.write_text(r'''const {Connection,PublicKey,TransactionMessage,
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
function raw(info){
 if(!info||!info.data)return null;
 const b=Buffer.isBuffer(info.data)?info.data:Buffer.from(info.data[0],"base64");
 if(b.length<72)return null;
 return new BN(b.subarray(64,72),"le");
}
function mint(info){
 if(!info||!info.data)return null;
 const b=Buffer.isBuffer(info.data)?info.data:Buffer.from(info.data[0],"base64");
 if(b.length<32)return null;
 try{return new PublicKey(b.subarray(0,32)).toBase58()}catch{return null}
}

(async()=>{
 console.log("[MTR-071] START");
 console.log("[SCOPE] Swap2 token-account flow; simulation only");

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

 const keys=[...new Set(swap.keys.filter(k=>k.isWritable)
   .map(k=>k.pubkey.toBase58()))];
 const preInfos=await c.getMultipleAccountsInfo(keys,"confirmed");

 const tokenKeys=[];
 const pre={};
 for(let i=0;i<keys.length;i++){
  const a=preInfos[i];
  if(!a)continue;
  const owner=a.owner.toBase58();
  if(owner.startsWith("Tokenkeg")||owner.startsWith("TokenzQd")){
   tokenKeys.push(keys[i]);
   pre[keys[i]]={amount:raw(a),mint:mint(a),owner};
  }
 }
 console.log(`[WRITABLE_TOKEN_ACCOUNTS] ${tokenKeys.length}`);

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({
  payerKey:USER,recentBlockhash:bh.blockhash,instructions:all
 }).compileToV0Message();
 const tx=new VersionedTransaction(msg);

 const sim=await c.simulateTransaction(tx,{
  sigVerify:false,replaceRecentBlockhash:true,commitment:"confirmed",
  accounts:{encoding:"base64",addresses:tokenKeys}
 });

 console.log(`[SIM_ERR] ${JSON.stringify(sim.value.err)}`);
 console.log(`[SIM_UNITS] ${sim.value.unitsConsumed??"null"}`);
 if(sim.value.err)throw Error("ZERO_MIN_SIM_FAILED");

 for(let i=0;i<tokenKeys.length;i++){
  const k=tokenKeys[i],p=pre[k];
  const post=raw(sim.value.accounts[i]);
  if(post===null)continue;
  const delta=post.sub(p.amount);
  console.log(`[FLOW] account=${k} mint=${p.mint} pre=${p.amount} post=${post} delta=${delta}`);
 }

 console.log(`[SDK_QUOTED_RAW] ${q.outAmount}`);
 console.log("[RESULT] METEORA_SWAP2_TOKEN_FLOW_CAPTURED");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-071] COMPLETE");
})().catch(e=>{
 console.error("[MTR-071] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
''',encoding="utf-8")

print(f"[BUILD] wrote {target}")
print("[BUILD] exact Meteora Swap2 token-flow accounting")
print("[SCOPE] diagnostic minOut=0; no private key; no signing; no sending")