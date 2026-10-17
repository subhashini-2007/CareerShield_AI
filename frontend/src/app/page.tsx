"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Database,
  Cpu,
  FileCheck,
  Search,
  Scale,
  Sparkles,
} from "lucide-react";
import { getHealthStatus } from "@/lib/api";
import { HealthResponse } from "@/lib/types";

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    getHealthStatus()
      .then((res) => {
        if (isMounted) {
          setHealth(res);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err?.message || "Failed to connect to backend");
          setHealth(null);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="relative overflow-hidden">
      {/* Background Glows */}
      <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[500px] w-[800px] -translate-x-1/2 rounded-full bg-gradient-to-b from-shield-blue/20 to-shield-cyan/5 blur-3xl" />

      {/* Hero Section */}
      <section className="mx-auto max-w-7xl px-4 pt-16 pb-20 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center text-center">
          {/* Eyebrow Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-shield-cyan/30 bg-shield-cyan/10 px-3.5 py-1.5 text-xs font-semibold text-shield-brightCyan mb-6">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Cybersecurity Intelligence for Indian Freshers & Students</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-6xl max-w-4xl leading-tight">
            Verify Opportunities.{" "}
            <span className="bg-gradient-to-r from-shield-brightCyan to-shield-lightBlue bg-clip-text text-transparent">
              Protect Futures.
            </span>
          </h1>

          {/* Subheading */}
          <p className="mt-6 text-lg sm:text-xl text-slate-300 max-w-2xl leading-relaxed">
            CareerShield AI helps graduates and freshers detect recruitment scams, hidden registration fees,
            domain spoofing, and unrealistic claims before applying or sharing sensitive documents.
          </p>

          {/* CTA Buttons */}
          <div className="mt-8 flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            <Link
              href="/analyzer"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-shield-blue px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-shield-blue/25 hover:bg-blue-600 transition-all hover:scale-[1.02]"
            >
              <Search className="h-4 w-4" />
              <span>Launch Risk Analyzer</span>
              <ArrowRight className="h-4 w-4 ml-1" />
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-navy-700 bg-navy-900/80 px-6 py-3.5 text-sm font-semibold text-slate-200 hover:bg-navy-800 transition-colors"
            >
              <FileCheck className="h-4 w-4 text-shield-cyan" />
              <span>View Analytics Dashboard</span>
            </Link>
          </div>

          {/* Live System Diagnostics Card */}
          <div className="mt-12 w-full max-w-2xl rounded-xl border border-navy-800 bg-navy-900/60 p-5 backdrop-blur-sm shadow-xl">
            <div className="flex items-center justify-between border-b border-navy-800 pb-3 mb-4">
              <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase flex items-center gap-2">
                <Cpu className="h-4 w-4 text-shield-cyan" />
                Live Architecture Diagnostics
              </span>
              <span className="text-xs text-slate-400">
                {health?.model.status === "trained" ? "Hybrid Intelligence (Rules + ML)" : "Heuristic Safety Protocol"}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
              {/* API Status */}
              <div className="rounded-lg border border-navy-800 bg-navy-950/70 p-3">
                <div className="text-xs text-slate-400">FastAPI Backend</div>
                <div className="mt-1 flex items-center gap-1.5 text-sm font-semibold">
                  {loading ? (
                    <span className="text-slate-400 text-xs">Connecting...</span>
                  ) : health?.status === "ok" ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="h-4 w-4" /> Operational
                    </span>
                  ) : (
                    <span className="text-rose-400 flex items-center gap-1">
                      <AlertTriangle className="h-4 w-4" /> Offline / Standby
                    </span>
                  )}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 truncate">
                  {health ? `REST API v${health.app.version} [${health.app.environment}]` : error ? "Port 8000 unreachable" : "REST API v0.1.0"}
                </div>
              </div>

              {/* Database Status */}
              <div className="rounded-lg border border-navy-800 bg-navy-950/70 p-3">
                <div className="text-xs text-slate-400">Database Engine</div>
                <div className="mt-1 flex items-center gap-1.5 text-sm font-semibold">
                  <Database className="h-4 w-4 text-shield-cyan" />
                  <span className="text-slate-200 uppercase">
                    {loading ? "Querying..." : health?.database.engine || (error ? "Unavailable" : "sqlite")}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                  {loading
                    ? "Checking schema..."
                    : health
                    ? health.database.connected
                      ? `Connected${health.database.latency_ms !== undefined ? ` (${health.database.latency_ms}ms)` : ""}`
                      : "Disconnected"
                    : "Database Offline"}
                </div>
              </div>

              {/* Rules & ML Model Status */}
              <div className="rounded-lg border border-navy-800 bg-navy-950/70 p-3">
                <div className="text-xs text-slate-400">Risk Scoring Engine</div>
                <div className="mt-1 flex items-center gap-1.5 text-sm font-semibold">
                  <Scale className="h-4 w-4 text-shield-cyan" />
                  <span className="text-slate-200">
                    {loading
                      ? "Inspecting..."
                      : health?.model.status === "trained"
                      ? "Hybrid Engine"
                      : health
                      ? "Rules Engine Only"
                      : "Unavailable"}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 truncate" title={health?.model.version}>
                  {loading
                    ? "Loading model state..."
                    : health?.model.status === "trained"
                    ? health.model.version
                    : health
                    ? "ML Model Untrained Fallback"
                    : "Scoring Engine Offline"}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Pillars */}
      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 border-t border-navy-800">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">
            Comprehensive Verification Layers
          </h2>
          <p className="mt-3 text-slate-400 text-sm sm:text-base">
            Engineered to address actual patterns documented by the Ministry of Labour & Employment and corporate advisories.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 hover:border-shield-cyan/40 transition-colors">
            <div className="h-10 w-10 rounded-lg bg-shield-blue/20 text-shield-brightCyan flex items-center justify-center mb-4">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Upfront Fee Detection</h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              Detects requests for registration fees, training kit charges, laptop courier deposits, and document verification charges disguised as legitimate hiring steps.
            </p>
          </div>

          {/* Card 2 */}
          <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 hover:border-shield-cyan/40 transition-colors">
            <div className="h-10 w-10 rounded-lg bg-shield-cyan/20 text-shield-brightCyan flex items-center justify-center mb-4">
              <Search className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Recruiter & Domain Sanity</h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              Audits recruiter domains against official career registries. Immediately flags instances where top MNC names (TCS, Infosys, Wipro) are claimed via free webmails.
            </p>
          </div>

          {/* Card 3 */}
          <div className="rounded-xl border border-navy-800 bg-navy-900/60 p-6 hover:border-shield-cyan/40 transition-colors">
            <div className="h-10 w-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4">
              <Scale className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Explainable AI Scoring</h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              Transparent, dual-tier assessment separating statistical text patterns from deterministic safety rules. Highlights the exact sentences that triggered warnings.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
