import { useState } from "react";

// Shows `validate`'s result only after the field has been touched once, so
// a blank field doesn't show "required" before anyone's typed anything —
// but updates live on every keystroke after that first blur. No form
// library: two three-field forms don't justify one — see
// docs/adr/0008-hand-rolled-form-validation.md.
export function useValidatedField(validate: (value: string) => string | undefined) {
  const [value, setValue] = useState("");
  const [touched, setTouched] = useState(false);

  return {
    value,
    setValue,
    error: touched ? validate(value) : undefined,
    onBlur: () => setTouched(true),
  };
}

export const validators = {
  email: (value: string) => (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? undefined : "Enter a valid email address."),
  password: (value: string) => (value.length >= 8 ? undefined : "At least 8 characters."),
  displayName: (value: string) => (value.trim().length >= 2 ? undefined : "Enter your name."),
};
