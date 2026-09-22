"""SAIJ API client — zero dependencies beyond stdlib."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Any

BASE_URL = "https://www.saij.gob.ar"

DOC_TYPE_FACETS = {
    "fallo": "Tipo de Documento/Jurisprudencia/Fallo",
    "sumario": "Tipo de Documento/Jurisprudencia/Sumario",
    "jurisprudencia": "Tipo de Documento/Jurisprudencia",
    "legislacion": "Tipo de Documento/Legislación",
    "ley": "Tipo de Documento/Legislación/Ley",
    "decreto": "Tipo de Documento/Legislación/Decreto",
    "doctrina": "Tipo de Documento/Doctrina",
    "dictamen": "Tipo de Documento/Dictamen",
    "todo": "Tipo de Documento",
}

VALID_DOC_TYPES = list(DOC_TYPE_FACETS.keys())


class SAIJError(Exception):
    """Error communicating with SAIJ API."""


def _fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
    url,
    headers={
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SAIJError(f"HTTP {e.code} from {url}") from e
    except urllib.error.URLError as e:
        raise SAIJError(f"Connection error: {e.reason}") from e


def _build_facets(doc_type: str | None) -> str:
    parts = ["Total"]
    if doc_type and doc_type in DOC_TYPE_FACETS:
        parts.append(DOC_TYPE_FACETS[doc_type])
    parts.extend(["Fecha", "Tribunal", "Jurisdicción"])
    return "|".join(parts)


def _parse_result(raw: dict[str, Any]) -> dict[str, Any]:
    """Parse a search result into a clean dict."""
    abstract = json.loads(raw["documentAbstract"])
    meta = abstract["document"]["metadata"]
    content = abstract["document"]["content"]
    furl = meta.get("friendly-url", {})

    result: dict[str, Any] = {
        "uuid": meta["uuid"],
        "type": meta.get("document-content-type", ""),
    }

    # Common fields
    for src, dst in [
        ("tribunal", "tribunal"),
        ("actor", "caratula"),
        ("fecha", "fecha"),
        ("tipo-fallo", "tipo_fallo"),
        ("magistrados", "magistrados"),
        ("titulo", "titulo"),
        ("numero-norma", "numero_norma"),
        ("tipo-norma", "tipo_norma"),
    ]:
        if src in content:
            val = content[src]
            result[dst] = val.get("texto", val) if isinstance(val, dict) else val

    # Jurisdiction
    if "jurisdiccion" in content:
        j = content["jurisdiccion"]
        result["jurisdiccion"] = j.get("descripcion", j) if isinstance(j, dict) else j

    # Sumario text
    if "texto" in content:
        result["texto"] = content["texto"]

    # Descriptors (thesaurus tags)
    if "descriptores" in content:
        descs = content["descriptores"]
        if isinstance(descs, dict) and "descriptor" in descs:
            dl = descs["descriptor"]
            if not isinstance(dl, list):
                dl = [dl]
            result["descriptores"] = [
                d.get("elegido", {}).get("termino", "") for d in dl
            ]

    # Vigencia (for legislation)
    if "estado-vigencia" in content:
        result["vigencia"] = content["estado-vigencia"]

    # Related sumarios (for fallos)
    sr = content.get("sumarios-relacionados", {})
    if sr:
        ids = sr.get("sumario-relacionado", [])
        if isinstance(ids, str):
            ids = [ids]
        result["sumarios_relacionados"] = ids

    # URL
    if furl.get("subdomain") and furl.get("description"):
        result["url"] = (
            f"{BASE_URL}/{furl['subdomain']}/{furl['description']}/{meta['uuid']}"
        )

    return result


def search(
    query: str,
    doc_type: str = "fallo",
    field: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search SAIJ.

    Args:
        query: Search terms.
        doc_type: One of fallo, sumario, jurisprudencia, legislacion, ley,
                  decreto, doctrina, dictamen, todo.
        field: Search field — "titulo" (works with everything) or "texto"
               (only works with sumarios). Defaults to "titulo".
        limit: Max results (1-25).
        offset: Pagination offset.
    """
    field = field or "titulo"
    limit = max(1, min(25, limit))

    params = {
        "r": f"+{field}: {query}",
        "o": offset,
        "p": limit,
        "f": _build_facets(doc_type),
        "v": "colapsada",
    }
    url = f"{BASE_URL}/busqueda?{urllib.parse.urlencode(params)}"
    data = _fetch_json(url)

    sr = data.get("searchResults", {})
    results = [_parse_result(d) for d in sr.get("documentResultList", [])]

    facets: dict[str, Any] = {}
    for cat in sr.get("categoriesResultList", []):
        children = cat.get("facetChildren", [])
        if children:
            facets[cat["facetName"]] = {
                c["facetName"]: int(c["facetHits"]) for c in children
            }

    return {
        "total": sr.get("totalSearchResults", 0),
        "offset": offset,
        "limit": limit,
        "results": results,
        "facets": facets,
    }


