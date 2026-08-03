"""
20 diverse real-world API endpoint fixtures for DocForge prompt tuning and benchmark evaluation.
Mix of CRUD, auth-protected, complex business logic, query-heavy, and webhook endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List
from app.models.route import ParsedRoute

BENCHMARK_ENDPOINTS: List[Dict[str, Any]] = [
    # 1. Simple Read
    {
        "id": "ep_01_user_profile",
        "route": ParsedRoute(
            method="GET",
            path="/api/v1/users/{user_id}",
            handler_name="get_user_profile",
            file_path="app/api/users.py",
            line_number=15,
            path_parameters=[{"name": "user_id", "type": "str"}],
            query_parameters=[{"name": "include_metadata", "type": "bool"}],
            request_model=None,
            response_model={"type": "UserProfileResponse"},
            docstring="Fetch a user profile by unique ID with optional metadata.",
        ),
        "source_code": """
@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str, include_metadata: bool = False, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
"""
    },
    # 2. Simple Create
    {
        "id": "ep_02_create_item",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/items",
            handler_name="create_item",
            file_path="app/api/items.py",
            line_number=25,
            path_parameters=[],
            query_parameters=[],
            request_model={"type": "ItemCreate", "fields": ["name", "price", "category"]},
            response_model={"type": "ItemResponse"},
            docstring="Create a new item in the catalog.",
        ),
        "source_code": """
@router.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate, current_user: User = Depends(get_current_user)):
    new_item = Item(**item.model_dump(), owner_id=current_user.id)
    db.add(new_item)
    db.commit()
    return new_item
"""
    },
    # 3. Update with Patch
    {
        "id": "ep_03_patch_settings",
        "route": ParsedRoute(
            method="PATCH",
            path="/api/v1/settings",
            handler_name="update_user_settings",
            file_path="app/api/settings.py",
            line_number=40,
            path_parameters=[],
            query_parameters=[],
            request_model={"type": "SettingsUpdate", "fields": ["theme", "notifications_enabled"]},
            response_model={"type": "SettingsResponse"},
            docstring="Partial update of account settings.",
        ),
        "source_code": """
@router.patch("/settings", response_model=SettingsResponse)
async def update_user_settings(payload: SettingsUpdate, user: User = Depends(get_current_user)):
    # Partial update logic
    return user.settings
"""
    },
    # 4. Delete Resource
    {
        "id": "ep_04_delete_repo",
        "route": ParsedRoute(
            method="DELETE",
            path="/api/v1/repos/{repo_id}",
            handler_name="delete_repository",
            file_path="app/api/repos.py",
            line_number=60,
            path_parameters=[{"name": "repo_id", "type": "int"}],
            query_parameters=[{"name": "force", "type": "bool"}],
            request_model=None,
            response_model={"type": "MessageResponse"},
            docstring="Delete a repository permanently.",
        ),
        "source_code": """
@router.delete("/repos/{repo_id}")
async def delete_repository(repo_id: int, force: bool = False, user: User = Depends(get_current_user)):
    # Delete logic with side effects
    return {"message": "Repository deleted"}
"""
    },
    # 5. Search / Query List
    {
        "id": "ep_05_search_products",
        "route": ParsedRoute(
            method="GET",
            path="/api/v1/products/search",
            handler_name="search_products",
            file_path="app/api/products.py",
            line_number=10,
            path_parameters=[],
            query_parameters=[
                {"name": "q", "type": "str"},
                {"name": "min_price", "type": "float"},
                {"name": "max_price", "type": "float"},
                {"name": "limit", "type": "int"},
                {"name": "offset", "type": "int"},
            ],
            request_model=None,
            response_model={"type": "ProductListResponse"},
            docstring="Search product catalog with keyword search and price filters.",
        ),
        "source_code": """
@router.get("/products/search")
async def search_products(q: str, min_price: float = 0, max_price: float = 1000, limit: int = 20, offset: int = 0):
    return {"items": [], "total": 0}
"""
    },
    # 6. Authentication Token Issue
    {
        "id": "ep_06_login",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/auth/login",
            handler_name="login_access_token",
            file_path="app/api/auth.py",
            line_number=30,
            path_parameters=[],
            query_parameters=[],
            request_model={"type": "OAuth2PasswordRequestForm"},
            response_model={"type": "TokenResponse"},
            docstring="OAuth2 compatible token login, get an access token for future requests.",
        ),
        "source_code": """
@router.post("/auth/login")
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    return {"access_token": create_token(user.id), "token_type": "bearer"}
"""
    },
    # 7. Webhook Handler
    {
        "id": "ep_07_stripe_webhook",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/webhooks/stripe",
            handler_name="stripe_webhook_event",
            file_path="app/api/webhooks.py",
            line_number=100,
            path_parameters=[],
            query_parameters=[],
            request_model=None,
            response_model={"type": "WebhookAck"},
            docstring="Process incoming Stripe webhook events (checkout.session.completed, invoice.payment_succeeded).",
        ),
        "source_code": """
