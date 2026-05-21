# 🤖 Member 2 (Kedar) — AI/ML Developer Task Sheet

> **Role:** AI/ML Developer  
> **Stack:** Python, Scikit-learn, llama-cpp, ChromaDB, FastAPI  
> **Your Code:** `Algorand Kedar/` folder  
> **Integration Target:** `projects/backend/`

---

## ✅ What You've Already Done

- [x] Random Forest ML model trained (`algoshield_model.pkl` + `label_encoder.pkl`)
- [x] Feature extraction from TEAL code (`utils/feature_extractor.py`)
- [x] Feature engineering pipeline (`utils/feature_engineer.py`)
- [x] ML inference module (`models/inference.py`)
- [x] Predictor wrapper class (`models/predictor.py`)
- [x] Rule-based suggestion engine (`models/suggester.py`)
- [x] RAG pipeline with ChromaDB vectorstore (`utils/rag_pipeline.py`)
- [x] Query builder for knowledge base search (`utils/query_builder.py`)
- [x] AI transaction analyzer for monitoring (`utils/ai_analyzer.py`)
- [x] Background monitoring loop with Supabase (`utils/background_tasks.py`)
- [x] Blockchain transaction fetcher (`utils/blockchain.py`)
- [x] Email alert service (`utils/email_service.py`)
- [x] Supabase client wrapper (`utils/supabase_client.py`)
- [x] Supabase schema (`supabase_setup.sql`)
- [x] Monitoring router (`routers/monitoring.py`)
- [x] Frontend: SuggestionPanel, UploadCard, MonitoringPanel components
- [x] 90 test contracts (safe/risky/vulnerable)
- [x] Knowledge base builder script (`scripts/build_knowledge_base.py`)
- [x] SLM model download script (`scripts/download_models.py`)
- [x] Test scripts (`scripts/test_suggestion.py`, `test_api.py`)

---

## 📋 Remaining Tasks — Integrate Your Code Into Main Project

### Priority 1: Integrate `ai_analyzer.py` into Main Backend

Your `ai_analyzer.py` is the **key missing piece** in the main project's monitoring pipeline. The main project currently uses ONLY the Isolation Forest anomaly model for transaction monitoring. Your code adds the Random Forest classifier on top.

**What to do:**
- [ ] Copy `Algorand Kedar/backend/utils/ai_analyzer.py` → `projects/backend/utils/ai_analyzer.py`
- [ ] Adapt the imports to match the main project structure:
  ```python
  # Change FROM (Kedar):
  from utils.feature_extractor import extract_features_from_teal
  from models.inference import predict
  
  # Change TO (Main):
  from utils.feature_extractor import extract_features_from_teal
  from ml_models.inference import predict
  ```
- [ ] Update `projects/backend/services/monitor_service.py` to also call `analyze_transaction()` alongside the Isolation Forest check
- [ ] The monitoring loop should now do TWO checks per transaction:
  1. Isolation Forest anomaly detection (existing) → statistical anomaly
  2. Random Forest classification via `ai_analyzer.py` (your code) → SAFE/SUSPICIOUS/RISKY label
- [ ] If EITHER flags the transaction, generate an alert

### Priority 2: Integrate Supabase for Monitoring System

The main project uses MongoDB for scans/certificates. For the 24hr monitoring system, we're using **Supabase** (your approach).

**What to do:**
- [ ] Copy `Algorand Kedar/backend/utils/supabase_client.py` → `projects/backend/utils/supabase_client.py`
- [ ] Copy `Algorand Kedar/backend/supabase_setup.sql` → `projects/backend/supabase_setup.sql`
- [ ] Add Supabase environment variables to `projects/backend/.env.template`:
  ```env
  # Supabase (for 24hr monitoring)
  SUPABASE_URL=https://your-project-id.supabase.co
  SUPABASE_KEY=your_anon_or_service_role_key
  ```
