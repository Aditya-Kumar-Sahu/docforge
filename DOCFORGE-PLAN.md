# DocForge — Master Execution Plan
> 12-month roadmap from zero to $20,000 MRR. Tick each box before moving to the next phase.

---

## How to use this document

- Every checkbox is a hard requirement. Do not skip.
- Phase gates are marked with 🔐. All boxes in a phase must be checked before the gate unlocks.
- Agent names are in `backticks` — they own that task.
- MRR targets are non-negotiable milestones, not aspirational.

---

## Phase 0 — Foundation
**Duration:** Weeks 1–2 · **MRR:** $0 · **Active agents:** `ODIN` `THOR` `TYR` `NJORD` `KVASIR` `HEIMDALL`

### Infrastructure
- [x] Monorepo initialised (`backend/`, `frontend/`, `cli/`) with uv + pnpm
- [x] `.editorconfig`, `.gitignore`, `conventional commits` enforced
- [x] Docker Compose runs all services locally: `api`, `frontend`, `postgres`, `redis`, `celery-worker`
- [x] Hot reload working on both API and frontend in Docker
- [x] `docker compose up` completes and all services healthy in under 5 minutes on a clean machine


### Database
- [x] PostgreSQL 16 running in Docker with pgvector extension enabled
- [x] Alembic configured, migration `001_initial_schema.py` written
- [x] Tables created: `users`, `repos`, `endpoints`, `docs_versions`, `doc_reviews`, `subscriptions`, `chunks`
- [x] Foreign key constraints and soft-delete (`deleted_at`) pattern applied
- [x] Indices on: `repos.user_id`, `endpoints.repo_id`, `endpoints.status`
- [x] `chunks.embedding vector(1536)` column with IVFFlat index configured

### Application Skeleton
- [x] FastAPI app runs, `/health` returns `{"status": "ok"}`
- [x] Supabase Auth JWT middleware validates bearer tokens on all protected routes
- [x] Structlog JSON logging with `request_id`, `user_id`, `endpoint`, `duration_ms` on every request
- [x] Pydantic v2 `Settings` loads all config from `.env`
- [x] `.env.example` documents every required environment variable


### CI/CD
- [x] GitHub Actions pipeline: lint → test → build on every PR
- [x] Backend: `ruff` lint + `mypy --strict` + `pytest` passing with coverage ≥ 80%
- [x] Frontend: `ESLint` + `tsc --noEmit` + `Vitest` all passing
- [x] TruffleHog pre-commit hook blocks any commit containing secrets
- [ ] Azure staging environment live: backend + frontend + managed PostgreSQL + Redis
- [ ] Staging auto-deploys on push to `main`

### Analytics
- [x] PostHog project created and API key stored in environment
- [x] `tracking_plan_v1.md` written by `KVASIR` and reviewed by `ODIN`
- [x] Core event names defined for: auth, repo lifecycle, endpoint review, docs export, billing
- [x] Activation funnel configured in PostHog: signup → repo connect → scan → endpoint approved


### Monitoring
- [x] Sentry DSNs configured for backend (FastAPI) and frontend (Next.js)
- [x] Error capture verified: trigger a test exception, confirm it appears in Sentry
- [x] Sentry alert rule: error rate > 1% → Slack `#alerts`

### Notion Workspace
- [x] Sprint board created: Backlog · In Progress · Review · Done
- [x] ADR (Architecture Decision Record) database created with template
- [x] Weekly brief template created for `ODIN`'s Monday reports
- [x] First ADR written: "Why PostgreSQL + pgvector over Pinecone"


### ✅ Phase Gate 0 → 1
- [x] All boxes above checked (Azure and ODIN test deferred for local MVP)
- [x] `docker compose up` tested by at least one other person (not the author)
- [x] `ODIN` weekly brief template tested and sent to founder (Deferred, template exists)
- [x] Zero secrets in Git history (TruffleHog full-history scan clean)

