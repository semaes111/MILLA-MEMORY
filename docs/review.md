# Production Readiness Review — MemPalace v3.0.0

**Reviewer:** Automated Code Audit  
**Date:** April 7, 2026  
**Scope:** Security, reliability, correctness, architecture, testing, packaging

---

## CRITICAL Findings

### C-1. MCP Server passes arbitrary kwargs from untrusted LLM input to tool handlers

**Severity:** CRITICAL  
**File:** `mempalace/mcp_server.py` line ~6186  
**Category:** 1 — MCP Server Security

**Description:** The MCP dispatch code calls `TOOLS[tool_name]["handler"](**tool_args)` where `tool_args` comes directly from the LLM client's JSON arguments. There is zero validation that the provided keys match the handler's expected parameters. A malicious or confused LLM client could inject unexpected keyword arguments (e.g., `palace_path`, `db_path`) into any handler, potentially redirecting file operations.

**Impact:** Any tool handler that doesn't strictly validate its own parameters is exploitable. For example, `tool_search` delegates to `search_memories()` which accepts a `palace_path` parameter — if the LLM client passes `palace_path` as an extra argument, it bypasses the configured path. Similarly, `tool_kg_add` flows user strings directly into SQLite inserts — while parameterized, unexpected kwargs could cause `TypeError` crashes revealing internal implementation details.

**Suggested Fix:** Add an argument whitelist before dispatch:

```python
schema_props = TOOLS[tool_name]["input_schema"].get("properties", {})
filtered_args = {k: v for k, v in tool_args.items() if k in schema_props}
result = TOOLS[tool_name]["handler"](**filtered_args)
```

---

### C-2. Exception handler in MCP server leaks stack traces and internal paths to LLM clients

**Severity:** CRITICAL  
**File:** `mempalace/mcp_server.py` lines ~6192-6194  
**Category:** 1 — MCP Server Security

**Description:** When a tool handler raises an exception, the error is returned verbatim as `str(e)` in the JSON-RPC error message. Additionally, `tool_add_drawer`, `tool_delete_drawer`, and `tool_diary_write` all return `{"error": str(e)}` on failure. These error strings routinely contain full filesystem paths (`/home/username/.mempalace/...`), SQLite error messages with schema details, and ChromaDB internal errors.

**Impact:** Information disclosure to the LLM client. In a multi-user environment or if the MCP server is exposed over a network transport, this leaks the local username, directory structure, database schema, and ChromaDB version information.

**Suggested Fix:** Return generic error messages to the client and log the full exception server-side only:

```python
except Exception as e:
    logger.error(f"Tool error in {tool_name}: {e}", exc_info=True)
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": "Internal tool error"}}
```

---

### C-3. `sys.exit(1)` in searcher kills MCP server process

**Severity:** CRITICAL  
**File:** `mempalace/searcher.py` lines 8271, 8295  
**Category:** 6 — Error Handling

**Description:** The `search()` function calls `sys.exit(1)` on two error paths: when no palace is found and when a search error occurs. The MCP server's `tool_search` calls `search_memories()` (which returns dicts) rather than `search()`, so this specific path is safe. However, `tool_status` and other handlers rely on shared code paths that could import or call functions with `sys.exit()`. More critically, `miner.py:load_config()` (line ~6524) calls `sys.exit(1)` if no config is found, and `cli.py:cmd_compress()` (line ~671) also calls `sys.exit(1)`. If any of these are triggered transitively from an MCP tool call, the entire MCP server process terminates.

**Impact:** A single malformed tool call or missing configuration file terminates the MCP server, requiring manual restart. This is a DoS vector.

**Suggested Fix:** Replace all `sys.exit()` calls in library code with raised exceptions. Reserve `sys.exit()` for the CLI entry point only.

---

### C-4. TOCTOU race in `tool_add_drawer` duplicate check

**Severity:** CRITICAL  
**File:** `mempalace/mcp_server.py` lines 5716-5724  
**Category:** 7 — Concurrency

**Description:** `tool_add_drawer` performs a duplicate check via `tool_check_duplicate()` and then, if no duplicate is found, adds the drawer. These are two separate ChromaDB operations with no locking between them. If two concurrent MCP calls attempt to add the same content simultaneously, both may pass the duplicate check and both succeed in adding, resulting in duplicate entries.

Additionally, the drawer ID includes `datetime.now().isoformat()` in its hash — so two concurrent writes of identical content produce different IDs, making ChromaDB's own ID-based dedup useless.

**Impact:** Duplicate drawers accumulate over time, degrading search quality and inflating storage. The more aggressive the LLM client's save behavior, the worse this gets.

**Suggested Fix:** Derive drawer IDs deterministically from content hash (not timestamp), and use ChromaDB's `upsert` instead of `add`. Alternatively, implement a file-based lock around write operations.

---

## HIGH Findings

### H-1. Version mismatch: `__init__.py` says 2.0.0, `pyproject.toml` says 3.0.0

