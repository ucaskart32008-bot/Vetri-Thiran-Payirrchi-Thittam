from fastapi.testclient import TestClient
from app.main import app
import uuid
client=TestClient(app)
def test_health():
    r=client.get("/health");assert r.status_code==200 and r.json()["status"]=="ok"
def test_register_login_plan_history():
    email=uuid.uuid4().hex+"@example.com"
    r=client.post("/api/auth/register",json={"name":"Test User","email":email,"password":"StrongPass123"});assert r.status_code==200,r.text
    r=client.post("/api/auth/login",data={"username":email,"password":"StrongPass123"});assert r.status_code==200,r.text
    h={"Authorization":"Bearer "+r.json()["access_token"]}
    p=client.post("/api/generate-home",headers=h,json={"budget":25000,"rooms":["Living room"],"style":"Modern","household_size":2,"priorities":"simple"})
    assert p.status_code==200,p.text
    assert p.json()["total_estimated"]<=25000
    assert client.get("/api/history",headers=h).status_code==200
def test_bad_login():assert client.post("/api/auth/login",data={"username":"noone@example.com","password":"bad"}).status_code==401
