import json
import logging
from datetime import date, datetime, timedelta, timezone

# Las fechas que este backend escribe son UTC (datetime.now(timezone.utc)), pero
# Oracle las devuelve "naive". Se les vuelve a marcar UTC antes de serializarlas
# para que el frontend (new Date()) las convierta bien a hora local.

from sqlalchemy.orm import Session

from app.core.email import enviar_correo, enviar_correo_plantilla, verificar_cupo
from app.core.exceptions import ForbiddenError
from app.models import Importacion
from app.modules.notificaciones.correos.repository import CorreosRepository
from app.modules.notificaciones.correos.schemas import (
    CampanaEnvioRequest,
    CampanaEnvioResultado,
    CampanaFallo,
    EmpresaPorVencer,
    EnvioRecordatoriosResultado,
    EstadoUltimoEnvio,
    FalloEnvio,
    HistorialEnvioItem,
    ListadoEmpresasPorVencer,
    ListadoTitularesPorVencer,
    TitularPorVencer,
)

logger = logging.getLogger(__name__)

PLANTILLA_VENCIMIENTO = "Vencimiento (1).html"
ASUNTO_VENCIMIENTO = "Tu membresía Plan Liga está por vencer"

# Permiso (modulo:accion en INTRANET_PERMISOS_APP) para disparar el envio de
# recordatorios. Solo lo revisa el envio; ver la lista no lo exige.
PERMISO_ENVIAR_RECORDATORIO = "recordatorios:gestionar"
PERMISO_ENVIAR_CAMPANA = "campanas:gestionar"


def _a_fecha(valor) -> date | None:
    if valor is None:
        return None
    return valor.date() if isinstance(valor, datetime) else valor


