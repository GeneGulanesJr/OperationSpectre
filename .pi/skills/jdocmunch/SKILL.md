---
name: jdocmunch
description: Section-level documentation indexing and retrieval. Use when navigating documentation sets, finding specific doc sections, checking doc coverage, or auditing documentation health. Cuts doc-reading token usage by ~95% vs brute-force file reading.
---

# jDocMunch — Structured Documentation Retrieval

Stop feeding documentation trees to the AI. Navigate by section, not by file.

## Prerequisites

- The `munch-bridge` extension must be loaded (provides `jdocmunch_*` tools)
- The target documentation must be indexed before querying

## When to Use This Skill

Use jDocMunch tools **instead of reading doc files** when:
- Navigating a documentation set (README, guides, API docs, wikis)
- Finding a specific section (configuration, installation, API reference)
- Browsing documentation structure (table of contents)
- Checking documentation health (broken links, coverage gaps, stale pages)
- Cross-referencing doc sections (backlinks, coverage against code symbols)

**Do NOT use for:** source code (use the `jcodemunch` skill for code). Do NOT use for actively editing doc files (use `read`/`edit` for that).

## Workflow

### Step 1: Check if Already Indexed

```
Call: jdocmunch_doc_list_repos
```

If the repo is listed, skip to Step 3.

### Step 2: Index the Documentation

For a local folder:
```
Call: jdocmunch_index_local
  path: "/absolute/path/to/docs"
```

For a GitHub repo:
```
Call: jdocmunch_doc_index_repo
  url: "owner/repo"
```

Wait for indexing to complete. Response includes file counts and section counts.

### Step 3: Explore and Retrieve

Pick the right tool for the job. See the tool reference below.

## Tool Reference

### Discovery & Indexing

| Tool | When to Use |
|------|-------------|
| `jdocmunch_doc_list_repos` | Check what doc sets are indexed. START HERE. |
| `jdocmunch_index_local` | Index a local documentation folder (.md, .txt, .rst, .adoc, .html, .ipynb, .json, .xml). |
| `jdocmunch_doc_index_repo` | Index a GitHub repository's documentation files. |
| `jdocmunch_delete_index` | Remove a doc index and its cached raw files. |

### Navigation

| Tool | When to Use |
|------|-------------|
| `jdocmunch_get_toc` | **Flat table of contents** — all sections across all docs, sorted by document order. Summaries only, no content. Great for orientation. |
| `jdocmunch_get_toc_tree` | **Nested TOC tree** — parent/child heading relationships per document. Shows the hierarchy structure. |
| `jdocmunch_get_document_outline` | Section hierarchy for a **single document**. Use when you know which file and want its structure. |

### Search & Retrieval

| Tool | When to Use |
|------|-------------|
| `jdocmunch_search_sections` | **Primary search.** Find sections by relevance. Returns summaries only — then use `get_section` for full content. |
| `jdocmunch_get_section` | **Primary retrieval.** Get full content of one section by its section_id. Byte-range reads — fast and precise. |
| `jdocmunch_get_sections` | **Batch retrieval.** Get full content for multiple sections in one call. More efficient than individual `get_section` calls. |
| `jdocmunch_get_section_context` | Section + full hierarchy context: ancestor headings for orientation, target section content, and child section summaries. Best for deep understanding. |

### Health & Quality

| Tool | When to Use |
|------|-------------|
| `jdocmunch_get_broken_links` | Find internal cross-references that no longer resolve. Checks markdown links, RST directives, wiki links. |
| `jdocmunch_get_doc_coverage` | Check which jcodemunch code symbols have matching doc sections. Bridges code ↔ docs. Requires both skills indexed. |
| `jdocmunch_get_backlinks` | Find all sections that link TO a given document. Inverse reference graph — useful for the LLM Wiki pattern. |
| `jdocmunch_get_stale_pages` | Find doc pages whose declared source files have been modified on disk (YAML frontmatter convention). |
| `jdocmunch_get_wiki_stats` | Wiki health dashboard: orphan pages, most-linked pages, tag distribution, coverage stats. |

## Common Patterns

### "Understand a documentation set at a glance"
```
1. jdocmunch_index_local  → index the docs folder
2. jdocmunch_get_toc  → flat section list with summaries
3. jdocmunch_get_toc_tree  → nested hierarchy for structure
```

### "Find a specific topic in docs"
```
1. jdocmunch_search_sections  → find relevant sections (summaries only)
2. jdocmunch_get_section (or get_sections for multiple)  → full content of matching sections
```

### "Deep-dive one topic with full context"
```
1. jdocmunch_search_sections  → find the section_id
2. jdocmunch_get_section_context  → get the section with ancestor headings + child summaries
```

### "Check documentation health"
```
1. jdocmunch_get_broken_links  → dead links
2. jdocmunch_get_wiki_stats  → overall health dashboard
3. jdocmunch_get_stale_pages  → docs that need updating
4. jdocmunch_get_doc_coverage  → code ↔ docs coverage gaps
```

### "Find what references a doc page"
```
1. jdocmunch_get_backlinks  → all sections linking to this document
```

## Supported Documentation Formats

| Format | Extensions | Parsing Method |
|--------|-----------|----------------|
| Markdown | `.md`, `.markdown` | ATX + setext headings |
| MDX | `.mdx` | JSX stripped, then heading-based |
| Plain text | `.txt` | Paragraph-block section splitting |
| reStructuredText | `.rst` | Adornment-based headings |
| AsciiDoc | `.adoc` | `=` heading hierarchy |
| Jupyter Notebook | `.ipynb` | Markdown cells as sections |
| HTML | `.html` | `<h1>`–`<h6>` headings |
| OpenAPI / Swagger | `.yaml`, `.yml`, `.json` | Operations grouped by tag |
| JSON / JSONC | `.json`, `.jsonc` | Top-level keys as sections |
| XML / SVG / XHTML | `.xml`, `.svg`, `.xhtml` | Element hierarchy |

## Section ID Format

Stable, human-readable IDs that survive re-indexing:
```
{repo}::{doc_path}::{ancestor-chain/slug}#{level}
```

Examples:
- `local/myproject::docs/install.md::installation#1`
- `local/myproject::docs/install.md::installation/prerequisites#3`
- `local/myproject::README.md::usage/configuration/advanced-configuration#4`

## Tips

- Always start with `jdocmunch_doc_list_repos` to check what's indexed
- Use `jdocmunch_search_sections` first (returns summaries only → cheap), then `jdocmunch_get_section` for full content
- `jdocmunch_get_section_context` is the most expensive but most informative single call — use for deep understanding
- `jdocmunch_get_toc` is ~40× cheaper than reading doc files — use it for orientation
- `jdocmunch_get_doc_coverage` bridges both skills: checks which code symbols have doc sections
- After editing doc files, re-index with `jdocmunch_index_local` to keep the index fresh
