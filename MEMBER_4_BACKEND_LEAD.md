# 🔧 Member 4 () — Backend Lead / Project Coordinator Task Sheet

> **Role:** Backend Developer + Team Lead  
> **Stack:** FastAPI, MongoDB, Python, Coordination  
> **Directory:** `projects/backend/`

---

## ✅ Already Done
- [x] FastAPI server with CORS, lifespan, APScheduler
- [x] MongoDB (Motor async) — scans, certificates, monitor_jobs, alerts collections
- [x] All API routes: /analyze, /suggest, /scan, /scans, /mint-certificate, /certificates, /monitor/start, /monitor/stop, /monitor/alerts, /health
- [x] Scanner orchestrator integrating ML + rules + RAG suggestions
- [x] Monitor service with APScheduler background loop
- [x] Database models, schemas, indexes
- [x] Requirements.txt, .env templates

---

## 📋 Remaining Tasks

### P1: Coordinate Kedar's Integration (Member 2)

**Your role:** Review and merge Kedar's code into main. Make sure imports work.

- [ ] After Kedar copies files, verify all imports resolve correctly:
  - `ml_models.inference` (not `models.inference`)
  - `utils.feature_extractor`, `utils.feature_engineer`
  - `utils.supabase_client` (new file)
  - `utils.ai_analyzer` (new file)
- [ ] Update `app.py` lifespan to initialize Supabase connection for monitoring
- [ ] Ensure both MongoDB (for scans/certs) and Supabase (for monitoring) work simultaneously
- [ ] Run the backend and test ALL endpoints respond

### P2: Update Monitor Service for Dual AI Analysis

- [ ] Update `services/monitor_service.py` to run both:
  1. Isolation Forest anomaly check (existing `ml_models.anomaly`)
  2. Random Forest classification via `utils.ai_analyzer` (Kedar's code)
- [ ] Alert should trigger if EITHER model flags the transaction
- [ ] Store alerts in Supabase (monitoring DB) with both scores

### P3: Wire Alert Channels into Monitor Loop

After Member 3 creates `telegram_service.py`:
- [ ] Update `monitor_service.py` to call both alert channels:
  ```python
  if result.get("is_anomaly"):
      # Store alert
      ...
      # Send Telegram if configured
      if job.get("telegram_chat_id"):
          from utils.telegram_service import send_telegram_alert
          send_telegram_alert(job["telegram_chat_id"], job["app_id"], result)
      # Send Email if configured
      if job.get("alert_email"):
          from utils.email_service import send_alert_email
          send_alert_email(...)
  ```
- [ ] Test both channels fire when anomaly is detected

### P4: Update .env.template with ALL Variables

- [ ] Create a comprehensive `.env.template` in `projects/backend/`:
  ```env
  # MongoDB (Main DB - scans, certificates)
  MONGODB_URL=mongodb://localhost:27017
  MONGODB_DB_NAME=algoshield

  # Supabase (Monitoring DB - 24hr monitoring)
  SUPABASE_URL=https://your-project-id.supabase.co
  SUPABASE_KEY=your_service_role_key

  # Algorand (Blockchain)
  PLATFORM_MNEMONIC=your 25 word mnemonic
  INDEXER_API_URL=https://mainnet-idx.algonode.cloud

  # SMTP Email Alerts
  SMTP_USER=your-email@gmail.com
  SMTP_PASSWORD=your_app_password
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=465

  # Telegram Alerts
  TELEGRAM_BOT_TOKEN=your_bot_token
  ```

### P5: Update requirements.txt

- [ ] Ensure `projects/backend/requirements.txt` includes ALL dependencies:
  ```
  fastapi
  uvicorn
  python-multipart
  motor
  pymongo
  certifi
  python-dotenv
  apscheduler
  scikit-learn
  numpy
  joblib
  llama-cpp-python
  chromadb
  httpx
  supabase
  pydantic[email]
  requests
  py-algorand-sdk
  ```

### P6: Update Main README.md

- [ ] Update `README.md` at project root with:
  - Accurate architecture diagram
  - Both database requirements (MongoDB + Supabase)
  - Complete .env setup guide
  - All team member credits
  - Demo flow instructions

### P7: Final Integration Testing

- [ ] Start backend: `python app.py`
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Test flow: Connect wallet → Upload .teal → Scan → Get Suggestions → Mint NFT
- [ ] Test monitoring: Start monitor → Wait for alerts → Check Telegram + Email
- [ ] Test SDK: `node bin/algoshield.js scan ../dataset/contracts/risky/12174882.teal`
- [ ] Record demo video

---

## ⏱️ Estimated Time: ~12-15 hrs
