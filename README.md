# saij-mcp

MCP server for searching [SAIJ](https://www.saij.gob.ar/) (Sistema Argentino de Información Jurídica) — Argentina's official legal information system.

Gives any AI client (Claude Desktop, Cursor, Windsurf, Claude Code, etc.) the ability to search and retrieve Argentine court decisions, legislation, legal summaries, and doctrine.

## Tools

| Tool | Description |
|------|-------------|
| `saij_search` | Search by keywords across fallos, sumarios, legislation, doctrine |
| `saij_get_document` | Get full document metadata by SAIJ ID (e.g. `FA20000057`) |
| `saij_get_sumarios` | Get all legal summaries linked to a court decision |

## Install

```bash
pip install saij-mcp
```

Or run directly with `uvx`:

```bash
uvx saij-mcp
```

## Configure

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "saij": {
      "command": "uvx",
      "args": ["saij-mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add saij -- uvx saij-mcp
```

### Cursor / Windsurf

Add to your MCP config:

```json
{
  "mcpServers": {
    "saij": {
      "command": "uvx",
      "args": ["saij-mcp"]
    }
  }
}
```

## Usage examples

Once configured, your AI client can:

- **"Buscame jurisprudencia sobre phishing bancario"** — searches sumarios with thesaurus-tagged legal topics
- **"Qué dice el fallo FA20000057?"** — retrieves full case metadata, tribunal, date, magistrates
- **"Dame los sumarios del fallo FA20000057"** — returns all legal principles extracted from the decision
- **"Buscá leyes sobre defensa del consumidor"** — searches legislation by title

### Search fields

| Field | Works with | Description |
|-------|-----------|-------------|
| `titulo` | Everything | Search by document title (default) |
| `texto` | Sumarios only | Full-text search in summary body |

### Document types

| Type | Description |
|------|-------------|
| `fallo` | Court decisions (default) |
| `sumario` | Case summaries with thesaurus descriptors |
| `jurisprudencia` | Both fallos and sumarios |
| `legislacion` | All legislation |
| `ley` | Laws |
| `decreto` | Decrees |
| `doctrina` | Legal doctrine and articles |
| `dictamen` | Official legal opinions |
| `todo` | All types |

## How it works

SAIJ exposes a public JSON API (no authentication required). This server wraps it with proper tool descriptions so AI clients can search effectively.

The API uses Lucene-style query syntax internally. The server handles query construction, facet filtering, and response parsing.

Sumarios are particularly useful — they contain legal principles extracted from court decisions, tagged with a hierarchical legal thesaurus (descriptors). These tags enable semantic legal search even without embeddings.

## Limitations

- **Fallo full text is PDF-only** — the API returns metadata and related sumarios, but the actual decision text is in an attached PDF. Use `pdf_url` from `saij_get_document` to download it.
- **`texto` field only searches sumarios** — for fallos, search by `titulo` (case caption).
- **No rate limiting detected**, but be respectful with request volume.

## License

MIT