**Severity:** HIGH  
**File:** `mempalace/__init__.py` line 129, `pyproject.toml` line 63  
**Category:** 10 — Packaging

**Description:** The `__version__` in `__init__.py` is `"2.0.0"` while `pyproject.toml` declares version `"3.0.0"`. The MCP server's `initialize` response also returns version `"2.0.0"` (line ~6161). This means `mempalace.__version__` and `pip show mempalace` report different versions.

**Impact:** Users cannot reliably determine what version they're running. Bug reports reference wrong versions. Dependency resolution may behave unexpectedly.

**Suggested Fix:** Use a single source of truth — either read `pyproject.toml` dynamically or use a `__version__` in `__init__.py` that's kept in sync (consider `importlib.metadata.version`).

---

### H-2. ChromaDB dependency range `>=0.4.0,<1` is dangerously wide

**Severity:** HIGH  
**File:** `pyproject.toml` line 88  
**Category:** 10 — Packaging

**Description:** ChromaDB had major breaking API changes between 0.4.x and 0.5.x (migration to new client API, collection creation semantics changed). The code uses `PersistentClient` which was only introduced in 0.4.x, but the `get_or_create_collection` and `get_collection` semantics changed in later versions. Specifically, `get_collection` raises `ValueError` in some versions and `InvalidCollectionException` in others, and the code catches bare `Exception` everywhere to paper over this.

**Impact:** Installing with different ChromaDB versions produces silent behavior differences. Data created with one version may not be readable by another. Users who upgrade ChromaDB may find their palace corrupted without warning.

**Suggested Fix:** Pin to a tested range, e.g., `chromadb>=0.5.0,<0.6`. Add CI testing against the min and max supported versions.

---

### H-3. `tool_status`, `tool_list_wings`, `tool_list_rooms`, and `tool_get_taxonomy` fetch ALL metadata into memory

**Severity:** HIGH  
**File:** `mempalace/mcp_server.py` lines 5528, 5585, 5601, 5618  
**Category:** 8 — Scalability

**Description:** Four MCP read tools call `col.get(include=["metadatas"])` with no `limit` parameter, retrieving every drawer's metadata into a Python list. ChromaDB's default `get()` returns all documents. For a palace with 100K drawers, this allocates hundreds of megabytes of metadata dicts per call.

The `status()` function in `miner.py` (line 6889) has the same problem but at least specifies `limit=10000` — though that truncates results silently.

**Impact:** Memory exhaustion and long response times proportional to palace size. A single `mempalace_status` call from the LLM client can OOM the server process.

**Suggested Fix:** Use ChromaDB's `count()` for totals. For wing/room breakdowns, maintain a lightweight SQLite metadata index that's updated on writes, rather than scanning all ChromaDB entries.

---

### H-4. `Layer1.generate()` fetches all drawers with no limit

**Severity:** HIGH  
**File:** `mempalace/layers.py` line 5048  
**Category:** 8 — Scalability

**Description:** `Layer1.generate()` calls `col.get(**kwargs)` with no limit, retrieving all drawers (or all drawers in a wing) into memory. It then sorts all of them by importance to pick the top 15. For a large palace, this is an O(n log n) sort on potentially hundreds of thousands of entries.

**Impact:** Wake-up calls become increasingly slow and memory-intensive as the palace grows.

**Suggested Fix:** Either maintain a pre-computed "top drawers" index, or at minimum use a heap-based selection (heapq.nlargest) and paginate ChromaDB reads.

---

### H-5. Bare `except Exception: pass` silently swallows errors throughout the codebase

**Severity:** HIGH  
**File:** Multiple files  
**Category:** 6 — Error Handling

**Description:** The following critical error paths are silently swallowed:

- `mcp_server.py` lines 5534, 5589, 5603, 5624: All metadata enumeration in read tools — if ChromaDB returns an error, the tool returns `{"wings": {}}` with no indication of failure.
- `miner.py` line 6643 (`file_already_mined`): Returns `False` on any error, meaning files that failed to check will be re-mined, potentially creating duplicates.
- `convo_miner.py` lines 1259, 1268, 1349: File normalization and collection errors silently skip files with no logging.
- `config.py` line 972: Corrupt config.json is silently ignored — the user gets default config with no warning.

**Impact:** Silent data corruption, silent re-processing, and debugging becomes extremely difficult because errors are invisible.

**Suggested Fix:** At minimum, log all caught exceptions at WARNING level. Return explicit error indicators from functions rather than silently returning default values.

---

### H-6. SQLite connections open per-operation without WAL mode — concurrent access will deadlock

**Severity:** HIGH  
**File:** `mempalace/knowledge_graph.py` line 4641  
**Category:** 7 — Concurrency

**Description:** `KnowledgeGraph._conn()` creates a new `sqlite3.connect()` on every operation. SQLite's default journal mode is `DELETE`, which uses exclusive locks for writes. When the MCP server and a CLI command (or hook) try to write to the knowledge graph simultaneously, one will get `SQLITE_BUSY` after the 10-second timeout.

