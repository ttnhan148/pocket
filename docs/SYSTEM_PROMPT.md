# SYSTEM_PROMPT.md — The Pocket Constitution

> **Version:** 1.0.0
> **Last Updated:** 2026-07-03
> **Status:** AUTHORITATIVE — Single Source of Truth
> **Authority Level:** Constitutional — All development decisions must comply with this document.
> **Audience:** Claude Code, AI coding agents, human developers

---

## Preamble

This document is the **Software Constitution** of Pocket. It defines the complete product vision, engineering principles, software architecture, AI architecture, database design, UI design system, coding standards, development workflow, and acceptance criteria for the Pocket project.

**Every line of code written for Pocket must be traceable to a requirement in this document.**

Claude Code must:
- Read this document before writing any code
- Treat every section as a binding constraint
- Never contradict any principle stated here
- Never add functionality not described or implied here
- Refer to companion documents (ARCHITECTURE.md, DATABASE.md, AI_ARCHITECTURE.md, UI_GUIDELINES.md, IMPLEMENTATION_PLAN.md) for detailed specifications

If a decision is ambiguous, the answer is found in this document. If this document is silent, default to simplicity.

---

## PART I — PRODUCT DEFINITION

---

### 1. Mission Statement

Pocket is a **Personal Context Engineering Platform**.

Pocket exists to solve one problem:

> **Help a single power user create the best possible prompt with the least possible effort.**

Pocket is NOT:
- A prompt library (it does not just store prompts)
- A prompt manager (it does not just organize prompts)
- A chatbot wrapper (it does not just forward messages to AI)
- A note-taking app (it does not replace Obsidian or Notion)
- A SaaS product (it is not multi-tenant)
- A marketplace (it does not sell prompts)

Pocket IS:
- A knowledge management system for AI interactions
- A context engineering platform that treats context as first-class knowledge objects
- An intelligent prompt builder that understands context relationships
- A learning system that improves with every interaction
- A personal tool optimized for a single user on a local machine

### 2. Product Vision

The user interacts with multiple AI models daily. Each interaction requires context: who they are, what project they're working on, what coding standards to follow, what architecture decisions have been made, what constraints exist.

Today, this context lives in:
- Scattered markdown files
- Browser bookmarks
- Copy-paste buffers
- Memory

Pocket centralizes all of this into a structured, searchable, intelligent knowledge graph. When the user wants to chat with AI, Pocket:

1. Understands the user's intent
2. Retrieves the most relevant context
3. Resolves dependencies between contexts
4. Compiles everything into an optimized prompt
5. Validates the prompt for completeness
6. Sends it to Azure OpenAI
7. Learns from the response to improve future interactions

### 3. Design Philosophy

Every feature must answer this question:

> **Does this help create a better prompt?**

If the answer is **No** → remove it.

Additional principles:
- **No feature just because it's pretty.** Every UI element must serve the mission.
- **No framework just because it's popular.** Every dependency must be justified.
- **No over-engineering.** Build what's needed now, not what might be needed later.
- **Simplicity is a feature.** The simplest correct solution is the best solution.
- **Explicit over implicit.** No magic. All behavior traceable through code.

### 4. Target User

There is exactly **one user**: the owner/developer.

This means:
- **No multi-tenant architecture.** No tenant isolation, no shared resources.
- **No authentication.** No login, no sessions, no JWT, no OAuth.
- **No RBAC.** No roles, no permissions, no access control.
- **No billing.** No subscription, no payment, no usage limits (beyond API costs).
- **No user management.** No user table, no profile, no preferences per user.

Everything is optimized for a single user running the application locally.

### 5. Deployment Target

| Environment | Support Level |
|------------|--------------|
| **Ubuntu Server** | Primary target |
| **Linux Desktop** | Primary target |
| **WSL (Windows Subsystem for Linux)** | Primary target |
| **macOS** | Should work (not actively tested) |
| **Docker** | Optional, not required |
| **Windows native** | Not supported |
| **Cloud hosting** | Not designed for |

The application runs as two local processes:
1. **Backend:** Python/FastAPI on port 8000
2. **Frontend:** Node.js/Next.js on port 3000

Database: SQLite file at `~/.pocket/pocket.db`

---

## PART II — TECHNOLOGY STACK

---

### 6. Backend Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Backend language |
| **FastAPI** | Latest | Web framework |
| **SQLAlchemy** | 2.0+ | ORM and database toolkit |
| **Alembic** | Latest | Database migrations |
| **SQLite** | 3.35+ | Primary database (WAL mode, FTS5) |
| **Pydantic** | v2 | Data validation and serialization |
| **Azure OpenAI SDK** | Latest | Azure OpenAI API client |
| **sentence-transformers** | Latest | Local embedding generation |
| **tiktoken** | Latest | Token counting |
| **RapidFuzz** | Latest | Fuzzy string matching |
| **Jinja2** | Latest | Template rendering |
| **Markdown-it** | Latest | Markdown processing |
| **PyYAML** | Latest | YAML parsing (import/export) |
| **python-dotenv** | Latest | Environment variable loading |
| **uvicorn** | Latest | ASGI server |
| **pytest** | Latest | Testing framework |
| **tenacity** | Latest | Retry logic |
| **httpx** | Latest | Async HTTP client (for testing) |

**Forbidden Backend Technologies:**
- Django (too heavyweight)
- Flask (FastAPI is superior for typed APIs)
- PostgreSQL, MySQL, MongoDB (SQLite only)
- Redis (not needed for single user)
- Celery (FastAPI BackgroundTasks sufficient)
- GraphQL (REST is simpler and sufficient)

