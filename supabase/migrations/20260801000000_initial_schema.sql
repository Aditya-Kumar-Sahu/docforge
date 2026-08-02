-- Enable pgvector extension for AI embeddings
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

-- Users table
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    plan VARCHAR NOT NULL DEFAULT 'free',
    github_installation_id VARCHAR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_users_email ON public.users (email);

-- Repos table
CREATE TABLE IF NOT EXISTS public.repos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    url VARCHAR NOT NULL DEFAULT '',
    github_repo_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    language VARCHAR,
    framework VARCHAR,
    scan_status VARCHAR NOT NULL DEFAULT 'pending',
    last_scanned_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_repos_user_id ON public.repos (user_id);

-- Endpoints table
CREATE TABLE IF NOT EXISTS public.endpoints (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL REFERENCES public.repos(id) ON DELETE CASCADE,
    method VARCHAR NOT NULL,
    path VARCHAR NOT NULL,
    handler_function VARCHAR,
    file_path VARCHAR NOT NULL,
    line_number INTEGER,
    params_json JSONB,
    response_schema_json JSONB,
    generated_doc_json JSONB,
    status VARCHAR NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_endpoints_repo_id ON public.endpoints (repo_id);
CREATE INDEX IF NOT EXISTS ix_endpoints_status ON public.endpoints (status);

-- Docs Versions table
CREATE TABLE IF NOT EXISTS public.docs_versions (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL REFERENCES public.repos(id) ON DELETE CASCADE,
    openapi_json JSONB NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    commit_sha VARCHAR,
    diff_summary JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_docs_versions_repo_id ON public.docs_versions (repo_id);

-- Doc Reviews table
CREATE TABLE IF NOT EXISTS public.doc_reviews (
    id SERIAL PRIMARY KEY,
    endpoint_id INTEGER NOT NULL REFERENCES public.endpoints(id) ON DELETE CASCADE,
    status VARCHAR NOT NULL,
    reviewer_comment TEXT,
    approved_by INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_doc_reviews_endpoint_id ON public.doc_reviews (endpoint_id);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR NOT NULL,
    stripe_subscription_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON public.subscriptions (user_id);

-- Chunks table (for vector embedding storage)
CREATE TABLE IF NOT EXISTS public.chunks (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL REFERENCES public.repos(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_chunks_repo_id ON public.chunks (repo_id);
CREATE INDEX IF NOT EXISTS ix_chunks_embedding ON public.chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Enable Storage Buckets if storage schema exists
INSERT INTO storage.buckets (id, name, public)
VALUES ('docs', 'docs', true)
ON CONFLICT (id) DO NOTHING;
