# AlgoShield AI 🛡️

AlgoShield AI is a comprehensive, machine-learning-powered security analysis and real-time monitoring platform tailored specifically for Algorand TEAL smart contracts. 

It provides developers with static risk classification, actionable remediation suggestions, and continuous live transaction monitoring to secure decentralized applications.

---

## 🌟 Key Features

1. **Risk Analysis (Prediction)**
   - Upload your `.teal` smart contract to evaluate its security posture.
   - Extracts key features from the code and runs a Random Forest classifier to flag the contract as **SAFE**, **SUSPICIOUS**, or **RISKY**.

2. **Actionable Suggestions (AI-Powered)**
   - Employs a Retrieval-Augmented Generation (RAG) pipeline powered by a Small Language Model (SLM).
   - Automatically detects vulnerabilities and provides precise, line-by-line fix recommendations and security scores.

3. **Smart Contract Monitoring**
   - Continuously monitors deployed contract addresses on the Algorand blockchain.
   - Fetches live transactions via the Algorand Indexer API.
   - Uses the AI model to analyze every incoming transaction for suspicious behavior.

4. **Real-time Email Alerts**
   - Integrates with Supabase for persistent alert storage.
   - Automatically dispatches high-priority email notifications when a `RISKY` transaction is detected on a monitored contract.

---

## 🛠️ Tech Stack

**Frontend:**
- **React (Vite)**
- **Pure CSS** (Premium Glassmorphism design)
- **Hoovers & Transitions** for interactive UI experience

**Backend:**
- **Python (FastAPI)**
- **Supabase** (Database & Alert Persistence)
- **Scikit-Learn** (Predictive ML Model)
- **Llama-cpp** (Local SLM Inference for Suggestions)
- **ChromaDB** (Vectorstore Knowledge Base)
- **SMTP** (Email Alert Service)

---

## 📂 Folder Structure

```
AlgoShield_AI/
├── backend/            # FastAPI server, ML models, Monitoring Engine
│   ├── routers/        # API endpoints (analyze, suggest, monitoring)
│   ├── utils/          # Blockchain, AI Analyzer, Email, Supabase utils
│   └── models/         # Pre-trained ML classifiers
├── frontend/           # React single-page application (Vite)
├── contracts/          # Sample .teal contracts (Safe/Risky) for testing
├── scripts/            # Database and setup scripts
├── README.md           # Project documentation
└── .gitignore          # Git exclusion rules
```

---

## 🚀 Installation & Setup

### Prerequisites
- Node.js (v18+)
- Python (3.12+)
- Supabase Account (for monitoring/alerts)

### 1. Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Open .env and add your SUPABASE_URL, SUPABASE_KEY, and SMTP credentials.
   ```

3. Start the FastAPI server:
   ```bash
   uvicorn app:app --port 8000
   ```

### 2. Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

---

## 📡 Demo Flow

1. **Static Analysis**: Upload a `.teal` file (e.g., from `/contracts/risky/`) and click **Analyze Risk** to see the AI classification.
2. **Suggestions**: Click **Get Suggestions** to receive a security score and remediation steps.
3. **Monitoring**:
   - Go to the monitoring section.
   - Enter a deployed contract address and your email.
   - Click **Start Monitoring**.
   - The system will now poll the blockchain every 30 seconds.
   - If a risky transaction is found, an alert is stored in the database and an email is sent to you immediately.

---

## 📄 License
This project is licensed under the MIT License.