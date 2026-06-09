import { apiClient } from "./client";

export interface Manufacturer {
  id: number;
  slug: string;
  name: string;
  short_name: string | null;
  country: string | null;
  city: string | null;
  founded_year: number | null;
  website: string | null;
  description: string | null;
  logo_url: string | null;
  is_our_brand: boolean;
  is_competitor: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string | null;
}

interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ManufacturerCreate {
  slug: string;
  name: string;
  short_name?: string | null;
  country?: string | null;
  city?: string | null;
  founded_year?: number | null;
  website?: string | null;
  description?: string | null;
  logo_url?: string | null;
  is_our_brand?: boolean;
  is_competitor?: boolean;
  sort_order?: number;
}

export interface ManufacturerUpdate {
  name?: string;
  short_name?: string | null;
  country?: string | null;
  city?: string | null;
  founded_year?: number | null;
  website?: string | null;
  description?: string | null;
  logo_url?: string | null;
  is_our_brand?: boolean;
  is_competitor?: boolean;
  sort_order?: number;
}

export async function fetchManufacturersAdmin(page = 1, size = 100): Promise<PageResponse<Manufacturer>> {
  const res = await apiClient.get<PageResponse<Manufacturer>>(`/manufacturers?page=${page}&size=${size}`);
  return res.data;
}

export async function createManufacturer(data: ManufacturerCreate): Promise<Manufacturer> {
  const res = await apiClient.post<Manufacturer>("/manufacturers", data);
  return res.data;
}

export async function updateManufacturer(id: number, data: ManufacturerUpdate): Promise<Manufacturer> {
  const res = await apiClient.patch<Manufacturer>(`/manufacturers/${id}`, data);
  return res.data;
}

export async function deleteManufacturer(id: number): Promise<void> {
  await apiClient.delete(`/manufacturers/${id}`);
}
