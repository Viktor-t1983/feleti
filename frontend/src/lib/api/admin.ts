import { apiClient } from "./client";
import type { User } from "./auth";

export interface UserCreate {
  email: string;
  username: string;
  full_name?: string | null;
  password: string;
  role: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface UserUpdate {
  email?: string;
  username?: string;
  full_name?: string | null;
  password?: string;
  role?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export async function fetchUsers(page = 1, size = 50): Promise<PageResponse<User>> {
  const res = await apiClient.get<PageResponse<User>>(`/users?page=${page}&size=${size}`);
  return res.data;
}

export async function fetchUser(id: number): Promise<User> {
  const res = await apiClient.get<User>(`/users/${id}`);
  return res.data;
}

export async function createUser(data: UserCreate): Promise<User> {
  const res = await apiClient.post<User>("/users", data);
  return res.data;
}

export async function updateUser(id: number, data: UserUpdate): Promise<User> {
  const res = await apiClient.patch<User>(`/users/${id}`, data);
  return res.data;
}

export async function deleteUser(id: number): Promise<void> {
  await apiClient.delete(`/users/${id}`);
}
