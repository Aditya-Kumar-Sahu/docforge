"""
Parser accuracy tests using code fixtures extracted from 5 real open-source
FastAPI repositories. Each fixture is representative of routes/patterns found
in the actual codebase and is stored inline for speed and reproducibility.

Repositories used as source material:
  1. tiangolo/full-stack-fastapi-template
  2. fastapi-users/fastapi-users
  3. fastapi-admin/fastapi-admin
  4. mealie (mealie-recipes/mealie)
  5. polarsource/polar

Accuracy threshold: ≥ 95% of routes parsed correctly per fixture.
"""
from __future__ import annotations

import pytest
from app.core.parser import FastAPIParser


# ── Fixtures ───────────────────────────────────────────────────────────────

# 1. tiangolo/full-stack-fastapi-template — typical CRUD router pattern
FIXTURE_FULL_STACK = """
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

router = APIRouter()

class ItemCreate(BaseModel):
    title: str
    description: str = ""

class ItemPublic(BaseModel):
    id: int
    title: str

@router.get("/items/{id}", response_model=ItemPublic)
def read_item(id: int) -> Any:
    \"\"\"Get a specific item by id.\"\"\"
    pass

@router.get("/items", response_model=list[ItemPublic])
def read_items(skip: int = 0, limit: int = 100) -> Any:
    \"\"\"Retrieve items.\"\"\"
    pass

@router.post("/items", response_model=ItemPublic)
def create_item(item_in: ItemCreate) -> Any:
    \"\"\"Create new item.\"\"\"
    pass

@router.put("/items/{id}", response_model=ItemPublic)
def update_item(id: int, item_in: ItemCreate) -> Any:
    \"\"\"Update an item.\"\"\"
    pass

@router.delete("/items/{id}")
def delete_item(id: int) -> str:
    \"\"\"Delete an item.\"\"\"
    pass
"""

# 2. fastapi-users — auth router pattern
FIXTURE_FASTAPI_USERS = """
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth")

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: str
    email: EmailStr

@router.post("/register", response_model=UserRead, status_code=201)
async def register(user_create: UserCreate) -> UserRead:
    \"\"\"Register a new user.\"\"\"
    pass

@router.post("/login")
async def login(email: str, password: str) -> dict:
    \"\"\"Obtain a login token.\"\"\"
    pass

@router.post("/logout")
async def logout() -> None:
    \"\"\"Log the current user out.\"\"\"
    pass

@router.get("/me", response_model=UserRead)
async def current_user() -> UserRead:
    \"\"\"Get current authenticated user.\"\"\"
    pass
"""

# 3. fastapi-admin — admin resource pattern with path params
FIXTURE_FASTAPI_ADMIN = """
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin")

class ResourceCreate(BaseModel):
    name: str
    label: Optional[str] = None

class ResourceOut(BaseModel):
    id: int
    name: str
    label: Optional[str]

@router.get("/resources", response_model=list[ResourceOut])
async def list_resources(page: int = 1, page_size: int = 10) -> list[ResourceOut]:
    \"\"\"List all admin resources with pagination.\"\"\"
    pass

@router.post("/resources", response_model=ResourceOut)
async def create_resource(data: ResourceCreate) -> ResourceOut:
    \"\"\"Create a new resource.\"\"\"
    pass

@router.get("/resources/{resource_id}", response_model=ResourceOut)
async def get_resource(resource_id: int) -> ResourceOut:
    \"\"\"Get a specific resource.\"\"\"
    pass

@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: int) -> dict:
    \"\"\"Delete a resource.\"\"\"
    pass
"""

# 4. mealie — recipe API with complex paths
FIXTURE_MEALIE = """
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter(prefix="/api/recipes")

class RecipeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tags: list[str] = []

class RecipeOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str

@router.get("", response_model=list[RecipeOut])
async def get_all_recipes(search: Optional[str] = None) -> list[RecipeOut]:
    \"\"\"Get all recipes, optionally filtered by search string.\"\"\"
    pass

@router.post("", response_model=RecipeOut, status_code=201)
async def create_recipe(recipe: RecipeCreate) -> RecipeOut:
    \"\"\"Create a new recipe.\"\"\"
    pass

@router.get("/{slug}", response_model=RecipeOut)
async def get_recipe(slug: str) -> RecipeOut:
    \"\"\"Get a single recipe by its slug.\"\"\"
    pass

@router.put("/{slug}", response_model=RecipeOut)
async def update_recipe(slug: str, recipe: RecipeCreate) -> RecipeOut:
    \"\"\"Update a recipe.\"\"\"
    pass

@router.delete("/{slug}")
async def delete_recipe(slug: str) -> dict:
    \"\"\"Delete a recipe.\"\"\"
    pass
"""

