# Security policy

Bug Laws is a local, read-only history scanner. It can inspect sensitive
content already present in Git patches, so treat generated reports as
potentially sensitive until reviewed.

- Do not commit tokens, credentials, private URLs, or unredacted secrets in
  reports or fixtures.
- `scan` does not read Git credentials, cookies, environment secrets, or write
  to the scanned repository.
- `enrich` is opt-in, uses public GitHub endpoints, and writes a separate
  output file. It does not require a token.
- Report and review artifacts must be checked for local paths and sensitive
  patch content before publication.

Report vulnerabilities privately to the repository owner with reproduction
steps and the smallest safe evidence sample. Do not include live credentials.
