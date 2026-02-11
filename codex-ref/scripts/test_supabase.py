#!/usr/bin/env python3
"""Test Supabase connection and verify all 4 tables exist with correct columns.
Run: python scripts/test_supabase.py
"""

import os
import sys


def main():
    # Load env
    from dotenv import load_dotenv

    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        print("FAIL: SUPABASE_URL or SUPABASE_SERVICE_KEY not set in .env")
        sys.exit(1)

    from supabase import create_client

    sb = create_client(url, key)

    tables = {
        "sources": ["source_id", "summary", "total_word_count"],
        "crawled_pages": [
            "id",
            "url",
            "chunk_number",
            "content",
            "metadata",
            "source_id",
            "embedding",
        ],
        "business_listings": [
            "listing_id",
            "company_name",
            "url",
            "asking_price",
            "revenue_estimate",
            "source_id",
        ],
        "buyer_profiles": ["buyer_id", "name", "buyer_type", "focus_industries"],
    }

    passed = 0
    failed = 0

    for table, expected_cols in tables.items():
        try:
            result = sb.table(table).select(",".join(expected_cols)).limit(1).execute()
            count = len(result.data)
            print(f"  OK: {table} — accessible, {count} rows, columns verified")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {table} — {e}")
            failed += 1

    print(f"\nResult: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
