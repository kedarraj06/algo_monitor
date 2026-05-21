# 🛡️ AlgoShield AI — Project Status (Team QANTAS)

> **Last Updated:** 17 May 2026  
> **Hackathon:** Algorand 3.0 Hack Series 🐍  
> **Team:** QANTAS (4 Members)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                   │
│  Landing │ Dashboard │ Scanner │ Certificates │ Monitor      │
│  Pera Wallet Connect │ Tailwind CSS │ TypeScript             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (localhost:5173 → :8000)
┌──────────────────────────▼──────────────────────────────────┐
│                    BACKEND (FastAPI)                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ AI Scanner   │  │ NFT Minting  │  │ 24hr Monitoring   │  │
│  │ ML Model     │  │ ARC-69 Certs │  │ Anomaly Detection │  │
│  │ RAG/SLM      │  │ Pera Wallet  │  │ Email + Telegram  │  │
│  │ Rules Engine │  │              │  │ Alerts            │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────────┘  │
│         │                 │                   │              │
│    MongoDB           Algorand            Supabase            │
│  (Scans, Certs)      Testnet         (Monitoring DB)         │
└─────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 SDK (npm: @kaustubh2512/algoshield)           │
│           scan() │ scanFile() │ watch() │ CLI                │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ What's DONE (Completed Features)

### 1. AI Security Scanner ✅
- [x] Random Forest ML model trained on 90 TEAL contracts (safe/risky/vulnerable)
- [x] Feature extraction from TEAL code (7 base features + 4 engineered features)
- [x] Rule-based vulnerability detection (8 rules: authorization, rekey, reentrancy, overflow, etc.)
- [x] RAG suggestion engine with ChromaDB vectorstore + Phi-3-mini SLM
- [x] Security score calculation (0-100) with severity-weighted deductions
- [x] Line-by-line vulnerability mapping in TEAL code
- [x] Scanner orchestrator combining ML + rules + RAG into unified results
- [x] `/analyze` endpoint — upload .teal file or provide App ID
- [x] `/suggest` endpoint — get AI-powered fix suggestions
- [x] `/analyze-with-slm` endpoint — direct SLM analysis
- [x] Fetch real contracts from Algorand mainnet/testnet by App ID

### 2. NFT Security Certificates ✅
- [x] ARC-69 NFT minting on Algorand testnet
- [x] Certificate metadata with score, contract hash, audit date
- [x] `/mint-certificate` endpoint (score ≥ 70 required)
- [x] `/certificates/{wallet}` endpoint — list minted certs
- [x] Pera Wallet integration for receiving NFTs

### 3. Frontend Dashboard ✅
- [x] Landing page with animated Dither background + hero text
- [x] Dashboard with wallet-connected view + action cards
- [x] Scanner page (upload, scan, results with score gauge + vulnerability cards)
- [x] Certificates page with NFT card grid
- [x] Monitor page (start monitoring, view alerts)
- [x] Pera Wallet connect/disconnect/reconnect flow
- [x] Protected routes (redirect if wallet not connected)
- [x] Dark terminal luxury theme with glassmorphism
- [x] Animated components (ASCIIText, DecryptedText, SpotlightCard)

### 4. Developer SDK ✅
- [x] Published to npm as `@kaustubh2512/algoshield`
- [x] `scan()` — programmatic contract scanning
- [x] `scanFile()` — file-based scanning
- [x] `watch()` — real-time directory watcher (auto-scan on save)
- [x] Color-coded terminal output with severity badges
- [x] CLI: `algoshield scan <file>` and `algoshield watch <dir>`

### 5. Backend Infrastructure ✅
- [x] FastAPI server with CORS, lifespan management
- [x] MongoDB (Motor async) for scans, certificates, monitor jobs
- [x] APScheduler background monitoring (30-second intervals)
- [x] Isolation Forest anomaly detection model
- [x] API key authentication for SDK
- [x] Health check endpoint
- [x] Scan history per wallet (`GET /scans/{wallet}`)

### 6. Kedar's AI Models (Separate Branch) ✅
- [x] `ai_analyzer.py` — Random Forest classification on live transactions
- [x] `background_tasks.py` — async monitoring loop with Supabase
- [x] `supabase_client.py` — Supabase database wrapper
- [x] `supabase_setup.sql` — monitoring tables schema
- [x] Monitoring API router with `/monitor/start`, `/monitor/list`, `/monitor/alerts`
- [x] SuggestionPanel, UploadCard, MonitoringPanel frontend components
- [x] Email alert service with rich HTML templates

---

## ❌ What's REMAINING (Not Yet Done)

### 🔴 Critical (Must Have for Demo)

| # | Task | Assigned To | Status | Details |
|---|---|---|---|---|
| 1 | **Integrate `ai_analyzer.py` into main project** | Member 2 (Kedar) | ❌ Not started | Kedar's transaction-level AI analysis isn't in the main backend. Monitoring currently uses ONLY Isolation Forest — needs Random Forest classifier too |
| 2 | **Integrate Supabase for monitoring** | Member 2 (Kedar) | ❌ Not started | Copy `supabase_client.py` + `supabase_setup.sql` to main. Update monitoring routes to use Supabase |
| 3 | **Telegram alert service** | Member 3 | ❌ Not started | Function exists inline in `app.py` but NOT extracted into a proper service module. Not tested |
| 4 | **Email alert end-to-end** | Member 3 | ❌ Not tested | Code exists in `utils/email_service.py` but never verified with real Gmail App Password in the monitoring loop |
| 5 | **Wire alerts into monitoring loop** | Member 4 (Lead) | ❌ Not started | After Members 2+3 finish their parts, connect Telegram + Email + Supabase alerts into the monitoring cycle |
| 6 | **Port SuggestionPanel to main frontend** | Member 1 | ❌ Not started | Kedar built a `SuggestionPanel.jsx` — needs to be ported to TSX + Tailwind and wired into Scanner page |
| 7 | **"Get AI Suggestions" button on Scanner** | Member 1 | ❌ Not started | Scanner page needs a second button that calls `/suggest` and shows results in SuggestionPanel |

