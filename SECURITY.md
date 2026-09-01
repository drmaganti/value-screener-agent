# Security

## Secrets and provider configuration

Never commit API keys, tokens or provider credentials.

Current configuration:

- `GEMINI_API_KEY` — required for Deep synthesis;
- `FRED_API_KEY` — optional macro evidence;
- `SEC_USER_AGENT` — not a secret, but should identify the deployed application/contact for responsible SEC automated access;
- `GEMINI_MODEL` — optional non-secret model override.

Use environment variables or the deployment platform's secret manager for keys. `.env` files containing real credentials must remain untracked.

## Data handled today

The Warren core currently needs only public ticker symbols and public market/fundamental/evidence data. It does not require user identity, brokerage credentials, holdings or transaction data.

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
- timeout/retry/circuit-breaker policy;
- dependency scanning;
- CORS configuration appropriate to intended clients.

## Financial-data and evidence integrity

Treat data integrity as a security/reliability concern:

- validate provider response types/units;
- preserve source and date/freshness metadata when supplied;
- preserve `source_status` failures instead of silently hiding them;
- never allow an LLM to overwrite source-of-truth numeric fields;
- never allow the LLM to claim unseen filing/article contents;
- record methodology/model/evidence versions for reproducibility as versioning is implemented;
- use official/primary endpoints where practical for filing metadata;
- respect upstream automated-access requirements and rate limits.

## Prompt injection from external evidence

Future full-text filings, earnings releases and news content should be treated as **untrusted data**, even when fetched from reputable sources. They must never be concatenated into prompts as executable instructions without explicit delimiting and instruction hierarchy.

Before full-text evidence is introduced:

- separate evidence content from system/developer instructions;
- strip or neutralize tool/instruction-like text where appropriate;
- prohibit evidence text from changing Warren's rules, tools or output schema;
- add prompt-injection eval fixtures.

Headline and structured-data evidence in v0.3 has a smaller attack surface, but the same principle applies.

## Vulnerability reporting

Until a dedicated security contact/process is established, do not publish sensitive vulnerability details in a public issue. Use a private repository/security reporting channel available to the project owner.
