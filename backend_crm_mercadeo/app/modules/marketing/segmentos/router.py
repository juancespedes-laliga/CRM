from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_username
from app.modules.marketing.segmentos.dependencies import get_segmentos_service
from app.modules.marketing.segmentos.schemas import (
    ConceptoServicio,
    FiltrosAudiencia,
    ListadoAudienciaSegmento,
    ListadoConceptosServicios,
    ListadoUbicaciones,
    ResumenUsoPlan,
    Ubicacion,
    UsoPlanPersona,
    ValoresDistintos,
)
from app.modules.marketing.segmentos.service import SegmentosService

router = APIRouter(
    prefix="/segmentos",
    tags=["Segmentos"],
    dependencies=[Depends(get_current_username)],
)


@router.get("/audiencias", response_model=ListadoAudienciaSegmento)
def obtener_audiencia(
    plan: Literal["plan_liga", "no_plan_liga"] | None = Query(
        "plan_liga",
        description=(
            "'plan_liga' ejecuta el consolidado TMPBI1 + INTRANET_VISTA_PLANLIGA "
            "(solo afiliados activos). 'no_plan_liga' ejecuta TMPBI1 + ABPAC "
            "excluyendo a los afiliados ACTIVOS de Plan Liga (incluye inactivos)."
        ),
    ),
    sexo: Literal["F", "M", "todos"] | None = Query(
        None, description="None o 'todos' = sin filtro."
    ),
    edad_min: int | None = Query(None, ge=0, le=120),
    edad_max: int | None = Query(None, ge=0, le=120),
    ciudad: str | None = Query(
        None, description="TMPBI1.MUNICIPIO (ej. 'PEREIRA')."
    ),
    departamento: str | None = Query(None),
    concepto: str | None = Query(None),
    servicio: str | None = Query(None),
    tipo_vinculacion: Literal["particular", "empresa", "todos"] | None = Query(
        None,
        description="Segun TIPO_PLAN = PARTICULAR u otro.",
    ),
    ultimo_uso: Literal["90", "60", "30"] | None = Query(
        None,
        description="Sin uso en los ultimos N dias (ULTIMO_USO <= SYSDATE - N).",
    ),
    uso_plan: Literal["con_uso", "sin_uso", "todos"] | None = Query(
        None,
        description=(
            "Solo aplica junto con plan='plan_liga'. 'con_uso'/None/'todos' = "
            "comportamiento actual (TMPBI1.TARIFA='PL'). 'sin_uso' = activos "
            "de Plan Liga sin ningun servicio con esa tarifa (no admite "
            "concepto/servicio/ultimo_uso: nadie en ese grupo tiene fila en TMPBI1)."
        ),
    ),
    pagina: int = Query(1, ge=1, description="Pagina a mostrar (1-indexada)."),
    por_pagina: int = Query(
        10, ge=1, le=500, description="Cuantas personas traer por pagina."
    ),
    service: SegmentosService = Depends(get_segmentos_service),
) -> ListadoAudienciaSegmento:
    return service.obtener_audiencia(
        FiltrosAudiencia(
            plan=plan,
            sexo=sexo,
            edad_min=edad_min,
            edad_max=edad_max,
            ciudad=ciudad,
            departamento=departamento,
            concepto=concepto,
            servicio=servicio,
            tipo_vinculacion=tipo_vinculacion,
            ultimo_uso=ultimo_uso,
            uso_plan=uso_plan,
            pagina=pagina,
            por_pagina=por_pagina,
        )
    )


@router.get(
    "/ciudades",
    response_model=ValoresDistintos,
    summary="Ciudades/municipios distintos en TMPBI1 (para el desplegable de filtro).",
)
def obtener_ciudades(
    service: SegmentosService = Depends(get_segmentos_service),
) -> ValoresDistintos:
    return ValoresDistintos(valores=service.obtener_ciudades())


@router.get(
    "/ubicaciones",
    response_model=ListadoUbicaciones,
    summary=(
        "Pares (departamento, municipio) distintos en TMPBI1, para el "
        "desplegable en cascada Departamento -> Ciudad/municipio."
    ),
)
def obtener_ubicaciones(
    service: SegmentosService = Depends(get_segmentos_service),
) -> ListadoUbicaciones:
    return ListadoUbicaciones(
        ubicaciones=[Ubicacion(**u) for u in service.obtener_ubicaciones()]
    )


@router.get(
    "/conceptos",
    response_model=ValoresDistintos,
    summary="Conceptos distintos en TMPBI1 (para el desplegable de filtro).",
)
def obtener_conceptos(
    service: SegmentosService = Depends(get_segmentos_service),
) -> ValoresDistintos:
    return ValoresDistintos(valores=service.obtener_conceptos())


@router.get(
    "/conceptos-servicios",
    response_model=ListadoConceptosServicios,
    summary=(
        "Pares (concepto, servicio) distintos en TMPBI1, para el "
        "desplegable en cascada Concepto -> Servicio."
    ),
)
def obtener_conceptos_servicios(
    service: SegmentosService = Depends(get_segmentos_service),
) -> ListadoConceptosServicios:
    return ListadoConceptosServicios(
        pares=[ConceptoServicio(**p) for p in service.obtener_conceptos_servicios()]
    )


@router.get(
    "/servicios",
    response_model=ValoresDistintos,
    summary="Servicios distintos en TMPBI1 (para el desplegable de filtro).",
)
def obtener_servicios(
    service: SegmentosService = Depends(get_segmentos_service),
) -> ValoresDistintos:
    return ValoresDistintos(valores=service.obtener_servicios())


@router.get(
    "/uso-plan/resumen",
    response_model=ResumenUsoPlan,
    summary=(
        "Resumen de uso de Plan Liga: titulares/beneficiarios ACTIVOS, "
        "cuantos tienen algun servicio con TMPBI1.TARIFA='PL' y cuantos no."
    ),
)
def obtener_resumen_uso_plan(
    service: SegmentosService = Depends(get_segmentos_service),
) -> ResumenUsoPlan:
    return service.obtener_resumen_uso_plan()


@router.get(
    "/uso-plan/buscar",
    response_model=UsoPlanPersona,
    summary="Busca un titular o beneficiario por documento y dice si ha usado el plan.",
)
def buscar_uso_plan(
    documento: str = Query(..., min_length=1),
    service: SegmentosService = Depends(get_segmentos_service),
) -> UsoPlanPersona:
    return service.buscar_uso_plan(documento)
