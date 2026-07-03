# ratios: loc_comments=4:0 imports_exports=1:0 calls_definitions=1:0
import os

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 720  # 30 days
# ratios: loc_comments=4:0 imports_exports=1:0 calls_definitions=1:0