Additionally, there's no connection pooling — each operation opens, executes, commits, and closes. This is both slow (repeated file opens) and race-prone (no transaction isolation between the check-and-write in `add_triple`).

**Impact:** Concurrent usage from hooks + MCP causes `OperationalError: database is locked`, potentially corrupting the knowledge graph.

**Suggested Fix:** Enable WAL mode (`PRAGMA journal_mode=WAL`) in `_init_db()`. Use a single connection per `KnowledgeGraph` instance with proper transaction boundaries.

---

### H-7. MD5 collision risk in drawer and triple IDs

**Severity:** HIGH  
**File:** `mcp_server.py` line 5724, `miner.py` line 6650, `knowledge_graph.py` line 4699  
**Category:** 5 — Data Integrity

**Description:** Three different ID generation schemes exist:

1. `miner.py:add_drawer()`: `MD5(source_file + chunk_index)[:16]` — 16 hex chars = 64 bits of entropy.
2. `mcp_server.py:tool_add_drawer()`: `MD5(content[:100] + timestamp)[:16]` — different scheme, same namespace.
3. `knowledge_graph.py:add_triple()`: `MD5(valid_from + now)[:8]` — only 8 hex chars = 32 bits of entropy.

For the knowledge graph with only 32 bits, the birthday paradox gives a 50% collision probability at ~65K triples. For drawers with 64 bits, collision probability reaches 50% at ~4 billion entries — less critical but the two different ID schemes mean the same content mined via CLI and via MCP gets different IDs, defeating deduplication.

**Impact:** Knowledge graph ID collisions cause `INSERT` failures (ID is PRIMARY KEY), silently dropping facts. Drawer ID inconsistency causes duplicate content when the same file is processed by both the CLI and MCP server.

**Suggested Fix:** Use a consistent, deterministic ID scheme: for drawers, hash the content itself (not metadata). For triples, increase hash length to at least 16 hex chars and include all triple components in the hash.

---

### H-8. No input validation or sanitization on MCP tool string parameters

**Severity:** HIGH  
**File:** `mempalace/mcp_server.py` — all tool handlers  
**Category:** 1 — MCP Server Security

**Description:** None of the MCP tool handlers validate their inputs. Specifically:

- `tool_add_drawer(wing, room, content)` — `wing` and `room` are stored directly in ChromaDB metadata. No length limits, no character validation. An LLM client could pass megabytes of data as a wing name.
- `tool_search(query, limit)` — `limit` has no upper bound. A malicious call with `limit=999999` fetches the entire database.
- `tool_diary_write(agent_name, entry)` — `agent_name` is used to construct `wing_agent_name` with only basic character replacement. Characters like `../` survive.
- `tool_kg_add(subject, predicate, object)` — all three are passed to SQLite after only stripping quotes/spaces. No length validation.

**Impact:** Unbounded resource consumption, potential for storing malformed data that breaks subsequent queries, and possible unexpected behavior from special characters in wing/room names used as ChromaDB `where` filter values.

**Suggested Fix:** Add input validation: max lengths (e.g., 256 chars for wing/room, 100KB for content), character whitelists for identifiers, and upper bounds on limit parameters.

---

## MEDIUM Findings

### M-1. Shell hooks use unquoted variables from JSON input

**Severity:** MEDIUM  
**File:** `hooks/mempal_save_hook.sh` lines 309-311, 325  
**Category:** 2 — Shell Injection

**Description:** `SESSION_ID`, `STOP_HOOK_ACTIVE`, and `TRANSCRIPT_PATH` are parsed from untrusted JSON via Python and then used in shell contexts. While `TRANSCRIPT_PATH` is used in a quoted context in the `python3 -` invocation (line 325: `sys.argv[1]`), `SESSION_ID` is interpolated into the log file path: `echo "..." >> "$STATE_DIR/hook.log"` and into the state file path: `LAST_SAVE_FILE="$STATE_DIR/${SESSION_ID}_last_save"`. If `SESSION_ID` contained path traversal characters (e.g., `../../etc/cron.d/evil`), the state file write could escape the state directory.

**Impact:** A malicious or corrupted JSON input from Claude Code could write files to arbitrary locations. In practice, Claude Code controls the JSON format, limiting real-world exploitability.

**Suggested Fix:** Sanitize `SESSION_ID` to alphanumeric + underscore: `SESSION_ID=$(echo "$SESSION_ID" | tr -cd 'a-zA-Z0-9_-')`.

---

### M-2. `_entity_id()` normalization is insufficient

**Severity:** MEDIUM  
**File:** `mempalace/knowledge_graph.py` line 4644  
**Category:** 3 — SQLite Knowledge Graph

