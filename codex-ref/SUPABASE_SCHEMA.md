# Supabase Schema Reference

> **Project:** `vjipbmnawfdpmqsbcpju`  
> **Snapshot date:** 2026-02-11  
> **All tables truncated** — 0 rows across the board.

---

## Tables

### 1. `sources`

Parent table — tracks each crawled domain/source.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `source_id` | `text` | **NO** (PK) | — | e.g. `"acquire.com"`, `"flippa.com"` |
| `summary` | `text` | YES | — | LLM-generated summary of the source |
| `total_word_count` | `integer` | YES | `0` | Aggregate word count across crawled pages |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | |

**PK:** `source_id`  
**Referenced by:** `crawled_pages.source_id`, `business_listings.source_id`

---

### 2. `crawled_pages`

Raw crawled content, chunked for embedding.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | `bigint` | **NO** (PK) | `nextval(seq)` | Auto-increment |
| `url` | `varchar` | NO | — | Full page URL |
| `chunk_number` | `integer` | NO | — | Chunk index within a page |
| `content` | `text` | NO | — | Chunked text content |
| `metadata` | `jsonb` | NO | `'{}'` | Arbitrary metadata |
| `source_id` | `text` | NO | — | FK → `sources.source_id` |
| `embedding` | `vector` | YES | — | pgvector embedding |
| `created_at` | `timestamptz` | NO | `now()` | |

**PK:** `id`  
**Unique:** `(url, chunk_number)`  
**FK:** `source_id` → `sources.source_id`

---

### 3. `business_listings`

Structured M&A deal listings extracted by LLM.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `listing_id` | `text` | **NO** (PK) | — | UUID string |
| `company_name` | `text` | YES | — | Business name |
| `url` | `text` | NO | — | Listing source URL |
| `description` | `text` | YES | — | Business description |
| `category` | `text` | YES | — | e.g. `"SaaS / Analytics"` |
| `revenue_estimate` | `numeric` | YES | — | Annual revenue |
| `profit_estimate` | `numeric` | YES | — | Net profit / SDE |
| `annual_recurring_revenue` | `numeric` | YES | — | ARR |
| `employee_count` | `integer` | YES | — | |
| `location` | `text` | YES | — | |
| `asking_price` | `numeric` | YES | — | |
| `tags` | `jsonb` | YES | `'[]'` | Array of tags |
| `metadata` | `jsonb` | YES | `'{}'` | Extra KV data |
| `source_id` | `text` | YES | — | FK → `sources.source_id` |
| `embedding` | `vector` | YES | — | pgvector embedding |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | |

**PK:** `listing_id`  
**FK:** `source_id` → `sources.source_id`

---

### 4. `buyer_profiles`

Buyer/investor profiles for deal matching.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `buyer_id` | `text` | **NO** (PK) | — | UUID string |
| `name` | `text` | NO | — | Buyer/fund name |
| `buyer_type` | `text` | YES | — | e.g. `"PE"`, `"Individual"` |
| `focus_industries` | `text[]` | YES | — | Array of industries |
| `ticket_size_min` | `numeric` | YES | — | Min deal size |
| `ticket_size_max` | `numeric` | YES | — | Max deal size |
| `preferred_categories` | `text[]` | YES | — | Array of categories |
| `geographies` | `text[]` | YES | — | Array of locations |
| `notes` | `text` | YES | — | |
| `metadata` | `jsonb` | YES | `'{}'` | |
| `embedding` | `vector` | YES | — | pgvector embedding |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | |

**PK:** `buyer_id`  
**No FKs** (standalone table)

---

## Indexes

### `business_listings`
| Index | Type | Column(s) |
|-------|------|-----------|
| `business_listings_pkey` | UNIQUE btree | `listing_id` |
| `idx_business_listings_asking_price` | btree | `asking_price` |
| `idx_business_listings_arr` | btree | `annual_recurring_revenue` |
| `idx_business_listings_revenue` | btree | `revenue_estimate` |
| `idx_business_listings_source_id` | btree | `source_id` |
| `idx_business_listings_category` | btree | `category` |
| `idx_business_listings_tags` | GIN | `tags` |
| `idx_business_listings_metadata` | GIN | `metadata` |
| `idx_business_listings_embedding` | IVFFlat (cosine) | `embedding` |

