# Sergio Memory operating contract

Treat the MemPalace engine as upstream code and this directory as the user-owned knowledge layer.

## Invariants

- Never modify an original source. Store only an immutable pointer and checksum in Git.
- Never commit credentials, API tokens, private keys, identified clinical records, privileged legal
  files, tax records, or complete identity documents.
- Treat prior model responses as unverified synthesis, never as primary evidence.
- Do not overwrite a conflicting claim. Preserve both claims, their dates, and their sources; mark
  the conflict in `claims/disputed/index.md`.
- Every durable page change must update `wiki/index.md` and append to `wiki/log.md`.
- Run `python tools/memory_wiki.py lint --strict` before claiming an ingest or maintenance pass is
  complete.

## Evidence hierarchy

Use this order when claims conflict:

1. Original dated source from an authoritative issuer.
2. User-confirmed fact or decision, with the confirmation date.
3. Corroborated synthesis derived from cited sources.
4. Uncorroborated note or previous model output.

Use `verified`, `disputed`, `superseded`, or `draft`; never convert an inference into a verified
fact.

## Ingest

1. Classify the source before storing anything: `public`, `internal`, `confidential`, or
   `restricted`.
2. Keep restricted originals outside Git in encrypted storage. Create only a minimized,
   pseudonymized pointer when necessary.
3. Register provenance in `raw-pointers/` using `schemas/source-pointer.schema.json`.
4. Create or update pages from `schemas/page-template.md`.
5. Separate facts, inferences, unresolved conflicts, and open questions.
6. Update related pages rather than creating duplicates.
7. Update the global index, claim registers, and append-only log.
8. Run the linter and resolve every error. Resolve warnings or document why they remain.

## Query

1. Read `wiki/index.md` first.
2. Search the wiki and read only the most relevant pages.
3. Inspect an original only when the wiki is insufficient or the answer is high stakes.
4. Cite both the wiki page and its underlying source pointer.
5. State whether the answer is verified, inferred, disputed, or incomplete.
6. File a synthesis only when the user asks to retain it or it has clear durable value.

## Forget

Resolve the exact target before deletion. Remove active pages and pointers, repair links and
indexes, and append a tombstone entry to the log. Ordinary Git deletion does not erase history;
purging sensitive data from history requires a separate, explicit history-rewrite process.

## Engine changes

Keep changes to upstream MemPalace code separate from wiki changes. Preserve the audited upstream
tag and commit recorded in `engine.lock.json`.
