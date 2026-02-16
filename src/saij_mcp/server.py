"""SAIJ MCP Server — expose Argentine legal database search to AI clients."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from . import __version__
from .client import (
    VALID_DOC_TYPES,
    SAIJError,
    get_document,
    get_sumarios,
    search,
)

mcp = FastMCP(
    "saij",
    instructions=(
        "Search and retrieve from SAIJ (Sistema Argentino de Información Jurídica) — "
        "Argentina's official legal information system. "
        "Access court decisions, legislation, legal summaries, and doctrine."
    ),
)


@mcp.tool()
def saij_search(
    query: str,
    doc_type: str = "fallo",
    field: str = "titulo",
    limit: int = 10,
    offset: int = 0,
) -> str:
    """Search Argentine legal documents in SAIJ.

    Use this tool to find court decisions (fallos), legal summaries (sumarios),
    legislation (leyes, decretos), doctrine, and dictámenes from Argentina's
    official legal database.

    Args:
        query: Search terms (e.g. "consumidor", "phishing bancario").
        doc_type: Type of document to search. Options:
            - "fallo": Court decisions (default)
            - "sumario": Case summaries with thesaurus tags
            - "jurisprudencia": Both fallos and sumarios
            - "legislacion": All legislation
            - "ley": Laws only
            - "decreto": Decrees only
            - "doctrina": Legal doctrine/articles
            - "dictamen": Official opinions
            - "todo": All document types
        field: Search field. "titulo" works with all types. "texto" only
            works with sumarios (searches the summary text body).
        limit: Maximum results to return (1-25, default 10).
        offset: Pagination offset for fetching more results.

    Returns:
        JSON with total count, results array, and facet breakdowns
        (by jurisdiction, tribunal, year).
    """
    if doc_type not in VALID_DOC_TYPES:
        return json.dumps(
            {"error": f"Invalid doc_type. Must be one of: {VALID_DOC_TYPES}"},
            ensure_ascii=False,
        )

    try:
        result = search(
            query=query,
            doc_type=doc_type,
            field=field,
            limit=limit,
            offset=offset,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except SAIJError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def saij_get_document(identifier: str) -> str:
    """Get a full document from SAIJ by its ID.

    Retrieves complete metadata for a court decision, law, or other legal
    document, including tribunal, date, jurisdiction, magistrates, and
    related sumarios. For fallos, includes PDF download URL.

    Args:
        identifier: Either a SAIJ id-infojus (e.g. "FA20000057" for a fallo,
            "LNS0007682" for a law) or the full document UUID.

    Returns:
        JSON with complete document metadata. For fallos: tribunal, date,
        case caption (caratula), magistrates, jurisdiction, related sumario
        IDs, and PDF URL. For sumarios: summary text, thesaurus descriptors.
    """
    try:
        result = get_document(identifier)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except SAIJError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def saij_get_sumarios(fallo_id: str) -> str:
    """Get all legal summaries (sumarios) linked to a court decision.

    Each sumario contains a legal principle extracted from the decision,
    tagged with thesaurus descriptors. Useful for understanding the key
    legal holdings of a case.

    Args:
        fallo_id: The fallo's id-infojus (e.g. "FA20000057"). The "FA"
            prefix is added automatically if missing.

    Returns:
        JSON with the fallo ID, total count, and array of sumarios, each
        with: summary text, thesaurus descriptors (legal topic tags),
        tribunal, date, and jurisdiction.
    """
    try:
        result = get_sumarios(fallo_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except SAIJError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def main():
    """Run the SAIJ MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
