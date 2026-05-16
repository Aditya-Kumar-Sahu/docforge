from app.core.parser import FastAPIParser

def test_fastapi_parser():
    parser = FastAPIParser()
    source_code = '''
from fastapi import FastAPI, APIRouter, Body

app = FastAPI()
router = APIRouter(prefix="/users", tags=["users"])

@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, q: str = None):
    """
    Get an item by ID.
    """
    return {"item_id": item_id, "q": q}

@router.post("")
async def create_user(user: User) -> UserResponse:
    return user
    '''
    
    routes = parser.parse_code(source_code, file_path="test_file.py")
    
    assert len(routes) == 2
    
    assert routes[0].method == "GET"
    assert routes[0].path == "/items/{item_id}"
    assert routes[0].handler_name == "read_item"
    assert "Get an item by ID." in routes[0].docstring
    assert len(routes[0].path_parameters) == 1
    assert routes[0].path_parameters[0] == {"name": "item_id", "type": "int"}
    assert len(routes[0].query_parameters) == 1
    assert routes[0].query_parameters[0] == {"name": "q", "type": "str"}
    assert routes[0].response_model == {"type": "ItemResponse"}
    assert routes[0].request_model is None
    
    assert routes[1].method == "POST"
    assert routes[1].path == ""
    assert routes[1].handler_name == "create_user"
    assert routes[1].request_model == {"name": "user", "type": "User"}
    assert routes[1].response_model == {"type": "UserResponse"}
