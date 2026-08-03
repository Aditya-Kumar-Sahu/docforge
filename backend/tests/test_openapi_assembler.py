from app.core.openapi_assembler import OpenAPIAssembler
from unittest.mock import MagicMock

def test_assemble_empty():
    spec = OpenAPIAssembler.assemble([])
    assert spec["openapi"] == "3.1.0"
    assert "paths" in spec

def test_assemble_with_endpoints():
    ep = MagicMock()
    ep.path = "/test"
    ep.method = "GET"
    ep.id = 1
    ep.handler_function = "test_handler"
    ep.generated_doc_json = {
        "title": "Test Title",
        "description": "Test Desc",
        "parameters": [
            {"name": "id", "in": "query", "schema": {"type": "integer"}}
        ],
        "responses": [
            {
                "status": 200,
                "description": "OK",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"foo": {"type": "string"}}
                        }
                    }
                }
            }
        ]
    }

    spec = OpenAPIAssembler.assemble([ep])
    
    assert "/test" in spec["paths"]
    assert "get" in spec["paths"]["/test"]
    operation = spec["paths"]["/test"]["get"]
    assert operation["summary"] == "Test Title"
    
    # check schemas deduplication
    assert "Schema1" in spec["components"]["schemas"]
