from fastapi import FastAPI
from fastapi.testclient import TestClient
app = FastAPI()
client = TestClient(app)
print(client.get("/nonexistent").text)