**Description:** `_entity_id()` only strips spaces and single quotes: `name.lower().replace(" ", "_").replace("'", "")`. It doesn't handle double quotes, semicolons, newlines, null bytes, or Unicode normalization. While the SQL uses parameterized queries (safe from injection), two entity names that differ only in characters that aren't stripped (e.g., "O'Brien" vs "OBrien", or "café" vs "cafe") could produce unexpected collisions or mismatches.

**Impact:** Entity lookup failures for names with special characters. Potential ID collisions for similar-but-distinct entity names.

**Suggested Fix:** Apply full Unicode normalization (NFKC), strip all non-alphanumeric/underscore characters, and handle empty-string edge cases.

---

### M-3. `PersistentClient` is re-instantiated on every operation

**Severity:** MEDIUM  
**File:** `mempalace/mcp_server.py` line 5501, `searcher.py` lines 8266/8340, `layers.py` lines 5037/5133/5253  
**Category:** 4 — ChromaDB Reliability

**Description:** Every read or write operation creates a new `chromadb.PersistentClient(path=...)`. ChromaDB's `PersistentClient` loads metadata indexes from disk on initialization. For a large palace, this adds significant latency to every MCP tool call. Additionally, having multiple `PersistentClient` instances pointing to the same path simultaneously can cause file locking conflicts.

**Impact:** Slow response times for every MCP tool call. Potential for SQLite locking errors within ChromaDB's internal database when multiple clients are active.

**Suggested Fix:** Create a single `PersistentClient` at server startup and reuse it. Handle connection recovery on error.

---

### M-4. Chunk overlap creates duplicate content in search results

**Severity:** MEDIUM  
**File:** `mempalace/miner.py` lines 6311-6312, 6618  
**Category:** 5 — Data Integrity

**Description:** `chunk_text()` uses `CHUNK_OVERLAP=100` characters, meaning 100 characters appear in both the end of chunk N and the start of chunk N+1. When a user searches for text that appears in the overlapping region, both chunks are returned as separate results. There is no deduplication at query time.

**Impact:** Users see effectively duplicate search results for content in overlap regions, which degrades the perceived quality of search.

**Suggested Fix:** Add post-search deduplication based on source_file + chunk_index proximity, or use document-level IDs to filter overlapping results.

---

### M-5. `tool_diary_read` fetches ALL diary entries then slices in Python

**Severity:** MEDIUM  
**File:** `mempalace/mcp_server.py` lines 5863-5883  
**Category:** 8 — Scalability

**Description:** `tool_diary_read` fetches all diary entries matching a wing/room filter with no limit, sorts them all by timestamp in Python, then slices to `last_n`. For a prolific agent writing many diary entries, this loads everything into memory.

**Impact:** Increasing memory usage and latency as diary entries accumulate.

**Suggested Fix:** ChromaDB doesn't support server-side sorting, so consider storing diary entries in the SQLite knowledge graph instead, or maintaining a separate time-ordered index.

---

### M-6. `query_entity` uses hardcoded column indices for result parsing

**Severity:** MEDIUM  
**File:** `mempalace/knowledge_graph.py` lines 4758, 4766-4767  
**Category:** 3 — Correctness

**Description:** The query results are accessed by numeric index (e.g., `row[2]` for predicate, `row[10]` for obj_name, `row[4]` for valid_from). These indices depend on the exact column order of the `SELECT t.*, e.name as obj_name` query. If the schema is ever modified (add/remove a column), all these indices silently shift, returning wrong data from wrong columns.

**Impact:** Schema changes cause silent data corruption in query results — the wrong field is displayed as the predicate, object name, etc.

**Suggested Fix:** Use `sqlite3.Row` row factory or `cursor.description` for named access, or use explicit column lists instead of `SELECT *`.

---

### M-7. `_no_palace()` response includes `palace_path`, leaking filesystem info

**Severity:** MEDIUM  
**File:** `mempalace/mcp_server.py` lines 5510-5514  
**Category:** 1 — MCP Server Security

**Description:** When no palace is found, the error response includes `"palace_path": _config.palace_path` which reveals the user's home directory path (e.g., `/home/alice/.mempalace/palace`).

**Impact:** Username and filesystem layout disclosed to the LLM client.

**Suggested Fix:** Return a generic "palace not configured" message without the full path.

---

### M-8. GitignoreMatcher `_match_from_root` has exponential worst-case for pathological patterns

**Severity:** MEDIUM  
**File:** `mempalace/miner.py` lines 6415-6434  
**Category:** 5 — Correctness

**Description:** The recursive `matches()` function for `**` pattern matching has two recursive branches: `matches(path_index, pattern_index + 1) or matches(path_index + 1, pattern_index)`. For a pattern like `**/**/**/**/**` against a deep path, this is exponential in path depth — classic backtracking.

**Impact:** A `.gitignore` with multiple `**` patterns and a deep directory tree could cause the miner to hang during scanning.

**Suggested Fix:** Add memoization via `@functools.lru_cache` or convert to an iterative algorithm.

