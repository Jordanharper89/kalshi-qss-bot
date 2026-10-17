const {Connection,PublicKey,SystemProgram,TransactionMessage,
 VersionedTransaction}=require("@solana/web3.js");
const BN=require("bn.js"),P=require("@pump-fun/pump-swap-sdk");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
 "https://api.mainnet-beta.solana.com";
const PUMP=new PublicKey("FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC");
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000");
const c=new Connection(RPC,"confirmed");

function txIxs(x){
 if(!x)return [];
 if(Array.isArray(x))return x.flatMap(txIxs);
 if(x.instructions)return x.instructions;
 if(x.transaction&&x.transaction.instructions)return x.transaction.instructions;
 if(x.programId&&x.keys)return [x];
 return [];
}

(async()=>{
 console.log("[MTR-062] START");
 console.log("[SCOPE] unsigned atomic construction; no private key; no signing; no sending");

 const on=new P.OnlinePumpAmmSdk(c);
 const ps=await on.swapSolanaState(PUMP,USER);
 const m=await DLMM.create(c,MET);
 const base=ps.pool.baseMint,quote=ps.pool.quoteMint;
 const mx=m.tokenX.mint.address,my=m.tokenY.mint.address;

 if(!quote.equals(W))throw Error("PUMP_QUOTE_NOT_WSOL");
 if(!((mx.equals(base)&&my.equals(W))||(my.equals(base)&&mx.equals(W))))
  throw Error("PAIR_MISMATCH");

 const y2x=W.equals(my);
 const bins=await m.getBinArrayForSwap(y2x);
 const mq=m.swapQuote(INPUT,y2x,new BN(50),bins);
 console.log(`[QUOTE] input=${INPUT} meteora_out=${mq.outAmount} meteora_min=${mq.minOutAmount}`);

 const mtx=await m.swap({
  inToken:W,outToken:base,inAmount:INPUT,minOutAmount:mq.minOutAmount,
  lbPair:MET,user:USER,binArraysPubkey:mq.binArraysPubkey
 });
 const mix=txIxs(mtx);
 console.log(`[METEORA_BUILD] instructions=${mix.length}`);
 if(!mix.length)throw Error("NO_METEORA_INSTRUCTIONS");

 const ptx=await P.PUMP_AMM_SDK.sellBaseInput(ps,mq.minOutAmount,0);
 const pix=txIxs(ptx);
 console.log(`[PUMP_BUILD] instructions=${pix.length}`);
 if(!pix.length)throw Error("NO_PUMP_INSTRUCTIONS");

 const all=[...mix,...pix];
 console.log(`[ATOMIC_BUILD] instructions=${all.length}`);
 console.log(`[PROGRAMS] ${[...new Set(all.map(x=>x.programId.toBase58()))].join(",")}`);

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({
  payerKey:USER,recentBlockhash:bh.blockhash,instructions:all
 }).compileToV0Message();

 console.log(`[MESSAGE] static_keys=${msg.staticAccountKeys.length} required_signatures=${msg.header.numRequiredSignatures}`);

 let serialized=null;
 try{
  const tx=new VersionedTransaction(msg);
  serialized=tx.serialize().length;
  console.log(`[UNSIGNED_SERIALIZED_BYTES] ${serialized}`);
 }catch(e){
  console.log(`[SERIALIZE_BOUNDARY] ${e.message}`);
 }

 const accountSet=new Set();
 for(const ix of all){
  accountSet.add(ix.programId.toBase58());
  for(const k of ix.keys)accountSet.add(k.pubkey.toBase58());
 }
 console.log(`[ACCOUNT_FOOTPRINT] unique=${accountSet.size}`);

 if(msg.header.numRequiredSignatures!==1)throw Error("UNEXPECTED_SIGNER_COUNT");

 console.log("[RESULT] UNSIGNED_ATOMIC_TWO_LEG_BUILD_PASS");
 console.log("[NEXT_GATE] ATOMIC_SIGNED_SIMULATION_AND_EXACT_NETWORK_FEE");
 console.log("[MTR-062] COMPLETE");
})().catch(e=>{
 console.error("[MTR-062] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
