"""
seed_demo_data.py — Seed script to populate MongoDB with realistic demo data.
Run this after starting MongoDB to have a complete demo environment.

Usage:
    python seed_demo_data.py
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os

# ─── Config ───────────────────────────────────────────────────
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "insider_threat_db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_USERS = [
    {"username": "admin", "email": "admin@threatsight.ai", "full_name": "System Administrator", "role": "admin", "department": "IT Security", "password": "Admin@123456"},
    {"username": "sarah_analyst", "email": "sarah@threatsight.ai", "full_name": "Sarah Johnson", "role": "analyst", "department": "IT Security", "password": "Analyst@123"},
    {"username": "john_doe", "email": "john.doe@company.com", "full_name": "John Doe", "role": "employee", "department": "Finance", "password": "Employee@123"},
    {"username": "emily_chen", "email": "emily.chen@company.com", "full_name": "Emily Chen", "role": "employee", "department": "Engineering", "password": "Employee@123"},
    {"username": "mike_ross", "email": "mike.ross@company.com", "full_name": "Mike Ross", "role": "employee", "department": "Legal", "password": "Employee@123"},
    {"username": "alice_wong", "email": "alice.wong@company.com", "full_name": "Alice Wong", "role": "employee", "department": "HR", "password": "Employee@123"},
    {"username": "bob_threat", "email": "bob.threat@company.com", "full_name": "Bob Malicious", "role": "employee", "department": "Finance", "password": "Employee@123"},
    {"username": "carol_risk", "email": "carol.risk@company.com", "full_name": "Carol Risky", "role": "employee", "department": "Sales", "password": "Employee@123"},
]

EVENT_TYPES = ["login", "logout", "file_access", "file_download", "usb_transfer",
               "web_browse", "email_attachment", "file_upload", "remote_access"]

SENSITIVITY_LEVELS = ["low", "low", "low", "medium", "medium", "high", "critical"]
IP_ADDRESSES = ["192.168.1.{}", "10.0.0.{}", "172.16.0.{}"]


def generate_activity(user_id: str, is_malicious: bool = False) -> dict:
    """Generate a realistic activity event."""
    now = datetime.now(timezone.utc)
    # Random timestamp in last 30 days
    days_ago = random.randint(0, 30)
    hour = random.choice([22, 23, 0, 1, 2] if is_malicious else list(range(7, 21)))
    timestamp = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
    timestamp = timestamp.replace(hour=hour)

    is_after_hours = hour < 7 or hour >= 21
    event_type = random.choice(
        ["usb_transfer", "file_download", "file_download", "email_attachment", "login"]
        if is_malicious
        else EVENT_TYPES
    )

    sensitivity = random.choice(
        ["high", "critical", "high", "medium"]
        if is_malicious
        else SENSITIVITY_LEVELS
    )

    transfer_size = random.uniform(200, 800) if is_malicious else random.uniform(0, 50)

    act = {
        "user_id": user_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "ip_address": random.choice(IP_ADDRESSES).format(random.randint(1, 254)),
        "device_id": f"DEV_{random.randint(1000, 9999)}",
        "sensitivity_level": sensitivity,
        "is_after_hours": is_after_hours,
        "transfer_size_mb": round(transfer_size, 2),
        "risk_contribution": 0.0,
    }

    if event_type in ("login", "logout"):
        act["login_status"] = random.choice(["failed", "failed", "success"] if is_malicious else ["success", "success", "success", "failed"])
    if event_type in ("file_access", "file_download", "file_upload"):
        act["file_name"] = random.choice(["financial_report_Q4.xlsx", "employee_data.csv", "contracts_2024.pdf", "salary_info.xlsx", "client_list.csv"])
    if event_type == "web_browse":
        act["url"] = random.choice(["https://competitor.com/internal", "https://pastebin.com/raw", "https://dropbox.com", "https://normal-site.com"])

    return act


def generate_alert(user_id: str, severity: str = "high") -> dict:
    """Generate a realistic security alert."""
    alert_types = {
        "critical": ("data_exfiltration", "🚨 Critical Data Exfiltration Detected"),
        "high": ("usb_abuse", "⚠️ USB Device Abuse Detected"),
        "medium": ("suspicious_login", "🔍 Suspicious Login Pattern"),
        "low": ("abnormal_browsing", "🌐 Abnormal Browsing Activity"),
    }

    atype, title = alert_types.get(severity, alert_types["medium"])
    descriptions = {
        "data_exfiltration": "Large volume of sensitive data transferred to external device.",
        "usb_abuse": "Multiple USB transfers of sensitive files detected after hours.",
        "suspicious_login": "Multiple failed login attempts followed by successful authentication.",
        "abnormal_browsing": "User visited several high-risk websites outside normal pattern.",
    }

    return {
        "user_id": user_id,
        "alert_type": atype,
        "severity": severity,
        "title": title,
        "description": descriptions.get(atype, "Anomalous behavior detected."),
        "risk_score": {"critical": 85, "high": 65, "medium": 45, "low": 20}.get(severity, 40),
        "status": random.choice(["open", "open", "investigating", "resolved"]),
        "is_read": random.choice([True, False, False]),
        "timestamp": datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 72)),
        "resolved_at": None,
        "resolved_by": None,
        "related_activity_ids": [],
    }


async def seed():
    print("\n" + "="*60)
    print("🌱 SEEDING DEMO DATA — ThreatSight AI Platform")
    print("="*60)

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    users_col = db["users"]
    activities_col = db["activities"]
    alerts_col = db["alerts"]

    # Clear existing demo data
    await users_col.delete_many({})
    await activities_col.delete_many({})
    await alerts_col.delete_many({})
    print("🗑️  Cleared existing data")

    # ── Seed users ────────────────────────────────────────
    print("\n👤 Creating demo users...")
    user_ids = {}
    for u in DEMO_USERS:
        is_malicious = u["username"] in ("bob_threat", "carol_risk")
        risk_score = random.uniform(70, 95) if is_malicious else random.uniform(5, 35)
        risk_level = "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 31 else "LOW"

        doc = {
            "username": u["username"],
            "email": u["email"],
            "full_name": u["full_name"],
            "hashed_password": pwd_context.hash(u["password"]),
            "department": u["department"],
            "role": u["role"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365)),
            "last_login": datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48)),
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
        }
        result = await users_col.insert_one(doc)
        user_ids[u["username"]] = str(result.inserted_id)
        status = "🚨 MALICIOUS" if is_malicious else "✅ Normal"
        print(f"   {status} — {u['full_name']} (@{u['username']}) risk={risk_level}")

    # ── Seed activities ───────────────────────────────────
    print("\n📊 Generating activity events...")
    total_activities = 0
    for username, uid in user_ids.items():
        is_malicious = username in ("bob_threat", "carol_risk")
        n_events = random.randint(60, 120) if is_malicious else random.randint(20, 50)
        acts = [generate_activity(uid, is_malicious) for _ in range(n_events)]
        if acts:
            await activities_col.insert_many(acts)
        total_activities += n_events
        print(f"   @{username}: {n_events} events ({'malicious' if is_malicious else 'normal'})")

    # ── Seed alerts ───────────────────────────────────────
    print("\n🚨 Generating security alerts...")
    alert_configs = [
        ("bob_threat", "critical"), ("bob_threat", "high"), ("bob_threat", "high"),
        ("carol_risk", "high"), ("carol_risk", "medium"),
        ("john_doe", "medium"), ("emily_chen", "low"),
    ]
    for username, severity in alert_configs:
        uid = user_ids.get(username)
        if uid:
            alert = generate_alert(uid, severity)
            await alerts_col.insert_one(alert)

    # ── Create indexes ────────────────────────────────────
    await users_col.create_index("email", unique=True)
    await users_col.create_index("username", unique=True)
    await activities_col.create_index([("user_id", 1), ("timestamp", -1)])
    await alerts_col.create_index([("severity", 1), ("timestamp", -1)])

    print(f"\n✅ Seeding complete!")
    print(f"   👤 Users: {len(DEMO_USERS)}")
    print(f"   📊 Activities: {total_activities}")
    print(f"   🚨 Alerts: {len(alert_configs)}")
    print(f"\n🔐 Login credentials:")
    print(f"   Admin: admin@threatsight.ai / Admin@123456")
    print(f"   Analyst: sarah@threatsight.ai / Analyst@123")
    print("="*60 + "\n")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