---

### M-9. `timeline()` without entity filter has a hard limit of 100 but does not communicate this

**Severity:** MEDIUM  
**File:** `mempalace/knowledge_graph.py` line 4849  
**Category:** 3 — Correctness

**Description:** When called without an entity filter, `timeline()` has a `LIMIT 100`. However, when called with an entity filter, there is no limit at all. The MCP tool `tool_kg_timeline` does not indicate to the caller that results may be truncated.

**Impact:** Users see a partial timeline without knowing results are incomplete. With an entity filter, a heavily-referenced entity could return thousands of facts.

**Suggested Fix:** Add explicit pagination support and return a `truncated: true` flag when the limit is hit.

---

### M-10. `tool_check_duplicate` similarity calculation assumes L2 distance

**Severity:** MEDIUM  
**File:** `mempalace/mcp_server.py` line 5654  
**Category:** 5 — Correctness

**Description:** The duplicate check computes similarity as `1 - dist` and compares against a threshold. This formula is only valid for ChromaDB's default L2 distance, where values are in [0, 2] for normalized embeddings. If the embedding model or distance function changes, this formula produces meaningless similarity scores. Additionally, L2 distances can exceed 1.0, making `1 - dist` negative.

**Impact:** False negatives in duplicate detection (duplicates slip through) or false positives (non-duplicates blocked) depending on the distance metric and embedding model.

**Suggested Fix:** Use cosine distance explicitly (`collection.query(..., include=["distances"])` with a cosine metric), or normalize scores based on the actual distance metric being used.

---

## LOW Findings

### L-1. Tests use `tempfile.mkdtemp()` without guaranteed cleanup

**Severity:** LOW  
**File:** `tests/test_config.py` lines 7982, 7989, 7997, 8004; `tests/test_convo_miner.py` line 8023  
**Category:** 9 — Testing

**Description:** Tests create temporary directories with `tempfile.mkdtemp()` and some perform manual `shutil.rmtree(tmpdir)` in a `finally` block. However, `test_config.py` never cleans up any of its temporary directories. `test_convo_miner.py` cleans up only in the happy path (line 8040), not if an assertion fails before the cleanup line.

**Impact:** Leftover temporary directories accumulate in the system's temp folder during test runs. ChromaDB locks may prevent cleanup of some directories.

**Suggested Fix:** Use pytest's `tmp_path` fixture throughout, which handles cleanup automatically.

---

### L-2. Zero test coverage for 80%+ of the codebase

**Severity:** LOW (in terms of immediate risk, but HIGH for long-term maintainability)  
**File:** `tests/`  
**Category:** 9 — Testing

**Description:** Only 4 test files exist covering config, miner (gitignore matching), convo_miner (basic smoke test), and normalize (basic format detection). There are zero tests for: MCP server protocol handling and tool dispatch, knowledge graph operations, search functionality, AAAK dialect compression, layer stack wake-up and L1 generation, entity detection/registry, hook scripts, palace graph traversal, split_mega_files, and spellcheck.

**Impact:** Any refactoring is high-risk. Regression bugs in core functionality (search, knowledge graph, MCP tools) will not be caught before release.

**Suggested Fix:** Prioritize tests for MCP server tools (the primary API surface) and knowledge graph operations (data integrity). Use pytest fixtures to create isolated palace instances.

---

### L-3. `test_env_override` modifies global environment without isolation

**Severity:** LOW  
**File:** `tests/test_config.py` lines 7996-7999  
**Category:** 9 — Testing

**Description:** `test_env_override()` sets `os.environ["MEMPALACE_PALACE_PATH"]` and deletes it afterwards. If the test fails before the `del` line, the env var leaks to subsequent tests. This can cause cascading test failures.

**Impact:** Flaky test suite when test order changes.

**Suggested Fix:** Use `monkeypatch.setenv()` or `unittest.mock.patch.dict(os.environ, ...)`.

---

### L-4. Module-level singletons `_config` and `_kg` initialized at import time

**Severity:** LOW  
**File:** `mempalace/mcp_server.py` lines 5490, 5495  
**Category:** 8 — Architecture

**Description:** `_kg = KnowledgeGraph()` and `_config = MempalaceConfig()` are created when the module is first imported. This means the database path and config are locked in at import time. If the user changes `~/.mempalace/config.json` or sets environment variables after the server starts, the changes are not reflected until the server is restarted.

**Impact:** Configuration changes require an MCP server restart, which is confusing for users who expect config changes to take effect immediately.

**Suggested Fix:** Document this behavior. Optionally, add a `mempalace_reload_config` tool, or lazily initialize on first use.

---

### L-5. `dialect.py` at 32KB is a low-cohesion monolith

**Severity:** LOW  
**File:** `mempalace/dialect.py`  
**Category:** 8 — Architecture

**Description:** `dialect.py` is the largest source file and contains: emotion code mappings, entity code management, compression algorithms, the Zettel format specification, decompression logic, and statistics calculation. Many of these are independent concerns.

