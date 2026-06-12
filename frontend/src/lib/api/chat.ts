import { apiClient } from "./client";

export interface ChatSessionSummary {
  id: number;
  title: string;
  page_context: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageRead {
  id: number;
  session_id: number;
  seq: number;
  role: "user" | "assistant";
  content: string;
  sources: { id: number; title: string; slug: string }[] | null;
  model: string | null;
  created_at: string;
}

export interface ChatSessionRead {
  id: number;
  user_id: number;
  title: string;
  page_context: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
  messages: ChatMessageRead[];
}

export async function listSessions(
  page = 1,
  size = 50,
): Promise<{ items: ChatSessionSummary[]; total: number }> {
  const { data } = await apiClient.get("/chat/sessions", {
    params: { page, size },
  });
  return data;
}

export async function createSession(
  title = "Новый диалог",
  pageContext?: string,
): Promise<ChatSessionRead> {
  const { data } = await apiClient.post("/chat/sessions", {
    title,
    page_context: pageContext || null,
  });
  return data;
}

export async function getSession(
  sessionId: number,
): Promise<ChatSessionRead> {
  const { data } = await apiClient.get(`/chat/sessions/${sessionId}`);
  return data;
}

export async function updateSession(
  sessionId: number,
  payload: { title?: string; page_context?: string | null },
): Promise<ChatSessionRead> {
  const { data } = await apiClient.patch(`/chat/sessions/${sessionId}`, payload);
  return data;
}

export async function deleteSession(sessionId: number): Promise<void> {
  await apiClient.delete(`/chat/sessions/${sessionId}`);
}

export async function addMessage(
  sessionId: number,
  role: "user" | "assistant",
  content: string,
  sources?: { id: number; title: string; slug: string }[] | null,
  model?: string | null,
): Promise<ChatMessageRead> {
  const { data } = await apiClient.post(`/chat/sessions/${sessionId}/messages`, {
    role,
    content,
    sources: sources || null,
    model: model || null,
  });
  return data;
}
