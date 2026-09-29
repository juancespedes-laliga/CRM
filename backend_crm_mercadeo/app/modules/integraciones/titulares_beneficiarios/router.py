import io
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font

from app.core.dependencies import get_current_username
from app.modules.integraciones.titulares_beneficiarios.dependencies import (
    get_titulares_beneficiarios_service,
)
from app.modules.integraciones.titulares_beneficiarios.schemas import (
    ActivacionBeneficiarioResultado,
    ActivacionTitularResultado,
    BeneficiarioActivar,
    BeneficiarioCrear,
    BeneficiarioDetalle,
    BeneficiarioUpdate,
    CambioFechaIngresoGrupo,
    CambioFechaIngresoGrupoResultado,
    CambioTitularBeneficiario,
    TipoPlanValores,
    CreacionBeneficiarioResultado,
    CreacionTitularResultado,
    DesactivacionBeneficiarioResultado,
    DesactivacionTitularResultado,
    ListadoRenovacionesMes,
    ListadoTitularesPaginado,
    PlanItem,
    PlanNombre,
    ReemplazoBeneficiarioResultado,
    ReemplazoPersona,
    ReemplazoTitularResultado,
    ResumenTitularesBeneficiarios,
    TitularActivar,
    TitularColorActualizar,
    TitularCrear,
    TitularDetalle,
    TitularUpdate,
)
from app.modules.integraciones.titulares_beneficiarios.service import (
    TitularesBeneficiariosService,
)

router = APIRouter(
    prefix="/titulares-beneficiarios",
    tags=["Titulares y Beneficiarios"],
    dependencies=[Depends(get_current_username)],
)

COLUMNAS_EXPORTACION = [
    ("TIPO_REGISTRO", "Tipo"),
    ("ID_TITULAR", "ID Titular"),
    ("TIPO_DOCUMENTO", "Tipo Documento"),
    ("DOCUMENTO", "Documento"),
    ("NOMBRE1", "Nombre 1"),
    ("NOMBRE2", "Nombre 2"),
    ("APELLIDO1", "Apellido 1"),
    ("APELLIDO2", "Apellido 2"),
    ("EMPRESA", "Empresa"),
    ("PLAN", "Plan"),
    ("TELEFONO", "Telefono"),
    ("CORREO", "Correo"),
    ("FECHA_INGRESO", "Fecha Ingreso"),
    ("ESTADO", "Estado"),
]


