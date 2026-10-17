const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const {AccountLayout}=require("@solana/spl-token");
const {PUMP_AMM_SDK}=require("@pump-fun/pump-swap-sdk");

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112";
const c=new Connection(RPC,"confirmed");
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function rows(x){return Array.isArray(x?.rows)?x.rows:[]}
function oldSet(){
 const f="mtr_057_funded_exact_pair_candidates.json",s=new Set();
 if(!fs.existsSync(f))return s;
 const j=JSON.parse(fs.readFileSync(f,"utf8"));
 const a=Array.isArray(j)?j:(j.candidates||j.funded||j.rows||j.results||j.items||[]);
 for(const r of a){
  const k=r.pump_pool||r.pumpPool||r.pool||r.pump_pool_address;
  if(k)s.add(k);
 }
 return s;
}
function chunks(a,n){const out=[];for(let i=0;i<a.length;i+=n)out.push(a.slice(i,i+n));return out}

(async()=>{
 console.log("[MTR-100] START");
 console.log("[SCOPE] new Pump physical-liquidity batch filter");

 const src="mtr_096_fresh_exact_pair_replenishment.json";
 if(!fs.existsSync(src))throw Error("MTR_096_NOT_FOUND");
 const old=oldSet();
 const fresh=rows(JSON.parse(fs.readFileSync(src,"utf8")))
  .filter(r=>r.new_vs_mtr057 && !old.has(r.pump_pool));

 console.log(`[NEW_POOL_ROWS] ${fresh.length}`);

 const decoded=[];
 let poolMiss=0,batch=0;

 for(const group of chunks(fresh,80)){
  batch++;
  const infos=await c.getMultipleAccountsInfo(
   group.map(r=>new PublicKey(r.pump_pool)),"confirmed");

  for(let i=0;i<group.length;i++){
   const ai=infos[i];
   if(!ai){poolMiss++;continue}
   try{
    const pool=PUMP_AMM_SDK.decodePool(ai);
    if(pool.quoteMint.toBase58()!==W)continue;
    decoded.push({
     ...group[i],
     base_vault:pool.poolBaseTokenAccount.toBase58(),
     quote_vault:pool.poolQuoteTokenAccount.toBase58()
    });
   }catch{poolMiss++}
  }

  if(batch%10===0)
   console.log(`[POOL_BATCH] batches=${batch} decoded=${decoded.length} miss=${poolMiss}`);
  await sleep(450);
 }

 console.log(`[POOL_DECODED] ${decoded.length}`);

 const funded=[];
 let vaultMiss=0,vi=0;

 for(const group of chunks(decoded,50)){
  vi++;
  const keys=[];
  for(const r of group){
   keys.push(new PublicKey(r.base_vault),new PublicKey(r.quote_vault));
  }

  const infos=await c.getMultipleAccountsInfo(keys,"confirmed");

  for(let i=0;i<group.length;i++){
   const b=infos[i*2],q=infos[i*2+1];
   if(!b||!q){vaultMiss++;continue}

   try{
    const ba=AccountLayout.decode(b.data).amount;
    const qa=AccountLayout.decode(q.data).amount;
    const base=BigInt(ba.toString()),quote=BigInt(qa.toString());

    if(base>0n && quote>0n)
     funded.push({
      ...group[i],
      base_raw:base.toString(),
      quote_raw:quote.toString(),
      quote_sol:Number(quote)/1e9
     });
   }catch{vaultMiss++}
  }

  if(vi%10===0)
   console.log(`[VAULT_BATCH] batches=${vi} funded=${funded.length} miss=${vaultMiss}`);
  await sleep(500);
 }

 funded.sort((a,b)=>b.quote_sol-a.quote_sol);

 fs.writeFileSync("mtr_100_new_pool_physical_liquidity.json",
  JSON.stringify({
   new_pool_rows:fresh.length,
   decoded_pools:decoded.length,
   funded_pools:funded.length,
   pool_miss:poolMiss,
   vault_miss:vaultMiss,
   rows:funded
  },null,2));

 console.log(`[SUMMARY] new=${fresh.length} decoded=${decoded.length} funded=${funded.length} pool_miss=${poolMiss} vault_miss=${vaultMiss}`);

 for(const r of funded.slice(0,30))
  console.log(`[FUNDED] quote_sol=${r.quote_sol.toFixed(6)} pump=${r.pump_pool} meteora=${r.meteora_count} base=${r.base_mint}`);

 console.log(funded.length?
  "[RESULT] NEW_PHYSICALLY_FUNDED_PUMP_SET_FOUND":
  "[RESULT] NO_NEW_PHYSICALLY_FUNDED_PUMP_SET");
 console.log("[OUTPUT] mtr_100_new_pool_physical_liquidity.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-100] COMPLETE");
})().catch(e=>{
 console.error("[MTR-100] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
