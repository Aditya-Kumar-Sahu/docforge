import json
import structlog
from typing import Any, Dict, List
from openapi_spec_validator import validate

logger = structlog.get_logger()


class OpenAPIAssembler:
    @staticmethod
    def assemble(endpoints: List[Any]) -> Dict[str, Any]:
        """
        Assemble a list of approved Endpoint ORM objects into a valid OpenAPI 3.1.0 specification.
        """
        openapi_spec: Dict[str, Any] = {
            "openapi": "3.1.0",
            "info": {
                "title": "Generated API Documentation",
                "version": "1.0.0"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }

        schema_counter = 1
        schema_map: Dict[str, str] = {}

        def extract_schemas(obj: Any) -> Any:
            nonlocal schema_counter
            if isinstance(obj, dict):
                if obj.get("type") == "object" and "properties" in obj:
                    schema_str = json.dumps(obj, sort_keys=True)
                    if schema_str not in schema_map:
                        schema_name = f"Schema{schema_counter}"
                        schema_counter += 1
                        schema_map[schema_str] = schema_name
                        openapi_spec["components"]["schemas"][schema_name] = obj
                    return {"$ref": f"#/components/schemas/{schema_map[schema_str]}"}
                
                return {k: extract_schemas(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [extract_schemas(item) for item in obj]
            return obj

        for ep in endpoints:
            if not ep.generated_doc_json:
                continue

            path = ep.path
            method = ep.method.lower()

            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}

            doc = ep.generated_doc_json

            operation: Dict[str, Any] = {
                "operationId": f"{ep.handler_function or 'endpoint'}_{ep.id}",
                "summary": doc.get("title", f"{ep.method} {ep.path}"),
                "description": doc.get("description", ""),
                "responses": {}
            }

            if doc.get("tags"):
                operation["tags"] = doc["tags"]

            if doc.get("code_examples"):
                operation["x-code-examples"] = doc["code_examples"]

            raw_params = doc.get("parameters")
            if raw_params and isinstance(raw_params, list):
                cleaned_params = []
                for p in raw_params:
                    if isinstance(p, dict) and "name" in p:
                        param_obj = {
                            "name": str(p["name"]),
                            "in": str(p.get("in", p.get("location", "query"))),
                            "description": str(p.get("description", "")),
                            "required": bool(p.get("required", False)),
                        }
                        if "schema" in p:
                            param_obj["schema"] = extract_schemas(p["schema"])
                        elif "type" in p:
                            param_obj["schema"] = {"type": str(p["type"])}
                        cleaned_params.append(param_obj)
                if cleaned_params:
                    operation["parameters"] = cleaned_params

            if doc.get("request_body"):
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": extract_schemas(doc["request_body"])
                        }
                    }
                }

            if doc.get("responses"):
                extracted_responses = extract_schemas(doc["responses"])
                if isinstance(extracted_responses, list):
                    for resp in extracted_responses:
                        if isinstance(resp, dict):
                            status = str(resp.get("status_code", resp.get("status", "200")))
                            desc = str(resp.get("description", "Response"))
                            resp_obj: Dict[str, Any] = {"description": desc}
                            if "example" in resp and resp["example"]:
                                resp_obj["content"] = {
                                    "application/json": {
                                        "example": resp["example"]
                                    }
                                }
                            operation["responses"][status] = resp_obj

            if not operation["responses"]:
                operation["responses"]["200"] = {"description": "Successful response"}

            openapi_spec["paths"][path][method] = operation

        # Validate spec
        try:
            validate(openapi_spec)
        except Exception as err:
            logger.warning("openapi_validation_warning", error=str(err))

        return openapi_spec