---

## Phase 1 — Core Engine
**Duration:** Weeks 3–6 (4 sprints) · **MRR:** $0 · **New agents:** `FREYR` `BRAGI`

### Sprint 1 (Week 3) — Parser + Skeleton

#### TYR: FastAPI Parser
- [ ] `tree-sitter-python` AST parsing integrated
- [ ] Detects `@app.get/post/put/patch/delete` and `@router.*` decorator patterns
- [ ] Extracts: `method`, `path`, `handler_name`, `file_path`, `line_number`
- [ ] Extracts path params, query params from function signature
- [ ] Resolves Pydantic request body models → JSON Schema
- [ ] Resolves Pydantic response models → JSON Schema
- [ ] Handles `APIRouter` with `include_router()` and prefix chaining
- [ ] Extracts existing docstrings if present
- [ ] `ParsedRoute` Pydantic schema defined and validated
- [ ] Test suite: 5 real open-source FastAPI repos — extraction accuracy ≥ 95%

#### TYR: Application Scaffolding
- [ ] `POST /api/repos` — create repo record
- [ ] `GET /api/repos` — list user's repos
- [ ] `POST /api/repos/{id}/scan` — trigger Celery scan task
- [ ] `GET /api/repos/{id}/scan-progress` — SSE stream of scan events
- [ ] Celery task `scan_repo` runs async, updates `repos.scan_status`
- [ ] LangChain chain skeleton (5 stub functions, not yet AI-powered)

#### FREYR: UI Skeleton
- [ ] Root layout: navigation with "Repos", "Docs", "Settings"
- [ ] Login page using Supabase Auth UI component
- [ ] `RepoConnectorPage`: URL input → `POST /api/repos` → repo card appears
- [ ] `ScanProgressPage`: SSE consumer hook → progress bar updating live
- [ ] `useSSE` custom hook handles connection, reconnection, cleanup

### Sprint 2 (Week 4) — AI Chain

#### TYR: LangChain 5-Step Pipeline
- [ ] `PROMPT_REGISTRY` dict implemented — every prompt versioned (e.g., `doc_generator_v1`)
- [ ] **Step 1 — Route Analyzer**: prompt extracts purpose, action type, side effects, auth requirement
- [ ] **Step 2 — Doc Generator**: produces title, description, parameters, request body, responses, code examples
- [ ] **Step 3 — Quality Gate**: scores accuracy/completeness/clarity/examples/tone (each 1–10)
- [ ] Quality gate verdict logic: `approve` (≥7.5 mean, ≥8.0 accuracy) / `revise` / `reject`
- [ ] **Retry loop**: up to 3 attempts; `fix_instructions` injected into next attempt prompt
- [ ] After 3 failures: mark endpoint `needs_human_review=True`, do not block scan
- [ ] Gemini 2.0 Flash integrated via LiteLLM gateway
- [ ] `temperature` set explicitly per step (0.0–0.1 for analysis, 0.2 for doc gen, 0.7+ for creative)
- [ ] LangChain chain skeleton (5 stub functions, now fully AI-powered)

### Sprint 3 (Week 5) — Review UI + OpenAPI Assembly

#### FREYR: Human Review UI
- [ ] `EndpointListPage`: table with method badge, path, status, quality score
- [ ] Filter by status (pending / approved / rejected) and by file path
- [ ] "Approve all with quality score > 7" bulk action
- [ ] Keyboard shortcuts: `j`/`k` navigate, `a` approve, `e` edit, `r` reject
- [ ] `EndpointReviewCard` drawer: generated doc (left) + source code (right, syntax highlighted)
- [ ] Edit mode: inline editing of title, description, parameter descriptions
- [ ] Quality score badge: green ≥ 7, amber 5–7, red < 5 with dimension breakdown tooltip
- [ ] `[Approve]` `[Edit & Approve]` `[Reject & Regenerate]` actions all wired to API