@router.get("/resumen", response_model=ResumenTitularesBeneficiarios)
def get_resumen(
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> ResumenTitularesBeneficiarios:
    return service.resumen()


@router.get("/listado", response_model=ListadoTitularesPaginado)
def get_listado(
    limit: int = 6,
    offset: int = 0,
    estado: str | None = None,
    tipo_plan_id: str | None = None,
    sexo: str | None = None,
    edad: str | None = None,
    busqueda: str | None = None,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> ListadoTitularesPaginado:
    return service.listar_titulares(limit, offset, estado, tipo_plan_id, sexo, edad, busqueda)


@router.get(
    "/renovaciones",
    response_model=ListadoRenovacionesMes,
    summary=(
        "Titulares cuyo FECHA_INGRESO cae en el mes/anio dado (se activaron o "
        "renovaron ese mes), separando renovaciones (RENOVADO='S') de altas "
        "nuevas (RENOVADO='N'), con el ultimo contacto de bitacora de cada uno."
    ),
)
def get_renovaciones_mes(
    anio: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> ListadoRenovacionesMes:
    return service.listar_renovaciones_mes(anio, mes)


@router.put(
    "/{id_titular}/color",
    summary="Fija (o quita, con COLOR=null) el color que el equipo le asigna a mano a un titular.",
)
def poner_color_titular(
    id_titular: int,
    data: TitularColorActualizar,
    username: str = Depends(get_current_username),
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> dict:
    if data.COLOR is None:
        service.quitar_color_titular(id_titular)
    else:
        service.establecer_color_titular(id_titular, data.COLOR, username)
    return {"COLOR": data.COLOR}


@router.get("/exportar")
def exportar_titulares_beneficiarios(
    estado: str | None = None,
    tipo_plan_id: str | None = None,
    sexo: str | None = None,
    edad: str | None = None,
    busqueda: str | None = None,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> Response:
    filas = service.exportar_titulares_beneficiarios(
        estado, tipo_plan_id, sexo, edad, busqueda
    )

    wb = Workbook(write_only=True)
    ws = wb.create_sheet("Titulares y Beneficiarios")

    encabezados = []
    for _, titulo in COLUMNAS_EXPORTACION:
        celda = WriteOnlyCell(ws, value=titulo)
        celda.font = Font(bold=True)
        encabezados.append(celda)
    ws.append(encabezados)

    claves = [clave for clave, _ in COLUMNAS_EXPORTACION]
    for fila in filas:
        ws.append([fila.get(clave) for clave in claves])

    buffer = io.BytesIO()
    wb.save(buffer)

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=titulares_beneficiarios.xlsx"
        },
    )


@router.get("/planes", response_model=list[PlanItem])
def get_planes(
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> list[PlanItem]:
    return service.listar_planes()


@router.get("/planes/nombres", response_model=list[PlanNombre])
def get_nombres_planes(
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> list[PlanNombre]:
    return service.listar_nombres_planes()


@router.get("/grupo/conteo", response_model=CambioFechaIngresoGrupoResultado)
def get_conteo_grupo_activo(
    empresa: str | None = None,
    tipo_plan: str | None = None,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> CambioFechaIngresoGrupoResultado:
    return service.contar_grupo_activo(empresa, tipo_plan)


@router.get(
    "/grupo/tipos-plan",
    response_model=TipoPlanValores,
    summary="Valores distintos de TIPO_PLAN, para elegir un grupo por tipo de plan en vez de por empresa.",
)
def get_tipos_plan(
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> TipoPlanValores:
    return TipoPlanValores(valores=service.listar_tipos_plan())


@router.post("/grupo/fecha-ingreso", response_model=CambioFechaIngresoGrupoResultado)
def cambiar_fecha_ingreso_grupo(
    data: CambioFechaIngresoGrupo,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> CambioFechaIngresoGrupoResultado:
    return service.cambiar_fecha_ingreso_grupo(data)


@router.get("/{id_titular}/beneficiarios", response_model=list[BeneficiarioDetalle])
def get_beneficiarios(
    id_titular: int,
    estado: Literal["A", "I"] = Query(
        "A",
        description="A = activos, I = inactivos.",
    ),
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
):
    return service.listar_beneficiarios(id_titular, estado)


@router.post(
    "/{id_titular}/beneficiarios",
    response_model=CreacionBeneficiarioResultado,
    status_code=status.HTTP_201_CREATED,
)
def crear_beneficiario(
    id_titular: int,
    data: BeneficiarioCrear,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> CreacionBeneficiarioResultado:
    return service.crear_beneficiario(id_titular, data)


@router.patch("/{id_titular}/beneficiarios/{id_beneficiario}", response_model=BeneficiarioDetalle)
def update_beneficiario(
    id_titular: int,
    id_beneficiario: int,
    data: BeneficiarioUpdate,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> BeneficiarioDetalle:
    return service.actualizar_beneficiario(id_titular, id_beneficiario, data)


@router.post(
    "/{id_titular}/beneficiarios/{id_beneficiario}/reemplazar",
    response_model=ReemplazoBeneficiarioResultado,
    status_code=status.HTTP_201_CREATED,
)
def reemplazar_beneficiario(
    id_titular: int,
    id_beneficiario: int,
    data: ReemplazoPersona,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> ReemplazoBeneficiarioResultado:
    return service.reemplazar_beneficiario(id_titular, id_beneficiario, data)


@router.post(
    "/{id_titular}/beneficiarios/{id_beneficiario}/activar",
    response_model=ActivacionBeneficiarioResultado,
)
def activar_beneficiario(
    id_titular: int,
    id_beneficiario: int,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> ActivacionBeneficiarioResultado:
    return service.activar_beneficiario(id_titular, id_beneficiario)


@router.post(
    "/{id_titular}/beneficiarios/{id_beneficiario}/desactivar",
    response_model=DesactivacionBeneficiarioResultado,
)
def desactivar_beneficiario(
    id_titular: int,
    id_beneficiario: int,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> DesactivacionBeneficiarioResultado:
    return service.desactivar_beneficiario(id_titular, id_beneficiario)


@router.post(
    "/beneficiarios/{documento}/activar",
    response_model=ActivacionBeneficiarioResultado,
)
def activar_beneficiario_sin_titular(
    documento: str,
    data: BeneficiarioActivar,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> ActivacionBeneficiarioResultado:
    return service.activar_beneficiario_sin_titular(documento, data.FECHA_INGRESO)


@router.post(
    "/beneficiarios/{documento}/desactivar",
    response_model=DesactivacionBeneficiarioResultado,
)
def desactivar_beneficiario_sin_titular(
    documento: str,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> DesactivacionBeneficiarioResultado:
    return service.desactivar_beneficiario_sin_titular(documento)


@router.post(
    "/beneficiarios/{id_beneficiario}/cambiar-titular",
    response_model=BeneficiarioDetalle,
)
def cambiar_titular_beneficiario(
    id_beneficiario: int,
    data: CambioTitularBeneficiario,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> BeneficiarioDetalle:
    return service.cambiar_titular_beneficiario(id_beneficiario, data.DOCUMENTO_TITULAR_NUEVO)


@router.post(
    "",
    response_model=CreacionTitularResultado,
    status_code=status.HTTP_201_CREATED,
)
def crear_titular(
    data: TitularCrear,
    username: str = Depends(get_current_username),
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> CreacionTitularResultado:
    return service.crear_titular(data, username)


@router.get("/{id_titular}", response_model=TitularDetalle)
def get_titular(
    id_titular: int,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> TitularDetalle:
    return service.obtener_titular(id_titular)


@router.patch("/{id_titular}", response_model=TitularDetalle)
def update_titular(
    id_titular: int,
    data: TitularUpdate,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> TitularDetalle:
    return service.actualizar_titular(id_titular, data)


@router.post(
    "/{id_titular}/reemplazar",
    response_model=ReemplazoTitularResultado,
    status_code=status.HTTP_201_CREATED,
)
def reemplazar_titular(
    id_titular: int,
    data: ReemplazoPersona,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> ReemplazoTitularResultado:
    return service.reemplazar_titular(id_titular, data)


@router.post("/{id_titular}/activar", response_model=ActivacionTitularResultado)
def activar_titular(
    id_titular: int,
    data: TitularActivar,
    username: str = Depends(get_current_username),
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> ActivacionTitularResultado:
    return service.activar_titular(
        id_titular,
        data.FECHA_INGRESO,
        data.APLICAR_A_GRUPO,
        data.CAMBIAR_PLAN,
        data.TIPO_PLAN,
        data.TIPO_PLAN_ID,
        username,
    )


@router.post("/{id_titular}/desactivar", response_model=DesactivacionTitularResultado)
def desactivar_titular(
    id_titular: int,
    service: TitularesBeneficiariosService = Depends(get_titulares_beneficiarios_service),
) -> DesactivacionTitularResultado:
    return service.desactivar_titular(id_titular)
