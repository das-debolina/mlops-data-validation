"""Profile the messy dataset and print per-issue counts.

Run::

    python profile_issues.py

The counts printed here are the ones documented in assignment2_report.md.
"""

from __future__ import annotations

import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(ROOT, "data", "customer_data.csv")

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
ALLOWED_COUNTRIES = {"USA", "Canada", "UK", "Australia"}


def main() -> None:
    df = pd.read_csv(CSV)
    n = len(df)
    print(f"Total rows: {n:,}\n")

    def line(label, count):
        pct = f"{count / n * 100:5.2f}%"
        print(f"  {label:<46s} {count:>6,}  ({pct})")

    print("customer_id")
    line("missing (null)", df["customer_id"].isna().sum())
    dup_ids = df["customer_id"].duplicated(keep=False) & df["customer_id"].notna()
    line("non-unique id values", dup_ids.sum())
    line("fully duplicated rows", df.duplicated(keep=False).sum())

    print("\nage")
    line("missing (null)", df["age"].isna().sum())
    line("negative (< 0)", (df["age"] < 0).sum())
    line("above 120", (df["age"] > 120).sum())

    print("\nemail")
    line("missing (null)", df["email"].isna().sum())
    invalid_email = df["email"].dropna().apply(lambda x: not EMAIL_REGEX.match(str(x)))
    line("invalid format (non-null)", invalid_email.sum())

    print("\nsalary")
    line("missing (null)", df["salary"].isna().sum())
    print(f"  {'present rate':<46s} {df['salary'].notna().mean() * 100:5.2f}%  (threshold 95%)")
    line("negative (< 0)", (df["salary"] < 0).sum())

    print("\ncountry")
    line("missing (null)", df["country"].isna().sum())
    bad_country = df["country"].dropna().apply(lambda c: c not in ALLOWED_COUNTRIES)
    line("outside allowed set (non-null)", bad_country.sum())

    print("\nsignup_date")
    line("missing (null)", df["signup_date"].isna().sum())
    parsed = pd.to_datetime(df["signup_date"], format="%Y-%m-%d", errors="coerce")
    line("invalid date strings (non-null)", (parsed.isna() & df["signup_date"].notna()).sum())
    print(f"  {'stored dtype':<46s} {df['signup_date'].dtype}  (expected datetime)")

    print("\ntable")
    print(f"  {'row count':<46s} {n:,}  (expected 500-1000)")


if __name__ == "__main__":
    main()