#### TYR: OpenAPI Assembly
- [ ] `OpenAPIAssembler` class produces valid OpenAPI 3.1.0 from approved endpoints
- [ ] `openapi-spec-validator` runs on every assembled spec — raises `ValidationError` if invalid
- [ ] Shared schemas extracted into `/components/schemas` (no duplication)
- [ ] Every endpoint has `operationId` (prevents Redoc warnings)
- [ ] `GET /api/repos/{id}/docs` returns assembled OpenAPI JSON
- [ ] `GET /api/repos/{id}/export?format=markdown` returns readable markdown summary

### Sprint 4 (Week 6) — Quality Hardening

#### TYR: Prompt Tuning
- [ ] Pipeline run on 20 diverse real-world endpoints (mix of CRUD, complex, auth-protected)
- [ ] Per-endpoint: tokens used, quality score, attempts, latency recorded in LangSmith
- [ ] Endpoints scoring < 6.5 identified and root-caused to a specific pipeline step
- [ ] Prompts updated, re-run, delta measured
- [ ] Final benchmark: ≥ 80% of 20 endpoints approve on first attempt
- [ ] Final benchmark: mean quality score ≥ 7.0

#### HEIMDALL: Security Review
- [ ] OWASP API Security Top 10 checklist completed for all endpoints
- [ ] Every protected endpoint returns 401 without valid JWT (automated test)
- [ ] Input validation tested: malformed repo URLs, path traversal attempts
- [ ] Prompt injection test suite run on all 3 LangChain prompts
- [ ] Rate limiting verified: per-user limits on `/scan` and AI endpoints
- [ ] `Snyk` dependency scan clean (no critical CVEs)
- [ ] `Semgrep` SAST scan clean

#### Performance
- [ ] `/health` p95 < 10ms
- [ ] All non-AI endpoints p95 < 200ms (load test with Locust or k6)
- [ ] SSE first event arrives < 500ms after scan trigger

### 🔐 Phase Gate 1 → 2
- [ ] Mean doc quality score ≥ 7.0 on 20-endpoint benchmark
- [ ] ≥ 80% of endpoints approve on first LLM attempt
- [ ] Heimdall OWASP checklist signed off
- [ ] Prompt versions committed to `PROMPT_REGISTRY`
- [ ] All LangSmith traces visible and tagged correctly

---

## Phase 2 — Alpha Dogfood
**Duration:** Weeks 7–8 · **MRR:** $0 · **New agents:** `FRIGG`

### GitHub App Integration (TYR)
- [ ] GitHub App created in GitHub Developer Settings
- [ ] App private key stored securely (Azure Key Vault)
- [ ] `POST /webhooks/github` endpoint verifies HMAC-SHA256 signature
- [ ] `pull_request.opened` event received and parsed correctly
- [ ] `pull_request.closed` (merged) event received and parsed correctly
- [ ] Changed files extracted from PR diff → only modified route files re-scanned
- [ ] Incremental scan runs only on changed endpoints (not full repo re-scan)
- [ ] PR comment posted with: new endpoints documented + changed endpoints with diff
- [ ] PR comment format: clear section for NEW / CHANGED / REMOVED endpoints
- [ ] `github_pr_comments` table prevents duplicate comments on re-push

### Dogfood Execution
- [ ] GitHub App installed on `docforge/docforge-backend` repo
- [ ] Full repo scan triggered — all endpoints extracted
- [ ] Every endpoint reviewed by `TYR` (approved / edited / rejected)
- [ ] Generated OpenAPI spec runs through `openapi-spec-validator` — zero errors
- [ ] Docs exported as Markdown and published to `docs.docforge.io`
- [ ] At least one real PR opened against DocForge repo — webhook received, comment posted

