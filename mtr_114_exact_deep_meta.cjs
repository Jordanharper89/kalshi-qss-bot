const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112";
const c=new Connection(RPC,"confirmed"),sleep=m=>new Promise(r=>setTimeout(r,m));

(async()=>{
 console.log("[MTR-114-META] START");
 const j=JSON.parse(fs.readFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json","utf8"));
 const src=(j.rows||[]).filter(r=>Number(r.meteora_wsol_sol)>=1)
   .sort((a,b)=>Number(b.meteora_wsol_sol)-Number(a.meteora_wsol_sol));

 const chosen=[],seen=new Set();
 for(const r of src){
   if(seen.has(r.base_mint))continue;
   seen.add(r.base_mint);
   chosen.push(r);
   if(chosen.length===12)break;
 }

 const out=[];
 for(let i=0;i<chosen.length;i++){
   const r=chosen[i];
   try{
     const m=await DLMM.create(c,new PublicKey(r.meteora_pool));
     const x=String(m.tokenX.mint.address),y=String(m.tokenY.mint.address);
     if(!([x,y].includes(W)&&[x,y].includes(r.base_mint)))
       throw Error("PAIR_MINT_MISMATCH");
     out.push({...r,token_x:x,token_y:y});
     console.log(`[META] ${out.length}/12 base=${r.base_mint} pump=${r.pump_pool} meteora=${r.meteora_pool}`);
   }catch(e){
     console.log(`[META_HOLD] base=${r.base_mint} reason=${String(e.message||e)}`);
   }
   await sleep(600);
 }

 fs.writeFileSync("mtr_114_exact_deep_meta.json",JSON.stringify(out,null,2));
 console.log(`[META_SUMMARY] requested=12 exact=${out.length}`);
 console.log("[MTR-114-META] COMPLETE");
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
