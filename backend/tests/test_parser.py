import pytest
from app.core.parser import FastAPIParser

TEST_CODE = """
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

app = FastAPI()
router = APIRouter()

@app.get("/health")
def health():
    \"\"\"Check API health.\"\"\"
    return {"status": "ok"}

@router.post("/users/{user_id}")
async def create_user(user_id: int, data: dict):
    return {"id": user_id}

@app.put("/items/")
def update_item(item_id: str, q: str | None = None):
    return {"item_id": item_id}

class UserCreate(BaseModel):
    username: str
    email: str
    age: int

@app.post("/users/")
def create_user_pydantic(user: UserCreate):
    return user
"""

def test_basic_extraction():
    parser = FastAPIParser()
    routes = parser.parse_file("test.py", TEST_CODE)
    
    # We expect 4 routes
    assert len(routes) == 4
    
    paths = [r["path"] for r in routes]
    assert "/health" in paths
    assert "/users/{user_id}" in paths
    assert "/items/" in paths
    assert "/users/" in paths
    
    methods = [r["method"] for r in routes]
    assert "GET" in methods
    assert "POST" in methods
    assert "PUT" in methods

def test_model_resolution():
    parser = FastAPIParser()
    routes = parser.parse_file("test.py", TEST_CODE)
    
    pydantic_route = next(r for r in routes if r["handler_name"] == "create_user_pydantic")
    user_param = pydantic_route["params"][0]
    
    assert user_param["name"] == "user"
    assert user_param["type"] == "UserCreate"
    assert user_param["schema"] is not None
    assert "username" in user_param["schema"]["fields"]
    assert user_param["schema"]["fields"]["username"]["type"] == "str"
    assert user_param["schema"]["fields"]["email"]["type"] == "str"
    assert user_param["schema"]["fields"]["age"]["type"] == "int"

    # Verify docstring
    health_route = next(r for r in routes if r["path"] == "/health")
    assert health_route["docstring"] == "Check API health."
