# 🤖 Agent 6 — DocForge
## AI-Powered API Documentation Generator · Full Product Brief

> *Assigned idea: "Point it at your codebase. Get Stripe-quality API docs in minutes."*

---

## Phase 2 — Validation

### ICP (Ideal Customer Profile)

| Segment | Description | Willingness to Pay |
|---------|-------------|-------------------|
| **Primary** | Backend engineers at startups who maintain internal APIs with no docs | Medium-High ($9–$49/mo) |
| **Secondary** | Dev tools / API-first companies publishing external docs | High ($99–$299/mo) |
| **Tertiary** | Developer advocates / DevRel teams maintaining public API references | High |

### Validation Checklist

```
[✓] Pain: "Undocumented internal APIs" is a top-3 complaint in developer surveys
[✓] Willingness to pay: Swagger/OpenAPI tooling, Redocly, Stoplight charge $50–$300/mo
[✓] Competition: Mintlify, Gitbook, Stoplight — none do code→docs AI-first generation
[✓] ICP reachable: Dev.to, r/webdev, r/programming, GitHub open-source community
[✓] Recurring: Codebases change constantly → docs need to stay in sync
```

### Why Now

Mintlify raised $18M proving the market for beautiful API docs. But Mintlify is a *documentation hosting* product, not a *generation* product. DocForge fills the upstream gap: **auto-generating** the content that Mintlify would then host. The two are complements, not competitors — and Mintlify integration is a first-class feature.

### Competitive Landscape

| Tool | What it does | Gap DocForge fills |
|------|-------------|-------------------|
| Swagger/OpenAPI | Auto-generates from decorators | Doesn't work on undocumented legacy code |
| Mintlify | Hosts beautiful docs | Doesn't generate content |
| GitHub Copilot | Suggests code + inline comments | Not structured API docs |
| Postman | API testing + collection sharing | Manual, not auto-generated |
| **DocForge** | Generates full docs from any codebase | End-to-end: code → OpenAPI → rendered docs |

### Pricing Model

| Tier | Price | Includes |
|------|-------|---------|
| **Free (CLI)** | $0 | Open-source CLI, 1 repo, watermarked HTML output |
| **Indie** | $9/mo | Unlimited repos, hosted docs portal, custom domain |
| **Team** | $49/mo | GitHub auto-PR on change, 5 repos, team review, Postman export |
| **Company** | $149/mo | Unlimited repos, SSO, audit log, Confluence sync, Slack alerts |

**Unit Economics (Team tier):**
```
Revenue:            $49/mo
LLM cost:           ~$2/mo  (5 repos, incremental doc updates on PRs, small diffs)
GitHub Actions:     ~$1/mo
Infra:              ~$3/mo
Gross margin:       ~88%  ✅
```

---

## Phase 3 — Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DocForge Platform                         │
│                                                                   │
│  [CLI Tool]              [Web Dashboard]           [GitHub App]  │
│  docforge generate        ┌──────────┐         ┌──────────────┐ │
│       │                   │ Next.js  │         │  GitHub App  │ │
│       │                   │ Frontend │         │  (Webhook)   │ │
│       └───────────────────▶          │         └──────┬───────┘ │
│                           └────┬─────┘                │         │
│                                │                      │         │
│                         ┌──────▼──────────────────────▼──────┐  │
│                         │           FastAPI Backend           │  │
│                         └──────┬──────────────────────┬──────┘  │
│                                │                      │         │
│                   ┌────────────▼────────┐   ┌────────▼───────┐ │
│                   │   Code Parser       │   │  Celery Tasks  │ │
│                   │                     │   │                │ │
│                   │ - Route extractor   │   │ - PR diff doc  │ │
│                   │   (FastAPI/Express/ │   │   update       │ │
│                   │    Django/Rails)    │   │ - Full repo    │ │
│                   │ - Type hint reader  │   │   scan         │ │
│                   │ - Existing comment  │   └────────────────┘ │
│                   │   reader            │                       │
│                   └────────┬────────────┘                       │
│                            │                                     │
│                   ┌────────▼────────────┐                       │
│                   │   AI Doc Generator  │                       │
│                   │                     │                       │
│                   │ LangChain Chain:    │                       │
│                   │ 1. Route Analyzer   │◀── Gemini Flash       │
│                   │ 2. Schema Extractor │                       │
│                   │ 3. Doc Writer       │                       │
│                   │ 4. Example Builder  │                       │
│                   └────────┬────────────┘                       │
│                            │                                     │
│                   ┌────────▼────────────┐                       │
│                   │   Output Layer      │                       │
│                   │                     │                       │
│                   │ - OpenAPI 3.1 JSON  │                       │
│                   │ - Markdown docs     │                       │
│                   │ - Postman Collection│                       │
│                   │ - Mintlify MDX      │                       │
│                   └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

