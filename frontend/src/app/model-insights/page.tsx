"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import {
  Cpu,
  ShieldCheck,
  AlertTriangle,
  ShieldAlert,
  Scale,
  RotateCcw,
  Search,
  Sliders,
  FileCode,
  TrendingUp,
  BarChart3,
} from "lucide-react";
import { getModelTransparency } from "@/lib/api";
import { ModelTransparencyResponse, RuleDefinition } from "@/lib/types";

export default function ModelInsightsPage() {
  const [data, setData] = useState<ModelTransparencyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const fetchTransparencyData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getModelTransparency();
      setData(res);
    } catch (err) {
      console.error("Failed to load model transparency specs:", err);
      let msg = "Could not connect to the model transparency service. If the server was idle, it may take a moment to wake up. Please retry shortly.";
      if (axios.isAxiosError(err)) {
        msg = err.response?.data?.detail || err.message || msg;
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransparencyData();
  }, []);

  const filterRules = (rules: RuleDefinition[]) => {
    if (selectedCategory === "ALL") return rules;
    return rules.filter((r) => r.category === selectedCategory);
  };

  return (
    <div className="relative min-h-screen py-10 px-4 sm:px-6 lg:px-8">
      {/* Background ambient lighting */}
      <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[500px] w-[850px] -translate-x-1/2 rounded-full bg-gradient-to-b from-shield-brightCyan/10 via-shield-blue/5 to-transparent blur-3xl" />

      <div className="mx-auto max-w-6xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-shield-cyan/30 bg-shield-cyan/10 px-3 py-1 text-xs font-semibold text-shield-brightCyan mb-2">
              <Scale className="h-3.5 w-3.5" />
              <span>Full Algorithmic Transparency</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Model Insights & Rules Architecture
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Honest architectural disclosure, heuristic rule specifications, scoring mechanics, and live trigger frequencies.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchTransparencyData}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-navy-700 bg-navy-900/80 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-navy-800 hover:text-white transition-all disabled:opacity-50"
              title="Refresh rule trigger stats"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Trigger Stats</span>
            </button>
            <Link
              href="/analyzer"
              className="inline-flex items-center gap-2 rounded-lg bg-shield-blue px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-shield-blue/20 hover:bg-blue-600 transition-all"
            >
              <Search className="h-3.5 w-3.5" />
              <span>Test Rules in Analyzer</span>
            </Link>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-8 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-rose-200">Unable to load transparency specifications</p>
              <p className="mt-0.5 text-xs text-rose-300/90">{error}</p>
            </div>
            <button
              onClick={fetchTransparencyData}
              className="rounded bg-rose-500/20 px-2.5 py-1 text-xs font-semibold text-rose-200 hover:bg-rose-500/30"
            >
              Retry
            </button>
          </div>
        )}

        {/* 1. Core Engine Architecture Banner */}
        <div className="rounded-xl border border-shield-cyan/30 bg-navy-900/80 p-6 shadow-xl backdrop-blur-sm mb-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-navy-800 pb-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-shield-cyan/20 border border-shield-cyan/40 text-shield-brightCyan">
                <Cpu className="h-6 w-6" />
              </div>
              <div>
                <span className="text-xs font-semibold text-shield-brightCyan uppercase tracking-wider">
                  Active Scoring Engine
                </span>
                <h2 className="text-xl font-bold text-white">
                  {data?.engine_type || "Hybrid Scoring Engine"}
                </h2>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <span className="font-mono text-[11px] text-shield-cyan bg-navy-950 px-2 py-0.5 rounded border border-navy-700">
                    Version: {data?.engine_version || "Active"}
                  </span>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    {data?.ml_model_status || "Baseline Active"}
                  </span>
                </div>
              </div>
            </div>
            <div className="inline-flex items-center gap-2 rounded-lg bg-navy-950/80 border border-navy-800 px-3.5 py-1.5 text-xs text-slate-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>{data?.total_rules_defined || 10} Rules Configured</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">
                {data ? `${data.total_evaluations_analyzed} Database Analyses` : "Loading..."}
              </span>
            </div>
          </div>

          <p className="text-sm text-slate-300 leading-relaxed mb-4">
            CareerShield AI operates a dual-layer hybrid architecture: deterministic heuristic safety rules act as the authoritative primary safeguard (specifically calibrated for Indian recruitment fraud, task scams, and upfront fees), while a supervised TF-IDF + Logistic Regression model provides a bounded advisory lift (+0 to +15 points) when suspicious lexical patterns are identified.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-3 rounded-lg border border-navy-800 bg-navy-950/60">
              <span className="font-semibold text-slate-200 block mb-0.5">Strict Rule Dominance</span>
              <span className="text-slate-400">Heuristic scores ≥ 65 dominate authoritative scoring; ML can never dilute or overturn confirmed fraud findings.</span>
            </div>
            <div className="p-3 rounded-lg border border-navy-800 bg-navy-950/60">
              <span className="font-semibold text-slate-200 block mb-0.5">Bounded Advisory Lift</span>
              <span className="text-slate-400">ML fraud probability ≥ 0.70 contributes up to +15 pts, strictly capped at 64.0 (cannot unilaterally trigger High Risk).</span>
            </div>
            <div className="p-3 rounded-lg border border-navy-800 bg-navy-950/60">
              <span className="font-semibold text-slate-200 block mb-0.5">Explainable Attributions</span>
              <span className="text-slate-400">Every penalty and lexical attribution is surfaced transparently with reason, text, and point impact.</span>
            </div>
          </div>
        </div>

        {/* 2. Machine Learning Baseline Evaluation & Transparency */}
        <div className="rounded-xl border border-purple-500/30 bg-purple-500/5 p-6 shadow-xl mb-8">
          <div className="flex items-start gap-3">
            <TrendingUp className="h-5 w-5 text-purple-400 shrink-0 mt-0.5" />
            <div className="w-full">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <h3 className="text-base font-bold text-purple-200">
                  Supervised ML Baseline Evaluation & Transparency
                </h3>
                {data?.ml_metrics_available && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/30">
                    <BarChart3 className="h-3 w-3" />
                    {data.benchmark_metrics?.dataset_name || "EMSCAD Held-Out Test Split (N=3,023)"}
                  </span>
                )}
              </div>

              {loading && !data && (
                <div className="h-24 rounded-lg bg-navy-950/50 animate-pulse my-3" />
              )}

              {data && data.ml_metrics_available ? (
                <>
                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                    The baseline machine learning model (TF-IDF + class-weighted Logistic Regression) was evaluated offline on a held-out test split (20% stratified test set, random_state=42, N={data.benchmark_metrics?.test_split_size?.toLocaleString() || "3,023"} records) of the benchmark EMSCAD dataset.
                  </p>

                  {/* 5 Key Metric KPI Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-4">
                    <div className="rounded-lg border border-navy-800 bg-navy-950/80 p-3 text-center">
                      <div className="text-[11px] text-slate-400 font-medium mb-1">ROC-AUC</div>
                      <div className="text-xl font-extrabold text-white">
                        {typeof data.benchmark_metrics?.roc_auc === "number"
                          ? data.benchmark_metrics.roc_auc.toFixed(4)
                          : "0.9628"}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">Overall discrimination</div>
                    </div>

                    <div className="rounded-lg border border-navy-800 bg-navy-950/80 p-3 text-center">
                      <div className="text-[11px] text-slate-400 font-medium mb-1">PR-AUC</div>
                      <div className="text-xl font-extrabold text-shield-brightCyan">
                        {typeof data.benchmark_metrics?.pr_auc === "number"
                          ? data.benchmark_metrics.pr_auc.toFixed(4)
                          : "0.7921"}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">Imbalanced fraud curve</div>
                    </div>

                    <div className="rounded-lg border border-navy-800 bg-navy-950/80 p-3 text-center">
                      <div className="text-[11px] text-slate-400 font-medium mb-1">Fraud Precision</div>
                      <div className="text-xl font-extrabold text-amber-300">
                        {typeof data.benchmark_metrics?.fraud_precision === "number"
                          ? `${data.benchmark_metrics.fraud_precision.toFixed(2)}%`
                          : "70.07%"}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">At optimal threshold</div>
                    </div>

                    <div className="rounded-lg border border-navy-800 bg-navy-950/80 p-3 text-center">
                      <div className="text-[11px] text-slate-400 font-medium mb-1">Fraud Recall</div>
                      <div className="text-xl font-extrabold text-emerald-400">
                        {typeof data.benchmark_metrics?.fraud_recall === "number"
                          ? `${data.benchmark_metrics.fraud_recall.toFixed(2)}%`
                          : "74.42%"}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">Detected fraudulent</div>
                    </div>

                    <div className="rounded-lg border border-navy-800 bg-navy-950/80 p-3 text-center col-span-2 sm:col-span-1">
                      <div className="text-[11px] text-slate-400 font-medium mb-1">Operating Threshold</div>
                      <div className="text-xl font-extrabold text-purple-300">
                        {typeof data.benchmark_metrics?.threshold === "number"
                          ? data.benchmark_metrics.threshold.toFixed(2)
                          : "0.61"}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">Cross-validation tuned</div>
                    </div>
                  </div>

                  {/* Narrative details */}
                  <div className="rounded-lg border border-navy-800 bg-navy-950/70 p-3 text-xs text-slate-300 leading-relaxed mb-3">
                    <strong className="text-purple-300 block mb-1">Evaluation Methodology & Baseline Provenance:</strong>
                    <span>{data.ml_metrics_explanation}</span>
                  </div>

                  {/* Explicit Domain Scope Notice */}
                  <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200/90 leading-relaxed flex items-start gap-2.5">
                    <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                    <span>
                      <strong>Important Domain & Real-World Caveat:</strong> {data.benchmark_metrics?.caveat ? `${data.benchmark_metrics.caveat} ` : ""}The EMSCAD benchmark dataset comprises historical international postings (2012–2014) with very few Indian recruitment records (276 total Indian postings; 4 fraudulent). Consequently, these offline benchmark metrics reflect historical text patterns and <strong>do not predict real-world Indian scam probabilities or live detection accuracy</strong>. Modern Indian job fraud (such as WhatsApp tasks, UPI verification fees, or refundable laptop deposits) is intercepted primarily through CareerShield&apos;s authoritative deterministic heuristic rules.
                    </span>
                  </div>
                </>
              ) : (
                <div className="rounded-lg border border-navy-800 bg-navy-950/70 p-3 text-xs text-slate-400 leading-relaxed">
                  <p>{data?.ml_metrics_explanation || "Machine learning evaluation metrics are currently unavailable."}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 3. Scoring Calibration & Bounds */}
        <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-xl mb-8">
          <div className="flex items-center justify-between mb-4 border-b border-navy-800 pb-3">
            <div>
              <h3 className="text-base font-semibold text-white">Scoring Formula & Classification Bands</h3>
              <p className="text-xs text-slate-400">Mathematical calibration and boundary enforcement</p>
            </div>
            <Sliders className="h-4 w-4 text-shield-cyan" />
          </div>

          <div className="rounded-lg border border-navy-800 bg-navy-950/60 p-4 mb-6">
            <div className="text-xs text-slate-400 mb-1 font-mono uppercase tracking-wider">Calibration Formula</div>
            <div className="font-mono text-xs sm:text-sm font-semibold text-shield-brightCyan leading-relaxed">
              {data?.score_calculation_formula ||
                "Final Risk Score = min(100.0, max(0.0, round(Raw Penalties - Mitigation Reductions, 1)))"}
            </div>
            <p className="text-xs text-slate-400 mt-2.5 leading-relaxed">
              Deterministic heuristic rules start at a baseline of 0. Additive penalties elevate risk when suspicious signals occur (up to +55 pts for upfront fee requests), while recognized corporate recruitment practices can reduce risk by up to 20 points. When heuristic risk is below 65.0, a high-confidence ML signal (P ≥ 0.70) adds a bounded advisory lift (up to +15 pts, strictly capped at 64.0). Output is strictly bounded between 0 and 100.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <span className="text-sm font-bold text-emerald-300">Low Risk (0 – 34)</span>
              </div>
              <p className="text-xs text-slate-400">
                Opportunities exhibit verified official corporate domains, multi-round interview structures, or recognized statutory benefits.
              </p>
            </div>

            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                <span className="text-sm font-bold text-amber-300">Needs Caution (35 – 64)</span>
              </div>
              <p className="text-xs text-slate-400">
                Unverified recruiter contact details, personal webmail handles, or elevated ML advisory signals warrant candidate diligence before applying.
              </p>
            </div>

            <div className="rounded-lg border border-rose-500/30 bg-rose-500/5 p-4">
              <div className="flex items-center gap-2 mb-1.5">
                <ShieldAlert className="h-4 w-4 text-rose-400" />
                <span className="text-sm font-bold text-rose-300">High Risk Indicators (65 – 100)</span>
              </div>
              <p className="text-xs text-slate-400">
                Critical scam indicators detected: mandatory registration/laptop fees, free email impersonation of top MNCs, or daily task payout schemes.
              </p>
            </div>
          </div>
        </div>

        {/* 4. Active Detection Rules Matrix */}
        <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-xl mb-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6 border-b border-navy-800 pb-4">
            <div>
              <h3 className="text-base font-semibold text-white">Active Heuristic Rule Catalog</h3>
              <p className="text-xs text-slate-400">
                Deterministic detection patterns and actual database trigger frequencies
              </p>
            </div>

            {/* Category Filter Pills */}
            <div className="flex flex-wrap gap-1.5 text-xs">
              {["ALL", "UPFRONT_FEE", "DOMAIN_SPOOFING", "CHANNEL_RISK", "SALARY_ANOMALY", "PRESSURE_TACTIC", "MISSING_INFO"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                    selectedCategory === cat
                      ? "bg-shield-blue text-white shadow"
                      : "bg-navy-950/70 text-slate-400 hover:text-slate-200 border border-navy-800"
                  }`}
                >
                  {cat.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          {loading && !data && (
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-28 rounded-lg border border-navy-800 bg-navy-950/50 animate-pulse" />
              ))}
            </div>
          )}

          {data && (
            <div className="space-y-4">
              {filterRules(data.rules).map((rule) => (
                <div
                  key={rule.rule_id}
                  className="rounded-xl border border-navy-800 bg-navy-950/60 p-4 transition-all hover:border-navy-700"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className="font-mono text-xs text-slate-400 font-semibold">{rule.rule_id}</span>
                      <h4 className="text-sm font-bold text-white">{rule.name}</h4>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          rule.severity === "CRITICAL"
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                            : rule.severity === "HIGH"
                            ? "bg-orange-500/10 text-orange-400 border-orange-500/30"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                        }`}
                      >
                        {rule.severity}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs font-bold text-rose-400 font-mono bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">
                        +{rule.risk_points} pts
                      </span>
                      <div className="text-right text-xs">
                        <span className="text-slate-400">Triggered: </span>
                        <span className="font-bold text-white">
                          {rule.historical_triggers_count} times
                        </span>
                        <span className="text-[10px] text-slate-500 ml-1">
                          ({rule.trigger_percentage}%)
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 mb-2 leading-relaxed">
                    {rule.description}
                  </p>

                  <div className="rounded-lg bg-navy-900/80 border border-navy-800/80 px-3 py-1.5 text-[11px] font-mono text-slate-400 flex items-center gap-2">
                    <FileCode className="h-3.5 w-3.5 text-shield-cyan shrink-0" />
                    <span className="truncate">Detection: {rule.detection_mechanism}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 5. Mitigating Legitimacy Signals */}
        <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-xl mb-8">
          <div className="flex items-center justify-between mb-4 border-b border-navy-800 pb-3">
            <div>
              <h3 className="text-base font-semibold text-white">Mitigating Legitimacy Signals</h3>
              <p className="text-xs text-slate-400">Signals that provide negative risk point contributions</p>
            </div>
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {data?.mitigating_signals.map((sig) => (
              <div key={sig.signal_id} className="rounded-lg border border-navy-800 bg-navy-950/60 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-emerald-400 font-mono">
                    -{sig.point_reduction} pts
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">{sig.signal_id}</span>
                </div>
                <h4 className="text-xs font-bold text-slate-200 mb-1">{sig.name}</h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-2">{sig.description}</p>
                <div className="text-[10px] text-slate-500 font-mono truncate">
                  Logic: {sig.detection_mechanism}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 6. Documented Limitations & Edge Cases */}
        <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-xl mb-8">
          <div className="flex items-center justify-between mb-4 border-b border-navy-800 pb-3">
            <div>
              <h3 className="text-base font-semibold text-white">System Limitations & Boundary Cases</h3>
              <p className="text-xs text-slate-400">Known behavioral boundaries of deterministic keyword detection</p>
            </div>
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          </div>

          <div className="space-y-2.5">
            {data?.limitations.map((lim, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed rounded-lg bg-navy-950/50 p-3 border border-navy-800/80"
              >
                <span className="font-mono text-amber-400 font-bold shrink-0">{idx + 1}.</span>
                <span>{lim}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
