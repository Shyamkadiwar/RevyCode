from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.user import User
from app.models.repository import Repository
from app.models.review import Review


async def init_db():
    """Initialize database connection and Beanie"""
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            User,
            Repository,
            Review
        ]
    )
    
    print("✅ Database initialized successfully")