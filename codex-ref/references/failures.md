# Known Failures & Pitfalls

Lessons from the previous crawl attempt. Each failure has a root cause and a fix strategy.

---

## 1. BizBuySell — Akamai Bot Protection

**Symptom:** Crawl returned 6-word HTML (bot challenge page) instead of listing content.

**Root cause:** BizBuySell uses Akamai bot detection. Default crawl4ai browser config triggers it.

**Fix strategy:**
- Use `BrowserConfig(headless=True, user_agent="...", extra_args=["--disable-blink-features=AutomationControlled"])`
- Enable stealth mode in crawl4ai: `CrawlerRunConfig(magic=True)`
- If still blocked: use proxy rotation or skip BizBuySell initially and focus on cleaner sites first
- Detect bot pages: if `len(markdown.split()) < 50`, flag as blocked and skip

---

## 2. Flippa — Listing IDs as Company Names

**Symptom:** LLM extracted listing IDs (e.g., "12345678") as the company name.

**Root cause:** The LLM extraction prompt was too vague. Flippa's HTML has the listing ID prominently in the URL/title, and the actual business name is deeper in the page.

**Fix strategy:**
- LLM instruction must explicitly say: "The business name is NOT the listing ID. Look for the actual company/product name in the description or header."
- Add `instruction` field to `LLMExtractionStrategy` with marketplace-specific guidance
- Validate: if `business_name` is all digits or matches URL pattern, flag for re-extraction

---

## 3. Null Financials

**Symptom:** Many listings had null for asking_price, revenue, profit — even when the data was on the page.

**Root cause:** Extraction prompt didn't tell the LLM where to look or what formats to expect (e.g., "$2.5M", "€50K/mo", "ARR: $120,000").

**Fix strategy:**
- LLM instruction: "Extract financial figures even if abbreviated. Convert K=thousands, M=millions. Monthly values should be noted as MRR. If a range is given, use the midpoint."
- Use `apply_chunking=True` — long pages may have financials below the chunk boundary
- Post-extraction validation: log listings with >3 null financial fields for review

---

## 4. Mixed Mock/Real Data

**Symptom:** Supabase had a mix of test data and real crawl results, making it impossible to trust any row.

**Root cause:** No source separation between test runs and real runs. Test inserts used real table, no cleanup.

**Fix strategy:**
- All tables are now truncated (clean slate)
- Test scripts should use a `test_` prefix in source_id (e.g., `test_acquire.com`)
- Before production runs: delete all `test_` prefixed sources
- Consider adding a `is_test` boolean column if test/prod mixing recurs

---

## 5. No URL Deduplication

**Symptom:** Same listing appeared multiple times across different crawl runs.

**Root cause:** No application-layer dedup. The `(url, chunk_number)` unique constraint on `crawled_pages` helps for raw content, but `business_listings` had no URL uniqueness constraint.

**Fix strategy:**
- `business_listings` needs a UNIQUE constraint on `url` (via migration)
- Application code: use `ON CONFLICT (url) DO UPDATE` for upsert behavior
- Before insert: check if URL already exists, compare `updated_at` to decide if re-extraction needed

---

## 6. Token Waste on Non-Listing Pages

**Symptom:** LLM extraction ran on about/terms/contact pages, wasting tokens and returning garbage.

**Root cause:** No URL filtering before extraction phase. Every discovered URL got full LLM treatment.

**Fix strategy:**
- Phase 1 (prefetch) discovers ALL URLs
- Filter layer (Script 2 pattern) screens before Phase 2:
  - `URLPatternFilter`: include only `*listing*`, `*business*`, `*for-sale*`, `*startup*`, `*marketplace*`
  - `ContentTypeFilter`: exclude PDFs, images, etc.
  - `DomainFilter`: only allowed marketplaces
- `KeywordRelevanceScorer` with deal terms: if score < threshold, skip
- This is the single highest-ROI fix — saves tokens AND improves data quality

---

## General Guards

| Guard | Implementation |
|-------|---------------|
| Bot detection | Check `len(markdown.split()) < 50` → flag as blocked |
| Empty extraction | If DealListing has no business_name AND no listing_url → discard |
| Financial validation | If all financial fields are null → log warning, still store but tag metadata.quality="incomplete" |
| Rate limiting | `RateLimiter(base_delay=(2.0, 4.0))` per marketplace — never faster |
| Memory safety | `memory_threshold_percent=70.0` — codespace has limited RAM |
