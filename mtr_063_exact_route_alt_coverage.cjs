const {Connection,PublicKey,SystemProgram,TransactionMessage,
 VersionedTransaction}=require("@solana/web3.js");
const BN=require("bn.js"),P=require("@pump-fun/pump-swap-sdk");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
 "https://api.mainnet-beta.solana.com";
const ALT=new PublicKey("HSEM6g4T");
const PUMP=new PublicKey("FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC");
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000"),c=new Connection(RPC,"confirmed");

function ixs(x){
 if(!x)return [];
 if(Array.isArray(x))return x.flatMap(ixs);
 if(x.instructions)return x.instructions;
 if(x.transaction&&x.transaction.instructions)return x.transaction.instructions;
 if(x.programId&&x.keys)return[x];
 return[];
}

(async()=>{
 console.log("[MTR-063] START");
 console.log("[SCOPE] exact-route ALT coverage; no signing; no sending");

 /* Resolve the full canonical ALT address from the existing executor source,
    because only its HSEM6g4T prefix is frozen in the checkpoint record. */
 const fs=require("fs"),path=require("path");
 const root=path.join("qseries_v2","oracle_execution","solana_atomic_executor");
 let altAddr=null;
 function walk(d){
  if(!fs.existsSync(d))return;
  for(const e of fs.readdirSync(d,{withFileTypes:true})){
   const p=path.join(d,e.name);
   if(e.isDirectory())walk(p);
   else if(/\.(py|json|js|cjs)$/.test(e.name)){
    const t=fs.readFileSync(p,"utf8");
    const m=t.match(/HSEM6g4T[1-9A-HJ-NP-Za-km-z]{20,50}/);
    if(m&&!altAddr)altAddr=m[0];
   }
  }
 }
 walk(root);
 if(!altAddr)throw Error("CANONICAL_ALT_FULL_ADDRESS_NOT_FOUND");
 console.log(`[ALT_ADDRESS] ${altAddr}`);

 const alt=(await c.getAddressLookupTable(new PublicKey(altAddr))).value;
 if(!alt)throw Error("CANONICAL_ALT_NOT_ON_CHAIN");
 console.log(`[ALT_ONCHAIN] addresses=${alt.state.addresses.length}`);

 const on=new P.OnlinePumpAmmSdk(c);
 const ps=await on.swapSolanaState(PUMP,USER);
 const m=await DLMM.create(c,MET);
 const base=ps.pool.baseMint;
 const y2x=W.equals(m.tokenY.mint.address);
 const bins=await m.getBinArrayForSwap(y2x);
 const q=m.swapQuote(INPUT,y2x,new BN(50),bins);

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
 try{
  bytes=new VersionedTransaction(msg).serialize().length;
  console.log(`[SERIALIZED_BYTES] ${bytes}`);
 }catch(e){
  console.log(`[SERIALIZE_FAIL] ${e.message}`);
  throw Error("ALT_SERIALIZATION_HOLD");
 }

 if(bytes>1232)throw Error("PACKET_LIMIT_EXCEEDED");
 console.log("[RESULT] EXACT_ROUTE_ALT_SERIALIZATION_PASS");
 console.log("[NEXT_GATE] FRESH_ATOMIC_SIMULATION_CONSTRUCTION");
 console.log("[MTR-063] COMPLETE");
})().catch(e=>{
 console.error("[MTR-063] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
