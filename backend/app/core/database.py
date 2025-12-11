from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.user import User
from app.models.repository import Repository
from app.models.review import Review, InlineComment, AgentExecution


async def init_db():
    """Initialize database connection with proper error handling"""
    try:
        print("🔄 Connecting to MongoDB...")
        
        # Create client with timeout to prevent hanging
        client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=10000  # 10 second timeout
        )
        
        # Test the connection
        await client.admin.command("ping")
        print("✅ Connected to MongoDB")

        # Initialize Beanie with document models
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[
                User,
                Repository,
                Review,
                InlineComment,
                AgentExecution,
            ]
        )

        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize database:")
        print(f"   Error: {str(e)}")
        print(f"\n💡 Common fixes:")
        print(f"   1. Check if your IP is whitelisted in MongoDB Atlas")
        print(f"   2. Verify MONGODB_URL in .env file")
        print(f"   3. Ensure MongoDB Atlas cluster is running")
        raise