## What the Crawler Must Do

Crawl M&A marketplaces and the broader web, extract structured business-for-sale listings using LLM-based extraction, and store results in Supabase.

---

## Requirements

### Crawling

- Deep crawl across multiple sites ([Acquire.com](http://Acquire.com), BizBuySell, Flippa, Empire Flippers, broader web)
- Async crawling for speed
- BFS deep crawl strategy to follow listing links from index pages
- Stealth mode / proxy support to avoid blocks
- Session management for sites requiring login

### Extraction

- LLM-based extraction using Pydantic schemas (not CSS selectors — layouts vary across sites)
- Structured JSON output per listing with these fields:
    - Business name
    - Asking price
    - Annual revenue / ARR / MRR
    - Net profit / SDE
    - Business model (all tech business models etc.)
    - Vertical / industry
    - Tech stack
    - Date founded
    - Location
    - Churn rate
    - Customer count
    - Growth trend
    - Listing URL (source)
    - Date scraped

### Storage

- Push structured JSON directly into Supabase (Postgres)
- Deduplicate by listing URL
- Embeddings via pgvector for semantic search later

### LLM

- DeepSeek as primary (cheap, fast)
- Fallback to GPT-4o or Claude for complex pages

---

## Base Repo

[**coleam00/mcp-crawl4ai-rag**](https://github.com/coleam00/mcp-crawl4ai-rag) — MCP + Crawl4AI + Supabase already wired. We fork and customize.

---

## 4 Scripts to Take from Crawl4AI Repo

All from [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai/tree/main) `main` branch. Each needs only light mods.

---

### Script 1 — LLM Extraction (the core)

**Path:** `docs/examples/llm_extraction_openai_[pricing.py](http://pricing.py)`

**Link:** [View on GitHub](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/llm_extraction_openai_pricing.py)

**What it does:** Crawls a single page, extracts structured JSON using a Pydantic schema + `LLMExtractionStrategy`. Uses LiteLLM so any provider works. Handles chunking, token limits, temperature control.

**What we modify:**

- Swap `OpenAIModelFee` Pydantic schema → our `DealListing` schema (business name, price, revenue, etc.)
- Swap `provider="openai/gpt-4o"` → `provider="deepseek/deepseek-chat"` with DeepSeek API key
- Swap URL from OpenAI pricing → marketplace listing URLs
- Add `input_format="fit_markdown"` to reduce token cost
- Add `apply_chunking=True` for long listing pages

**Effort:** ~30 min. Schema swap + provider swap. Everything else works as-is.

---

### Script 2 — Deep Crawl with Filters + Scorers

**Path:** `docs/examples/deepcrawl_[example.py](http://example.py)`

**Link:** [View on GitHub](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/deepcrawl_example.py)

**What it does:** Full deep crawling tutorial (18KB). Demonstrates BFS, DFS, BestFirstCrawlingStrategy. Uses `FilterChain` (URLPatternFilter, DomainFilter, ContentTypeFilter), `KeywordRelevanceScorer`, streaming mode, max_pages limits, and score thresholds.

**What we take:** The `wrap_up()` function pattern — combines BestFirst strategy + filter chain + keyword scorer + streaming. This is our marketplace crawler skeleton.

**What we modify:**

- `allowed_domains` → `["[acquire.com](http://acquire.com)", "[bizbuysell.com](http://bizbuysell.com)", "[flippa.com](http://flippa.com)", "[empireflippers.com](http://empireflippers.com)"]`
- `URLPatternFilter` patterns → `["*listing*", "*business*", "*for-sale*", "*startup*"]`
- `KeywordRelevanceScorer` keywords → `["saas", "revenue", "arr", "ebitda", "asking price", "business for sale"]`
- `max_depth=2`, `max_pages=100` for production
- Plug Script 1's `LLMExtractionStrategy` into `CrawlerRunConfig.extraction_strategy`

**Effort:** ~1 hour. Filter/scorer config + wire in LLM extraction from Script 1.

---

### Script 3 — Two-Phase Prefetch Crawl

**Path:** `docs/examples/prefetch_two_phase_[crawl.py](http://crawl.py)`

**Link:** [View on GitHub](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/prefetch_two_phase_crawl.py)

**What it does:** Two-phase crawling. Phase 1: `prefetch=True` for 5-10x faster URL discovery (HTML + links only, no markdown/extraction). Phase 2: full processing on selected URLs only. Includes deep crawl + prefetch combo.

**What we take:** The `example_two_phase_crawl()` pattern. Discover all listing URLs fast, filter to actual deal pages, then LLM-extract only those.

**What we modify:**

- Phase 1 URL → marketplace index pages (e.g. [`acquire.com/marketplace`](http://acquire.com/marketplace), [`bizbuysell.com/businesses`](http://bizbuysell.com/businesses))
- URL filter logic → match listing detail page patterns per site
- Phase 2 config → plug in our `LLMExtractionStrategy` from Script 1
- Add `arun_many` with dispatcher (Script 4) for batch Phase 2 processing

**Effort:** ~45 min. URL patterns + wire extraction strategy. The two-phase pattern is exactly what we need.

---

### Script 4 — Batch Dispatcher with Rate Limiting

**Path:** `docs/examples/dispatcher_[example.py](http://example.py)`

**Link:** [View on GitHub](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/dispatcher_example.py)

**What it does:** `MemoryAdaptiveDispatcher` + `RateLimiter` + `CrawlerMonitor` for crawling many URLs in parallel. Memory-aware concurrency (won't crash on large batches). Rate limiting with exponential backoff. Real-time monitoring dashboard.

**What we take:** The `memory_adaptive_with_rate_limit()` function. This is how we batch-process all the listing URLs discovered in Phase 1 (Script 3).

**What we modify:**

- `urls` list → listing URLs from Phase 1 discovery
- `RateLimiter(base_delay=(2.0, 4.0))` → polite delays per marketplace
- `memory_threshold_percent=70.0` → keep for production safety
- `max_session_permit=5` → conservative for marketplace scraping
- Plug in `CrawlerRunConfig` with our LLM extraction strategy

**Effort:** ~30 min. Mostly config tuning for rate limits and concurrency.

---

## How They Fit Together

<aside>
🔧

**Pipeline:** Script 3 (prefetch discovery) → Script 4 (batch dispatcher) → Script 1 (LLM extraction per page) → Supabase

Script 2 gives us the filter/scorer layer that wraps the whole thing — controlling which URLs get crawled and in what priority order.

</aside>

---

## Official Docs

- [LLM Extraction Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/) — Pydantic schemas, chunking, any LLM via LiteLLM
- [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/) — BFS/DFS/BestFirst, filters, scorers, crash recovery, prefetch mode
- [Code Examples Index](https://docs.crawl4ai.com/core/examples/) — Full list of all example scripts