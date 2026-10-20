"use client";

import React, { useState } from "react";
import Link from "next/link";
import axios from "axios";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  RotateCcw,
  Sparkles,
  Search,
  ExternalLink,
  CheckCircle2,
  Building2,
  Mail,
  IndianRupee,
  HelpCircle,
  Send,
  Loader2,
  History,
  MapPin,
  Phone,
  Globe,
  Layers,
  Info,
} from "lucide-react";
import { analyzeJob } from "@/lib/api";
import { JobAnalysisRequest, JobAnalysisResponse, RiskLevel } from "@/lib/types";

// 1-Click Preset Demonstration Scenarios
const PRESET_SCENARIOS: { label: string; tag: string; data: JobAnalysisRequest }[] = [
  {
    label: "Legitimate Campus Placement",
    tag: "Low Risk",
    data: {
      job_title: "Graduate Engineer Trainee (GET)",
      company_name: "Tata Consultancy Services (TCS)",
      recruiter_email: "campus.recruitment@tcs.com",
      recruiter_phone: "",
      contact_channel: "OFFICIAL_PORTAL",
      salary_offered: "₹3,80,000",
      salary_frequency: "ANNUAL",
      location: "Pan India (Pune / Bangalore / Chennai)",
      application_url: "https://www.tcs.com/careers",
      requires_payment: false,
      payment_amount_claimed: 0,
      payment_reason: "",
      job_description:
        "TCS is inviting applications for Graduate Engineer Trainee across engineering streams. " +
        "Candidates will undergo an online National Qualifier Test (NQT) followed by technical assessment and panel interview. " +
        "Selected candidates will receive offer letters via TCS NextStep portal. Benefits include provident fund, gratuity, and medical insurance. " +
        "TCS never charges any application or training fees at any stage of the recruitment process.",
    },
  },
  {
    label: "Registration & Laptop Deposit Scam",
    tag: "High Risk",
    data: {
      job_title: "Associate Data Processing Executive",
      company_name: "QuickHire Global Infotech",
      recruiter_email: "quickhire.hr.team@gmail.com",
      recruiter_phone: "+91 98765 43210",
      contact_channel: "WHATSAPP",
      salary_offered: "₹45,000",
      salary_frequency: "MONTHLY",
      location: "Work from Home (Pan India)",
      application_url: "",
      requires_payment: true,
      payment_amount_claimed: 2500,
      payment_reason: "Refundable security deposit for work-from-home laptop and training kit",
      job_description:
        "Urgent vacancy for freshers! Direct joining letter issued today without any interview. " +
        "Selected candidates must pay Rs 2500 refundable security deposit for laptop courier dispatch and document verification kit. " +
        "Limited seats available, apply today only to book your spot. Transfer fee via UPI scanner to confirm appointment.",
    },
  },
  {
    label: "Telegram Paid Task Scheme",
    tag: "High Risk",
    data: {
      job_title: "Social Media Review Assistant",
      company_name: "Star Media Promotions",
      recruiter_email: "contact@t.me/starmedia_bot",
      recruiter_phone: "",
      contact_channel: "TELEGRAM",
      salary_offered: "₹3,000 - ₹5,000",
      salary_frequency: "DAILY",
      location: "Remote / Flexible",
      application_url: "",
      requires_payment: false,
      payment_amount_claimed: 0,
      payment_reason: "",
      job_description:
        "Simple part-time mobile job for college students. Like YouTube videos and subscribe to Telegram channels to earn up to Rs 5000 per day. " +
        "No resume or technical test needed. Instant daily payout to your UPI or Google Pay account after completing prepaid tasks.",
    },
  },
  {
    label: "Unverified Freelance Gig",
    tag: "Needs Caution",
    data: {
      job_title: "Junior Web Content Writer",
      company_name: "Digital Pulse Media",
      recruiter_email: "editor.digitalpulse@gmail.com",
      recruiter_phone: "",
      contact_channel: "EMAIL",
      salary_offered: "₹15,000",
      salary_frequency: "MONTHLY",
      location: "Remote",
      application_url: "",
      requires_payment: false,
      payment_amount_claimed: 0,
      payment_reason: "",
      job_description:
        "Looking for a fresher content writer to draft tech articles and blog summaries. " +
        "Submit 2 writing samples for evaluation. Work is remote on a 3-month contract basis. Stipend paid monthly.",
    },
  },
];

