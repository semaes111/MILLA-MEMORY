# Data classification and storage policy

| Class | Typical content | Git policy |
|---|---|---|
| Public | Published articles, public company facts | Wiki and pointer allowed |
| Internal | Non-public project notes without regulated data | Minimized wiki and pointer allowed |
| Confidential | Contracts, strategy, unpublished finance | Pseudonymized synthesis only; original external |
| Restricted | Identified health data, privileged legal files, credentials, tax identity data | No original; minimal opaque pointer only |

## Mandatory controls

- Keep restricted originals encrypted and segregated by domain.
- Use least-privilege access and log reads and writes at the storage layer.
- Never put passwords, access tokens, private keys, recovery codes, or full identity numbers in the
  wiki or source pointers.
- Pseudonymize people and matters unless identity is essential to the query.
- Treat deletion from the current branch as non-erasure because Git retains history.
- Escalate a suspected secret or regulated-data leak before further ingestion.