def get_document(identifier: str) -> dict[str, Any]:
    """
    Get a full document by UUID or SAIJ id-infojus (e.g. FA20000057).

    Returns complete metadata and content.
    """
    uuid = identifier

    # Resolve id-infojus to UUID
    if not identifier.startswith("123456789"):
        params = {"r": f"id-infojus:{identifier}", "o": 0, "p": 1, "f": "Total"}
        url = f"{BASE_URL}/busqueda?{urllib.parse.urlencode(params)}"
        data = _fetch_json(url)
        docs = data.get("searchResults", {}).get("documentResultList", [])
        if not docs:
            raise SAIJError(f"Document not found: {identifier}")
        abstract = json.loads(docs[0]["documentAbstract"])
        uuid = abstract["document"]["metadata"]["uuid"]

    url = f"{BASE_URL}/view-document?guid={urllib.parse.quote(uuid)}"
    data = _fetch_json(url)
    doc = json.loads(data["data"])
    content = doc["document"]["content"]
    meta = doc["document"]["metadata"]

    result: dict[str, Any] = {
        "uuid": uuid,
        "id_infojus": content.get("id-infojus", ""),
        "content_type": meta.get("document-content-type", ""),
    }

    # Copy key fields
    for src, dst in [
        ("tribunal", "tribunal"),
        ("actor", "caratula"),
        ("fecha", "fecha"),
        ("tipo-fallo", "tipo_fallo"),
        ("magistrados", "magistrados"),
        ("provincia", "provincia"),
        ("localidad", "localidad"),
        ("instancia", "instancia"),
        ("titulo", "titulo"),
        ("numero-norma", "numero_norma"),
    ]:
        if src in content:
            result[dst] = content[src]

    # Jurisdiction
    if "jurisdiccion" in content:
        j = content["jurisdiccion"]
        result["jurisdiccion"] = j.get("descripcion", j) if isinstance(j, dict) else j

    # Sumario text
    if "texto" in content:
        result["texto"] = content["texto"]

    # Descriptors
    if "descriptores" in content:
        descs = content["descriptores"]
        if isinstance(descs, dict) and "descriptor" in descs:
            dl = descs["descriptor"]
            if not isinstance(dl, list):
                dl = [dl]
            result["descriptores"] = [
                d.get("elegido", {}).get("termino", "") for d in dl
            ]

    # Related sumarios
    sr = content.get("sumarios-relacionados", {})
    if sr:
        ids = sr.get("sumario-relacionado", [])
        if isinstance(ids, str):
            ids = [ids]
        result["sumarios_relacionados"] = ids

    # PDF info
    texto_doc = content.get("texto-doc", {})
    if isinstance(texto_doc, dict) and texto_doc.get("uuid"):
        result["pdf_url"] = (
            f"{BASE_URL}/descarga-archivo"
            f"?guid={texto_doc['uuid']}&name={texto_doc.get('file-name', 'doc.pdf')}"
        )

    # URL
    furl = meta.get("friendly-url", {})
    if furl.get("subdomain") and furl.get("description"):
        result["url"] = (
            f"{BASE_URL}/{furl['subdomain']}/{furl['description']}/{uuid}"
        )

    return result


def get_sumarios(fallo_id: str) -> dict[str, Any]:
    """
    Get all sumarios linked to a fallo.

    Args:
        fallo_id: Fallo id-infojus, e.g. "FA20000057".
    """
    fallo_id = fallo_id.upper()
    if not fallo_id.startswith("FA") and not fallo_id.startswith("SUA"):
        fallo_id = f"FA{fallo_id}"

    # Get the fallo to find sumario IDs
    params = {"r": f"id-infojus:{fallo_id}", "o": 0, "p": 1, "f": "Total"}
    url = f"{BASE_URL}/busqueda?{urllib.parse.urlencode(params)}"
    data = _fetch_json(url)

    docs = data.get("searchResults", {}).get("documentResultList", [])
    if not docs:
        raise SAIJError(f"Fallo not found: {fallo_id}")

    abstract = json.loads(docs[0]["documentAbstract"])
    content = abstract["document"]["content"]
    sr = content.get("sumarios-relacionados", {})
    ids = sr.get("sumario-relacionado", [])
    if isinstance(ids, str):
        ids = [ids]

    if not ids:
        return {"fallo": fallo_id, "total": 0, "sumarios": []}

    # Fetch all sumarios
    or_query = " OR ".join(f"id-infojus:SU{sid}" for sid in ids)
    params = {"r": or_query, "o": 0, "p": 500, "f": "Total"}
    url = f"{BASE_URL}/busqueda?{urllib.parse.urlencode(params)}"
    data = _fetch_json(url)

    sumarios = [
        _parse_result(d)
        for d in data.get("searchResults", {}).get("documentResultList", [])
    ]

    return {"fallo": fallo_id, "total": len(sumarios), "sumarios": sumarios}
