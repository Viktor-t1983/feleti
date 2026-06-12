import { apiClient } from "./client";

export interface TopicRead {
  id: number;
  slug: string;
  label: string;
  description: string | null;
  path: string;
  parent_id: number | null;
  level: number;
  sort_order: number;
  icon: string | null;
  article_count: number;
  created_at: string;
  updated_at: string;
}

export interface TopicCreate {
  label: string;
  slug: string;
  description?: string | null;
  parent_id?: number | null;
  sort_order?: number;
  icon?: string | null;
}

export interface TopicUpdate {
  label?: string;
  description?: string | null;
  parent_id?: number | null;
  sort_order?: number;
  icon?: string | null;
}

export async function getTopic(id: number): Promise<TopicRead> {
  const { data } = await apiClient.get(`/knowledge/topics/${id}`);
  return data;
}

export async function createTopic(payload: TopicCreate): Promise<TopicRead> {
  const { data } = await apiClient.post("/knowledge/topics", payload);
  return data;
}

export async function updateTopic(
  id: number,
  payload: TopicUpdate,
): Promise<TopicRead> {
  const { data } = await apiClient.patch(`/knowledge/topics/${id}`, payload);
  return data;
}

export async function deleteTopic(id: number): Promise<void> {
  await apiClient.delete(`/knowledge/topics/${id}`);
}
