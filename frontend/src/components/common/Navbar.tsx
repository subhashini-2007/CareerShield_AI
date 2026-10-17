"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Shield } from "lucide-react";
import { getHealthStatus } from "@/lib/api";
import { HealthResponse } from "@/lib/types";

export const Navbar: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    getHealthStatus()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-navy-800 bg-navy-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-shield-blue/20 border border-shield-cyan/30 text-shield-brightCyan shadow-[0_0_15px_rgba(6,182,212,0.25)] transition-all group-hover:scale-105">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white group-hover:text-shield-brightCyan transition-colors">
                CareerShield
              </span>
              <span className="rounded bg-shield-cyan/15 px-1.5 py-0.5 text-xs font-semibold text-shield-brightCyan border border-shield-cyan/30">
                AI
              </span>
            </div>
            <p className="hidden text-xs text-slate-400 sm:block">
              Verify Opportunities. Protect Futures.
            </p>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          <Link
            href="/analyzer"
            className="text-sm font-medium text-slate-300 hover:text-shield-brightCyan transition-colors"
          >
            Risk Analyzer
          </Link>
          <Link
            href="/dashboard"
            className="text-sm font-medium text-slate-300 hover:text-shield-brightCyan transition-colors"
          >
            Dashboard
          </Link>
          <Link
            href="/history"
            className="text-sm font-medium text-slate-300 hover:text-shield-brightCyan transition-colors"
          >
            Audit History
          </Link>
          <Link
            href="/model-insights"
            className="text-sm font-medium text-slate-300 hover:text-shield-brightCyan transition-colors"
          >
            Model Insights
          </Link>
        </nav>

        {/* Diagnostic Status Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-navy-700 bg-navy-900/90 px-3 py-1 text-xs">
            {loading ? (
              <span className="flex items-center gap-1.5 text-slate-400">
                <span className="h-2 w-2 animate-pulse rounded-full bg-slate-500" />
                Connecting API...
              </span>
            ) : health ? (
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                API Online ({health.database.engine})
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-amber-400 font-medium">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                Backend Offline
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
