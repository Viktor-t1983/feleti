import { apiClient } from "./client";

export interface SourceRead {
  id: number;
  domain: string;
  score: number;
  is_blacklisted: boolean;
  label: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceCreate {
  domain: string;
  score?: number;
  is_blacklisted?: boolean;
  label?: string | null;
  notes?: string | null;
}

export interface SourceUpdate {
  domain?: string;
  score?: number;
  is_blacklisted?: boolean;
  label?: string | null;
  notes?: string | null;
}

export async function listSources(blacklisted?: boolean): Promise<SourceRead[]> {
  const params = blacklisted !== undefined ? { blacklisted } : {};
  const { data } = await apiClient.get("/sources/", { params });
  return data;
}

export async function createSource(payload: SourceCreate): Promise<SourceRead> {
  const { data } = await apiClient.post("/sources/", payload);
  return data;
}

export async function getSource(id: number): Promise<SourceRead> {
  const { data } = await apiClient.get(`/sources/${id}`);
  return data;
}

export async function updateSource(id: number, payload: SourceUpdate): Promise<SourceRead> {
  const { data } = await apiClient.put(`/sources/${id}`, payload);
  return data;
}

export async function deleteSource(id: number): Promise<void> {
  await apiClient.delete(`/sources/${id}`);
}
