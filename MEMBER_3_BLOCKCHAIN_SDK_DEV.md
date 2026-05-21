# ⛓️ Member 3 — Blockchain + SDK Developer Task Sheet

> **Role:** Blockchain Developer + SDK Improvements  
> **Stack:** Python (py-algorand-sdk), Node.js (npm SDK), Algorand Testnet  
> **Directories:** `sdk/`

---

## ✅ Already Done
- [x] Algorand contract fetcher by App ID
- [x] ARC-69 NFT Certificate minting
- [x] Transaction poller for monitoring
- [x] SDK published to npm (`@kaustubh2512/algoshield`)
- [x] scan(), scanFile(), watch(), CLI binary, terminal formatter

---

## 📋 Remaining Tasks

### P1: Telegram Alert Service (REMAINING)

Move `_send_telegram()` from `app.py` line 340 into its own module.

- [ ] Create `projects/backend/utils/telegram_service.py` with:
  - `send_telegram_alert(chat_id, app_id, result)` function
  - Read `TELEGRAM_BOT_TOKEN` from env
  - Severity emoji mapping (🔴 Critical, 🟠 High, 🟡 Medium, 🔵 Low)
  - Markdown-formatted alert with App ID, severity, score, explorer link
  - Proper error handling — never crash the monitoring loop
- [ ] Wire into `services/monitor_service.py` — call when anomaly detected AND `telegram_chat_id` is set
- [ ] Add `TELEGRAM_BOT_TOKEN` to `.env.template`
- [ ] Test: Create bot via @BotFather, get chat_id, verify alerts arrive

### P2: Email Alert Verification (REMAINING)

Email service code exists but needs end-to-end testing.

- [ ] Verify `utils/email_service.py` works with Gmail App Passwords
- [ ] Ensure `monitor_service.py` calls `send_alert_email()` when anomaly detected AND `alert_email` is set
- [ ] Add SMTP env vars to `.env.template`: `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_HOST`, `SMTP_PORT`
- [ ] Test end-to-end: start monitoring → trigger alert → verify email arrives

### P3: SDK Improvements

#### Add PyTEAL (.py) support
- [ ] Update `src/scanner.js` line 29: accept `.py` and `.txt` alongside `.teal`
- [ ] Update `src/file-watcher.js` to watch `.py` files too

#### Add `getReport(scanId)` method
- [ ] Add to `src/index.js`: fetches full scan from `GET /scan/{scanId}`

#### Add batch scanning `scanDir(dirPath)`
- [ ] New method: reads all `.teal`/`.py` files in directory, scans each, returns array of results

#### Add CI/CD features
- [ ] `--json` flag for machine-readable output
- [ ] `--threshold N` flag for custom pass/fail score
- [ ] Exit code 1 if score < threshold (default 70) — essential for CI pipelines

#### Add TypeScript definitions
- [ ] Create `index.d.ts` with AlgoShield, ScanResult, Vulnerability interfaces

### P4: Blockchain Hardening

- [ ] Test NFT minting end-to-end on testnet (generate wallet → fund → scan → mint)
- [ ] Handle edge cases: recipient not opted in, wallet out of funds, API down
- [ ] Verify poller correctly deduplicates transactions
- [ ] Test `algorand_fetcher.py` with real mainnet App IDs

---

## ⏱️ Estimated Time: ~10-14 hrs
