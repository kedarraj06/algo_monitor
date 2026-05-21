# backend/database.py
import os, certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()

ca = certifi.where()
client = AsyncIOMotorClient(
    os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
    tlsCAFile=ca, 
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=5000
)
db = client[os.getenv("MONGODB_DB_NAME", "algoshield")]

scans_col        = db["scans"]
certificates_col = db["certificates"]
monitor_jobs_col = db["monitor_jobs"]
alerts_col       = db["alerts"]

async def create_indexes():
    await scans_col.create_index("wallet_address")
    await scans_col.create_index("created_at")
    await certificates_col.create_index("wallet_address")
    await monitor_jobs_col.create_index([("app_id", 1), ("wallet_address", 1)])
    await alerts_col.create_index("monitor_job_id")
