#!/usr/bin/env node
const path = require('path');
const AlgoShield = require('../src/index');
const chalk = require('chalk');

const args = process.argv.slice(2);
const command = args[0] && !args[0].startsWith('--') ? args[0] : 'help';
const target = args[1] && !args[1].startsWith('--') ? args[1] : '.';

const isJson = process.argv.includes('--json');
const thresholdIndex = process.argv.indexOf('--threshold');
const threshold = thresholdIndex > -1 ? parseInt(process.argv[thresholdIndex + 1]) : 70;

const shield = new AlgoShield();
if (isJson) shield.config.silent = true;

async function run() {
  if (command === 'scan') {
    if (target.endsWith('.teal') || target.endsWith('.py') || target.endsWith('.txt')) {
      const r = await shield.scanFile(target);
      if (isJson) console.log(JSON.stringify(r, null, 2));
      if (r.score < threshold) process.exit(1);
    } else {
      console.error(chalk.red('Please provide a .teal, .py, or .txt file to scan.'));
      process.exit(1);
    }
  } else if (command === 'watch') {
    shield.watch(target);
  } else {
    console.log(chalk.bold.cyan('\n🛡️  AlgoShield AI — Developer CLI\n'));
    console.log('Usage:');
    console.log('  algoshield scan <file>         Analyze a smart contract');
    console.log('  algoshield watch <dir>         Monitor directory for changes');
    console.log('\nOptions:');
    console.log('  --api-key <key>                Set your API key');
    console.log('  --json                         Output result as JSON string');
    console.log('  --threshold <N>                Fail with exit code 1 if score < N (default 70)');
  }
}

run().catch(() => process.exit(1));