### Data Model

```sql
-- Core
users(id, email, plan, github_installation_id, created_at)
repos(id, user_id, github_repo_id, name, language, framework, last_scanned_at)
endpoints(id, repo_id, method, path, handler_function, file_path, line_number,
          params_json, response_schema_json, generated_doc_json, last_updated_at)
docs_versions(id, repo_id, openapi_json, generated_at, commit_sha, diff_summary)

-- Review flow
doc_reviews(id, endpoint_id, status, reviewer_comment, approved_by, approved_at)

-- Integrations
integrations(id, user_id, type, config_json)  -- type: mintlify|confluence|postman
```

### Code Parser — Framework Support

```python
SUPPORTED_FRAMEWORKS = {
    "fastapi":  FastAPIParser,    # Parses @app.get/post/etc + Pydantic models
    "express":  ExpressParser,    # Parses router.get/post + JSDoc if present
    "django":   DjangoParser,     # Parses urlpatterns + DRF serializers
    "rails":    RailsParser,      # Parses routes.rb + controller methods
    "flask":    FlaskParser,      # Parses @app.route decorators
    "nestjs":   NestJSParser,     # Parses @Controller, @Get/@Post decorators
    "hono":     HonoParser,       # Parses app.get/post (TypeScript Hono)
}

# Auto-detect framework from:
# 1. requirements.txt / package.json
# 2. Import statements in main file
# 3. Common file patterns (manage.py → Django, etc.)
```

### AI Doc Generation Pipeline

```
Step 1: ROUTE EXTRACTION (deterministic, no LLM)
  Input:  Source file(s)
  Action: AST parsing (tree-sitter for multi-language)
  Output: routes[] with {method, path, handler_name, params, return_type}

Step 2: CONTEXT ENRICHMENT
  Input:  Handler function code + surrounding types/schemas
  Action: Extract Pydantic models / TypeScript interfaces / serializers
  Output: enriched_route with full type context

Step 3: DOC GENERATION (LLM)
  Input:  enriched_route
  Prompt:
    "You are a technical writer producing Stripe-quality API documentation.
     For this endpoint, generate:
     - title: short, verb-first (e.g., 'Create a payment intent')
     - description: what it does, when to use it, important caveats (2-3 sentences)
     - parameters: each param with type, required/optional, description, example
     - request_body: schema with field descriptions + example JSON
     - responses: 200 (success schema + example), 400 (validation error), 401, 404
     - code_examples: curl + Python requests + JavaScript fetch
     Be precise. Never fabricate fields not present in the code."
  Output: doc_json per endpoint
  Model:  Gemini Flash | Temp: 0.2

Step 4: OPENAPI ASSEMBLY
  Input:  All doc_jsons
  Action: Assemble valid OpenAPI 3.1 spec
  Validate: openapi-spec-validator library
  Output: openapi.json

Step 5: HUMAN REVIEW GATE
  Action: Show diff of changed endpoints in web UI / PR comment
  Required: Explicit approval before publishing
  (This is the critical trust-building feature — never auto-publish without review)
```

### Key API Endpoints

```
POST /api/repos/connect          — Connect GitHub repo
POST /api/repos/{id}/scan        — Trigger full scan (async)
GET  /api/repos/{id}/endpoints   — List all parsed endpoints
GET  /api/repos/{id}/docs        — Get latest generated OpenAPI spec
POST /api/endpoints/{id}/approve — Approve doc for this endpoint
GET  /api/repos/{id}/export      — Export: openapi.json / markdown / postman
POST /webhooks/github            — GitHub App webhook (PR events)
GET  /api/docs/{repo_id}/preview — Rendered docs preview
```

---

## Phase 4 — MVP Build Plan

### Folder Structure

```
docforge/
├── cli/                        # Python CLI (published to PyPI)
│   ├── docforge/
│   │   ├── parsers/            # Per-framework AST parsers
│   │   ├── generators/         # LangChain doc generation
│   │   └── exporters/          # OpenAPI, Markdown, Postman
│   └── pyproject.toml          # pip install docforge
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── services/
│   │   │   ├── parser.py       # Orchestrates CLI parsers
│   │   │   ├── ai_docs.py      # LangChain generation pipeline
│   │   │   ├── github.py       # GitHub App integration
│   │   │   └── openapi.py      # OpenAPI spec assembler + validator
│   │   └── tasks/              # Celery: scan on PR, full repo scan
│   └── Dockerfile
├── frontend/ (Next.js 14)
│   ├── app/
│   │   ├── repos/              # Repo list + status
│   │   ├── endpoints/          # Endpoint review + approval UI
│   │   ├── docs/               # Rendered docs preview
│   │   └── settings/           # Integrations (Mintlify, Postman)
└── docker-compose.yml
```

