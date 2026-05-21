-- Supabase Schema for AlgoShield Monitoring System

CREATE TABLE IF NOT EXISTS monitored_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address TEXT NOT NULL,
    app_id BIGINT NOT NULL,
    account_address TEXT NOT NULL,
    telegram_chat_id TEXT,
    alert_email TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_txn_id TEXT,
    last_round BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monitor_job_id UUID REFERENCES monitored_contracts(id) ON DELETE CASCADE,
    app_id BIGINT NOT NULL,
    txn_id TEXT,
    anomaly_score DOUBLE PRECISION,
    ai_label TEXT,
    ai_risk_level TEXT,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS) but allow service role access
ALTER TABLE monitored_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Create policies for service role
CREATE POLICY "Service Role Full Access Monitored Contracts" ON monitored_contracts FOR ALL USING (true);
CREATE POLICY "Service Role Full Access Alerts" ON alerts FOR ALL USING (true);
