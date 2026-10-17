'use strict';
// ORACLE-119: single-path, atomic PumpSwap <-> Meteora DLMM executor.
// Scanner files provide pool identities only. All price decisions use fresh SDK state.
// No network, signing, or wallet mutation is performed merely by requiring this module.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const ROOT = process.cwd();
const WORKER = __dirname;
const REPORT = path.resolve(ROOT, 'runtime_state/oracle/oracle_live_execution/ORACLE_120_ATOMIC_MACHINE.json');
const JOURNAL = path.resolve(ROOT, 'runtime_state/oracle/oracle_live_execution/ORACLE_120_BROADCAST_JOURNAL.jsonl');
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
 const primary=path.resolve(ROOT,'runtime_state/oracle/oracle_live_execution/ORACLE_120_LIVE_REPLENISHED_PAIRS.json');
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
  if(typeof pump.PUMP_AMM_SDK?.sellInstructions!=='function')throw Error('PUMP_SELL_EXPLICIT_UNAVAILABLE');
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
  if(!gross.admitted){res.directions.push({direction:c.direction,status:'REJECT_GROSS',min_sol_out:c.minOutput.toString(),gross_min_delta:gross.minimum_net_lamports});continue;}
  const q={direction:c.direction,status:'HOLD',min_sol_out:c.minOutput.toString()};res.directions.push(q);
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
async function run(mode){
 const dep=dependencies(),{web3}=dep;
 if(!process.env.SOLANA_RPC_URL||!/^https:\/\//.test(process.env.SOLANA_RPC_URL))throw Error('SOLANA_RPC_URL_HTTPS_REQUIRED');
 const trade=mode==='trade';
 if(trade)throw Error('LIVE_EXECUTION_NOT_CERTIFIED_NO_SIGN_OR_BROADCAST');
 const secret=process.env.QSB_SOLANA_PRIVATE_KEY||'';
 let keypair=null,wallet;
 if(secret){keypair=parseWalletSecret(secret,web3);wallet=keypair.publicKey;}
 else if(process.env.ORACLE_PUBLIC_KEY){wallet=new web3.PublicKey(process.env.ORACLE_PUBLIC_KEY)}
 else throw Error('WALLET_PUBLIC_KEY_REQUIRED');
 if(trade&&!keypair)throw Error('PRIVATE_KEY_ENV_REQUIRED_FOR_TRADE');
 if(trade && unresolvedJournal().length)throw Error('UNRESOLVED_PREVIOUS_BROADCAST_CHECK_JOURNAL');
 let cands=poolCandidates(sources());if(!cands.length)throw Error('NO_CROSSLISTED_POOL_IDENTITIES');
 const conn=new web3.Connection(process.env.SOLANA_RPC_URL,{commitment:'confirmed',disableRetryOnRateLimit:true});
 const alts=await lookupTables(conn,dep);
 const once=process.argv.includes('--once');
 const perCycle=Math.max(1,Math.min(24,Number(process.env.ORACLE120_PAIRS_PER_CYCLE||6)||6));
 let cursor=0,cycle=0;
 console.log('[ORACLE-120] mode='+mode+' crosslisted='+cands.length+' scanner=UNCHANGED canary=0.010_SOL trade_enabled='+trade);
 while(true){
  cycle++;
  // Reload canonical scanner/replenishment materialization each cycle; do not freeze at startup.
  const reloaded=poolCandidates(sources());
  if(reloaded.length){
   const old=cands.length, oldCursor=cursor;
   cands=reloaded;
   if(old!==cands.length)console.log('[INVENTORY_RELOADED] previous='+old+' current='+cands.length);
   cursor=oldCursor%cands.length;
  }
  const report={revision:'ORACLE-120',mode,cycle,status:'RUNNING',timestamp_unix:Math.floor(Date.now()/1000),
   scanner_modified:false,source_role:'IDENTITY_ONLY_LIVE_SDK_QUOTES',candidate_count:cands.length,signing_enabled:trade,broadcast_enabled:trade,canary_lamports:SIZE.toString(),rows:[]};
  for(let i=0;i<perCycle;i++){
   const r=cands[cursor%cands.length];cursor++;
   try{const row=await oneCandidate(conn,dep,r,wallet,trade?keypair:null,trade,alts);report.rows.push(row);
    const statuses=row.directions.map(d=>d.direction+':'+d.status).join('|');
    console.log('[PAIR]',r.token.slice(0,12),row.status,statuses);
    if(row.status==='TRADE_CONFIRMED'||row.status==='STOP_BROADCAST_UNRESOLVED'){
     report.status=row.status;recordReport(report);
     console.log('[EXECUTION]',JSON.stringify(row.directions.filter(d=>d.signature).map(d=>({signature:d.signature,status:d.status,realized_wallet_sol_delta:d.realized_wallet_sol_delta,realized_combined_sol_wsol_delta:d.realized_combined_sol_wsol_delta}))));
     return;
    }
   }catch(e){report.rows.push({token:r.token,status:'HOLD_ERROR',reason:redact(e)});
    if(is429(e)){report.status='HOLD_RPC_429_STOP';break;}
   }
   await sleep(850);
  }
  if(report.status==='RUNNING')report.status=report.rows.some(r=>r.status==='SIMULATED_CANDIDATE_ONLY')?'POSITIVE_UNSIGNED_SIMULATION_ONLY':'NO_VERIFIED_EXECUTABLE_PROFIT';
  recordReport(report);
  console.log('[CYCLE]',cycle,report.status,'checked='+report.rows.length,'[REPORT]',REPORT);
  if(once||report.status==='HOLD_RPC_429_STOP')return;
  await sleep(15000);
 }
}
if(require.main===module){
 const mode=process.argv.includes('--trade')?'trade':process.argv.includes('--watch')?'watch':null;
 if(!mode){console.error('Usage: node oracle119_atomic_machine.cjs --watch [--once] OR --trade');process.exitCode=2}
 else run(mode).catch(e=>{console.error('[HOLD]',redact(e));process.exitCode=1});
}
module.exports={SIZE,priority,budget,reserveBps,encode58,decode58,quoteGate,validatePoolRow,poolCandidates,altCandidates,redact,is429,mergeIxs,compactIx,unresolvedJournal,getPumpMinimumTokens,getPumpMinimumSol,dlmmQuote};