def _utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class CorreosService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CorreosRepository(db)

    # ------------------------------------------------------------------
    # Estado / historial (mercadeo_crm_historial_procesos)
    # ------------------------------------------------------------------
    @staticmethod
    def _fallos_de(fila: Importacion) -> list[FalloEnvio]:
        if not fila.detalle_errores:
            return []
        try:
            return [FalloEnvio(**f) for f in json.loads(fila.detalle_errores)]
        except (ValueError, TypeError):
            return []

    @staticmethod
    def _rango_de(fila: Importacion) -> tuple[int | None, int | None]:
        """Ventana de dias guardada en `avisos` como JSON."""
        if not fila.avisos:
            return None, None
        try:
            meta = json.loads(fila.avisos)
            return meta.get("dias_previos"), meta.get("dias_vencidos")
        except (ValueError, TypeError):
            return None, None

    def _estado_envio(self) -> EstadoUltimoEnvio:
        fila = self.repository.ultimo_envio_vencimiento()
        intervalos = self.repository.intervalos_cubiertos()
        cubierto_desde = min((a for a, _ in intervalos), default=None)
        cubierto_hasta = max((b for _, b in intervalos), default=None)

        if fila is None:
            return EstadoUltimoEnvio(
                cubierto_desde=cubierto_desde, cubierto_hasta=cubierto_hasta
            )
        prev, venc = self._rango_de(fila)
        return EstadoUltimoEnvio(
            ultimo_envio=_utc(fila.fecha),
            ultimo_total=(fila.registros or 0) + (fila.errores or 0),
            ultimo_enviados=fila.registros,
            ultimo_fallidos=fila.errores,
            ejecutado_por=fila.usuario.usuario if fila.usuario else None,
            dias_previos=prev,
            dias_vencidos=venc,
            cubierto_desde=cubierto_desde,
            cubierto_hasta=cubierto_hasta,
        )

    def historial_envios(self, limit: int = 20) -> list[HistorialEnvioItem]:
        filas = self.repository.historial_envios_vencimiento(limit)
        items = []
        for fila in filas:
            prev, venc = self._rango_de(fila)
            items.append(
                HistorialEnvioItem(
                    fecha=_utc(fila.fecha),
                    enviados=fila.registros or 0,
                    fallidos=fila.errores or 0,
                    total=(fila.registros or 0) + (fila.errores or 0),
                    ejecutado_por=fila.usuario.usuario if fila.usuario else None,
                    dias_previos=prev,
                    dias_vencidos=venc,
                    fallos=self._fallos_de(fila),
                )
            )
        return items

    # ------------------------------------------------------------------
    # Listado (preparar, no envia)
    # ------------------------------------------------------------------
    @staticmethod
    def _ya_cubierta(fecha_fin: date | None, intervalos: list[tuple[date, date]]) -> bool:
        if fecha_fin is None:
            return False
        return any(desde <= fecha_fin <= hasta for desde, hasta in intervalos)

    def _a_item(
        self, fila: dict, intervalos: list[tuple[date, date]]
    ) -> TitularPorVencer:
        # El dialecto de Oracle normaliza los nombres de columna de un text()
        # a minusculas; el schema los espera en mayusculas.
        datos = {clave.upper(): valor for clave, valor in fila.items()}
        dias = int(datos["DIAS"])
        datos["DIAS"] = dias
        datos["VENCIDO"] = dias < 0
        datos["YA_ENVIADO"] = self._ya_cubierta(
            _a_fecha(datos.get("FECHA_FIN")), intervalos
        )
        return TitularPorVencer(**datos)

    def listar_titulares_por_vencer(
        self,
        dias_previos: int = 7,
        dias_vencidos: int = 0,
        solo_con_correo: bool = True,
        segmento: str = "particular",
    ) -> ListadoTitularesPorVencer:
        intervalos = self.repository.intervalos_cubiertos()
        filas = self.repository.listar_titulares_por_vencer(
            dias_previos, dias_vencidos, solo_con_correo, segmento=segmento
        )
        items = [self._a_item(f, intervalos) for f in filas]
        # Primero los pendientes (YA_ENVIADO=False), luego los ya avisados. El
        # sort es estable: dentro de cada grupo se conserva el orden por
        # FECHA_FIN / NOMBRE que trae la consulta.
        items.sort(key=lambda i: i.YA_ENVIADO)
        nuevos = sum(1 for i in items if not i.YA_ENVIADO)
        return ListadoTitularesPorVencer(
            total=len(items),
            nuevos=nuevos,
            ya_enviados=len(items) - nuevos,
            dias_previos=dias_previos,
            dias_vencidos=dias_vencidos,
            estado_envio=self._estado_envio(),
            items=items,
        )

    # ------------------------------------------------------------------
    # Empresas (agrupado) — SOLO consulta: el CRM no envia correos a las
    # empresas ni a sus colaboradores desde este modulo.
    # ------------------------------------------------------------------
    def listar_empresas_por_vencer(
        self, dias_previos: int = 7, dias_vencidos: int = 0
    ) -> ListadoEmpresasPorVencer:
        """Titulares de un convenio empresarial (con EMPRESA) por vencer,
        agrupados por empresa. Es informativo: no dispara ningun envio."""
        filas = self.repository.listar_titulares_por_vencer(
            dias_previos, dias_vencidos, solo_con_correo=False, segmento="empresa"
        )
        # Sin intervalos: YA_ENVIADO no aplica al recordatorio empresarial
        # (el historial de "cubierto" es del envio particular a cada titular).
        items = [self._a_item(f, intervalos=[]) for f in filas]

        agrupado: dict[str, list[TitularPorVencer]] = {}
        for item in items:
            agrupado.setdefault(item.EMPRESA or "Sin empresa", []).append(item)

        empresas = [
            EmpresaPorVencer(EMPRESA=nombre, TOTAL=len(titulares), titulares=titulares)
            for nombre, titulares in agrupado.items()
        ]
        empresas.sort(key=lambda e: min(t.DIAS for t in e.titulares))

        return ListadoEmpresasPorVencer(
            total_empresas=len(empresas),
            total_titulares=len(items),
            dias_previos=dias_previos,
            dias_vencidos=dias_vencidos,
            empresas=empresas,
        )

    def _verificar_permiso_envio(self, username: str) -> None:
        from app.modules.auth.repository import AuthRepository

        usuario_id = self.repository.obtener_usuario_id(username)
        permisos = (
            AuthRepository(self.db).obtener_permisos(usuario_id) if usuario_id else []
        )
        if PERMISO_ENVIAR_RECORDATORIO not in permisos:
            raise ForbiddenError(
                "No tienes permiso para enviar recordatorios de vencimiento."
            )


    def _verificar_permiso_campana(self, username: str) -> None:
        from app.modules.auth.repository import AuthRepository

        usuario_id = self.repository.obtener_usuario_id(username)
        permisos = (
            AuthRepository(self.db).obtener_permisos(usuario_id) if usuario_id else []
        )
        if PERMISO_ENVIAR_CAMPANA not in permisos:
            raise ForbiddenError("No tienes permiso para enviar campañas.")

    def enviar_campana(
        self, username: str, data: CampanaEnvioRequest
    ) -> CampanaEnvioResultado:
        """Envía el HTML de una plantilla de Campañas a una lista de correos.

        Best-effort por destinatario: si uno falla, se sigue con los demás.
        Se manda un correo individual por persona (no van en copia entre sí).
        """
        self._verificar_permiso_campana(username)
        verificar_cupo(len(data.destinatarios))

        enviados = 0
        fallos: list[CampanaFallo] = []
        for correo in data.destinatarios:
            try:
                enviar_correo([str(correo)], data.asunto, data.html)
                enviados += 1
            except Exception as exc:  # noqa: BLE001 - best effort por destinatario
                logger.exception("Fallo la campaña a %s", correo)
                fallos.append(CampanaFallo(correo=str(correo), error=str(exc)))

        return CampanaEnvioResultado(
            total=len(data.destinatarios),
            enviados=enviados,
            fallidos=len(fallos),
            fallos=fallos,
        )

    # ------------------------------------------------------------------
    # Envio (boton manual) — SOLO particulares (sin EMPRESA). A los
    # titulares de empresa NO se les manda correo desde el CRM.
    # ------------------------------------------------------------------
    def enviar_recordatorios_vencimiento(
        self,
        username: str,
        dias_previos: int = 7,
        dias_vencidos: int = 0,
        incluir_ya_enviados: bool = False,
    ) -> EnvioRecordatoriosResultado:
        """Envia el correo de vencimiento a los titulares PARTICULARES (sin
        empresa asociada) de la ventana pedida.

        Por defecto SOLO a los que todavia no lo recibieron (su FECHA_FIN no
        cae en ningun rango ya cubierto por un envio anterior). Con
        `incluir_ya_enviados=True` se reenvia a todos los de la ventana.

        Best-effort por destinatario. Registra la corrida en el historial y
        marca el rango [hoy - dias_vencidos, hoy + dias_previos] como cubierto.

        Exige el permiso `recordatorios:gestionar` (defensa en profundidad: el
        frontend ya oculta el boton, esto cubre una peticion armada a mano).
        """
        self._verificar_permiso_envio(username)
        usuario_id = self.repository.obtener_usuario_id(username)

        intervalos = self.repository.intervalos_cubiertos()
        filas = self.repository.listar_titulares_por_vencer(
            dias_previos, dias_vencidos, solo_con_correo=True, segmento="particular"
        )
        items = [self._a_item(f, intervalos) for f in filas]

        if incluir_ya_enviados:
            a_enviar = items
        else:
            a_enviar = [i for i in items if not i.YA_ENVIADO]
        omitidos = len(items) - len(a_enviar)
        # Antes de mandar nada: si no caben en el cupo de hoy no se envia ninguno
        # (y no se marca el rango como cubierto).
        verificar_cupo(len(a_enviar))

        enviados = 0
        fallos: list[FalloEnvio] = []
        for item in a_enviar:
            try:
                enviar_correo_plantilla(
                    destinatarios=[item.CORREO],
                    asunto=ASUNTO_VENCIMIENTO,
                    plantilla=PLANTILLA_VENCIMIENTO,
                    variables={
                        "nombre": item.NOMBRE or "",
                        "dias": item.DIAS,
                        "fecha_fin": item.FECHA_FIN_TXT,
                    },
                )
                enviados += 1
            except Exception as exc:  # noqa: BLE001 - best effort por destinatario
                logger.exception(
                    "Fallo el correo de vencimiento a %s (%s)",
                    item.DOCUMENTO,
                    item.CORREO,
                )
                fallos.append(
                    FalloEnvio(
                        DOCUMENTO=item.DOCUMENTO,
                        NOMBRE=item.NOMBRE,
                        CORREO=item.CORREO,
                        error=str(exc),
                    )
                )

        hoy = datetime.now(timezone.utc).date()
        self.repository.registrar_envio_vencimiento(
            enviados,
            len(fallos),
            [f.model_dump() for f in fallos],
            usuario_id,
            dias_previos,
            dias_vencidos,
            cubre_desde=hoy - timedelta(days=dias_vencidos),
            cubre_hasta=hoy + timedelta(days=dias_previos),
        )

        return EnvioRecordatoriosResultado(
            total=len(items),
            a_enviar=len(a_enviar),
            enviados=enviados,
            fallidos=len(fallos),
            omitidos_ya_enviados=omitidos,
            fallos=fallos,
            estado_envio=self._estado_envio(),
        )
