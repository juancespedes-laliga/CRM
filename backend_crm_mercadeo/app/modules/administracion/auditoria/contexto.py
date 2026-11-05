"""Quien, desde donde y como se hace una accion, para la auditoria.

`contexto_auditoria` es una dependencia de FastAPI: se resuelve una vez por
request y se le pasa a los services que registran auditoria (ver
titulares_beneficiarios/dependencies.py). El frontend puede mandar:

- X-Auditoria-Origen: 'excel' durante una carga masiva (por defecto 'manual').
- X-Auditoria-Lote: nombre del archivo de la carga (URL-encoded), que queda
  como motivo de cada cambio de esa carga.
"""

from dataclasses import dataclass
from urllib.parse import unquote

from fastapi import Depends, Request

from app.core.dependencies import get_current_username

ORIGENES = {"manual", "excel", "grupo", "sistema"}


@dataclass(frozen=True)
class ContextoAuditoria:
    username: str | None
    ip: str | None = None
    origen: str = "manual"
    lote: str | None = None


# Para procesos que no vienen de un request (tareas programadas, scripts).
CONTEXTO_SISTEMA = ContextoAuditoria(username=None, origen="sistema")


def _ip_cliente(request: Request) -> str | None:
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[0].strip()[:45] or None
    return request.client.host[:45] if request.client else None


def contexto_auditoria(
    request: Request,
    username: str = Depends(get_current_username),
) -> ContextoAuditoria:
    origen = (request.headers.get("x-auditoria-origen") or "manual").strip().lower()
    if origen not in ORIGENES:
        origen = "manual"
    lote = request.headers.get("x-auditoria-lote")
    lote = unquote(lote).strip()[:200] if lote else None
    return ContextoAuditoria(username=username, ip=_ip_cliente(request), origen=origen, lote=lote or None)
