# GEMINI.MD — M&A Deal Crawler

You are the autonomous build agent (Gemini) for an M&A deal crawler inside `mcp-crawl4ai-rag/`. You write code, run terminal commands, test, and debug — one pipeline stage at a time.

---

## Project

**What:** Crawl M&A marketplaces (Acquire.com, BizBuySell, Flippa, Empire Flippers), extract structured business-for-sale listings via LLM, store in Supabase.

**Base repo:** `coleam00/mcp-crawl4ai-rag` — MCP server + Crawl4AI + Supabase + pgvector already wired.

**Stack:** Python 3.12, crawl4ai 0.6.2, supabase-py, openai (embeddings), LiteLLM (DeepSeek primary, GPT-4o fallback).

---

## Pipeline

```
Phase 1: Prefetch discovery (fast HTML + link extraction)
    → Filter & score URLs (marketplace-specific patterns)
        → Phase 2: Batch dispatch (MemoryAdaptiveDispatcher + RateLimiter)
            → LLM extract per page (DealListing Pydantic schema)
                → Supabase upsert (dedup by URL)
```

---

## Key Files

| File | Role | Status |
|------|------|--------|
| `mcp-crawl4ai-rag/src/crawl4ai_mcp.py` | Main MCP server (1854 lines) | Unmodified — will be extended |
| `mcp-crawl4ai-rag/src/utils.py` | Supabase client, embeddings, search (738 lines) | Unmodified — will be extended |
| `codex-ref/crawl4ai_scripts/` | 4 reference scripts from Crawl4AI | **READ-ONLY — never edit** |
| `codex-ref/SUPABASE_SCHEMA.md` | Live Supabase schema reference | Updated after every migration |
| `codex-ref/references/pipeline.md` | Pipeline architecture + script mapping | Reference doc |
| `codex-ref/references/failures.md` | Known failures and how to avoid them | Reference doc |
| `codex-ref/scripts/test_supabase.py` | Verify Supabase connection + tables | Run to validate env |
| `codex-ref/scripts/test_single_extract.py` | Test LLM extraction on one URL | Run to validate extraction |
| `Goal.MD` (workspace root) | Full requirements spec | Read when you need field-level detail |

---

## What's Built vs What's Not

**Done:** Supabase tables (sources, crawled_pages, business_listings, buyer_profiles), RPC functions, pgvector indexes, embedding helpers, MCP server skeleton, reference scripts downloaded.

**Not built yet:**
- [ ] `DealListing` Pydantic schema
- [ ] DeepSeek provider config
- [ ] Marketplace URL filters + keyword scorers
- [ ] Two-phase crawl wired to index pages
- [ ] Batch dispatcher with rate limits
- [ ] Supabase upsert with URL dedup
- [ ] Embedding generation for listings

---

## Rules

### 1. Think, then code
State assumptions before implementing. If multiple approaches exist, name them. If unclear, ask.

### 2. Simplicity first
Minimum code that solves the problem. No speculative features, no premature abstractions. If 200 lines could be 50, rewrite.

### 3. Surgical changes
Touch only what you must. Don't "improve" adjacent code. Match existing style. Every changed line traces to the task.

### 4. Never delete — replace
When modifying `src/` files, replace functions in-place. Comment out deprecated code with `# DEPRECATED: reason`. Don't gut files.

### 5. Reference scripts are read-only
Files in `codex-ref/crawl4ai_scripts/` are untouchable. Copy patterns into `mcp-crawl4ai-rag/src/` or new files.

### 6. Test before moving on
Each pipeline stage must be verified independently before building the next:
- Extraction → test one known URL → verify JSON matches schema
- Crawl → test one marketplace → verify URLs discovered
- Supabase → test one insert → verify row + columns
- Dedup → insert same URL twice → verify no duplicate

### 7. Environment
All API keys in `.env` (never hardcoded). Key vars:
- `OPENAI_API_KEY` — embeddings (text-embedding-3-small)
- `DEEPSEEK_API_KEY` — primary LLM via LiteLLM
- `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` — database
- Provider string: `deepseek/deepseek-chat`

### 8. Schema changes = migrations
Use Supabase `apply_migration` for DDL. Update `SUPABASE_SCHEMA.md` after every migration.

### 9. Commits
After each working pipeline stage (not each file edit). Format: `feat:` / `fix:` / `chore:`

---

## When you need more context

- **Full schema details** → read `codex-ref/SUPABASE_SCHEMA.md`
- **Pipeline architecture + script mapping** → read `codex-ref/references/pipeline.md`
- **Known failures & pitfalls** → read `codex-ref/references/failures.md`
- **Field-level requirements** → read `Goal.MD` (workspace root)
- **Build plan + checklist** → read `.github/agents/Discovery-planner.agent.md`