- [ ] Add `supabase` to `projects/backend/requirements.txt`
- [ ] Update `projects/backend/services/monitor_service.py` to store monitored contracts and alerts in **Supabase** instead of MongoDB
- [ ] The `/monitor/start`, `/monitor/stop`, and `/monitor/alerts` endpoints should read/write to Supabase tables

### Priority 3: Integrate `background_tasks.py` Pattern

Your async monitoring loop is cleaner than the main project's APScheduler approach for the Supabase-backed monitoring.

**What to do:**
- [ ] Merge the best parts of your `background_tasks.py` into `projects/backend/services/monitor_service.py`:
  - Keep APScheduler as the trigger mechanism (it's already set up in `app.py`)
  - Use your `_run_monitoring_cycle()` logic for the actual work
  - Use `asyncio.to_thread()` for CPU-bound ML calls (your pattern)
  - Store alerts in Supabase using your `_store_alert()` function
- [ ] Make sure the monitoring loop calls BOTH:
  1. `ai_analyzer.analyze_transaction()` (your Random Forest)
  2. `anomaly.get_monitor().check_transaction()` (existing Isolation Forest)

### Priority 4: Add `/monitor/list` Endpoint to Main

Your monitoring router has a `GET /monitor/list` endpoint that's missing from main.

- [ ] Add to `projects/backend/routes/monitor.py`:
  ```python
  @router.get("/monitor/list")
  async def list_monitored_contracts():
      supabase = get_supabase_client()
      response = supabase.table("monitored_contracts").select("*").execute()
      return {"contracts": response.data}
  ```

### Priority 5: Test the Full ML Pipeline End-to-End

- [ ] Run `scripts/build_knowledge_base.py` to ensure ChromaDB vectorstore is populated
- [ ] Run `scripts/download_models.py` to ensure Phi-3-mini SLM is downloaded
- [ ] Test `/analyze` with a risky contract from `dataset/contracts/risky/`
- [ ] Test `/suggest` with the same contract — verify suggestions appear
- [ ] Test monitoring: start monitoring a testnet address, verify AI analysis runs every 30s
- [ ] Run `scripts/test_suggestion.py` to validate suggestion quality

### Priority 6: Improve Suggestion Quality

- [ ] Review the knowledge base content — ensure it covers all 10 vulnerability classes from PROMPT_2
- [ ] Add more TEAL vulnerability patterns to the knowledge base if gaps exist
- [ ] Test with edge cases: empty contracts, very large contracts, PyTEAL contracts
- [ ] Verify the security score calculation matches expected values for known contracts

---

## 📝 File Mapping: Your Code → Main Project

| Your File | Copy To | Notes |
|---|---|---|
| `utils/ai_analyzer.py` | `projects/backend/utils/ai_analyzer.py` | Fix imports: `models.` → `ml_models.` |
| `utils/supabase_client.py` | `projects/backend/utils/supabase_client.py` | Direct copy |
| `utils/background_tasks.py` | Merge into `projects/backend/services/monitor_service.py` | Cherry-pick logic |
| `routers/monitoring.py` | Merge into `projects/backend/routes/monitor.py` | Add `/monitor/list` |
| `supabase_setup.sql` | `projects/backend/supabase_setup.sql` | Direct copy |
| `models/predictor.py` | `projects/backend/ml_models/predictor.py` | Fix imports |
| `.env.example` | Merge into `projects/backend/.env.template` | Add SUPABASE vars |

---

## ⏱️ Estimated Time

| Task | Est. Time |
|---|---|
| Integrate ai_analyzer.py | 1-2 hrs |
| Integrate Supabase for monitoring | 2-3 hrs |
| Merge background_tasks pattern | 2-3 hrs |
| Add /monitor/list endpoint | 30 min |
| End-to-end ML testing | 2-3 hrs |
| Suggestion quality improvements | 2-3 hrs |
| **Total** | **~10-15 hrs** |
