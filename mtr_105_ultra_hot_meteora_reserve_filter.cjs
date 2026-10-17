const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const {AccountLayout}=require("@solana/spl-token");

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const PROG=new PublicKey("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const c=new Connection(RPC,"confirmed");
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function deriveReserve(token,pair){
 return PublicKey.findProgramAddressSync(
  [pair.toBuffer(),token.toBuffer()],PROG
 )[0];
}
function chunks(a,n){
 const out=[];
 for(let i=0;i<a.length;i+=n)out.push(a.slice(i,i+n));
 return out;
}

(async()=>{
 console.log("[MTR-105] START");
 console.log("[SCOPE] ULTRA-HOT Meteora physical reserve batch filter");

 const src="mtr_102_tiered_replenishment_manifest.json";
 if(!fs.existsSync(src))throw Error("MTR_102_NOT_FOUND");

 const j=JSON.parse(fs.readFileSync(src,"utf8"));
 const links=Array.isArray(j.ultra_hot_links)?j.ultra_hot_links:[];
 console.log(`[ULTRA_HOT_LINKS] ${links.length}`);

 const rows=[];
 let miss=0,batch=0;

 for(const group of chunks(links,50)){
  batch++;
  const keys=[],meta=[];

  for(const r of group){
   const pair=new PublicKey(r.meteora_pool);
   const base=new PublicKey(r.base_mint);
   const baseReserve=deriveReserve(base,pair);
   const wsolReserve=deriveReserve(W,pair);
   keys.push(baseReserve,wsolReserve);
   meta.push({r,baseReserve,wsolReserve});
  }

  const infos=await c.getMultipleAccountsInfo(keys,"confirmed");

  for(let i=0;i<meta.length;i++){
   const b=infos[i*2],w=infos[i*2+1];
   if(!b||!w){miss++;continue}

   try{
    const baseRaw=BigInt(AccountLayout.decode(b.data).amount.toString());
    const wsolRaw=BigInt(AccountLayout.decode(w.data).amount.toString());

    rows.push({
     tier:"ULTRA_HOT",
     pump_pool:meta[i].r.pump_pool,
     meteora_pool:meta[i].r.meteora_pool,
     base_mint:meta[i].r.base_mint,
     pump_quote_sol:meta[i].r.quote_sol,
     meteora_base_raw:baseRaw.toString(),
     meteora_wsol_raw:wsolRaw.toString(),
     meteora_wsol_sol:Number(wsolRaw)/1e9,
     base_reserve:meta[i].baseReserve.toBase58(),
     wsol_reserve:meta[i].wsolReserve.toBase58()
    });
   }catch{miss++}
  }

  if(batch%10===0)
   console.log(`[BATCH] batches=${batch} read=${rows.length} miss=${miss}`);

  await sleep(500);
 }

 rows.sort((a,b)=>b.meteora_wsol_sol-a.meteora_wsol_sol);

 const TH=[0,0.01,0.025,0.05,0.1,0.25,0.5,1,2,5,10];
 const surface=[];

 for(const t of TH){
  const keep=rows.filter(r=>
   BigInt(r.meteora_base_raw)>0n &&
   r.meteora_wsol_sol>=t
  );
  const pumps=new Set(keep.map(r=>r.pump_pool)).size;
  const bases=new Set(keep.map(r=>r.base_mint)).size;
  surface.push({min_wsol_sol:t,links:keep.length,pumps,bases});
  console.log(
   `[THRESHOLD] min_wsol=${t} links=${keep.length} pumps=${pumps} bases=${bases}`
  );
 }

 const physical=rows.filter(r=>
  BigInt(r.meteora_base_raw)>0n &&
  BigInt(r.meteora_wsol_raw)>0n
 );

 fs.writeFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json",
  JSON.stringify({
   input_links:links.length,
   readable_links:rows.length,
   physical_links:physical.length,
   misses:miss,
   thresholds:surface,
   rows:physical
  },null,2));

 console.log(
  `[SUMMARY] input=${links.length} readable=${rows.length} physical=${physical.length} miss=${miss}`
 );

 for(const r of physical.slice(0,25))
  console.log(
   `[TOP] meteora_wsol=${r.meteora_wsol_sol.toFixed(6)} pump=${r.pump_pool} meteora=${r.meteora_pool} base=${r.base_mint}`
  );

 console.log(physical.length?
  "[RESULT] ULTRA_HOT_METEORA_PHYSICAL_SET_FOUND":
  "[RESULT] NO_ULTRA_HOT_METEORA_PHYSICAL_SET");

 console.log("[OUTPUT] mtr_105_ultra_hot_meteora_reserve_filter.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-105] COMPLETE");
})().catch(e=>{
 console.error("[MTR-105] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
