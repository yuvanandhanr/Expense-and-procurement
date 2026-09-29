from src.auth.security import create_access_token
print(create_access_token({"sub": "admin@dataeko.ai", "user_id": 1, "roles": ["Admin"]}))