### 4-Week Sprint Plan

**Week 1 — Foundation + CLI**
- FastAPI parser (tree-sitter + custom extractor)
- LangChain doc generation pipeline
- CLI tool: `docforge generate --input ./app --output ./docs`
- OpenAPI 3.1 assembler + validator
- Publish to PyPI (free, open-source)

**Week 2 — GitHub Integration**
- GitHub App setup (webhook on PR events)
- PR diff → incremental doc update (only changed endpoints)
- Auto-PR bot: opens PR with updated `docs/openapi.json`
- Supabase auth (GitHub OAuth)

**Week 3 — Web UI + Billing**
- Repo connector + scan progress UI
- Endpoint review UI (approve / edit / reject per endpoint)
- Rendered docs preview (using Redoc component)
- Stripe billing
- Export: OpenAPI JSON + Markdown + Postman collection

**Week 4 — Polish + Launch**
- Express + Django + Flask parser support
- Mintlify export (MDX format)
- Landing page ("Your codebase already has docs. We just have to find them.")
- ProductHunt + Dev.to launch post

### MVP Exclusions (Post-v1)
- Confluence sync
- Slack alerts on doc drift
- SDK generation (TypeScript/Python client from OpenAPI)
- API changelog / versioning tracker

---

## Phase 5 — Launch Strategy

### Landing Page Copy

**Headline:** "Your Codebase Already Has Docs. We Just Have to Find Them."
**Subheadline:** "DocForge reads your FastAPI, Express, or Django code and generates Stripe-quality API documentation automatically. On every PR, your docs stay up to date."
**CTA:** "Generate Docs from Your Repo →"

**3 Feature Bullets:**
1. 🔍 *Code-first, not decorator-first* — works on legacy code with no existing docs, no annotations required
2. 🤖 *Auto-updates on every PR* — when your API changes, your docs change too (no stale docs, ever)
3. 📦 *Export anywhere* — OpenAPI JSON, Mintlify MDX, Postman Collection, plain Markdown — one click

### Distribution Channels (Ranked by ROI)

| # | Channel | Effort | Expected Return |
|---|---------|--------|----------------|
| 1 | Open-source CLI on GitHub + HN "Show HN" post | Low | Very High (dev audience) |
| 2 | Dev.to / Hashnode technical blog post ("How we auto-generated our API docs") | Low | High |
| 3 | r/webdev, r/Python, r/node | Low | Medium–High |
| 4 | GitHub Marketplace listing (GitHub App) | Medium | High (captive dev audience) |
| 5 | ProductHunt | Medium | Medium |

### Open-Source GTM Strategy

The CLI is open-source (MIT license). This serves as:
1. **Top-of-funnel**: Developers discover via GitHub/PyPI → try CLI → want hosted features → upgrade
2. **Trust signal**: "If I can read the code, I trust it won't leak my codebase"
3. **Community contributions**: Parser support for new frameworks added by the community
4. **SEO moat**: Open-source GitHub repo earns organic backlinks and stars over time

### Moat-Building Roadmap

```
Month 1–3:  Open-source stars → community adds parsers for new frameworks
Month 3–6:  Collect approved/rejected doc pairs → proprietary training dataset
Month 6+:   Fine-tune model on "developer-approved" API documentation style
Year 2:     "DocForge Verified" badge — external API users trust docs
            Become the standard for API doc generation (network effect)
```

---

## Technical Deep Dive: The Human Review Gate

This is the most important product decision. Never auto-publish AI-generated docs without human approval. The review UI shows:

```
┌──────────────────────────────────────────────────────────────┐
│ POST /api/payments/create-intent          [REVIEW REQUIRED]  │
├──────────────────────────────────────────────────────────────┤
│ AI Generated:                   Your Edit:                   │
│                                                              │
│ Title: Create a payment intent  [Create a payment intent   ] │
│                                                              │
│ Description: Creates a new      [                           ]│
│ Stripe payment intent and       [                           ]│
│ returns the client_secret       [                           ]│
│ for frontend confirmation.      [                           ]│
│                                                              │
│ [✓ Approve]  [✎ Edit]  [✗ Reject & Regenerate]              │
└──────────────────────────────────────────────────────────────┘
```

Every rejection is a training signal. After 100 rejected docs per framework, the model improves substantially through few-shot examples in the system prompt.
