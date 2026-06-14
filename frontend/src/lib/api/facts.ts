import { apiClient } from "./client";

export interface FactItem {
  id: number;
  subject_name: string;
  subject_type: string;
  predicate: string;
  object_name: string;
  object_type: string;
  confidence: number;
  status: string;
  source_text: string | null;
  article_id: number;
  chunk_id: number | null;
  created_at: string;
}

export interface VerificationReport {
  duplicates: Array<{
    subject_name: string;
    subject_type: string;
    predicate: string;
    object_name: string;
    object_type: string;
    count: number;
    fact_ids: number[];
  }>;
  contradictions: Array<{
    subject_name: string;
    subject_type: string;
    predicate: string;
    objects: Array<{
      fact_id: number;
      object_name: string;
      confidence: number;
      source_text: string | null;
    }>;
  }>;
  auto_result: Record<string, unknown>;
}

export async function listFacts(params?: {
  status?: string;
  predicate?: string;
  limit?: number;
}): Promise<FactItem[]> {
  const { data } = await apiClient.get("/knowledge/facts", { params });
  return data as FactItem[];
}

export async function updateFactStatus(
  factId: number,
  status: "confirmed" | "deprecated"
): Promise<FactItem> {
  const { data } = await apiClient.patch(`/knowledge/facts/${factId}/status`, { status });
  return data as FactItem;
}

export async function getVerificationReport(): Promise<VerificationReport> {
  const { data } = await apiClient.get("/knowledge/verify/report");
  return data as VerificationReport;
}

export async function runAutoVerify(): Promise<VerificationReport> {
  const { data } = await apiClient.post("/knowledge/verify/auto");
  return data as VerificationReport;
}
