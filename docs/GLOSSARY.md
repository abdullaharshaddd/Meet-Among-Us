# Glossary

Plain-English definitions, added the first time each term is used in code.

- **Connection pooler** — a proxy that sits in front of Postgres and hands out a small set of
  real database connections to many client requests, so the database itself doesn't have to
  open a connection per request.
- **Transaction pooling mode** — a pooler mode that hands out a database connection only for
  the length of one transaction, then takes it back — cheaper, but the connection you get can
  change between transactions.
- **Migration** — a versioned, scripted change to the database schema (e.g. "add this table"),
  so every environment ends up with the same schema by applying the same scripts in order.
- **Design token** — a named constant (a color, font, spacing value) used instead of a
  hardcoded literal, so the whole app can be restyled by editing one file.
