// EXPO_PUBLIC_* vars are inlined at build time by Expo's Metro config — no
// extra package needed. Falls back to localhost for the web/simulator dev
// loop; a physical device needs a LAN IP or tunnel — see Task 4 setup.
export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8001";

// Same value as backend/.env's google_client_id_web — not a secret, it's
// the audience Google mints the ID token for. GoogleSignInButton.native.tsx
// passes this as `serverClientId` so the token verifies against the backend.
export const GOOGLE_CLIENT_ID_WEB = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID_WEB ?? "";
