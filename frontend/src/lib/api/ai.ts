import type { AISettings, AISettingsUpdate, AITestResult, AIAskResponse } from "@/types/ai";
import { apiClient } from "./client";

export async function getAISettings(): Promise<AISettings> {
  const { data } = await apiClient.get("/ai/settings");
  return data;
}

export async function updateAISettings(payload: AISettingsUpdate): Promise<AISettings> {
  const { data } = await apiClient.put("/ai/settings", payload);
  return data;
}

export async function testAI(): Promise<AITestResult> {
  const { data } = await apiClient.post("/ai/test");
  return data;
}

export async function askAI(question: string, topK = 5): Promise<AIAskResponse> {
  const { data } = await apiClient.post("/ai/ask", { question, top_k: topK });
  return data;
}