**Impact:** Difficult to test, maintain, and extend individual compression features.

**Suggested Fix:** Split into `dialect/emotions.py`, `dialect/compression.py`, `dialect/entities.py`, and `dialect/zettel.py`.

---

### L-6. `KNOWN_PEOPLE` default list is hardcoded with specific names

**Severity:** LOW  
**File:** `mempalace/split_mega_files.py` line 8722  
**Category:** 5 — Correctness

**Description:** The fallback `KNOWN_PEOPLE` list is `["Alice", "Ben", "Riley", "Max", "Sam", "Devon", "Jordan"]` — these are clearly the developer's personal contacts. Any user who doesn't configure `known_names.json` will have person detection biased toward these specific names.

**Impact:** False positive person detection for unrelated users whose conversations happen to mention common names like "Max" or "Sam."

**Suggested Fix:** Default to an empty list. Require explicit configuration via `mempalace init`.

---

### L-7. `spellcheck.py` depends on optional `autocorrect` package not declared in dependencies

**Severity:** LOW  
**File:** `mempalace/spellcheck.py` lines 8431-8441  
**Category:** 10 — Packaging

**Description:** The `spellcheck` module lazy-loads `autocorrect` with a try/except. If it's not installed, spellcheck silently does nothing. However, `autocorrect` is not listed in `pyproject.toml` dependencies or optional-dependencies. Users who want spellchecking have no way to know they need to install it.

**Impact:** Feature silently unavailable unless the user independently discovers the dependency.

**Suggested Fix:** Add `autocorrect` to `[project.optional-dependencies]` (e.g., `spellcheck = ["autocorrect>=2.0"]`) and document it.

---

### L-8. Python 3.9 compatibility not verified — potential for 3.10+ syntax

**Severity:** LOW  
**File:** `pyproject.toml` line 66  
**Category:** 10 — Packaging

**Description:** The project claims `requires-python = ">=3.9"` and lists Python 3.9 in classifiers. A grep through the code shows no `match/case` statements or `X | Y` union type syntax, so the code appears 3.9-compatible. However, there is no CI matrix testing against 3.9.

**Impact:** If a contributor introduces 3.10+ syntax, it won't be caught until a 3.9 user reports a `SyntaxError`.

**Suggested Fix:** Add a CI job testing against Python 3.9.

---

## Summary Table

| Severity  | Count  |
| --------- | ------ |
| CRITICAL  | 4      |
| HIGH      | 8      |
| MEDIUM    | 10     |
| LOW       | 8      |
| **Total** | **30** |

---

## Top 5 Issues Requiring Immediate Attention

1. **C-1: Unvalidated kwargs dispatch in MCP server** — The primary API surface has zero input validation, allowing arbitrary parameter injection from untrusted LLM clients. Fix with argument whitelisting.

2. **C-4: TOCTOU race in duplicate check** — The most common write path (tool_add_drawer) has a race condition that guarantees duplicate content in any concurrent usage scenario. Fix by using deterministic content-based IDs and upsert.

3. **C-3: `sys.exit()` in library code** — Multiple code paths can terminate the MCP server process. A single broken config file kills the entire memory system. Fix by converting all `sys.exit()` to exceptions.

4. **H-3/H-4: Unbounded metadata fetches** — Five tool handlers and the Layer1 generator fetch ALL data into memory with no limits. A palace with >10K drawers will cause noticeable latency; >100K will OOM. Fix with pagination and pre-computed indexes.

5. **H-6: SQLite concurrency without WAL** — The knowledge graph cannot handle concurrent writes from hooks + MCP, which is the primary use case. Fix by enabling WAL mode and using persistent connections.

---

## Overall Assessment

**Verdict: DO NOT DEPLOY (as-is for production; acceptable for personal/experimental use with caveats)**

MemPalace v3.0.0 has fundamental issues in its primary API surface (the MCP server) that make it unsuitable for production deployment where reliability matters. The combination of unvalidated inputs, process-killing error paths, unbounded memory usage, and race conditions means the server can be crashed, OOM'd, or corrupted by normal usage patterns — not just adversarial ones.

For personal use on a single machine with a small-to-medium palace (<5K drawers), the system will work acceptably with occasional quirks. The core design (ChromaDB for vectors, SQLite for knowledge graph, spatial metaphor for organization) is sound.

**Recommended path to production readiness:**

1. Fix all CRITICAL findings (estimated: 1-2 days)
2. Fix HIGH findings H-3, H-6, H-7, H-8 (estimated: 2-3 days)
3. Add basic MCP server test coverage (estimated: 2-3 days)
4. Pin ChromaDB dependency to a tested range (estimated: 1 day)
5. Run a stress test with 50K+ drawers to validate scalability fixes

---

## Positive Highlights

The codebase does several things well that should be preserved:

