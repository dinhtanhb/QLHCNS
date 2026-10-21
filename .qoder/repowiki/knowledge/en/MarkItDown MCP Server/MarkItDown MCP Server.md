---
kind: external_dependency
name: MarkItDown MCP Server
slug: markitdown-mcp
category: external_dependency
category_hints:
    - vendor_identity
    - sdk_real_api
scope:
    - '**'
---

### MarkItDown MCP Server
- A Python-based MCP server launched via `uvx markitdown-mcp` from `.mcp.json`, exposing all tools.
- Depends on Python 3.x and uv/uvx being available in PATH; the `--version` flag is not supported by this package even though the package itself loads fine.
- Verify exact tool names and invocation flags against the official markitdown-mcp docs.