"""CareerShield AI — India Fraud Counts Verification Script.

Inspects fake_job_postings.csv and computes exact counts under different filtering logics:
1. Exact Country ISO Code ('IN' as first token before comma)
2. Starts with 'IN,' (ISO location prefix)
3. Regex word boundary r'\bIN\b' (which accidentally includes US State Indiana 'US, IN, ...')
4. Literal text search 'India' in location string
5. Full text search 'India' across all job text fields (title, description, company_profile)

Usage:
    cd backend
    python data/docs/verify_india_counts.py
"""

from pathlib import Path
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = SCRIPT_DIR.parents[1] / "data" / "raw" / "fake_job_postings.csv"

def verify():
    print("=" * 80)
    print("CareerShield AI — India Postings Verification & Discrepancy Analysis")
    print(f"Dataset: {CSV_PATH}")
    print("=" * 80)

    df = pd.read_csv(CSV_PATH)
    print(f"Total dataset records: {len(df):,}")
    print(f"Total fraudulent records globally: {(df['fraudulent'] == 1).sum():,}")

    loc_clean = df["location"].fillna("").astype(str).str.strip()

    # --- Filter 1: Proper ISO Country Code extraction ---
    country_series = loc_clean.apply(lambda s: s.split(",")[0].strip() if "," in s else s)
    df_iso_in = df[country_series == "IN"]
    iso_counts = df_iso_in["fraudulent"].value_counts().to_dict()
    print("\n[FILTER 1] Standard ISO Country Code Extraction (location.split(',')[0].strip() == 'IN'):")
    print(f"  - Total Postings in India: {len(df_iso_in)}")
    print(f"  - Genuine (0):             {iso_counts.get(0, 0)}")
    print(f"  - Fraudulent (1):          {iso_counts.get(1, 0)}")
    print(f"  - Fraud Rate:              {iso_counts.get(1, 0) / len(df_iso_in) * 100:.2f}%")

    # List all fraudulent postings under Filter 1
    fake_iso_in = df_iso_in[df_iso_in["fraudulent"] == 1]
    print(f"\n  Details of Fraudulent Postings under Filter 1 (Total: {len(fake_iso_in)}):")
    for _, row in fake_iso_in.iterrows():
        print(f"    * ID: {row['job_id']:<5} | Title: {str(row['title'])[:30]:<30} | Location: {row['location']}")

    # --- Filter 2: Starts with 'IN,' ---
    df_startswith_in = df[loc_clean.str.startswith("IN,")]
    sw_counts = df_startswith_in["fraudulent"].value_counts().to_dict()
    print("\n[FILTER 2] Prefix Match (location.startswith('IN,')):")
    print(f"  - Total Postings:          {len(df_startswith_in)}")
    print(f"  - Genuine (0):             {sw_counts.get(0, 0)}")
    print(f"  - Fraudulent (1):          {sw_counts.get(1, 0)}")

    # --- Filter 3: Regex Word Boundary \bIN\b (Catches Indiana, USA) ---
    df_word_in = df[loc_clean.str.contains(r"\bIN\b", na=False)]
    wb_counts = df_word_in["fraudulent"].value_counts().to_dict()
    print("\n[FILTER 3] Word Boundary Regex (location.str.contains(r'\\bIN\\b')) [ACCIDENTAL INDIANA MATCH]:")
    print(f"  - Total Postings:          {len(df_word_in)}")
    print(f"  - Genuine (0):             {wb_counts.get(0, 0)}")
    print(f"  - Fraudulent (1):          {wb_counts.get(1, 0)}")
    # How many of these are Indiana, USA?
    df_us_indiana = df[loc_clean.str.contains(r"US,\s*IN", na=False)]
    us_in_counts = df_us_indiana["fraudulent"].value_counts().to_dict()
    print(f"    -> Of which US State of Indiana (US, IN, ...): {len(df_us_indiana)} postings")
    print(f"       Genuine in Indiana:    {us_in_counts.get(0, 0)}")
    print(f"       Fraudulent in Indiana: {us_in_counts.get(1, 0)}")

    # --- Filter 4: Literal 'India' in location ---
    df_literal_india = df[loc_clean.str.contains("India", case=False, na=False)]
    lit_counts = df_literal_india["fraudulent"].value_counts().to_dict()
    print("\n[FILTER 4] Literal String Search (location.str.contains('India', case=False)):")
    print(f"  - Total Postings:          {len(df_literal_india)}")
    print(f"  - Genuine (0):             {lit_counts.get(0, 0)}")
    print(f"  - Fraudulent (1):          {lit_counts.get(1, 0)}")

    # Summary table
    print("\n" + "=" * 80)
    print("VERIFICATION CONCLUSION:")
    print("=" * 80)
    print(f"1. Validated Country = 'IN' (India): {len(df_iso_in)} total postings.")
    print(f"   -> Genuine:    {iso_counts.get(0, 0)}")
    print(f"   -> Fraudulent: {iso_counts.get(1, 0)}")
    print("2. Source of Discrepancy (16 vs 4):")
    print("   - If Filter 1 yields 4, then the true number of fake Indian postings is 4.")
    print("   - If Filter 3 was used, word boundary '\\bIN\\b' matched Indiana ('US, IN, ...') which has additional fake jobs!")
    print("=" * 80)

if __name__ == "__main__":
    verify()
