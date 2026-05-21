const AlgoShield = require('../src/index');
const shield = new AlgoShield({ apiUrl: 'http://localhost:8000' });

const vulnerable = `#pragma version 6
txn ApplicationID
bz handle_creation
byte "balance"
app_global_get
int 1000000
+
byte "balance"
app_global_put
int 1
return
handle_creation:
int 1
return`;

console.log('Testing AlgoShield SDK...\n');
shield.scan(vulnerable)
  .then(r => {
    if (r.score === 50 && !r.vulnerabilities?.length) {
      console.error('FAIL: Stub still running or model not loading');
      process.exit(1);
    }
    console.log(`\nScore: ${r.score} | Risk: ${r.risk_level} | Vulns: ${r.vulnerabilities?.length}`);
    console.log('SDK TEST PASSED ✅');
  })
  .catch(e => {
    console.error('FAILED:', e.message);
    process.exit(1);
  });
