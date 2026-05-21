const chalk = require('chalk');
const boxen = require('boxen');

const RISK_COLOR = { Safe: chalk.bgGreen.black.bold, Risky: chalk.bgYellow.black.bold, Critical: chalk.bgRed.white.bold, SAFE: chalk.bgGreen.black.bold, SUSPICIOUS: chalk.bgYellow.black.bold, RISKY: chalk.bgRed.white.bold };
const SEV_COLOR  = { Critical: chalk.red.bold, High: chalk.hex('#ff6b35').bold, Medium: chalk.yellow.bold, Low: chalk.blue };
const SEV_ICON   = { Critical: '🔴', High: '⚠ ', Medium: '⚡', Low: 'ℹ ' };

function formatResult(result, filePath) {
  const sc = result.score >= 70 ? chalk.green : result.score >= 40 ? chalk.yellow : chalk.red;
  const rl = RISK_COLOR[result.risk_level] || chalk.white;
  const lines = [
    chalk.bold.white('AlgoShield AI — Security Scan'),
    filePath ? chalk.gray(`File: ${filePath}`) : '',
    '',
    `Score:    ${sc.bold(result.score + '/100')}`,
    `Risk:     ${rl(' ' + (result.risk_level || '').toUpperCase() + ' ')}`,
    `ML Label: ${chalk.gray(result.label || 'N/A')}`,
    result.summary ? '' : null,
    result.summary ? chalk.gray(result.summary) : null,
  ].filter(l => l !== null);

  const out = [boxen(lines.join('\n'), {
    padding: 1,
    borderColor: result.score >= 70 ? 'green' : result.score >= 40 ? 'yellow' : 'red',
    borderStyle: 'round'
  }), ''];

  const vulns = result.vulnerabilities || [];
  if (vulns.length > 0) {
    const order = { Critical: 0, High: 1, Medium: 2, Low: 3 };
    vulns.sort((a, b) => (order[a.severity] ?? 4) - (order[b.severity] ?? 4)).forEach(v => {
      const icon = SEV_ICON[v.severity] || '⚠ ';
      const badge = (SEV_COLOR[v.severity] || (x => x))(`[${(v.severity||'').toUpperCase()}]`);
      out.push(`${icon}  ${chalk.gray('Line ' + String(v.line || '?').padEnd(4))}  ${badge}  ${chalk.white(v.issue || '')}`);
      if (v.suggestion) out.push(`   ${chalk.cyan('Fix:')} ${chalk.gray(v.suggestion)}`);
      out.push('');
    });
  } else {
    out.push(chalk.green('✅  No vulnerabilities found!'));
    out.push('');
  }

  out.push(chalk.gray('─'.repeat(52)));
  out.push(chalk.gray(`Scan ID: ${result.scan_id || 'N/A'}`));
  if (result.score >= 70) out.push(chalk.green('🏆  Score ≥ 70 — eligible for NFT Certificate at https://algoshield.io'));
  else out.push(chalk.yellow('💡  Fix the vulnerabilities above to improve your score'));
  out.push('');
  return out.join('\n');
}

function printScanResult(result, { filePath } = {}) {
  console.log(formatResult(result, filePath));
}

function printError(err) {
  console.error(boxen(chalk.red.bold('AlgoShield Error\n\n') + chalk.white(err.message), { padding: 1, borderColor: 'red', borderStyle: 'round' }));
}

module.exports = { formatResult, printScanResult, printError };
