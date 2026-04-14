# NL2SQL Confidence MCP Server

## Project Overview
An MCP server that exposes NL2SQL confidence scoring as tools usable inside Claude Code
and Cursor. Users ask natural language questions; the server automatically scores confidence
across four dimensions and either proceeds or explains why it can't before any SQL runs.

## Current Phase
**Phase 1 — Learn MCP Fundamentals**
See @docs/phases.md for full plan and progress tracking.

## Architecture Decisions
- Single MCP server for now — semantic layer and confidence scoring live together
- Gate pattern UX: confidence runs first, query only proceeds if threshold is met
- All scoring logic will eventually live in server.py until there is a clear reason to split
- stdio transport for local development (each developer runs their own instance)

## Tech Stack
- Python 3.11+
- `fastmcp` library (install: `pip install fastmcp`)
- Transport: stdio (local only — Claude Code spawns the server as a subprocess)
- No database, no real backend — mock return values only in Phase 1

## Project Structure
```
nl2sql-mcp/
├── CLAUDE.md
├── docs/
│   └── phases.md
├── src/
│   └── mcp_server/
│       ├── __init__.py
│       └── server.py        ← all code lives here for now
└── tests/
    └── test_server.py
```

## Conventions
- Tool names: snake_case verbs (e.g. score_question, should_execute)
- Every tool must have a docstring — FastMCP exposes it as the tool description the LLM sees
- Tools return a dict with at least: confidence (float 0–1) and reasons (list of strings)
- Keep server.py under 100 lines in Phase 1 — clarity over completeness
- Never execute SQL anywhere in this project

## Key Commands
```bash
# Install dependency
pip install fastmcp

# Run server manually to check for errors
python src/mcp_server/server.py

# Run tests
pytest tests/

# Validate tools are visible in MCP Inspector
npx @modelcontextprotocol/inspector python src/mcp_server/server.py
```

## Claude Code Config
Register the server by adding this to claude_desktop_config.json:
- macOS/Linux: ~/.claude/claude_desktop_config.json
- Windows: %APPDATA%\Claude\claude_desktop_config.json

```json
{
  "mcpServers": {
    "nl2sql-confidence": {
      "command": "python",
      "args": ["src/mcp_server/server.py"],
      "cwd": "/absolute/path/to/nl2sql-mcp"
    }
  }
}
```

## Claude Code Workflow Tips
- Use /clear between distinct tasks to keep context clean
- Each Phase 1 task is self-contained — clear after each one
- Ask Claude Code to check off tasks in @docs/phases.md as you complete them