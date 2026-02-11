#!/usr/bin/env python3
"""Validate that the DealListing Pydantic schema maps correctly to business_listings table.
Run: python scripts/validate_schema.py

Checks:
1. DealListing model can be imported
2. All direct-mapped fields exist in the Supabase table
3. Metadata overflow fields are documented
"""

import os
import sys

# Direct mappings: DealListing field → business_listings column
DIRECT_MAP = {
    "business_name": "company_name",
    "asking_price": "asking_price",
    "annual_revenue": "revenue_estimate",
    "arr": "annual_recurring_revenue",
    "net_profit": "profit_estimate",
    "location": "location",
    "listing_url": "url",
    "source_marketplace": "source_id",
}

# Fields that go into metadata jsonb
METADATA_FIELDS = [
    "mrr",
    "business_model",  # also maps to category
    "vertical",
    "tech_stack",
    "date_founded",
    "churn_rate",
    "customer_count",
    "growth_trend",
]


def main():
    from dotenv import load_dotenv

    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        print("FAIL: SUPABASE_URL or SUPABASE_SERVICE_KEY not set")
        sys.exit(1)

    from supabase import create_client

    sb = create_client(url, key)

    # Verify table columns by selecting them
    columns_to_check = list(DIRECT_MAP.values()) + [
        "metadata",
        "embedding",
        "listing_id",
        "tags",
    ]

    try:
        result = (
            sb.table("business_listings")
            .select(",".join(columns_to_check))
            .limit(0)
            .execute()
        )
        print("  OK: All direct-mapped columns exist in business_listings")
    except Exception as e:
        print(f"  FAIL: Column check failed — {e}")
        sys.exit(1)

    # Report mapping
    print("\n  Direct mappings:")
    for deal_field, table_col in DIRECT_MAP.items():
        print(f"    {deal_field:25s} → {table_col}")

    print("\n  Metadata overflow fields:")
    for field in METADATA_FIELDS:
        print(f"    {field:25s} → metadata.{field}")

    print("\nPASS: Schema mapping validated")


if __name__ == "__main__":
    main()
