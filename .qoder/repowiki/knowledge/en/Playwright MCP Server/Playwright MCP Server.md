---
kind: external_dependency
name: Playwright MCP Server
slug: playwright-mcp
category: external_dependency
category_hints:
    - vendor_identity
    - sdk_real_api
scope:
    - '**'
---

### Playwright MCP Server
- An MCP server launched via `npx -y @playwright/mcp@latest` from `.mcp.json`, exposing all tools.
- Provides browser automation/testing tools through the MCP protocol; runtime depends on Node.js / npx.
- The `@latest` tag pins no fixed version — verify exact tool API against the current @playwright/mcp docs before relying on it.