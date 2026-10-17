"""Heuristic safety and recruitment risk assessment engine for CareerShield AI.

Evaluates job postings, recruiter communications, fee requests, channel risks,
and domain patterns using an explainable, deterministic rules architecture.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Free webmail providers commonly used in impersonation scams
FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "yahoo.co.in",
    "outlook.com",
    "hotmail.com",
    "rediffmail.com",
    "aol.com",
    "protonmail.com",
    "mail.com",
    "zoho.com",
    "yandex.com",
}

# Major Indian tech employers and their official domains for spoofing checks
KNOWN_TECH_EMPLOYERS = {
    "tcs": {
        "canonical": "Tata Consultancy Services (TCS)",
        "aliases": ["tcs", "tata consultancy services", "tata consultancy"],
        "domains": ["tcs.com", "careers.tcs.com"],
        "portal": "https://www.tcs.com/careers",
        "advisory": "TCS never requests registration fees, training charges, or security deposits at any stage of hiring.",
    },
    "infosys": {
        "canonical": "Infosys",
        "aliases": ["infosys", "infosys limited", "infosys technologies"],
        "domains": ["infosys.com", "career.infosys.com"],
        "portal": "https://www.infosys.com/careers",
        "advisory": "Infosys conducts campus hiring exclusively via official portals and never demands monetary deposits.",
    },
    "wipro": {
        "canonical": "Wipro",
        "aliases": ["wipro", "wipro limited", "wipro enterprises"],
        "domains": ["wipro.com", "careers.wipro.com"],
        "portal": "https://careers.wipro.com",
        "advisory": "Wipro does not charge any application, processing, or training fees for candidates.",
    },
    "cognizant": {
        "canonical": "Cognizant Technology Solutions",
        "aliases": ["cognizant", "cts", "cognizant technology solutions"],
        "domains": ["cognizant.com"],
        "portal": "https://careers.cognizant.com",
        "advisory": "Cognizant never sends job offers via personal Gmail/WhatsApp accounts or asks for fee transfers.",
    },
    "accenture": {
        "canonical": "Accenture India",
        "aliases": ["accenture", "accenture india"],
        "domains": ["accenture.com"],
        "portal": "https://www.accenture.com/in-en/careers",
        "advisory": "Accenture does not solicit fees for interviews, training programs, or job placement.",
    },
    "hcl": {
        "canonical": "HCLTech",
        "aliases": ["hcl", "hcltech", "hcl technologies"],
        "domains": ["hcltech.com", "hcl.com"],
        "portal": "https://www.hcltech.com/careers",
        "advisory": "HCLTech candidates are evaluated through authorized HR communication from official company domains.",
    },
    "tech mahindra": {
        "canonical": "Tech Mahindra",
        "aliases": ["tech mahindra", "techmahindra"],
        "domains": ["techmahindra.com"],
        "portal": "https://careers.techmahindra.com",
        "advisory": "Tech Mahindra does not require security deposits or equipment courier payments.",
    },
    "google": {
        "canonical": "Google India",
        "aliases": ["google", "google india"],
        "domains": ["google.com"],
        "portal": "https://careers.google.com",
        "advisory": "Google does not recruit through informal WhatsApp or Telegram channels and never asks for application payments.",
    },
    "microsoft": {
        "canonical": "Microsoft India",
        "aliases": ["microsoft", "microsoft india"],
        "domains": ["microsoft.com"],
        "portal": "https://careers.microsoft.com",
        "advisory": "Microsoft never charges recruitment fees or training deposits.",
    },
    "amazon": {
        "canonical": "Amazon India",
        "aliases": ["amazon", "amazon india", "amazon jobs"],
        "domains": ["amazon.jobs", "amazon.com"],
        "portal": "https://www.amazon.jobs",
        "advisory": "Amazon does not charge any fee at any hiring stage and only communicates via official corporate email.",
    },
}

def map_score_to_risk_level(score: float) -> str:
    """Canonical mapping from numeric risk score to categorical risk band.

    Documented bands:
    - 0.0 to 34.0: LOW_RISK
    - 34.1 to 64.9 (< 65.0): NEEDS_CAUTION
    - 65.0 to 100.0: HIGH_RISK_INDICATORS
    """
    if score <= 34.0:
        return "LOW_RISK"
    elif score < 65.0:
        return "NEEDS_CAUTION"
    else:
        return "HIGH_RISK_INDICATORS"


def _extract_domain(url_or_email: Optional[str]) -> str:
    """Extract clean lowercase domain name from email address or URL string."""
    if not url_or_email:
        return ""
    text = str(url_or_email).strip().lower()
    if "@" in text:
        return text.split("@")[-1].strip()
    try:
        from urllib.parse import urlparse

        if not text.startswith(("http://", "https://")):
            text = "https://" + text
        parsed = urlparse(text)
        netloc = (parsed.netloc or "").strip().lower()
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def _domain_matches(domain: str, official_domains: List[str]) -> bool:
    """Check if domain exactly matches or is a valid subdomain of any authorized domain."""
    if not domain:
        return False
    clean_d = domain.strip().lower()
    for off in official_domains:
        off_clean = off.strip().lower()
        if clean_d == off_clean or clean_d.endswith("." + off_clean):
            return True
    return False


def _match_benchmark_employer(company_name: str, email_domain: str = "") -> Optional[Dict[str, Any]]:
    """
    Match company against KNOWN_TECH_EMPLOYERS corporate benchmark registry.
    Checks company name, aliases, canonical names, and authorized email domains.
    """
    comp_lower = company_name.strip().lower()

    # 1. Match by company name or aliases
    for key, benchmark in KNOWN_TECH_EMPLOYERS.items():
        aliases = benchmark.get("aliases", [key])
        canonical = benchmark["canonical"].lower()
        if (
            any(alias in comp_lower for alias in aliases)
            or key in comp_lower
            or comp_lower in canonical
            or canonical in comp_lower
        ):
            return benchmark

    # 2. If company name did not match an alias directly, check if email domain belongs to an authorized benchmark
    if email_domain:
        for key, benchmark in KNOWN_TECH_EMPLOYERS.items():
            if _domain_matches(email_domain, benchmark["domains"]):
                return benchmark

    return None


# Regex patterns for high-risk signals
FEE_PATTERNS = [
    (r"(?:registration|processing|application|portal|exam)\s+(?:fee|charge|cost|amount|payment)", "Mandatory application/registration fee request"),
    (r"(?:security|refundable)\s+(?:deposit|amount|caution\s+money)", "Refundable security deposit demand"),
    (r"(?:training|lms|kit|module)\s+(?:fee|charge|cost|payment)", "Upfront paid training or LMS module fee"),
    (r"(?:laptop|courier|device|equipment)\s+(?:deposit|charge|security|fee)", "Laptop or equipment courier deposit request"),
    (r"(?:pay|transfer|send|deposit)\s+(?:rs\.?|inr|₹)\s*\d+", "Explicit monetary payment amount mentioned in job description"),
    (r"(?:document\s+verification|police\s+clearance)\s+(?:charge|fee)", "Verification or document clearance fee requested"),
]

PRESSURE_PATTERNS = [
    (r"(?:immediate|spot|direct)\s+(?:joining|selection|offer|appointment)", "Guaranteed spot selection without assessment"),
    (r"(?:limited|few)\s+(?:seats|vacancies|openings)\s+(?:left|hurry|closing|available)", "Artificial scarcity or urgency pressure"),
    (r"(?:no\s+interview|without\s+(?:any\s+)?interview|direct\s+joining\s+letter)", "Hiring promised without interview or technical evaluation"),
    (r"(?:apply\s+today\s+only|offer\s+valid\s+till\s+today|urgent\s+requirement)", "High-urgency deadline pressure"),
]

TASK_SCAM_PATTERNS = [
    (r"(?:like|subscribe)\s+(?:youtube|instagram|telegram)\s+(?:videos?|channels?)", "Social media liking or rating task scheme"),
    (r"(?:typing|captcha)\s+(?:entry|work|job)\s+(?:from\s+home)?", "Part-time captcha/data typing bond scheme"),
    (r"(?:daily|weekly)\s+(?:payout|earning|income)\s+(?:of\s+)?(?:rs\.?|inr|₹)?\s*\d{3,}", "Unrealistic daily or task-based payout guarantee"),
    (r"(?:earn\s+(?:up\s+to\s+)?(?:rs\.?|inr|₹)?\s*\d{4,}\s+per\s+day)", "Exorbitant daily income promise for entry-level work"),
]

LEGITIMACY_PATTERNS = [
    (r"(?:coding|technical|aptitude)\s+(?:round|test|assessment|evaluation)", "Structured technical evaluation rounds"),
    (r"(?:rounds?\s+of\s+interview|panel\s+interview|hr\s+discussion)", "Standard multi-stage interview process"),
    (r"(?:background\s+verification|bcv|pre-employment\s+screening)", "Standard corporate background check protocol"),
    (r"(?:provident\s+fund|pf|gratuity|medical\s+insurance|health\s+insurance)", "Standard statutory employee benefits"),
]


class HeuristicRulesEngine:
    """Deterministic, explainable rule engine for job opportunity risk scoring."""

    def __init__(self):
        self.rules_version = "v1.0-rules-engine"

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comprehensive heuristic assessment on job opportunity attributes.
        Returns a dictionary with scores, indicators, evidence, and recommendations.
        """
        score = 0.0
        warnings: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []
        recommendations: List[str] = []

        job_title = data.get("job_title", "").strip()
        company_name = data.get("company_name", "").strip()
        recruiter_email = (data.get("recruiter_email") or "").strip().lower()
        contact_channel = (data.get("contact_channel") or "EMAIL").strip().upper()
        description = data.get("job_description", "").strip()
        requires_payment = bool(data.get("requires_payment", False))
        payment_amount = data.get("payment_amount_claimed")
        payment_reason = data.get("payment_reason") or ""
        application_url = (data.get("application_url") or "").strip()

        # ---------------------------------------------------------------------
        # 1. UPFRONT PAYMENT / DEPOSIT ANALYSIS (Heaviest Risk Factor)
        # ---------------------------------------------------------------------
        fee_detected = False

        if requires_payment:
            fee_detected = True
            amount_str = f"₹{payment_amount:,.2f}" if payment_amount else "an unspecified amount"
            reason_str = f" for '{payment_reason}'" if payment_reason else ""
            score += 55.0
            warnings.append({
                "id": f"warn-{uuid.uuid4().hex[:8]}",
                "category": "UPFRONT_FEE",
                "severity": "CRITICAL",
                "title": "Recruiter Demands Upfront Payment",
                "description": (
                    f"The recruiter explicitly requested {amount_str}{reason_str}. "
                    "Legitimate Indian companies, recruitment agencies, and campus placement drives NEVER charge candidates for job opportunities."
                ),
                "matched_text": f"Payment claimed: {amount_str} {reason_str}".strip(),
            })
            evidence.append({
                "id": f"evi-{uuid.uuid4().hex[:8]}",
                "text": f"User flagged payment demand: {amount_str} ({payment_reason or 'No reason provided'})",
                "attribution": "heuristic_rule",
                "impact_score": 55.0,
                "reason": "Direct upfront monetary demand is the #1 hallmark of employment fraud in India.",
            })
            recommendations.append(
                "STOP: Do not transfer any money via UPI, net banking, QR code, or payment gateway. Legitimate employers never charge candidates."
            )

        # Also search description text for fee keywords
        for pattern, explanation in FEE_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match and not fee_detected:
                fee_detected = True
                matched_phrase = match.group(0)
                score += 50.0
                warnings.append({
                    "id": f"warn-{uuid.uuid4().hex[:8]}",
                    "category": "UPFRONT_FEE",
                    "severity": "CRITICAL",
                    "title": "Job Text Mentions Upfront Payment or Deposit",
                    "description": f"The job description mentions '{matched_phrase}'. {explanation}.",
                    "matched_text": matched_phrase,
                })
                evidence.append({
                    "id": f"evi-{uuid.uuid4().hex[:8]}",
                    "text": matched_phrase,
                    "attribution": "heuristic_rule",
                    "impact_score": 50.0,
                    "reason": "Employment listings referencing registration fees or refundable deposits violate fair recruitment practices.",
                })
                recommendations.append(
                    "Clarify with the recruiter in writing whether any payment is required. If confirmed, decline the offer immediately."
                )
                break

        # ---------------------------------------------------------------------
        # 2. COMPANY IDENTITY & DOMAIN SPOOFING ASSESSMENT
        # ---------------------------------------------------------------------
        company_assessment, domain_score_delta, domain_warnings, domain_evidence = self._assess_company_and_domain(
            company_name, recruiter_email, application_url
        )
        score += domain_score_delta
        warnings.extend(domain_warnings)
        evidence.extend(domain_evidence)

        # ---------------------------------------------------------------------
        # 3. COMMUNICATION CHANNEL RISKS (Telegram / WhatsApp)
        # ---------------------------------------------------------------------
        if contact_channel == "TELEGRAM":
            score += 30.0
            warnings.append({
                "id": f"warn-{uuid.uuid4().hex[:8]}",
                "category": "CHANNEL_RISK",
                "severity": "HIGH",
                "title": "Recruitment Conducted via Telegram",
                "description": (
                    "The candidate is contacted primarily via Telegram. Legitimate corporate recruitment in India "
                    "uses verified company domains, official applicant tracking systems (ATS), or LinkedIn. "
                    "Telegram is frequently abused by task fraud networks due to untraceable handles."
                ),
                "matched_text": "Contact Channel: Telegram",
            })
            evidence.append({
                "id": f"evi-{uuid.uuid4().hex[:8]}",
                "text": "Channel: Telegram",
                "attribution": "heuristic_rule",
                "impact_score": 30.0,
                "reason": "Telegram lacks corporate verification and is the predominant vector for task scams in India.",
            })
            recommendations.append(
                "Never complete paid tasks, investment recharges, or share ID proofs (Aadhaar, PAN) over Telegram."
            )

        elif contact_channel == "WHATSAPP":
            # WhatsApp without verified corporate domain
            score += 20.0
            warnings.append({
                "id": f"warn-{uuid.uuid4().hex[:8]}",
                "category": "CHANNEL_RISK",
                "severity": "MEDIUM",
                "title": "Informal Hiring Communication via WhatsApp",
                "description": (
                    "Hiring discussions and job offers conducted solely over WhatsApp without an official application link "
                    "or corporate email address represent an elevated risk factor."
                ),
                "matched_text": "Contact Channel: WhatsApp",
            })
            evidence.append({
                "id": f"evi-{uuid.uuid4().hex[:8]}",
                "text": "Channel: WhatsApp",
                "attribution": "heuristic_rule",
                "impact_score": 20.0,
                "reason": "WhatsApp numbers are easily discarded or spoofed using virtual numbers.",
            })
            recommendations.append(
                "Request an official interview call invitation from an official company email address before proceeding."
            )

        # ---------------------------------------------------------------------
        # 4. TASK SCAMS & UNREALISTIC SALARY CLAIMS
        # ---------------------------------------------------------------------
        for pattern, explanation in TASK_SCAM_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0)
                score += 30.0
                warnings.append({
                    "id": f"warn-{uuid.uuid4().hex[:8]}",
                    "category": "SALARY_ANOMALY",
                    "severity": "HIGH",
                    "title": "Task-Based High-Return Work Scheme",
                    "description": f"The listing promises '{matched_phrase}'. {explanation}. These often start with small payouts to build trust before demanding a deposit.",
                    "matched_text": matched_phrase,
                })
                evidence.append({
                    "id": f"evi-{uuid.uuid4().hex[:8]}",
                    "text": matched_phrase,
                    "attribution": "heuristic_rule",
                    "impact_score": 30.0,
                    "reason": "Advertised daily payouts for simple social media or typing tasks match classic prepaid task frauds.",
                })
                recommendations.append(
                    "Be skeptical of schemes paying thousands of rupees daily for liking videos, rating hotels, or typing captchas."
                )
                break

        # ---------------------------------------------------------------------
        # 5. PRESSURE TACTICS & ZERO-INTERVIEW SELECTION
        # ---------------------------------------------------------------------
        for pattern, explanation in PRESSURE_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0)
                score += 20.0
                warnings.append({
                    "id": f"warn-{uuid.uuid4().hex[:8]}",
                    "category": "PRESSURE_TACTIC",
                    "severity": "MEDIUM",
                    "title": "Artificial Urgency or Guaranteed Selection",
                    "description": f"The posting uses pressure tactics: '{matched_phrase}'. {explanation}.",
                    "matched_text": matched_phrase,
                })
                evidence.append({
                    "id": f"evi-{uuid.uuid4().hex[:8]}",
                    "text": matched_phrase,
                    "attribution": "heuristic_rule",
                    "impact_score": 20.0,
                    "reason": "Artificial deadlines are designed to induce panic so freshers transfer money before doing due diligence.",
                })
                recommendations.append(
                    "Never let artificial deadlines rush you into paying money or signing unreviewed service agreements."
                )
                break

        # ---------------------------------------------------------------------
        # 6. MISSING VERIFIABLE COMPANY INFORMATION
        # ---------------------------------------------------------------------
        has_url = bool(application_url and application_url.startswith(("http://", "https://")))
        has_email = bool(recruiter_email and "@" in recruiter_email)

        if not has_url and not has_email:
            score += 15.0
            warnings.append({
                "id": f"warn-{uuid.uuid4().hex[:8]}",
                "category": "MISSING_INFO",
                "severity": "LOW",
                "title": "No Verifiable Company Contact Info Provided",
                "description": (
                    "Neither a corporate website link nor an official email address was provided with this posting. "
                    "Verify the employer on LinkedIn, Zauba Corp, or MCA (Ministry of Corporate Affairs) records."
                ),
                "matched_text": "Missing website and email",
            })
            recommendations.append(
                "Search the hiring entity on MCA.gov.in or LinkedIn to confirm the company actually exists and has an active office."
            )

        # ---------------------------------------------------------------------
        # 7. POSITIVE LEGITIMACY SIGNALS (Reduces Risk)
        # ---------------------------------------------------------------------
        legitimacy_points = 0.0
        for pattern, explanation in LEGITIMACY_PATTERNS:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0)
                legitimacy_points += 8.0
                evidence.append({
                    "id": f"evi-{uuid.uuid4().hex[:8]}",
                    "text": matched_phrase,
                    "attribution": "heuristic_rule",
                    "impact_score": -8.0,
                    "reason": f"Presence of standard recruitment practices ({explanation}) suggests professional hiring conduct.",
                })
                if legitimacy_points >= 20.0:
                    break

        score = max(0.0, score - legitimacy_points)

        # ---------------------------------------------------------------------
        # 8. FINAL SCORE CALIBRATION & CATEGORIZATION
        # ---------------------------------------------------------------------
        final_score = min(100.0, max(0.0, round(score, 1)))

        risk_level = map_score_to_risk_level(final_score)

        if risk_level == "LOW_RISK":
            if not recommendations:
                recommendations.append("The posting exhibits standard corporate hiring signals. Always verify interview details via official company portals.")
        elif risk_level == "NEEDS_CAUTION":
            recommendations.append("Exercise caution: Verify the recruiter's identity on LinkedIn and ensure no payments or deposits are ever made.")
        else:
            recommendations.append("CRITICAL: Strong indicators of employment risk detected. Do not share bank account details, Aadhaar, or transfer money.")

        # Always add standard safety recommendations for freshers
        recommendations.append("Never share sensitive personal IDs (Aadhaar front/back, bank passbooks) until receiving an official offer on an official corporate domain.")

        # Compute confidence based on input completeness
        confidence = self._compute_confidence(data)

        return {
            "ml_risk_score": 0.0,  # ML model is untrained in Phase 2
            "heuristic_risk_score": final_score,
            "final_risk_score": final_score,
            "risk_level": risk_level,
            "confidence_score": confidence,
            "warning_signs": warnings,
            "evidence_snippets": evidence,
            "recommendations": list(dict.fromkeys(recommendations)),  # Deduplicate while preserving order
            "company_assessment": company_assessment,
            "model_version": self.rules_version,
        }

    def _assess_company_and_domain(
        self, company_name: str, recruiter_email: str, application_url: str
    ) -> Tuple[Dict[str, Any], float, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Evaluate recruiter email domain and application URL against company name and known employer registry.
        """
        score_delta = 0.0
        warnings: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []

        email_domain = _extract_domain(recruiter_email) if recruiter_email and "@" in recruiter_email else ""
        url_domain = _extract_domain(application_url) if application_url else ""

        matched_benchmark = _match_benchmark_employer(company_name, email_domain)

        if matched_benchmark:
            # Case A: Claiming to be a major tech firm using a personal/free email provider
            if email_domain and email_domain in FREE_EMAIL_DOMAINS:
                score_delta += 40.0
                warnings.append({
                    "id": f"warn-{uuid.uuid4().hex[:8]}",
                    "category": "DOMAIN_SPOOFING",
                    "severity": "CRITICAL",
                    "title": f"Free Email Used to Impersonate {matched_benchmark['canonical']}",
                    "description": (
                        f"The recruiter uses a public free email domain (@{email_domain}) while claiming to hire for "
                        f"{matched_benchmark['canonical']}. Official HR recruiters from {matched_benchmark['canonical']} "
                        f"only communicate using verified company domains like @{matched_benchmark['domains'][0]}."
                    ),
                    "matched_text": f"Claimed: {company_name} | Contact: {recruiter_email}",
                })
                evidence.append({
                    "id": f"evi-{uuid.uuid4().hex[:8]}",
                    "text": f"{recruiter_email} for {matched_benchmark['canonical']}",
                    "attribution": "heuristic_rule",
                    "impact_score": 40.0,
                    "reason": f"Recruiters representing top MNCs never recruit candidates from personal {email_domain} accounts.",
                })
                return (
                    {
                        "domain_status": "personal_domain",
                        "is_known_firm": True,
                        "advisory_note": matched_benchmark["advisory"],
                        "verified_url": matched_benchmark["portal"],
                    },
                    score_delta,
                    warnings,
                    evidence,
                )

            # Case B: Matches official company domain
            # Verified when email domain matches official domains, or when no email is provided but official portal URL matches
            email_verified = bool(email_domain and _domain_matches(email_domain, matched_benchmark["domains"]))
            url_verified = bool(url_domain and _domain_matches(url_domain, matched_benchmark["domains"]))

            if email_verified or (not email_domain and url_verified):
                score_delta -= 15.0  # Legitimate corporate domain confirmed
                matched_source = f"@{email_domain}" if email_verified else url_domain
                evidence.append({
                    "id": f"evi-{uuid.uuid4().hex[:8]}",
                    "text": f"Verified official domain: {matched_source}",
                    "attribution": "heuristic_rule",
                    "impact_score": -15.0,
                    "reason": f"Domain matches official {matched_benchmark['canonical']} corporate registry.",
                })
                return (
                    {
                        "domain_status": "verified_match",
                        "is_known_firm": True,
                        "advisory_note": matched_benchmark["advisory"],
                        "verified_url": matched_benchmark["portal"],
                    },
                    score_delta,
                    warnings,
                    evidence,
                )

            # Case C: Recruiter supplied an unauthorized or lookalike email domain for known firm
            if email_domain:
                score_delta += 25.0
                warnings.append({
                    "id": f"warn-{uuid.uuid4().hex[:8]}",
                    "category": "DOMAIN_SPOOFING",
                    "severity": "HIGH",
                    "title": f"Unverified Email Domain for {matched_benchmark['canonical']}",
                    "description": (
                        f"The email domain (@{email_domain}) does not match the official domain "
                        f"(@{matched_benchmark['domains'][0]}) for {matched_benchmark['canonical']}."
                    ),
                    "matched_text": f"Claimed: {company_name} | Domain: @{email_domain}",
                })
                evidence.append({
                    "id": f"evi-{uuid.uuid4().hex[:8]}",
                    "text": f"Unmatched domain: @{email_domain}",
                    "attribution": "heuristic_rule",
                    "impact_score": 25.0,
                    "reason": f"Email domain does not belong to authorized domains for {matched_benchmark['canonical']}.",
                })
                return (
                    {
                        "domain_status": "unverified_domain",
                        "is_known_firm": True,
                        "advisory_note": matched_benchmark["advisory"],
                        "verified_url": matched_benchmark["portal"],
                    },
                    score_delta,
                    warnings,
                    evidence,
                )

            # Case D: Known firm claimed, but no email provided and unverified URL
            return (
                {
                    "domain_status": "missing" if not url_domain else "unverified_domain",
                    "is_known_firm": True,
                    "advisory_note": matched_benchmark["advisory"],
                    "verified_url": matched_benchmark["portal"],
                },
                score_delta,
                warnings,
                evidence,
            )

        # Non-benchmark general company checks
        if email_domain in FREE_EMAIL_DOMAINS:
            # Personal email for general company
            score_delta += 15.0
            warnings.append({
                "id": f"warn-{uuid.uuid4().hex[:8]}",
                "category": "DOMAIN_SPOOFING",
                "severity": "MEDIUM",
                "title": "Recruiter Using Personal Webmail Domain",
                "description": (
                    f"The recruiter is using a free public email provider (@{email_domain}) rather than an organization domain. "
                    "While small startups or individual consultants sometimes use personal emails, this warrants caution."
                ),
                "matched_text": f"Recruiter Email: {recruiter_email}",
            })
            evidence.append({
                "id": f"evi-{uuid.uuid4().hex[:8]}",
                "text": f"Personal webmail domain: @{email_domain}",
                "attribution": "heuristic_rule",
                "impact_score": 15.0,
                "reason": "Personal webmails lack corporate accountability and verifiable domain ownership.",
            })
            return (
                {
                    "domain_status": "personal_domain",
                    "is_known_firm": False,
                    "advisory_note": "Request confirmation from the company's official corporate contact address.",
                    "verified_url": None,
                },
                score_delta,
                warnings,
                evidence,
            )

        elif email_domain:
            return (
                {
                    "domain_status": "unverified_domain",
                    "is_known_firm": False,
                    "advisory_note": "Ensure the domain corresponds to an established registered business entity.",
                    "verified_url": None,
                },
                score_delta,
                warnings,
                evidence,
            )
        else:
            return (
                {
                    "domain_status": "missing",
                    "is_known_firm": False,
                    "advisory_note": "No recruiter email domain provided for verification.",
                    "verified_url": None,
                },
                score_delta,
                warnings,
                evidence,
            )


    def _compute_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score (0.0 to 1.0) based on input data completeness."""
        weight = 0.5  # Base confidence with job title & description
        desc_len = len(data.get("job_description", ""))
        if desc_len > 200:
            weight += 0.2
        elif desc_len > 80:
            weight += 0.1

        if data.get("recruiter_email"):
            weight += 0.15
        if data.get("application_url"):
            weight += 0.1
        if data.get("salary_offered"):
            weight += 0.05

        return min(0.98, round(weight, 2))


# Module singleton
_engine_instance = HeuristicRulesEngine()


def evaluate_job_risk(data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper functional interface to analyze job opportunities."""
    return _engine_instance.analyze(data)
