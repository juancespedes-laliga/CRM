from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class CorreoBienvenida(BaseModel):
    NOMBRE: str
    CORREO: EmailStr


class CorreoRegistro(BaseModel):
    NOMBRE: str
    CORREO: EmailStr


class CorreoEnviadoResultado(BaseModel):
    enviado: bool = True


class TitularPorVencer(BaseModel):
    """Titular activo con el plan proximo a vencer (o recien vencido). Trae
    listo lo que necesita la plantilla de vencimiento: NOMBRE, CORREO, DIAS y
    FECHA_FIN_TXT (mapean a {{ nombre }} / {{ dias }} / {{ fecha_fin }})."""

    ID: int
    TIPO: Optional[str] = None
    DOCUMENTO: Optional[str] = None
    NOMBRE: Optional[str] = None
    CORREO: Optional[str] = None
    TELEFONO: Optional[str] = None
    EMPRESA: Optional[str] = None
    TIPO_PLAN: Optional[str] = None
    FECHA_INGRESO: Optional[date] = None
    FECHA_FIN: Optional[date] = None
    DIAS: int
    FECHA_FIN_TXT: str
    RENOVADO: Optional[str] = None
    VENCIDO: bool
    # True si su fecha de vencimiento ya cae en un rango cubierto por un envio
    # anterior (a este titular ya se le mando el recordatorio).
    YA_ENVIADO: bool = False


class EstadoUltimoEnvio(BaseModel):
    """Resumen de la ultima corrida del envio de recordatorios (fila mas
    reciente de mercadeo_crm_historial_procesos con tipo de vencimiento)."""

    ultimo_envio: Optional[datetime] = None
    ultimo_total: Optional[int] = None
    ultimo_enviados: Optional[int] = None
    ultimo_fallidos: Optional[int] = None
    ejecutado_por: Optional[str] = None
    # Ventana de dias con la que se corrio el ultimo envio. None en corridas
    # viejas sin este dato.
    dias_previos: Optional[int] = None
    dias_vencidos: Optional[int] = None
    # Union de todas las ventanas de FECHA_FIN ya cubiertas por envios
    # anteriores: a los titulares que vencen dentro de [desde, hasta] ya se les
    # mando el recordatorio.
    cubierto_desde: Optional[date] = None
    cubierto_hasta: Optional[date] = None


class ListadoTitularesPorVencer(BaseModel):
    total: int
    # Cuantos del total NO han recibido el recordatorio todavia / cuantos si.
    nuevos: int
    ya_enviados: int
    dias_previos: int
    dias_vencidos: int
    estado_envio: EstadoUltimoEnvio
    items: list[TitularPorVencer]


class FalloEnvio(BaseModel):
    DOCUMENTO: Optional[str] = None
    NOMBRE: Optional[str] = None
    CORREO: Optional[str] = None
    error: str


class EnvioRecordatoriosResultado(BaseModel):
    total: int            # cuantos entraban en la ventana pedida
    a_enviar: int         # a cuantos se intento enviar (segun el modo)
    enviados: int
    fallidos: int
    omitidos_ya_enviados: int  # los que se saltaron por haber recibido ya el aviso
    fallos: list[FalloEnvio]
    estado_envio: EstadoUltimoEnvio


class HistorialEnvioItem(BaseModel):
    """Una corrida pasada del envio de recordatorios, guardada en
    mercadeo_crm_historial_procesos (tipo 'correo_vencimiento_plan_liga')."""

    fecha: Optional[datetime] = None
    enviados: int
    fallidos: int
    total: int
    ejecutado_por: Optional[str] = None
    dias_previos: Optional[int] = None
    dias_vencidos: Optional[int] = None
    fallos: list[FalloEnvio]


class EmpresaPorVencer(BaseModel):
    """Una empresa con uno o mas titulares (Plan Liga Empresarial) por vencer
    en la ventana consultada."""

    EMPRESA: str
    TOTAL: int
    titulares: list[TitularPorVencer]


class ListadoEmpresasPorVencer(BaseModel):
    total_empresas: int
    total_titulares: int
    dias_previos: int
    dias_vencidos: int
    empresas: list[EmpresaPorVencer]


class CampanaEnvioRequest(BaseModel):
    asunto: str
    html: str                       # HTML completo de la plantilla (ya viene con estilos inline)
    destinatarios: list[EmailStr]   # se valida cada correo


class CampanaFallo(BaseModel):
    correo: str
    error: str


class CampanaEnvioResultado(BaseModel):
    total: int
    enviados: int
    fallidos: int
    fallos: list[CampanaFallo]


class UsoDiarioCorreos(BaseModel):
    """Correos mandados hoy por Gmail frente al tope diario (GMAIL_LIMITE_DIARIO)."""

    fecha: str
    enviados: int
    limite: int | None
    disponibles: int | None
