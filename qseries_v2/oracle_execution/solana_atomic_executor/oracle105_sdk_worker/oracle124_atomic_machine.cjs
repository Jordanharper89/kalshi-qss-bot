'use strict';
// ORACLE-119: single-path, atomic PumpSwap <-> Meteora DLMM executor.
// Scanner files provide pool identities only. All price decisions use fresh SDK state.
// No network, signing, or wallet mutation is performed merely by requiring this module.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const ROOT = process.cwd();
const WORKER = __dirname;
const REPORT = path.resolve(ROOT, 'runtime_state/oracle/oracle_live_execution/ORACLE_124_ATOMIC_MACHINE.json');
const JOURNAL = path.resolve(ROOT, 'runtime_state/oracle/oracle_live_execution/ORACLE_124_BROADCAST_JOURNAL.jsonl');
const SOL = 'So11111111111111111111111111111111111111112';
const SIZE = 10000000n; // Fixed initial canary: exactly 0.010 SOL; no adjustable sizing.
const MAX_TX_BYTES = 1232;
const SLIP_BPS = 50n;
const MAX_PRIORITY_MICROLAMPORTS = 25000;
const DEFAULT_PRIORITY_MICROLAMPORTS = 5000;
const MIN_EXCESS_LAMPORTS = 30000n;
const KEY = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
const SIG = /^[1-9A-HJ-NP-Za-km-z]{80,90}$/;
const ALPHABET='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
function encode58(bytes){
 let v=0n;for(const b of bytes)v=(v<<8n)+BigInt(b);
 let text='';while(v>0n){const r=v%58n;text=ALPHABET[Number(r)]+text;v/=58n}
 for(const b of bytes){if(b!==0)break;text='1'+text}
 return text||'1';
}
function decode58(s){
 let n=0n;for(const c of s){const i=ALPHABET.indexOf(c);if(i<0)throw Error('UNSUPPORTED_KEY_FORMAT');n=n*58n+BigInt(i)}
 const a=[];while(n>0n){a.push(Number(n&255n));n>>=8n}a.reverse();
 for(const c of s){if(c!=='1')break;a.unshift(0)}
 return Uint8Array.from(a);
}
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const is429 = e => /429|Too Many Requests|rate.limit/i.test(String(e?.message||e));
const redact = (v) => String(v?.message || v).replace(/(api-key=)[^&\s]+/ig, '$1[REDACTED]').replace(/https?:\/\/[^\s]+/gi, '[RPC_REDACTED]').replace(/(private.?key|secret|authorization)\s*[=:]\s*[^\s,}]+/ig,'$1=[REDACTED]').slice(0,180);
const str = x => x && typeof x.toBase58 === 'function' ? x.toBase58() : String(x || '');
const n = x => BigInt(String(x));
function requirePositive(x, name) { const v=n(x); if(v <= 0n) throw Error('INVALID_'+name); return v; }
function priority(x) { let v=Number(x ?? DEFAULT_PRIORITY_MICROLAMPORTS);if(!Number.isInteger(v)||v<0||v>MAX_PRIORITY_MICROLAMPORTS)throw Error('INVALID_PRIORITY_CAP');return v; }
function budget(size) { if(n(size)!==SIZE) throw Error('FIXED_CANARY_ONLY'); return SIZE; }
function reserveBps(amount,bps) { return n(amount)*(10000n-n(bps))/10000n; }
function quoteGate(size, output, fees, rent, extra) {
 const cost=budget(size)+n(fees)+n(rent)+n(extra);
 const out=n(output); const net=out-cost;
 return {cost:cost.toString(),minimum_proceeds:out.toString(),minimum_net_lamports:net.toString(),admitted:net>MIN_EXCESS_LAMPORTS};
}
function validatePoolRow(r) {
 if(!r || typeof r!=='object') return null;
 const token=r.token, pump=r.pump_pool, dlmm=r.meteora_pool;
 if(!KEY.test(token||'')||!KEY.test(pump||'')||!KEY.test(dlmm||'')||token===SOL||token===pump||token===dlmm||pump===dlmm)return null;
 return {token,pump_pool:pump,meteora_pool:dlmm,reported_tvl:Number(r.reported_tvl||0)||0};
}
function poolCandidates(sourceFiles) {
 const seen=new Set(), out=[];
 for(const f of sourceFiles){
  if(!fs.existsSync(f))continue;
  let j;try{const s=fs.statSync(f);if(s.size>20000000||s.size<2)continue;j=JSON.parse(fs.readFileSync(f,'utf8'));}catch{continue}
  const rows=Array.isArray(j)?j:(Array.isArray(j.rows)?j.rows:[]);
  for(const raw of rows){const r=validatePoolRow(raw);if(!r)continue;
   const id=r.token+'|'+r.pump_pool+'|'+r.meteora_pool;
   if(seen.has(id))continue;seen.add(id);out.push({...r,source:path.relative(ROOT,f)});
  }
 }
 return out;
}
function sources(){
 const base=path.resolve(ROOT,'runtime_state/oracle/solana_atomic_executor');
 const primary=path.resolve(ROOT,'runtime_state/oracle/oracle_live_execution/ORACLE_122_LIVE_REPLENISHED_PAIRS.json');
 return [primary,...['live_hot_book.json','capacity_aware_warm_universe.json','full_surface_replenishment_inventory.json','multi_dlmm_pair_registry.json'].map(f=>path.join(base,f))];
}

