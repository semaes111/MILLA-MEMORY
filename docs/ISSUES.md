# MemPalace Issue Tracker

> Synced from [milla-jovovich/mempalace](https://github.com/milla-jovovich/mempalace/issues) on 2026-04-10
> Total: **155 open issues**, **192 open PRs**

## Sync Delta (2026-04-09 → 2026-04-10)

| Metric | Previous | Current | Change |
|---|---|---|---|
| Open issues | 92 | 155 | **+63** |
| Open PRs | 132 | 192 | **+60** |
| Closed issues (rolling 2wk) | 33 | 75 | **+42** |

**Notable:** A large wave of new issues landed today (#467–#541), many from new reporters (`krugdenis`, `jphein`, `nautis`, `nanoscopic`). Several high-severity stability bugs filed today are still **unlabeled** — see the "Bugs — Unlabeled" section below.

Previously-tracked items closed since 2026-04-09: #394, #296, #290, #214, #209, #186, #180, #179, #163, #105, #47, #345, #267, #257, #253, #250, #249, #248, #241, #233, #228, #227, #374, #375, #407, #443, #457, #460, #472.

---

## CRITICAL / SECURITY (Open)

Hand-picked by severity (crash, data-loss, corruption, security) regardless of label state.

| # | Title | Labels | PR |
|---|---|---|---|
| **538** | MCP server stdio transport: `add_drawer` and `kg_add` write to WAL but not to ChromaDB/SQLite | bug | — |
| **526** | MCP tools `diary_write` and `kg_add` return internal error -32000 | bug | — |
| **525** | HNSW `link_lists.bin` grows to terabytes, causes segfault and APFS orphaned blocks on macOS | — | — |
| **521** | hnswlib `updatePoint` race on modified-file re-mine: EXC_BAD_ACCESS in `repairConnectionsForUpdate` (macOS ARM64, Python 3.13, chromadb 0.6.3) | — | — |
| **503** | MCP server fails with surrogate error on Windows when writing CJK content | — | — |
| **487** | `chromadb<0.7` pin breaks MCP server on Python 3.14 | — | — |
| **479** | Duplicate `_client_cache`/`_collection_cache` declarations reset state in `mcp_server.py` | — | — |
| **477** | MCP `tool_search` has no upper bound on `limit` parameter — potential memory exhaustion | — | — |
| **475** | Float mtime comparison breaks file deduplication — every file re-mined on each run | — | — |
| **469** | Palace data gone after upgrade to v3.1.0 | bug | — |
| **445** | v3.1.0 ChromaDB pin breaks existing palace created with Chroma 1.x | — | — |
| **444** | Global palace is a single point of failure — one corrupted project destroys all data | — | — |
| 397 | ARM64 segfault mitigation is a no-op — `ORT_DISABLE_COREML` is not a real ONNX RT env var | — | — |
| 396 | OOM crash on large transcript files — `split_mega_files.py` and `normalize.py` load entire file | — | — |
| 395 | `cmd_repair` infinite recursion when palace_path has trailing slash — fills disk | — | — |
| 357 | Parallel mining corrupts ChromaDB HNSW index — no warning, silent failure | — | — |
| 344 | HNSW index bloat: `link_lists.bin` grows to 441GB when mining >10K drawers | — | #346 |
| 339 | Silent `except Exception: pass` in MCP tools hides errors from callers | bug | #371 |
| 333 | System prompt context prepended to queries drops retrieval from 89.8% to 1.0% | — | — |
| 326 | mempalace.tech serving malicious JavaScript — ad injection and redirect chain | bug | — |

---

## BUGS — Labeled `bug` (Open, 26)

| # | Title | Author | Filed |
|---|---|---|---|
| 541 | Contributing page mentions discussions | nanoscopic | 2026-04-10 |
| 538 | MCP server stdio transport: `add_drawer` and `kg_add` write to WAL but not to ChromaDB/SQLite | duha887b | 2026-04-10 |
| 531 | README chromadb version differs from actual | nanoscopic | 2026-04-10 |
| 526 | MCP tools `diary_write` and `kg_add` return internal error -32000 | bmaltais | 2026-04-10 |
| 524 | "Remove Baldfaced Lies Please" (README/claims discrepancy) | nanoscopic | 2026-04-10 |
| 469 | Palace data gone after upgrade to v3.1.0 | R0uter | 2026-04-10 |
| 412 | Discord link impossible to verify | CodeAKrome | 2026-04-09 |
| 411 | `mine` step not clear, unrelated results found | jchronowski | 2026-04-09 |
| 404 | `detect_room` called with empty content in `miner.py` — patch proposed | gai095481 | 2026-04-09 |
| 378 | Windows: `plugin.json` and hook scripts use `python3` — no Windows-compatible hooks | JefffromNJ | 2026-04-09 |
| 377 | Hook scripts call `mempalace hook run` command that doesn't exist in PyPI v3.0.0 | JefffromNJ | 2026-04-09 |
| 368 | `mempalace plugin install` fails | jerrythomas | 2026-04-09 |
| 359 | `json.dumps(response)` does not set `ensure_ascii=False` | janzwang666555 | 2026-04-09 |
| 347 | Codex hook message counting does not match Codex transcript schema | xiaomayi-ant | 2026-04-09 |
| 339 | Silent `except Exception: pass` in MCP tools hides errors from callers | wuxiwei | 2026-04-09 |
| 330 | ChatGPT mapping imports can silently ingest the wrong branch | GaosCode | 2026-04-09 |
| 326 | mempalace.tech serving malicious JavaScript — ad injection and redirect chain | nhumphreys | 2026-04-09 |
| 303 | Split command fails with all argument formats on Windows 11 | JefffromNJ | 2026-04-08 |
| 284 | `pip install` requires `--break-system-packages` | flundstrom2 | 2026-04-08 |
| 263 | Website quiz results don't show UTF-8 check mark | cm-tramcase | 2026-04-08 |
| 247 | `mempalace_check_duplicate` misses existing text at default threshold 0.9 | lzhuojun251 | 2026-04-08 |
| 210 | Init in documentation has no dir, but it is required | scottp | 2026-04-08 |
| 159 | Bugs and improvements (omnibus) | cktang88 | 2026-04-07 |
| 27 | Multiple issues between README claims and codebase | lhl | 2026-04-07 |
| 19 | Super slow mine on Windows | idanf-glbe | 2026-04-07 |
| 14 | Setup is throwing an error | neocybereth | 2026-04-07 |

---

## BUGS — Unlabeled but clearly bugs (Open)

These are filed without the `bug` label but are unambiguous defects. Upstream labeling has fallen behind.

| # | Title | Author | Filed |
|---|---|---|---|
| 536 | `--extract general` dumps Markdown-bold content into `emotional` room via overly broad `\*[^*]+\*` regex | krugdenis | 2026-04-10 |
| 535 | `UnicodeEncodeError` in miner/convo_miner/split_mega_files on Windows cp1251/cp1252 (incomplete fix of #47) | krugdenis | 2026-04-10 |
| 534 | `SKILL.md` uses nonexistent `mempalace --version`; init instructions omit `--yes` so agents hit `EOFError` | krugdenis | 2026-04-10 |
| 525 | HNSW `link_lists.bin` grows to terabytes, causes segfault + APFS orphaned blocks on macOS | swesty | 2026-04-10 |
| 521 | hnswlib `updatePoint` race on re-mine: EXC_BAD_ACCESS (macOS ARM64, Python 3.13) | StefanKremen | 2026-04-10 |
| 504 | Add lock/kill-switch guidance for autosave and MCP hook wrappers | vanachterjacob | 2026-04-10 |
| 503 | MCP server fails with surrogate error on Windows when writing CJK content | wangjisong000 | 2026-04-10 |
| 487 | `chromadb<0.7` pin breaks MCP server on Python 3.14 | director-LAC | 2026-04-10 |
| 479 | Duplicate `_client_cache`/`_collection_cache` declarations reset state in `mcp_server.py` | jphein | 2026-04-10 |
| 478 | Status/taxonomy MCP tools silently truncate at 10,000 drawers — wrong counts for large palaces | jphein | 2026-04-10 |
| 477 | MCP `tool_search` has no upper bound on `limit` parameter — potential memory exhaustion | jphein | 2026-04-10 |
| 476 | Entity detector flags common code terms as projects (Handler, Node, One, Service) | jphein | 2026-04-10 |
| 475 | Float mtime comparison breaks file deduplication — every file re-mined on each run | jphein | 2026-04-10 |
| 448 | Add backup command + auto-backup before mine to prevent data loss | — | 2026-04-09 |
| 445 | v3.1.0 ChromaDB pin breaks existing palace created with Chroma 1.x | — | 2026-04-09 |
| 444 | Global palace is a single point of failure — one corrupted project destroys all data | — | 2026-04-09 |
| 408 | Plugin assumes `python3 -m mempalace` — breaks on modern Linux (PEP 668) and with uv/pipx | — | 2026-04-09 |
| 398 | Stop hook fails: `hook` is not a valid CLI subcommand | — | 2026-04-09 |
| 397 | ARM64 segfault mitigation is a no-op — `ORT_DISABLE_COREML` not a real ONNX RT env var | — | 2026-04-09 |
| 396 | OOM crash on large transcript files | — | 2026-04-09 |
| 395 | `cmd_repair` infinite recursion on trailing-slash paths | — | 2026-04-09 |
| 369 | v3.0.14 not on PyPI — hook command missing | — | — |
| 363 | Windows: `mempalace_search` fails with "TextInputSequence must be str" on non-ASCII | — | #205 |
| 357 | Parallel mining corrupts ChromaDB HNSW index | — | — |
| 355 | pip package does not include `mcp` subcommand — Claude Desktop setup fails | — | #340 |
| 344 | HNSW index bloat: `link_lists.bin` grows to 441GB | — | #346 |
| 338 | `list_wings` / `list_rooms` / `get_taxonomy` silently return empty on large collections | — | #307, #371 |
| 333 | System prompt context prepended to queries drops retrieval from 89.8% to 1.0% | — | — |
| 327 | `normalize.py`: Claude Code JSONL parser doesn't match `type: "user"` messages | — | — |
| 323 | `mempal-stop-hook.sh` calls nonexistent `hook` subcommand | — | #325 |
| 275 | Windows compatibility gaps in tests and CI | — | #277 |
| 225 | `mempalace mcp` writes startup text to stdout instead of stderr | — | #261 |
| 218 | Collection created without `hnsw:space=cosine` causes negative similarity scores | — | #262 |
| 196 | SQLite connection leak in `KnowledgeGraph` methods | — | **#198** |
| 195 | `IndexError` when ChromaDB query returns empty results | — | **#197** |
| 185 | `mempalace init` writes `entities.json` + `mempalace.yaml` to project dir instead of `~/.mempalace/` | — | — |
| 184 | Hook scripts not included in pip package | — | #265 |
| 171 | MCP server: `list_wings` and `get_taxonomy` return empty despite data in palace | — | #307 |
| 97 | Entity detection ignores directory names, surfaces generic words from READMEs | — | #349 |

---

## FEATURES / ENHANCEMENTS — Labeled (Open, 30)

| # | Title | Author | Filed |
|---|---|---|---|
| 537 | [RFC] `scoring_mode`: weighted-sum model for RetrievalProfile (#519 follow-up) | matrix9neonebuchadnezzar2199 | 2026-04-10 |
| 533 | Centralized Skill Management (Agentic Skills Library) | alpiua | 2026-04-10 |
| 498 | [SPEC] RLM Context Handle Protocol + LCM Heat Scoring for AI-native memory retrieval | 40verse | 2026-04-10 |
| 496 | MemPalace Lite — zero-inference fallback mode | duskfallcrew | 2026-04-10 |
| 495 | Claude desktop session integration via browser-tab-as-proxy pattern | lukewp | 2026-04-10 |
| 494 | "Silent Mode" / background processing for the Stop hook (auto-save) | Adhders | 2026-04-10 |
| 489 | [RFC] Synapse Phase 1–2 — biologically-inspired scoring layer + co-retrieval | matrix9neonebuchadnezzar2199 | 2026-04-10 |
| 486 | "Calm" repo ask — community/non-profit | tetraminz | 2026-04-10 |
| 481 | "Hello, my name is Agero Flynn, just calm" | tetraminz | 2026-04-10 |
| 474 | TLDR | tomByrer | 2026-04-10 |
| 473 | Agero Flynn | tetraminz | 2026-04-10 |
| 454 | Hello, World! | tetraminz | 2026-04-09 |
| 420 | MemPalace as hoarder cleanup! | wafuzio | 2026-04-09 |
| 401 | Octocode — MemPalace security hardening | bgauryy | 2026-04-09 |
| 383 | new issue | Vrishinram | 2026-04-09 |
| 348 | Entity detector false positives — programming keywords detected as projects | matrix9neonebuchadnezzar2199 | 2026-04-09 |
| 341 | Clarification: current implementation role of closets | SparkyWen | 2026-04-09 |
| 332 | Soft-archive wings — exclude from search without deleting data | matrix9neonebuchadnezzar2199 | 2026-04-09 |
| 331 | Time-decay scoring for search results | matrix9neonebuchadnezzar2199 | 2026-04-09 |
| 292 | Per-user isolation for shared remote ChromaDB | cypromis | 2026-04-08 |
| 271 | WSL2: GPU detection failure causes slow `mempalace init` (CPU fallback) | manuerumx | 2026-04-08 |
| 255 | Allow `.rst` files | soyacz | 2026-04-08 |
| 231 | Add multilingual support | EndeavorYen | 2026-04-08 |
| 215 | Remote MCP | rafalzawadzki | 2026-04-08 |
| 213 | Test performance execution and token measurement | PaTiToMaSteR | 2026-04-08 |
| 189 | Secure Git-friendly export/import for specific wings (team sync) | alpiua | 2026-04-08 |
| 117 | Add PT-BR support for AAAK | MorningloryFox | 2026-04-07 |
| 73 | Separate recall vs brief retrieval modes | adampnielsen | 2026-04-07 |
| 46 | Support XDG base directory for configuration | noirbizarre | 2026-04-07 |
| 37 | 简体中文用户看过来 (Simplified Chinese users) | 3150214587 | 2026-04-07 |

---

## FEATURES / ENHANCEMENTS — Unlabeled (notable, Open)

Selected from the 99 unlabeled open issues. These are framed as features but lack the `enhancement` label.

| # | Title | Filed |
|---|---|---|
| 516 | Improve Chinese semantic search quality | 2026-04-10 |
| 515 | GPU-accelerated embeddings via optional sentence-transformers | 2026-04-10 |
| 514 | Feedback from production use: the weight of memory itself | 2026-04-10 |
| 467 | Add `SessionStart` hook to load memory protocol on wake-up | 2026-04-10 |
| 466 | Make AAAK opt-in (not default) in `diary_write` and save flows | 2026-04-10 |
| 465 | Include `created_at` timestamp in search results | 2026-04-10 |
| 464 | Automatic deduplication on `add_drawer` | 2026-04-10 |
| 391 | Memory-librarian skill + stuck-detector hook for Claude Code | 2026-04-09 |
| 376 | `search` and `kg_query` are completely disconnected | 2026-04-09 |
| 358 | MemPalace as memory substrate for decentralized agent network | 2026-04-09 |
| 352 | Add "Era" metadata — temporal axis for the palace | 2026-04-09 |
| 342 | Native OpenCode integration for MemPalace | 2026-04-09 |
| 318 | Smart wing auto-detection when mining conversations | 2026-04-09 |
| 283 | Vocabulary map to improve NL search | 2026-04-08 |
| 278 | `.al` extension support + wing-aware duplicate detection | 2026-04-08 |
| 274 | Native Cursor SQLite ingestion support | 2026-04-08 |
| 273 | Domain-scoped collections + local embedding model for retrieval at scale | 2026-04-08 |
| 269 | Hybrid retrieval direction | 2026-04-08 |
| 266 | Pluggable storage/backend layer | 2026-04-08 |
| 258 | "Singularity Equation" (A* + Stigmergy) for knowledge graph navigation | 2026-04-08 |
| 245 | Opt-in Cursor source filtering for `mempalace_search` | 2026-04-08 |
| 242 | Benchmark adapters discard assistant turns, causing 0% recall | 2026-04-08 |
| 237 | No storage-limit handling or disk-full graceful degradation | 2026-04-08 |
| 224 | Stale drawer retrieval injects contradictory memory | 2026-04-08 |
| 211 | Scaling fixes for large vaults (40k+ drawers) | 2026-04-08 |
| 206 | OpenClaw/ClawHub skill for MemPalace | 2026-04-08 |
| 122 | Enforcement Rules layer + typed memory with Why/How structure | 2026-04-07 |
| 118 | PII Guard | 2026-04-07 |
| 101 | Multipass — multi-hop paths through the Mem Palace | 2026-04-07 |
| 92 | Multilingual support: French (100+ languages) via Ollama BGE-M3 | 2026-04-07 |
| 59 | Import support for more AI tool session formats | 2026-04-07 |
| 11 | Knowledge graph: auto-resolve conflicting triples | 2026-04-07 |
| 10 | Episodic memory: track retrieval outcomes | 2026-04-07 |

---

## QUESTIONS / DISCUSSION / THANKS / LOW-SIGNAL (Open)

~25 low-actionable items. Highlights:

| # | Title |
|---|---|
| 532 | Architecture that makes harm structurally impossible — not by policy |
| 528 | 谢谢 (thanks) |
| 511 | Observation: Since starting MemPalace, LLM sessions are lasting way longer |
| 506 | Is `mempalace.tech` a hacked website using this repo's name? |
| 485 | A Large Thank You |
| 386 | Why is this starting at v3? |
| 366 | [SECURITY] Missing T-Virus containment protocols / Red Queen oversight (satirical) |
| 362 | How does the vector DB work when storing only raw text |
| 301 | Has anyone tried to use it to manage knowledge base? |
| 235 | Would like to contact |
| 199 | Thank you from Larry — multimodal AI agent with Palace powers |

---

## CLOSED (recent 2 weeks, top by number)

| # | Title | Labels |
|---|---|---|
| 472 | Null (no content) | — |
| 460 | Hook scripts missing from pip package | — |
| 457 | 3.1.0 upgrade silently breaks running MCP servers due to ChromaDB version downgrade | — |
| 443 | Staff Engineer Review: Postgres/Prisma Railway Wiring Plan | — |
| 441 | [RFC] Synapse: biologically-inspired memory scoring layer | enhancement |
| 407 | Discord invite invalid | — |
| 394 | MCP server hangs when client sends null arguments — unhandled AttributeError | — |
| 375 | Cursor MCP integration failed | bug |
| 374 | How does MemPalace fit in Entertainment AI Chatbots? | — |
| 345 | Codex hook message counting does not match Codex transcript schema | bug |
| 314 | Benchmark Design Issues in LongMemEval | bug |
| 312 | Related project: SophionMem | — |
| 296 | Invalid command `mcp` not recognized | bug |
| 290 | Inconsistent versions between pip package and Claude plugin | bug |
| 267 | Malicious entities on www.mempalace.tech | — |
| 257 | chromadb version pin on PyPI differs from main | — |
| 253 | Does this MCP make any off-box connections? | — |
| 250 | Missing input validation across file processing pipeline | bug |
| 249 | Potential API key exposure in multiple file paths | bug |
| 248 | Missing input validation on LLM API requests/responses | bug |
| 241 | Alignment between claims and capability would help adoption | bug |
| 235 | Would like to contact | — |
| 233 | Add support for `.gitignore` files | enhancement |
| 228 | Just wanted to say thank you | — |
| 227 | Are u real Milla Jovovich? | bug |

---

## Audit Findings vs Issue Coverage (2026-04-09, carried forward)

Cross-reference of validated findings from `docs/r1.md` and `docs/r2.md` against existing issues and open PRs.

### Covered by existing issues/PRs

| Finding | Issue | PR | Status |
|---|---|---|---|
| SQLite connection leaks in `knowledge_graph.py` | #196 | **#198** | PR open |
| Unpinned `chromadb>=0.5.0,<0.7` | #100 (closed) | ~~#365~~ | PR closed unmerged; `<0.7` pin landed upstream via other commit |
| Path traversal / shell injection in hooks | #110 (closed) | **#320** | PR open |
| ChatGPT parser follows first child only (data loss) | #330 | **#329** | PR open |
| Thread-unsafe ChromaDB client / ARM64 segfault | #74 (closed) | — | No PR; symptom re-reported in #521 (EXC_BAD_ACCESS on macOS ARM64 re-mine) |
| MCP error hardening (partial coverage of null args) | #394 (CLOSED) | **#181** | PR open; null-args symptom closed |
| Security hardening (partial coverage of delete auth) | — | **#175** | PR open (auth/encryption, broad scope) |

### New critical findings (need tracking)

| Finding | Severity | Issue |
|---|---|---|
| ChromaDB version downgrade on v3.1.0 upgrade silently wipes palace | CRITICAL | #469, #445, #457 |
| HNSW `link_lists.bin` grows to terabytes | CRITICAL | #525 |
| hnswlib `updatePoint` race on re-mine (EXC_BAD_ACCESS) | CRITICAL | #521 |
| MCP stdio transport drops writes (WAL only) | CRITICAL | #538 |
| Global palace single point of failure | HIGH | #444 |
| MCP cache declarations reset state | HIGH | #479 |
| MCP `tool_search` no limit upper bound (memory DoS) | HIGH | #477 |
| Float mtime breaks dedup (re-mines every file) | HIGH | #475 |
| CJK surrogate error on Windows in MCP | HIGH | #503 |
| `chromadb<0.7` pin breaks Python 3.14 | HIGH | #487 |

### Low-priority findings (no issue needed)

| Finding | Severity | Reason |
|---|---|---|
| Unauthenticated `delete_drawer` MCP tool | MEDIUM | Local-only; partial coverage by PR #175, PR #181 |
| Precompact hook unsanitized SESSION_ID | MEDIUM | Only used in logging; partial coverage by PR #320 |
| `--palace` path not sandboxed | MEDIUM | Local CLI tool, user controls their own paths |
| Unexpanded `~` in `hooks_cli.py` `MEMPAL_DIR` | MEDIUM | Niche env var usage |
| `_entity_id` collision ("O'Neil" vs "oneil") | LOW | Edge case |
| Dual env var names (`MEMPALACE` vs `MEMPAL`) | LOW | Convenience, not a bug |
| Temporal invalidation allows contradictions | LOW | No user reports |

---

## Summary by Category

| Category | Open | Closed (rolling 2wk) | Notes |
|---|---|---|---|
| Bugs — labeled `bug` | 26 | 15 | |
| Bugs — unlabeled but clearly bugs | ~40 | — | Upstream label debt |
| Features — labeled `enhancement` | 30 | 5 | |
| Features — unlabeled (notable) | ~35 | — | |
| Questions / Discussion / Thanks | ~25 | — | |
| **Total open issues** | **155** | — | |
| **Total open PRs** | **192** | — | |

---

## Open PRs Addressing Audit Findings

| PR | Branch | Addresses | State |
|---|---|---|---|
| **#439** | `docs/vitepress-site` (igorls) | VitePress documentation site (22 pages) | OPEN, MERGEABLE |
| #198 | `fix/kg-sqlite-connection-leak` | SQLite connection leaks (r1 HIGH, r2 CRITICAL) | OPEN |
| #320 | `fix/shell-injection` | Hook shell injection (r1 HIGH) | OPEN |
| #329 | `fix/chatgpt-mapping-active-branch` | ChatGPT parser data loss (r1/r2 MEDIUM) | OPEN |
| #181 | `fix/mcp-error-hardening` | MCP error handling (r2 CRITICAL — partial) | OPEN |
| #175 | `feat/security-hardening` | Auth/encryption hardening (r1 CRITICAL — partial) | OPEN |
| #346 | `fix/hnsw-index-bloat` | HNSW index corruption (related to concurrency issues) | OPEN |
| #371 | `fix/issue-339-338-silent-exceptions-pagination` | Silent exceptions + pagination | OPEN |
| ~~#365~~ | `fix/chromadb-version-pin` | ChromaDB version pinning | CLOSED (unmerged) |