@router.post("/webhooks/stripe")
async def stripe_webhook_event(request: Request, stripe_signature: str = Header(...)):
    # Verify signature and process event
    return {"status": "received"}
"""
    },
    # 8. File Upload Endpoint
    {
        "id": "ep_08_upload_avatar",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/users/me/avatar",
            handler_name="upload_avatar",
            file_path="app/api/users.py",
            line_number=80,
            path_parameters=[],
            query_parameters=[],
            request_model={"type": "UploadFile"},
            response_model={"type": "AvatarResponse"},
            docstring="Upload a new profile avatar image (PNG/JPEG under 5MB).",
        ),
        "source_code": """
@router.post("/users/me/avatar")
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    # Save file and return URL
    return {"avatar_url": "http://cdn.example.com/avatar.jpg"}
"""
    },
    # 9. Complex Calculation / Financial
    {
        "id": "ep_09_calculate_tax",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/checkout/calculate-tax",
            handler_name="calculate_checkout_tax",
            file_path="app/api/checkout.py",
            line_number=50,
            path_parameters=[],
            query_parameters=[],
            request_model={"type": "TaxCalculationRequest", "fields": ["line_items", "shipping_address", "currency"]},
            response_model={"type": "TaxCalculationResponse"},
            docstring="Calculate sales tax and vat rates for a cart checkout session.",
        ),
        "source_code": """
@router.post("/checkout/calculate-tax")
async def calculate_checkout_tax(payload: TaxCalculationRequest):
    # Call Taxjar/Stripe Tax API
    return {"tax_total": 12.50, "currency": "USD"}
"""
    },
    # 10. Bulk Action
    {
        "id": "ep_10_bulk_delete_tasks",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/tasks/bulk-delete",
            handler_name="bulk_delete_tasks",
            file_path="app/api/tasks.py",
            line_number=120,
            path_parameters=[],
            query_parameters=[],
            request_model={"type": "BulkDeleteRequest", "fields": ["task_ids"]},
            response_model={"type": "BulkDeleteResult"},
            docstring="Delete multiple task items by array of IDs.",
        ),
        "source_code": """
@router.post("/tasks/bulk-delete")
async def bulk_delete_tasks(req: BulkDeleteRequest, user: User = Depends(get_current_user)):
    return {"deleted_count": len(req.task_ids)}
"""
    },
    # 11. Pagination Cursor
    {
        "id": "ep_11_list_audit_logs",
        "route": ParsedRoute(
            method="GET",
            path="/api/v1/audit-logs",
            handler_name="list_audit_logs",
            file_path="app/api/logs.py",
            line_number=15,
            path_parameters=[],
            query_parameters=[
                {"name": "cursor", "type": "str"},
                {"name": "limit", "type": "int"},
                {"name": "action_type", "type": "str"},
            ],
            request_model=None,
            response_model={"type": "PaginatedAuditLogs"},
            docstring="List system audit logs with cursor pagination and action type filtering.",
        ),
        "source_code": """
@router.get("/audit-logs")
async def list_audit_logs(cursor: str | None = None, limit: int = 50, action_type: str | None = None):
    return {"data": [], "next_cursor": None}
"""
    },
    # 12. Subscription Management
    {
        "id": "ep_12_cancel_subscription",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/subscriptions/{sub_id}/cancel",
            handler_name="cancel_subscription",
            file_path="app/api/billing.py",
            line_number=90,
            path_parameters=[{"name": "sub_id", "type": "str"}],
            query_parameters=[{"name": "at_period_end", "type": "bool"}],
            request_model=None,
            response_model={"type": "SubscriptionStatus"},
            docstring="Cancel an active subscription plan immediately or at the end of the billing cycle.",
        ),
        "source_code": """
@router.post("/subscriptions/{sub_id}/cancel")
async def cancel_subscription(sub_id: str, at_period_end: bool = True):
    return {"status": "canceled"}
"""
    },
    # 13. Password Reset Request
    {
        "id": "ep_13_forgot_password",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/auth/forgot-password",
            handler_name="request_password_reset",
            file_path="app/api/auth.py",
            line_number=70,
            path_parameters=[],
            query_parameters=[],
            request_model={"type": "ForgotPasswordRequest", "fields": ["email"]},
            response_model={"type": "MessageResponse"},
            docstring="Request a password reset email token.",
        ),
        "source_code": """
@router.post("/auth/forgot-password")
async def request_password_reset(body: ForgotPasswordRequest):
    # Send email token
    return {"message": "Password reset email sent"}
"""
    },
    # 14. Export Data Report
    {
        "id": "ep_14_export_analytics",
        "route": ParsedRoute(
            method="GET",
            path="/api/v1/analytics/export",
            handler_name="export_analytics_data",
            file_path="app/api/analytics.py",
            line_number=45,
            path_parameters=[],
            query_parameters=[{"name": "format", "type": "str"}, {"name": "start_date", "type": "str"}],
            request_model=None,
            response_model={"type": "FileDownload"},
            docstring="Export analytics summary report as CSV or JSON format.",
        ),
        "source_code": """
