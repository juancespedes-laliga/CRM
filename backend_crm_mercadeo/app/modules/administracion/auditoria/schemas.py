from datetime import date, datetime

from pydantic import BaseModel


class CampoCambiado(BaseModel):
    campo: str
    etiqueta: str
    antes: str | None = None
    despues: str | None = None


class TitularGrupo(BaseModel):
    id: int
    nombre: str
    documento: str | None = None


class Cambio(BaseModel):
    id: int
    fecha: datetime
    usuario_id: int
    usuario: str
    nombre_usuario: str
    rol: str | None = None
    ip: str | None = None
    accion: str
    origen: str
    lote_id: str | None = None
    modulo: str
    registro_id: int
    registro_nombre: str
    documento: str | None = None
    titular: TitularGrupo | None = None
    id_titular: int | None = None
    id_beneficiario: int | None = None
    estado_antes: str | None = None
    estado_despues: str | None = None
    fecha_inscripcion: date | None = None
    fecha_registro: datetime | None = None
    fecha_ingreso: date | None = None
    renovado: bool | None = None
    fecha_renovado: date | None = None
    vigencia_hasta: date | None = None
    motivo: str | None = None
    campos: list[CampoCambiado] = []


class ResumenCambios(BaseModel):
    total: int = 0
    usuarios: int = 0
    cambios_estado: int = 0
    renovaciones: int = 0
    masivos: int = 0


class UsuarioCambio(BaseModel):
    id: int  # 0 = proceso automatico
    usuario: str
    nombre: str


class ListadoCambios(BaseModel):
    items: list[Cambio]
    # Total de cambios que cumplen los filtros (todas las paginas).
    total: int
    pagina: int = 1
    por_pagina: int = 20
    # True si no cupieron todos en la pagina pedida (solo pasa al exportar con el tope).
    truncado: bool = False
    resumen: ResumenCambios = ResumenCambios()
    # Opciones de los filtros Usuario y Estado dentro del modulo y rango de fechas.
    usuarios: list[UsuarioCambio] = []
    estados: list[str] = []


class ResumenModulo(BaseModel):
    modulo: str
    total: int
    ultimo_cambio: datetime | None = None


class RenovadoPor(BaseModel):
    nombre: str
    usuario: str


class TitularRef(BaseModel):
    id: int
    nombre: str


class Renovacion(BaseModel):
    tipo: str  # 'titular' | 'beneficiario'
    id: int
    nombre: str
    documento: str
    empresa: str | None = None
    plan: str | None = None
    # Texto libre TIPO_PLAN (ej. 'CYP'); 'plan' es el nombre del catalogo.
    tipo_plan: str | None = None
    estado: str
    fecha_ingreso: date
    renovado: bool
    fecha_renovado: date | None = None
    vencimiento: date
    renovado_por: RenovadoPor | None = None
    titular: TitularRef | None = None