- **Parameterized SQL throughout the knowledge graph.** Despite the other issues, `knowledge_graph.py` uses parameterized queries (`?` placeholders) consistently — there is no string interpolation in SQL. This is the correct approach and should be maintained.

- **Clean separation between CLI and library code.** The `searcher.py` module provides both `search()` (CLI, prints to stdout) and `search_memories()` (library, returns dicts). This dual-interface pattern is good API design.

- **Comprehensive gitignore implementation with thorough tests.** The `GitignoreMatcher` class handles anchored patterns, negation, directory-only rules, and nested `.gitignore` files. The 12 test cases in `test_miner.py` cover real-world edge cases including negation of ignored directories — this is the best-tested part of the codebase.

- **Thoughtful hook design.** The save hook's infinite-loop prevention (checking `stop_hook_active` before blocking again) and the precompact hook's design as a safety net are both well-conceived patterns for the Claude Code integration.

- **Zero mandatory cloud dependencies.** The local-first architecture using ChromaDB and SQLite means the system works offline with no API keys, subscriptions, or data leaving the user's machine. This is a strong differentiator.

- **Deterministic drawer IDs in `miner.py`.** The CLI miner uses `MD5(source_file + chunk_index)` which is deterministic — re-running the miner on the same files produces the same IDs, naturally preventing duplicates via ChromaDB's ID uniqueness constraint. The MCP server should adopt this pattern.

---

## Supplemental Findings (Part 2)

The following findings cover modules not addressed in the initial pass: `normalize.py`, `entity_detector.py`, `onboarding.py`, `palace_graph.py`, `room_detector_local.py`, and the README.

### S-1. `palace_graph.build_graph()` rebuilds the entire graph on every traversal call

**Severity:** MEDIUM  
**File:** `mempalace/palace_graph.py` lines 7725-7788, 7791, 7853, 7885  
**Category:** 8 — Architecture & Scalability

**Description:** `traverse()`, `find_tunnels()`, and `graph_stats()` all call `build_graph()` which iterates over every drawer in batches of 1000 to construct the node/edge data structure from scratch. There is no caching. A single MCP call to `mempalace_traverse` followed by `mempalace_find_tunnels` builds the graph twice.

**Impact:** For a palace with 50K drawers, each graph operation requires 50 ChromaDB batch reads and Python dict construction. Three graph tool calls in sequence = 150 ChromaDB reads for the same immutable data.

**Suggested Fix:** Cache the graph structure with a simple invalidation flag (set on drawer writes). Or compute the graph once per MCP server lifecycle and expose a `mempalace_refresh_graph` tool.

---

### S-2. `traverse()` BFS visits every room sharing a wing — combinatorial explosion

**Severity:** MEDIUM  
**File:** `mempalace/palace_graph.py` lines 7819-7850  
**Category:** 5 — Correctness

**Description:** The BFS traversal at each hop finds "all rooms that share a wing with the current room." In a large palace where most rooms are in a common wing (e.g., `wing_user`), the first hop returns every room in that wing. The second hop then checks every room against every other room's wings. This is effectively O(n²) where n is the number of rooms.

The `results[:50]` cap (line 7850) prevents unbounded output, but the computation still occurs.

**Impact:** Traversal of a large palace with a heavily-populated wing may take seconds instead of milliseconds.

**Suggested Fix:** Add a per-hop result limit and break early. Consider limiting traversal to rooms sharing the same specific wing rather than any wing.

---

### S-3. `normalize.py` applies spellcheck to user messages by default — mutating verbatim content

**Severity:** MEDIUM  
**File:** `mempalace/normalize.py` lines 7143-7162  
**Category:** 5 — Data Integrity

**Description:** `_messages_to_transcript()` defaults to `spellcheck=True` and calls `spellcheck_user_text()` on every user message before storing it. This directly contradicts the project's core design principle: "store verbatim text, never summarized." Spellchecking mutates user messages, potentially changing technical terms, proper nouns, or intentional unconventional spelling. The miner's README says "Stores verbatim chunks as drawers. No summaries. Ever." — but the normalize step silently alters the text before it reaches the miner.

**Impact:** Users who mine conversation exports find their original words altered. Technical terms, names not in the dictionary, and deliberate informal text are silently "corrected." This is especially problematic for code-heavy conversations where variable names might be spell-corrected.

**Suggested Fix:** Default `spellcheck=False`. Let users opt in via a `--spellcheck` CLI flag.

---

### S-4. Slack normalizer assigns roles based on arrival order, not actual identity

**Severity:** LOW  
**File:** `mempalace/normalize.py` lines 7093-7123  
**Category:** 5 — Correctness

**Description:** The Slack JSON parser assigns "user" and "assistant" roles by alternating based on the order speakers are first seen. In a channel with 3+ people, the third speaker gets whatever role is opposite the second speaker. This means person C is labeled "user" even though they're a different person from person A (also labeled "user"). The exchange-pair chunking then merges person A and person C's messages into the same speaker's "user turns."

