import createClient from "openapi-fetch";
import { API_URL } from "@/config/env";
import { useAuthStore } from "@/store/authStore";
import type { AuthTokenResponse } from "./authTypes";
import type { paths } from "./types.gen";

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(typeof body === "object" && body && "detail" in body ? String((body as { detail: unknown }).detail) : `Request failed (${status})`);
  }
}

let refreshPromise: Promise<string | null> | null = null;

// Concurrent 401s all await this one call instead of each firing their own
// refresh — otherwise several screens querying at once could each rotate
// the refresh token and invalidate each other's retry.
function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function doRefresh(): Promise<string | null> {
  const { refreshToken, setSession, clearTokens } = useAuthStore.getState();
  if (!refreshToken) return null;

  // Raw fetch, not the typed `api` client below — `api` wraps authFetch, which
  // calls this function, so going through `api` here would be circular.
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  }).catch(() => null);

  if (!res || !res.ok) {
    clearTokens();
    return null;
  }
  const data = (await res.json()) as AuthTokenResponse;
  setSession(data.access_token, data.refresh_token);
  return data.access_token;
}

// The fetch openapi-fetch calls under the hood: attaches the bearer token,
// and on a 401 refreshes once and retries exactly once. A 401 after that
// retry is a real auth failure, not a stale-token race.
async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const attempt = async () => {
    const { accessToken } = useAuthStore.getState();
    // openapi-fetch calls this with a pre-built Request as `input` and
    // `init` left undefined — reading headers from `init?.headers` here
    // silently produced an empty Headers object, which dropped the
    // Content-Type: application/json set by openapi-fetch's serializer when
    // the request got reconstructed below. Without it the backend stopped
    // parsing the body as JSON, so Pydantic saw the raw string instead of a
    // dict (422 "Input should be a valid dictionary"). Read from the
    // Request's own headers when that's what we were given.
    const headers = new Headers(input instanceof Request ? input.headers : init?.headers);
    if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
    return fetch(input, { ...init, headers });
  };

  let res = await attempt();
  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) res = await attempt();
  }
  return res;
}

// The typed client — every real endpoint (currently /auth/google, /health)
// gets full request/response inference from types.gen.ts for free.
export const api = createClient<paths>({ baseUrl: API_URL, fetch: authFetch });

// openapi-fetch returns {data, error, response} instead of throwing.
// unwrap() gives throw-on-error semantics, which is what a TanStack Query
// queryFn/mutationFn is expected to do.
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined) throw new ApiError(result.response.status, result.error);
  return result.data as T;
}
