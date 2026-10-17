const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const bs58=require("bs58");
const D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const DISC=Buffer.from("f19a6d0411b16dbc","hex");
const c=new Connection(RPC,"confirmed");

function key(v){return v?.toBase58?v.toBase58():String(v)}
function rows(x){
 if(Array.isArray(x))return x;
 for(const k of ["candidates","funded","rows","results","items"])
  if(Array.isArray(x?.[k]))return x[k];
 return[];
}
function oldPumpSet(){
 const f="mtr_057_funded_exact_pair_candidates.json";
 if(!fs.existsSync(f))return new Set();
 const out=new Set();
 for(const r of rows(JSON.parse(fs.readFileSync(f,"utf8")))){
  const p=r.pump_pool||r.pumpPool||r.pool||r.pump_pool_address;
  if(p)out.add(p);
 }
 return out;
}

(async()=>{
 console.log("[MTR-096] START");
 console.log("[SCOPE] fresh current PumpSwap/WSOL exact-pair replenishment");

 const b58=bs58.encode?bs58.encode(DISC):bs58.default.encode(DISC);

 const pumpAccounts=await c.getProgramAccounts(PUMP,{
  commitment:"confirmed",
  filters:[
   {dataSize:301},
   {memcmp:{offset:0,bytes:b58}},
   {memcmp:{offset:75,bytes:W.toBase58()}}
  ],
  dataSlice:{offset:43,length:64}
 });

 console.log(`[PUMP_WSOL_POOLS] ${pumpAccounts.length}`);

 const pumps=[];
 for(const a of pumpAccounts){
  const d=a.account.data;
  if(!Buffer.isBuffer(d)||d.length<64)continue;
  const base=new PublicKey(d.subarray(0,32));
  const quote=new PublicKey(d.subarray(32,64));
  if(!quote.equals(W))continue;
  pumps.push({pump_pool:a.pubkey.toBase58(),base_mint:base.toBase58()});
 }
 console.log(`[PUMP_PARSED] ${pumps.length}`);

 const all=await DLMM.getLbPairs(c);
 console.log(`[METEORA_PAIRS] ${all.length}`);

 const byBase=new Map();
 for(const z of all){
  const pk=key(z.publicKey||z.pubkey||z.address),a=z.account||z;
  const x=key(a.tokenXMint),y=key(a.tokenYMint);
  let base=null;
  if(x===W.toBase58()&&y!==W.toBase58())base=y;
  else if(y===W.toBase58()&&x!==W.toBase58())base=x;
  if(!base)continue;
  if(!byBase.has(base))byBase.set(base,[]);
  byBase.get(base).push(pk);
 }

 const old=oldPumpSet(),out=[];
 let links=0,newPump=0;

 for(const r of pumps){
  const mets=byBase.get(r.base_mint)||[];
  if(!mets.length)continue;
  links+=mets.length;
  const isNew=!old.has(r.pump_pool);
  if(isNew)newPump++;
  out.push({
   pump_pool:r.pump_pool,
   base_mint:r.base_mint,
   meteora_pools:mets,
   meteora_count:mets.length,
   new_vs_mtr057:isNew
  });
 }

 out.sort((a,b)=>
  Number(b.new_vs_mtr057)-Number(a.new_vs_mtr057)||
  b.meteora_count-a.meteora_count||
  a.pump_pool.localeCompare(b.pump_pool));

 fs.writeFileSync("mtr_096_fresh_exact_pair_replenishment.json",
  JSON.stringify({
   pump_wsol_pools:pumps.length,
   exact_pump_pools:out.length,
   exact_links:links,
   new_pump_pools:newPump,
   rows:out
  },null,2));

 console.log(`[SUMMARY] pump_wsol=${pumps.length} exact_pump_pools=${out.length} exact_links=${links} new_vs_mtr057=${newPump}`);
 for(const r of out.filter(x=>x.new_vs_mtr057).slice(0,25))
  console.log(`[NEW] pump=${r.pump_pool} meteora=${r.meteora_count} base=${r.base_mint}`);

 console.log(out.length?
  "[RESULT] FRESH_EXACT_PAIR_REPLENISHMENT_FOUND":
  "[RESULT] NO_FRESH_EXACT_PAIR_REPLENISHMENT");
 console.log("[OUTPUT] mtr_096_fresh_exact_pair_replenishment.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-096] COMPLETE");
})().catch(e=>{
 console.error("[MTR-096] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
