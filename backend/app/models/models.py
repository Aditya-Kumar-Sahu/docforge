import datetime
from typing import Any

from pgvector.sqlalchemy import Vector # type: ignore
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True) # Supabase UID
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    
    repositories: Mapped[list["Repository"]] = relationship(back_populates="owner")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    stripe_subscription_id: Mapped[str] = mapped_column(String, unique=True)
    plan_tier: Mapped[str] = mapped_column(String) # Free, Indie, Team, Company
    status: Mapped[str] = mapped_column(String) # active, trialing, past_due, canceled
    current_period_end: Mapped[datetime.datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="subscriptions")

class Repository(Base):
    __tablename__ = "repositories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String, unique=True)
    github_id: Mapped[int] = mapped_column(Integer, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    
    owner: Mapped["User"] = relationship(back_populates="repositories")
    endpoints: Mapped[list["Endpoint"]] = relationship(back_populates="repository")

class Endpoint(Base):
    __tablename__ = "endpoints"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    path: Mapped[str] = mapped_column(String)
    method: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    summary: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    raw_ast_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    
    repository: Mapped["Repository"] = relationship(back_populates="endpoints")
    docs_versions: Mapped[list["DocumentationVersion"]] = relationship(back_populates="endpoint")

class DocumentationVersion(Base):
    __tablename__ = "docs_versions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoints.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[str] = mapped_column(String, default="1.0.0")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    
    endpoint: Mapped["Endpoint"] = relationship(back_populates="docs_versions")
    reviews: Mapped[list["DocReview"]] = relationship(back_populates="doc_version")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="doc_version")

class DocReview(Base):
    __tablename__ = "doc_reviews"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_version_id: Mapped[int] = mapped_column(ForeignKey("docs_versions.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    feedback: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String) # approved, rejected, revision_requested
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    doc_version: Mapped["DocumentationVersion"] = relationship(back_populates="reviews")

class Chunk(Base):
    __tablename__ = "chunks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_version_id: Mapped[int] = mapped_column(ForeignKey("docs_versions.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    # Using 1536 as per plan (common for OpenAI/modern models)
    embedding: Mapped[Vector | None] = mapped_column(Vector(1536))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    doc_version: Mapped["DocumentationVersion"] = relationship(back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_embedding", embedding, postgresql_using="ivfflat", postgresql_with={"lists": 100}, postgresql_ops={"embedding": "vector_cosine_ops"}),
    )
