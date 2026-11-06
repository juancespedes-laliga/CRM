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
    fecha_registro: date | None = None
    fecha_ingreso: date | None = None
    renovado: bool | None = None
    fecha_renovado: date | None = None
    vigencia_hasta: date | None = None
    motivo: str | None = None
    campos: list[CampoCambiado] = []


class ListadoCambios(BaseModel):
    items: list[Cambio]
    total: int
    # True si se llego al tope de filas: conviene acotar el rango de fechas.
    truncado: bool = False


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
    estado: str
    fecha_ingreso: date
    renovado: bool
    fecha_renovado: date | None = None
    vencimiento: date
    renovado_por: RenovadoPor | None = None
    titular: TitularRef | None = None
