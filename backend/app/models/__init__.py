from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector  # type: ignore

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    plan: Mapped[str] = mapped_column(String, default="free")
    github_installation_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class Repo(Base, TimestampMixin):
    __tablename__ = "repos"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    github_repo_id: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    framework: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class Endpoint(Base, TimestampMixin):
    __tablename__ = "endpoints"
    id: Mapped[int] = mapped_column(primary_key=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), index=True)
    method: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String)
    handler_function: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_path: Mapped[str] = mapped_column(String)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    params_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    response_schema_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    generated_doc_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending", index=True)

class DocsVersion(Base, TimestampMixin):
    __tablename__ = "docs_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), index=True)
    openapi_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    commit_sha: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    diff_summary: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

class DocReview(Base, TimestampMixin):
    __tablename__ = "doc_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoints.id"), index=True)
    status: Mapped[str] = mapped_column(String)
    reviewer_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stripe_customer_id: Mapped[str] = mapped_column(String)
    stripe_subscription_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)

class Chunk(Base, TimestampMixin):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(1536), nullable=True)

    __table_args__ = (
        Index('ix_chunks_embedding', 'embedding', postgresql_using='ivfflat', postgresql_with={'lists': 100}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )

