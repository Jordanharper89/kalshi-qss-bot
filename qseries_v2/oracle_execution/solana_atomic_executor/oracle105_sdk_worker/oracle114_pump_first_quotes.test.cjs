'use strict';
const assert=require('assert'),m=require('./oracle114_pump_first_quotes.cjs');
const k='So11111111111111111111111111111111111111112';
assert.equal(m.rows({rows:[{token:k,pump_pool:k,meteora_pool:k}]}).length,1);
assert.equal(m.rows({rows:[{token:'bad',pump_pool:k,meteora_pool:k}]}).length,0);
assert(m.rate(new Error('429 Too Many Requests')));
assert.throws(()=>m.argsFromState({}),/PUMP_STATE_INCOMPLETE/);
assert.equal(typeof m.pumpBuyQuote,'function');
console.log('[PASS] ORACLE-114 five offline contract checks');
