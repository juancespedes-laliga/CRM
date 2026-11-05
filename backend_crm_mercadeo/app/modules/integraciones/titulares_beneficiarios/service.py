import logging
from datetime import date
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from app.core.email import enviar_correo_plantilla
from app.modules.administracion.auditoria.contexto import ContextoAuditoria
from app.modules.administracion.auditoria.registro import RegistradorAuditoria, campo_cambiado
from app.modules.integraciones.titulares_beneficiarios.auditoria import (
    MODULO_BENEFICIARIOS,
    MODULO_TITULARES,
    AuditoriaPlanLiga,
    diferencias,
    nombre_completo,
)
from app.modules.integraciones.titulares_beneficiarios.exceptions import (
    BeneficiarioInactivoError,
    BeneficiarioNotFoundError,
    CupoBeneficiariosExcedidoError,
    CupoPlanInsuficienteError,
    DocumentoDuplicadoError,
    TitularAmbiguoError,
    TitularInactivoError,
    TitularNotFoundError,
)
from app.modules.integraciones.titulares_beneficiarios.legacy_repository import (
    LegacyRepository,
)
from app.modules.integraciones.titulares_beneficiarios.repository import (
    ESTADO_ACTIVO,
    TitularesBeneficiariosRepository,
)
from app.modules.integraciones.titulares_beneficiarios.schemas import (
    ActivacionBeneficiarioResultado,
    ActivacionTitularResultado,
    BeneficiarioCrear,
    BeneficiarioDetalle,
    BeneficiarioUpdate,
    CambioFechaIngresoGrupo,
    CambioFechaIngresoGrupoResultado,
    CreacionBeneficiarioResultado,
    CreacionTitularResultado,
    DesactivacionBeneficiarioResultado,
    DesactivacionTitularResultado,
    ListadoTitulares,
    ListadoTitularesPaginado,
    ListadoRenovacionesMes,
    PlanItem,
    PlanNombre,
    ReemplazoBeneficiarioResultado,
    ReemplazoPersona,
    ReemplazoTitularResultado,
    RenovacionMesItem,
    ResumenRenovacionesMes,
    ResumenTitularesBeneficiarios,
    TitularCrear,
    TitularDetalle,
    TitularUpdate,
)

logger = logging.getLogger(__name__)

# Nombres de archivo en app/templates/emails/ (ver app/core/email.py).
PLANTILLA_CORREO_REGISTRO = "Registro (1).html"
PLANTILLA_CORREO_BIENVENIDA = "Bienvenida (1).html"

# Permiso (modulo:accion en INTRANET_PERMISOS_APP) que habilita elegir un plan
# distinto del Estandar al dar de alta un titular. Se asigna al rol Comercial;
# Jefe y Admin lo reciben por comodin (ver AuthRepository.obtener_permisos).
# Cualquier otro rol queda fijo en Estandar.
PERMISO_ELEGIR_PLAN = "planliga:elegir_plan"


def _persona(fila: dict | None) -> str | None:
    """'Nombre (documento)' para el antes -> despues de la auditoria."""
    if not fila:
        return None
    nombre = nombre_completo(fila)
    documento = fila.get("DOCUMENTO")
    return f"{nombre} ({documento})" if documento else nombre


