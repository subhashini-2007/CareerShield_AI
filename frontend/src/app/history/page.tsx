"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import {
  History,
  Search,
  Filter,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Building2,
  ExternalLink,
  ChevronRight,
  X,
  Loader2,
  Layers,
  MapPin,
  Phone,
  Globe,
  Mail,
  IndianRupee,
} from "lucide-react";
import { getAnalyses } from "@/lib/api";
import { JobAnalysisResponse, PaginatedAnalysesResponse, RiskLevel } from "@/lib/types";

export default function HistoryPage() {
  const [data, setData] = useState<PaginatedAnalysesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [selectedRisk, setSelectedRisk] = useState<string>("ALL");
  const [page, setPage] = useState(1);
  const [selectedItem, setSelectedItem] = useState<JobAnalysisResponse | null>(null);

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAnalyses({
        page,
        page_size: 10,
        risk_level: selectedRisk === "ALL" ? undefined : selectedRisk,
        search: activeSearch || undefined,
      });
      setData(res);
    } catch (err) {
      console.error("Failed to fetch analysis history:", err);
      let msg = "Could not connect to the analysis history service. If the server was idle, it may take a moment to wake up. Please retry shortly.";
      if (axios.isAxiosError(err)) {
        msg = err.response?.data?.detail || err.message || msg;
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [page, selectedRisk, activeSearch]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setActiveSearch(searchTerm.trim());
  };

  const getRiskBadge = (level: RiskLevel) => {
    switch (level) {
      case "LOW_RISK":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="h-3.5 w-3.5" /> Low Risk
          </span>
        );
      case "NEEDS_CAUTION":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="h-3.5 w-3.5" /> Needs Caution
          </span>
        );
      case "HIGH_RISK_INDICATORS":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <ShieldAlert className="h-3.5 w-3.5" /> High Risk Indicators
          </span>
        );
    }
  };

  return (
    <div className="relative min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      {/* Background glow */}
      <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[450px] w-[800px] -translate-x-1/2 rounded-full bg-gradient-to-b from-purple-500/10 to-transparent blur-3xl" />

      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-semibold text-purple-300 mb-2">
              <History className="h-3.5 w-3.5" />
              <span>Persistent Audit Trail</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
              Job Opportunity Analysis History
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Search and review past risk evaluations, detected fee requests, and actionable recommendations.
            </p>
          </div>

          <Link
            href="/analyzer"
            className="inline-flex items-center gap-2 rounded-lg bg-shield-blue px-4 py-2.5 text-xs font-semibold text-white shadow-md hover:bg-blue-600 transition-colors"
          >
            <Search className="h-4 w-4" /> Analyze New Opportunity
          </Link>
        </div>

        {/* Search and Filters Card */}
        <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-4 mb-6 backdrop-blur-sm">
          <form
            onSubmit={handleSearchSubmit}
            className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3"
          >
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by company name or job title..."
                className="w-full rounded-lg border border-navy-700 bg-navy-950 pl-9 pr-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-shield-cyan focus:outline-none"
              />
            </div>

            {/* Risk Tier Filter */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-500 shrink-0" />
              <select
                value={selectedRisk}
                onChange={(e) => {
                  setSelectedRisk(e.target.value);
                  setPage(1);
                }}
                className="rounded-lg border border-navy-700 bg-navy-950 px-3 py-2 text-xs text-white focus:border-shield-cyan focus:outline-none"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="LOW_RISK">Low Risk Only</option>
                <option value="NEEDS_CAUTION">Needs Caution Only</option>
                <option value="HIGH_RISK_INDICATORS">High Risk Indicators Only</option>
              </select>
            </div>

            <button
              type="submit"
              className="rounded-lg bg-navy-800 px-4 py-2 text-xs font-semibold text-white hover:bg-navy-750 transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 rounded-xl border border-rose-500/30 bg-rose-500/10 p-5 text-rose-300 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1 text-sm">
              <strong className="block text-white mb-1">Failed to Load History</strong>
              <span>{error}</span>
              <button
                type="button"
                onClick={fetchRecords}
                className="block mt-2 text-xs font-semibold text-rose-400 hover:text-white underline"
              >
                Retry Connection
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="rounded-xl border border-navy-800 bg-navy-900/40 p-12 text-center">
            <Loader2 className="h-8 w-8 text-shield-cyan animate-spin mx-auto mb-3" />
            <p className="text-sm text-slate-400">Loading verified analyses from SQLite...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && data && data.items.length === 0 && (
          <div className="rounded-2xl border border-navy-800 bg-navy-900/40 p-12 text-center">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-navy-800 text-slate-400 mb-4">
              <History className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">No Analysis Records Found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mb-5">
              {searchTerm || selectedRisk !== "ALL"
                ? "No saved assessments matched your search filters. Try clearing the filters."
                : "You have not evaluated any job opportunities yet. Use the Job Risk Analyzer to analyze your first job posting."}
            </p>
            <Link
              href="/analyzer"
              className="inline-flex items-center gap-2 rounded-lg bg-shield-blue px-4 py-2 text-xs font-semibold text-white hover:bg-blue-600 transition-colors"
            >
              <Search className="h-3.5 w-3.5" /> Launch Risk Analyzer
            </Link>
          </div>
        )}

        {/* Records Table / List */}
        {!loading && !error && data && data.items.length > 0 && (
          <div className="space-y-3">
            <div className="rounded-xl border border-navy-800 bg-navy-900/70 overflow-hidden shadow-lg">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="border-b border-navy-800 bg-navy-950 text-slate-400 uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-3 px-4">Opportunity</th>
                      <th className="py-3 px-4">Company</th>
                      <th className="py-3 px-4">Risk Verdict</th>
                      <th className="py-3 px-4 text-center">Score</th>
                      <th className="py-3 px-4">Channel</th>
                      <th className="py-3 px-4">Date</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-navy-800/60 font-medium">
                    {data.items.map((item) => (
                      <tr
                        key={item.id}
                        className="hover:bg-navy-850/50 transition-colors cursor-pointer"
                        onClick={() => setSelectedItem(item)}
                      >
                        <td className="py-3.5 px-4 font-semibold text-white">
                          {item.job_title}
                        </td>
                        <td className="py-3.5 px-4 text-slate-300">
                          {item.company_name}
                        </td>
                        <td className="py-3.5 px-4">
                          {getRiskBadge(item.risk_level)}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <span className="font-bold text-white text-sm">
                            {item.final_risk_score}
                          </span>
                          <span className="text-[10px] text-slate-500">/100</span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="rounded bg-navy-950 px-2 py-0.5 text-[10px] font-mono border border-navy-700">
                            {item.contact_channel}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                          {item.created_at ? new Date(item.created_at).toLocaleDateString() : "Recent"}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedItem(item);
                            }}
                            className="inline-flex items-center gap-1 text-shield-brightCyan hover:text-white text-xs font-semibold"
                          >
                            <span>Inspect</span>
                            <ChevronRight className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination Controls */}
            {data.pages > 1 && (
              <div className="flex items-center justify-between text-xs text-slate-400 px-2 pt-2">
                <span>
                  Showing page {data.page} of {data.pages} ({data.total} total analyses)
                </span>
                <div className="flex items-center gap-2">
                  <button
                    disabled={data.page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="rounded border border-navy-700 bg-navy-900 px-3 py-1.5 text-xs text-white disabled:opacity-40"
                  >
                    Previous
                  </button>
                  <button
                    disabled={data.page >= data.pages}
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded border border-navy-700 bg-navy-900 px-3 py-1.5 text-xs text-white disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Modal / Detailed Inspection Drawer */}
        {selectedItem && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-navy-700 bg-navy-900 p-6 shadow-2xl text-left">
              {/* Close Button */}
              <button
                onClick={() => setSelectedItem(null)}
                className="absolute top-5 right-5 text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>

              <div className="flex items-center gap-2 mb-2">
                {getRiskBadge(selectedItem.risk_level)}
                <span className="text-xs text-slate-500 font-mono">
                  ID: {selectedItem.id}
                </span>
              </div>

              <h2 className="text-xl font-bold text-white">
                {selectedItem.job_title}
              </h2>
              <p className="text-xs text-slate-400 mb-4">
                {selectedItem.company_name} • Channel: {selectedItem.contact_channel} • Model: {selectedItem.model_version}
              </p>

              {/* Dual-Tier Score Decomposition */}
              <div className="grid grid-cols-3 gap-2.5 mb-5 text-center">
                <div className="rounded-lg border border-navy-800 bg-navy-950 p-2.5">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Authoritative Rules</div>
                  <div className="text-base font-bold text-white font-mono mt-0.5">{selectedItem.heuristic_risk_score}</div>
                  <div className="text-[9px] text-slate-500">Heuristic Penalties</div>
                </div>
                <div className="rounded-lg border border-navy-800 bg-navy-950 p-2.5">
                  <div className="text-[10px] text-purple-300 uppercase font-semibold">ML Text Advisory</div>
                  <div className="text-base font-bold text-purple-300 font-mono mt-0.5">{selectedItem.ml_risk_score}</div>
                  <div className="text-[9px] text-slate-500">TF-IDF Advisory</div>
                </div>
                <div className="rounded-lg border border-shield-cyan/30 bg-shield-cyan/5 p-2.5">
                  <div className="text-[10px] text-shield-brightCyan uppercase font-semibold">Final Calibrated</div>
                  <div className="text-base font-bold text-white font-mono mt-0.5">{selectedItem.final_risk_score}</div>
                  <div className="text-[9px] text-shield-cyan font-mono">/ 100 Score</div>
                </div>
              </div>

              {/* Recruiter & Opportunity Details */}
              {(selectedItem.location || selectedItem.recruiter_phone || selectedItem.recruiter_email || selectedItem.application_url || selectedItem.salary_offered || selectedItem.requires_payment) && (
                <div className="mb-5 rounded-xl border border-navy-800 bg-navy-950 p-4 text-xs">
                  <h4 className="font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-2 text-[11px]">
                    <Building2 className="h-3.5 w-3.5 text-shield-cyan" />
                    Opportunity & Recruiter Contact Details
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs text-slate-300">
                    {selectedItem.location && (
                      <div className="flex items-center gap-2">
                        <MapPin className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        <span><strong>Location:</strong> {selectedItem.location}</span>
                      </div>
                    )}
                    {selectedItem.recruiter_email && (
                      <div className="flex items-center gap-2">
                        <Mail className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        <span><strong>Email:</strong> {selectedItem.recruiter_email}</span>
                      </div>
                    )}
                    {selectedItem.recruiter_phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        <span><strong>Phone:</strong> {selectedItem.recruiter_phone}</span>
                      </div>
                    )}
                    {selectedItem.salary_offered && (
                      <div className="flex items-center gap-2">
                        <IndianRupee className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        <span><strong>Salary:</strong> {selectedItem.salary_offered} ({selectedItem.salary_frequency?.toLowerCase() || "annual"})</span>
                      </div>
                    )}
                    {selectedItem.application_url && (
                      <div className="sm:col-span-2 flex items-center gap-2">
                        <Globe className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        <span className="truncate">
                          <strong>Portal URL:</strong>{" "}
                          <a
                            href={selectedItem.application_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-shield-brightCyan hover:underline inline-flex items-center gap-1"
                          >
                            <span>{selectedItem.application_url}</span>
                            <ExternalLink className="h-2.5 w-2.5 shrink-0" />
                          </a>
                        </span>
                      </div>
                    )}
                  </div>
                  {selectedItem.requires_payment && (
                    <div className="mt-2.5 pt-2 border-t border-navy-800 text-xs text-rose-300 flex items-center gap-2">
                      <ShieldAlert className="h-3.5 w-3.5 text-rose-400 shrink-0" />
                      <span>
                        <strong>Payment Demanded:</strong> ₹{selectedItem.payment_amount_claimed?.toLocaleString() ?? 0} &bull; Stated Reason: &ldquo;{selectedItem.payment_reason || "Unspecified"}&rdquo;
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Company & Domain Sanity Card */}
              {selectedItem.company_assessment && (
                <div className="mb-5 rounded-xl border border-navy-800 bg-navy-950 p-3.5 text-xs">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-semibold text-slate-300">Employer & Domain Sanity Check</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        selectedItem.company_assessment.domain_status === "verified_match"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                          : selectedItem.company_assessment.domain_status === "personal_domain"
                          ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      {selectedItem.company_assessment.domain_status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-slate-400 text-xs">
                    {selectedItem.company_assessment.advisory_note ||
                      (selectedItem.company_assessment.is_known_firm
                        ? "Matches recognized corporate enterprise database."
                        : "Entity not listed in top corporate registry.")}
                  </p>
                </div>
              )}

              {/* Warning Signs */}
              <div className="space-y-3 mb-5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Detected Warning Indicators ({selectedItem.warning_signs.length})
                </h4>
                {selectedItem.warning_signs.length === 0 ? (
                  <p className="text-xs text-emerald-400">No critical risk warnings detected.</p>
                ) : (
                  selectedItem.warning_signs.map((w, idx) => (
                    <div key={idx} className="rounded-lg border border-navy-800 bg-navy-950 p-3 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-white">{w.title}</span>
                        <span className="text-[10px] uppercase font-bold text-amber-400">{w.severity}</span>
                      </div>
                      <p className="text-slate-400">{w.description}</p>
                    </div>
                  ))
                )}
              </div>

              {/* Audit Evidence & Attributions */}
              <div className="space-y-3 mb-5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5 text-shield-cyan" />
                    Audit Evidence & Attributions ({selectedItem.evidence_snippets?.length || 0})
                  </span>
                  <span className="text-[10px] text-slate-500 font-normal">Traceable Signals</span>
                </h4>
                {!selectedItem.evidence_snippets || selectedItem.evidence_snippets.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">
                    No specific text evidence snippets or ML feature attributions recorded for this assessment.
                  </p>
                ) : (
                  selectedItem.evidence_snippets.map((e, eIdx) => {
                    const isHeuristic = e.attribution === "heuristic_rule";
                    return (
                      <div
                        key={e.id || eIdx}
                        className={`rounded-lg border p-3 text-xs ${
                          isHeuristic
                            ? "border-sky-500/30 bg-sky-500/5 text-slate-200"
                            : "border-purple-500/30 bg-purple-500/5 text-slate-200"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                              isHeuristic
                                ? "bg-sky-500/20 text-sky-300 border-sky-500/30"
                                : "bg-purple-500/20 text-purple-300 border-purple-500/30"
                            }`}
                          >
                            {isHeuristic ? "Rule Evidence" : "ML Advisory Signal"}
                          </span>
                          <span className="font-mono font-bold text-[11px] text-slate-300">
                            {e.impact_score > 0
                              ? `+${e.impact_score} pts`
                              : e.impact_score < 0
                              ? `-${Math.abs(e.impact_score)} pts`
                              : "0 pts"}
                          </span>
                        </div>
                        <p className="text-slate-300 mb-1.5 leading-relaxed">{e.reason}</p>
                        {e.text && (
                          <div className="rounded bg-navy-950 px-2.5 py-1 text-[11px] font-mono text-slate-300 border border-navy-800">
                            &ldquo;{e.text}&rdquo;
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>

              {/* Recommendations */}
              <div className="rounded-xl border border-navy-800 bg-navy-950 p-4 mb-5 text-xs">
                <h4 className="font-bold text-white mb-2">Recommended Next Steps</h4>
                <ul className="space-y-1.5 text-slate-300">
                  {selectedItem.recommendations.map((rec, rIdx) => (
                    <li key={rIdx} className="flex items-start gap-2">
                      <span className="text-shield-cyan">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Footer */}
              <div className="flex justify-end pt-3 border-t border-navy-800">
                <button
                  type="button"
                  onClick={() => setSelectedItem(null)}
                  className="rounded-lg bg-navy-800 px-4 py-2 text-xs font-semibold text-white hover:bg-navy-700"
                >
                  Close Inspection
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
