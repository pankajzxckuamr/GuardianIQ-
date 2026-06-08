/* src/services/auth/authService.ts */
import type { LoginCredentials, TokenResponse, RefreshRequest } from "./authTypes";
import type { User } from "../../types/auth";
import { getDeviceId } from "../shared/deviceId";
import { generateRequestId } from "../shared/requestId";
import { parseErrorResponse } from "../shared/serviceErrors";

const AUTH_BASE = "/api/auth";

function authHeaders(token?: string): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Device-ID": getDeviceId(),
    "X-Request-ID": generateRequestId(),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const res = await fetch(`${AUTH_BASE}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-Device-ID": getDeviceId(),
      "X-Request-ID": generateRequestId(),
    },
    credentials: "include",
    body: formData.toString(),
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function logout(token: string): Promise<void> {
  await fetch(`${AUTH_BASE}/logout`, {
    method: "POST",
    headers: authHeaders(token),
    credentials: "include",
  });
}

export async function fetchMe(token: string): Promise<User> {
  const res = await fetch(`${AUTH_BASE}/me`, {
    method: "GET",
    headers: authHeaders(token),
    credentials: "include",
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function refreshAccessToken(req: RefreshRequest): Promise<TokenResponse> {
  const res = await fetch(`${AUTH_BASE}/refresh`, {
    method: "POST",
    headers: authHeaders(),
    credentials: "include",
    body: JSON.stringify(req),
  });
  if (!res.ok) throw await parseErrorResponse(res);
  const body = await res.json();
  return body.data ?? body;
}

export async function changePassword(newPassword: string, token: string): Promise<void> {
  const res = await fetch(`${AUTH_BASE}/change-password`, {
    method: "POST",
    headers: authHeaders(token),
    credentials: "include",
    body: JSON.stringify({ new_password: newPassword }),
  });
  if (!res.ok) throw await parseErrorResponse(res);
}
