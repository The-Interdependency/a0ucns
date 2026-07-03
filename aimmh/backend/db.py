# ratios: loc_comments=5:0 imports_exports=2:0 calls_definitions=1:0
from motor.motor_asyncio import AsyncIOMotorClient
import os

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
# ratios: loc_comments=5:0 imports_exports=2:0 calls_definitions=1:0