### 🟡 Important (Should Have)

| # | Task | Assigned To | Status | Details |
|---|---|---|---|---|
| 8 | Email input on Monitor page | Member 1 | ❌ Not started | Add email field so users can configure alert email when starting monitoring |
| 9 | Alert history display on Monitor page | Member 1 | ❌ Not started | Show recent alerts with severity badges, auto-refresh every 30s |
| 10 | Dashboard recent activity feed | Member 1 | ❌ Not started | Show last 3 scans on Dashboard (fetch from `GET /scans/{wallet}`) |
| 11 | Add `/monitor/list` endpoint to main | Member 2 (Kedar) | ❌ Not started | Kedar has this, main doesn't |
| 12 | SDK: Add `.py` file support | Member 3 | ❌ Not started | Currently only scans `.teal` files |
| 13 | SDK: Add `getReport()` method | Member 3 | ❌ Not started | Fetch full scan result by scan ID |
| 14 | SDK: Add `scanDir()` batch scanning | Member 3 | ❌ Not started | Scan all contracts in a directory at once |
| 15 | SDK: CI/CD exit codes + `--json` flag | Member 3 | ❌ Not started | Exit code 1 if score < threshold, JSON output for pipelines |
| 16 | Update `.env.template` with ALL variables | Member 4 (Lead) | ❌ Not started | MongoDB + Supabase + SMTP + Telegram + Algorand |
| 17 | Update `requirements.txt` | Member 4 (Lead) | ❌ Not started | Add supabase, pydantic[email], httpx |
| 18 | End-to-end ML pipeline testing | Member 2 (Kedar) | ❌ Not started | Build knowledge base, download SLM, test with all contract types |

### 🔵 Nice to Have

| # | Task | Assigned To | Status | Details |
|---|---|---|---|---|
| 19 | SDK: TypeScript definitions (`index.d.ts`) | Member 3 | ❌ Not started | Type safety for TS projects |
| 20 | NFT minting testnet verification | Member 3 | ❌ Not tested | Full flow: generate wallet → fund → scan → mint → verify in Pera |
| 21 | Frontend mobile responsiveness check | Member 1 | ❌ Not started | Verify all pages on < 768px |
| 22 | Loading skeletons for all API calls | Member 1 | ❌ Not started | Replace spinners with skeleton loaders |
| 23 | Update main README.md | Member 4 (Lead) | ❌ Not started | Accurate setup guide with both DBs |
| 24 | Record demo video | Member 4 (Lead) | ❌ Not started | Full walkthrough for hackathon submission |

---

## 📊 Progress Summary

| Category | Done | Remaining | % Complete |
|---|---|---|---|
| AI Scanner | 12/12 | 0 | **100%** |
| NFT Certificates | 5/5 | 0 | **100%** |
| Frontend Dashboard | 10/10 | 6 extras | **100%** (core) |
| Developer SDK | 6/6 | 5 extras | **100%** (core) |
| 24hr Monitoring | 5/12 | 7 | **~42%** |
| Alert System (Telegram + Email) | 0/4 | 4 | **0%** |
| Integration (Kedar → Main) | 0/5 | 5 | **0%** |
| **Overall** | **38/54** | **16 critical + 11 extras** | **~70%** |

---

## 🗂️ Task Files Per Member

| Member | File | Est. Hours |
|---|---|---|
| Member 1 (Frontend) | [MEMBER_1_FRONTEND_DEV.md](./MEMBER_1_FRONTEND_DEV.md) | ~10-14 hrs |
| Member 2 / Kedar (AI/ML) | [MEMBER_2_AI_DEV.md](./MEMBER_2_AI_DEV.md) | ~10-15 hrs |
| Member 3 (Blockchain + SDK) | [MEMBER_3_BLOCKCHAIN_SDK_DEV.md](./MEMBER_3_BLOCKCHAIN_SDK_DEV.md) | ~10-14 hrs |
| Member 4 / You (Backend Lead) | [MEMBER_4_BACKEND_LEAD.md](./MEMBER_4_BACKEND_LEAD.md) | ~8-12 hrs |

---

## 🗄️ Database Strategy (CONFIRMED)

| Database | Used For | Owner |
|---|---|---|
| **MongoDB** | Scans, Certificates, Scan History | Main project (existing) |
| **Supabase** | 24hr Monitoring: monitored_contracts, alerts | Kedar's approach (to integrate) |

---

## 🔧 Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | React (Vite), TypeScript, Tailwind CSS, Pera Wallet Connect |
| Backend | FastAPI, Python 3.9+, APScheduler |
| AI/ML | Scikit-learn (Random Forest, Isolation Forest), llama-cpp (Phi-3-mini), ChromaDB |
| Blockchain | Algorand Python SDK, ARC-69 NFTs, Algonode Indexer |
| Main Database | MongoDB (Motor async) |
| Monitoring Database | Supabase (PostgreSQL) |
| Alerts | SMTP Email (Gmail) + Telegram Bot API |
| SDK | Node.js, npm (@kaustubh2512/algoshield) |

---

## 🚀 How to Run Locally

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python app.py                  # Starts on :8000
```

### Frontend
```bash
cd projects/frontend
npm install
npm run dev                    # Starts on :5173
```

### SDK
```bash
cd projects/algoshield-sdk
npm install
node bin/algoshield.js scan ../dataset/contracts/risky/12174882.teal
```

---

*Securing the decentralized future, one block at a time.* 🛡️