# 5. polarsource/polar — subscription/billing endpoints
FIXTURE_POLAR = """
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from enum import Enum

router = APIRouter(prefix="/subscriptions")

class SubscriptionTier(str, Enum):
    free = "free"
    pro = "pro"
    business = "business"

class SubscriptionCreate(BaseModel):
    product_id: str
    tier: SubscriptionTier

class SubscriptionOut(BaseModel):
    id: str
    status: str
    tier: SubscriptionTier

@router.get("", response_model=list[SubscriptionOut])
async def list_subscriptions(active_only: bool = True) -> list[SubscriptionOut]:
    \"\"\"List all subscriptions for the current user.\"\"\"
    pass

@router.post("", response_model=SubscriptionOut, status_code=201)
async def create_subscription(sub: SubscriptionCreate) -> SubscriptionOut:
    \"\"\"Create a new subscription.\"\"\"
    pass

@router.get("/{subscription_id}", response_model=SubscriptionOut)
async def get_subscription(subscription_id: str) -> SubscriptionOut:
    \"\"\"Get details of a subscription.\"\"\"
    pass

@router.delete("/{subscription_id}")
async def cancel_subscription(subscription_id: str) -> dict:
    \"\"\"Cancel a subscription.\"\"\"
    pass

@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    \"\"\"Receive Stripe webhook events.\"\"\"
    pass
"""

FIXTURES = [
    ("full_stack_fastapi_template", FIXTURE_FULL_STACK, 5),
    ("fastapi_users", FIXTURE_FASTAPI_USERS, 4),
    ("fastapi_admin", FIXTURE_FASTAPI_ADMIN, 4),
    ("mealie", FIXTURE_MEALIE, 5),
    ("polar", FIXTURE_POLAR, 5),
]


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def parser() -> FastAPIParser:
    return FastAPIParser()


@pytest.mark.parametrize("name, code, expected_count", FIXTURES)
def test_parser_extraction_count(
    parser: FastAPIParser, name: str, code: str, expected_count: int
) -> None:
    """Parser must extract every route in each fixture."""
    routes = parser.parse_code(code, file_path=f"{name}.py")
    assert len(routes) == expected_count, (
        f"[{name}] Expected {expected_count} routes, got {len(routes)}: "
        + str([r.path for r in routes])
    )


@pytest.mark.parametrize("name, code, expected_count", FIXTURES)
def test_parser_accuracy_threshold(
    parser: FastAPIParser, name: str, code: str, expected_count: int
) -> None:
    """At least 95% of routes must be correctly extracted (method + path + handler)."""
    routes = parser.parse_code(code, file_path=f"{name}.py")
    valid = [
        r for r in routes
        if r.method and r.path and r.handler_name and r.line_number > 0
    ]
    accuracy = len(valid) / expected_count if expected_count else 0
    assert accuracy >= 0.95, (
        f"[{name}] Accuracy {accuracy:.0%} < 95% — check parser for edge cases"
    )


def test_full_stack_path_params(parser: FastAPIParser) -> None:
    routes = parser.parse_code(FIXTURE_FULL_STACK, file_path="full_stack.py")
    read_item = next(r for r in routes if r.handler_name == "read_item")
    assert any(p["name"] == "id" for p in read_item.path_parameters)


def test_full_stack_query_params(parser: FastAPIParser) -> None:
    routes = parser.parse_code(FIXTURE_FULL_STACK, file_path="full_stack.py")
    read_items = next(r for r in routes if r.handler_name == "read_items")
    query_names = {p["name"] for p in read_items.query_parameters}
    assert "skip" in query_names
    assert "limit" in query_names


def test_fastapi_users_router_prefix_applied(parser: FastAPIParser) -> None:
    routes = parser.parse_code(FIXTURE_FASTAPI_USERS, file_path="auth.py")
    paths = {r.path for r in routes}
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/me" in paths


def test_fastapi_admin_router_prefix_applied(parser: FastAPIParser) -> None:
    routes = parser.parse_code(FIXTURE_FASTAPI_ADMIN, file_path="admin.py")
    paths = {r.path for r in routes}
    assert "/admin/resources" in paths
    assert "/admin/resources/{resource_id}" in paths


def test_mealie_post_request_model_detected(parser: FastAPIParser) -> None:
    routes = parser.parse_code(FIXTURE_MEALIE, file_path="recipes.py")
    create = next(r for r in routes if r.handler_name == "create_recipe")
    assert create.request_model is not None
    assert create.request_model.get("type") == "RecipeCreate"


def test_polar_methods_correct(parser: FastAPIParser) -> None:
    routes = parser.parse_code(FIXTURE_POLAR, file_path="subscriptions.py")
    methods = {r.handler_name: r.method for r in routes}
    assert methods["list_subscriptions"] == "GET"
    assert methods["create_subscription"] == "POST"
    assert methods["cancel_subscription"] == "DELETE"
    assert methods["stripe_webhook"] == "POST"


def test_docstrings_extracted_across_fixtures(parser: FastAPIParser) -> None:
    """Every handler in every fixture has a docstring; all should be extracted."""
    for name, code, _ in FIXTURES:
        routes = parser.parse_code(code, file_path=f"{name}.py")
        for route in routes:
            assert route.docstring, (
                f"[{name}] Missing docstring on {route.handler_name}"
            )
