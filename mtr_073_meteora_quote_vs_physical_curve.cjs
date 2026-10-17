const {Connection,PublicKey,TransactionMessage,
VersionedTransaction}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const SIZES=["1000000","2500000","5000000","10000000","20000000"];
const c=new Connection(RPC,"confirmed");

function ixs(x){
 if(!x)return[];
 if(Array.isArray(x))return x.flatMap(ixs);
 if(x.instructions)return x.instructions;
 if(x.transaction&&x.transaction.instructions)return x.transaction.instructions;
 if(x.programId&&x.keys)return[x];
 return[];
}
function raw(info,sim=false){
 if(!info||!info.data)return null;
 const b=sim?Buffer.from(info.data[0],"base64"):Buffer.from(info.data);
 if(b.length<72)return null;
 return new BN(b.subarray(64,72),"le");
}

(async()=>{
 console.log("[MTR-073] START");
 console.log("[SCOPE] Meteora SDK quote versus physical Swap2 curve; simulation only");

 for(const s of SIZES){
  const input=new BN(s);
  const m=await DLMM.create(c,MET);
  const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
  const base=W.equals(x)?y:x,y2x=W.equals(y);
  const bins=await m.getBinArrayForSwap(y2x);
  const q=m.swapQuote(input,y2x,new BN(100),bins);

  const built=await m.swap({
   inToken:W,outToken:base,inAmount:input,minOutAmount:new BN(0),
   lbPair:MET,user:USER,binArraysPubkey:q.binArraysPubkey
  });
  const all=ixs(built);
  const swap=all.find(z=>z.programId.toBase58()==="LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo");
  if(!swap)throw Error("SWAP2_NOT_FOUND");

  const vaultKey=swap.keys[2].pubkey;
  const preInfo=await c.getAccountInfo(vaultKey,"confirmed");
  const pre=raw(preInfo);

  const bh=await c.getLatestBlockhash("confirmed");
  const msg=new TransactionMessage({
   payerKey:USER,recentBlockhash:bh.blockhash,instructions:all
  }).compileToV0Message();
  const tx=new VersionedTransaction(msg);

  const sim=await c.simulateTransaction(tx,{
   sigVerify:false,replaceRecentBlockhash:true,commitment:"confirmed",
   accounts:{encoding:"base64",addresses:[vaultKey.toBase58()]}
  });

  if(sim.value.err){
   console.log(`[SIZE] input=${input} SIM_FAIL=${JSON.stringify(sim.value.err)}`);
   continue;
  }

  const post=raw(sim.value.accounts[0],true);
  const physical=pre.sub(post);
  const quoted=new BN(q.outAmount.toString());
  const diff=quoted.sub(physical);
  const ratio=physical.mul(new BN(1000000)).div(quoted);

  console.log(
   `[SIZE] input=${input} quoted=${quoted} physical=${physical} `+
   `shortfall=${diff} physical_ppm=${ratio}`
  );
 }

 console.log("[RESULT] METEORA_QUOTE_PHYSICAL_CURVE_CAPTURED");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-073] COMPLETE");
})().catch(e=>{
 console.error("[MTR-073] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
