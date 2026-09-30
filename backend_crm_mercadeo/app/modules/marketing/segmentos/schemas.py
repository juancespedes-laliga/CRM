from typing import Literal

from pydantic import BaseModel, Field


class FiltrosAudiencia(BaseModel):
    """Filtros del consolidado TMPBI1 + INTRANET_VISTA_PLANLIGA
    (GET /segmentos/audiencias)."""

    plan: str | None = Field(
        default="plan_liga",
        description="'plan_liga' ejecuta el consolidado. 'no_plan_liga' responde vacio.",
    )
    uso_plan: str | None = Field(
        default=None,
        description=(
            "Solo aplica junto con plan='plan_liga'. 'con_uso'/None = "
            "comportamiento actual (TMPBI1.TARIFA='PL'). 'sin_uso' = activos "
            "de Plan Liga sin ningun servicio con esa tarifa."
        ),
    )
    sexo: str | None = Field(default=None, description="'F' | 'M' | 'todos'/None.")
    edad_min: int | None = None
    edad_max: int | None = None
    ciudad: str | None = Field(
        default=None,
        description="Valor de TMPBI1.MUNICIPIO (nombre, ej. 'PEREIRA').",
    )
    departamento: str | None = None
    concepto: str | None = None
    servicio: str | None = None
    tipo_vinculacion: str | None = Field(
        default=None,
        description="'particular' | 'empresa' | 'todos'/None (segun TIPO_PLAN).",
    )
    ultimo_uso: str | None = Field(
        default=None,
        description="'90' | '60' | '30' = sin uso en esos dias. None = sin filtro.",
    )
    pagina: int = Field(default=1, ge=1)
    por_pagina: int = Field(default=10, ge=1, le=500)


class AudienciaSegmentoItem(BaseModel):
    """Una persona del consolidado (ultima fila de servicio por identificacion)."""

    IDENTIFICACION: str | None = None
    NOMBRES: str | None = None
    EMPRESA: str | None = None
    SEXO: str | None = None
    EDAD: int | None = None
    CIUDAD: str | None = None
    DEPARTAMENTO: str | None = None
    CORREO: str | None = None
    TELEFONO: str | None = None
    TIPO_PLAN: str | None = None
    CONCEPTO: str | None = None
    SERVICIO: str | None = None
    ESPECIALIDAD: str | None = None
    SERVICIOS_USADOS: int | None = None
    ULTIMO_USO: str | None = None
    TIPO_VINCULACION: str | None = None


class ListadoAudienciaSegmento(BaseModel):
    total: int
    items: list[AudienciaSegmentoItem]


class ValoresDistintos(BaseModel):
    """Lista de valores distintos de una columna de TMPBI1, para poblar
    desplegables de filtro (ciudad, concepto, servicio)."""

    valores: list[str]


class Ubicacion(BaseModel):
    departamento: str
    municipio: str


class ListadoUbicaciones(BaseModel):
    """Pares (departamento, municipio) distintos de TMPBI1, para el
    desplegable en cascada de Departamento -> Ciudad/municipio."""

    ubicaciones: list[Ubicacion]


class ConceptoServicio(BaseModel):
    concepto: str
    servicio: str


class ListadoConceptosServicios(BaseModel):
    """Pares (concepto, servicio) distintos de TMPBI1, para el desplegable
    en cascada de Concepto -> Servicio."""

    pares: list[ConceptoServicio]


# Alias por compatibilidad con imports previos del modulo.
TitularSegmentoItem = AudienciaSegmentoItem
ListadoTitularesSegmento = ListadoAudienciaSegmento


class CategoriaUsoPlan(BaseModel):
    """Activos/con uso/sin uso de un grupo (titulares, beneficiarios o total).
    'Uso' = al menos un servicio con TARIFA = 'PL' en TMPBI1."""

    activos: int
    con_uso: int
    sin_uso: int
    porcentaje_uso: float


class ResumenUsoPlan(BaseModel):
    """GET /segmentos/uso-plan/resumen: cuantos titulares/beneficiarios
    ACTIVOS (INTRANET_PLANLIGA / INTRANET_PLANLIGA_BENEFICIARIO) tienen
    algun servicio con tarifa PL en TMPBI1."""

    total: CategoriaUsoPlan
    titulares: CategoriaUsoPlan
    beneficiarios: CategoriaUsoPlan


class UsoPlanPersona(BaseModel):
    """GET /segmentos/uso-plan/buscar: si un documento es titular o
    beneficiario (el que se encuentre primero) y si ha usado el plan."""

    documento: str
    tipo: Literal["titular", "beneficiario"]
    nombre: str
    estado: str
    ha_usado: bool
    servicios_usados: int
    ultimo_uso: str | None = None