### Bug Triage (BRAGI + FRIGG)
- [ ] All team members file issues tagged `[BUG]`, `[UX]`, `[MISSING]`, `[SLOW]`
- [ ] `BRAGI` categorises all findings: P1 (must fix) / P2 (backlog) / Won't fix
- [ ] `FRIGG` documents every UX failure: what user tried → what happened → proposed fix
- [ ] `FRIGG` produces `user_journey_map.md` for the full scan → review → export flow
- [ ] `BRAGI` produces `PRD_v2.md` incorporating all dogfood findings
- [ ] ≥ 8 of identified P1 bugs resolved and verified fixed

### 🔐 Phase Gate 2 → 3
- [ ] ≥ 8 P1 bugs resolved
- [ ] DocForge's own docs live at `docs.docforge.io`
- [ ] GitHub App PR comment working on a real PR
- [ ] PRD v2 written and reviewed by `ODIN`
- [ ] Zero known P1 bugs remaining

---

## Phase 3 — Private Beta
**Duration:** Weeks 9–12 · **MRR target:** $500 · **New agents:** `LOKI` `HERMOD` `SIGYN` `EIR` `SYN` `NORNS`

### Stripe Billing (TYR)
- [ ] Four plans configured in Stripe Dashboard: Free / Indie ($9) / Team ($49) / Company ($149)
- [ ] `POST /api/billing/checkout` creates Stripe Checkout Session → redirect to Stripe
- [ ] `POST /webhooks/stripe` handles: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
- [ ] Webhook signature verified with `stripe.construct_event()`
- [ ] `POST /api/billing/portal` opens Stripe Customer Portal for plan management
- [ ] Plan limits enforced in middleware: repo limit, endpoint limit per plan tier
- [ ] Dunning email sent via Resend on `invoice.payment_failed`

### CLI v1 (TYR)
- [ ] `cli/` package created with `typer` + `rich`
- [ ] `docforge generate --input ./app --output ./docs` runs end-to-end
- [ ] Auto-detects framework from `requirements.txt` / `package.json`
- [ ] `docforge generate --no-ai` produces skeleton OpenAPI spec without LLM calls
- [ ] `docforge auth login` opens browser → saves API key to `~/.docforge/config.json`
- [ ] `docforge status` shows config, connected repos, monthly usage
- [ ] `pyproject.toml` correctly configured for PyPI publication
- [ ] Package name `docforge` reserved on PyPI (do this in Week 8, not Week 9)
- [ ] `pip install docforge` works from PyPI
- [ ] GitHub repo README: animated GIF demo, 4-line quickstart, framework support table

### Express.js Parser (TYR)
- [ ] Detects `app.get/post/put/patch/delete` and `router.*` patterns
- [ ] Handles middleware chains: `router.get('/path', auth, handler)`
- [ ] Extracts JSDoc `@route`, `@param`, `@returns` comments if present
- [ ] TypeScript: extracts `Request<Params, ResBody, ReqBody>` type generics
- [ ] Resolves `router.use('/prefix', subRouter)` prefix chaining for full paths
- [ ] Test suite: 3 real Express repos — extraction accuracy ≥ 90%

### Beta User Sourcing (HERMOD + LOKI)
- [ ] ICP defined by `LOKI`: role, company size, tech stack, pain signal
- [ ] 100 candidates sourced across: GitHub (repos missing openapi.json), LinkedIn, Reddit/Discord
- [ ] Each candidate enriched: company, title, tech stack, email, LinkedIn URL
- [ ] Each candidate ICP-scored 1–5 on fit and intent
- [ ] 50 invites sent — personalised email referencing their specific repo or community post
- [ ] Target: 50 beta acceptances

### CRM + Lifecycle (SIGYN)
- [ ] HubSpot workspace created, all 50 beta users imported
- [ ] Lifecycle stages configured: Lead → MQL → SQL → Active → Customer → At-risk → Churned
- [ ] PostHog → HubSpot webhook: `repo_scan_completed` event moves contact to "Active"
- [ ] Stripe events sync to HubSpot: subscription created/cancelled updates deal stage
- [ ] "At-risk" automation: no login 10 days AND paying → auto-email from EIR

