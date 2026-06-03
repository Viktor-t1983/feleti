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

export type SSEEvent =
  | { type: "token"; content: string }
  | { type: "done"; model: string }
  | { type: "error"; message: string }
  | { type: "sources"; count: number; articles?: { id: number; title: string; slug: string }[] };

export async function askAIStream(
  question: string,
  onEvent: (event: SSEEvent) => void,
  topK = 5,
  signal?: AbortSignal,
): Promise<void> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/ai/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ question, top_k: topK }),
    signal,
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`SSE error ${response.status}: ${body}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const event = JSON.parse(line.slice(6)) as SSEEvent;
          onEvent(event);
        } catch {
          // skip malformed JSON
        }
      }
    }
  }
}
