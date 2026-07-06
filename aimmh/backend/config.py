# ratios: loc_comments=8:2 imports_exports=1:0 calls_definitions=1:0
import os

# JWT_SECRET has no insecure default: a missing secret must fail startup rather
# than sign/verify HS256 tokens with a world-known literal (which would let
# anyone forge a token for any user id).
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError('JWT_SECRET is required and has no default; set it before starting the backend')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 720  # 30 days
# ratios: loc_comments=8:2 imports_exports=1:0 calls_definitions=1:0
