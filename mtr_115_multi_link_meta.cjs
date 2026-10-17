const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112";
const c=new Connection(RPC,"confirmed"),sleep=m=>new Promise(r=>setTimeout(r,m));

(async()=>{
 console.log("[MTR-115-META] START");
 const j=JSON.parse(fs.readFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json","utf8"));
 const src=(j.rows||[]).filter(r=>Number(r.meteora_wsol_sol)>=1)
  .sort((a,b)=>Number(b.meteora_wsol_sol)-Number(a.meteora_wsol_sol));

 const groups=new Map();
 for(const r of src){
  if(!groups.has(r.pump_pool))groups.set(r.pump_pool,[]);
  const a=groups.get(r.pump_pool);
  if(!a.some(x=>x.meteora_pool===r.meteora_pool))a.push(r);
 }
 const eligible=[...groups.values()].filter(x=>x.length>=2)
  .sort((a,b)=>Number(b[0].meteora_wsol_sol)-Number(a[0].meteora_wsol_sol));

 const chosen=[];
 for(const g of eligible){
  for(const r of g.slice(0,3)){chosen.push(r);if(chosen.length>=12)break}
  if(chosen.length>=12)break;
 }
 if(chosen.length<8)throw Error("INSUFFICIENT_MULTI_LINK_GROUPS");

 const out=[];
 for(let i=0;i<chosen.length;i++){
  const r=chosen[i];
  try{
   const m=await DLMM.create(c,new PublicKey(r.meteora_pool));
   const x=String(m.tokenX.mint.address),y=String(m.tokenY.mint.address);
   if(!([x,y].includes(W)&&[x,y].includes(r.base_mint)))throw Error("PAIR_MINT_MISMATCH");
   out.push({...r,token_x:x,token_y:y});
   console.log(`[META] ${out.length}/${chosen.length} pump=${r.pump_pool} meteora=${r.meteora_pool}`);
  }catch(e){console.log(`[META_HOLD] ${String(e.message||e)}`)}
  await sleep(650);
 }
 fs.writeFileSync("mtr_115_multi_link_meta.json",JSON.stringify(out,null,2));
 console.log(`[META_SUMMARY] selected=${chosen.length} exact=${out.length}`);
 console.log("[MTR-115-META] COMPLETE");
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
