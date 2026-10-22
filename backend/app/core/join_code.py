import secrets

# Crockford Base32 drops I, L, O and U because they are easy to mix up when a code
# is read aloud. See docs/adr/0016-two-workspace-join-mechanisms.md.
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CODE_LENGTH = 8

_MISTYPED = str.maketrans({"O": "0", "I": "1", "L": "1"})


def generate_join_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def normalize_join_code(raw_code: str) -> str:
    cleaned = raw_code.replace("-", "").replace(" ", "").upper()

    return cleaned.translate(_MISTYPED)


def format_join_code(code: str) -> str:
    return f"{code[:4]}-{code[4:]}"
