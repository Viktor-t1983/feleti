import { apiClient } from "./client";
import type { Competitor } from "@/components/competitors/CompetitorCard";

interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface CompetitorUpdate {
  name?: string;
  country?: string | null;
  founded_year?: number | null;
  segment?: string | null;
  is_main_competitor?: boolean;
  client_count?: number | null;
  recipe_count?: number | null;
  warranty_years?: number | null;
  has_cloud?: boolean | null;
  has_mobile_app?: boolean | null;
  has_remote_monitoring?: boolean | null;
  has_video_camera?: boolean | null;
  description?: string | null;
  strengths?: string[];
  weaknesses?: string[];
  base_url?: string | null;
  sitemap_url?: string | null;
  dealers?: Record<string, unknown>[];
  [key: string]: unknown;
}

export async function fetchCompetitorsAdmin(page = 1, size = 100): Promise<PageResponse<Competitor>> {
  const res = await apiClient.get<PageResponse<Competitor>>(`/competitors?page=${page}&size=${size}`);
  return res.data;
}

export async function updateCompetitor(id: number | string, data: CompetitorUpdate): Promise<Competitor> {
  const res = await apiClient.patch<Competitor>(`/competitors/${id}`, data);
  return res.data;
}

export async function deleteCompetitor(id: number | string): Promise<void> {
  await apiClient.delete(`/competitors/${id}`);
}