### 7. Frontend Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Next.js** | 14+ | React framework with App Router |
| **React** | 18+ | UI library |
| **TypeScript** | 5+ (strict) | Type safety |
| **Tailwind CSS** | 3+ | Utility-first CSS with CSS variables for theming |
| **shadcn/ui** | Latest | Component primitives (Radix-based) |
| **Radix UI** | Latest | Accessible unstyled primitives |
| **Lucide React** | Latest | Icon library |
| **@monaco-editor/react** | Latest | Code/markdown editor |
| **@xyflow/react** (ReactFlow) | Latest | Context graph visualization |
| **TanStack Query** | v5 | Server state management |
| **React Hook Form** | Latest | Form management |
| **Zod** | Latest | Schema validation |
| **Framer Motion** | Latest | Animations |
| **react-markdown** | Latest | Markdown rendering |
| **remark-gfm** | Latest | GitHub Flavored Markdown |
| **rehype-highlight** | Latest | Syntax highlighting |
| **@tanstack/react-virtual** | Latest | Virtual scrolling |

**Forbidden Frontend Technologies:**
- Redux, Zustand, MobX (TanStack Query + useState sufficient)
- Material UI, Ant Design, Chakra UI (shadcn/ui only)
- CSS Modules (Tailwind only)
- styled-components, emotion (Tailwind only)
- jQuery (React only)
- Bootstrap (Tailwind only)
- Any pre-built admin template

### 8. AI Stack

| Technology | Purpose |
|-----------|---------|
| **Azure OpenAI** | LLM provider (NOT OpenAI public endpoint) |
| **GPT-4.1** | Primary chat model (complex tasks) |
| **GPT-4.1 Mini** | Secondary chat model (simple tasks, classification) |
| **text-embedding-3-large** | Azure embedding model |
| **all-MiniLM-L6-v2** | Local embedding model (sentence-transformers) |
| **SQLite FTS5** | Full-text search with BM25 |
| **RapidFuzz** | Fuzzy string matching |
| **tiktoken** | Token counting |

**Forbidden AI Technologies:**
- OpenAI public API (Azure only)
- LangChain, LlamaIndex (too abstract, build from scratch)
- Pinecone, Weaviate, ChromaDB (SQLite is the vector store)
- Hugging Face Inference API (local sentence-transformers only)

---

## PART III — ARCHITECTURE

---

### 9. Architecture Style

Pocket follows **Clean Architecture** with **lightweight Domain-Driven Design**.

#### 9.1 Layer Architecture

```
┌─────────────────────────────────┐
│    Presentation Layer           │  FastAPI Routers, Pydantic Schemas
├─────────────────────────────────┤
│    Application Layer            │  Services, Use Cases, DTOs
├─────────────────────────────────┤
│    Domain Layer                 │  Entities, Value Objects, Interfaces
├─────────────────────────────────┤
│    Infrastructure Layer         │  Repositories, AI Clients, Search
└─────────────────────────────────┘
```

**Dependency Rule:** Dependencies point inward. The Domain Layer has zero external dependencies.

| Layer | Can Import | Cannot Import |
|-------|-----------|--------------|
| Presentation | Application, Domain | Infrastructure |
| Application | Domain | Presentation, Infrastructure |
| Domain | Nothing | Everything |
| Infrastructure | Domain | Presentation, Application |

#### 9.2 Key Patterns

| Pattern | Usage |
|---------|-------|
| **Repository Pattern** | All data access behind repository interfaces |
| **Service Layer** | All business logic in services, not routers |
| **Dependency Injection** | FastAPI `Depends()` for all dependencies |
| **Feature-First** | Code organized by feature (contexts, templates, etc.), not layer |
| **Event-Driven** | Domain events for cross-module communication |

#### 9.3 Forbidden Patterns

| Anti-Pattern | Why Forbidden |
|-------------|--------------|
| Business logic in routers | Routers handle HTTP only |
| Raw SQL in services | Services use repositories |
| Direct AI calls outside AI layer | AI layer is isolated |
| Global mutable state | Use DI instead |
| God classes (>300 lines) | Split into focused modules |
| Circular imports | Restructure dependencies |
| `Any` type in TypeScript | Use proper types |
| `# type: ignore` in Python | Fix the type error |
| `TODO` comments in release code | Resolve before merge |

### 10. Project Structure

