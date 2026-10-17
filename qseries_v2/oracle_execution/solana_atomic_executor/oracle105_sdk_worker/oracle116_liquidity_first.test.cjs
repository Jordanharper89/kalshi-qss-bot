"use strict";
const assert=require('assert');const m=require('./oracle116_liquidity_first.cjs');
const b={base:'100',max_quote:'10000000'};
assert.equal(m.limits(100),8);assert.equal(m.limits(0),1);
assert.equal(m.evaluate({consumedInAmount:'90',outAmount:'12000000',minOutAmount:'11000000'},b,'10000000').reason,'PARTIAL_FILL');
assert.equal(m.evaluate({consumedInAmount:'100',outAmount:'12000000',minOutAmount:'11000000'},b,'10000000').positive_gross,true);
assert.equal(m.evaluate({consumedInAmount:'100',outAmount:'9000000',minOutAmount:'8000000'},b,'10000000').positive_gross,false);
console.log('[PASS] ORACLE-116 five deterministic liquidity and bounds checks');
