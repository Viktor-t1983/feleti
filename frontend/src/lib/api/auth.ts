import { apiClient } from "./client";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
}

export async function loginJson(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login/json", credentials);
  return response.data;
}

export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/refresh", { refresh_token });
  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}