function parseWalletSecret(secret,web3){
 const s=String(secret||'').trim();if(!s)throw Error('WALLET_KEY_UNAVAILABLE');
 let bytes;
 if(s[0]==='['){let data;try{data=JSON.parse(s)}catch{throw Error('UNSUPPORTED_KEY_FORMAT')};if(!Array.isArray(data)||data.length!==64||!data.every(i=>Number.isInteger(i)&&i>=0&&i<256))throw Error('UNSUPPORTED_KEY_FORMAT');bytes=Uint8Array.from(data);}
 else {try {bytes=decode58(s)}catch{throw Error('UNSUPPORTED_KEY_FORMAT')}}
 if(bytes.length!==64)throw Error('UNSUPPORTED_KEY_LENGTH');
 return web3.Keypair.fromSecretKey(Uint8Array.from(bytes));
}
function dependencies(){
 // SDKs are loaded only for actual runtime; offline tests have no wallet/SDK requirements.
 const {createRequire}=require('module');
 const req=createRequire(path.join(WORKER,'package.json'));
 const web3=req('@solana/web3.js');
 const spl=req('@solana/spl-token');
 const BN=req('@coral-xyz/anchor').BN;
 const pump=req('@pump-fun/pump-swap-sdk');
 const dlmmPkg=req('@meteora-ag/dlmm');
 const DLMM=dlmmPkg.default||dlmmPkg.DLMM||dlmmPkg;
 return {req,web3,spl,BN,pump,DLMM};
}
function pumpQuoteArgs(state) {
 const {pool,poolBaseAmount,poolQuoteAmount,globalConfig,feeConfig,baseMint,baseMintAccount}=state;
 if(!pool||!poolBaseAmount||!poolQuoteAmount||!globalConfig||!feeConfig)throw Error('PUMP_STATE_INCOMPLETE');
 return {baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,virtualQuoteReserves:pool.virtualQuoteReserves,
  feeBucketsTotal:pool.protocolFees&&pool.creatorFees?pool.protocolFees.add(pool.creatorFees):undefined,
  globalConfig,feeConfig,baseMint,baseMintAccount,coinCreator:pool.coinCreator,creator:pool.creator,
  quoteMint:pool.quoteMint,isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function getPumpMinimumTokens(state,P,BN) {
 if(typeof P.buyQuoteInput!=='function')throw Error('OFFICIAL_EXACT_BUY_QUOTE_MISSING');
 const q=P.buyQuoteInput({...pumpQuoteArgs(state),quote:new BN(SIZE.toString()),slippage:0});
 if(!q?.base)throw Error('OFFICIAL_BUY_QUOTE_SHAPE');
 const raw=requirePositive(q.base,'PUMP_BASE');
 // Exact-input instruction also enforces at least this amount; conservative 50-bps token slippage.
 const min=reserveBps(raw,SLIP_BPS);
 if(min<1n)throw Error('PUMP_MIN_OUTPUT_ZERO');
 return {expected:raw,min};
}
function getPumpMinimumSol(state,P,BN,amount) {
 if(typeof P.sellBaseInput!=='function')throw Error('OFFICIAL_SELL_QUOTE_MISSING');
 const q=P.sellBaseInput({...pumpQuoteArgs(state),base:new BN(String(amount)),slippage:0.5});
 const min=q?.minQuote;
 if(!min)throw Error('OFFICIAL_SELL_QUOTE_SHAPE');
 return requirePositive(min,'PUMP_SELL_OUTPUT');
}
function validateIdentity(state,d,r) {
 const pm=[str(state.pool?.baseMint),str(state.pool?.quoteMint)];
 const dm=[str(d.lbPair?.tokenXMint),str(d.lbPair?.tokenYMint)];
 if(pm[0]!==r.token||pm[1]!==SOL||!dm.includes(r.token)||!dm.includes(SOL))throw Error('LIVE_MINT_IDENTITY_MISMATCH');
 return dm;
}
function dlmmQuote(d,BN,dm,from,to,amount,arrays){
 const swapForY = dm[0]===from && dm[1]===to;
 if(!swapForY && !(dm[1]===from && dm[0]===to))throw Error('DLMM_SWAP_DIRECTION_IDENTITY');
 const q=d.swapQuote(new BN(amount.toString()),swapForY,new BN(SLIP_BPS.toString()),arrays,false);
 const inAmount=requirePositive(q.consumedInAmount,'DLMM_CONSUMED');
 if(inAmount!==amount)throw Error('DLMM_PARTIAL_FILL');
 const minimum=requirePositive(q.minOutAmount,'DLMM_MIN');
 const expected=requirePositive(q.outAmount,'DLMM_EXPECTED');
 if(minimum>expected)throw Error('DLMM_MIN_GT_EXPECTED');
 if(!Array.isArray(q.binArraysPubkey)||q.binArraysPubkey.length===0)throw Error('NO_DLMM_BIN_ARRAY_KEYS');
 return {swapForY,quote:q,minimum,expected};
}
async function hydrate(conn,dep,r,wallet){
 const {web3,DLMM,pump}=dep;
 const online=new pump.OnlinePumpAmmSdk(conn);
 const state=await online.swapSolanaState(new web3.PublicKey(r.pump_pool),wallet);
 const d=await DLMM.create(conn,new web3.PublicKey(r.meteora_pool));
 const dm=validateIdentity(state,d,r);
 return {online,state,d,dm};
}
async function directionQuotes(pool,dep){
 const {BN,pump}=dep;
 const {state,d,dm}=pool;
 const outcomes=[];
 for(const direction of ['PUMP_TO_METEORA','METEORA_TO_PUMP']){
  try{
   if(direction==='PUMP_TO_METEORA'){
    const p=getPumpMinimumTokens(state,pump,BN);
    const forY=dm[0]===str(state.pool.baseMint);
    const arrays=await d.getBinArrayForSwap(forY,8);
    const dl=dlmmQuote(d,BN,dm,str(state.pool.baseMint),SOL,p.min,arrays);
    outcomes.push({direction,minOutput:dl.minimum,tokenInput:p.min,pumpExpected:p.expected,dl,arrays});
   }else{
    const forY=dm[0]===SOL;
    const arrays=await d.getBinArrayForSwap(forY,8);
    const dl=dlmmQuote(d,BN,dm,SOL,str(state.pool.baseMint),SIZE,arrays);
    const pOut=getPumpMinimumSol(state,pump,BN,dl.minimum);
    outcomes.push({direction,minOutput:pOut,tokenInput:dl.minimum,dl,arrays});
   }
  }catch(e){if(is429(e))throw e;outcomes.push({direction,error:redact(e)})}
 }
 return outcomes;
}
function compactIx(ix,dep,wsolAta){
 const {spl,web3}=dep;
 if(ix.programId.equals(web3.ComputeBudgetProgram.programId))return false;
 const isToken=ix.programId.equals(spl.TOKEN_PROGRAM_ID)||ix.programId.equals(spl.TOKEN_2022_PROGRAM_ID);
 // Defer native ATA close until both swap legs finish, avoiding premature WSOL destruction.
 if(isToken&&ix.data?.length&&ix.data[0]===9&&ix.keys?.[0]?.pubkey?.equals(wsolAta))return false;
 return true;
}
function normalizeIxs(ixs,dep,wsolAta){
 const flattened=Array.isArray(ixs)?ixs:ixs?.instructions;
 if(!Array.isArray(flattened))throw Error('OFFICIAL_INSTRUCTION_SHAPE');
 const ans=[],atas=new Set();
 for(const ix of flattened){
  if(!ix?.programId||!ix.keys||!ix.data)throw Error('BAD_NATIVE_INSTRUCTION');
  if(!compactIx(ix,dep,wsolAta))continue;
  if(ix.programId.equals(dep.spl.ASSOCIATED_TOKEN_PROGRAM_ID)){
   const ata=ix.keys[1]?.pubkey?.toBase58();
   if(ata && atas.has(ata))continue;
   if(ata)atas.add(ata);
  }
  ans.push(ix);
 }
 return ans;
}
function mergeIxs(legs,dep,wsolAta){
 const out=[],atas=new Set();
 for(const leg of legs){for(const ix of normalizeIxs(leg,dep,wsolAta)){
   if(ix.programId.equals(dep.spl.ASSOCIATED_TOKEN_PROGRAM_ID)){
    const ata=ix.keys[1]?.pubkey?.toBase58();if(ata&&atas.has(ata))continue;if(ata)atas.add(ata);
   }
   out.push(ix);
 }}
 if(out.length<2)throw Error('MISSING_SWAP_INSTRUCTIONS');
 return out;
}
function altCandidates() {
 const base=path.resolve(ROOT,'runtime_state/oracle');
 const candidates=new Set(); let inspected=0;
 function collect(obj,depth=0) {
  if(depth>9||!obj||typeof obj!=='object')return;
  for(const [k,v] of Object.entries(obj)){
   const key=k.toLowerCase();
   if(/^(alt_address|alt_pubkey|lookup_table_address|lookup_table_pubkey|address_lookup_table|table_pubkey|table_address|alt_account)$/.test(key)){
    if(typeof v==='string'&&KEY.test(v))candidates.add(v);
    if(v && typeof v==='object' && typeof v.address==='string'&&KEY.test(v.address))candidates.add(v.address);
   }
   if(key==='lookup_table'||key==='alt'||key==='lookup_table_account'){
    if(typeof v==='string'&&KEY.test(v))candidates.add(v);
    else if(v&&typeof v==='object'&&typeof v.address==='string'&&KEY.test(v.address))candidates.add(v.address);
   }
   if(v&&typeof v==='object')collect(v,depth+1);
  }
 }
 function walk(dir,depth){
  if(depth>5||!fs.existsSync(dir)||inspected>250)return;
  let entries;try{entries=fs.readdirSync(dir,{withFileTypes:true})}catch{return}
  for(const f of entries){
   if(inspected>250)break;
   const full=path.join(dir,f.name);
   if(f.isDirectory()){walk(full,depth+1);continue;}
   if(!f.isFile()||!/alt|lookup/i.test(f.name)||!f.name.endsWith('.json'))continue;
   try{if(fs.statSync(full).size>500000)continue;inspected++;collect(JSON.parse(fs.readFileSync(full,'utf8')))}catch{}
  }
 }
 walk(base,0);
 return [...candidates].slice(0,6);
}
async function lookupTables(conn,dep){
 const explicit=String(process.env.ORACLE_ATOMIC_ALT||'').trim().split(',').map(s=>s.trim()).filter(Boolean);
 const auto=altCandidates();
 const addresses=[...new Set([...explicit,...auto])].slice(0,6), out=[];
 for(const s of addresses){
  if(!KEY.test(s)){if(explicit.includes(s))throw Error('INVALID_EXPLICIT_ALT_ADDRESS');continue;}
  try{
   const {value}=await conn.getAddressLookupTable(new dep.web3.PublicKey(s),{commitment:'confirmed'});
   if(!value||!value.state?.addresses?.length){if(explicit.includes(s))throw Error('LOOKUP_TABLE_NOT_USABLE');continue;}
   out.push(value);
  }catch(e){if(is429(e))throw e;if(explicit.includes(s))throw e;}
 }
 console.log('[ALT]',out.length,'loaded from existing configuration; no extensions or mutations');
 return out;
}

async function prepareInstructions(conn,dep,pool,choice,wallet){
 const {pump,BN,web3,spl}=dep;
 const sol=spl.NATIVE_MINT;
 const base=new web3.PublicKey(str(pool.state.pool.baseMint));
 const state=pool.state,d=pool.d,dl=choice.dl;
 const nativeAta=spl.getAssociatedTokenAddressSync(sol,wallet,false,spl.TOKEN_PROGRAM_ID);
 const baseInfo=await conn.getAccountInfo(base,'confirmed');
 if(!baseInfo||!baseInfo.owner.equals(spl.TOKEN_PROGRAM_ID))throw Error('TOKEN2022_NOT_CERTIFIED_FOR_EXECUTION');
 const baseAta=spl.getAssociatedTokenAddressSync(base,wallet,false,spl.TOKEN_PROGRAM_ID);
 const nativeExisting=await conn.getAccountInfo(nativeAta,'confirmed');
 const baseExisting=await conn.getAccountInfo(baseAta,'confirmed');
 const extras=[];
 if(!nativeExisting)extras.push(spl.createAssociatedTokenAccountIdempotentInstruction(wallet,nativeAta,wallet,sol));
 if(!baseExisting)extras.push(spl.createAssociatedTokenAccountIdempotentInstruction(wallet,baseAta,wallet,base));
 let pIxs;
 if(choice.direction==='PUMP_TO_METEORA'){
  if(typeof pump.PUMP_AMM_SDK?.buyExactQuoteInV2Instructions!=='function')throw Error('PUMP_EXACT_QUOTE_BUY_V2_UNAVAILABLE');
  pIxs=await pump.PUMP_AMM_SDK.buyExactQuoteInV2Instructions(state,new BN(SIZE.toString()),new BN(choice.tokenInput.toString()));
 }else{
  if(typeof pump.PUMP_AMM_SDK?.sellInstructions!=='function')throw Error('OFFICIAL_PUMP_SELL_BUILDER_MISMATCH_NO_ATOMIC_SIMULATION');
  pIxs=await pump.PUMP_AMM_SDK.sellInstructions(state,new BN(choice.tokenInput.toString()),new BN(choice.minOutput.toString()));
 }
 const dlTx=await d.swap({inToken:choice.direction==='PUMP_TO_METEORA'?base:sol,
  outToken:choice.direction==='PUMP_TO_METEORA'?sol:base,
  inAmount:dl.quote.consumedInAmount,minOutAmount:dl.quote.minOutAmount,
  lbPair:d.pubkey,user:wallet,binArraysPubkey:dl.quote.binArraysPubkey});
 const trade=choice.direction==='PUMP_TO_METEORA'?[pIxs,dlTx.instructions]:[dlTx.instructions,pIxs];
 let ixs=mergeIxs([extras,...trade],dep,nativeAta);
 // Cleanup newly-created native ATA at the end to realize WSOL into wallet SOL.
 if(!nativeExisting)ixs.push(spl.createCloseAccountInstruction(nativeAta,wallet,wallet));
 const rents=(baseExisting?0n:BigInt(await conn.getMinimumBalanceForRentExemption(165,'confirmed')));
 // Extra safety reserve when native ATA must be created (rent is returned on closure).
 return {ixs,rent:rents,wsolAta:nativeAta,createdNative:!nativeExisting,createdBase:!baseExisting};
}
async function assemble(conn,dep,ixs,feePayer,alts){
 const {web3}=dep;
 const micro=priority(process.env.ORACLE_PRIORITY_MICROLAMPORTS);
 const compute=[web3.ComputeBudgetProgram.setComputeUnitLimit({units:1300000}),web3.ComputeBudgetProgram.setComputeUnitPrice({microLamports:micro})];
 const blockhash=await conn.getLatestBlockhash('confirmed');
 const message=new web3.TransactionMessage({payerKey:feePayer,recentBlockhash:blockhash.blockhash,instructions:[...compute,...ixs]}).compileToV0Message(alts);
 const tx=new web3.VersionedTransaction(message);
 const byteLength=tx.serialize().length;
 if(byteLength>MAX_TX_BYTES)throw Error('ATOMIC_V0_PACKET_OVER_1232_BYTES:'+byteLength);
 let fee=await conn.getFeeForMessage(message,'confirmed');
 const lamports=fee?.value;
 if(!Number.isInteger(lamports)||lamports<5000)throw Error('RPC_MESSAGE_FEE_UNKNOWN');
 const cuReserve=BigInt(Math.ceil(1300000*micro/1e6));
 // getFeeForMessage already includes priority fee on many RPC versions.
 // Reserve both reported fee and priority cost again to err strictly conservative.
 const totalFee=BigInt(lamports)+cuReserve;
 return {tx,blockhash,byteLength,fee:totalFee,ixCount:ixs.length,cuReserve};
}
async function simulate(conn,built,keypair){
 if(keypair)built.tx.sign([keypair]);
 const result=await conn.simulateTransaction(built.tx,{sigVerify:!!keypair,replaceRecentBlockhash:false,commitment:'confirmed'});
 if(result.value?.err)throw Error('ATOMIC_SIMULATION_FAILED:'+JSON.stringify(result.value.err).slice(0,100));
 const units=result.value?.unitsConsumed;
 if(!Number.isInteger(units)||units<1||units>1300000)throw Error('UNVERIFIED_COMPUTE_CONSUMPTION');
 return {unitsConsumed:units,logs_count:(result.value.logs||[]).length,signed:!!keypair};
}
async function tokenBalanceOrZero(conn,account){
 try{const r=await conn.getTokenAccountBalance(account,'confirmed');return BigInt(r.value.amount)}
 catch(e){if(is429(e))throw e;if(/could not find account|Invalid param|does not exist|AccountNotFound/i.test(String(e?.message||e)))return 0n;throw e}
}
function recordReport(report){
 const safe=JSON.stringify(report,(_k,v)=>typeof v==='bigint'?v.toString():v,2);
 fs.mkdirSync(path.dirname(REPORT),{recursive:true});
 const tmp=REPORT+'.tmp';fs.writeFileSync(tmp,safe,{encoding:'utf8',mode:0o600});fs.renameSync(tmp,REPORT);
}
function appendJournal(row){
 fs.mkdirSync(path.dirname(JOURNAL),{recursive:true});
 const fd=fs.openSync(JOURNAL,'a',0o600);
 try{fs.writeSync(fd,JSON.stringify({...row,unix:Math.floor(Date.now()/1000)})+'\n');fs.fsyncSync(fd)}finally{fs.closeSync(fd)}
}
function unresolvedJournal(){
 if(!fs.existsSync(JOURNAL))return [];
 const content=fs.readFileSync(JOURNAL,'utf8').split(/\r?\n/).filter(Boolean);
 if(content.length>100000)throw Error('BROADCAST_JOURNAL_TOO_LONG');
 const attempts=new Map(),resolved=new Set();
 for(const s of content){let row;try{row=JSON.parse(s)}catch{throw Error('BROADCAST_JOURNAL_CORRUPTED')};
  if(!row.signature||!SIG.test(row.signature))throw Error('BROADCAST_JOURNAL_INVALID_SIGNATURE');
  if(row.event==='BROADCAST_INTENT')attempts.set(row.signature,row);
  if(row.event==='CONFIRMED'||row.event==='CHAIN_FAILED')resolved.add(row.signature);
 }
 return [...attempts.values()].filter(row=>!resolved.has(row.signature));
}
function rowPublic(r,direction){return {token:r.token,pump_pool:r.pump_pool,meteora_pool:r.meteora_pool,direction}}
async function oneCandidate(conn,dep,r,wallet,keypair,trade,alts){
 const res={...rowPublic(r,null),status:'HOLD',directions:[]};
 let pool;
 try{pool=await hydrate(conn,dep,r,wallet);}catch(e){if(is429(e))throw e;res.reason='HYDRATE_OR_IDENTITY_FAILED';res.detail=redact(e);return res;}
 const qs=await directionQuotes(pool,dep);
 for(const c of qs){
  if(c.error){res.directions.push({direction:c.direction,status:'REJECT_QUOTE',reason:c.error});continue;}
  const gross=quoteGate(SIZE,c.minOutput,0,0,0);
  if(!gross.admitted){res.directions.push({direction:c.direction,status:'REJECT_GROSS',min_sol_out:c.minOutput.toString(),gross_min_delta:gross.minimum_net_lamports,break_even_lamports:SIZE.toString(),min_required_output_lamports:(SIZE+MIN_EXCESS_LAMPORTS).toString()});continue;}
  const q={direction:c.direction,status:'HOLD',min_sol_out:c.minOutput.toString(),gross_min_delta:gross.minimum_net_lamports};res.directions.push(q);
  try{
   const plan=await prepareInstructions(conn,dep,pool,c,wallet);
   const built=await assemble(conn,dep,plan.ixs,wallet,alts);
   const net=quoteGate(SIZE,c.minOutput,built.fee,plan.rent,10000n);
   q.net_min_lamports=net.minimum_net_lamports;
   q.packet_bytes=built.byteLength;
   q.instruction_count=built.ixCount;
   if(!net.admitted){q.status='REJECT_NET_AFTER_FEES_AND_RENT';continue;}
   const start=Date.now();
   // Dry-run always unsigned; signing requires explicit --trade plus full preflight.
   const sim=await simulate(conn,built,null);
   q.simulation=sim;
   q.status='UNSIGNED_SIM_PASS';
   if(!trade){q.reason='READ_ONLY_NO_BROADCAST';continue;}
   // Strict freshness: before any signing, rebuild the live quote and transaction from new on-chain state.
   if(!keypair)throw Error('LIVE_WALLET_KEY_REQUIRED');
   if(Date.now()-start>10000)throw Error('SIMULATION_TOO_OLD');
   const fresh=await hydrate(conn,dep,r,wallet);
   const refreshed=(await directionQuotes(fresh,dep)).find(x=>x.direction===c.direction);
   if(!refreshed||refreshed.error)throw Error('REFRESHED_QUOTE_UNAVAILABLE');
   if(refreshed.minOutput<c.minOutput)throw Error('REFRESHED_QUOTE_DETERIORATED');
   const plan2=await prepareInstructions(conn,dep,fresh,refreshed,wallet);
   const built2=await assemble(conn,dep,plan2.ixs,wallet,alts);
   const net2=quoteGate(SIZE,refreshed.minOutput,built2.fee,plan2.rent,10000n);
   if(!net2.admitted)throw Error('REFRESHED_NET_NEGATIVE');
   const funded=await conn.getBalance(wallet,'confirmed');
   if(BigInt(funded)<SIZE+8000000n)throw Error('INSUFFICIENT_SOL_FOR_CANARY_AND_FEES');
   const signedSim=await simulate(conn,built2,keypair);
   q.signed_simulation=signedSim;q.status='SIGNED_SIM_PASS';
   const beforeWrapped=await tokenBalanceOrZero(conn,plan2.wsolAta);
   // Durable intent before first broadcast. Unknown confirmation MUST NEVER cause an automatic resend.
   const plannedSig=encode58(built2.tx.signatures[0]);
   q.signature=plannedSig;q.status='BROADCAST_INTENT';
   appendJournal({event:'BROADCAST_INTENT',signature:plannedSig,token:r.token,direction:c.direction,canary_lamports:SIZE.toString()});
   const returned=await conn.sendRawTransaction(built2.tx.serialize(),{skipPreflight:false,maxRetries:0,preflightCommitment:'confirmed'});
   if(returned!==plannedSig)throw Error('BROADCAST_SIGNATURE_MISMATCH');
   q.status='SENT';
   const confirmed=await conn.confirmTransaction({signature:plannedSig,blockhash:built2.blockhash.blockhash,lastValidBlockHeight:built2.blockhash.lastValidBlockHeight},'confirmed');
   if(confirmed.value.err){appendJournal({event:'CHAIN_FAILED',signature:plannedSig});throw Error('TRANSACTION_CONFIRMED_ERROR');}
   q.status='CONFIRMED';
   const txMeta=await conn.getTransaction(plannedSig,{commitment:'confirmed',maxSupportedTransactionVersion:0});
   if(!txMeta?.meta||txMeta.meta.err)throw Error('CONFIRMED_META_MISSING');
   const index=txMeta.transaction.message.staticAccountKeys.findIndex(x=>x.equals(wallet));
   if(index<0)throw Error('FEE_PAYER_INDEX_MISSING');
   const realized=BigInt(txMeta.meta.postBalances[index])-BigInt(txMeta.meta.preBalances[index]);
   const afterWrapped=await tokenBalanceOrZero(conn,plan2.wsolAta);
   const realizedTotal=realized+(afterWrapped-beforeWrapped);
   q.realized_wallet_sol_delta=realized.toString();
   q.realized_combined_sol_wsol_delta=realizedTotal.toString();
   q.network_fee_lamports=String(txMeta.meta.fee);
   q.status=realizedTotal>0n?'POSITIVE_REALIZED_SOL_PLUS_WSOL':'CONFIRMED_NONPOSITIVE_SOL_PLUS_WSOL';
   appendJournal({event:'CONFIRMED',signature:plannedSig,realized_wallet_sol_delta:realized.toString(),realized_combined_sol_wsol_delta:realizedTotal.toString()});
   res.status='TRADE_CONFIRMED';return res;
  }catch(e){
   if(q.signature && q.status!=='HOLD'){
    q.status='BROADCAST_UNRESOLVED_STOP';q.reason=redact(e);
    res.status='STOP_BROADCAST_UNRESOLVED';return res;
   }
   q.status='HOLD';q.reason=redact(e);
   if(is429(e))throw e;
  }
 }
 res.status=res.directions.some(x=>x.status==='UNSIGNED_SIM_PASS')?'SIMULATED_CANDIDATE_ONLY':'HOLD_NO_EXECUTABLE_PROFIT';
 return res;
}
// ORACLE-124 independent selection engine. Identity does not imply fresh liquidity.
const identity = r => r.token+'|'+r.pump_pool+'|'+r.meteora_pool;
function stageScore(stage){return ({HOT:0,ACTIVE:1,COOLING:3,RECHECK:4,OBSERVE:6,RETIRED:9})[stage] ?? 6;}
function sourceScore(source){return ({UNIVERSAL_LIVE_CROSSLIST:0,MRIYA_REPLENISHED:1,HISTORICAL_IDENTITY_ONLY:5})[source] ?? 5;}
function selectionScore(r, item, now){
 const state=item||{};
 const cooldown=Math.max(0,(state.cooldownUntil||0)-now);
 // Cooldowns are real exclusion windows, not just ranking penalties.
 if(cooldown>0)return Infinity;
 const previous=state.lastChecked||0;
 const elapsed=previous?Math.max(0,now-previous):3600000;
 const ageCredit=Math.min(300,elapsed/1000);
 const activity=Math.max(0,Math.min(500,Number(r.pump_activity)||0));
 const fail=Math.min(8,state.failStreak||0);
 const st=stageScore(r.lifecycle);
 const src=sourceScore(r.source);
 // Fairness: never-checked and long-waiting identities get substantial priority.
 return src*13 + st*6 + fail*12 - Math.min(160,ageCredit) - Math.min(40,activity*2);
}
function selectBatch(cands,states,count,now){
 const eligible=cands.map((r,i)=>({r,i,id:identity(r),score:selectionScore(r,states.get(identity(r)),now)})).filter(x=>Number.isFinite(x.score));
 eligible.sort((a,b)=>a.score-b.score || a.id.localeCompare(b.id));
 // A repeated token may have multiple pool pairs. Spread coverage across tokens first.
 const seenTokens=new Set(),batch=[];
 for(const entry of eligible){if(seenTokens.has(entry.r.token))continue;seenTokens.add(entry.r.token);batch.push(entry);if(batch.length===count)break;}
 if(batch.length<count)for(const entry of eligible){if(batch.some(x=>x.id===entry.id))continue;batch.push(entry);if(batch.length===count)break;}
 return batch.map(x=>x.r);
}
function isBidirectionallyQuoted(row){
 if(!row||!Array.isArray(row.directions)||row.directions.length!==2)return false;
 const dirs=new Set();
 for(const d of row.directions){
  if(!['PUMP_TO_METEORA','METEORA_TO_PUMP'].includes(d.direction))return false;
  if(d.status==='REJECT_QUOTE'||d.status==='HOLD'||!d.min_sol_out)return false;
  try{if(BigInt(d.min_sol_out)<=0n)return false;}catch{return false;}
  dirs.add(d.direction);
 }
 return dirs.size===2;
}
function observeResult(state,row,now){
 const next={...(state||{}),lastChecked:now};
 const failed=(row.status==='HOLD_ERROR'||row.status==='HOLD_NO_EXECUTABLE_PROFIT' || row.status==='HOLD');
 const quotefail=row.directions?.some(d=>d.status==='REJECT_QUOTE')||row.status==='HYDRATE_OR_IDENTITY_FAILED';
 if(isBidirectionallyQuoted(row)){
  next.failStreak=0;next.cooldownUntil=0;next.lastFullQuote=now;
 }else if(failed){
  next.failStreak=Math.min(12,(next.failStreak||0)+1);
  const seconds=quotefail?Math.min(300,20*2**Math.min(4,next.failStreak-1)):Math.min(90,15*next.failStreak);
  next.cooldownUntil=now+seconds*1000;
 }
 return next;
}
async function run(mode){
 const dep=dependencies(),{web3}=dep;
 if(!process.env.SOLANA_RPC_URL||!/^https:\/\//.test(process.env.SOLANA_RPC_URL))throw Error('SOLANA_RPC_URL_HTTPS_REQUIRED');
 const trade=mode==='trade';
 if(trade)throw Error('LIVE_EXECUTION_NOT_CERTIFIED_NO_SIGN_OR_BROADCAST');
 const secret=process.env.QSB_SOLANA_PRIVATE_KEY||'';
 let wallet;
 if(secret)wallet=parseWalletSecret(secret,web3).publicKey;
 else if(process.env.ORACLE_PUBLIC_KEY)wallet=new web3.PublicKey(process.env.ORACLE_PUBLIC_KEY);
 else throw Error('WALLET_PUBLIC_KEY_REQUIRED');
 const conn=new web3.Connection(process.env.SOLANA_RPC_URL,{commitment:'confirmed',disableRetryOnRateLimit:true});
 let alts=[];
 try{alts=await lookupTables(conn,dep)}catch(e){if(!is429(e))throw e;console.log('[RPC_BACKOFF] ALT lookup rate limited; retaining no ALTs');await sleep(15000)}
 const once=process.argv.includes('--once');
 const perCycle=Math.max(1,Math.min(12,Number(process.env.ORACLE124_PAIRS_PER_CYCLE||4)||4));
 const freshWindowMs=120000;
 const pause=Math.max(1200,Number(process.env.ORACLE124_RPC_GAP_MS||2200));
 const checkedState=new Map(),verified=new Map();
 let cycle=0,rateStreak=0,former=new Set();
 console.log('[ORACLE-124] mode=watch dynamic_universal_mriya_scheduler=ACTIVE scanner=UNCHANGED canary=0.010_SOL trade_enabled=false');
 while(true){
  cycle++;
  const cands=poolCandidates(sources());
  if(!cands.length)throw Error('NO_CROSSLISTED_POOL_IDENTITIES');
  const current=new Set(cands.map(identity));
  const added=[...current].filter(id=>!former.has(id)).length;
  const deleted=[...former].filter(id=>!current.has(id)).length;
  if(cycle===1||added||deleted)console.log('[INVENTORY_RELOADED] candidates='+cands.length+' new='+added+' retired_or_removed='+deleted);
  former=current;
  // Invalidate quote verification when a pool identity falls out of active inventory.
  for(const id of verified.keys())if(!current.has(id))verified.delete(id);
  // Only current pair identities can become ready, and only by two exact live quotes.
  const selected=selectBatch(cands,checkedState,perCycle,Date.now());
  const report={revision:'ORACLE-124',mode:'watch',cycle,status:'RUNNING',timestamp_unix:Math.floor(Date.now()/1000),
   scanner_modified:false,source_role:'IDENTITY_ONLY_LIVE_SDK_QUOTES',candidate_count:cands.length,
   signing_enabled:false,broadcast_enabled:false,canary_lamports:SIZE.toString(),selected_ids:selected.map(identity),rows:[]};
  if(selected.length===0)console.log('[PAIR_COOLDOWN] all candidates temporarily cooling; keeping both scanners and replenishment running');
  for(const r of selected){
   const id=identity(r);
   try{
    const row=await oneCandidate(conn,dep,r,wallet,null,false,alts);
    report.rows.push(row);
    checkedState.set(id,observeResult(checkedState.get(id),row,Date.now()));
    if(isBidirectionallyQuoted(row))verified.set(id,Date.now());
    else verified.delete(id);
    const statuses=(row.directions||[]).map(d=>d.direction+':'+d.status).join('|');
    console.log('[PAIR]',r.token.slice(0,12),row.status,statuses,'source='+String(r.source||'UNKNOWN'));
   }catch(e){
    report.rows.push({token:r.token,status:'HOLD_ERROR',reason:redact(e)});
    checkedState.set(id,observeResult(checkedState.get(id),{status:'HOLD_ERROR',directions:[]},Date.now()));
    verified.delete(id);
    if(is429(e)){report.status='RPC_RATE_LIMIT_BACKOFF';rateStreak=Math.min(rateStreak+1,7);break;}
   }
   await sleep(pause);
  }
  for(const [id,stamp] of verified)if(Date.now()-stamp>freshWindowMs)verified.delete(id);
  if(report.status==='RUNNING')report.status=report.rows.some(r=>r.status==='SIMULATED_CANDIDATE_ONLY')?'POSITIVE_UNSIGNED_SIMULATION_ONLY':'NO_VERIFIED_EXECUTABLE_PROFIT';
  const within=selected.filter(r=>checkedState.get(identity(r))?.cooldownUntil>Date.now()).length;
  const quoted=report.rows.flatMap(x=>x.directions||[]).filter(d=>d.min_sol_out);
  const gaps=quoted.map(d=>BigInt(d.min_sol_out)-SIZE);
  const rejects=report.rows.flatMap(x=>x.directions||[]).reduce((acc,d)=>{acc[d.status]=(acc[d.status]||0)+1;return acc},{});
  report.economics={base_lamports:SIZE.toString(),min_profit_threshold_lamports:MIN_EXCESS_LAMPORTS.toString(),quoted_direction_count:quoted.length,best_gross_lamports:gaps.length?gaps.reduce((a,b)=>a>b?a:b).toString():null,worst_gross_lamports:gaps.length?gaps.reduce((a,b)=>a<b?a:b).toString():null,rejection_counts:rejects,signing_disabled:true};
  console.log('[ECONOMICS]','quoted='+quoted.length,'best_gross_lamports='+report.economics.best_gross_lamports,'rejections='+JSON.stringify(rejects));
  report.verified_bidirectional_quotable_pairs=verified.size;
  report.fresh_pair_gate=verified.size>=28?'MET':'NOT_MET';
  report.target_fresh_pairs=28;
  report.distinct_pool_identities_scanned=checkedState.size;
  report.cooldown_pairs=[...checkedState.values()].filter(s=>s.cooldownUntil>Date.now()).length;
  report.selection_is_fair_across_tokens=true;
  report.fresh_pair_count_is_not_execution_certification=true;
  recordReport(report);
  console.log('[CYCLE]',cycle,report.status,'checked='+report.rows.length,'distinct_ever_checked='+checkedState.size,
   '[BIDIRECTIONAL_QUOTES]',verified.size+'/28','cooldown='+report.cooldown_pairs,'[REPORT]',REPORT);
  if(once)return;
  if(report.status==='RPC_RATE_LIMIT_BACKOFF'){
   const delay=Math.min(120000,8000*2**(rateStreak-1));
   console.log('[RPC_429_RECOVERY] retry_seconds='+delay/1000+' consecutive='+rateStreak);
   await sleep(delay);
  }else{
   rateStreak=0;
   await sleep(Math.max(3000,Number(process.env.ORACLE124_CYCLE_GAP_MS||5000)));
  }
 }
}

if(require.main===module){
 const mode=process.argv.includes('--trade')?'trade':process.argv.includes('--watch')?'watch':null;
 if(!mode){console.error('Usage: node oracle123_atomic_machine.cjs --watch [--once] OR --trade');process.exitCode=2}
 else run(mode).catch(e=>{console.error('[HOLD]',redact(e));process.exitCode=1});
}
module.exports={identity,selectBatch,isBidirectionallyQuoted,observeResult,SIZE,priority,budget,reserveBps,encode58,decode58,quoteGate,validatePoolRow,poolCandidates,altCandidates,redact,is429,mergeIxs,compactIx,unresolvedJournal,getPumpMinimumTokens,getPumpMinimumSol,dlmmQuote};