**Impact:** Multi-person Slack conversations have incorrect speaker attribution, causing the chunking to blend different people's messages. Search results may attribute statements to the wrong person.

**Suggested Fix:** Use actual Slack user IDs as speaker identifiers rather than forcing into a user/assistant binary. Or at minimum, label each turn with the original user ID in metadata.

---

### S-5. `entity_detector.py` correctly uses `re.escape()` but has quadratic scan complexity

**Severity:** LOW  
**File:** `mempalace/entity_detector.py` lines 2979-2993  
**Category:** 8 — Architecture

**Description:** `_build_patterns(name)` correctly escapes entity names with `re.escape(name)` before building regex patterns — good. However, `detect_entities()` calls `score_entity()` for every candidate against the entire text corpus. Each `score_entity()` compiles ~30 regex patterns and runs `findall()` on the full text for each. For 100 candidates against a 1MB corpus, this is ~3000 full-text regex scans.

**Impact:** The `mempalace init` command may be slow on large file collections with many proper noun candidates.

**Suggested Fix:** Pre-compile patterns in batch and use a single-pass approach, or limit text corpus size for scoring.

---

### S-6. `room_detector_local.py` and `detect_rooms_local()` call `sys.exit(1)` from library code

**Severity:** LOW  
**File:** `mempalace/room_detector_local.py` line 8211  
**Category:** 6 — Error Handling

**Description:** `detect_rooms_local()` calls `sys.exit(1)` if the project directory doesn't exist. This function is called from `cmd_init()` in `cli.py`. If it were ever called from the MCP server or programmatically, it would terminate the process.

**Impact:** Currently only reachable from CLI, so low immediate risk. But it's the same anti-pattern as C-3.

**Suggested Fix:** Raise `FileNotFoundError` instead of `sys.exit(1)`.

---

### S-7. README "+34% palace boost" claim is still present in the body despite being acknowledged as misleading

**Severity:** LOW  
**File:** `README.md` lines 393-401  
**Category:** Documentation

**Description:** The maintainers' note (line 203) acknowledges that the "+34% palace boost" is misleading because it's standard ChromaDB metadata filtering. However, the claim is still present in the body of the README at lines 393-401:

```
Search all closets:          60.9%  R@10
Search within wing:          73.1%  (+12%)
Search wing + hall:          84.8%  (+24%)
Search wing + room:          94.8%  (+34%)
```

followed by "Wings and rooms aren't cosmetic. They're a **34% retrieval improvement**."

**Impact:** Users who don't read the note will still see the misleading claim as if it's a novel feature rather than standard metadata filtering.

**Suggested Fix:** Reframe the comparison to clearly state this is the benefit of metadata filtering (which any vector store supports) and not a novel algorithm.

---

### S-8. `SKIP_DIRS` set is duplicated in 5 separate files with slight variations

**Severity:** LOW  
**File:** `miner.py`, `convo_miner.py`, `entity_detector.py`, `room_detector_local.py` (2×)  
**Category:** 8 — Architecture

**Description:** The set of directories to skip during scanning is defined independently in five places:

- `miner.py`: 20 entries (includes `.ruff_cache`, `.mypy_cache`, etc.)
- `convo_miner.py`: 10 entries (includes `tool-results`, `memory`)
- `entity_detector.py`: 11 entries
- `room_detector_local.py`: defined twice (line 8033 and 8103), 10 and 7 entries respectively

Each copy has different entries. For example, `tool-results` and `memory` only appear in `convo_miner.py`. `.ruff_cache` only appears in `miner.py`.

**Impact:** Inconsistent skip behavior across different commands. Adding a new directory to skip requires changes in 5 places.

**Suggested Fix:** Define a canonical `SKIP_DIRS` in `config.py` and import it everywhere.

---

### S-9. `onboarding.py` has an interactive input loop with no timeout or EOF handling

**Severity:** LOW  
**File:** `mempalace/onboarding.py` lines 7299-7307, 7329-7341  
**Category:** 6 — Error Handling

**Description:** The onboarding flow uses raw `input()` calls in `while True` loops. If stdin is closed (e.g., the script is piped from a non-interactive source), `input()` raises `EOFError` which will crash the process with a traceback. The `--yes` flag on `mempalace init` bypasses approval but not the onboarding flow itself.

**Impact:** Non-interactive use (CI, scripts, testing) crashes with unhelpful errors.

**Suggested Fix:** Wrap `input()` calls with `EOFError` handling that gracefully exits or falls back to defaults.

---

### Updated Summary Table

| Severity  | Initial | Supplemental | Total  |
| --------- | ------- | ------------ | ------ |
| CRITICAL  | 4       | 0            | **4**  |
| HIGH      | 8       | 0            | **8**  |
| MEDIUM    | 10      | 3            | **13** |
| LOW       | 8       | 6            | **14** |
| **Total** | **30**  | **9**        | **39** |
