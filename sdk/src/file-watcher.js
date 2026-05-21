// file-watcher.js
const chokidar = require('chokidar');
const chalk = require('chalk');
const { scanFile } = require('./scanner');
const { printScanResult, printError } = require('./formatter');

function watchDirectory(dirPath, options = {}) {
  const { debounceMs = 1000 } = options;

  console.log(chalk.cyan(`\n🛡️  AlgoShield watching: ${dirPath}`));
  console.log(chalk.gray('   Auto-scanning .teal and .py files on every save...\n'));

  const debounceTimers = {};

  const watcher = chokidar.watch(`${dirPath}/**/*.{teal,py}`, {
    ignoreInitial: false,
    persistent: true
  });

  async function runScan(filePath) {
    console.log(chalk.gray(`\n📄 Scanning: ${filePath}`));
    try {
      const result = await scanFile(filePath, options);
      printScanResult(result, { filePath });
    } catch (error) {
      printError(error);
    }
  }

  watcher.on('change', (filePath) => {
    clearTimeout(debounceTimers[filePath]);
    debounceTimers[filePath] = setTimeout(() => runScan(filePath), debounceMs);
  });

  watcher.on('add', (filePath) => {
    runScan(filePath);
  });

  watcher.on('error', (error) => {
    console.error(chalk.red('Watcher error:'), error);
  });

  return watcher;
}

module.exports = { watchDirectory };
