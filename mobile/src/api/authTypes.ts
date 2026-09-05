import type { components } from "./types.gen";

// All 4 auth endpoints exist server-side now, so every request/response shape
// comes from the generated spec — no hand-written duplicates (see CLAUDE.md
// "Never hand-write a type that mirrors a backend model").
export type SignupRequest = components["schemas"]["SignupRequest"];
export type LoginRequest = components["schemas"]["LoginRequest"];
export type RefreshRequest = components["schemas"]["RefreshRequest"];
export type AuthTokenResponse = components["schemas"]["TokenResponse"];
export type CurrentUserResponse = components["schemas"]["UserResponse"];
