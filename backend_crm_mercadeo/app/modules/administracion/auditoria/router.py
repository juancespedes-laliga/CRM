from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, requiere_permiso
from app.modules.administracion.auditoria.repository import LIMITE_CAMBIOS
from app.modules.administracion.auditoria.schemas import (
    Cambio,
    ListadoCambios,
    Renovacion,
    ResumenModulo,
)
from app.modules.administracion.auditoria.service import AuditoriaService

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoria"],
    dependencies=[Depends(requiere_permiso("auditoria:ver"))],
)


def get_auditoria_service(db: Session = Depends(get_db)) -> AuditoriaService:
    return AuditoriaService(db)


@router.get("/modulos", response_model=list[ResumenModulo], summary="Conteo de cambios por modulo.")
def resumen_modulos(
    desde: date | None = None,
    hasta: date | None = None,
    service: AuditoriaService = Depends(get_auditoria_service),
) -> list[ResumenModulo]:
    return service.resumen_modulos(desde, hasta)


@router.get(
    "/cambios",
    response_model=ListadoCambios,
    summary=(
        "Log de cambios paginado y filtrado en el servidor. modulo acepta varios separados por coma "
        "(ej. titulares,beneficiarios); buscar compara documento, nombre, IDs y usuario."
    ),
)
def listar_cambios(
    modulo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    submodulo: str | None = None,
    buscar: str | None = None,
    accion: str | None = None,
    usuario: int | None = Query(None, description="0 = proceso automatico (sin usuario)."),
    origen: str | None = None,
    estado: str | None = None,
    renovado: bool | None = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=LIMITE_CAMBIOS),
    service: AuditoriaService = Depends(get_auditoria_service),
) -> ListadoCambios:
    return service.listar_cambios(
        modulo,
        desde,
        hasta,
        submodulo=submodulo,
        buscar=buscar,
        accion=accion,
        usuario=usuario,
        origen=origen,
        estado=estado,
        renovado=renovado,
        pagina=pagina,
        por_pagina=por_pagina,
    )


@router.get("/cambios/{id_cambio}", response_model=Cambio)
def obtener_cambio(
    id_cambio: int,
    service: AuditoriaService = Depends(get_auditoria_service),
) -> Cambio:
    return service.obtener_cambio(id_cambio)


@router.get("/historial", response_model=list[Cambio], summary="Todo lo que se le ha hecho a un registro.")
def historial(
    modulo: str,
    registro_id: int,
    service: AuditoriaService = Depends(get_auditoria_service),
) -> list[Cambio]:
    return service.historial(modulo, registro_id)


@router.get(
    "/renovaciones",
    response_model=list[Renovacion],
    summary="Titulares y beneficiarios de Plan Liga con su estado de renovacion y vencimiento.",
)
def renovaciones(
    tipo: Literal["titular", "beneficiario"] | None = Query(None),
    service: AuditoriaService = Depends(get_auditoria_service),
) -> list[Renovacion]:
    return service.renovaciones(tipo)
