const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112";
const c=new Connection(RPC,"confirmed"),sleep=m=>new Promise(r=>setTimeout(r,m));
(async()=>{
 console.log("[MTR-118-META] START");
 const j=JSON.parse(fs.readFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json","utf8"));
 const src=(j.rows||[]).filter(r=>Number(r.meteora_wsol_sol)>=1)
  .sort((a,b)=>Number(b.meteora_wsol_sol)-Number(a.meteora_wsol_sol));
 const by=new Map();
 for(const r of src){
  if(!by.has(r.pump_pool))by.set(r.pump_pool,[]);
  const g=by.get(r.pump_pool);
  if(!g.some(x=>x.meteora_pool===r.meteora_pool))g.push(r);
 }
 const chosen=[];
 for(const g of by.values()){
  for(const r of g.slice(0,2)){chosen.push(r);if(chosen.length>=24)break}
  if(chosen.length>=24)break;
 }
 if(chosen.length<16)throw Error("INSUFFICIENT_TARGET_ROUTES:"+chosen.length);
 const out=[];
 for(let i=0;i<chosen.length;i++){
  const r=chosen[i];
  for(let a=1;a<=6;a++){
   try{
    const m=await DLMM.create(c,new PublicKey(r.meteora_pool));
    const x=String(m.tokenX.mint.address),y=String(m.tokenY.mint.address);
    if(!([x,y].includes(W)&&[x,y].includes(r.base_mint)))throw Error("PAIR_MINT_MISMATCH");
    out.push({...r,token_x:x,token_y:y});break;
   }catch(e){
    if(a===6)console.log(`[META_HOLD] pump=${r.pump_pool} reason=${String(e.message||e)}`);
    else await sleep(Math.min(600*(2**(a-1)),5000));
   }
  }
  console.log(`[META_PROGRESS] ${i+1}/${chosen.length} exact=${out.length}`);
  await sleep(500);
 }
 fs.writeFileSync("mtr_118_target_only_24_meta.json",JSON.stringify(out,null,2));
 console.log(`[META_SUMMARY] selected=${chosen.length} exact=${out.length}`);
 console.log("[MTR-118-META] COMPLETE");
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
