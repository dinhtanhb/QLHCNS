---
kind: external_dependency
name: Upstash Context7 MCP Server
slug: context7-mcp
category: external_dependency
category_hints:
    - vendor_identity
    - sdk_real_api
scope:
    - '**'
---

### Upstash Context7 MCP
- An MCP server launched via `npx -y @upstash/context7-mcp` from `.mcp.json`, exposing all tools (`tools: ["*"]`).
- Used as a local MCP extension by the IDE's MCP client; its runtime depends on Node.js / npx being available in PATH.
- Verify exact tool names and capabilities against the official @upstash/context7-mcp docs.