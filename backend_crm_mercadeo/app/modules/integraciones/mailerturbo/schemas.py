from pydantic import BaseModel, Field


class ListaMT(BaseModel):
    id: int
    titulo: str
    estado: str
    total_correos: int
    total_activos: int
    total_rebotes: int = 0
    total_salidas: int = 0
    total_envios: int = 0
    total_vistas: int = 0
    total_clicks: int = 0
    total_telefonos: int = 0
    tipo: str | None = None
    fecha_creacion: str | None = None


class ListadoListasMT(BaseModel):
    listas: list[ListaMT]


class CrearListaMT(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)


class PlantillaMT(BaseModel):
    id: int
    nombre: str


class ListadoPlantillasMT(BaseModel):
    plantillas: list[PlantillaMT]


class PerfilEnvioMT(BaseModel):
    id: int
    titulo: str
    correo: str
    estado: str


class ListadoPerfilesMT(BaseModel):
    perfiles: list[PerfilEnvioMT]


class CampanaMT(BaseModel):
    id: int
    nombre: str
    asunto: str | None = None
    estado: str
    tipo: str
    fecha: str | None = None
    listas: str = ""
    total_envios: int = 0
    total_vistas: int = 0
    porcentaje_vistas: float = 0
    total_clicks: int = 0
    porcentaje_clicks: float = 0
    total_rebotes: int = 0
    total_salidas: int = 0


class ListadoCampanasMT(BaseModel):
    campanas: list[CampanaMT]
    total: int
    total_paginas: int


class EstadisticasCampanaMT(BaseModel):
    total_envios: int = 0
    total_vistas: int = 0
    porcentaje_vistas: float = 0
    total_clicks: int = 0
    porcentaje_clicks: float = 0
    vistas_landing: int = 0
    total_rebotes: int = 0
    porcentaje_rebotes: float = 0
    total_salidas: int = 0
    porcentaje_salidas: float = 0
    total_rechazados: int = 0


class DetalleCampanaMT(BaseModel):
    """ObtenerInfoCampana (sin el HTML del correo)."""

    id: int
    nombre: str
    asunto: str | None = None
    estado: str
    tipo: str
    fecha: str | None = None
    fecha_programacion: str | None = None
    perfil_envio: str | None = None
    correo_perfil_envio: str | None = None
    listas: str | None = None
    usuario_envio: str | None = None
    estadisticas: EstadisticasCampanaMT


class DestinatarioCampanaMT(BaseModel):
    """Una fila de ObtenerCorreosEnviadosCampana (+ el link si hizo clic)."""

    nombre: str
    correo: str
    telefono: str | None = None
    estado_envio: str
    resultado_envio: str
    fecha_enviado: str | None = None
    abrio: bool = False
    fecha_apertura: str | None = None
    clic: bool = False
    fecha_clic: str | None = None
    links: list[str] = []
    baja: bool = False
    fecha_baja: str | None = None
    vista_landing: bool = False


class DestinatariosCampanaMT(BaseModel):
    destinatarios: list[DestinatarioCampanaMT]
    total: int


class ContactoMT(BaseModel):
    nombre: str = ""
    apellido: str = ""
    correo: str
    telefono: str = ""
    documento: str | None = None
    ciudad: str | None = None


class FiltrosAudienciaMT(BaseModel):
    """Mismos filtros de GET /segmentos/audiencias (sin paginacion): se usan cuando
    en Audiencias se elige "Seleccionar toda la audiencia" y el backend arma la
    lista completa en vez de recibir solo las filas que el navegador ya cargo."""

    plan: str | None = "plan_liga"
    uso_plan: str | None = None
    sexo: str | None = None
    edad_min: int | None = None
    edad_max: int | None = None
    ciudad: str | None = None
    departamento: str | None = None
    concepto: str | None = None
    servicio: str | None = None
    tipo_vinculacion: str | None = None
    ultimo_uso: str | None = None
    # Documentos que el usuario desmarco a mano despues de "Seleccionar todo".
    excluir_documentos: list[str] = []


class CorreoContactoMT(BaseModel):
    correo: str
    enviar_campana: str | None = None
    estado: str | None = None


class InfoContactoMT(BaseModel):
    """Contacto tal como esta en MailerTurbo (ObtenerInfoContacto)."""

    id: int
    nombre: str
    apellido: str
    telefono: str
    correos: list[CorreoContactoMT]
    campos_dinamicos: dict[str, str]


class SincronizarContactosMT(BaseModel):
    id_lista: int
    contactos: list[ContactoMT] = []
    audiencia: FiltrosAudienciaMT | None = None
    etiquetas: list[str] = []


class FalloContactoMT(BaseModel):
    correo: str
    error: str


class ResultadoSincronizacionMT(BaseModel):
    total: int
    creados: int
    actualizados: int
    fallidos: int
    fallos: list[FalloContactoMT]


class EnviarCampanaMT(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    asunto: str = Field(min_length=1, max_length=300)
    id_perfil_envio: int
    id_plantilla: int | None = None
    html: str | None = None
    id_listas: list[int] = []
    contactos: list[ContactoMT] = []
    audiencia: FiltrosAudienciaMT | None = None
    nombre_lista: str | None = None
    id_listas_excluir: list[int] = []
    # 'YYYY-MM-DD HH:MM:SS' (hora Colombia) o None para enviar de inmediato.
    fecha_programacion: str | None = None


class ResultadoEnvioCampanaMT(BaseModel):
    id_campana: int
    explicacion: str | None = None
    total_contactos: int | None = None


class SesionMT(BaseModel):
    """Token para abrir MailerTurbo ya logueado: el navegador hace POST de
    `tokensesion` a `url_inicio_sesion`."""

    tokensesion: str
    fecha_expiracion: str | None
    url_inicio_sesion: str = "https://mailerturbo.com/iniciar-sesion"


class UsoMensualMT(BaseModel):
    """Correos enviados en el mes actual frente al cupo mensual del plan.
    `limite_mensual` es None si no se configuro MAILERTURBO_LIMITE_MENSUAL."""

    mes: str
    enviados: int
    limite_mensual: int | None
    disponibles: int | None
