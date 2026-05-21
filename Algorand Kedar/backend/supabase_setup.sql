-- Supabase Schema for AlgoShield Monitoring System

CREATE TABLE IF NOT EXISTS monitored_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_address TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    last_txn BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_address TEXT NOT NULL REFERENCES monitored_contracts(contract_address) ON DELETE CASCADE,
    message TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS) but allow service role access
ALTER TABLE monitored_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Create policies for service role (optional if you use the service role key which bypasses RLS)
CREATE POLICY "Service Role Full Access Monitored Contracts" ON monitored_contracts FOR ALL USING (true);
CREATE POLICY "Service Role Full Access Alerts" ON alerts FOR ALL USING (true);