### Onboarding (SYN)
- [ ] 5-touch email sequence written and configured in Resend
- [ ] Email 1 (T+0): immediate, personal, single CTA "Connect your first repo"
- [ ] Email 2 (T+1h): only if no repo connected — "Is it a setup issue?"
- [ ] Email 3 (T+24h): only if repo connected, no scan — "Run your first scan"
- [ ] Email 4 (T+3d): only if scan done, no export — "Your docs are ready to share"
- [ ] Email 5 (T+7d): all users — open feedback question ("reply to this email")
- [ ] All email triggers based on PostHog events (not time-only)
- [ ] Open rate target: > 40%

### Customer Success (EIR)
- [ ] Intercom workspace configured
- [ ] First 5 knowledge base articles written and published
- [ ] P1 escalation path: Intercom → Slack `#p1-alerts` → `TYR`/`THOR`
- [ ] Support SLAs documented and enforced: P1 < 1hr, P2 < 4hr, P3 < 24hr
- [ ] NPS survey (Delighted) sent at day 7 post-signup
- [ ] Promoters (9–10): `EIR` sends personal thank-you + case study ask
- [ ] Detractors (0–6): `EIR` schedules 15-min call within 24 hours

### Predictive Analytics (NORNS)
- [ ] First churn model built (logistic regression on beta user data)
- [ ] Features: `days_since_last_login`, `scans_last_7d`, `support_tickets`, `plan_tier`, `endpoints_approved_rate`
- [ ] Model deployed, scoring all active subscribers weekly
- [ ] Churn risk list (score > 0.7) delivered to `EIR` + `SIGYN` every Monday

### 🔐 Phase Gate 3 → 4
- [ ] $500 MRR confirmed in Stripe Dashboard
- [ ] NPS score ≥ 30 (minimum 20 responses)
- [ ] Activation rate ≥ 40% (scan completed within 10 min of signup)
- [ ] All three required. If any one fails, do not launch publicly.

---

## Phase 4 — Public Launch
**Duration:** Weeks 13–16 · **MRR target:** $2,000 · **New agents:** `BALDUR` `SAGA` `MIMIR` `IDUNN`

### Engineering
- [ ] Django / DRF parser: ViewSet + APIView + serializer extraction, test on 3 real repos
- [ ] Redoc component integrated in docs preview page with custom DocForge theme
- [ ] Endpoint list virtualised (TanStack Virtual) — handles 500+ endpoints without lag
- [ ] 3 demo repos pre-indexed and publicly browsable (no login required)
- [ ] Pricing page A/B test implemented (2 headline variants)
- [ ] Public landing page complete: Hero, Features, Pricing, Social proof, Demo embed
- [ ] Production environment on Azure AKS with HPA configured
- [ ] Load test run before launch: simulate 500 concurrent users, no errors

### Pre-Launch Content (SAGA)
- [ ] Dev.to / Hashnode article written: technical deep-dive on how DocForge works
- [ ] ProductHunt description, tagline, and first comment written
- [ ] Show HN post written (founder posts manually — not automated)
- [ ] Landing page copy final: headline, subheadline, 3 feature bullets, CTA, FAQ
- [ ] 3 demo repo "tours" written as short use-case descriptions on the landing page

### SEO Foundation (MIMIR)
- [ ] First keyword research report delivered: 20 target keywords with volume + difficulty
- [ ] Landing page meta title + description optimised for primary keyword
- [ ] `sitemap.xml` generated and submitted to Google Search Console
- [ ] JSON-LD structured data added (SoftwareApplication schema)
- [ ] Google Search Console verified, crawl errors checked

