const {Connection,PublicKey,TransactionMessage,
VersionedTransaction}=require("@solana/web3.js");
const BN=require("bn.js"),P=require("@pump-fun/pump-swap-sdk");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const ALT=new PublicKey("HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r");
const PUMP=new PublicKey("FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC");
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

(async()=>{
 console.log("[MTR-065] START");
 console.log("[SCOPE] exact atomic unsigned simulation + fee; no private key; no send");

 const alt=(await c.getAddressLookupTable(ALT)).value;
 if(!alt)throw Error("ALT_NOT_FOUND");

 const on=new P.OnlinePumpAmmSdk(c);
 const ps=await on.swapSolanaState(PUMP,USER);
 const m=await DLMM.create(c,MET);
 const base=ps.pool.baseMint,mx=m.tokenX.mint.address,my=m.tokenY.mint.address;

 if(!ps.pool.quoteMint.equals(W))throw Error("PUMP_QUOTE_NOT_WSOL");
 if(!((mx.equals(base)&&my.equals(W))||(my.equals(base)&&mx.equals(W))))
  throw Error("PAIR_MISMATCH");

 const y2x=W.equals(my),bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(100),bins);
 console.log(`[FRESH_QUOTE] in=${INPUT} out=${q.outAmount} min=${q.minOutAmount}`);

 const mt=await m.swap({inToken:W,outToken:base,inAmount:INPUT,
  minOutAmount:q.minOutAmount,lbPair:MET,user:USER,
  binArraysPubkey:q.binArraysPubkey});

 /* Pump leg uses the executable Meteora minimum, not optimistic output. */
 const pt=await P.PUMP_AMM_SDK.sellBaseInput(ps,q.minOutAmount,0);
 const all=[...ixs(mt),...ixs(pt)];
 console.log(`[ATOMIC] instructions=${all.length}`);

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({payerKey:USER,recentBlockhash:bh.blockhash,
  instructions:all}).compileToV0Message([alt]);

 const tx=new VersionedTransaction(msg);
 const bytes=tx.serialize().length;
 console.log(`[SERIALIZED_BYTES] ${bytes}`);
 if(bytes>1232)throw Error("PACKET_LIMIT_EXCEEDED");

 const fee=await c.getFeeForMessage(msg,"confirmed");
 if(fee.value===null)throw Error("NETWORK_FEE_UNAVAILABLE");
 console.log(`[NETWORK_FEE_LAMPORTS] ${fee.value}`);

 const sim=await c.simulateTransaction(tx,{
  sigVerify:false,
  replaceRecentBlockhash:true,
  commitment:"confirmed"
 });

 console.log(`[SIM_ERR] ${JSON.stringify(sim.value.err)}`);
 console.log(`[SIM_UNITS] ${sim.value.unitsConsumed??"null"}`);

 if(sim.value.err){
  const logs=sim.value.logs||[];
  for(const x of logs.slice(-25))console.log(`[SIM_LOG] ${x}`);
  throw Error("ATOMIC_SIMULATION_REJECTED");
 }

 console.log("[RESULT] ATOMIC_UNSIGNED_SIMULATION_PASS");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[NEXT_GATE] SIGNED_ATOMIC_SIMULATION_AND_NET_PROFIT");
 console.log("[MTR-065] COMPLETE");
})().catch(e=>{
 console.error("[MTR-065] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
