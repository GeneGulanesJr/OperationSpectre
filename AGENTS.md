# Code & Doc Retrieval — Enforced

You have access to jCodeMunch (`jcodemunch_*` tools) and jDocMunch (`jdocmunch_*` tools) via the munch-bridge extension.

**These are your PRIMARY tools for finding and reading code and documentation.**

Before using `read`, `bash` (grep/find), or any tool to search/explore code or docs, you MUST:
1. Try jCodeMunch for code files → `jcodemunch_search_symbols`, `jcodemunch_get_file_outline`, `jcodemunch_get_symbol_source`
2. Try jDocMunch for doc files → `jdocmunch_search_sections`, `jdocemunch_get_toc`, `jdocmunch_get_section`

Only fall back to `read`/`grep`/`find` if the structured tools fail or if you need to edit a file you already have full context on.

Check `jcodemunch_list_repos` and `jdocmunch_doc_list_repos` first. If empty, index with `jcodemunch_index_folder` or `jdocmunch_index_local`.