### `buyer_profiles`
| Index | Type | Column(s) |
|-------|------|-----------|
| `buyer_profiles_pkey` | UNIQUE btree | `buyer_id` |
| `idx_buyer_profiles_type` | btree | `buyer_type` |
| `idx_buyer_profiles_ticket_min` | btree | `ticket_size_min` |
| `idx_buyer_profiles_ticket_max` | btree | `ticket_size_max` |
| `idx_buyer_profiles_metadata` | GIN | `metadata` |
| `idx_buyer_profiles_embedding` | IVFFlat (cosine) | `embedding` |

### `crawled_pages`
| Index | Type | Column(s) |
|-------|------|-----------|
| `crawled_pages_pkey` | UNIQUE btree | `id` |
| `crawled_pages_url_chunk_number_key` | UNIQUE btree | `(url, chunk_number)` |
| `idx_crawled_pages_source_id` | btree | `source_id` |
| `idx_crawled_pages_metadata` | GIN | `metadata` |
| `crawled_pages_embedding_idx` | IVFFlat (cosine) | `embedding` |

### `sources`
| Index | Type | Column(s) |
|-------|------|-----------|
| `sources_pkey` | UNIQUE btree | `source_id` |

---

## RLS Policies

All 4 tables have RLS **enabled** with a single read-only policy each:

| Table | Policy | Command | Qualifier |
|-------|--------|---------|-----------|
| `sources` | Allow public read access to sources | SELECT | `true` |
| `crawled_pages` | Allow public read access to crawled_pages | SELECT | `true` |
| `business_listings` | Allow public read access to business_listings | SELECT | `true` |
| `buyer_profiles` | Allow public read access to buyer_profiles | SELECT | `true` |

> **Note:** Only SELECT is allowed via RLS. INSERT/UPDATE/DELETE require service_role key.

---

## Custom Functions (RPC)

### `match_crawled_pages(query_embedding, match_count, filter, source_filter)`
Vector similarity search on `crawled_pages`. Filters by `metadata @> filter` and optional `source_id`.

### `match_business_listings(query_embedding, match_count, ...filters)`
Vector similarity search on `business_listings` with optional filters:
`category_filter`, `min/max_revenue`, `min/max_arr`, `min/max_asking_price`, `location_filter`, `source_filter`, `tags_filter`.

### `match_buyer_profiles(query_embedding, match_count, buyer_type_filter, min/max_ticket)`
Vector similarity search on `buyer_profiles` with optional type and ticket size filters.

### `match_buyer_to_listings(p_buyer_id, match_count)`
Given a buyer, finds matching listings by ticket size + preferred categories + vector similarity. Returns `match_reasons[]` array.

### `find_buyers_for_listing(p_listing_id, match_count)`
Given a listing, finds matching buyers by price range + category overlap + vector similarity. Returns `match_reasons[]` array.

---

## Migration History

| Version | Name |
|---------|------|
| `20260211014112` | `allow_null_company_name` |

---

## What Was Attempted (Previous Session)

The schema was designed for an M&A deal crawler pipeline. Data that existed before truncation:

- **22 sources** — Crawled domains including `acquire.com`, `bizbuysell.com`, `flippa.com`, `adventinternational.com`, `sitefy.co`, `businessesforsale.com`, `example-marketplace.com`, `localhost:8085` (mock)
- **285 crawled_pages** — Raw chunked content from those sources, with embeddings
- **12 business_listings** — Extracted deal listings (mostly incomplete — many had null `asking_price`, null `revenue_estimate`, some had numeric IDs as `company_name` like `"11951475"` from Flippa)
- **10 buyer_profiles** — Test buyer profiles (`"Test Capital Partners"`, `"SaaS Growth Fund"`, `"Indie Hacker Fund"`, etc.)

**What went wrong:**
- Flippa listings extracted with Flippa listing IDs as company names instead of actual business names
- Many listings had null financials — LLM extraction likely got blocked pages or didn't parse correctly
- BizBuySell only returned 6 words (Akamai bot-protection page was crawled, not actual content)
- Mix of real crawls and mock/test data muddied the results
- No deduplication by URL was enforced at the application layer
