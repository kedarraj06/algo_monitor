const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

async function scanContract(contractCode, options = {}) {
  const { apiKey = 'demo-key-123', apiUrl = 'http://localhost:8000', walletAddress = 'sdk-user', timeout = 30000 } = options;
  if (!contractCode || typeof contractCode !== 'string') throw new Error('contractCode must be a non-empty string');

  const form = new FormData();
  form.append('file', Buffer.from(contractCode), { filename: 'contract.teal', contentType: 'text/plain' });
  form.append('wallet_address', walletAddress);

  try {
    const res = await axios.post(`${apiUrl}/analyze`, form, {
      headers: { ...form.getHeaders(), 'X-API-Key': apiKey },
      timeout
    });
    return res.data;
  } catch (err) {
    if (err.response) throw new Error(`API ${err.response.status}: ${JSON.stringify(err.response.data)}`);
    if (err.code === 'ECONNREFUSED') throw new Error(`Cannot connect to ${apiUrl}. Is the backend running? cd backend && uvicorn app:app --reload`);
    throw err;
  }
}

async function scanFile(filePath, options = {}) {
  if (!fs.existsSync(filePath)) throw new Error(`File not found: ${filePath}`);
  if (!['.teal', '.py', '.txt'].includes(path.extname(filePath).toLowerCase())) throw new Error('Only .teal, .py, and .txt files supported');
  return scanContract(fs.readFileSync(filePath, 'utf-8'), options);
}

module.exports = { scanContract, scanFile };
