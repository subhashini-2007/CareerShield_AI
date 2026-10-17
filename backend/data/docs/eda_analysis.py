"""CareerShield AI — Automated Exploratory Data Analysis (EDA) Script.

Performs comprehensive data inspection, validation, class imbalance analysis,
location analysis (with special focus on India), missing value audits,
and visualization generation for fake_job_postings.csv (EMSCAD).

Usage:
    cd backend
    python data/docs/eda_analysis.py
"""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

# Optional visualization imports with graceful fallback
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Path configurations relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parents[1]
RAW_DATA_PATH = BACKEND_DIR / "data" / "raw" / "fake_job_postings.csv"
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"
DOCS_DIR = BACKEND_DIR / "data" / "docs"
REPORT_OUTPUT_PATH = DOCS_DIR / "eda_report.md"


def run_eda(csv_path: Path = RAW_DATA_PATH):
    print("=" * 78)
    print("CareerShield AI — Exploratory Data Analysis (EDA)")
    print(f"Target Dataset: {csv_path}")
    print("=" * 78)

    if not csv_path.exists():
        print(f"[ERROR] Dataset not found at: {csv_path}")
        print("Please ensure fake_job_postings.csv exists in backend/data/raw/.")
        sys.exit(1)

    # 1. Load dataset using pandas
    print("\n[1/6] Loading dataset with Pandas...")
    df = pd.read_csv(csv_path)
    total_rows, total_cols = df.shape
    print(f"  - Dataset Shape: {total_rows:,} rows, {total_cols} columns")

    # 2. Check column names, types, missing values, duplicates
    print("\n[2/6] Inspecting Columns, Types, and Quality...")
    duplicates_full = df.duplicated().sum()
    cols_no_id = [c for c in df.columns if c != "job_id"]
    duplicates_no_id = df.duplicated(subset=cols_no_id).sum()
    print(f"  - Exact Duplicate Rows (including job_id): {duplicates_full}")
    print(f"  - Duplicate Postings (excluding job_id):   {duplicates_no_id}")

    missing_series = df.isnull().sum()
    missing_pct = (missing_series / total_rows) * 100

    print("\n  Column Summary:")
    print(f"  {'#':<3} {'Column Name':<22} {'Data Type':<12} {'Missing':<10} {'Missing %':<10}")
    print("  " + "-" * 62)
    for idx, col in enumerate(df.columns, 1):
        dtype_str = str(df[col].dtype)
        m_count = missing_series[col]
        m_pct = missing_pct[col]
        print(f"  {idx:<3} {col:<22} {dtype_str:<12} {m_count:<10} {m_pct:>6.2f}%")

    # 3. Target Distribution: Genuine vs Fraudulent
    print("\n[3/6] Target Variable Distribution ('fraudulent'):")
    fraud_counts = df["fraudulent"].value_counts().to_dict()
    genuine_count = fraud_counts.get(0, 0)
    fake_count = fraud_counts.get(1, 0)
    genuine_pct = (genuine_count / total_rows) * 100
    fake_pct = (fake_count / total_rows) * 100
    imbalance_ratio = genuine_count / fake_count if fake_count > 0 else 0

    print(f"  - Genuine / Legitimate (0): {genuine_count:,} ({genuine_pct:.2f}%)")
    print(f"  - Fraudulent / Scam    (1): {fake_count:,} ({fake_pct:.2f}%)")
    print(f"  - Class Imbalance Ratio:   ~{imbalance_ratio:.1f} : 1")

    # 4. India Location Analysis
    print("\n[4/6] Geographical Analysis (Focus on India):")
    # Extract 2-letter ISO country code from location (formatted like "US, NY, New York" or "IN, TN, Chennai")
    df["country"] = df["location"].str.split(",").str[0].str.strip()
    india_df = df[df["country"] == "IN"]
    india_total = len(india_df)

    if india_total > 0:
        india_fraud_counts = india_df["fraudulent"].value_counts().to_dict()
        india_genuine = india_fraud_counts.get(0, 0)
        india_fake = india_fraud_counts.get(1, 0)
        india_fake_pct = (india_fake / india_total) * 100
        india_genuine_pct = (india_genuine / india_total) * 100

        print(f"  - Total Indian Postings (country='IN'): {india_total} ({india_total / total_rows * 100:.2f}% of global data)")
        print(f"  - Genuine Postings in India:          {india_genuine} ({india_genuine_pct:.2f}%)")
        print(f"  - Fraudulent Postings in India:       {india_fake} ({india_fake_pct:.2f}%)")
        print(f"  - India Fraud Rate:                   {india_fake_pct:.2f}% (vs Global {fake_pct:.2f}%)")
    else:
        india_genuine, india_fake, india_fake_pct = 0, 0, 0.0
        print("  - No postings with ISO code 'IN' detected.")

    # 5. Most Common Locations and Job Titles
    print("\n[5/6] Most Common Locations & Job Titles:")
    print("\n  Top 10 Locations:")
    top_locations = df["location"].value_counts().head(10)
    for loc, count in top_locations.items():
        print(f"    - {loc:<30}: {count} postings")

    print("\n  Top 10 Countries:")
    top_countries = df["country"].value_counts().head(10)
    for ctry, count in top_countries.items():
        print(f"    - {ctry:<10}: {count} postings")

    print("\n  Top 10 Job Titles:")
    top_titles = df["title"].value_counts().head(10)
    for title, count in top_titles.items():
        print(f"    - {title:<35}: {count} postings")

    # 6. Generate Charts if Matplotlib is available
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if HAS_MATPLOTLIB:
        print("\n[6/6] Generating visualization plots...")
        try:
            # Chart 1: Class Distribution
            fig, ax = plt.subplots(figsize=(7, 4.5))
            bars = ax.bar(["Genuine (0)", "Fraudulent (1)"], [genuine_count, fake_count], color=["#10B981", "#EF4444"], width=0.5)
            ax.set_title("CareerShield AI — EMSCAD Class Distribution (Severe Imbalance)", fontsize=12, pad=12)
            ax.set_ylabel("Count of Postings")
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f"{height:,} ({height/total_rows*100:.1f}%)",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")
            plt.tight_layout()
            plt.savefig(PROCESSED_DIR / "class_distribution.png", dpi=200)
            plt.close()
            print(f"  - Saved: {PROCESSED_DIR / 'class_distribution.png'}")

            # Chart 2: Missing Values
            fig, ax = plt.subplots(figsize=(10, 5.5))
            missing_sorted = missing_pct[missing_pct > 0].sort_values(ascending=True)
            bars = ax.barh(missing_sorted.index, missing_sorted.values, color="#3B82F6")
            ax.set_title("Missing Value Percentage by Feature (>0% Missingness)", fontsize=12, pad=12)
            ax.set_xlabel("Missing Percentage (%)")
            for bar in bars:
                width = bar.get_width()
                ax.annotate(f"{width:.1f}%",
                            xy=(width, bar.get_y() + bar.get_height() / 2),
                            xytext=(4, 0), textcoords="offset points", ha="left", va="center", fontsize=9)
            plt.tight_layout()
            plt.savefig(PROCESSED_DIR / "missing_values.png", dpi=200)
            plt.close()
            print(f"  - Saved: {PROCESSED_DIR / 'missing_values.png'}")

            # Chart 3: India vs Global Fraud Rate
            fig, ax = plt.subplots(figsize=(7, 4.5))
            rates = [fake_pct, india_fake_pct]
            labels = ["Global EMSCAD (All 17,880)", f"India Postings (Total {india_total})"]
            bars = ax.bar(labels, rates, color=["#F59E0B", "#DC2626"], width=0.45)
            ax.set_title("Recruitment Scam Rate: India vs. Global Dataset", fontsize=12, pad=12)
            ax.set_ylabel("Scam Rate (%)")
            ax.set_ylim(0, max(rates) * 1.35)
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f"{height:.2f}%",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=11, fontweight="bold")
            plt.tight_layout()
            plt.savefig(PROCESSED_DIR / "india_vs_global_fraud.png", dpi=200)
            plt.close()
            print(f"  - Saved: {PROCESSED_DIR / 'india_vs_global_fraud.png'}")

        except Exception as exc:
            print(f"  [WARNING] Matplotlib chart generation failed: {exc}")
    else:
        print("\n[6/6] Matplotlib not detected. Skipping PNG generation (SVG charts created in processed/).")

    print("\n" + "=" * 78)
    print("EDA execution completed successfully!")
    print("=" * 78)


if __name__ == "__main__":
    run_eda()
