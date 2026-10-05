"""
database.py — MongoDB async connection using Motor.
Provides a singleton database client and collection accessors.
"""
import motor.motor_asyncio
from config import get_settings

settings = get_settings()

# Create async MongoDB client
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.MONGO_DB_NAME]


# ─── Collection accessors ─────────────────────────────────────────────────────
def get_users_collection():
    return db["users"]


def get_activities_collection():
    return db["activities"]


def get_alerts_collection():
    return db["alerts"]


def get_risk_scores_collection():
    return db["risk_scores"]


def get_investigations_collection():
    return db["investigations"]


def get_reports_collection():
    return db["reports"]


async def create_indexes():
    """Create MongoDB indexes for optimized queries."""
    users_col = get_users_collection()
    activities_col = get_activities_collection()
    alerts_col = get_alerts_collection()
    risk_col = get_risk_scores_collection()

    # Users — unique email index
    await users_col.create_index("email", unique=True)
    await users_col.create_index("username", unique=True)

    # Activities — compound indexes
    await activities_col.create_index([("user_id", 1), ("timestamp", -1)])
    await activities_col.create_index("event_type")
    await activities_col.create_index("timestamp")

    # Alerts — severity + timestamp
    await alerts_col.create_index([("severity", 1), ("timestamp", -1)])
    await alerts_col.create_index("user_id")
    await alerts_col.create_index("is_read")

    # Risk scores
    await risk_col.create_index([("user_id", 1), ("calculated_at", -1)])
