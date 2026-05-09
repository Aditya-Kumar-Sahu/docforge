import pytest
from app.core.parser import FastAPIParser

TEST_CODE = """
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

@app.get("/health")
def health():
    return {"status": "ok"}

@router.post("/users/{user_id}")
async def create_user(user_id: int, data: dict):
    return {"id": user_id}

@app.put("/items/")
def update_item(item_id: str, q: str | None = None):
    return {"item_id": item_id}
"""

def test_basic_extraction():
    parser = FastAPIParser()
    routes = parser.parse_file("test.py", TEST_CODE)
    
    # We expect 3 routes: /health, /users/{user_id}, /items/
    # This test will fail until the parser is implemented
    assert len(routes) == 3
    
    paths = [r["path"] for r in routes]
    assert "/health" in paths
    assert "/users/{user_id}" in paths
    assert "/items/" in paths
    
    methods = [r["method"] for r in routes]
    assert "GET" in methods
    assert "POST" in methods
    assert "PUT" in methods
