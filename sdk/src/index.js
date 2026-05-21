const { scanContract, scanFile } = require('./scanner');
const { watchDirectory } = require('./file-watcher');
const { formatResult, printError } = require('./formatter');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

class AlgoShield {
  constructor(config = {}) {
    this.config = {
      apiKey:        config.apiKey        || process.env.ALGOSHIELD_API_KEY || 'demo-key-123',
      apiUrl:        config.apiUrl        || process.env.ALGOSHIELD_API_URL || 'http://localhost:8000',
      walletAddress: config.walletAddress || 'sdk-user',
      silent:        config.silent        || false,
    };
  }

  async scan(contractCode) {
    try {
      const r = await scanContract(contractCode, this.config);
      if (!this.config.silent) console.log(formatResult(r));
      return r;
    } catch (e) { if (!this.config.silent) printError(e); throw e; }
  }

  async scanFile(filePath) {
    try {
      const r = await scanFile(filePath, this.config);
      if (!this.config.silent) console.log(formatResult(r, filePath));
      return r;
    } catch (e) { if (!this.config.silent) printError(e); throw e; }
  }

  watch(dirPath, options = {}) {
    return watchDirectory(dirPath, { ...this.config, ...options });
  }

  async getReport(scanId) {
    try {
      const res = await axios.get(`${this.config.apiUrl}/scan/${scanId}`, {
        headers: { 'X-API-Key': this.config.apiKey }
      });
      return res.data;
    } catch (e) {
      if (!this.config.silent) printError(e);
      throw e;
    }
  }

  async scanDir(dirPath) {
    if (!fs.existsSync(dirPath)) throw new Error(`Directory not found: ${dirPath}`);
    const files = fs.readdirSync(dirPath).filter(f => ['.teal', '.py', '.txt'].includes(path.extname(f).toLowerCase()));
    const results = [];
    for (const f of files) {
      results.push(await this.scanFile(path.join(dirPath, f)));
    }
    return results;
  }
}

module.exports = AlgoShield;
module.exports.scan      = (code, opts) => new AlgoShield(opts).scan(code);
module.exports.scanFile  = (fp, opts)   => new AlgoShield(opts).scanFile(fp);
module.exports.watch     = (dp, opts)   => new AlgoShield(opts).watch(dp);
