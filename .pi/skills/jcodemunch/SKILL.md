---
name: jcodemunch
description: Structured code retrieval via tree-sitter AST indexing. Use when exploring unfamiliar codebases, finding functions/classes, impact analysis, dead code detection, or any task that would normally require reading full source files. Cuts token usage by ~95% vs brute-force file reading.
---

# jCodeMunch — Structured Code Retrieval

Index once. Query cheaply. Stop paying the model to read the whole damn file.

## Prerequisites

- The `munch-bridge` extension must be loaded (provides `jcodemunch_*` tools)
- The target codebase must be indexed before querying

## When to Use This Skill

Use jCodeMunch tools **instead of reading files** when:
- Exploring an unfamiliar codebase
- Finding a specific function, class, or method
- Understanding file/module structure
- Checking impact of a change
- Looking for dead code or untested symbols
- Tracing imports or call hierarchies

**Do NOT use for:** files you're actively editing (use `read`/`edit` for surgical edits on known files).

## Workflow

### Step 1: Check if Already Indexed

```
Call: jcodemunch_list_repos
```

If the repo is listed, skip to Step 3.

### Step 2: Index the Codebase

For a local folder:
```
Call: jcodemunch_index_folder
  path: "/absolute/path/to/project"
```

For a GitHub repo:
```
Call: jcodemunch_index_repo
  url: "owner/repo"
```

Wait for indexing to complete. Response includes file counts and discovery stats.

### Step 3: Resolve the Repo Identifier

After indexing, resolve the path to the repo identifier used by other tools:
```
Call: jcodemunch_resolve_repo
  path: "/absolute/path/to/project"
```

**All subsequent calls need this `repo` identifier.**

### Step 4: Explore and Retrieve

Pick the right tool for the job. See the tool reference below.

## Tool Reference

### Discovery & Indexing

| Tool | When to Use |
|------|-------------|
| `jcodemunch_list_repos` | Check what's indexed. START HERE. |
| `jcodemunch_resolve_repo` | Get the repo identifier from a filesystem path. O(1) lookup. |
| `jcodemunch_index_folder` | Index a local folder. Do this first if nothing is indexed. |
| `jcodemunch_index_repo` | Index a GitHub repository. |
| `jcodemunch_index_file` | Re-index a single file after editing (surgical update). |
| `jcodemunch_summarize_repo` | Re-run AI summaries if they're missing or stale. |
| `jcodemunch_invalidate_cache` | Delete an index and force full re-index. |
| `jcodemunch_register_edit` | Clear caches for a file after editing. Faster than full re-index. |

### Exploration

| Tool | When to Use |
|------|-------------|
| `jcodemunch_suggest_queries` | Unfamiliar repo? Get suggested queries + entry-point files + stats. Great first call. |
| `jcodemunch_get_repo_outline` | High-level overview: directories, file counts, languages, symbol counts. Lightweight. |
| `jcodemunch_get_file_tree` | List files in an indexed repo, optionally filtered by path prefix. |
| `jcodemunch_get_file_outline` | All symbols in one file with signatures and summaries. Cheaper than reading the file. |
| `jcodemunch_get_repo_outline` | Bird's-eye view of the repo structure. |
| `jcodemunch_plan_turn` | Confidence-guided routing: what should I look at next? Returns high/medium/low confidence. |

### Search

| Tool | When to Use |
|------|-------------|
| `jcodemunch_search_symbols` | **Primary search.** Find symbols by name (supports fuzzy matching). Returns signatures + summaries. |
| `jcodemunch_search_text` | Full-text search when symbol search misses (string literals, comments, config values). |
| `jcodemunch_search_columns` | Search column metadata across data models (dbt, SQLMesh, etc.). |
| `jcodemunch_find_references` | Where is an identifier used? Combines import graph + content search. |
| `jcodemunch_check_references` | Quick boolean: is this identifier referenced anywhere? |

### Retrieval

| Tool | When to Use |
|------|-------------|
| `jcodemunch_get_symbol_source` | **Primary retrieval.** Get exact source of one or more symbols by ID. Byte-precise extraction. |
| `jcodemunch_get_file_content` | Get cached source for a file, optionally sliced to a line range. Use when you need full file context. |
| `jcodemunch_get_context_bundle` | Multi-symbol bundle: source + imports in one call. Deduplicates shared imports. Set `token_budget`. |
| `jcodemunch_get_ranked_context` | Assemble best-fit context for a query within a token budget. BM25 + centrality ranking. |

### Impact Analysis

| Tool | When to Use |
|------|-------------|
| `jcodemunch_get_blast_radius` | What files break if I change this symbol? Confirmed + potential impacts with depth-weighted scores. |
| `jcodemunch_get_impact_preview` | What breaks if a symbol is removed/renamed? Transitive call-graph walk. |
| `jcodemunch_get_call_hierarchy` | Callers and callees N levels deep. AST-derived, not regex-based. |
| `jcodemunch_find_importers` | What files import a given file? `has_importers=false` means the file is unreachable. |
| `jcodemunch_get_dependency_graph` | File-level dependency graph up to 3 hops. |
| `jcodemunch_get_dependency_cycles` | Detect circular import chains. Returns strongly-connected components. |