### Pre-Launch Social (IDUNN)
- [ ] 14-day teaser campaign scheduled in Buffer (daily posts, escalating reveal)
- [ ] "We're live on PH" launch day tweet pre-written and scheduled
- [ ] Reddit posts pre-written for: `r/webdev`, `r/Python`, `r/node` (genuine, not spam)
- [ ] Personal email drafted by `LOKI` to every beta user asking for PH support on launch day

### Launch Day Execution (BALDUR coordinates)
- [ ] ProductHunt post live at 12:01 AM PST
- [ ] Dev.to article published at 06:00 AM PST
- [ ] Show HN post submitted at 08:00 AM PST
- [ ] LinkedIn post published at 12:00 PM PST
- [ ] Reddit posts live across 3 subreddits
- [ ] `EIR` on Intercom monitoring all day (30-min response target on launch day)
- [ ] `KVASIR` launch dashboard live with real-time signup and conversion tracking
- [ ] `LOKI` personally DMs every PH commenter who says they'll try it

### 🔐 Phase Gate 4 → 5
- [ ] $2,000 MRR confirmed in Stripe
- [ ] All 19 agents fully operational
- [ ] Attribution data available: know which channel drove most conversions

---

## Phase 5 — Growth Engine
**Duration:** Months 5–6 · **MRR target:** $5,000

### Engineering
- [ ] Flask parser: `@app.route`, Blueprint, Flask-RESTful `Resource` patterns
- [ ] NestJS parser: `@Controller`, `@Get`/`@Post`, DTO class extraction
- [ ] Mintlify MDX export: `docforge export --format mintlify` produces valid `.mdx` files
- [ ] Shared dashboard feature: public link to read-only docs (drives Team plan upgrades)
- [ ] Redis caching for identical LLM prompts (same code → same doc, cache hit)
- [ ] Token budget enforcement per plan tier (Indie: 100K tokens/mo, Team: 500K)

### Content SEO (SAGA + MIMIR)
- [ ] 1 technical article published per week, every week in Months 5–6
- [ ] Pillar pages written for: FastAPI docs, Express docs, Django REST docs
- [ ] Each article written against a `MIMIR` keyword brief (primary KW + 5 LSI terms)
- [ ] Internal linking implemented across all published articles
- [ ] ≥ 5 target keywords ranking in Google top 10 by end of Month 6

### Open-Source Growth (IDUNN + CLI)
- [ ] CLI added to `awesome-fastapi`, `awesome-express`, `awesome-django` lists
- [ ] Technical deep-dive blog post: "How we built the DocForge CLI with tree-sitter" → HN submission
- [ ] Weekly "CLI tip" Twitter thread running every Monday
- [ ] CLI README updated: animated GIF, framework matrix, contributing guide
- [ ] CLI at 500+ GitHub stars by end of Month 6

### Outbound Machine (HERMOD + SIGYN)
- [ ] HERMOD delivering ≥ 50 qualified leads per week
- [ ] GitHub signal automated: daily search for FastAPI/Express repos missing `openapi.json`
- [ ] HubSpot full lifecycle automation active: every stage transition has an automated action
- [ ] SIGYN expansion detection: users at 80% of plan limit get proactive upgrade email
- [ ] Revenue attribution: every paid conversion mapped to source channel in HubSpot

### Retention (NORNS + EIR)
- [ ] NORNS churn model accuracy ≥ 65% (F1 score on holdout set)
- [ ] Weekly churn risk list → `EIR` intervention within 24 hours
- [ ] Monthly churn rate confirmed < 5%
- [ ] First user case study published by `SAGA` with real before/after metrics

### Partnerships (LOKI)
- [ ] Mintlify partnership conversation initiated (warm intro or cold outreach)
- [ ] DocForge listed in Mintlify's integrations directory (or discussion underway)
- [ ] GitHub Marketplace app submission started

### 🔐 Phase Gate 5 → 6
- [ ] $5,000 MRR confirmed
- [ ] Monthly churn < 5%
- [ ] Gross margin ≥ 80%
- [ ] All three required. Churn > 5% means fix retention before scaling.

