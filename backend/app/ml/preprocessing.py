"""Preprocessing and text normalization utilities for CareerShield AI ML pipeline.

Provides text cleaning, feature combination, and deduplication to guarantee
zero data leakage across train and test partitions.
"""

import html
import re
from typing import List, Optional, Tuple
import pandas as pd


# Regex pattern to remove HTML tags
HTML_TAG_RE = re.compile(r"<[^>]+>")
# Whitespace normalization pattern
WHITESPACE_RE = re.compile(r"\s+")
# Common EMSCAD placeholder tokens
PLACEHOLDER_RE = re.compile(r"#(?:URL|EMAIL|PHONE)_[a-f0-9]+#")


def clean_text(raw_text: Optional[str]) -> str:
    """
    Clean and normalize raw job posting text.
    
    Steps:
    1. Null check and string conversion.
    2. HTML entity unescaping (e.g. &amp; -> &).
    3. HTML tag removal (<p>, <br>, <ul>, etc.).
    4. Masked placeholder token removal (#URL_...#, #EMAIL_...#).
    5. Lowercase normalization.
    6. Whitespace condensing.
    """
    if raw_text is None or pd.isna(raw_text):
        return ""

    text = str(raw_text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Strip HTML tags
    text = HTML_TAG_RE.sub(" ", text)
    # Remove masked URL / email / phone placeholders
    text = PLACEHOLDER_RE.sub(" ", text)
    # Lowercase
    text = text.lower()
    # Normalize whitespaces
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def combine_text_fields(
    df: pd.DataFrame,
    fields: Optional[List[str]] = None,
    clean: bool = True,
) -> pd.Series:
    """
    Combine multiple text columns from job posting DataFrame into a single unified text corpus.
    
    Default fields:
    - title
    - company_profile
    - description
    - requirements
    - benefits
    """
    if fields is None:
        fields = ["title", "company_profile", "description", "requirements", "benefits"]

    # Select only fields that actually exist in the dataframe
    valid_fields = [f for f in fields if f in df.columns]

    # Combine text with space separation
    combined = df[valid_fields[0]].fillna("").astype(str)
    for field in valid_fields[1:]:
        combined = combined + " " + df[field].fillna("").astype(str)

    if clean:
        combined = combined.apply(clean_text)

    return combined


def compute_text_fingerprint(row: pd.Series) -> str:
    """
    Compute a normalized composite fingerprint for duplicate detection.
    Combines normalized title and first 300 characters of description.
    """
    t = clean_text(row.get("title", ""))
    d = clean_text(row.get("description", ""))[:300]
    return f"{t}|||{d}"


def deduplicate_postings(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Deduplicate job postings to prevent train/test data leakage.
    
    Identifies postings sharing the exact same title and core description snippet,
    keeping the first occurrence and dropping re-posted duplicates.
    
    Returns:
        Tuple of (deduplicated_df, records_removed_count)
    """
    initial_count = len(df)
    
    # Compute fingerprint
    fingerprints = df.apply(compute_text_fingerprint, axis=1)
    
    # Identify non-duplicate indices
    mask_unique = ~fingerprints.duplicated(keep="first")
    deduped_df = df[mask_unique].copy().reset_index(drop=True)
    
    removed_count = initial_count - len(deduped_df)
    return deduped_df, removed_count
