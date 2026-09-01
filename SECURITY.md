# Security

## Secrets

Never commit API keys, tokens or provider credentials.

Current secret:

- `GEMINI_API_KEY` — required only for Deep mode.

Use environment variables or the deployment platform's secret manager. `.env` files containing real credentials must remain untracked.

## Data handled today

The Warren core currently needs only public ticker symbols and public market/fundamental data. It does not require user identity, brokerage credentials, holdings or transaction data.

Keep that boundary unless a future product requirement explicitly requires sensitive financial information.

## Future portfolio integrations

If Warren is later used with portfolios/watchlists tied to identifiable users:

- keep user identity outside the core analysis engine when possible;
- send only the minimum holdings/context needed;
- define retention/deletion rules;
- encrypt sensitive data at rest and in transit;
- document data residency and subprocessors;
- perform a privacy/security review before launch.

## API security before public deployment

The current API is a development interface. Before exposing it publicly add:

- authentication/authorization;
- rate limits and quotas;
- request-size limits at the edge;
- abuse protection;
- structured logging with secret redaction;
- timeout/retry policy;
- dependency scanning;
- CORS configuration appropriate to intended clients.

## Financial-data integrity

Treat data integrity as a security/reliability concern:

- validate provider response types/units;
- preserve source/freshness metadata;
- never allow an LLM to overwrite source-of-truth numeric fields;
- record methodology/model versions for reproducibility.

## Vulnerability reporting

Until a dedicated security contact/process is established, do not publish sensitive vulnerability details in a public issue. Use a private repository/security reporting channel available to the project owner.
