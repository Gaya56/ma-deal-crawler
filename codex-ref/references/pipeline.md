# Pipeline Architecture

## Overview

```
marketplace index pages
        │
        ▼
┌─────────────────────────┐
│  Phase 1: Prefetch       │  Fast HTML + link extraction (no markdown/LLM)
│  (Script 3 pattern)      │  5-10x faster than full crawl
└──────────┬──────────────┘
           │ discovered URLs
           ▼
┌─────────────────────────┐
│  Filter & Score          │  URLPatternFilter + DomainFilter + ContentTypeFilter
│  (Script 2 pattern)      │  KeywordRelevanceScorer ranks by deal relevance
└──────────┬──────────────┘
           │ filtered + scored URLs
           ▼
┌─────────────────────────┐
│  Phase 2: Batch Dispatch │  MemoryAdaptiveDispatcher + RateLimiter
│  (Script 4 pattern)      │  Parallel crawl with memory-aware concurrency
└──────────┬──────────────┘
           │ full page content
           ▼
┌─────────────────────────┐
│  LLM Extract             │  LLMExtractionStrategy + DealListing Pydantic schema
│  (Script 1 pattern)      │  DeepSeek primary, GPT-4o fallback via LiteLLM
└──────────┬──────────────┘
           │ structured JSON
           ▼
┌─────────────────────────┐
│  Supabase Upsert         │  Dedup by listing URL
│  (utils.py)              │  Generate pgvector embeddings
└─────────────────────────┘
```

---

## Script → Implementation Mapping

| Script | Source File | Key Function/Pattern | Our Implementation |
|--------|-----------|---------------------|-------------------|
| Script 1 | `crawl4ai_scripts/llm_extraction_openai_pricing.py` | `LLMExtractionStrategy` + `LLMConfig` + Pydantic model | Swap `OpenAIModelFee` → `DealListing`, provider → `deepseek/deepseek-chat` |
| Script 2 | `crawl4ai_scripts/deepcrawl_example.py` | `wrap_up()` — BestFirst + FilterChain + KeywordRelevanceScorer | Configure filters for marketplace URL patterns, keywords for deal terms |
| Script 3 | `crawl4ai_scripts/prefetch_two_phase_crawl.py` | `example_two_phase_crawl()` — prefetch=True Phase 1, full Phase 2 | Index pages → prefetch → filter → full extract on listing pages only |
| Script 4 | `crawl4ai_scripts/dispatcher_example.py` | `memory_adaptive_with_rate_limit()` — MemoryAdaptiveDispatcher | Batch process filtered URLs with polite delays per marketplace |

---

## Marketplace Entry Points

| Marketplace | Index URL(s) | Listing URL Pattern | Notes |
|-------------|-------------|-------------------|-------|
| Acquire.com | `acquire.com/marketplace` | `acquire.com/startup/*` | Clean HTML, usually no bot block |
| BizBuySell | `bizbuysell.com/businesses-for-sale/` | `bizbuysell.com/Business-Opportunity/*` | Akamai bot protection — needs stealth/proxy |
| Flippa | `flippa.com/businesses` | `flippa.com/*/` (numeric listing IDs) | API available; listing IDs ≠ company names |
| Empire Flippers | `empireflippers.com/marketplace/` | `empireflippers.com/listing/*` | Login may be required for details |

---

## Configuration Tuning

| Parameter | Value | Reason |
|-----------|-------|--------|
| `max_depth` | 2 | Index → listing detail (2 hops max) |
| `max_pages` | 100 | Per marketplace per run |
| `RateLimiter.base_delay` | `(2.0, 4.0)` | Polite — avoid bans |
| `memory_threshold_percent` | 70.0 | Safety for codespace |
| `max_session_permit` | 5 | Conservative concurrency |
| `input_format` | `"fit_markdown"` | Reduce token cost |
| `apply_chunking` | True | For long listing pages |
| `score_threshold` | 0.3 | Only extract pages likely to be deals |

---

## DealListing Pydantic Schema (Target)

```python
from pydantic import BaseModel
from typing import Optional

class DealListing(BaseModel):
    business_name: Optional[str] = None
    asking_price: Optional[float] = None
    annual_revenue: Optional[float] = None
    arr: Optional[float] = None          # Annual Recurring Revenue
    mrr: Optional[float] = None          # Monthly Recurring Revenue
    net_profit: Optional[float] = None   # or SDE
    business_model: Optional[str] = None # SaaS, ecommerce, content, etc.
    vertical: Optional[str] = None       # Industry vertical
    tech_stack: Optional[str] = None
    date_founded: Optional[str] = None
    location: Optional[str] = None
    churn_rate: Optional[float] = None
    customer_count: Optional[int] = None
    growth_trend: Optional[str] = None   # "growing", "stable", "declining"
    listing_url: str                      # Required — dedup key
    source_marketplace: Optional[str] = None
```

### Schema → Table Column Mapping

| DealListing Field | business_listings Column | Notes |
|------------------|------------------------|-------|
| business_name | company_name | Direct map |
| asking_price | asking_price | Direct map |
| annual_revenue | revenue_estimate | Direct map |
| arr | annual_recurring_revenue | Direct map |
| mrr | — | Store in metadata.mrr |
| net_profit | profit_estimate | Direct map |
| business_model | category | May need richer values |
| vertical | — | Store in tags or metadata.vertical |
| tech_stack | — | Store in metadata.tech_stack |
| date_founded | — | Store in metadata.date_founded |
| location | location | Direct map |
| churn_rate | — | Store in metadata.churn_rate |
| customer_count | employee_count | Rename semantics differ — use metadata.customer_count |
| growth_trend | — | Store in metadata.growth_trend |
| listing_url | url | Direct map, dedup key |
| source_marketplace | source_id | FK to sources table |
