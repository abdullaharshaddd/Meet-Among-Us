import { ApiError } from "./client";

// Names the specific situation instead of a generic apology — "wrong
// password," "email already registered," and "no network" are three
// different problems and the user should be told which.
export function loginErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "Incorrect email or password.";
    return `The server had a problem signing you in (${error.status}). Try again in a moment.`;
  }
  return "Can't reach the server. Check your connection and try again.";
}

export function signupErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 409) return "An account with this email already exists — sign in instead.";
    return `The server had a problem creating your account (${error.status}). Try again in a moment.`;
  }
  return "Can't reach the server. Check your connection and try again.";
}
