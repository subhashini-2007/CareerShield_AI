"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  ArrowRight,
  RotateCcw,
  CreditCard,
  Layers,
  Activity,
  Search,
  ExternalLink,
  Shield,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { getAnalyticsSummary } from "@/lib/api";
import { AnalyticsSummaryResponse, RiskLevel } from "@/lib/types";

interface CustomChartTooltipProps {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: number | string;
    color?: string;
    fill?: string;
    dataKey?: string;
    payload?: {
      percentage?: number;
      average_risk_score?: number;
      [key: string]: unknown;
    };
  }>;
  label?: string;
}

// Custom Dark Tooltip for Recharts
const CustomChartTooltip = ({ active, payload, label }: CustomChartTooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="rounded-lg border border-navy-700 bg-navy-950/95 p-3 shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-slate-200 mb-1">{label || data.name}</p>
        <div className="flex items-center gap-2">
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: data.color || data.fill || "#06B6D4" }}
          />
          <span className="text-slate-400">{data.dataKey || "Count"}:</span>
          <span className="font-bold text-white">{data.value}</span>
        </div>
        {data.payload?.percentage !== undefined && (
          <div className="text-slate-400 mt-1">
            Share: <span className="font-semibold text-shield-brightCyan">{data.payload.percentage}%</span>
          </div>
        )}
        {data.payload?.average_risk_score !== undefined && (
          <div className="text-slate-400 mt-0.5">
            Avg Risk Score: <span className="font-semibold text-rose-400">{data.payload.average_risk_score}/100</span>
          </div>
        )}
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const [data, setData] = useState<AnalyticsSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const fetchSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const summary = await getAnalyticsSummary();
      setData(summary);
    } catch (err) {
      console.error("Failed to load analytics summary:", err);
      let msg = "Could not connect to the CareerShield AI analytics service. If the server was idle, it may take a moment to wake up. Please refresh or retry.";
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
    setMounted(true);
    fetchSummary();
  }, []);

  const getRiskBadge = (level: RiskLevel) => {
    switch (level) {
      case "LOW_RISK":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="h-3 w-3" /> Low Risk
          </span>
        );
      case "NEEDS_CAUTION":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="h-3 w-3" /> Needs Caution
          </span>
        );
      case "HIGH_RISK_INDICATORS":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <ShieldAlert className="h-3 w-3" /> High Risk Indicators
          </span>
        );
    }
  };

  return (
    <div className="relative min-h-screen py-10 px-4 sm:px-6 lg:px-8">
      {/* Background ambient lighting */}
      <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[500px] w-[850px] -translate-x-1/2 rounded-full bg-gradient-to-b from-shield-blue/15 via-shield-cyan/5 to-transparent blur-3xl" />

      <div className="mx-auto max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-shield-cyan/30 bg-shield-cyan/10 px-3 py-1 text-xs font-semibold text-shield-brightCyan mb-2">
              <Activity className="h-3.5 w-3.5" />
              <span>Real-Time Database Intelligence</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Recruitment Risk Intelligence Dashboard
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Aggregated safety metrics and risk distribution patterns derived from stored job opportunity analyses.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchSummary}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-navy-700 bg-navy-900/80 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-navy-800 hover:text-white transition-all disabled:opacity-50"
              title="Refresh dashboard metrics"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Metrics</span>
            </button>
            <Link
              href="/analyzer"
              className="inline-flex items-center gap-2 rounded-lg bg-shield-blue px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-shield-blue/20 hover:bg-blue-600 transition-all"
            >
              <Search className="h-3.5 w-3.5" />
              <span>Analyze New Job</span>
            </Link>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-8 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-rose-200">Unable to load dashboard metrics</p>
              <p className="mt-0.5 text-xs text-rose-300/90">{error}</p>
            </div>
            <button
              onClick={fetchSummary}
              className="rounded bg-rose-500/20 px-2.5 py-1 text-xs font-semibold text-rose-200 hover:bg-rose-500/30"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && !data && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-32 rounded-xl border border-navy-800 bg-navy-900/50 p-5 animate-pulse"
              />
            ))}
          </div>
        )}

        {/* Empty State when no records exist */}
        {!loading && data && data.total_analyses === 0 && (
          <div className="rounded-2xl border border-navy-800 bg-navy-900/40 p-10 text-center shadow-xl mb-12">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-shield-cyan/15 border border-shield-cyan/30 text-shield-brightCyan mb-4 shadow-[0_0_20px_rgba(6,182,212,0.2)]">
              <BarChart3 className="h-8 w-8" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">No Job Opportunities Analyzed Yet</h2>
            <p className="text-sm text-slate-400 max-w-lg mx-auto mb-6 leading-relaxed">
              The CareerShield AI dashboard derives statistics strictly from verified database records.
              To populate live distribution charts and risk correlations, run an assessment or test our 1-click presets in the Risk Analyzer.
            </p>
            <div className="flex justify-center gap-4">
              <Link
                href="/analyzer"
                className="inline-flex items-center gap-2 rounded-lg bg-shield-blue px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-shield-blue/20 hover:bg-blue-600 transition-all hover:scale-[1.02]"
              >
                <Search className="h-4 w-4" />
                <span>Launch Risk Analyzer</span>
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>

            {/* Informative Preview of tracked dimensions */}
            <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4 text-left border-t border-navy-800/80 pt-8 max-w-3xl mx-auto">
              <div className="p-3 rounded-lg border border-navy-800/60 bg-navy-950/40">
                <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 mb-1">
                  <ShieldCheck className="h-3.5 w-3.5" /> Risk Proportions
                </span>
                <p className="text-xs text-slate-400">
                  Real-time segmentation into Low Risk, Needs Caution, and High Risk Indicators.
                </p>
              </div>
              <div className="p-3 rounded-lg border border-navy-800/60 bg-navy-950/40">
                <span className="text-xs font-semibold text-shield-brightCyan flex items-center gap-1.5 mb-1">
                  <Layers className="h-3.5 w-3.5" /> Channel Risk Profiles
                </span>
                <p className="text-xs text-slate-400">
                  Empirical risk scoring comparing Telegram, WhatsApp, Email, and Official Portals.
                </p>
              </div>
              <div className="p-3 rounded-lg border border-navy-800/60 bg-navy-950/40">
                <span className="text-xs font-semibold text-rose-400 flex items-center gap-1.5 mb-1">
                  <CreditCard className="h-3.5 w-3.5" /> Upfront Deposit Tracking
                </span>
                <p className="text-xs text-slate-400">
                  Proportion of recruitment listings attempting registration or laptop kit fees.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Populated Dashboard Content */}
        {data && data.total_analyses > 0 && (
          <>
            {/* 1. KPI Summary Cards */}
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
              {/* Card 1: Total Analyses */}
              <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-5 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Total Opportunities</span>
                  <Activity className="h-4 w-4 text-shield-cyan" />
                </div>
                <div className="text-3xl font-extrabold text-white">{data.total_analyses}</div>
                <div className="mt-2 flex items-center gap-1 text-xs text-slate-400">
                  <span>Persisted in local database audit</span>
                </div>
              </div>

              {/* Card 2: Average Risk Score */}
              <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-5 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Average Risk Index</span>
                  <TrendingUp className="h-4 w-4 text-shield-brightCyan" />
                </div>
                <div className="flex items-baseline gap-2">
                  <div className="text-3xl font-extrabold text-white">{data.average_risk_score}</div>
                  <span className="text-xs text-slate-400">/ 100</span>
                </div>
                <div className="mt-2 text-xs">
                  {data.average_risk_score <= 34 ? (
                    <span className="text-emerald-400 font-medium">Low Overall Risk Trend</span>
                  ) : data.average_risk_score <= 64 ? (
                    <span className="text-amber-400 font-medium">Moderate Risk Baseline</span>
                  ) : (
                    <span className="text-rose-400 font-medium">Elevated Scam Prevalence</span>
                  )}
                </div>
              </div>

              {/* Card 3: High Risk Indicators Rate */}
              <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-5 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">High Risk Share</span>
                  <ShieldAlert className="h-4 w-4 text-rose-400" />
                </div>
                <div className="flex items-baseline gap-2">
                  <div className="text-3xl font-extrabold text-rose-400">{data.high_risk_percentage}%</div>
                  <span className="text-xs text-slate-400">({data.high_risk_count} postings)</span>
                </div>
                <div className="mt-2 text-xs text-slate-400">
                  Severe recruitment scam signals
                </div>
              </div>

              {/* Card 4: Upfront Fee Demands */}
              <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-5 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider">Payment Requests</span>
                  <CreditCard className="h-4 w-4 text-amber-400" />
                </div>
                <div className="flex items-baseline gap-2">
                  <div className="text-3xl font-extrabold text-amber-400">{data.payment_demanded_percentage}%</div>
                  <span className="text-xs text-slate-400">({data.payment_demanded_count} demands)</span>
                </div>
                <div className="mt-2 text-xs text-slate-400">
                  Demanded registration or kit deposits
                </div>
              </div>
            </div>

            {/* 2. Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Chart A: Risk Category Distribution (Donut Pie) */}
              <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4 border-b border-navy-800 pb-3">
                  <div>
                    <h3 className="text-base font-semibold text-white">Risk Tier Distribution</h3>
                    <p className="text-xs text-slate-400">Proportion of opportunities by calibrated risk level</p>
                  </div>
                  <Shield className="h-4 w-4 text-shield-cyan" />
                </div>

                {mounted && (
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={data.risk_distribution}
                          dataKey="count"
                          nameKey="label"
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={85}
                          paddingAngle={4}
                        >
                          {data.risk_distribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomChartTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Legend with counts and percentages */}
                <div className="mt-4 grid grid-cols-3 gap-2 border-t border-navy-800/80 pt-4 text-center">
                  {data.risk_distribution.map((item) => (
                    <div key={item.category} className="p-2 rounded-lg bg-navy-950/50">
                      <div className="flex items-center justify-center gap-1.5 text-xs text-slate-400 mb-1">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
                        <span>{item.label}</span>
                      </div>
                      <div className="text-sm font-bold text-white">{item.count}</div>
                      <div className="text-[10px] text-slate-400">{item.percentage}%</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Chart B: Score Range Histogram */}
              <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4 border-b border-navy-800 pb-3">
                  <div>
                    <h3 className="text-base font-semibold text-white">Risk Score Distribution</h3>
                    <p className="text-xs text-slate-400">Count of opportunities across standardized risk intervals</p>
                  </div>
                  <BarChart3 className="h-4 w-4 text-shield-brightCyan" />
                </div>

                {mounted && (
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.score_ranges} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1C2541" vertical={false} />
                        <XAxis
                          dataKey="range_label"
                          stroke="#64748B"
                          tick={{ fill: "#94A3B8", fontSize: 10 }}
                          interval={0}
                          angle={-15}
                          textAnchor="end"
                        />
                        <YAxis stroke="#64748B" tick={{ fill: "#94A3B8", fontSize: 11 }} allowDecimals={false} />
                        <Tooltip content={<CustomChartTooltip />} />
                        <Bar dataKey="count" name="Postings" fill="#06B6D4" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <div className="mt-4 text-xs text-slate-400 text-center border-t border-navy-800/80 pt-3">
                  Scores 0–34 represent Low Risk; 35–64 represent Caution; 65–100 represent High Risk Indicators.
                </div>
              </div>
            </div>

            {/* 3. Secondary Analytics: Channel Risk & Top Warning Indicators */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Channel Risk Profile */}
              <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4 border-b border-navy-800 pb-3">
                  <div>
                    <h3 className="text-base font-semibold text-white">Channel Risk Profile</h3>
                    <p className="text-xs text-slate-400">Communication channels and observed average risk score</p>
                  </div>
                  <Layers className="h-4 w-4 text-shield-cyan" />
                </div>

                {data.channel_distribution.length === 0 ? (
                  <div className="py-12 text-center text-xs text-slate-500">
                    No channel breakdown available yet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {data.channel_distribution.map((ch) => (
                      <div
                        key={ch.channel}
                        className="rounded-lg border border-navy-800 bg-navy-950/50 p-3 flex items-center justify-between gap-4"
                      >
                        <div>
                          <div className="text-xs font-semibold text-slate-200">{ch.channel}</div>
                          <div className="text-[11px] text-slate-400">
                            {ch.count} postings ({ch.percentage}% of total)
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs font-bold text-slate-300">
                            Avg Score:{" "}
                            <span
                              className={
                                ch.average_risk_score >= 65
                                  ? "text-rose-400"
                                  : ch.average_risk_score >= 35
                                  ? "text-amber-400"
                                  : "text-emerald-400"
                              }
                            >
                              {ch.average_risk_score}/100
                            </span>
                          </div>
                          <div className="w-24 bg-navy-800 h-1.5 rounded-full overflow-hidden mt-1.5">
                            <div
                              className={`h-full rounded-full ${
                                ch.average_risk_score >= 65
                                  ? "bg-rose-500"
                                  : ch.average_risk_score >= 35
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(100, ch.average_risk_score)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Frequently Detected Warning Indicators */}
              <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-lg backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4 border-b border-navy-800 pb-3">
                  <div>
                    <h3 className="text-base font-semibold text-white">Most Detected Risk Indicators</h3>
                    <p className="text-xs text-slate-400">Heuristic categories triggered across stored analyses</p>
                  </div>
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                </div>

                {data.top_warning_indicators.length === 0 ? (
                  <div className="py-12 text-center text-xs text-slate-500">
                    No risk indicators flagged across current analyses.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {data.top_warning_indicators.slice(0, 5).map((w) => (
                      <div
                        key={w.category}
                        className="rounded-lg border border-navy-800 bg-navy-950/50 p-3 flex items-center justify-between gap-4"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                                w.severity === "CRITICAL"
                                  ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                                  : w.severity === "HIGH"
                                  ? "bg-orange-500/10 text-orange-400 border-orange-500/30"
                                  : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              }`}
                            >
                              {w.severity}
                            </span>
                            <span className="text-xs font-semibold text-slate-200 truncate">
                              {w.title}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 mt-1">
                            Category: {w.category}
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-xs font-bold text-white">{w.count} times</div>
                          <div className="text-[10px] text-slate-400">{w.percentage}% of all jobs</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 4. Recent Analysis Activity Stream */}
            <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 shadow-lg backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4 border-b border-navy-800 pb-3">
                <div>
                  <h3 className="text-base font-semibold text-white">Recent Analysis Activity</h3>
                  <p className="text-xs text-slate-400">Latest job opportunities evaluated (PII minimized)</p>
                </div>
                <Link
                  href="/history"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-shield-brightCyan hover:underline"
                >
                  <span>Full Audit History</span>
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </div>

              {data.recent_activity.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-500">
                  No recent activity recorded.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-navy-800 text-slate-400">
                        <th className="py-2.5 px-3 font-semibold">Job Title</th>
                        <th className="py-2.5 px-3 font-semibold">Company</th>
                        <th className="py-2.5 px-3 font-semibold">Channel</th>
                        <th className="py-2.5 px-3 font-semibold">Payment Demand</th>
                        <th className="py-2.5 px-3 font-semibold">Risk Score</th>
                        <th className="py-2.5 px-3 font-semibold">Risk Level</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-navy-800/60">
                      {data.recent_activity.map((item) => (
                        <tr key={item.id} className="hover:bg-navy-800/30 transition-colors">
                          <td className="py-3 px-3 font-medium text-slate-200">
                            {item.job_title}
                          </td>
                          <td className="py-3 px-3 text-slate-300">
                            {item.company_name}
                          </td>
                          <td className="py-3 px-3 text-slate-400">
                            {item.contact_channel}
                          </td>
                          <td className="py-3 px-3">
                            {item.requires_payment ? (
                              <span className="text-rose-400 font-semibold">
                                Yes ({item.payment_amount_claimed ? `₹${item.payment_amount_claimed}` : "Demanded"})
                              </span>
                            ) : (
                              <span className="text-slate-500">None</span>
                            )}
                          </td>
                          <td className="py-3 px-3 font-bold text-white">
                            {item.final_risk_score}/100
                          </td>
                          <td className="py-3 px-3">
                            {getRiskBadge(item.risk_level)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