@router.get("/analytics/export")
async def export_analytics_data(format: str = "csv", start_date: str = "2026-01-01"):
    return Response(content="date,views\n2026-01-01,100", media_type="text/csv")
"""
    },
    # 15. Nested Resource Create
    {
        "id": "ep_15_add_comment",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/posts/{post_id}/comments",
            handler_name="create_post_comment",
            file_path="app/api/comments.py",
            line_number=20,
            path_parameters=[{"name": "post_id", "type": "int"}],
            query_parameters=[],
            request_model={"type": "CommentCreate", "fields": ["content", "parent_id"]},
            response_model={"type": "CommentResponse"},
            docstring="Add a new comment or reply under a specific blog post.",
        ),
        "source_code": """
@router.post("/posts/{post_id}/comments")
async def create_post_comment(post_id: int, comment: CommentCreate, user: User = Depends(get_current_user)):
    return {"id": 1, "post_id": post_id, "content": comment.content}
"""
    },
    # 16. API Key Generation
    {
        "id": "ep_16_create_api_key",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/api-keys",
            handler_name="generate_api_key",
            file_path="app/api/keys.py",
            line_number=30,
            path_parameters=[],
            query_parameters=[],
            request_model={"type": "APIKeyCreate", "fields": ["name", "scopes", "expires_in_days"]},
            response_model={"type": "APIKeyCreatedResponse"},
            docstring="Generate a new API secret key with specific scopes and expiration.",
        ),
        "source_code": """
@router.post("/api-keys")
async def generate_api_key(req: APIKeyCreate, user: User = Depends(get_current_user)):
    return {"name": req.name, "key": "df_live_secret12345"}
"""
    },
    # 17. Metrics Summary
    {
        "id": "ep_17_repo_stats",
        "route": ParsedRoute(
            method="GET",
            path="/api/v1/repos/{repo_id}/stats",
            handler_name="get_repo_statistics",
            file_path="app/api/stats.py",
            line_number=10,
            path_parameters=[{"name": "repo_id", "type": "int"}],
            query_parameters=[{"name": "range", "type": "str"}],
            request_model=None,
            response_model={"type": "RepoStatsResponse"},
            docstring="Get repository scan statistics, quality score distributions, and endpoint counts.",
        ),
        "source_code": """
@router.get("/repos/{repo_id}/stats")
async def get_repo_statistics(repo_id: int, range: str = "30d"):
    return {"total_endpoints": 42, "approved": 38, "avg_quality": 8.4}
"""
    },
    # 18. Revoke Permission
    {
        "id": "ep_18_revoke_member",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/teams/{team_id}/members/{user_id}/revoke",
            handler_name="revoke_team_member",
            file_path="app/api/teams.py",
            line_number=85,
            path_parameters=[{"name": "team_id", "type": "int"}, {"name": "user_id", "type": "int"}],
            query_parameters=[],
            request_model=None,
            response_model={"type": "MessageResponse"},
            docstring="Revoke a team member's access privileges.",
        ),
        "source_code": """
@router.post("/teams/{team_id}/members/{user_id}/revoke")
async def revoke_team_member(team_id: int, user_id: int, current_user: User = Depends(get_current_user)):
    return {"message": "Member access revoked"}
"""
    },
    # 19. System Status Detail
    {
        "id": "ep_19_system_health_detail",
        "route": ParsedRoute(
            method="GET",
            path="/api/v1/system/health-detail",
            handler_name="get_system_health_detail",
            file_path="app/api/health.py",
            line_number=20,
            path_parameters=[],
            query_parameters=[],
            request_model=None,
            response_model={"type": "SystemHealthDetail"},
            docstring="Detailed system health report including PostgreSQL, Redis, Celery, and LLM gateway status.",
        ),
        "source_code": """
@router.get("/system/health-detail")
async def get_system_health_detail():
    return {"postgres": "healthy", "redis": "healthy", "celery": "active"}
"""
    },
    # 20. OpenAPI Spec Import Endpoint
    {
        "id": "ep_20_import_openapi_spec",
        "route": ParsedRoute(
            method="POST",
            path="/api/v1/repos/{repo_id}/import-spec",
            handler_name="import_openapi_spec",
            file_path="app/api/importer.py",
            line_number=50,
            path_parameters=[{"name": "repo_id", "type": "int"}],
            query_parameters=[],
            request_model={"type": "SpecImportRequest", "fields": ["spec_json", "overwrite_existing"]},
            response_model={"type": "SpecImportResult"},
            docstring="Import an existing OpenAPI 3.0/3.1 JSON specification into a repository.",
        ),
        "source_code": """
@router.post("/repos/{repo_id}/import-spec")
async def import_openapi_spec(repo_id: int, body: SpecImportRequest):
    return {"imported_routes": 15, "overwritten": False}
"""
    },
]
