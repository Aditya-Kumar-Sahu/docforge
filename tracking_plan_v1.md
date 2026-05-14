# DocForge Tracking Plan v1
*Author: Kvasir | Reviewer: Odin*

## Overview
Core event tracking to support the Phase 0 activation funnel: signup → repo connect → scan → endpoint approved.

## Core Events

### 1. Auth & Onboarding
- **`auth_signup`**
  - Trigger: User completes Supabase auth flow
  - Properties: `provider` (github), `plan` (free)

### 2. Repo Lifecycle
- **`repo_connected`**
  - Trigger: User connects a GitHub repository
  - Properties: `repo_name`, `language`, `framework`
- **`repo_scan_triggered`**
  - Trigger: User clicks 'Scan Repo' or PR webhook fires
  - Properties: `repo_id`, `trigger_type` (manual/webhook)
- **`repo_scan_completed`**
  - Trigger: Celery worker completes parsing & LLM generation for a repo
  - Properties: `repo_id`, `endpoints_found`, `duration_ms`

### 3. Review Flow
- **`endpoint_review_action`**
  - Trigger: User approves, edits, or rejects a generated doc
  - Properties: `endpoint_id`, `action` (approve/edit/reject), `quality_score` (from LLM evaluator)

### 4. Export & Value Realization
- **`docs_exported`**
  - Trigger: User downloads OpenAPI spec or Markdown
  - Properties: `format` (openapi/markdown/postman)
