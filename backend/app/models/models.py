from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, Text, DateTime, func, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from typing import List, Optional
import datetime

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True) # Supabase UID
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    repositories: Mapped[List["Repository"]] = relationship(back_populates="owner")

class Repository(Base):
    __tablename__ = "repositories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String, unique=True)
    github_id: Mapped[int] = mapped_column(Integer, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    owner: Mapped["User"] = relationship(back_populates="repositories")
    endpoints: Mapped[List["Endpoint"]] = relationship(back_populates="repository")

class Endpoint(Base):
    __tablename__ = "endpoints"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    path: Mapped[str] = mapped_column(String)
    method: Mapped[str] = mapped_column(String)
    summary: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    raw_ast_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    repository: Mapped["Repository"] = relationship(back_populates="endpoints")
    documentations: Mapped[List["Documentation"]] = relationship(back_populates="endpoint")

class Documentation(Base):
    __tablename__ = "documentations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoints.id"))
    content: Mapped[str] = mapped_column(Text)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[str] = mapped_column(String, default="1.0.0")
    # 768 is common for Gemini/OpenAI embeddings
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(768)) 
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    endpoint: Mapped["Endpoint"] = relationship(back_populates="documentations")
