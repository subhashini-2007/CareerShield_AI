/**
 * CareerShield AI — API Client
 */

import axios from "axios";
import {
  AnalyticsSummaryResponse,
  HealthResponse,
  JobAnalysisRequest,
  JobAnalysisResponse,
  ModelTransparencyResponse,
  PaginatedAnalysesResponse,
} from "./types";

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const API_BASE_URL = rawApiUrl.endsWith("/") ? rawApiUrl.slice(0, -1) : rawApiUrl;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

/**
 * Fetch system diagnostics and health status.
 */
export async function getHealthStatus(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>("/health");
  return response.data;
}

/**
 * Submit a job opportunity for risk analysis.
 */
export async function analyzeJob(payload: JobAnalysisRequest): Promise<JobAnalysisResponse> {
  const response = await apiClient.post<JobAnalysisResponse>("/analyze", payload);
  return response.data;
}

/**
 * Fetch paginated analysis audit history.
 */
export async function getAnalyses(params?: {
  page?: number;
  page_size?: number;
  risk_level?: string;
  search?: string;
}): Promise<PaginatedAnalysesResponse> {
  const response = await apiClient.get<PaginatedAnalysesResponse>("/analyses", { params });
  return response.data;
}

/**
 * Fetch single analysis report by ID.
 */
export async function getAnalysisById(id: string): Promise<JobAnalysisResponse> {
  const response = await apiClient.get<JobAnalysisResponse>(`/analyses/${id}`);
  return response.data;
}

/**
 * Fetch aggregated metrics for the Analytics Dashboard.
 */
export async function getAnalyticsSummary(): Promise<AnalyticsSummaryResponse> {
  const response = await apiClient.get<AnalyticsSummaryResponse>("/analytics/summary");
  return response.data;
}

/**
 * Fetch heuristic model transparency specifications and trigger stats.
 */
export async function getModelTransparency(): Promise<ModelTransparencyResponse> {
  const response = await apiClient.get<ModelTransparencyResponse>("/analytics/model-transparency");
  return response.data;
}

