export interface AISettings {
  provider: string;
  endpoint: string;
  api_key: string | null;
  model_name: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface AISettingsUpdate {
  provider?: string;
  endpoint?: string;
  api_key?: string | null;
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  enabled?: boolean;
}

export interface AITestResult {
  success: boolean;
  model: string | null;
  latency_ms: number | null;
  error: string | null;
}

export interface KnowledgeArticleSummary {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  category: string;
  tags: string[];
  is_published: boolean;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface AIAskResponse {
  answer: string;
  sources: KnowledgeArticleSummary[];
  query: string;
  model: string;
}
