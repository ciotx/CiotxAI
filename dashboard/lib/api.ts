const API_URL = process.env.NEXT_PUBLIC_API_URL || "";
if (!API_URL && typeof window !== "undefined") {
  console.error("NEXT_PUBLIC_API_URL is not set. API calls will fail.");
}

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

function getTokens(): TokenPair | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("ciotx_tokens");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setTokens(tokens: TokenPair) {
  localStorage.setItem("ciotx_tokens", JSON.stringify(tokens));
}

function clearTokens() {
  localStorage.removeItem("ciotx_tokens");
}

async function refreshTokens(): Promise<string | null> {
  const tokens = getTokens();
  if (!tokens?.refresh_token) return null;

  try {
    const res = await fetch(`${API_URL}/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: tokens.refresh_token }),
    });

    if (!res.ok) {
      clearTokens();
      return null;
    }

    const newTokens: TokenPair = await res.json();
    setTokens(newTokens);
    return newTokens.access_token;
  } catch {
    return null;
  }
}

export async function api(path: string, options: RequestInit = {}): Promise<Response> {
  const tokens = getTokens();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (tokens?.access_token) {
    headers["Authorization"] = `Bearer ${tokens.access_token}`;
  }

  let res = await fetch(`${API_URL}${path}`, { ...options, headers });

  // If 401, try refresh
  if (res.status === 401 && tokens?.refresh_token) {
    const newAccessToken = await refreshTokens();
    if (newAccessToken) {
      headers["Authorization"] = `Bearer ${newAccessToken}`;
      res = await fetch(`${API_URL}${path}`, { ...options, headers });
    }
  }

  return res;
}

export async function login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_URL}/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const data = await res.json();
      return { success: false, error: data.detail || "Login failed." };
    }

    const tokens: TokenPair = await res.json();
    setTokens(tokens);
    return { success: true };
  } catch {
    return { success: false, error: "Network error. Is the server running?" };
  }
}

export async function signup(email: string, password: string, name?: string): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_URL}/v1/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    });

    if (!res.ok) {
      const data = await res.json();
      return { success: false, error: data.detail || "Signup failed." };
    }

    return { success: true };
  } catch {
    return { success: false, error: "Network error. Is the server running?" };
  }
}

export async function verifyEmail(email: string, code: string): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch(`${API_URL}/v1/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code }),
    });

    if (!res.ok) {
      const data = await res.json();
      return { success: false, error: data.detail || "Verification failed." };
    }

    return { success: true };
  } catch {
    return { success: false, error: "Network error. Is the server running?" };
  }
}

export async function getMe() {
  try {
    const res = await api("/v1/auth/me");
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export function logout() {
  clearTokens();
  window.location.href = "/login";
}
