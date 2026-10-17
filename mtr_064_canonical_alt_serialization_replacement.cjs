const {Connection,PublicKey,TransactionMessage,
VersionedTransaction}=require("@solana/web3.js");
const BN=require("bn.js"),P=require("@pump-fun/pump-swap-sdk");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const fs=require("fs"),path=require("path");

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const PREFIX="HSEM6g4T";
const PUMP=new PublicKey("FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC");
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000"),c=new Connection(RPC,"confirmed");

function validKey(s){
 try{return new PublicKey(s).toBase58()===s}catch{return false}
}
function ixs(x){
 if(!x)return[];
 if(Array.isArray(x))return x.flatMap(ixs);
 if(x.instructions)return x.instructions;
 if(x.transaction&&x.transaction.instructions)return x.transaction.instructions;
 if(x.programId&&x.keys)return[x];
 return[];
}
function discover(d,out=[]){
 if(!fs.existsSync(d))return out;
 for(const e of fs.readdirSync(d,{withFileTypes:true})){
  const p=path.join(d,e.name);
  if(e.isDirectory())discover(p,out);
  else if(/\.(py|json|js|cjs|txt)$/i.test(e.name)){
   let t; try{t=fs.readFileSync(p,"utf8")}catch{continue}
   for(const m of t.matchAll(/HSEM6g4T[1-9A-HJ-NP-Za-km-z]{24,50}/g))
    if(validKey(m[0]))out.push({key:m[0],file:p});
  }
 }
 return out;
}

(async()=>{
 console.log("[MTR-064] START");
 console.log("[SCOPE] replacement canonical ALT serialization proof; no signing; no sending");

 const root=path.join("qseries_v2","oracle_execution","solana_atomic_executor");
 const found=discover(root);
 const unique=[...new Map(found.map(x=>[x.key,x])).values()];
 console.log(`[ALT_DISCOVERY] valid_candidates=${unique.length}`);
 for(const x of unique)console.log(`[ALT_CANDIDATE] ${x.key} source=${x.file}`);
 if(!unique.length)throw Error("NO_VALID_CANONICAL_ALT_CANDIDATE");

 let chosen=null,alt=null;
 for(const x of unique){
  const a=(await c.getAddressLookupTable(new PublicKey(x.key))).value;
  if(a&&x.key.startsWith(PREFIX)){chosen=x;alt=a;break}
 }
 if(!alt)throw Error("NO_DISCOVERED_ALT_EXISTS_ON_CHAIN");

 console.log(`[ALT_ADDRESS] ${chosen.key}`);
 console.log(`[ALT_ONCHAIN] addresses=${alt.state.addresses.length}`);

 const on=new P.OnlinePumpAmmSdk(c);
 const ps=await on.swapSolanaState(PUMP,USER);
 const m=await DLMM.create(c,MET);
 const base=ps.pool.baseMint;

 if(!ps.pool.quoteMint.equals(W))throw Error("PUMP_QUOTE_NOT_WSOL");
 const mx=m.tokenX.mint.address,my=m.tokenY.mint.address;
 if(!((mx.equals(base)&&my.equals(W))||(my.equals(base)&&mx.equals(W))))
  throw Error("PAIR_MISMATCH");

 const y2x=W.equals(my),bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(50),bins);
 console.log(`[QUOTE] input=${INPUT} out=${q.outAmount} min=${q.minOutAmount}`);

 const mt=await m.swap({inToken:W,outToken:base,inAmount:INPUT,
  minOutAmount:q.minOutAmount,lbPair:MET,user:USER,
  binArraysPubkey:q.binArraysPubkey});
 const pt=await P.PUMP_AMM_SDK.sellBaseInput(ps,q.minOutAmount,0);
 const all=[...ixs(mt),...ixs(pt)];

 const required=new Set();
 for(const x of all){
  required.add(x.programId.toBase58());
  for(const k of x.keys)required.add(k.pubkey.toBase58());
 }
 const have=new Set(alt.state.addresses.map(x=>x.toBase58()));
 const covered=[...required].filter(x=>have.has(x));
 const missing=[...required].filter(x=>!have.has(x));

 console.log(`[ROUTE] instructions=${all.length} unique_accounts=${required.size}`);
 console.log(`[ALT_COVERAGE] covered=${covered.length} missing=${missing.length}`);
 console.log(`[ALT_MISSING] ${missing.join(",")}`);

 const bh=await c.getLatestBlockhash("confirmed");
 const msg=new TransactionMessage({payerKey:USER,recentBlockhash:bh.blockhash,
  instructions:all}).compileToV0Message([alt]);

 console.log(`[V0] static=${msg.staticAccountKeys.length} lookups=${msg.addressTableLookups.length} signatures=${msg.header.numRequiredSignatures}`);

 let bytes;
 try{bytes=new VersionedTransaction(msg).serialize().length}
 catch(e){
  console.log(`[SERIALIZE_FAIL] ${e.message}`);
  throw Error("CANONICAL_ALT_INSUFFICIENT_FOR_PACKET");
 }
 console.log(`[SERIALIZED_BYTES] ${bytes}`);

 if(bytes>1232)throw Error("PACKET_LIMIT_EXCEEDED");
 if(msg.header.numRequiredSignatures!==1)throw Error("UNEXPECTED_SIGNER_COUNT");

 console.log("[RESULT] CANONICAL_ALT_ATOMIC_SERIALIZATION_PASS");
 console.log("[NEXT_GATE] FRESH_ATOMIC_SIMULATION_CONSTRUCTION");
 console.log("[MTR-064] COMPLETE");
})().catch(e=>{
 console.error("[MTR-064] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
