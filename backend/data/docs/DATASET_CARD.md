# CareerShield AI — Dataset Card & Provenance Documentation

**Document Version:** 1.0  
**Last Updated:** October 13, 2026  
**Primary Dataset:** Employment Scam Aegean Dataset (EMSCAD)  
**Target Path:** `backend/data/raw/fake_job_postings.csv`

---

## 1. Overview & Dataset Identity

The primary benchmark dataset selected for CareerShield AI is the **Employment Scam Aegean Dataset (EMSCAD)**. Originally constructed and published by the Laboratory of Information & Communication Systems Security (Info-Sec-Lab) at the University of the Aegean in 2017, EMSCAD is the most widely recognized academic benchmark for evaluating automated detection of online recruitment fraud (ORF).

In modern data science repositories (such as Kaggle and GitHub), this dataset is distributed under the standard filename:
`fake_job_postings.csv`

---

## 2. Dataset Provenance & Academic Citation

- **Original Creators / Authors:** Sokratis Vidros, Constantinos Kolias, Georgios Kambourakis, and Leman Akoglu.
- **Affiliated Institution:** Department of Information and Communication Systems Engineering, University of the Aegean, Karlovassi, Samos, Greece.
- **Peer-Reviewed Publication:**  
  *Vidros, S., Kolias, C., Kambourakis, G., & Akoglu, L. (2017). Automatic Detection of Online Recruitment Frauds: Characteristics, Methods, and a Public Dataset. Future Internet, 9(1), 6.*  
  **DOI:** [10.3390/fi9010006](https://doi.org/10.3390/fi9010006)
- **Original Source Repository:** University of the Aegean Info-Sec-Lab (`http://emscad.samos.aegean.gr/`)
- **Primary Active Mirrors:**
  - Kaggle (Curated by Shivam Bansal): [Real or Fake Job Posting Prediction](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction)
  - Kaggle (EMSCAD Upload by Amruthjithraj V R): [Recruitment Scam (EMSCAD)](https://www.kaggle.com/datasets/amruthjithrajvr/recruitment-scam)

---

## 3. License & Usage Terms

- **Research Publication License:** The peer-reviewed research paper describing the dataset (*Future Internet* 2017, 9(1), 6) is published open-access under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.
- **Standalone Dataset Licensing Status (Unverified):** The standalone EMSCAD dataset hosted by the University of the Aegean Info-Sec-Lab was made available for public academic research and benchmarking without an explicit, standalone Creative Commons deed bundled in the data files. The standalone dataset's formal licensing terms have not been conclusively verified from primary-source documentation.
- **Third-Party Mirror Discrepancies:** Third-party distribution platforms display conflicting license information:
  - The Kaggle upload by Shivam Bansal (`shivamb/real-or-fake-fake-jobposting-prediction`) tags the dataset under **CC0: Public Domain**.
  - Alternative mirrors (such as `amruthjithrajvr/recruitment-scam`) classify the license as "Other" or unspecified.
  - CareerShield AI does not assert that the dataset is definitively CC0 or CC BY 4.0.
- **Usage & Attribution:** Consistent with academic research standards, the dataset is utilized strictly for educational and open-source fraud-detection benchmarking. Proper academic attribution should always cite the original publication by Vidros et al. (2017).

---

## 4. Dataset Dimensions & Class Distribution

| Attribute | Value |
|---|---|
| **Total Rows (Job Postings)** | **17,880** |
| **Total Columns (Features)** | **18** |
| **Legitimate Job Postings (`fraudulent = 0`)** | **17,014** (95.16%) |
| **Fraudulent Job Postings (`fraudulent = 1`)** | **866** (4.84%) |
| **Class Imbalance Ratio** | **~19.6 : 1** (Negative to Positive) |
| **Uncompressed CSV Size** | **~48.3 MB** |
| **Compressed (.zip) Size** | **~15.9 MB** |

> [!WARNING]
> **Severe Class Imbalance:**
> Because 95.16% of the postings are legitimate, a trivial dummy model predicting constant `0` achieves 95.16% accuracy while catching zero scams. Evaluation in Phase 4 must prioritize **Precision, Recall, F1-Score (Macro / Fraudulent Class), PR-AUC, and ROC-AUC**, never simple accuracy alone.

---

## 5. Schema & Data Dictionary

| # | Column Name | Data Type | Nullable? | Description & Context |
|---|---|---|---|---|
| 1 | `job_id` | Integer | No | Unique identifier for each posting (1 to 17,880). |
| 2 | `title` | String | No | Advertised position title (e.g., "Customer Service Representative", "DevOps Engineer"). |
| 3 | `location` | String | Yes | Geolocation formatted as ISO country, state, city (e.g., `US, NY, New York`). |
| 4 | `department` | String | Yes (~64.6% null) | Organizational unit (e.g., "Engineering", "Clerical"). |
| 5 | `salary_range` | String | Yes (~83.8% null) | Advertised compensation range (e.g., `50000-75000`). |
| 6 | `company_profile` | Text | Yes (~18.5% null) | Narrative overview of the hiring entity. Frequently blank or generic in fraudulent ads. |
| 7 | `description` | Text | No (1 row empty) | Core narrative describing day-to-day duties, mission, and scope. Primary NLP text feature. |
| 8 | `requirements` | Text | Yes (~15.1% null) | Skills, certifications, educational prerequisites. |
| 9 | `benefits` | Text | Yes (~40.3% null) | Health insurance, PF, pension, paid leave, perks. |
| 10 | `telecommuting` | Integer (0/1) | No | Binary flag: `1` if remote position allowed, `0` otherwise. |
| 11 | `has_company_logo`| Integer (0/1) | No | Binary flag: `1` if company logo was present, `0` otherwise. |
| 12 | `has_questions` | Integer (0/1) | No | Binary flag: `1` if screening questions were included in application. |
| 13 | `employment_type` | String | Yes (~19.4% null) | Full-time, Part-time, Contract, Temporary, Other. |
| 14 | `required_experience`| String | Yes (~39.4% null) | Entry level, Associate, Mid-Senior level, Executive, etc. |
| 15 | `required_education` | String | Yes (~44.9% null) | High School or equivalent, Bachelor's Degree, Master's, etc. |
| 16 | `industry` | String | Yes (~27.4% null) | Industry classification (e.g., "Information Technology and Services"). |
| 17 | `function` | String | Yes (~36.1% null) | Business function (e.g., "Engineering", "Sales", "Administrative"). |
| 18 | `fraudulent` | Integer (0/1) | No | **Target Label:** `0` = Legitimate Opportunity; `1` = Confirmed Fraudulent Scam. |

---

## 6. Target Label Semantics

- **`0` (Legitimate):** Genuine recruitment notices collected from verified employer accounts on the Workable recruitment platform between 2012 and 2014.
- **`1` (Fraudulent):** Verified recruitment scams identified and cross-checked against complaints, suspicious domain registrations, non-existent entity filings, or advance-fee employment frauds.

---

## 7. Known Limitations & Domain Boundary Considerations

When utilizing EMSCAD within CareerShield AI, the following structural limitations must be addressed during preprocessing and modeling:

1. **Temporal Horizon (2012–2014 Collection Period):**
   EMSCAD reflects recruitment fraud tactics from the early 2010s. Modern 2020s scam patterns prevalent in India—such as **Telegram channel tasks**, **WhatsApp daily-payout liking schemes**, **UPI security deposits**, and **lookalike corporate domain spoofing**—are underrepresented.  
   *Mitigation:* CareerShield AI uses a hybrid architecture where EMSCAD trains general lexical scam classification, while the deterministic Heuristic Rules Engine captures modern Indian fresher-specific vectors.
2. **Geographical Distribution:**
   The raw dataset is predominantly US, UK, and Western Europe oriented. Location strings primarily reflect Western cities (`US, CA, Los Angeles`, `GB, LND, London`).
3. **HTML Artifacts & Encoding Noise:**
   Many textual columns contain raw HTML fragments (`<p>`, `<ul>`, `&amp;`, `\r\n`), requiring parsing and normalization during cleaning.
4. **Missing Values:**
   Columns like `salary_range` and `department` have extremely high missingness (>60–80%) and cannot be treated as dense tabular features without dedicated missing-indicator encoding.

---

## 8. Directory Architecture

The dataset directory structure in CareerShield AI is organized as follows:

```
backend/data/
├── docs/
│   ├── DATASET_CARD.md          # This documentation
│   └── download_dataset.py      # Automated acquisition script
├── raw/
│   ├── .gitkeep                 # Preserves directory in git
│   └── fake_job_postings.csv    # Raw, unmodified dataset (gitignored)
└── processed/
    ├── .gitkeep                 # Preserves directory in git
    ├── train.csv                # Cleaned 80% training split (gitignored)
    └── test.csv                 # Cleaned 20% held-out test split (gitignored)
```

Both `backend/data/raw/*` and `backend/data/processed/*` are excluded in `.gitignore` to prevent committing ~50 MB binary datasets into source control.

---

## 9. Reproducible Acquisition Procedures

To obtain `fake_job_postings.csv` and place it in `backend/data/raw/`, use any of the three methods below:

### Method A: Automated Python Script (Recommended)

Run the dedicated helper script included in `backend/data/docs/`:

```powershell
# Open terminal in project directory
cd C:\Users\subha\OneDrive\Desktop\CareerShield_AI\backend
python data\docs\download_dataset.py
```

This script attempts to download the file directly from verified academic mirrors and verifies its SHA-256 integrity upon arrival.

### Method B: Kaggle CLI

If you have the `kaggle` CLI configured with an API token (`~/.kaggle/kaggle.json`):

```powershell
cd C:\Users\subha\OneDrive\Desktop\CareerShield_AI\backend\data\raw
kaggle datasets download -d shivamb/real-or-fake-fake-jobposting-prediction --unzip
```

Ensure the resulting file is named `fake_job_postings.csv` in `backend/data/raw/`.

### Method C: Manual Browser Download

1. Navigate to: [Kaggle Real or Fake Job Posting Prediction](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction)
2. Click **Download** (requires free Kaggle registration).
3. Extract the downloaded `archive.zip`.
4. Copy `fake_job_postings.csv` to:
   `C:\Users\subha\OneDrive\Desktop\CareerShield_AI\backend\data\raw\fake_job_postings.csv`

---

## 10. File Integrity Verification

Once downloaded, verify that the raw file matches expected dimensions:

- **Filename:** `fake_job_postings.csv`
- **Expected Line Count:** 17,881 lines (1 header + 17,880 rows)
- **Expected Columns:** 18
- **Expected Size:** ~48,318,000 bytes (±1% depending on line endings)
- **PowerShell Verification Command:**
  ```powershell
  Get-Item C:\Users\subha\OneDrive\Desktop\CareerShield_AI\backend\data\raw\fake_job_postings.csv | Select-Object Name, Length, LastWriteTime
  ```