class TitularesBeneficiariosService:
    def __init__(self, db: Session, contexto: ContextoAuditoria | None = None) -> None:
        self.db = db
        self.repository = TitularesBeneficiariosRepository(db)
        self.legacy_repository = LegacyRepository(db)
        self.auditoria = AuditoriaPlanLiga(RegistradorAuditoria(db, contexto))

    def _auditar(self, registrar: Callable[[], None]) -> None:
        """La auditoria nunca debe tumbar la accion del usuario (que ya hizo commit)."""
        try:
            registrar()
        except Exception:
            logger.exception("No se pudo registrar la auditoria de Plan Liga")

    def resumen(self) -> ResumenTitularesBeneficiarios:
        r = self.repository
        return ResumenTitularesBeneficiarios(
            titulares_activos=r.contar_titulares_activos(),
            beneficiarios_activos=r.contar_beneficiarios_activos(),
        )

    def obtener_titular(self, id_titular: int) -> TitularDetalle:
        fila = self.repository.obtener_titular(id_titular)
        if fila is None:
            raise TitularNotFoundError(id_titular)
        return TitularDetalle(**fila)

    def listar_beneficiarios(self, id_titular: int, estado: str = "A") -> list[BeneficiarioDetalle]:
        if self.repository.obtener_titular(id_titular) is None:
            raise TitularNotFoundError(id_titular)
        filas = self.repository.listar_beneficiarios(id_titular, estado)
        return [BeneficiarioDetalle(**fila) for fila in filas]

    def _puede_elegir_plan(self, username: str | None) -> bool:
        """Elegir un plan distinto del Estandar esta reservado al rol Comercial
        (Jefe/Admin lo reciben por comodin). Cualquier otro rol -o un username
        que no resuelve a un usuario_id- no puede elegirlo: defensa contra una
        peticion armada a mano que se salte el bloqueo del frontend."""
        if not username:
            return False
        usuario_id = self.repository.obtener_usuario_id(username)
        if usuario_id is None:
            return False

        from app.modules.auth.repository import AuthRepository

        return PERMISO_ELEGIR_PLAN in AuthRepository(self.db).obtener_permisos(usuario_id)

    def crear_titular(self, data: TitularCrear, username: str) -> CreacionTitularResultado:
        duplicado = self.repository.existe_documento(data.TIPO_DOCUMENTO, data.DOCUMENTO)
        if duplicado is not None:
            raise DocumentoDuplicadoError(data.DOCUMENTO, duplicado)

        datos = data.model_dump(exclude={"FECHA_INGRESO"})
        usuario_id = self.repository.obtener_usuario_id(username)

        # tipo_plan_id NULL = Plan Estandar (ver BENEFICIARIOS_PLAN_ESTANDAR en repository.py).
        if not self._puede_elegir_plan(username) or not datos.get("TIPO_PLAN_ID"):
            datos["TIPO_PLAN_ID"] = None

        self.legacy_repository.crear_preplanliga(datos, usuario_id)

        id_titular = self.repository.crear_titular(datos, data.FECHA_INGRESO)

        usuario_creado = self.legacy_repository.crear_usuario_servinte(
            data.TIPO_DOCUMENTO, data.DOCUMENTO, data.NOMBRE1, data.NOMBRE2,
            data.APELLIDO1, data.APELLIDO2,
        )
        nombre_completo = " ".join(
            parte for parte in [data.NOMBRE1, data.NOMBRE2, data.APELLIDO1, data.APELLIDO2]
            if parte
        )
        marcado_incle = self.legacy_repository.marcar_nuevo_titular_incle(
            data.TIPO_DOCUMENTO, data.DOCUMENTO, nombre_completo
        )

        # Correo de registro al titular nuevo (best-effort): si Gmail falla o el
        # titular no tiene correo, no debe tumbar la creacion, que ya quedo hecha. No se
        # manda en carga masiva (ENVIAR_CORREO_REGISTRO en False ahi), solo alta manual.
        if data.CORREO and data.ENVIAR_CORREO_REGISTRO:
            try:
                enviar_correo_plantilla(
                    destinatarios=[data.CORREO],
                    asunto="Completa tu registro - Membresía Plan Liga",
                    plantilla=PLANTILLA_CORREO_REGISTRO,
                    variables={"nombre": nombre_completo},
                )
                # Solo se marca 'SI' si el envio no lanzo: si Gmail falla o el
                # titular no tiene correo, la columna CORREO_ENVIADO queda como
                # estaba (sin escribir nada).
                self.legacy_repository.marcar_correo_enviado_preplanliga(
                    data.TIPO_DOCUMENTO, data.DOCUMENTO
                )
            except Exception:
                logger.exception(
                    "No se pudo enviar el correo de registro al titular %s", id_titular
                )

        fila = self.repository.obtener_titular(id_titular)
        self._auditar(lambda: self.auditoria.registrar(MODULO_TITULARES, "creacion", fila))
        return CreacionTitularResultado(
            titular=TitularDetalle(**fila),
            usuario_servinte_creado=usuario_creado,
            marcado_en_incle=marcado_incle,
        )

    def crear_beneficiario(
        self, id_titular: int, data: BeneficiarioCrear
    ) -> CreacionBeneficiarioResultado:
        titular = self.repository.obtener_titular(id_titular)
        if titular is None:
            raise TitularNotFoundError(id_titular)
        if titular["ESTADO"] != ESTADO_ACTIVO:
            raise TitularInactivoError(id_titular, accion="crear el beneficiario")

        duplicado = self.repository.existe_documento(data.TIPO_DOCUMENTO, data.DOCUMENTO)
        if duplicado is not None:
            raise DocumentoDuplicadoError(data.DOCUMENTO, duplicado)

        cantidad_actual = self.repository.contar_beneficiarios(id_titular)
        cupo = self.repository.cupo_beneficiarios_titular(id_titular)
        if cantidad_actual >= cupo:
            raise CupoBeneficiariosExcedidoError(id_titular)

        # El beneficiario hereda la fecha de ingreso del titular (mismo criterio que
        # activar_beneficiario): el frontend nunca manda FECHA_INGRESO al crear un
        # beneficiario porque asume que el backend hace esto.
        fecha_ingreso = self.repository.obtener_fecha_ingreso_titular(id_titular)
        orden = self.repository.siguiente_orden_beneficiario(id_titular)
        datos = data.model_dump()
        id_beneficiario = self.repository.crear_beneficiario(
            id_titular,
            datos,
            fecha_ingreso,
            orden,
            titular["TIPO_PLAN"],
            titular["EMPRESA"],
            titular["PLAN_NOMBRE"],
        )

        usuario_creado = self.legacy_repository.crear_usuario_servinte(
            data.TIPO_DOCUMENTO, data.DOCUMENTO, data.NOMBRE1, data.NOMBRE2,
            data.APELLIDO1, data.APELLIDO2,
        )
        nombre_completo = " ".join(
            parte for parte in [data.NOMBRE1, data.NOMBRE2, data.APELLIDO1, data.APELLIDO2]
            if parte
        )
        marcado_incle = self.legacy_repository.marcar_nuevo_beneficiario_incle(
            data.TIPO_DOCUMENTO, data.DOCUMENTO, nombre_completo
        )

        # Correo de bienvenida al agregar un beneficiario nuevo (best-effort: si Gmail
        # falla, no tumba la creacion, que ya quedo hecha). Se manda al beneficiario Y al
        # titular de su grupo (para que el titular vea que se agrego alguien nuevo) -
        # a quien tenga correo cargado de los dos, no falla si a alguno le falta. No se
        # manda en carga masiva (ENVIAR_CORREO_BIENVENIDA en False ahi), solo alta manual.
        if data.ENVIAR_CORREO_BIENVENIDA:
            destinatarios = [c for c in {data.CORREO, titular.get("CORREO")} if c]
            if destinatarios:
                try:
                    enviar_correo_plantilla(
                        destinatarios=destinatarios,
                        asunto="Bienvenido(a) a la membresía Plan Liga",
                        plantilla=PLANTILLA_CORREO_BIENVENIDA,
                        variables={"lista": f'<li style="margin: 0 0 8px 0;">{nombre_completo}</li>'},
                    )
                except Exception:
                    logger.exception(
                        "No se pudo enviar el correo de bienvenida al beneficiario %s", id_beneficiario
                    )

        fila = self.repository.obtener_beneficiario(id_titular, id_beneficiario)
        self._auditar(lambda: self.auditoria.registrar(
            MODULO_BENEFICIARIOS, "creacion", fila, titular_id=id_titular
        ))
        return CreacionBeneficiarioResultado(
            beneficiario=BeneficiarioDetalle(**fila),
            usuario_servinte_creado=usuario_creado,
            marcado_en_incle=marcado_incle,
        )

    def actualizar_titular(
        self, id_titular: int, data: TitularUpdate, username: str | None = None
    ) -> TitularDetalle:
        cambios = data.model_dump(
            exclude_unset=True, exclude={"CAMBIAR_PLAN", "TIPO_PLAN_ID"}
        )
        # Cambio del plan contratado: igual que en la renovacion (activar_titular),
        # requiere el permiso planliga:elegir_plan y no permite bajar a un plan
        # cuyo cupo sea menor a los beneficiarios activos que ya tiene el titular.
        cambiar_plan = data.CAMBIAR_PLAN and self._puede_elegir_plan(username)
        if cambiar_plan:
            cupo_nuevo_plan = self.repository.cupo_de_plan(data.TIPO_PLAN_ID)
            beneficiarios_activos = self.repository.contar_beneficiarios(id_titular)
            if beneficiarios_activos > cupo_nuevo_plan:
                raise CupoPlanInsuficienteError(
                    id_titular, beneficiarios_activos, cupo_nuevo_plan
                )
        antes = self.repository.obtener_titular(id_titular)
        if not self.repository.actualizar_titular(
            id_titular, cambios, cambiar_plan, data.TIPO_PLAN_ID
        ):
            raise TitularNotFoundError(id_titular)
        fila = self.repository.obtener_titular(id_titular)

        def auditar() -> None:
            cambio_plan = (antes or {}).get("TIPO_PLAN_ID") != fila.get("TIPO_PLAN_ID") or (
                (antes or {}).get("TIPO_PLAN") != fila.get("TIPO_PLAN")
            )
            datos = self.auditoria.fila(
                MODULO_TITULARES, "cambio_plan" if cambio_plan else "edicion", fila, anterior=antes
            )
            # Guardar sin tocar nada no deja rastro.
            if datos["cambios"] or datos["estado_antes"] != datos["estado_despues"]:
                self.auditoria.registrar_varios([datos])

        self._auditar(auditar)
        return TitularDetalle(**fila)

    def actualizar_beneficiario(
        self, id_titular: int, id_beneficiario: int, data: BeneficiarioUpdate
    ) -> BeneficiarioDetalle:
        if self.repository.obtener_titular(id_titular) is None:
            raise TitularNotFoundError(id_titular)
        cambios = data.model_dump(exclude_unset=True)
        antes = self.repository.obtener_beneficiario(id_titular, id_beneficiario)
        if not self.repository.actualizar_beneficiario(id_titular, id_beneficiario, cambios):
            raise BeneficiarioNotFoundError(id_beneficiario)
        fila = self.repository.obtener_beneficiario(id_titular, id_beneficiario)

        def auditar() -> None:
            datos = self.auditoria.fila(
                MODULO_BENEFICIARIOS, "edicion", fila, anterior=antes, titular_id=id_titular
            )
            if datos["cambios"] or datos["estado_antes"] != datos["estado_despues"]:
                self.auditoria.registrar_varios([datos])

        self._auditar(auditar)
        return BeneficiarioDetalle(**fila)

    def cambiar_titular_beneficiario(
        self, id_beneficiario: int, documento_titular_nuevo: str
    ) -> BeneficiarioDetalle:
        beneficiario_actual = self.repository.obtener_beneficiario_por_id(id_beneficiario)
        if beneficiario_actual is None:
            raise BeneficiarioNotFoundError(id_beneficiario)
        id_titular_actual = beneficiario_actual["PLANLIGA_ID"]

        titulares = self.repository.buscar_titulares_por_documento(documento_titular_nuevo)
        if not titulares:
            raise TitularNotFoundError(documento_titular_nuevo)
        if len(titulares) > 1:
            raise TitularAmbiguoError(documento_titular_nuevo)

        titular_nuevo = titulares[0]
        id_titular_nuevo = titular_nuevo["ID_TITULAR"]
        if titular_nuevo["ESTADO"] != ESTADO_ACTIVO:
            raise TitularInactivoError(id_titular_nuevo, accion="mover el beneficiario")

        cantidad_actual = self.repository.contar_beneficiarios(id_titular_nuevo)
        cupo = self.repository.cupo_beneficiarios_titular(id_titular_nuevo)
        if cantidad_actual >= cupo:
            raise CupoBeneficiariosExcedidoError(id_titular_nuevo)

        detalle_titular_nuevo = self.repository.obtener_titular(id_titular_nuevo)
        orden = self.repository.siguiente_orden_beneficiario(id_titular_nuevo)
        if not self.repository.cambiar_titular_beneficiario(
            id_titular_actual,
            id_beneficiario,
            id_titular_nuevo,
            orden,
            detalle_titular_nuevo["TIPO_PLAN"],
            detalle_titular_nuevo["EMPRESA"],
            detalle_titular_nuevo["PLAN_NOMBRE"],
        ):
            raise BeneficiarioNotFoundError(id_beneficiario)

        fila = self.repository.obtener_beneficiario(id_titular_nuevo, id_beneficiario)

        def auditar() -> None:
            titular_anterior = self.repository.obtener_titular(id_titular_actual)
            cambios = [
                campo_cambiado("TITULAR", "Titular", _persona(titular_anterior), _persona(detalle_titular_nuevo)),
                *diferencias(beneficiario_actual, fila),
            ]
            self.auditoria.registrar(
                MODULO_BENEFICIARIOS, "cambio_titular", fila,
                anterior=beneficiario_actual, titular_id=id_titular_nuevo, cambios=cambios,
            )

        self._auditar(auditar)
        return BeneficiarioDetalle(**fila)

    def reemplazar_titular(
        self, id_titular: int, data: ReemplazoPersona
    ) -> ReemplazoTitularResultado:
        anterior = self.repository.obtener_titular(id_titular)
        if anterior is None:
            raise TitularNotFoundError(id_titular)
        if anterior["ESTADO"] != ESTADO_ACTIVO:
            raise TitularInactivoError(id_titular, accion="reemplazar el titular")

        # Si el nuevo titular es un beneficiario de este mismo grupo (ej. el titular
        # fallecio y un beneficiario toma su lugar) se permite: su fila de
        # beneficiario queda inactiva en el grupo anterior como historial. Cualquier
        # otro duplicado se rechaza.
        id_beneficiario_promovido = None
        duplicado = self.repository.existe_documento(data.TIPO_DOCUMENTO, data.DOCUMENTO)
        if duplicado == "BENEFICIARIO":
            id_beneficiario_promovido = self.repository.buscar_beneficiario_del_grupo(
                id_titular, data.TIPO_DOCUMENTO, data.DOCUMENTO
            )
        if duplicado is not None and id_beneficiario_promovido is None:
            raise DocumentoDuplicadoError(data.DOCUMENTO, duplicado)

        ids_beneficiarios = self.repository.ids_beneficiarios_titular(id_titular, solo_activos=True)
        resultado = self.repository.reemplazar_titular(
            id_titular, data.model_dump(), id_beneficiario_promovido
        )
        if resultado is None:
            raise TitularInactivoError(id_titular, accion="reemplazar el titular")
        id_nuevo, num_beneficiarios = resultado

        # El titular anterior queda fuera de Plan Liga en Servinte.
        num_incle_marcados = self.legacy_repository.marcar_registros_incle(
            anterior["TIPO_DOCUMENTO"], anterior["DOCUMENTO"]
        )
        self.legacy_repository.desactivar_preplanliga(
            anterior["TIPO_DOCUMENTO"], anterior["DOCUMENTO"]
        )

        # El titular nuevo se da de alta en Servinte como si fuera un ingreso nuevo.
        usuario_creado = self.legacy_repository.crear_usuario_servinte(
            data.TIPO_DOCUMENTO, data.DOCUMENTO, data.NOMBRE1, data.NOMBRE2,
            data.APELLIDO1, data.APELLIDO2,
        )
        nombre_completo = " ".join(
            parte for parte in [data.NOMBRE1, data.NOMBRE2, data.APELLIDO1, data.APELLIDO2]
            if parte
        )
        marcado_incle = self.legacy_repository.marcar_nuevo_titular_incle(
            data.TIPO_DOCUMENTO, data.DOCUMENTO, nombre_completo
        )
        # Un beneficiario promovido ya estaba en INCLE (marcar_nuevo_titular_incle no
        # hace nada); si estaba inactivo quedo con CLEEST = 1, asi que se reactiva.
        if id_beneficiario_promovido is not None:
            self.legacy_repository.desmarcar_registros_incle(
                data.TIPO_DOCUMENTO, data.DOCUMENTO
            )

        fila = self.repository.obtener_titular(id_nuevo)

        def auditar() -> None:
            anterior_despues = self.repository.obtener_titular(id_titular)
            nuevo, viejo = _persona(fila), _persona(anterior)
            filas = [
                self.auditoria.fila(
                    MODULO_TITULARES, "reemplazo", anterior_despues, anterior=anterior,
                    cambios=[campo_cambiado("REEMPLAZADO_POR", "Reemplazado por", None, nuevo)],
                    motivo=f"Reemplazado por {nuevo}",
                ),
                self.auditoria.fila(
                    MODULO_TITULARES, "creacion", fila, motivo=f"Reemplaza al titular {viejo}"
                ),
            ]
            # Los beneficiarios activos pasan al titular nuevo (o, si uno de ellos es el
            # nuevo titular, su fila de beneficiario queda inactiva).
            for b in self.repository.obtener_beneficiarios_por_ids(ids_beneficiarios).values():
                if b.get("PLANLIGA_ID") == id_nuevo:
                    filas.append(self.auditoria.fila(
                        MODULO_BENEFICIARIOS, "cambio_titular", b, anterior=b, titular_id=id_nuevo,
                        cambios=[campo_cambiado("TITULAR", "Titular", viejo, nuevo)],
                        motivo="Reemplazo del titular del grupo", origen="grupo",
                    ))
                elif b.get("ESTADO") != ESTADO_ACTIVO:
                    filas.append(self.auditoria.fila(
                        MODULO_BENEFICIARIOS, "desactivacion", b, anterior={**b, "ESTADO": ESTADO_ACTIVO},
                        titular_id=id_titular, cambios=[], motivo="Pasó a ser el titular del grupo",
                    ))
            self.auditoria.registrar_varios(filas)

        self._auditar(auditar)
        return ReemplazoTitularResultado(
            titular_anterior_id=id_titular,
            titular_nuevo=TitularDetalle(**fila),
            beneficiarios_reasignados=num_beneficiarios,
            usuario_servinte_creado=usuario_creado,
            marcado_en_incle=marcado_incle,
            registros_incle_marcados_anterior=num_incle_marcados,
            beneficiario_promovido=id_beneficiario_promovido is not None,
        )

    def reemplazar_beneficiario(
        self, id_titular: int, id_beneficiario: int, data: ReemplazoPersona
    ) -> ReemplazoBeneficiarioResultado:
        if self.repository.obtener_titular(id_titular) is None:
            raise TitularNotFoundError(id_titular)

        anterior = self.repository.obtener_beneficiario(id_titular, id_beneficiario)
        if anterior is None:
            raise BeneficiarioNotFoundError(id_beneficiario)
        if anterior["ESTADO"] != ESTADO_ACTIVO:
            raise BeneficiarioInactivoError(id_beneficiario)

        duplicado = self.repository.existe_documento(data.TIPO_DOCUMENTO, data.DOCUMENTO)
        if duplicado is not None:
            raise DocumentoDuplicadoError(data.DOCUMENTO, duplicado)

        id_nuevo = self.repository.reemplazar_beneficiario(
            id_titular, id_beneficiario, data.model_dump()
        )
        if id_nuevo is None:
            raise BeneficiarioInactivoError(id_beneficiario)

        # El beneficiario anterior queda fuera de Plan Liga en Servinte.
        num_incle_marcados = self.legacy_repository.marcar_registros_incle(
            anterior["TIPO_DOCUMENTO"], anterior["DOCUMENTO"]
        )

        # El beneficiario nuevo se da de alta en Servinte como si fuera un ingreso nuevo.
        usuario_creado = self.legacy_repository.crear_usuario_servinte(
            data.TIPO_DOCUMENTO, data.DOCUMENTO, data.NOMBRE1, data.NOMBRE2,
            data.APELLIDO1, data.APELLIDO2,
        )
        nombre_completo = " ".join(
            parte for parte in [data.NOMBRE1, data.NOMBRE2, data.APELLIDO1, data.APELLIDO2]
            if parte
        )
        marcado_incle = self.legacy_repository.marcar_nuevo_beneficiario_incle(
            data.TIPO_DOCUMENTO, data.DOCUMENTO, nombre_completo
        )

        fila = self.repository.obtener_beneficiario(id_titular, id_nuevo)

        def auditar() -> None:
            anterior_despues = self.repository.obtener_beneficiario(id_titular, id_beneficiario)
            nuevo, viejo = _persona(fila), _persona(anterior)
            self.auditoria.registrar_varios([
                self.auditoria.fila(
                    MODULO_BENEFICIARIOS, "reemplazo", anterior_despues or anterior, anterior=anterior,
                    titular_id=id_titular,
                    cambios=[campo_cambiado("REEMPLAZADO_POR", "Reemplazado por", None, nuevo)],
                    motivo=f"Reemplazado por {nuevo}",
                ),
                self.auditoria.fila(
                    MODULO_BENEFICIARIOS, "creacion", fila, titular_id=id_titular,
                    motivo=f"Reemplaza al beneficiario {viejo}",
                ),
            ])

        self._auditar(auditar)
        return ReemplazoBeneficiarioResultado(
            beneficiario_anterior_id=id_beneficiario,
            beneficiario_nuevo=BeneficiarioDetalle(**fila),
            usuario_servinte_creado=usuario_creado,
            marcado_en_incle=marcado_incle,
            registros_incle_marcados_anterior=num_incle_marcados,
        )

    def activar_beneficiario(
        self,
        id_titular: int,
        id_beneficiario: int,
        fecha_ingreso: date | None = None,
        enviar_correo_bienvenida: bool = True,
    ) -> ActivacionBeneficiarioResultado:
        titular = self.repository.obtener_titular(id_titular)
        if titular is None:
            raise TitularNotFoundError(id_titular)
        if titular["ESTADO"] != ESTADO_ACTIVO:
            raise TitularInactivoError(id_titular)

        if fecha_ingreso is None:
            fecha_ingreso = self.repository.obtener_fecha_ingreso_titular(id_titular)

        antes = self.repository.obtener_beneficiario(id_titular, id_beneficiario)
        if not self.repository.activar_beneficiario(id_titular, id_beneficiario, fecha_ingreso):
            raise BeneficiarioNotFoundError(id_beneficiario)
        fila = self.repository.obtener_beneficiario(id_titular, id_beneficiario)
        # Si ya estaba activo, "activar" solo le cambia la fecha: es una renovacion.
        accion = "renovacion" if (antes or {}).get("ESTADO") == ESTADO_ACTIVO else "activacion"
        self._auditar(lambda: self.auditoria.registrar(
            MODULO_BENEFICIARIOS, accion, fila, anterior=antes, titular_id=id_titular
        ))
        num_incle = self.legacy_repository.desmarcar_registros_incle(
            fila["TIPO_DOCUMENTO"], fila["DOCUMENTO"]
        )

        # Correo de bienvenida al reactivar (estaba inactivo): mismo criterio best-effort
        # que al crearlo, no tumba la activacion si Gmail falla. Se manda al beneficiario Y
        # al titular de su grupo (para que sepa que ya quedo activo), a quien tenga correo
        # cargado de los dos. No se manda desde la activacion masiva por Excel (ver
        # activar_beneficiario_sin_titular mas abajo).
        if enviar_correo_bienvenida:
            destinatarios = [c for c in {fila["CORREO"], titular.get("CORREO")} if c]
            if destinatarios:
                try:
                    nombre_completo = " ".join(
                        parte for parte in [fila["NOMBRE1"], fila["NOMBRE2"], fila["APELLIDO1"], fila["APELLIDO2"]]
                        if parte
                    )
                    enviar_correo_plantilla(
                        destinatarios=destinatarios,
                        asunto="Bienvenido(a) a la membresía Plan Liga",
                        plantilla=PLANTILLA_CORREO_BIENVENIDA,
                        variables={"lista": f'<li style="margin: 0 0 8px 0;">{nombre_completo}</li>'},
                    )
                except Exception:
                    logger.exception(
                        "No se pudo enviar el correo de bienvenida al activar el beneficiario %s", id_beneficiario
                    )

        return ActivacionBeneficiarioResultado(
            beneficiario=BeneficiarioDetalle(**fila),
            registros_incle_desmarcados=num_incle,
        )

    def desactivar_beneficiario(
        self, id_titular: int, id_beneficiario: int
    ) -> DesactivacionBeneficiarioResultado:
        antes = self.repository.obtener_beneficiario(id_titular, id_beneficiario)
        if not self.repository.desactivar_beneficiario(id_titular, id_beneficiario):
            raise BeneficiarioNotFoundError(id_beneficiario)
        fila = self.repository.obtener_beneficiario(id_titular, id_beneficiario)
        self._auditar(lambda: self.auditoria.registrar(
            MODULO_BENEFICIARIOS, "desactivacion", fila, anterior=antes, titular_id=id_titular
        ))
        num_incle = self.legacy_repository.marcar_registros_incle(
            fila["TIPO_DOCUMENTO"], fila["DOCUMENTO"]
        )
        return DesactivacionBeneficiarioResultado(
            beneficiario=BeneficiarioDetalle(**fila),
            registros_incle_marcados=num_incle,
        )

    def activar_beneficiario_sin_titular(
        self, documento: str, fecha_ingreso: date
    ) -> ActivacionBeneficiarioResultado:
        # Solo la usa la activacion masiva por Excel (accionMasivaBeneficiarios.ts): por eso
        # enviar_correo_bienvenida=False, no manda el correo por cada fila del archivo.
        fila = self.repository.buscar_beneficiario_por_documento(documento)
        if fila is None:
            raise BeneficiarioNotFoundError(documento)
        return self.activar_beneficiario(
            fila["PLANLIGA_ID"], fila["ID"], fecha_ingreso, enviar_correo_bienvenida=False
        )

    def desactivar_beneficiario_sin_titular(
        self, documento: str
    ) -> DesactivacionBeneficiarioResultado:
        fila = self.repository.buscar_beneficiario_por_documento(documento)
        if fila is None:
            raise BeneficiarioNotFoundError(documento)
        return self.desactivar_beneficiario(fila["PLANLIGA_ID"], fila["ID"])

    def activar_titular(
        self,
        id_titular: int,
        fecha_ingreso: date,
        aplicar_a_grupo: bool = True,
        cambiar_plan: bool = False,
        tipo_plan: str | None = None,
        tipo_plan_id: int | None = None,
        username: str | None = None,
    ) -> ActivacionTitularResultado:
        # Revalidacion del permiso (ver _puede_elegir_plan): si el usuario no
        # puede elegir plan, CAMBIAR_PLAN se ignora aunque venga en True.
        cambiar_plan = cambiar_plan and self._puede_elegir_plan(username)
        if cambiar_plan:
            # No se permite bajar a un plan cuyo cupo sea menor a los
            # beneficiarios activos que el titular ya tiene: primero hay que
            # desactivarlos, o la renovacion completa (incluida la fecha) se
            # rechaza sin aplicar nada.
            cupo_nuevo_plan = self.repository.cupo_de_plan(tipo_plan_id)
            beneficiarios_activos = self.repository.contar_beneficiarios(id_titular)
            if beneficiarios_activos > cupo_nuevo_plan:
                raise CupoPlanInsuficienteError(
                    id_titular, beneficiarios_activos, cupo_nuevo_plan
                )
        antes = self.repository.obtener_titular(id_titular)
        ids_beneficiarios = (
            self.repository.ids_beneficiarios_titular(id_titular) if aplicar_a_grupo else []
        )
        beneficiarios_antes = self.repository.obtener_beneficiarios_por_ids(ids_beneficiarios)
        if not self.repository.activar_titular(
            id_titular, fecha_ingreso, cambiar_plan, tipo_plan, tipo_plan_id
        ):
            raise TitularNotFoundError(id_titular)
        num_beneficiarios = (
            self.repository.activar_beneficiarios(id_titular, fecha_ingreso)
            if aplicar_a_grupo
            else 0
        )
        fila = self.repository.obtener_titular(id_titular)

        def auditar() -> None:
            # Activo antes -> renovacion; inactivo -> activacion (que tambien lo deja renovado).
            accion = "renovacion" if (antes or {}).get("ESTADO") == ESTADO_ACTIVO else "activacion"
            filas = [self.auditoria.fila(MODULO_TITULARES, accion, fila, anterior=antes)]
            motivo = f"Renovación del grupo de {nombre_completo(fila)}"
            for id_b, b in self.repository.obtener_beneficiarios_por_ids(ids_beneficiarios).items():
                filas.append(self.auditoria.fila(
                    MODULO_BENEFICIARIOS, "renovacion", b, anterior=beneficiarios_antes.get(id_b),
                    titular_id=id_titular, motivo=motivo, origen="grupo",
                ))
            self.auditoria.registrar_varios(filas)

        self._auditar(auditar)
        num_incle = self.legacy_repository.desmarcar_registros_incle(
            fila["TIPO_DOCUMENTO"], fila["DOCUMENTO"]
        )
        return ActivacionTitularResultado(
            titular=TitularDetalle(**fila),
            beneficiarios_activados=num_beneficiarios,
            registros_incle_desmarcados=num_incle,
        )

    def contar_grupo_activo(
        self, empresa: str | None = None, tipo_plan: str | None = None
    ) -> CambioFechaIngresoGrupoResultado:
        titulares, beneficiarios = self.repository.contar_grupo_activo(empresa, tipo_plan)
        return CambioFechaIngresoGrupoResultado(
            titulares_actualizados=titulares,
            beneficiarios_actualizados=beneficiarios,
        )

    def cambiar_fecha_ingreso_grupo(
        self, data: CambioFechaIngresoGrupo
    ) -> CambioFechaIngresoGrupoResultado:
        ids_t, ids_b = self.repository.ids_grupo_activo(data.EMPRESA, data.TIPO_PLAN)
        titulares_antes = self.repository.obtener_titulares_por_ids(ids_t)
        beneficiarios_antes = self.repository.obtener_beneficiarios_por_ids(ids_b)
        titulares, beneficiarios = self.repository.cambiar_fecha_ingreso_grupo(
            data.FECHA_INGRESO, data.EMPRESA, data.TIPO_PLAN
        )

        def auditar() -> None:
            motivo = (
                f"Cambio de fecha por empresa {data.EMPRESA}" if data.EMPRESA
                else f"Cambio de fecha por plan {data.TIPO_PLAN}"
            )
            filas = [
                self.auditoria.fila(
                    MODULO_TITULARES, "renovacion", t, anterior=titulares_antes.get(id_t),
                    motivo=motivo, origen="grupo",
                )
                for id_t, t in self.repository.obtener_titulares_por_ids(ids_t).items()
            ]
            filas += [
                self.auditoria.fila(
                    MODULO_BENEFICIARIOS, "renovacion", b, anterior=beneficiarios_antes.get(id_b),
                    titular_id=b.get("PLANLIGA_ID"), motivo=motivo, origen="grupo",
                )
                for id_b, b in self.repository.obtener_beneficiarios_por_ids(ids_b).items()
            ]
            self.auditoria.registrar_varios(filas)

        self._auditar(auditar)
        return CambioFechaIngresoGrupoResultado(
            titulares_actualizados=titulares,
            beneficiarios_actualizados=beneficiarios,
        )

    def listar_tipos_plan(self) -> list[str]:
        return self.repository.listar_tipos_plan()

    def desactivar_titular(self, id_titular: int) -> DesactivacionTitularResultado:
        antes = self.repository.obtener_titular(id_titular)
        ids_beneficiarios = self.repository.ids_beneficiarios_titular(id_titular, solo_activos=True)
        beneficiarios_antes = self.repository.obtener_beneficiarios_por_ids(ids_beneficiarios)
        if not self.repository.desactivar_titular(id_titular):
            raise TitularNotFoundError(id_titular)
        fila = self.repository.obtener_titular(id_titular)
        tipo, documento = fila["TIPO_DOCUMENTO"], fila["DOCUMENTO"]

        beneficiarios_desactivados = self.repository.desactivar_beneficiarios(id_titular)
        self.legacy_repository.desactivar_preplanliga(tipo, documento)

        num_incle = self.legacy_repository.marcar_registros_incle(tipo, documento)
        for tipo_b, documento_b in beneficiarios_desactivados:
            num_incle += self.legacy_repository.marcar_registros_incle(tipo_b, documento_b)

        def auditar() -> None:
            filas = [self.auditoria.fila(MODULO_TITULARES, "desactivacion", fila, anterior=antes)]
            motivo = f"Desactivación del titular {nombre_completo(fila)}"
            for id_b, b in self.repository.obtener_beneficiarios_por_ids(ids_beneficiarios).items():
                filas.append(self.auditoria.fila(
                    MODULO_BENEFICIARIOS, "desactivacion", b, anterior=beneficiarios_antes.get(id_b),
                    titular_id=id_titular, motivo=motivo, origen="grupo",
                ))
            self.auditoria.registrar_varios(filas)

        self._auditar(auditar)
        return DesactivacionTitularResultado(
            titular=TitularDetalle(**fila),
            beneficiarios_desactivados=len(beneficiarios_desactivados),
            registros_incle_marcados=num_incle,
        )

    def exportar_titulares_beneficiarios(
        self,
        estado: str | None = None,
        tipo_plan_id: str | None = None,
        sexo: str | None = None,
        edad: str | None = None,
        busqueda: str | None = None,
    ) -> Iterator[dict]:
        return self.repository.exportar_titulares_beneficiarios(
            estado, tipo_plan_id, sexo, edad, busqueda
        )

    def listar_titulares(
        self,
        limit: int = 6,
        offset: int = 0,
        estado: str | None = None,
        tipo_plan_id: str | None = None,
        sexo: str | None = None,
        edad: str | None = None,
        busqueda: str | None = None,
    ) -> ListadoTitularesPaginado:
        filas = self.repository.listar_titulares(
            limit, offset, estado, tipo_plan_id, sexo, edad, busqueda
        )
        total = self.repository.contar_titulares(estado, tipo_plan_id, sexo, edad, busqueda)
        return ListadoTitularesPaginado(
            items=[ListadoTitulares(**fila) for fila in filas],
            total=total,
            limit=limit,
            offset=offset,
        )

    def listar_renovaciones_mes(self, anio: int, mes: int) -> ListadoRenovacionesMes:
        filas = self.repository.listar_renovaciones_mes(anio, mes)
        items = [RenovacionMesItem(**fila) for fila in filas]
        vencen = [RenovacionMesItem(**fila) for fila in self.repository.listar_vencen_mes(anio, mes)]
        renovados = sum(1 for i in items if i.RENOVADO == "S")
        activos = sum(1 for i in items if i.ESTADO == ESTADO_ACTIVO)
        resumen = ResumenRenovacionesMes(
            anio=anio,
            mes=mes,
            total=len(items),
            renovados=renovados,
            altas_nuevas=len(items) - renovados,
            activos=activos,
            inactivos=len(items) - activos,
            vencen=len(vencen),
        )
        return ListadoRenovacionesMes(resumen=resumen, items=items, vencen=vencen)

    def establecer_color_titular(self, id_titular: int, color: str, username: str | None) -> None:
        usuario_id = self.repository.obtener_usuario_id(username) if username else None
        if not self.repository.establecer_color_titular(id_titular, color, usuario_id):
            raise TitularNotFoundError(id_titular)

    def quitar_color_titular(self, id_titular: int) -> None:
        # No es un error quitar un color que ya no estaba puesto (idempotente);
        # solo falla si el titular en si no existe.
        if self.repository.obtener_titular(id_titular) is None:
            raise TitularNotFoundError(id_titular)
        self.repository.quitar_color_titular(id_titular)

    def listar_planes(self) -> list[PlanItem]:
        return [
            PlanItem(
                ID=servicio.id,
                NOMBRE=(
                    f"{servicio.nombre} - {servicio.categoria}"
                    if servicio.categoria
                    else servicio.nombre
                ),
                TIPO=servicio.tipo_cliente,
                MAX_BENEFICIARIOS=servicio.beneficiarios,
                BENEFICIARIOS_ADICIONALES=servicio.beneficiarios_adicionales,
                DESCRIPCION=servicio.descripcion,
                ESTADO=servicio.estado,
            )
            for servicio in self.repository.listar_planes()
        ]

    def listar_nombres_planes(self) -> list[PlanNombre]:
        return [PlanNombre(**fila) for fila in self.repository.listar_nombres_planes()]
