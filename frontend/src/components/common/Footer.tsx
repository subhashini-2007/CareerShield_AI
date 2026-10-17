import React from "react";
import Link from "next/link";
import { Shield, AlertTriangle, ExternalLink } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-navy-800 bg-navy-950 py-10 text-slate-400">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Brand & Advisory */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-shield-brightCyan" />
              <span className="text-base font-bold text-white tracking-wide">
                CareerShield AI
              </span>
            </div>
            <p className="text-sm text-slate-400 max-w-md leading-relaxed">
              An intelligent, transparent cybersecurity and job risk evaluation platform
              protecting Indian students and fresh graduates from deceptive recruitment schemes.
            </p>
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-amber-300 flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
              <span>
                <strong>Responsible AI Notice:</strong> CareerShield AI outputs advisory signals based on statistical
                indicators and heuristic policies. It does not provide legal judgments. Genuine Indian employers never charge candidates application or training fees.
              </span>
            </div>
          </div>

          {/* Core Navigation */}
          <div>
            <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/analyzer" className="hover:text-shield-brightCyan transition-colors">
                  Job Risk Analyzer
                </Link>
              </li>
              <li>
                <Link href="/dashboard" className="hover:text-shield-brightCyan transition-colors">
                  Platform Analytics
                </Link>
              </li>
              <li>
                <Link href="/history" className="hover:text-shield-brightCyan transition-colors">
                  Audit History
                </Link>
              </li>
              <li>
                <Link href="/model-insights" className="hover:text-shield-brightCyan transition-colors">
                  Model Transparency
                </Link>
              </li>
            </ul>
          </div>

          {/* Official Resources & Helplines */}
          <div>
            <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-3">
              Official Portals
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://cybercrime.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 hover:text-shield-brightCyan transition-colors"
                >
                  National Cyber Crime Portal
                  <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <a
                  href="https://ncs.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 hover:text-shield-brightCyan transition-colors"
                >
                  National Career Service (NCS)
                  <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <span className="text-xs text-slate-500">Cyber Helpline: Dial 1930 (India)</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-navy-800 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© {new Date().getFullYear()} CareerShield AI. Portfolio Project Demonstration.</p>
          <p>Built with Next.js, FastAPI, PostgreSQL, and Scikit-learn.</p>
        </div>
      </div>
    </footer>
  );
};