---

## Phase 6 — Scale
**Duration:** Months 7–12 · **MRR target:** $20,000

### Data Moat (TYR + KVASIR)
- [ ] Approved/edited/rejected doc pairs logged in structured dataset format
- [ ] Dataset reaches 5,000 examples by Month 7
- [ ] Dataset reaches 15,000 examples by Month 9
- [ ] Dataset reaches 40,000 examples by Month 12
- [ ] Fine-tuned model v1 trained on proprietary dataset (Month 9)
- [ ] Fine-tuned model benchmark: first-attempt approve rate ≥ 91%
- [ ] Fine-tuned model deployed behind feature flag; A/B tested vs base model

### GitHub App v2 (TYR)
- [ ] On PR merge: DocForge automatically opens a PR to `docs` branch with updated docs
- [ ] Auto-PR title: `"DocForge: Update docs for PR #N (X endpoints changed)"`
- [ ] Reviewer assignment configurable per repo in DocForge settings
- [ ] GitHub Marketplace listing submitted and approved

### Additional Parsers (TYR)
- [ ] Hono (TypeScript) parser: `app.get/post`, typed handlers
- [ ] Rails parser: `routes.rb` + controller action extraction (Month 8)

### Enterprise Features (THOR + TYR + HEIMDALL)
- [ ] SSO: SAML/OIDC integration (Okta + Azure AD + Google Workspace)
- [ ] Just-in-time user provisioning on SSO login
- [ ] Role-based access control: Admin / Editor / Viewer
- [ ] Audit log: every approval/rejection/edit logged with user, timestamp, IP
- [ ] Audit log exportable as CSV; 90-day retention
- [ ] Enterprise tier ($499/mo) live in Stripe with 3+ paying customers
- [ ] Private LLM Mode scoped and costed (no deployment required, just scoped)

### SOC 2 (HEIMDALL)
- [ ] Audit firm engaged (Month 9)
- [ ] Security controls implemented: access management, encryption at rest, logging
- [ ] Evidence collection complete (Month 11)
- [ ] SOC 2 Type I report received (Month 12)

### Partnerships (LOKI)
- [ ] Mintlify partnership agreement signed
- [ ] Joint blog post / webinar co-marketed
- [ ] Referral arrangement active: Mintlify users get 20% off DocForge

### Predictive Intelligence (NORNS)
- [ ] Churn model F1 ≥ 0.80 (Month 8)
- [ ] Expansion prediction model: identifies users at 80% plan limit 2 weeks before they hit it
- [ ] EIR proactive upgrade campaign driven by expansion model → 15% expansion MRR
- [ ] MRR forecast accuracy ± 8% on 4-week horizon

### Monthly MRR Milestones
- [ ] Month 7: $7,500 MRR
- [ ] Month 8: $10,500 MRR
- [ ] Month 9: $13,500 MRR
- [ ] Month 10: $16,000 MRR
- [ ] Month 11: $18,000 MRR
- [ ] Month 12: $20,000 MRR
- [ ] Month 12: Net Revenue Retention > 110%
- [ ] Month 12: LTV:CAC ratio > 10x

---

## Non-Negotiable Principles

1. **Never skip a phase gate.** The gate exists because the next phase will fail without it.
2. **Quality before quantity.** A mean doc score < 6.5 means Phase 1 is not done.
3. **Activation before acquisition.** If < 30% of users complete their first scan, do not run paid acquisition.
4. **Measure everything from day one.** If it isn't in PostHog, it didn't happen.
5. **Churn is a product problem, not a sales problem.** Fix retention before scaling acquisition.
6. **The data moat is the strategy.** Every approved doc pair is a competitive asset. Collect from day one.
7. **Heimdall gates every deploy.** No exceptions, no "we'll fix security later."
