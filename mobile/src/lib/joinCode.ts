// Workspace join codes are 8 characters, shown as XXXX-XXXX and stored without the dash.
const CODE_LENGTH = 8;
const GROUP = 4;

export function cleanJoinCode(raw: string): string {
  return raw.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, CODE_LENGTH);
}

export function formatJoinCode(code: string): string {
  const clean = cleanJoinCode(code);

  return clean.length > GROUP ? `${clean.slice(0, GROUP)}-${clean.slice(GROUP)}` : clean;
}

export function isCompleteJoinCode(code: string): boolean {
  return cleanJoinCode(code).length === CODE_LENGTH;
}
