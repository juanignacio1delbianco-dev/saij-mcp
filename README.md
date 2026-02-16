# saij-mcp

Servidor MCP para buscar en [SAIJ](https://www.saij.gob.ar/) (Sistema Argentino de Información Jurídica), la base de datos jurídica oficial de Argentina.

Permite que cualquier cliente de IA (Claude Desktop, Cursor, Windsurf, Claude Code, etc.) busque y recupere fallos, legislación, sumarios y doctrina argentina.

## Herramientas

| Herramienta | Descripción |
|-------------|-------------|
| `saij_search` | Buscar por palabras clave en fallos, sumarios, legislación, doctrina |
| `saij_get_document` | Obtener metadatos completos de un documento por ID SAIJ (ej. `FA20000057`) |
| `saij_get_sumarios` | Obtener todos los sumarios vinculados a un fallo |

## Instalación

```bash
pip install saij-mcp
```

O ejecutar directamente con `uvx`:

```bash
uvx saij-mcp
```

## Configuración

### Claude Desktop

Agregar a `claude_desktop_config.json`:

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

Agregar a la configuración MCP:

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

## Ejemplos de uso

Una vez configurado, tu cliente de IA puede:

- **"Buscame jurisprudencia sobre phishing bancario"** — busca sumarios con descriptores del tesauro jurídico
- **"Qué dice el fallo FA20000057?"** — recupera metadatos completos: tribunal, fecha, magistrados
- **"Dame los sumarios del fallo FA20000057"** — devuelve todos los principios jurídicos extraídos del fallo
- **"Buscá leyes sobre defensa del consumidor"** — busca legislación por título

### Campos de búsqueda

| Campo | Funciona con | Descripción |
|-------|-------------|-------------|
| `titulo` | Todo | Busca por título del documento (default) |
| `texto` | Solo sumarios | Búsqueda en el cuerpo del sumario |

### Tipos de documento

| Tipo | Descripción |
|------|-------------|
| `fallo` | Sentencias y resoluciones judiciales (default) |
| `sumario` | Resúmenes con descriptores del tesauro |
| `jurisprudencia` | Fallos y sumarios |
| `legislacion` | Toda la legislación |
| `ley` | Leyes |
| `decreto` | Decretos |
| `doctrina` | Doctrina y artículos jurídicos |
| `dictamen` | Dictámenes |
| `todo` | Todos los tipos |

## Cómo funciona

SAIJ expone una API JSON pública (sin autenticación). Este servidor la envuelve con descripciones de herramientas MCP para que los clientes de IA puedan buscar de forma efectiva.

La API usa sintaxis de consulta tipo Lucene internamente. El servidor se encarga de construir las queries, filtrar por facetas y parsear las respuestas.

Los sumarios son particularmente útiles: contienen principios jurídicos extraídos de los fallos, etiquetados con un tesauro jerárquico de descriptores. Estos descriptores permiten búsqueda semántica legal incluso sin embeddings.

## Limitaciones

- **El texto completo de los fallos es solo PDF** — la API devuelve metadatos y sumarios vinculados, pero el texto de la sentencia está en un PDF adjunto. Usá `pdf_url` de `saij_get_document` para descargarlo.
- **El campo `texto` solo busca en sumarios** — para fallos, buscá por `titulo` (carátula).
- **No se detectó rate limiting**, pero usá con moderación.

## Licencia

MIT
