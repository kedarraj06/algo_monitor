# 🛡️ AlgoShield AI SDK (Official Technical Documentation)

[![NPM Version](https://img.shields.io/npm/v/@kaustubh2512/algoshield?color=00ff88)](https://www.npmjs.com/package/@kaustubh2512/algoshield)
[![Algorand](https://img.shields.io/badge/Blockchain-Algorand-black)](https://algorand.co)

**AlgoShield AI** is a state-of-the-art security platform built specifically for the **Algorand Blockchain**. It provides real-time, AI-driven security auditing for TEAL smart contracts, helping developers identify vulnerabilities before they are deployed to Mainnet.

---

## 🛠️ Project Architecture

AlgoShield is built with a high-performance **Tri-Layer Architecture**:

1.  **AI/ML Core (Python/FastAPI)**: A machine learning brain that uses Random Forest models to classify contracts into `SAFE`, `RISKY`, or `VULNERABLE` categories based on logic density, transaction patterns, and known attack vectors.
2.  **Blockchain Integration (Algorand Python SDK)**: An automated workflow using **ARC-69** standards to mint **Security Certificate NFTs** for verified contracts, creating a decentralized proof-of-trust.
3.  **Developer Experience (This SDK)**: A Node.js library that bridges the gap between the developer's local machine and our AI auditing cloud.

---

## ✨ Key Features

- **✅ Deep Line-by-Line Analysis**: Identifies critical vulnerabilities like missing RekeyTo checks, timestamp manipulation, and reentrancy risks.
- **🧠 ML-Powered Scoring**: Generates a 0-100 Security Score based on a sophisticated feature-extraction pipeline.
- **🛡️ Hybrid Intelligence**: If the ML model finds a sophisticated pattern the static rules missed, it automatically elevates the risk level to ensure maximum safety.
- **🔗 On-Chain Proof**: Successful scans are eligible for an on-chain Certificate NFT, verifiable by any Pera Wallet or Explorer.

---

## 🚀 Installation & Setup

### For CLI Usage (All Developers):
Install the package globally to access the `algoshield` command from any terminal:
```bash
npm install -g @kaustubh2512/algoshield
```

### For Project Integration (Application Developers):
Install as a dependency in your React/Node project:
```bash
npm install @kaustubh2512/algoshield
```

---

## 📝 SDK API Reference (Functions)

The SDK exposes the `AlgoShield` class and several utility functions.

### 1. `scan(contractCode)` — Programmatic Analysis
Use this for dynamic scanning within your application logic.
- **Input**: `string` (The raw TEAL code)
- **Output**: `Promise<ScanResult>` (Detailed JSON object with score, risk level, and line errors)

```javascript
const AlgoShield = require('@kaustubh2512/algoshield');
const shield = new AlgoShield();

const result = await shield.scan(`
#pragma version 8
txn Sender
global CreatorAddress
==
assert
...`);

console.log(`Risk: ${result.risk_level}`); // Output: SAFE
```

### 2. `scanFile(filePath)` — File-Based Audit
Ideal for local scripts or unit testing.
- **Input**: `string` (Path to a `.teal` file)
- **Output**: `Promise<ScanResult>`

```javascript
const result = await shield.scanFile('./contracts/vault.teal');
```

### 3. `watch(dirPath)` — Real-Time Monitoring
The ultimate developer tool. Watches a directory and runs a scan automatically every time a file is saved.

```javascript
shield.watch('./projects/contracts');
```

### 4. CLI Commands
- `algoshield scan <filename>`: Run a one-time audit and print a beautiful report.
- `algoshield watch <directory>`: Turn on real-time protection for that folder.

---

## 🏗️ Implementation Guide (How to Integrate)

### Integration Example 1: GitHub Actions (CI/CD)
Block any PR that introduces insecure smart contracts. Create `.github/workflows/security.yml`:

```yaml
steps:
  - uses: actions/checkout@v3
  - run: npm install -g @kaustubh2512/algoshield
  - name: AlgoShield Audit
    run: algoshield scan ./contracts/main.teal
```

### Integration Example 2: Express/Backend
Add security as a service to your own platform:
```javascript
app.post('/api/upload-contract', async (req, res) => {
  const shield = new AlgoShield();
  const report = await shield.scan(req.body.code);
  
  if (report.score < 70) {
    return res.status(400).json({ error: "Contract rejected by AlgoShield AI", report });
  }
  // Proceed with deployment...
});
```

---

## 🏆 The Reward: On-Chain Certificates
AlgoShield is not just a report—it's a reputation system. When a contract achieves a **SAFE** status (Score ≥ 70) through the SDK, the developer can connect their **Pera Wallet** to our platform to:
1.  **Mint the Certificate**: Creates a verifiable NFT on the Algorand Testnet.
2.  **Display Badge**: Get a clickable shield badge for your GitHub README.

---

## 🤝 Project Credits
Created for the **Algorand 3.0 Hackathon**  
**Principal Architect**: Kaustubh 🛡️

*AlgoShield AI — Protecting the decentralized world, one TEAL file at a time.*
