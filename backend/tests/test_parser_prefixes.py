from app.core.parser import FastAPIParser

def test_fastapi_router_prefixes():
    code = """
from fastapi import APIRouter

router = APIRouter(prefix="/users")

@router.get("/")
def get_users():
    '''List all users'''
    return []

@router.post("/{user_id}")
def create_user(user_id: str, data: dict):
    return {"id": user_id}

api_router = APIRouter(prefix="/api/v1")

@api_router.get("/health")
def health():
    return {"status": "ok"}
"""
    parser = FastAPIParser()
    routes = parser.parse_code(code)
    
    # Check prefixes
    paths = {r.path for r in routes}
    assert "/users" in paths  # /users/ becomes /users due to rstrip
    assert "/users/{user_id}" in paths
    assert "/api/v1/health" in paths
    
    print("Prefix test passed!")

def test_pydantic_heuristic():
    code = """
from typing import List, Optional
from pydantic import BaseModel

class User(BaseModel):
    name: str

@app.post("/users")
def create_user(user: User, tags: List[str], limit: Optional[int] = 10):
    return user
"""
    parser = FastAPIParser()
    routes = parser.parse_code(code)
    
    route = routes[0]
    assert route.request_model is not None
    assert route.request_model["type"] == "User"
    assert len(route.query_parameters) == 2
    
    print("Pydantic heuristic test passed!")

if __name__ == "__main__":
    test_fastapi_router_prefixes()
    test_pydantic_heuristic()
