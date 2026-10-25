/**
 * CareerShield AI — TypeScript Domain Types & Interfaces
 */

export type RiskLevel = "LOW_RISK" | "NEEDS_CAUTION" | "HIGH_RISK_INDICATORS";

export interface DatabaseHealth {
  connected: boolean;
  engine: "postgresql" | "sqlite" | string;
  latency_ms?: number;
  error?: string | null;
}

export interface ModelHealth {
  loaded: boolean;
  version: string;
  status: "trained" | "not_trained";
}

export interface AppInfo {
  name: string;
  version: string;
  environment: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  timestamp: string;
  app: AppInfo;
  database: DatabaseHealth;
  model: ModelHealth;
}

export interface WarningSign {
  id: string;
  category: "UPFRONT_FEE" | "DOMAIN_SPOOFING" | "CHANNEL_RISK" | "SALARY_ANOMALY" | "ZERO_INTERVIEW" | "PRESSURE_TACTIC" | "MISSING_INFO" | "OTHER" | string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  title: string;
  description: string;
  matched_text?: string;
}

export interface EvidenceSnippet {
  id: string;
  text: string;
  attribution: "ml_feature" | "heuristic_rule";
  impact_score: number;
  reason: string;
}

export interface JobAnalysisRequest {
  job_title: string;
  company_name: string;
  recruiter_name?: string;
  recruiter_email?: string;
  recruiter_phone?: string;
  contact_channel: "EMAIL" | "TELEGRAM" | "WHATSAPP" | "LINKEDIN" | "OFFICIAL_PORTAL" | "OTHER";
  job_description: string;
  salary_offered?: string;
  salary_frequency?: "MONTHLY" | "ANNUAL" | "PER_TASK" | "DAILY";
  location?: string;
  application_url?: string;
  requires_payment: boolean;
  payment_amount_claimed?: number;
  payment_reason?: string;
}

export interface JobAnalysisResponse {
  id: string;
  job_title: string;
  company_name: string;
  recruiter_name?: string;
  recruiter_email?: string;
  recruiter_phone?: string;
  contact_channel: string;
  job_description: string;
  salary_offered?: string;
  salary_frequency?: string;
  location?: string;
  application_url?: string;
  requires_payment: boolean;
  payment_amount_claimed?: number;
  payment_reason?: string;
  ml_risk_score: number;
  heuristic_risk_score: number;
  final_risk_score: number;
  risk_level: RiskLevel;
  confidence_score: number;
  warning_signs: WarningSign[];
  evidence_snippets: EvidenceSnippet[];
  recommendations: string[];
  company_assessment: {
    domain_status: "verified_match" | "personal_domain" | "unverified_domain" | "missing";
    is_known_firm: boolean;
    advisory_note?: string;
    verified_url?: string;
  };
  model_version: string;
  disclaimer?: string;
  created_at: string;
}

export interface PaginatedAnalysesResponse {
  items: JobAnalysisResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface FeedbackSubmission {
  analysis_id: string;
  user_verdict: "ACCURATE" | "TOO_STRICT" | "MISSED_SCAM" | "INCONCLUSIVE";
  actual_outcome?: "CONFIRMED_LEGITIMATE" | "CONFIRMED_SCAM" | "UNRESOLVED";
  comments?: string;
}

export interface RiskCategoryStat {
  category: string;
  label: string;
  count: number;
  percentage: number;
  color: string;
}

export interface ScoreRangeStat {
  range_label: string;
  min_score: number;
  max_score: number;
  count: number;
  percentage: number;
}

export interface ChannelRiskStat {
  channel: string;
  count: number;
  percentage: number;
  average_risk_score: number;
}

export interface WarningIndicatorStat {
  category: string;
  title: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  count: number;
  percentage: number;
}

export interface RecentAnalysisSummaryItem {
  id: string;
  job_title: string;
  company_name: string;
  contact_channel: string;
  final_risk_score: number;
  risk_level: RiskLevel;
  requires_payment: boolean;
  payment_amount_claimed?: number | null;
  created_at?: string | null;
}

export interface AnalyticsSummaryResponse {
  total_analyses: number;
  average_risk_score: number;
  high_risk_count: number;
  high_risk_percentage: number;
  caution_count: number;
  caution_percentage: number;
  low_risk_count: number;
  low_risk_percentage: number;
  payment_demanded_count: number;
  payment_demanded_percentage: number;
  risk_distribution: RiskCategoryStat[];
  score_ranges: ScoreRangeStat[];
  channel_distribution: ChannelRiskStat[];
  top_warning_indicators: WarningIndicatorStat[];
  recent_activity: RecentAnalysisSummaryItem[];
}

export interface RuleDefinition {
  rule_id: string;
  name: string;
  category: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  risk_points: number;
  impact_type: "PENALTY" | "MITIGATION";
  description: string;
  detection_mechanism: string;
  historical_triggers_count: number;
  trigger_percentage: number;
}

export interface MitigatingSignalDefinition {
  signal_id: string;
  name: string;
  point_reduction: number;
  description: string;
  detection_mechanism: string;
}

export interface ScoreBandDefinition {
  tier: string;
  label: string;
  min_score: number;
  max_score: number;
  description: string;
  color: string;
}

export interface OfflineBenchmarkMetrics {
  dataset_name: string;
  test_split_size: number;
  roc_auc: number;
  pr_auc: number;
  fraud_precision: number;
  fraud_recall: number;
  threshold: number;
  caveat?: string;
}

export interface ModelTransparencyResponse {
  engine_type: string;
  engine_version: string;
  total_rules_defined: number;
  ml_model_status: string;
  ml_metrics_available: boolean;
  ml_metrics_explanation: string;
  total_evaluations_analyzed: number;
  score_calculation_formula: string;
  score_bands: ScoreBandDefinition[];
  rules: RuleDefinition[];
  mitigating_signals: MitigatingSignalDefinition[];
  limitations: string[];
  benchmark_metrics?: OfflineBenchmarkMetrics | null;
}

