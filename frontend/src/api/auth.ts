import apiClient from './client';
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types/auth';

export async function loginApi(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', data);
  return response.data;
}

export async function registerApi(data: RegisterRequest): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', data);
  return response.data;
}

export async function getMeApi(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
}
