import { useAuthStore } from "@/lib/auth/store";
import type { TokenPair } from "@/lib/auth/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : "Terjadi kesalahan");
    this.status = status;
    this.detail = detail;
  }
}

async function parseErrorDetail(response: Response): Promise<unknown> {
  try {
    const body = await response.json();
    return body?.detail ?? body;
  } catch {
    return response.statusText;
  }
}

let refreshPromise: Promise<string | null> | null = null;

/** Calls POST /auth/refresh once, de-duped across concurrent callers. */
async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, setAccessToken, clear } = useAuthStore.getState();
  if (!refreshToken) return null;

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (res) => {
        if (!res.ok) {
          clear();
          return null;
        }
        const tokens: TokenPair = await res.json();
        setAccessToken(tokens.access_token);
        useAuthStore.setState({ refreshToken: tokens.refresh_token });
        return tokens.access_token;
      })
      .catch(() => {
        clear();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Skip Authorization header (e.g. the /auth/login call itself). */
  skipAuth?: boolean;
}

/** Fetch wrapper: attaches the access token, retries once via refresh on a
 * 401, and throws ApiError with the backend's `detail` message otherwise. */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, skipAuth, headers, ...rest } = options;

  const doFetch = async (): Promise<Response> => {
    const token = useAuthStore.getState().accessToken;
    return fetch(`${API_URL}${path}`, {
      ...rest,
      headers: {
        "Content-Type": "application/json",
        ...(!skipAuth && token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  };

  let response = await doFetch();

  if (response.status === 401 && !skipAuth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await doFetch();
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
