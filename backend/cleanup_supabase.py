"""Clean up invalid test addresses and analyze current Supabase state"""
from utils.supabase_client import get_supabase_client

s = get_supabase_client()

# 1. Show all contracts
r = s.table('monitored_contracts').select('*').execute()
print(f"=== All monitored_contracts ({len(r.data)} rows) ===")
for row in r.data:
    addr = row['contract_address']
    status = row['status']
    last_txn = row.get('last_txn', 0)
    print(f"  {row['id'][:8]}... | addr={addr[:40]} | status={status} | last_txn={last_txn}")

# 2. Delete invalid/test addresses (ones that don't look like real Algorand base58 addresses)
invalid_patterns = ['TEST_', 'RANDOM_', 'ALGOSHIELD', 'BROWSER_001']
deleted_count = 0
for row in r.data:
    addr = row['contract_address']
    is_invalid = any(addr.startswith(p) or p in addr for p in invalid_patterns)
    if is_invalid:
        result = s.table('monitored_contracts').delete().eq('id', row['id']).execute()
        print(f"  -> Deleted invalid row: {addr[:50]}")
        deleted_count += 1

print(f"\n=== Cleaned {deleted_count} invalid rows ===")

# 3. Show remaining
r2 = s.table('monitored_contracts').select('*').execute()
print(f"\n=== After cleanup: {len(r2.data)} active rows ===")
for row in r2.data:
    print(f"  {row['id'][:8]}... | addr={row['contract_address'][:40]} | status={row['status']}")