const INITIAL_FORM: JobAnalysisRequest = {
  job_title: "",
  company_name: "",
  recruiter_email: "",
  recruiter_phone: "",
  contact_channel: "EMAIL",
  salary_offered: "",
  salary_frequency: "ANNUAL",
  location: "",
  application_url: "",
  requires_payment: false,
  payment_amount_claimed: 0,
  payment_reason: "",
  job_description: "",
};

export default function AnalyzerPage() {
  const [formData, setFormData] = useState<JobAnalysisRequest>(INITIAL_FORM);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<JobAnalysisResponse | null>(null);

  // Field change handler
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    if (type === "checkbox") {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }

    // Clear validation error on change
    if (validationErrors[name]) {
      setValidationErrors((prev) => {
        const updated = { ...prev };
        delete updated[name];
        return updated;
      });
    }
  };

  // Load preset scenario
  const handleLoadPreset = (preset: typeof PRESET_SCENARIOS[0]) => {
    setFormData(preset.data);
    setValidationErrors({});
    setApiError(null);
    setResult(null);
  };

  // Reset form
  const handleReset = () => {
    setFormData(INITIAL_FORM);
    setValidationErrors({});
    setApiError(null);
    setResult(null);
  };

  // Client-side validation
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.job_title.trim()) {
      errors.job_title = "Job title is required.";
    } else if (formData.job_title.trim().length < 2) {
      errors.job_title = "Job title must be at least 2 characters.";
    }

    if (!formData.company_name.trim()) {
      errors.company_name = "Company name is required.";
    } else if (formData.company_name.trim().length < 2) {
      errors.company_name = "Company name must be at least 2 characters.";
    }

    if (!formData.job_description.trim()) {
      errors.job_description = "Job description or offer text is required.";
    } else if (formData.job_description.trim().length < 15) {
      errors.job_description = "Job description must be at least 15 characters to analyze patterns.";
    }

    if (formData.requires_payment) {
      if (
        formData.payment_amount_claimed !== undefined &&
        formData.payment_amount_claimed !== null &&
        Number(formData.payment_amount_claimed) < 0
      ) {
        errors.payment_amount_claimed = "Payment amount cannot be negative.";
      }
    }

    if (formData.recruiter_email && formData.recruiter_email.trim()) {
      const email = formData.recruiter_email.trim();
      if (!email.includes("@") && !email.includes(".me/")) {
        errors.recruiter_email = "Enter a valid email address or contact handle.";
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const payload: JobAnalysisRequest = {
        ...formData,
        payment_amount_claimed: formData.requires_payment
          ? Number(formData.payment_amount_claimed || 0)
          : undefined,
        payment_reason: formData.requires_payment
          ? formData.payment_reason || undefined
          : undefined,
      };

      const response = await analyzeJob(payload);
      setResult(response);
    } catch (err) {
      console.error("Analysis request failed:", err);
      let message = "Unable to connect to the CareerShield AI analysis service. If the backend was sleeping, it may take a few moments to spin up. Please try again.";
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.detail || err.message || message;
      } else if (err instanceof Error) {
        message = err.message;
      }
      setApiError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper for risk color scale
  const getRiskBadgeStyles = (level: RiskLevel) => {
    switch (level) {
      case "LOW_RISK":
        return {
          bg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
          icon: <ShieldCheck className="h-5 w-5 text-emerald-400" />,
          label: "Low Risk Opportunity",
          barColor: "bg-emerald-500",
        };
      case "NEEDS_CAUTION":
        return {
          bg: "bg-amber-500/10 border-amber-500/30 text-amber-400",
          icon: <AlertTriangle className="h-5 w-5 text-amber-400" />,
          label: "Needs Caution",
          barColor: "bg-amber-500",
        };
      case "HIGH_RISK_INDICATORS":
      default:
        return {
          bg: "bg-rose-500/10 border-rose-500/30 text-rose-400",
          icon: <ShieldAlert className="h-5 w-5 text-rose-400" />,
          label: "High Risk Indicators Detected",
          barColor: "bg-rose-500",
        };
    }
  };

  return (
    <div className="relative min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      {/* Background glow */}
      <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[450px] w-[800px] -translate-x-1/2 rounded-full bg-gradient-to-b from-shield-blue/15 to-transparent blur-3xl" />

      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-shield-cyan/30 bg-shield-cyan/10 px-3 py-1 text-xs font-semibold text-shield-brightCyan mb-4">
            <Sparkles className="h-3.5 w-3.5" />
            <span>AI Risk Assessment Engine — Heuristic Safety Protocol</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Job Opportunity Risk Analyzer
          </h1>
          <p className="mt-3 text-base text-slate-300 max-w-2xl mx-auto">
            Evaluate job descriptions, recruiter credentials, upfront fee demands, and communication patterns
            to identify predatory recruitment schemes before sharing sensitive documents.
          </p>
        </div>

        {/* 1-Click Preset Scenario Buttons */}
        <div className="mb-8 rounded-xl border border-navy-800 bg-navy-900/60 p-4 backdrop-blur-sm shadow-md">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Search className="h-3.5 w-3.5 text-shield-brightCyan" />
              Load Sample Scenarios (Indian Fresher Patterns):
            </span>
            <span className="text-xs text-slate-500">Click any preset to prefill form</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
            {PRESET_SCENARIOS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleLoadPreset(preset)}
                className="flex flex-col text-left p-2.5 rounded-lg border border-navy-700 bg-navy-950/80 hover:border-shield-cyan/50 hover:bg-navy-800/80 transition-all text-xs group"
              >
                <span className="font-semibold text-white group-hover:text-shield-brightCyan transition-colors">
                  {preset.label}
                </span>
                <span
                  className={`mt-1 inline-block text-[10px] font-medium px-1.5 py-0.5 rounded w-fit ${
                    preset.tag === "Low Risk"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                      : preset.tag === "Needs Caution"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                      : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                  }`}
                >
                  {preset.tag}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* API Error Banner */}
        {apiError && (
          <div className="mb-6 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-rose-300 flex items-start gap-3 shadow-lg">
            <AlertTriangle className="h-5 w-5 shrink-0 text-rose-400 mt-0.5" />
            <div className="flex-1 text-sm">
              <strong className="font-semibold block text-white mb-1">Backend Connection Error</strong>
              <span>{apiError}</span>
            </div>
            <button
              onClick={() => setApiError(null)}
              className="text-xs text-rose-400 hover:text-white underline ml-2"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Main Form & Results Grid */}
        <div className="grid grid-cols-1 gap-8">
          {/* Analysis Input Form */}
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-navy-800 bg-navy-900/80 p-6 sm:p-8 backdrop-blur-md shadow-xl"
          >
            <div className="border-b border-navy-800 pb-4 mb-6 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-shield-brightCyan" />
                <h2 className="text-lg font-bold text-white">Job Opportunity Details</h2>
              </div>
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Reset Form
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Job Title */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Job Title <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  name="job_title"
                  value={formData.job_title}
                  onChange={handleInputChange}
                  placeholder="e.g. Associate Software Engineer, Data Entry Intern"
                  className={`w-full rounded-lg border bg-navy-950 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors ${
                    validationErrors.job_title
                      ? "border-rose-500 focus:border-rose-400"
                      : "border-navy-700 focus:border-shield-cyan"
                  }`}
                />
                {validationErrors.job_title && (
                  <p className="mt-1 text-xs text-rose-400">{validationErrors.job_title}</p>
                )}
              </div>

              {/* Company Name */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Company Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleInputChange}
                  placeholder="e.g. Tata Consultancy Services, Acme Solutions"
                  className={`w-full rounded-lg border bg-navy-950 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors ${
                    validationErrors.company_name
                      ? "border-rose-500 focus:border-rose-400"
                      : "border-navy-700 focus:border-shield-cyan"
                  }`}
                />
                {validationErrors.company_name && (
                  <p className="mt-1 text-xs text-rose-400">{validationErrors.company_name}</p>
                )}
              </div>

              {/* Recruiter Email or Website */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Recruiter Email or Domain
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
                  <input
                    type="text"
                    name="recruiter_email"
                    value={formData.recruiter_email || ""}
                    onChange={handleInputChange}
                    placeholder="e.g. careers@company.com or recruiter@gmail.com"
                    className={`w-full rounded-lg border bg-navy-950 pl-9 pr-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors ${
                      validationErrors.recruiter_email
                        ? "border-rose-500 focus:border-rose-400"
                        : "border-navy-700 focus:border-shield-cyan"
                    }`}
                  />
                </div>
                {validationErrors.recruiter_email && (
                  <p className="mt-1 text-xs text-rose-400">{validationErrors.recruiter_email}</p>
                )}
              </div>

              {/* Communication Channel */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Application / Contact Channel
                </label>
                <select
                  name="contact_channel"
                  value={formData.contact_channel}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-navy-700 bg-navy-950 px-3.5 py-2.5 text-sm text-white focus:border-shield-cyan focus:outline-none transition-colors"
                >
                  <option value="EMAIL">Email (Corporate or Personal)</option>
                  <option value="OFFICIAL_PORTAL">Official Career Portal / ATS</option>
                  <option value="LINKEDIN">LinkedIn Job Post / Message</option>
                  <option value="WHATSAPP">WhatsApp Group / Recruiter</option>
                  <option value="TELEGRAM">Telegram Bot / Channel</option>
                  <option value="OTHER">Other / Job Board</option>
                </select>
              </div>

              {/* Advertised Salary */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Advertised Compensation
                </label>
                <div className="relative">
                  <IndianRupee className="absolute left-3 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
                  <input
                    type="text"
                    name="salary_offered"
                    value={formData.salary_offered || ""}
                    onChange={handleInputChange}
                    placeholder="e.g. ₹3,50,000 or ₹25,000/month"
                    className="w-full rounded-lg border border-navy-700 bg-navy-950 pl-9 pr-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-shield-cyan focus:outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Salary Frequency */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Compensation Frequency
                </label>
                <select
                  name="salary_frequency"
                  value={formData.salary_frequency || "ANNUAL"}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-navy-700 bg-navy-950 px-3.5 py-2.5 text-sm text-white focus:border-shield-cyan focus:outline-none transition-colors"
                >
                  <option value="ANNUAL">Annual (LPA)</option>
                  <option value="MONTHLY">Monthly</option>
                  <option value="DAILY">Daily</option>
                  <option value="PER_TASK">Per Task / Piece-rate</option>
                </select>
              </div>

              {/* Job Location */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Job Location / Work Mode
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
                  <input
                    type="text"
                    name="location"
                    value={formData.location || ""}
                    onChange={handleInputChange}
                    placeholder="e.g. Bangalore / Remote, Pune, Delhi NCR"
                    className="w-full rounded-lg border border-navy-700 bg-navy-950 pl-9 pr-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-shield-cyan focus:outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Recruiter Phone / WhatsApp */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Recruiter Phone / WhatsApp
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
                  <input
                    type="text"
                    name="recruiter_phone"
                    value={formData.recruiter_phone || ""}
                    onChange={handleInputChange}
                    placeholder="e.g. +91 98765 43210"
                    className="w-full rounded-lg border border-navy-700 bg-navy-950 pl-9 pr-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-shield-cyan focus:outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Application / Career URL */}
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Application Portal / Website URL
                </label>
                <div className="relative">
                  <Globe className="absolute left-3 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
                  <input
                    type="url"
                    name="application_url"
                    value={formData.application_url || ""}
                    onChange={handleInputChange}
                    placeholder="e.g. https://careers.company.com/job/12345"
                    className="w-full rounded-lg border border-navy-700 bg-navy-950 pl-9 pr-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-shield-cyan focus:outline-none transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* Upfront Payment Toggle Section */}
            <div className="mt-5 rounded-xl border border-navy-800 bg-navy-950/60 p-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  name="requires_payment"
                  checked={formData.requires_payment}
                  onChange={handleInputChange}
                  className="h-4 w-4 rounded border-navy-700 bg-navy-900 text-shield-cyan focus:ring-shield-cyan"
                />
                <span className="text-sm font-semibold text-white">
                  Did the recruiter or job post ask for ANY payment, fee, or deposit?
                </span>
              </label>

              {formData.requires_payment && (
                <div className="mt-4 pt-4 border-t border-navy-800 grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Demanded Amount (INR)
                    </label>
                    <input
                      type="number"
                      name="payment_amount_claimed"
                      value={formData.payment_amount_claimed || ""}
                      onChange={handleInputChange}
                      placeholder="e.g. 1500, 2500"
                      min="0"
                      className="w-full rounded-lg border border-navy-700 bg-navy-900 px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-shield-cyan focus:outline-none"
                    />
                    {validationErrors.payment_amount_claimed && (
                      <p className="mt-1 text-xs text-rose-400">
                        {validationErrors.payment_amount_claimed}
                      </p>
                    )}
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Stated Reason for Payment
                    </label>
                    <input
                      type="text"
                      name="payment_reason"
                      value={formData.payment_reason || ""}
                      onChange={handleInputChange}
                      placeholder="e.g. Training kit, registration, laptop courier deposit"
                      className="w-full rounded-lg border border-navy-700 bg-navy-900 px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-shield-cyan focus:outline-none"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Job Description / Offer Letter Text */}
            <div className="mt-5">
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Job Description / Offer Letter Text <span className="text-rose-400">*</span>
                </label>
                <span className="text-[11px] text-slate-500">
                  {formData.job_description.length} characters (min 15)
                </span>
              </div>
              <textarea
                name="job_description"
                rows={5}
                value={formData.job_description}
                onChange={handleInputChange}
                placeholder="Paste the job description, WhatsApp message, email offer letter, or recruitment advertisement text here..."
                className={`w-full rounded-lg border bg-navy-950 p-3.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors ${
                  validationErrors.job_description
                    ? "border-rose-500 focus:border-rose-400"
                    : "border-navy-700 focus:border-shield-cyan"
                }`}
              />
              {validationErrors.job_description && (
                <p className="mt-1 text-xs text-rose-400">{validationErrors.job_description}</p>
              )}
            </div>

            {/* Submit Action */}
            <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-navy-800">
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <HelpCircle className="h-4 w-4 text-shield-brightCyan shrink-0" />
                Assessment evaluates upfront fees, domain sanity, pressure tactics, and task patterns.
              </span>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-lg bg-shield-blue px-7 py-3 text-sm font-semibold text-white shadow-lg shadow-shield-blue/20 hover:bg-blue-600 disabled:opacity-60 transition-all hover:scale-[1.01]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Analyzing Indicators...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    <span>Run Risk Assessment</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Assessment Result Panel */}
          {result && (
            <div className="rounded-2xl border border-navy-800 bg-navy-900/90 p-6 sm:p-8 backdrop-blur-md shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-300">
              {/* Result Header & Score Gauge */}
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-navy-800">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                        getRiskBadgeStyles(result.risk_level).bg
                      }`}
                    >
                      {getRiskBadgeStyles(result.risk_level).icon}
                      {getRiskBadgeStyles(result.risk_level).label}
                    </span>
                    <span className="text-xs text-slate-500">
                      ID: {result.id.slice(0, 8)}...
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold text-white">
                    {result.job_title} at {result.company_name}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Evaluated via CareerShield {result.ml_risk_score > 0 ? "Hybrid Engine (Heuristic Rules + ML Baseline)" : "Heuristic Rules Engine"} ({result.model_version}) •{" "}
                    Confidence: {Math.round(result.confidence_score * 100)}%
                  </p>
                </div>

                {/* Score Dial / Visual Gauge */}
                <div className="flex items-center gap-4 bg-navy-950 p-4 rounded-xl border border-navy-800 w-full md:w-auto">
                  <div className="text-right">
                    <div className="text-xs text-slate-400 uppercase tracking-wider font-medium">
                      Risk Index
                    </div>
                    <div className="text-3xl font-extrabold text-white">
                      {result.final_risk_score}
                      <span className="text-base text-slate-500 font-normal"> / 100</span>
                    </div>
                  </div>
                  <div className="h-12 w-2 rounded-full bg-navy-800 overflow-hidden flex flex-col-reverse">
                    <div
                      className={`w-full ${getRiskBadgeStyles(result.risk_level).barColor}`}
                      style={{ height: `${result.final_risk_score}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Dual-Tier Score Decomposition */}
              <div className="my-5 grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="rounded-xl border border-navy-800 bg-navy-950/70 p-3 text-left">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    1. Authoritative Rules
                  </div>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-xl font-bold text-white font-mono">{result.heuristic_risk_score}</span>
                    <span className="text-xs text-slate-500">/ 100</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    Deterministic policy penalties
                  </div>
                </div>

                <div className="rounded-xl border border-navy-800 bg-navy-950/70 p-3 text-left">
                  <div className="text-[11px] font-semibold text-purple-300 uppercase tracking-wider">
                    2. ML Text Advisory
                  </div>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-xl font-bold text-purple-300 font-mono">{result.ml_risk_score}</span>
                    <span className="text-xs text-slate-500">/ 100</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    {result.ml_risk_score > 0
                      ? `TF-IDF text fraud probability: ${Math.round(result.ml_risk_score)}%`
                      : "No supplementary ML lift applied"}
                  </div>
                </div>

                <div className="rounded-xl border border-shield-cyan/30 bg-shield-cyan/5 p-3 text-left">
                  <div className="text-[11px] font-semibold text-shield-brightCyan uppercase tracking-wider">
                    3. Final Calibrated Score
                  </div>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-xl font-bold text-white font-mono">{result.final_risk_score}</span>
                    <span className="text-xs text-slate-500">/ 100</span>
                  </div>
                  <div className="text-[10px] text-shield-cyan mt-0.5">
                    {result.heuristic_risk_score >= 65.0
                      ? "Strict Rule Dominance (≥65)"
                      : result.final_risk_score > result.heuristic_risk_score
                      ? `Rule score + bounded ML lift (+${(result.final_risk_score - result.heuristic_risk_score).toFixed(1)})`
                      : "Authoritative heuristic baseline"}
                  </div>
                </div>
              </div>

              {/* Evaluated Opportunity & Recruiter Contact Details */}
              {(result.location || result.recruiter_phone || result.application_url || result.salary_offered || result.requires_payment) && (
                <div className="mb-5 rounded-xl border border-navy-800 bg-navy-950/60 p-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-2">
                    <Search className="h-4 w-4 text-shield-cyan" />
                    Evaluated Opportunity & Recruiter Contact Details
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                    {result.location && (
                      <div className="flex items-center gap-2">
                        <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span className="text-slate-300 truncate" title={result.location}>
                          {result.location}
                        </span>
                      </div>
                    )}
                    {result.recruiter_phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span className="text-slate-300 font-mono">
                          {result.recruiter_phone}
                        </span>
                      </div>
                    )}
                    {result.application_url && (
                      <div className="flex items-center gap-2 truncate">
                        <Globe className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <a
                          href={result.application_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-shield-brightCyan hover:underline truncate inline-flex items-center gap-1"
                        >
                          <span>{result.application_url.replace(/^https?:\/\//, "")}</span>
                          <ExternalLink className="h-2.5 w-2.5 shrink-0" />
                        </a>
                      </div>
                    )}
                    {result.salary_offered && (
                      <div className="flex items-center gap-2">
                        <IndianRupee className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span className="text-slate-300">
                          {result.salary_offered} ({result.salary_frequency?.toLowerCase() || "annual"})
                        </span>
                      </div>
                    )}
                  </div>
                  {result.requires_payment && (
                    <div className="mt-3 pt-2.5 border-t border-navy-800/80 flex items-center gap-2 text-xs text-rose-300">
                      <ShieldAlert className="h-4 w-4 text-rose-400 shrink-0" />
                      <span>
                        <strong>Payment Demanded:</strong> ₹{result.payment_amount_claimed?.toLocaleString() ?? 0} &bull; Stated Reason: &ldquo;{result.payment_reason || "Unspecified"}&rdquo;
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Advisory Disclaimer Notice */}
              <div className="my-5 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3.5 text-xs text-amber-300 flex items-start gap-2.5">
                <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Advisory Disclaimer:</strong> {result.disclaimer} This assessment highlights detected patterns
                  and risk signals to guide student due diligence. A high score indicates caution and verification are needed;
                  always cross-verify offers on official portals before sharing personal data.
                </span>
              </div>

              {/* Company & Domain Sanity Card */}
              {result.company_assessment && (
                <div className="mb-6 rounded-xl border border-navy-800 bg-navy-950/70 p-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-shield-cyan" />
                    Company & Recruiter Verification
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-400">Employer Status: </span>
                      <span className="text-white font-medium">
                        {result.company_assessment.is_known_firm
                          ? "Matches Known Enterprise Registry"
                          : "General Entity (Unverified Registry)"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400">Email Domain Check: </span>
                      <span
                        className={`font-medium ${
                          result.company_assessment.domain_status === "verified_match"
                            ? "text-emerald-400"
                            : result.company_assessment.domain_status === "personal_domain"
                            ? "text-rose-400"
                            : "text-amber-400"
                        }`}
                      >
                        {result.company_assessment.domain_status === "verified_match"
                          ? "Official Corporate Domain Verified"
                          : result.company_assessment.domain_status === "personal_domain"
                          ? "Personal Webmail (@gmail, @yahoo) Detected"
                          : "Unverified Domain"}
                      </span>
                    </div>
                  </div>
                  {result.company_assessment.advisory_note && (
                    <p className="mt-2 text-xs text-slate-300 border-t border-navy-800/80 pt-2">
                      <strong>Policy Note:</strong> {result.company_assessment.advisory_note}
                    </p>
                  )}
                </div>
              )}

              {/* Detected Warning Indicators */}
              <div className="mb-6">
                <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-rose-400" />
                  Detected Risk Indicators ({result.warning_signs.length})
                </h4>
                {result.warning_signs.length === 0 ? (
                  <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs text-emerald-300 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>No critical predatory patterns (upfront fees, task scams, domain spoofing) were detected in this posting.</span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {result.warning_signs.map((warning, wIdx) => (
                      <div
                        key={wIdx}
                        className={`rounded-xl border p-4 text-xs ${
                          warning.severity === "CRITICAL"
                            ? "border-rose-500/30 bg-rose-500/5 text-rose-200"
                            : warning.severity === "HIGH"
                            ? "border-orange-500/30 bg-orange-500/5 text-orange-200"
                            : "border-amber-500/30 bg-amber-500/5 text-amber-200"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-bold text-white text-sm">
                            {warning.title}
                          </span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                              warning.severity === "CRITICAL"
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                : warning.severity === "HIGH"
                                ? "bg-orange-500/20 text-orange-300 border border-orange-500/40"
                                : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                            }`}
                          >
                            {warning.severity}
                          </span>
                        </div>
                        <p className="text-slate-300 leading-relaxed mb-2">
                          {warning.description}
                        </p>
                        {warning.matched_text && (
                          <div className="rounded bg-navy-950/80 px-2.5 py-1 text-[11px] font-mono text-slate-300 border border-navy-800">
                            <strong>Matched Phrase:</strong> &ldquo;{warning.matched_text}&rdquo;
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Audit Evidence & Signal Attributions */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <Layers className="h-4 w-4 text-shield-cyan" />
                    Audit Evidence & Signal Attributions ({result.evidence_snippets?.length || 0})
                  </h4>
                  <span className="text-[11px] text-slate-500">
                    Deterministic Rules & Advisory ML Signals
                  </span>
                </div>

                {!result.evidence_snippets || result.evidence_snippets.length === 0 ? (
                  <div className="rounded-lg border border-navy-800 bg-navy-950/60 p-4 text-xs text-slate-400">
                    No specific textual evidence snippets or ML lexical feature attributions were extracted for this posting.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {result.evidence_snippets.map((snippet, sIdx) => {
                      const isHeuristic = snippet.attribution === "heuristic_rule";
                      return (
                        <div
                          key={snippet.id || sIdx}
                          className={`rounded-xl border p-4 text-xs transition-colors ${
                            isHeuristic
                              ? "border-sky-500/30 bg-sky-500/5 text-slate-200"
                              : "border-purple-500/30 bg-purple-500/5 text-slate-200"
                          }`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                                  isHeuristic
                                    ? "bg-sky-500/20 text-sky-300 border-sky-500/40"
                                    : "bg-purple-500/20 text-purple-300 border-purple-500/40"
                                }`}
                              >
                                {isHeuristic
                                  ? "Deterministic Rule Evidence"
                                  : "Supplementary ML Feature Attribution"}
                              </span>
                              <span className="text-[10px] font-mono text-slate-500">
                                ID: {snippet.id}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="text-slate-400 text-[11px]">Signal Impact:</span>
                              <span
                                className={`font-mono text-xs font-bold px-2 py-0.5 rounded border ${
                                  snippet.impact_score > 0
                                    ? isHeuristic
                                      ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                                      : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                                    : snippet.impact_score < 0
                                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                    : "bg-navy-900 text-slate-400 border-navy-700"
                                }`}
                              >
                                {snippet.impact_score > 0
                                  ? `+${snippet.impact_score} pts`
                                  : snippet.impact_score < 0
                                  ? `-${Math.abs(snippet.impact_score)} pts`
                                  : "0 pts"}
                              </span>
                            </div>
                          </div>

                          <p className="text-slate-300 leading-relaxed mb-2 font-medium">
                            {snippet.reason}
                          </p>

                          {snippet.text && (
                            <div className="rounded bg-navy-950/80 px-3 py-2 text-[11px] font-mono text-slate-300 border border-navy-800">
                              <span className="text-slate-500 uppercase tracking-wider text-[10px] block mb-0.5 font-sans">
                                Extracted Evidence Text:
                              </span>
                              &ldquo;{snippet.text}&rdquo;
                            </div>
                          )}

                          {!isHeuristic && (
                            <div className="mt-2.5 flex items-start gap-1.5 text-[10px] text-purple-300/80 bg-purple-950/30 rounded p-2.5 border border-purple-800/30">
                              <Info className="h-3.5 w-3.5 shrink-0 mt-0.5 text-purple-400" />
                              <span className="leading-relaxed">
                                <strong>Advisory Signal Notice:</strong> Statistical lexical feature correlations reflect vocabulary patterns
                                from historical baseline training data. They provide a supplementary advisory lift and do not constitute
                                proof of fraud.
                              </span>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Actionable Fresher Next Steps Checklist */}
              <div className="rounded-xl border border-navy-800 bg-navy-950/60 p-5 mb-6">
                <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-shield-cyan" />
                  Recommended Action Steps for Freshers
                </h4>
                <ul className="space-y-2 text-xs text-slate-300">
                  {result.recommendations.map((rec, rIdx) => (
                    <li key={rIdx} className="flex items-start gap-2.5">
                      <span className="h-5 w-5 rounded-full bg-navy-800 text-shield-brightCyan flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                        {rIdx + 1}
                      </span>
                      <span className="leading-relaxed">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Footer Actions */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-navy-800">
                <button
                  type="button"
                  onClick={handleReset}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-lg border border-navy-700 bg-navy-950 px-5 py-2.5 text-xs font-semibold text-slate-300 hover:text-white hover:bg-navy-800 transition-colors"
                >
                  <RotateCcw className="h-3.5 w-3.5" /> Analyze Another Job
                </button>

                <Link
                  href="/history"
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-lg bg-shield-cyan/15 border border-shield-cyan/30 px-5 py-2.5 text-xs font-semibold text-shield-brightCyan hover:bg-shield-cyan/25 transition-colors"
                >
                  <History className="h-3.5 w-3.5" /> View in Audit History
                  <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
