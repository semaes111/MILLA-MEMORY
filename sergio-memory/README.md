# Sergio Memory

Persistent, source-aware memory built from two complementary layers:

- MemPalace stores and retrieves verbatim local material through its MCP server.
- This wiki stores maintained synthesis, cross-references, decisions, claim state, and provenance.

The context window remains finite. The system behaves as long-term memory by retrieving only the
relevant pages and source excerpts for each task.

## Safety boundary

Git contains the wiki, schemas, decisions, and minimized source pointers. Sensitive originals stay
in encrypted, access-controlled storage outside Git. A private repository is not a substitute for
clinical, legal, fiscal, or credential-grade secret storage.

## Main operations

```bash
python tools/memory_wiki.py status
python tools/memory_wiki.py query "avatar diario arquitectura"
python tools/memory_wiki.py lint --strict
```

Ingestion and synthesis are agent-maintained operations governed by `sergio-memory/AGENTS.md`. The
deterministic tool validates and searches the resulting wiki; it does not manufacture evidence or
summarize sources by itself.
