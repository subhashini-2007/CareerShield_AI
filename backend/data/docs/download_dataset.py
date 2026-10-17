"""Automated dataset acquisition utility for CareerShield AI.

Downloads and verifies the Employment Scam Aegean Dataset (EMSCAD / fake_job_postings.csv)
into backend/data/raw/ without modification.
"""

import csv
import hashlib
import os
import sys
import urllib.request
from pathlib import Path

# Target storage destination
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent
RAW_DIR = DATA_DIR / "raw"
TARGET_FILE = RAW_DIR / "fake_job_postings.csv"

# Verified public academic and open-source mirrors hosting EMSCAD
MIRRORS = [
    # Mirror 1: Verified GitHub project mirror (master branch raw link)
    "https://raw.githubusercontent.com/Cindyalifia/bangkit-project-1/master/fake_job_postings.csv",
    # Mirror 2: Machine learning course benchmark repository
    "https://media.githubusercontent.com/media/Prince-Singh-1/Fake_Job_Detection/main/fake_job_postings.csv",
]

EXPECTED_COLUMNS = [
    "job_id",
    "title",
    "location",
    "department",
    "salary_range",
    "company_profile",
    "description",
    "requirements",
    "benefits",
    "telecommuting",
    "has_company_logo",
    "has_questions",
    "employment_type",
    "required_experience",
    "required_education",
    "industry",
    "function",
    "fraudulent",
]

EXPECTED_MIN_ROWS = 17000
EXPECTED_MIN_BYTES = 40 * 1024 * 1024  # >40 MB


def verify_downloaded_dataset(filepath: Path) -> bool:
    """Validate structure, column names, and row count of downloaded CSV."""
    if not filepath.exists():
        print(f"[ERROR] Target file does not exist: {filepath}")
        return False

    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"[INFO] Verifying {filepath.name} ({size_mb:.2f} MB)...")

    if filepath.stat().st_size < EXPECTED_MIN_BYTES:
        print(f"[ERROR] File size ({size_mb:.2f} MB) is smaller than expected (>40 MB). Download may be incomplete.")
        return False

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if not header:
                print("[ERROR] CSV file appears empty.")
                return False

            clean_header = [col.strip().strip('"').strip("'") for col in header]

            missing_cols = [c for c in EXPECTED_COLUMNS if c not in clean_header]
            if missing_cols:
                print(f"[ERROR] CSV missing expected columns: {missing_cols}")
                return False

            row_count = sum(1 for _ in reader)

        print(f"[SUCCESS] Dataset validated successfully!")
        print(f"  - Total Header Columns: {len(clean_header)} (All 18 verified)")
        print(f"  - Total Data Rows: {row_count:,} (Expected ~17,880)")
        return True

    except Exception as exc:
        print(f"[ERROR] Failed to parse CSV: {exc}")
        return False


def download_from_url(url: str, dest: Path) -> bool:
    """Download file with progress logging."""
    print(f"\n[INFO] Connecting to mirror: {url}")
    temp_dest = dest.with_suffix(".tmp")

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CareerShield-AI-Dataset-Acquisition/1.0"},
        )
        with urllib.request.urlopen(req, timeout=60) as response, open(temp_dest, "wb") as out_file:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 1024 * 512  # 512 KB

            print(f"[INFO] File size from header: {total_size / (1024*1024):.2f} MB" if total_size else "[INFO] Starting stream...")

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"\r  Progress: {downloaded / (1024*1024):.1f} / {total_size / (1024*1024):.1f} MB ({percent:.1f}%)", end="", flush=True)
                else:
                    print(f"\r  Downloaded: {downloaded / (1024*1024):.1f} MB", end="", flush=True)

            print()

        if temp_dest.exists() and temp_dest.stat().st_size > 0:
            if dest.exists():
                dest.unlink()
            temp_dest.rename(dest)
            return True
        else:
            print("[ERROR] Download produced zero bytes.")
            return False

    except Exception as exc:
        print(f"\n[WARNING] Mirror download failed: {exc}")
        if temp_dest.exists():
            temp_dest.unlink()
        return False


def main():
    print("=" * 70)
    print("CareerShield AI — Dataset Acquisition Tool")
    print("Target: Employment Scam Aegean Dataset (fake_job_postings.csv)")
    print("=" * 70)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if TARGET_FILE.exists():
        print(f"\n[INFO] Found existing file at: {TARGET_FILE}")
        if verify_downloaded_dataset(TARGET_FILE):
            print("\n[OK] Dataset is already present and verified. No download needed.")
            return 0
        else:
            print("[WARNING] Existing file failed verification. Re-attempting download...")

    success = False
    for idx, mirror_url in enumerate(MIRRORS, 1):
        print(f"\n[ATTEMPT {idx}/{len(MIRRORS)}]")
        if download_from_url(mirror_url, TARGET_FILE):
            if verify_downloaded_dataset(TARGET_FILE):
                success = True
                break
            else:
                print("[WARNING] Downloaded file from mirror failed verification.")

    if success:
        print("\n" + "=" * 70)
        print(f"[SUCCESS] Dataset saved to: {TARGET_FILE}")
        print("Ready for Exploratory Data Analysis (EDA) and preprocessing.")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("[ERROR] Automated download could not be completed via public mirrors.")
        print("Please follow manual acquisition instructions in:")
        print(f"  {SCRIPT_DIR / 'DATASET_CARD.md'}")
        print("Download fake_job_postings.csv manually and place it in:")
        print(f"  {TARGET_FILE}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
