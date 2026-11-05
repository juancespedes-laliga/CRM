from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, requiere_permiso
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
    summary="Log de cambios. modulo acepta varios separados por coma (ej. titulares,beneficiarios).",
)
def listar_cambios(
    modulo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    service: AuditoriaService = Depends(get_auditoria_service),
) -> ListadoCambios:
    return service.listar_cambios(modulo, desde, hasta)


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