#### 10.1 Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app factory
│   ├── config.py                    # Pydantic BaseSettings
│   ├── dependencies.py              # DI container
│   ├── core/                        # Cross-cutting concerns
│   │   ├── database.py              # Engine, session, PRAGMA
│   │   ├── exceptions.py            # Exception hierarchy
│   │   ├── middleware.py            # CORS, error handler, timing
│   │   ├── security.py              # Validation, rate limiting
│   │   └── events.py                # Domain event dispatcher
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── base.py                  # Base model (id, timestamps, soft delete)
│   │   ├── workspace.py
│   │   ├── context.py
│   │   ├── template.py
│   │   ├── variable.py
│   │   ├── conversation.py
│   │   ├── prompt.py
│   │   ├── provider.py
│   │   ├── analytics.py
│   │   ├── ai_job.py
│   │   ├── learning.py
│   │   ├── journal.py
│   │   └── settings.py
│   ├── features/                    # Feature-first modules
│   │   ├── contexts/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── dependencies.py
│   │   ├── workspaces/
│   │   ├── templates/
│   │   ├── variables/
│   │   ├── conversations/
│   │   ├── prompts/
│   │   ├── search/
│   │   ├── analytics/
│   │   ├── favorites/
│   │   ├── journals/
│   │   ├── settings/
│   │   └── providers/
│   └── ai/                          # AI Layer (isolated)
│       ├── client.py                # Azure OpenAI wrapper
│       ├── embeddings.py            # Embedding service
│       ├── pipeline/                # 18-step pipeline
│       │   ├── orchestrator.py
│       │   ├── intent.py
│       │   ├── retrieval.py
│       │   ├── ranking.py
│       │   ├── compiler.py
│       │   ├── validator.py
│       │   ├── optimizer.py
│       │   ├── enhancer.py
│       │   ├── critic.py
│       │   ├── scorer.py
│       │   └── token_counter.py
│       ├── features/                # AI feature services
│       └── learning/                # Learning engine
├── alembic/
├── tests/
├── pyproject.toml
└── requirements.txt
```

#### 10.2 Frontend Structure

```
frontend/
├── src/
│   ├── app/                         # Next.js App Router
│   │   ├── layout.tsx               # Root layout
│   │   ├── page.tsx                 # Dashboard redirect
│   │   ├── globals.css              # Global styles + CSS variables
│   │   └── (dashboard)/             # Dashboard route group
│   │       ├── layout.tsx           # App shell (sidebar + header + content)
│   │       ├── page.tsx             # Dashboard
│   │       ├── contexts/
│   │       ├── templates/
│   │       ├── variables/
│   │       ├── conversations/
│   │       ├── builder/
│   │       ├── graph/
│   │       ├── analytics/
│   │       ├── journals/
│   │       └── settings/
│   ├── components/
│   │   ├── ui/                      # shadcn/ui components
│   │   ├── layout/                  # Sidebar, Header, CommandPalette
│   │   ├── editor/                  # Monaco, Markdown preview
│   │   ├── context/                 # Context-specific components
│   │   ├── prompt/                  # Prompt builder components
│   │   ├── graph/                   # ReactFlow graph
│   │   ├── chat/                    # Chat components
│   │   └── shared/                  # Empty state, loading, error boundary
│   ├── hooks/                       # Custom hooks (use-contexts, use-keyboard, etc.)
│   ├── lib/                         # Utilities (api client, constants, format)
│   ├── types/                       # TypeScript types
│   └── styles/                      # Additional CSS
├── public/
│   └── fonts/                       # Self-hosted fonts
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── tests/
```

### 11. Core Domain Model

#### 11.1 Context as Knowledge Object

**A Context is NOT plain text. A Context is a Knowledge Object.**

Every Context has:

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `workspace_id` | UUID | Parent workspace |
| `title` | string | Human-readable title |
| `slug` | string | URL-safe identifier |
| `content` | string | The actual content (markdown) |
| `content_type` | enum | markdown, yaml, json, text |
| `context_type` | enum | persona, role, instruction, knowledge, constraint, example, reference, snippet |
| `priority` | 0-100 | Importance weight |
| `confidence` | 0.0-1.0 | AI-adjusted confidence |
| `quality_score` | 0.0-1.0 | AI-evaluated quality |
| `token_count` | integer | Token count of content |
| `usage_count` | integer | How many times used |
| `last_used_at` | datetime | Last usage timestamp |
| `current_version` | integer | Version counter |
| `metadata` | JSON | Extensible metadata |
| `tags` | list | Associated tags |
| `dependencies` | list | DAG edges to other contexts |
| `embedding` | vector | Semantic embedding |

#### 11.2 Context Types

| Type | Purpose | Example |
|------|---------|---------|
| `persona` | AI personality | "You are a senior Python developer with 15 years of experience..." |
| `role` | Task-specific role | "Act as a code reviewer focusing on security..." |
| `instruction` | Behavioral directives | "Always use type hints. Never use bare except." |
| `knowledge` | Domain knowledge | "Our architecture follows Clean Architecture with these layers..." |
| `constraint` | Output constraints | "Response must be under 500 words. Use markdown formatting." |
| `example` | Few-shot examples | "Input: X → Output: Y" |
| `reference` | External references | "Refer to PEP 8 for style guidelines." |
| `snippet` | Reusable fragments | "Standard error handling pattern: try/except/log" |

#### 11.3 Context Graph (DAG)

Contexts form a **Directed Acyclic Graph** (DAG). Dependencies between contexts define compilation order.

Dependency types:

| Type | Meaning | Compilation Behavior |
|------|---------|---------------------|
| `requires` | A cannot be used without B | B must be included before A |
| `extends` | A adds to B's content | B appears first, A follows |
| `overrides` | A replaces parts of B | A takes priority, B sections overridden |
| `complements` | A and B work well together | Both included, no specific order |

**Compilation uses topological sort (Kahn's algorithm).** Circular dependencies are forbidden and detected at dependency creation time.

---

## PART IV — DATABASE

---

### 12. Database Design

**See DATABASE.md for complete specification.** This section summarizes key principles.

#### 12.1 Data Store

- **SQLite** is the sole data store
- Database file: `~/.pocket/pocket.db`
- WAL mode enabled for concurrent reads
- Foreign keys enforced (`PRAGMA foreign_keys = ON`)
- All queries use parameterized statements (prepared statements)
- Zero string interpolation in SQL

#### 12.2 Schema Principles

| Principle | Rule |
|-----------|------|
| Normalization | 3NF minimum |
| Primary keys | UUIDv4 stored as TEXT(36) |
| Timestamps | `created_at`, `updated_at` (ISO 8601, UTC) |
| Soft delete | `deleted_at` timestamp |
| Versioning | Separate version tables for content entities |
| No ORM queries | SQLAlchemy Core for queries, ORM for model definitions |

#### 12.3 Total Tables: 32

Core: workspaces, contexts, templates, variables, conversations, messages, providers, settings
History: context_versions, template_versions, prompt_versions
Graph: context_dependencies
Taxonomy: tags, categories, context_tags
Junction: workspace_variables, template_variables, prompt_contexts
AI: context_embeddings, ai_jobs, ai_job_results, learning_records, context_candidates, context_health_scores
Analytics: analytics_events, context_usages, prompt_runs, prompt_scores
UI: favorites
System: audit_log, workspace_settings, journals

#### 12.4 Full-Text Search

FTS5 virtual tables for:
- `contexts_fts` (title, content, context_type)
- `templates_fts` (title, description, content)
- `messages_fts` (content)

Kept in sync via SQLite triggers (AFTER INSERT, UPDATE, DELETE).
BM25 ranking with title weighted 10x over content.

#### 12.5 Migrations

Alembic manages all schema changes:
- One migration per feature
- Always reversible (upgrade + downgrade)
- Data migrations separate from schema migrations
- Naming: `YYYY_MM_DD_HHMM_description.py`

---

## PART V — AI ARCHITECTURE

---

### 13. AI Pipeline

**See AI_ARCHITECTURE.md for complete specification.** This section defines the mandatory pipeline.

#### 13.1 The 18-Step Pipeline

Every user message goes through this pipeline. **No step may be skipped.**

```
Step  1: User Request (input)
Step  2: Intent Detection (GPT-4.1 Mini)
Step  3: Workspace Detection (rule-based or inferred)
Step  4: Variable Resolution (system → global → workspace → template → runtime)
Step  5: Hybrid Retrieval (FTS5 + RapidFuzz + Embedding, parallel)
Step  6: Dependency Resolution (topological sort, Kahn's algorithm)
Step  7: Conflict Detection (duplicate persona, contradictory instructions)
Step  8: Context Ranking (9-factor weighted scoring)
Step  9: Prompt Compilation (contexts + template + variables → prompt)
Step 10: Prompt Validation (11 checks, blocks on error)
Step 11: Token Optimization (if >80% of limit)
Step 12: AI Enhancement (GPT-4.1, optional but recommended)
Step 13: AI Critique (GPT-4.1, optional but recommended)
Step 14: Prompt Score (GPT-4.1 Mini, 5-dimension scoring)
Step 15: Final Prompt (assembled)
Step 16: Azure OpenAI Chat (send to model)
Step 17: Conversation Storage (store messages, prompt run, metadata)
Step 18: Learning Engine (post-conversation analysis, background)
```

#### 13.2 Critical vs. Non-Critical Steps

| Step | Critical | Fallback |
|------|----------|---------|
| Intent Detection | No | Default to "instruction" |
| Workspace Detection | No | Use current workspace |
| Variable Resolution | Yes | Must resolve all variables |
| Hybrid Retrieval | No | Use manually selected contexts |
| Dependency Resolution | Yes | Cannot compile incorrectly |
| Conflict Detection | No | Warn but continue |
| Context Ranking | No | Sort by priority |
| Prompt Compilation | Yes | Core functionality |
| Validation | Yes | Must not send invalid prompts |
| Token Optimization | No | Use unoptimized prompt |
| AI Enhancement | No | Skip enhancement |
| AI Critique | No | Skip critique |
| Prompt Scoring | No | No score |

If a **critical step** fails → pipeline stops, return error to user.
If a **non-critical step** fails → use fallback, continue pipeline.

#### 13.3 Model Routing

| Task | Model |
|------|-------|
| Chat completion | GPT-4.1 |
| Enhancement, Critique, Generation | GPT-4.1 |
| Intent, Scoring, Tagging, Classification | GPT-4.1 Mini |
| Azure embedding | text-embedding-3-large |
| Local embedding | all-MiniLM-L6-v2 |

### 14. Retrieval Engine

Pocket does NOT use vector search alone. It uses **Hybrid Search**:

```
Query → Query Rewrite → [FTS5 (BM25) || RapidFuzz || Embedding (Cosine)] → Merge → Rank → Top K
```

Search methods execute in **parallel** (asyncio.gather).

Scoring weights:
- FTS5 (BM25): 25%
- RapidFuzz (fuzzy): 10%
- Embedding (semantic): 35%
- Metadata (priority, usage, recency): 30%

### 15. Context Ranking

9-factor scoring formula:

| Factor | Weight | Computation |
|--------|--------|------------|
| Semantic similarity | 0.25 | From retrieval score |
| Priority | 0.15 | User-defined (0-100 → 0-1) |
| Usage frequency | 0.10 | log(count+1)/log(100), capped at 1.0 |
| Recency | 0.10 | exp(-0.05 × days_since_use), ~14 day half-life |
| Workspace match | 0.05 | 1.0 if same workspace, 0.3 otherwise |
| Favorite | 0.05 | 1.0 if favorited, 0.0 otherwise |
| Dependency weight | 0.10 | From dependency edge weights |
| Confidence | 0.10 | AI-adjusted (0-1) |
| Quality score | 0.10 | AI-evaluated (0-1) |

### 16. Validation Engine

Acts as a **compiler** for prompts. 11 validation checks:

| # | Check | Severity | When it Fails |
|---|-------|----------|--------------|
| 1 | Duplicate contexts | warning | >90% content similarity |
| 2 | Conflicting instructions | error | Contradictory directives |
| 3 | Circular dependencies | error | Cycles in DAG |
| 4 | Missing role | warning | No persona or role |
| 5 | Missing output format | warning | No output specification |
| 6 | Missing constraints | info | Suggest adding constraints |
| 7 | Missing variables | error | Unresolved `{{ var }}` |
| 8 | Broken references | error | Referenced ID doesn't exist |
| 9 | Token overflow | error | Exceeds model limit |
| 10 | Unused contexts | warning | Included but not referenced |
| 11 | Prompt quality | warning | AI score below 0.5 |

**If any error-severity check fails → prompt is NOT sent to AI.**

### 17. Prompt Optimization

12-step optimization pipeline (9 rule-based + 3 LLM-based):

1. Normalize whitespace
2. Deduplicate content
3. Merge related sections
4. Compress verbose content
5. Order constraints (MUST > SHOULD > MAY)
6. Order reasoning steps
7. Optimize schema
8. Optimize examples
9. Polish markdown
10. LLM Review (optional)
11. LLM Rewrite (optional)
12. Final optimized prompt

### 18. AI Features

14 AI-powered features:

| Feature | Model | Description |
|---------|-------|-------------|
| AI Enhance | GPT-4.1 | Improve prompt clarity and specificity |
| AI Critique | GPT-4.1 | Identify issues and suggest fixes |
| AI Auto Tagging | GPT-4.1 Mini | Suggest tags for a context |
| AI Variable Extraction | GPT-4.1 Mini | Find hardcoded values to parameterize |
| AI Duplicate Detection | GPT-4.1 Mini | Find near-duplicate contexts |
| AI Merge Context | GPT-4.1 | Merge similar contexts |
| AI Generate Context | GPT-4.1 | Generate context from description |
| AI Context Suggestion | GPT-4.1 Mini | Suggest relevant contexts |
| AI Prompt Benchmark | GPT-4.1 | Compare prompt variants |
| AI Weekly Review | GPT-4.1 | Weekly usage analysis |
| AI Context Health | GPT-4.1 Mini | Evaluate context freshness and quality |
| AI Learning | GPT-4.1 Mini | Post-conversation analysis |
| AI Prompt Score | GPT-4.1 Mini | 5-dimension quality scoring |
| AI Context Quality | GPT-4.1 Mini | Evaluate individual context quality |

**All AI suggestions are CANDIDATES. Never auto-applied. User always confirms.**

### 19. Learning Engine

After every conversation, the Learning Engine:

1. Analyzes the conversation quality
2. Identifies missing contexts
3. Identifies success/failure factors
4. Generates new context candidates (pending user review)
5. Updates usage scores for used contexts
6. Adjusts confidence scores based on effectiveness

The system must **self-improve** over time.

### 20. Embedding Engine

Dual strategy:
- **Local (default):** sentence-transformers (all-MiniLM-L6-v2), 384 dimensions, fast
- **Azure (optional):** text-embedding-3-large, 3072 dimensions, highest quality

Content-hash deduplication: if content hasn't changed, skip re-embedding.
Background jobs for batch embedding on context creation/update.

---

## PART VI — API DESIGN

---

### 21. API Conventions

| Convention | Rule |
|-----------|------|
| Base URL | `/api/v1` |
| Resource naming | Plural nouns (e.g., `/contexts`, `/templates`) |
| HTTP methods | GET (read), POST (create), PATCH (partial update), DELETE (soft delete) |
| Status codes | 200, 201, 204, 400, 404, 409, 422, 500, 502 |
| Pagination | `?offset=0&limit=50` |
| Filtering | Query parameters (e.g., `?workspace_id=...&context_type=...`) |
| Sorting | `?sort_by=updated_at&sort_order=desc` |
| Search | `?search=query` |
| Versioning | URL path (`/api/v1/`) |
| Error format | `{"detail": "...", "error_code": "...", "errors": [...]}` |

### 22. API Endpoint Summary

**See ARCHITECTURE.md Section 9.2 for the complete endpoint catalog.** Core endpoints:

```
Workspaces:     GET/POST/PATCH/DELETE  /api/v1/workspaces
Contexts:       GET/POST/PATCH/DELETE  /api/v1/contexts (+ versions, dependencies, graph, embed, health)
Templates:      GET/POST/PATCH/DELETE  /api/v1/templates (+ versions, preview)
Variables:      GET/POST/PATCH/DELETE  /api/v1/variables (+ resolve)
Conversations:  GET/POST/DELETE        /api/v1/conversations (+ messages)
Prompts:        POST                   /api/v1/prompts/compile, validate, optimize, score
Search:         POST                   /api/v1/search (+ contexts, semantic, suggest)
AI Features:    POST                   /api/v1/ai/* (enhance, critique, auto-tag, etc.)
Analytics:      GET                    /api/v1/analytics/* (dashboard, usage, costs, trends)
Favorites:      GET/POST/PUT           /api/v1/workspaces/{workspace_id}/favorites (+ toggle, reorder)
Journals:       GET/POST/PATCH/DELETE  /api/v1/journals
Settings:       GET/PUT                /api/v1/settings
Providers:      GET/POST/PUT/DELETE    /api/v1/providers (+ test, default)
Import/Export:  POST/GET               /api/v1/import/*, /api/v1/export/*
```

---

## PART VII — UI DESIGN SYSTEM

---

### 23. Design Philosophy

**See UI_GUIDELINES.md for the complete design specification.**

#### 23.1 Design References

| Reference | Inspiration |
|-----------|------------|
| Linear | Layout, transitions, keyboard UX |
| Cursor | IDE split views, dark theme |
| Raycast | Command palette, instant search |
| Claude | Conversation UI, markdown rendering |
| Vercel Dashboard | Metrics, card layouts |
| Notion | Sidebar navigation, page hierarchy |
| Obsidian | Graph view, markdown-first |

#### 23.2 Core Principles

- **Developer-first:** Power user UX. Keyboard shortcuts for everything.
- **Minimal:** Every pixel justifies its existence.
- **Dark mode first:** Design in dark, adapt to light.
- **Keyboard-first:** All actions reachable via keyboard.
- **Pixel-perfect:** Consistent alignment, spacing, typography.
- **No admin templates.** No Material Design. No Bootstrap.

### 24. Color System

#### Dark Mode (Default)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#09090B` | Main background |
| `--bg-secondary` | `#18181B` | Panels, sidebars, cards |
| `--bg-tertiary` | `#27272A` | Elevated surfaces |
| `--text-primary` | `#FAFAFA` | Primary text |
| `--text-secondary` | `#A1A1AA` | Muted text |
| `--border-default` | `#27272A` | Borders |
| `--accent-primary` | `#3B82F6` | Blue-600, CTAs, links |

#### Light Mode

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#FFFFFF` | Main background |
| `--bg-secondary` | `#F8FAFC` | Panels |
| `--text-primary` | `#0F172A` | Primary text |
| `--text-secondary` | `#64748B` | Muted text |
| `--border-default` | `#E2E8F0` | Borders |

Context type colors: Persona (#8B5CF6), Role (#06B6D4), Instruction (#3B82F6), Knowledge (#22C55E), Constraint (#EAB308), Example (#F97316), Reference (#EC4899), Snippet (#6366F1).

### 25. Typography

| Element | Size | Weight | Font |
|---------|------|--------|------|
| H1 | 48px | 800 | Geist Sans |
| H2 | 36px | 700 | Geist Sans |
| H3 | 24px | 600 | Geist Sans |
| Body | 16px | 400 | Geist Sans |
| Small | 14px | 500 | Geist Sans |
| Code | 14px/13px | 400 | Geist Mono |

### 26. Layout

- **Sidebar:** 240px (collapsible to 48px)
- **Header:** 56px
- **Content max-width:** 1200px
- **Spacing grid:** 4px base
- **Border radius:** 8px (cards), 6px (buttons/inputs), 4px (badges)

### 27. Motion

| Duration | Usage | Easing |
|----------|-------|--------|
| 100ms | Hover, focus | ease-out |
| 200ms | Dropdown, tooltip | ease-in-out |
| 300ms | Modal, page transition | cubic-bezier(0.16, 1, 0.3, 1) |

Rules: Only animate `transform` and `opacity`. Respect `prefers-reduced-motion`. No bounce effects. Subtle movements only (4-12px).

### 28. Key UI Screens

| Screen | Layout |
|--------|--------|
| **Dashboard** | Metric cards + charts + activity feed |
| **Context Library** | Tab filters + card list + search |
| **Context Editor** | Split view: Monaco + Markdown preview |
| **Prompt Builder** | Context selector + variable panel + live preview |
| **Graph Explorer** | ReactFlow full-page graph |
| **Conversations** | List + chat panel |
| **Analytics** | Charts + tables |
| **Settings** | Grouped form sections |
| **Command Palette** | Centered overlay (Cmd+K) |

### 29. UI States

Every component must handle:
- **Empty:** Illustration + description + CTA
- **Loading:** Skeleton screens (not spinners)
- **Error:** Message + retry button
- **Success:** Toast notification

### 30. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Command Palette |
| `Cmd+\` | Toggle Sidebar |
| `Cmd+1-4` | Navigate sections |
| `Cmd+B` | Prompt Builder |
| `Cmd+N` | New Conversation |
| `Cmd+Shift+C` | Create Context |
| `Cmd+Shift+F` | Search Everywhere |
| `Cmd+S` | Save |
| `Cmd+Z` / `Cmd+Shift+Z` | Undo/Redo |
| `/` | Focus Search |

---

## PART VIII — SECURITY

---

### 31. Security Requirements

| Requirement | Implementation |
|-------------|---------------|
| **API Key Protection** | Keys in `.env` only. Never in DB, frontend, logs, or responses. |
| **SQL Injection Prevention** | All queries use parameterized statements. Zero string interpolation. |
| **XSS Prevention** | React auto-escaping. Markdown sanitized. |
| **Input Validation** | Every API input validated via Pydantic with strict constraints. |
| **Rate Limiting** | AI endpoints: 10 req/min. General: 100 req/min. |
| **Audit Logging** | All create/update/delete operations logged to `audit_log` table. |
| **Secret Redaction** | Content matching API key patterns redacted in logs. |
| **CORS** | Restricted to frontend origin only. |
| **Prepared Statements** | Mandatory for ALL database operations. |
| **Path Traversal Prevention** | File operations use allowlisted base directories. |

---

## PART IX — PERFORMANCE

---

### 32. Performance Requirements

| Metric | Target |
|--------|--------|
| Page load (initial) | < 2 seconds |
| API response (non-AI) | < 200ms |
| Full AI pipeline | < 15 seconds |
| FTS5 search | < 50ms |
| Hybrid search | < 500ms |
| Frontend bundle (initial) | < 500KB |

### 33. Performance Techniques

| Technique | Where |
|-----------|-------|
| **SQLite Indexes** | All foreign keys, query patterns, partial indexes |
| **FTS5** | Full-text search with BM25 |
| **WAL Mode** | Concurrent read access |
| **Connection Pool** | SQLAlchemy pool_size=5, max_overflow=10 |
| **Caching** | TanStack Query (30s staleTime), Python lru_cache (settings) |
| **Debounce** | Search input (300ms), autosave (2s) |
| **Lazy Loading** | Monaco Editor, ReactFlow (React.lazy) |
| **Virtual Scrolling** | @tanstack/react-virtual for lists > 100 items |
| **Background Jobs** | Embedding, auto-tagging (FastAPI BackgroundTasks) |
| **Code Splitting** | Next.js automatic per-route splitting |
| **Optimistic Updates** | TanStack Query onMutate for instant feedback |

---

## PART X — TESTING

---

### 34. Testing Strategy

| Level | Framework | Coverage Target |
|-------|-----------|----------------|
| **Unit** (Backend) | pytest | ≥ 90% |
| **Unit** (Frontend) | Vitest + React Testing Library | ≥ 90% |
| **Integration** (Backend) | pytest + httpx (TestClient) | All API endpoints |
| **Integration** (Frontend) | Vitest | All hooks, complex components |
| **E2E** | Playwright | All critical user flows |
| **Prompt Regression** | pytest | 20 golden test cases |

### 35. Testing Rules

| Rule | Detail |
|------|--------|
| **Test isolation** | Each test uses fresh database |
| **No mocking production code** | Mock external services only (Azure OpenAI) |
| **Factories** | Use factory functions for test data, not fixtures |
| **Naming** | `test_<feature>_<scenario>_<expected>` |
| **No flaky tests** | Deterministic. No sleep(), no random(). |
| **CI-ready** | All tests runnable in CI without external dependencies |

### 36. Prompt Regression Testing

- 20 golden test cases with known input and expected prompt structure
- Test verifies: section ordering, variable substitution, dependency inclusion
- Score regression: average score must not decrease by > 5%
- Run on every PR

---

## PART XI — CODING STANDARDS

---

### 37. Python Standards

| Standard | Rule |
|----------|------|
| **Type hints** | ALL functions have full type annotations. No untyped functions. |
| **Strict typing** | Use `mypy --strict` or equivalent |
| **Pydantic v2** | All API models use Pydantic with strict mode |
| **Async** | All I/O operations are async (async def, await) |
| **Docstrings** | All public functions have docstrings |
| **Naming** | snake_case for functions/variables, PascalCase for classes |
| **Max function length** | 50 lines. Split if longer. |
| **Max file length** | 300 lines. Split if longer. |
| **No bare except** | Always catch specific exceptions |
| **No `# type: ignore`** | Fix the type error |
| **No `Any`** | Use specific types or generics |
| **No magic numbers** | Use named constants |
| **No dead code** | Remove unused imports, functions, variables |
| **No TODO in release** | Resolve all TODOs before merge |

### 38. TypeScript Standards

| Standard | Rule |
|----------|------|
| **Strict mode** | `"strict": true` in tsconfig.json |
| **No `any`** | Use proper types. `unknown` if truly unknown. |
| **No `as` casts** | Use type guards instead |
| **Interface over type** | For object shapes. Use `type` for unions/intersections. |
| **Props always typed** | Every component has explicit Props interface |
| **Hooks return types** | All custom hooks have explicit return types |
| **Named exports** | No default exports (except Next.js pages) |
| **Naming** | camelCase (functions/variables), PascalCase (components/types), UPPER_SNAKE_CASE (constants) |
| **Max component length** | 200 lines. Split if longer. |
| **No inline styles** | Use Tailwind classes |
| **No `index` as key** | Use unique IDs |

### 39. General Principles

| Principle | Rule |
|-----------|------|
| **SOLID** | Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion |
| **KISS** | Keep It Simple, Stupid |
| **DRY** | Don't Repeat Yourself (but don't over-abstract either) |
| **YAGNI** | You Aren't Gonna Need It. Build what's needed now. |
| **Explicit > Implicit** | No magic. All behavior traceable. |
| **Composition > Inheritance** | Prefer composing behaviors over deep inheritance chains. |
| **Fail Fast** | Validate early. Throw errors early. Don't silently swallow. |

---

## PART XII — DEVELOPMENT WORKFLOW

---

### 40. Git Conventions

| Convention | Rule |
|-----------|------|
| **Branch naming** | `feature/M{number}-{description}` (e.g., `feature/M5-context-crud`) |
| **Commit messages** | `[M{number}] {type}: {description}` (e.g., `[M5] feat: add context CRUD API`) |
| **Commit types** | `feat`, `fix`, `refactor`, `test`, `docs`, `chore` |
| **Commit frequency** | Commit after each logical unit of work |
| **Main branch** | Always deployable |

### 41. Development Process

1. **Read the Constitution** (this document)
2. **Read IMPLEMENTATION_PLAN.md** for current milestone
3. **Read companion docs** (ARCHITECTURE.md, DATABASE.md, AI_ARCHITECTURE.md, UI_GUIDELINES.md) as needed
4. **Implement the milestone** following all constraints
5. **Write tests** achieving ≥ 90% coverage
6. **Verify** the acceptance criteria
7. **Commit** with proper message
8. **Move to next milestone**

### 42. Code Review Checklist (Self-Review)

Before marking a milestone as complete, verify:

- [ ] All acceptance criteria met
- [ ] Tests written and passing
- [ ] Coverage ≥ 90%
- [ ] No `any`, `# type: ignore`, bare except
- [ ] No TODO comments
- [ ] No dead code
- [ ] No magic numbers
- [ ] All functions typed
- [ ] Max file/function length respected
- [ ] Architecture constraints respected (no business logic in routers, etc.)
- [ ] Security requirements met (no SQL injection, no exposed keys)
- [ ] Performance targets met (< 200ms API response)

---

## PART XIII — ACCEPTANCE CRITERIA

---

### 43. Project-Level Acceptance Criteria

The Pocket project is complete when ALL of the following are true:

#### 43.1 Functional

- [ ] All 50 milestones from IMPLEMENTATION_PLAN.md are complete
- [ ] All 32 database tables created and functional
- [ ] All API endpoints from ARCHITECTURE.md implemented and tested
- [ ] Full 18-step AI pipeline executing end-to-end
- [ ] Hybrid retrieval engine (FTS5 + RapidFuzz + Embedding) functional
- [ ] Context ranking with 9-factor scoring operational
- [ ] Validation engine blocking invalid prompts
- [ ] Prompt optimization reducing tokens without quality loss
- [ ] All 14 AI features functional
- [ ] Learning engine generating context candidates
- [ ] Import/export fully functional with round-trip integrity
- [ ] All UI screens from UI_GUIDELINES.md implemented

#### 43.2 Quality

- [ ] Backend test coverage ≥ 90%
- [ ] Frontend test coverage ≥ 90%
- [ ] E2E tests cover all critical user flows
- [ ] Prompt regression tests established with baselines
- [ ] Zero `any` types in TypeScript
- [ ] Zero `# type: ignore` in Python
- [ ] Zero TODO comments in release code
- [ ] Zero dead code

#### 43.3 Performance

- [ ] Page load < 2 seconds
- [ ] Non-AI API response < 200ms
- [ ] Full AI pipeline < 15 seconds
- [ ] Frontend bundle < 500KB initial
- [ ] No N+1 queries
- [ ] All queries use indexes (verified with EXPLAIN QUERY PLAN)

#### 43.4 Security

- [ ] API keys never exposed in DB, frontend, logs, or API responses
- [ ] All queries use parameterized statements
- [ ] Input validation on all API endpoints
- [ ] Rate limiting on AI endpoints
- [ ] Audit logging operational
- [ ] CORS properly configured

#### 43.5 Architecture

- [ ] Clean Architecture respected (no layer violations)
- [ ] Feature-first folder structure maintained
- [ ] Repository pattern used for all data access
- [ ] Service layer handles all business logic
- [ ] AI layer isolated from direct DB access
- [ ] No circular imports
- [ ] No god classes (>300 lines)

#### 43.6 UX

- [ ] All keyboard shortcuts working
- [ ] Command palette functional (Cmd+K)
- [ ] Dark mode and light mode working
- [ ] All empty, loading, error states implemented
- [ ] Autosave working
- [ ] Responsive layout (sidebar collapses on mobile)
- [ ] Virtual scrolling for long lists
- [ ] Animations smooth and purposeful

---

## PART XIV — COMPANION DOCUMENTS

---

### 44. Document Reference

| Document | Purpose | Location |
|----------|---------|----------|
| **SYSTEM_PROMPT.md** | This document. The Constitution. | `docs/SYSTEM_PROMPT.md` |
| **ARCHITECTURE.md** | Detailed software architecture, layers, modules, data flow, API catalog, sequence diagrams, state diagrams | `docs/ARCHITECTURE.md` |
| **DATABASE.md** | Complete database specification: 32 tables, ERD, indexes, FTS5, migrations, query patterns | `docs/DATABASE.md` |
| **AI_ARCHITECTURE.md** | AI pipeline, retrieval engine, ranking algorithm, validation, optimization, learning engine, embedding, features | `docs/AI_ARCHITECTURE.md` |
| **UI_GUIDELINES.md** | Design system: colors, typography, spacing, motion, components, interactions, states, accessibility | `docs/UI_GUIDELINES.md` |
| **IMPLEMENTATION_PLAN.md** | 50 milestones with acceptance criteria, organized in 8 phases | `docs/IMPLEMENTATION_PLAN.md` |

### 45. Document Hierarchy

```
SYSTEM_PROMPT.md (Constitution — highest authority)
├── ARCHITECTURE.md (Software architecture detail)
├── DATABASE.md (Database specification detail)
├── AI_ARCHITECTURE.md (AI pipeline detail)
├── UI_GUIDELINES.md (Design system detail)
└── IMPLEMENTATION_PLAN.md (Execution roadmap)
```

If any companion document contradicts this Constitution, **this Constitution takes precedence.**

---

## EPILOGUE

Pocket exists to make AI interactions more effective through intelligent context engineering. Every architectural decision, every line of code, every UI element must serve this mission.

When in doubt, ask: **Does this help create a better prompt?**

If the answer is no, remove it.

Build simple. Build correct. Build useful.

---

*End of SYSTEM_PROMPT.md — The Pocket Constitution*