### Quality & Health

| Tool | When to Use |
|------|-------------|
| `jcodemunch_find_dead_code` | Files/symbols with zero importers and no entry-point role. Import-graph based. |
| `jcodemunch_get_dead_code_v2` | Enhanced dead code detection: 3 independent evidence signals (unreachable + no tests + no references). |
| `jcodemunch_get_untested_symbols` | Functions/methods with no test coverage evidence. Import-graph reachability + name matching. |
| `jcodemunch_get_hotspots` | Highest-risk code: complexity × git churn. Top-N ranking. |
| `jcodemunch_get_repo_health` | One-call triage: dead code %, avg complexity, dependency cycles, test coverage summary. |
| `jcodemunch_get_symbol_complexity` | Cyclomatic complexity, nesting depth, parameter count for one symbol. |
| `jcodemunch_get_coupling_metrics` | Afferent/efferent coupling and instability score for a file. |
| `jcodemunch_get_layer_violations` | Check architectural layer boundaries. Reports forbidden cross-layer imports. |
| `jcodemunch_audit_agent_config` | Audit CLAUDE.md/.cursorrules for token waste, stale references, dead paths. |

### Refactoring

| Tool | When to Use |
|------|-------------|
| `jcodemunch_plan_refactoring` | Edit-ready instructions for rename, move, extract, or signature change. Returns `{old_text, new_text}` blocks. |
| `jcodemunch_check_rename_safe` | Will renaming a symbol cause name collisions? Scans all affected files. |
| `jcodemunch_get_extraction_candidates` | Functions that are good candidates for extraction to a shared module. |
| `jcodemunch_get_symbol_diff` | Diff symbol sets between two index snapshots (e.g., two git branches). |
| `jcodemunch_get_changed_symbols` | Map a git diff to affected symbols between two commits. |

### Session & Cross-Repo

| Tool | When to Use |
|------|-------------|
| `jcodemunch_get_session_stats` | Token savings and cost avoided for this session and all-time. |
| `jcodemunch_get_session_context` | Files accessed, searches performed, edits registered this session. |
| `jcodemunch_get_session_snapshot` | ~200 token compact summary of session activity for context continuity. |
| `jcodemunch_get_related_symbols` | Symbols related to a given one via heuristic clustering (co-location, shared importers, calls). |
| `jcodemunch_get_symbol_importance` | Most architecturally important symbols ranked by PageRank on the import graph. |
| `jcodemunch_get_class_hierarchy` | Full inheritance chain: ancestors (extends/implements) and descendants (subclasses). |
| `jcodemunch_get_cross_repo_map` | Cross-repository package-level dependency map. |
| `jcodemunch_embed_repo` | Precompute symbol embeddings for semantic search. |
| `jcodemunch_get_churn_rate` | Git churn metrics: commit count, authors, first/last seen, churn rate for a file or symbol. |

## Common Patterns

### "Find a function and understand it"
```
1. jcodemunch_search_symbols  → find the symbol_id
2. jcodemunch_get_symbol_source  → get exact implementation
```

### "What breaks if I change this?"
```
1. jcodemunch_get_blast_radius  → impacted files
2. jcodemunch_get_call_hierarchy  → caller/callee chain
3. jcodemunch_get_impact_preview  → removal/renaming impact
```

### "Understand a module at a glance"
```
1. jcodemunch_get_file_outline  → all symbols with signatures
2. jcodemunch_get_context_bundle (top 3-5 symbols)  → source + imports
```

### "Onboard to an unfamiliar repo"
```
1. jcodemunch_index_folder  → index the codebase
2. jcodemunch_suggest_queries  → what to look at first
3. jcodemunch_get_repo_outline  → directory structure
4. jcodemunch_search_symbols  → find key abstractions
```

### "Dead code sweep"
```
1. jcodemunch_find_dead_code_v2  → dead code with 3-signal confidence
2. jcodemunch_get_untested_symbols  → untested functions
3. jcodemunch_get_repo_health  → overall health dashboard
```

### "Refactoring preparation"
```
1. jcodemunch_check_rename_safe  → collision check
2. jcodemunch_plan_refactoring  → generate edit blocks
3. After editing: jcodemunch_register_edit  → clear caches
```

## Tips

- Always call `jcodemunch_list_repos` or `jcodemunch_resolve_repo` first to get the `repo` identifier
- Use `jcodemunch_get_symbol_source` instead of reading files when you know the symbol name
- Use `jcodemunch_get_file_outline` instead of reading full files to understand structure
- Set `token_budget` on `jcodemunch_get_context_bundle` and `jcodemunch_get_ranked_context` to control context size
- After editing files, call `jcodemunch_register_edit` to invalidate stale caches
- Use `jcodemunch_plan_turn` for confidence-guided next steps when you're unsure what to look at
